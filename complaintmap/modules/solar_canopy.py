# modules/solar_canopy.py
"""
Solar canopy — monthly target, multi-panel options, partial installs,
mixed-panel greedy optimizer, cost & payback, and simple grid preview.
"""

import math
import requests
import numpy as np
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from io import BytesIO
import base64
import html

# Optional PVGIS via pvlib
try:
    from pvlib.iotools import get_pvgis_tmy
    PVLIB_AVAILABLE = True
except Exception:
    PVLIB_AVAILABLE = False


# ---------------- Helpers ----------------

def nominatim_search(q, limit=5):
    if not q or len(q) < 3:
        return []
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "jsonv2", "limit": limit},
            headers={"User-Agent": "smart-solar-app"},
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        return [{"name": d["display_name"], "lat": float(d["lat"]), "lon": float(d["lon"])} for d in data]
    except Exception:
        return []


def suggest_tilt(lat, mode):
    if mode.startswith("Summer"):
        t = lat - 10.0
    else:
        t = lat
    return max(5.0, min(60.0, t))


def get_pvgis_specific_yield(lat, lon):
    """Try PVGIS via pvlib; return kWh/kWp/year or None."""
    if not PVLIB_AVAILABLE:
        return None
    try:
        tmy, meta = get_pvgis_tmy(latitude=float(lat), longitude=float(lon), outputformat="json")
        def find_Ey(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "E_y":
                        return v
                    r = find_Ey(v)
                    if r is not None:
                        return r
            return None
        Ey = find_Ey(meta.get("outputs", {}))
        if Ey is not None:
            return float(Ey)
        if "P" in tmy.columns:
            return float(tmy["P"].sum())
        return None
    except Exception:
        return None


# Greedy mixed-panel optimizer (fast, heuristic)
def greedy_mixed_optimizer(panel_catalog, area_avail, required_installed_kWp, losses, specific_yield,
                           objective="coverage"):
    """
    panel_catalog: list of dicts {name, Wp, area}
    objective: "coverage" (maximize energy produced with area) or "meet_target" (try reach required_installed_kWp)
    Returns: dict with chosen panels list and metrics
    """
    # compute Wp/area and Wp per panel
    items = []
    for p in panel_catalog:
        Wp = float(p["Wp"]); a = float(p["area"])
        items.append({**p, "Wp": Wp, "area": a, "density": (Wp / a) if a > 0 else 0.0})

    # For coverage: sort by density (Wp per m2) descending and fill with largest density first
    # For meet_target: sort by Wp per area too, but allow smaller panels later to fine-tune
    if objective == "coverage":
        items_sorted = sorted(items, key=lambda x: x["density"], reverse=True)
    else:
        # meet_target: prefer high Wp/area, but also keep small panels available (stable order)
        items_sorted = sorted(items, key=lambda x: (x["density"], -x["area"]), reverse=True)

    remaining_area = area_avail
    chosen = []
    # We'll greedily add panels of each type as many as fit
    for it in items_sorted:
        if remaining_area < it["area"] or it["area"] <= 0:
            continue
        max_fit = int(math.floor(remaining_area / it["area"]))
        if max_fit <= 0:
            continue
        # Add them all initially
        chosen.append({"name": it["name"], "Wp": it["Wp"], "area": it["area"], "n": max_fit})
        remaining_area -= max_fit * it["area"]

    # compute installed and production
    total_panels = sum(c["n"] for c in chosen)
    installed_kWp = sum(c["n"] * c["Wp"] for c in chosen) / 1000.0
    annual_prod = installed_kWp * specific_yield * (1.0 - losses)
    coverage = (annual_prod / 365.0) / (required_installed_kWp * specific_yield / required_installed_kWp if required_installed_kWp>0 else 1)  # not useful; we recalc below
    monthly_prod = annual_prod / 12.0

    return {
        "chosen": chosen,
        "installed_kWp": installed_kWp,
        "annual_prod_kWh": annual_prod,
        "monthly_prod_kWh": monthly_prod,
        "panels_total": total_panels,
        "area_used_m2": area_avail - remaining_area,
        "area_remaining_m2": remaining_area
    }


def format_currency(x):
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return str(x)


def svg_grid_preview(roof_w_m, roof_h_m, panel_w_m, panel_h_m, n_cols=None, n_rows=None, show_counts=True):
    """
    Create a simple SVG preview showing how many panels (rectangles) fit in a rectangular roof.
    Assumes panels arranged in rows/cols with same orientation.
    panel_w_m, panel_h_m are panel footprint dims (use sqrt(area) approximation if unknown).
    """
    # approximate panel dims if not realistic
    panel_w = float(panel_w_m)
    panel_h = float(panel_h_m)

    roof_w = float(roof_w_m)
    roof_h = float(roof_h_m)

    # orientation: assume panel longer side along roof length; compute how many fit
    cols = int(math.floor(roof_w / panel_w))
    rows = int(math.floor(roof_h / panel_h))
    if cols <= 0 or rows <= 0:
        # try swapping
        cols = int(math.floor(roof_w / panel_h))
        rows = int(math.floor(roof_h / panel_w))
        if cols <= 0 or rows <= 0:
            # nothing fits
            svg = f"<div>No panels fit in preview (roof {roof_w}×{roof_h} m, panel {panel_w}×{panel_h} m)</div>"
            return svg, 0, 0

    cell_px = 30
    svg_w = cols * cell_px + 20
    svg_h = rows * cell_px + 20

    svg_parts = [f'<svg width="{svg_w}" height="{svg_h}" xmlns="http://www.w3.org/2000/svg">']
    svg_parts.append(f'<rect x="0" y="0" width="{svg_w}" height="{svg_h}" fill="#f6f6f6" stroke="#888" />')
    count = 0
    for r in range(rows):
        for c in range(cols):
            x = 10 + c * cell_px
            y = 10 + r * cell_px
            svg_parts.append(f'<rect x="{x}" y="{y}" width="{cell_px-2}" height="{cell_px-2}" fill="#1f77b4" stroke="#033" />')
            count += 1
    svg_parts.append(f'<text x="10" y="{svg_h-2}" font-size="12" fill="#000">Panels: {count} ({cols}×{rows})</text>')
    svg_parts.append('</svg>')
    svg = "\n".join(svg_parts)
    return svg, cols, rows


# ---------------- Main render ----------------

def render():
    st.set_page_config(page_title="Solar canopy - optimizer + payback", layout="wide")
    st.title("☀️ Solar canopy — optimizer, cost & payback, preview")

    # session state defaults
    if "lat" not in st.session_state:
        st.session_state.lat = 41.9028
    if "lon" not in st.session_state:
        st.session_state.lon = 12.4964

    ss = st.session_state

    # --- Location
    st.subheader("1) Location (search or click)")
    c1, c2 = st.columns([3, 1])
    with c1:
        q = st.text_input("Search address (min 3 chars)", "")
        suggestions = nominatim_search(q) if q else []
        if suggestions:
            st.write("Suggestions (click to select)")
            for s in suggestions:
                if st.button(s["name"], key=f"s_{hash(s['name'])}"):
                    ss.lat = s["lat"]; ss.lon = s["lon"]; st.success(f"Selected: {s['name']}")
    with c2:
        if st.button("Use my IP location"):
            try:
                ip = requests.get("https://ipapi.co/json", timeout=4).json()
                lat = ip.get("latitude") or ip.get("lat")
                lon = ip.get("longitude") or ip.get("lon")
                if lat and lon:
                    ss.lat = float(lat); ss.lon = float(lon); st.success("Approx location set")
                else:
                    st.error("IP location not available")
            except Exception:
                st.error("IP lookup failed")

    st.write("Click the map to set the exact coordinates (single click):")
    m = folium.Map(location=[ss.lat, ss.lon], zoom_start=15)
    folium.Marker([ss.lat, ss.lon], tooltip="Selected location").add_to(m)
    map_out = st_folium(m, height=420, width=800, returned_objects=["last_clicked"])
    if map_out and map_out.get("last_clicked"):
        latc = map_out["last_clicked"]["lat"]; lonc = map_out["last_clicked"]["lng"]
        ss.lat = float(latc); ss.lon = float(lonc); st.success(f"Location set: {ss.lat:.6f}, {ss.lon:.6f}")

    st.markdown("---")

    # --- Roof size
    st.subheader("2) Roof size & packing")
    c3, c4 = st.columns(2)
    with c3:
        method = st.radio("Provide roof size by:", ("Length × Width (m)", "Usable area (m²)"))
        if method == "Length × Width (m)":
            length = st.number_input("Roof length (m)", value=8.0, min_value=0.5, step=0.1)
            width = st.number_input("Roof width (m)", value=6.0, min_value=0.5, step=0.1)
            usable_area = float(length * width)
            st.write(f"Computed area: **{usable_area:.2f} m²**")
        else:
            usable_area = st.number_input("Usable area (m²)", value=40.0, min_value=0.1, step=0.5)
            length = None; width = None
        packing_pct = st.slider("Packing efficiency (%)", min_value=50, max_value=95, value=75)
        packing = packing_pct / 100.0
        effective_area = usable_area * packing
        st.write(f"Effective area for panels: **{effective_area:.2f} m²** ({packing_pct}%)")
    with c4:
        st.write("3) Monthly energy target")
        monthly_target = st.number_input("Monthly target (kWh/month)", value=150.0, min_value=0.0, step=1.0)
        target_month = float(monthly_target)
        target_year = target_month * 12.0
        target_day = target_year / 365.0
        st.write(f"→ {target_month:.1f} kWh/month ≈ {target_year:.0f} kWh/year ≈ {target_day:.2f} kWh/day")

    st.markdown("---")

    # panel catalog
    panel_catalog = [
        {"name": "400 W (2.0 m²)", "Wp": 400.0, "area": 2.0},
        {"name": "330 W (1.7 m²)", "Wp": 330.0, "area": 1.7},
        {"name": "275 W (1.6 m²)", "Wp": 275.0, "area": 1.6},
        {"name": "200 W (1.2 m²)", "Wp": 200.0, "area": 1.2},
        {"name": "100 W (0.6 m²)", "Wp": 100.0, "area": 0.6},
        {"name": "50 W (0.3 m²)",  "Wp": 50.0,  "area": 0.3},
    ]

    st.subheader("4) System settings & economics")
    colA, colB = st.columns(2)
    with colA:
        losses_pct = st.slider("System losses (%)", min_value=5, max_value=30, value=14)
        losses = losses_pct / 100.0
        tilt_mode = st.selectbox("Tilt mode", ["Annual", "Summer-optimised"])
        tilt = suggest_tilt(ss.lat, tilt_mode)
    with colB:
        st.write("Cost & payback")
        price_per_Wp = st.number_input("Approx. price per Wp (EUR/Wp)", value=0.8, min_value=0.0, step=0.01)
        electricity_price = st.number_input("Electricity price (EUR/kWh)", value=0.25, min_value=0.0, step=0.01)
        st.write("These values are used to estimate system cost and simple payback.")

    st.markdown("---")

    # Compute options & optimizer
    st.subheader("5) Compute options, optimizer & economics")
    if st.button("Compute options & optimize"):

        # PVGIS attempt
        st.info("Attempting PVGIS (pvlib) for site-specific yield...")
        specific_yield = get_pvgis_specific_yield(ss.lat, ss.lon)
        if specific_yield:
            st.success(f"PVGIS yield: {specific_yield:.0f} kWh/kWp/year")
        else:
            specific_yield = st.number_input("Specific yield (kWh/kWp/year) — manual", value=1200.0, step=10.0)

        # Required kWp before/after losses
        required_kWp_before_losses = (target_month * 12.0) / specific_yield
        required_installed_kWp = required_kWp_before_losses / (1.0 - losses) if (1.0 - losses) > 0 else float("inf")

        st.write(f"Required installed capacity (accounting losses): **{required_installed_kWp:.2f} kWp**")

        # For each panel type compute metrics (as before)
        options = []
        for p in panel_catalog:
            Wp = float(p["Wp"]); area_p = float(p["area"])
            max_fit = int(math.floor(effective_area / area_p)) if area_p > 0 else 0
            installed_if_full = (max_fit * Wp) / 1000.0
            panels_needed_for_target = int(math.ceil((required_installed_kWp * 1000.0) / Wp)) if Wp > 0 else int(1e9)
            fits_target = panels_needed_for_target <= max_fit
            prod_full_year = installed_if_full * specific_yield * (1.0 - losses)
            prod_full_month = prod_full_year / 12.0
            coverage_full = (prod_full_month / target_month * 100.0) if target_month > 0 else 0.0
            if fits_target:
                installed_target = panels_needed_for_target * Wp / 1000.0
                prod_target_year = installed_target * specific_yield * (1.0 - losses)
                prod_target_month = prod_target_year / 12.0
                coverage_target = (prod_target_month / target_month * 100.0) if target_month > 0 else 0.0
            else:
                installed_target = None
                prod_target_year = None
                coverage_target = None
            options.append({
                "name": p["name"],
                "Wp": Wp,
                "area_m2": area_p,
                "max_panels_fit": max_fit,
                "installed_if_full_kWp": installed_if_full,
                "prod_full_year_kWh": prod_full_year,
                "prod_full_month_kWh": prod_full_month,
                "coverage_full_pct": coverage_full,
                "panels_needed_for_target": panels_needed_for_target,
                "fits_target": fits_target,
                "installed_if_target_kWp": installed_target,
                "prod_target_year_kWh": prod_target_year,
                "coverage_target_pct": coverage_target
            })

        df = pd.DataFrame(options)
        display = df[[
            "name", "Wp", "area_m2", "max_panels_fit", "installed_if_full_kWp",
            "prod_full_month_kWh", "coverage_full_pct", "panels_needed_for_target", "fits_target",
            "installed_if_target_kWp", "coverage_target_pct"
        ]].copy()
        display.columns = [
            "Panel type", "Wp", "Area (m²)", "Max panels that fit", "Installed kWp (if full)",
            "Monthly prod if full (kWh)", "Coverage if full (%)", "Panels needed for target", "Fits target?",
            "Installed kWp (to meet target)", "Coverage if meeting target (%)"
        ]
        # round numeric columns
        for c in ["Installed kWp (if full)", "Monthly prod if full (kWh)", "Coverage if full (%)",
                  "Installed kWp (to meet target)", "Coverage if meeting target (%)"]:
            if c in display.columns:
                display[c] = display[c].map(lambda x: round(x, 2) if pd.notnull(x) else x)

        st.write(f"Effective area: **{effective_area:.2f} m²**")
        st.dataframe(display)

        # Best single option
        best = max(options, key=lambda o: o["coverage_full_pct"] if o["coverage_full_pct"] is not None else -1)
        st.markdown("### Best single-panel option (if you fill roof with this type)")
        st.write(f"- {best['name']}: fits **{best['max_panels_fit']}** panels → installed **{best['installed_if_full_kWp']:.2f} kWp**, "
                 f"monthly **{best['prod_full_month_kWh']:.0f} kWh** ({best['coverage_full_pct']:.1f}% of monthly target)")

        feasible = [o for o in options if o["fits_target"]]
        if feasible:
            st.success("Some panel types can meet the full monthly target within the area:")
            for o in feasible:
                st.write(f"- {o['name']}: needs **{o['panels_needed_for_target']}** panels → installed **{o['installed_if_target_kWp']:.2f} kWp**, "
                         f"monthly **{o['prod_target_year_kWh']/12.0:.0f} kWh** ({o['coverage_target_pct']:.1f}% coverage)")
        else:
            st.warning("No single panel type fits enough panels to meet the monthly target.")

        st.markdown("---")
        st.subheader("Mixed-panel greedy optimizer (fast heuristic)")

        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            if st.button("Optimize for MAX COVERAGE"):
                res_cov = greedy_mixed_optimizer(panel_catalog, effective_area, required_installed_kWp, losses, specific_yield, objective="coverage")
                st.write("Greedy MAX COVERAGE result:")
                st.write(f"- Installed kWp: **{res_cov['installed_kWp']:.2f} kWp**")
                st.write(f"- Monthly production: **{res_cov['monthly_prod_kWh']:.1f} kWh/month**")
                st.write(f"- Area used: **{res_cov['area_used_m2']:.2f} m²**, Panels: **{res_cov['panels_total']}**")
                st.write("Panel breakdown:")
                for c in res_cov["chosen"]:
                    st.write(f"  - {c['name']}: {c['n']} panels ({c['n']*c['Wp']/1000.0:.2f} kWp, {c['n']*c['area']:.2f} m²)")
                # cost & payback
                total_cost = res_cov['installed_kWp'] * 1000.0 * price_per_Wp
                annual_savings = res_cov['annual_prod_kWh'] * electricity_price
                payback_years = total_cost / annual_savings if annual_savings > 0 else float("inf")
                st.write(f"- Estimated system cost: **€{format_currency(total_cost)}**")
                st.write(f"- Estimated annual savings: **€{format_currency(annual_savings)}**")
                st.write(f"- Simple payback: **{payback_years:.1f} years**" if payback_years != float("inf") else "- Payback: not available")
                # download
                out_df = pd.DataFrame([
                    {"panel_type": c["name"], "count": c["n"], "installed_kWp": c["n"]*c["Wp"]/1000.0, "area_m2": c["n"]*c["area"]}
                    for c in res_cov["chosen"]
                ])
                out_df.loc[len(out_df.index)] = ["TOTAL", res_cov["panels_total"], round(res_cov["installed_kWp"],3), round(res_cov["area_used_m2"],3)]
                st.download_button("Download coverage plan (CSV)", out_df.to_csv(index=False).encode("utf-8"), "coverage_plan.csv", "text/csv")

        with col_opt2:
            if st.button("Try to MEET TARGET (greedy)"):
                res_meet = greedy_mixed_optimizer(panel_catalog, effective_area, required_installed_kWp, losses, specific_yield, objective="meet_target")
                # After greedy fill, if installed_kWp < required_installed_kWp try to refine by replacing some panels with smaller ones:
                installed_kwp = res_meet["installed_kWp"]
                if installed_kwp < required_installed_kWp:
                    st.info("Greedy attempt couldn't reach required kWp; trying small-panel substitution to reduce shortfall...")
                    # simple refinement: try removing one large panel and adding as many small panels as possible to increase installed_kWp
                    # Build a flat list of candidate panels by repeating types
                    flat = []
                    for p in panel_catalog:
                        flat.append({"name": p["name"], "Wp": p["Wp"], "area": p["area"]})
                    # Try local search: for each chosen type, try replacing one with small panels if area allows
                    best_local = res_meet
                    shortfall = required_installed_kWp - installed_kwp
                    # quick local improvement loop (limited)
                    for idx in range(len(res_meet["chosen"])):
                        # try remove one panel of this type
                        c = res_meet["chosen"][idx]
                        if c["n"] <= 0:
                            continue
                        # freed area
                        freed = c["area"]
                        # current installed if remove one
                        installed_after_removal = res_meet["installed_kWp"] - c["Wp"]/1000.0
                        # try to fill freed area with best density panels
                        # candidate panels sorted by density
                        candidates = sorted(flat, key=lambda x: (x["Wp"]/x["area"]) if x["area"]>0 else 0.0, reverse=True)
                        new_add = []
                        area_left = freed
                        inst_added = 0.0
                        for cand in candidates:
                            if area_left < cand["area"]:
                                continue
                            can_fit = int(math.floor(area_left / cand["area"]))
                            if can_fit <= 0:
                                continue
                            area_left -= can_fit * cand["area"]
                            inst_added += (can_fit * cand["Wp"] / 1000.0)
                            new_add.append((cand["name"], can_fit))
                        new_installed = installed_after_removal + inst_added
                        if new_installed > best_local["installed_kWp"]:
                            # accept improvement
                            # construct new chosen list
                            new_chosen = [dict(x) for x in res_meet["chosen"]]
                            new_chosen[idx]["n"] -= 1
                            # append new adds
                            for name, cnt in new_add:
                                found = False
                                for nc in new_chosen:
                                    if nc["name"] == name:
                                        nc["n"] += cnt; found = True; break
                                if not found:
                                    # find original panel spec
                                    spec = next((pp for pp in panel_catalog if pp["name"]==name), None)
                                    if spec:
                                        new_chosen.append({"name": spec["name"], "Wp": spec["Wp"], "area": spec["area"], "n": cnt})
                            best_local = {
                                "chosen": new_chosen,
                                "installed_kWp": new_installed,
                                "annual_prod_kWh": new_installed * specific_yield * (1.0 - losses),
                                "monthly_prod_kWh": new_installed * specific_yield * (1.0 - losses) / 12.0,
                                "panels_total": sum(x["n"] for x in new_chosen),
                                "area_used_m2": area_avail - (res_meet["area_remaining_m2"] - area_left),
                                "area_remaining_m2": res_meet["area_remaining_m2"] - area_left
                            }
                    res_meet = best_local

                st.write("Mixed-panel (meet-target heuristic) result:")
                st.write(f"- Installed kWp: **{res_meet['installed_kWp']:.2f} kWp**")
                st.write(f"- Monthly prod: **{res_meet['monthly_prod_kWh']:.1f} kWh/month**")
                st.write(f"- Area used: **{res_meet['area_used_m2']:.2f} m²**, Panels: **{res_meet['panels_total']}**")
                st.write("Panel breakdown:")
                for c in res_meet["chosen"]:
                    st.write(f"  - {c['name']}: {c['n']} panels ({c['n']*c['Wp']/1000.0:.2f} kWp, {c['n']*c['area']:.2f} m²)")
                total_cost = res_meet['installed_kWp'] * 1000.0 * price_per_Wp
                annual_savings = res_meet['annual_prod_kWh'] * electricity_price
                payback = total_cost / annual_savings if annual_savings > 0 else float("inf")
                st.write(f"- Estimated system cost: **€{format_currency(total_cost)}**")
                st.write(f"- Estimated annual savings: **€{format_currency(annual_savings)}**")
                st.write(f"- Simple payback: **{payback:.1f} years**" if payback != float("inf") else "- Payback: not available")
                out_df = pd.DataFrame([
                    {"panel_type": c["name"], "count": c["n"], "installed_kWp": c["n"]*c["Wp"]/1000.0, "area_m2": c["n"]*c["area"]}
                    for c in res_meet["chosen"]
                ])
                out_df.loc[len(out_df.index)] = ["TOTAL", res_meet["panels_total"], round(res_meet["installed_kWp"],3), round(res_meet["area_used_m2"],3)]
                st.download_button("Download mixed-plan (CSV)", out_df.to_csv(index=False).encode("utf-8"), "mixed_plan.csv", "text/csv")

        st.markdown("---")
        st.subheader("Panel preview (grid) & manual partial plan")

        # allow user to pick a single panel type and see grid preview and manual pick
        pick_names = [p["name"] for p in panel_catalog]
        pick = st.selectbox("Pick a panel type to preview & plan manually", pick_names, key="preview_pick")
        spec = next(p for p in panel_catalog if p["name"] == pick)
        # approximate panel footprint: square root of area (best-effort)
        panel_side = math.sqrt(spec["area"])
        # roof dims for preview: if user provided length/width use those otherwise approximate a rectangle from usable_area
        if method == "Length × Width (m)" or (locals().get('length') and locals().get('width')):
            preview_w = length if length else (math.sqrt(usable_area) * 1.5)
            preview_h = width if width else (math.sqrt(usable_area) * 0.8)
        else:
            # estimate rectangle with aspect ratio 1.5
            preview_w = math.sqrt(usable_area) * 1.5
            preview_h = math.sqrt(usable_area) * 0.8

        svg, cols, rows = svg_grid_preview(preview_w, preview_h, panel_side, panel_side)
        st.markdown("**Grid preview (approximate)**")
        st.write(f"Preview roof ≈ {preview_w:.1f} × {preview_h:.1f} m — panel approx {panel_side:.2f} m side")
        st.markdown(svg, unsafe_allow_html=True)

        # manual partial plan
        max_fit = int(math.floor(effective_area / spec["area"]))
        st.write(f"Max {spec['name']} panels that fit (area-based): **{max_fit}**")
        if max_fit > 0:
            n_manual = st.number_input("Choose number of panels to install (manual plan)", min_value=0, max_value=max_fit, value=min(max_fit, 4), step=1)
            n_manual = int(n_manual)
            inst_kw_manual = n_manual * spec["Wp"] / 1000.0
            prod_year_manual = inst_kw_manual * specific_yield * (1.0 - losses)
            prod_month_manual = prod_year_manual / 12.0
            coverage_manual = (prod_month_manual / target_month * 100.0) if target_month > 0 else 0.0
            st.write(f"- Installed: **{inst_kw_manual:.2f} kWp**")
            st.write(f"- Monthly production: **{prod_month_manual:.1f} kWh/month**")
            st.write(f"- Coverage of monthly target: **{coverage_manual:.1f}%**")
            # cost & payback for manual plan
            cost_manual = inst_kw_manual * 1000.0 * price_per_Wp
            savings_manual = prod_year_manual * electricity_price
            payback_manual = cost_manual / savings_manual if savings_manual > 0 else float("inf")
            st.write(f"- Estimated cost: **€{format_currency(cost_manual)}**, annual savings **€{format_currency(savings_manual)}**, simple payback **{payback_manual:.1f} years**" if payback_manual != float("inf") else "- Payback: not available")
            # download manual plan
            plan_df = pd.DataFrame({
                "metric":["panel_type","panels","installed_kWp","monthly_prod_kWh","annual_prod_kWh","coverage_pct","cost_eur"],
                "value":[spec["name"], n_manual, round(inst_kw_manual,3), round(prod_month_manual,2), round(prod_year_manual,1), round(coverage_manual,2), round(cost_manual,2)]
            })
            st.download_button("Download manual plan (CSV)", plan_df.to_csv(index=False).encode("utf-8"), "manual_plan.csv", "text/csv")
        else:
            st.error("No panels of this type fit the available area. Choose a smaller panel or increase area.")

        st.success("Optimization & cost estimates complete.")

# end render()