import math
import requests
import pandas as pd
import streamlit as st 
import numpy as np

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_OK = True
except Exception:
    FOLIUM_OK = False

# Map center and initial coordinates for the user.
LYON_LAT = 45.76
LYON_LON = 4.85
DEFAULT_YIELD = 1200.0 # Standard yield to start the user off

# --- FRANCE FIXED LOCATION
MIN_LAT = 41.0
MAX_LAT = 52.0
MIN_LON = -6.0
MAX_LON = 10.0

# --- Helper Functions ---

def is_within_france(lat, lon):
    """Checks if coordinates are within the approximate bounding box of France."""
    return (MIN_LAT <= lat <= MAX_LAT) and (MIN_LON <= lon <= MAX_LON)

def nominatim(q, limit=5):
    """Searches for an address using OpenStreetMap Nominatim, results focused on France."""
    if not q or len(q) < 3:
        return []
    try:
        # Adding country code 'fr' to limit results to France
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": q, "countrycodes": "fr", "format": "jsonv2", "limit": limit},
                         headers={"User-Agent": "solar-canopy-app"}, timeout=6)
        return [{"name": d["display_name"], "lat": float(d["lat"]), "lon": float(d["lon"])} for d in r.json()]
    except Exception:
        return []


def suggest_tilt(lat):
    """
    Suggests the annual optimal tilt angle based on latitude.
    Annual rule of thumb: Tilt angle is approximately equal to latitude.
    """
    t = abs(lat)
    # Constrain to a practical range: 5 to 60 degrees.
    return max(5.0, min(60.0, t))


# --- Main Render Function ---

def render():
    st.title("☀️ Solar tool ")

    # --- location
    if "lat" not in st.session_state:
        st.session_state.lat = LYON_LAT
        st.session_state.lon = LYON_LON
    
    # --- Initialize state for computation
    if 'computation_done' not in st.session_state:
        st.session_state.computation_done = False
    
    # Set fixed, reliable default yield values
    if 'yearly_per_kw' not in st.session_state:
        st.session_state.yearly_per_kw = DEFAULT_YIELD
    if 'yield_source' not in st.session_state:
        st.session_state.yield_source = "Default"
    
    st.subheader("1) Location (Lyon, France)")
    
    # --- ADDRESS SEARCH ---
    q = st.text_input("Search address (Please enter your location:)", "")
    if q:
        res = nominatim(q)
        for r in res:
            if st.button(r["name"], key=r["name"]):
                new_lat, new_lon = r["lat"], r["lon"]
                
                # Check bounds for search result (safety check)
                if not is_within_france(new_lat, new_lon):
                    st.error("Location found, but it appears outside of metropolitan France. Please choose a location within the French borders.")
                else:
                    st.session_state.lat, st.session_state.lon = new_lat, new_lon
                    st.success("Location selected")
                    st.session_state.computation_done = False
    
    # --- MAP CENTERING ON LYON ---
    if FOLIUM_OK:
        st.write("Click map to select coordinates:")
    
        # Map starts centered on the current lat/lon (Lyon by default)
        m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=14)
    
        # Add a marker for the current selection
        folium.Marker([st.session_state.lat, st.session_state.lon]).add_to(m)
        
        # Set width to 100% and a good height
        out = st_folium(m, width='100%', height=650, returned_objects=["last_clicked"]) 
        
        if out and out.get("last_clicked"):
            lat = out["last_clicked"]["lat"]; lon = out["last_clicked"]["lng"]
            
            # --- VALIDATION CHECK: ENSURE LOCATION IS IN FRANCE ---
            if not is_within_france(lat, lon):
                st.error("⚠️ Location selected is outside of Lyon, France. Please click a location within Lyon.")
                
                # Reset coordinates to Lyon and force rerun to recenter the map
                st.session_state.lat, st.session_state.lon = LYON_LAT, LYON_LON
                st.session_state.computation_done = False
                st.experimental_rerun()
                
            elif (lat != st.session_state.lat) or (lon != st.session_state.lon):
                # Valid change, update coordinates
                st.session_state.lat, st.session_state.lon = float(lat), float(lon)
                st.success(f"Selected {lat:.6f}, {lon:.6f}")
                st.session_state.computation_done = False
    else:
        st.info("Map not available (optional packages missing). Enter coordinates manually.")
        
        new_lat = st.number_input("Latitude", value=float(st.session_state.lat), format="%.6f", key="input_lat")
        new_lon = st.number_input("Longitude", value=float(st.session_state.lon), format="%.6f", key="input_lon")

        # Manual input validation
        if not is_within_france(new_lat, new_lon):
            st.error("Coordinates are outside of France.")
            
        elif (new_lat != st.session_state.lat) or (new_lon != st.session_state.lon):
            st.session_state.lat = new_lat
            st.session_state.lon = new_lon
            st.session_state.computation_done = False


    st.markdown("---")

    # --- roof & demand
    st.subheader("2) Roof & demand")
    left, right = st.columns(2)
    with left:
        method = st.radio("Roof input", ("Length × Width", "Usable area (m²)"))
        if method == "Length × Width":
            length = st.number_input("Length (m)", value=8.0, min_value=0.5, step=0.1, format="%.2f")
            width = st.number_input("Width (m)", value=6.0, min_value=0.5, step=0.1, format="%.2f")
            usable = float(length * width)
            st.write(f"Area: **{usable:.1f} m²**")
        else:
            usable = st.number_input("Usable area (m²)", value=40.0, min_value=0.1, step=0.5, format="%.2f")
        packing_pct = st.slider("Packing efficiency (%)", min_value=50, max_value=95, value=75)
        eff_area = usable * (packing_pct / 100.0)
        st.write(f"Effective area: **{eff_area:.2f} m²**")
    with right:
        monthly = st.number_input("Monthly target (kWh/month)", value=150.0, min_value=0.0, step=1.0, format="%.1f")
        losses_pct = st.slider("System losses (%)", 5, 30, 14)
        
        # Tilt calculation is kept as it is based only on latitude
        tilt = suggest_tilt(st.session_state.lat)
        st.write(f"Suggested annual tilt (based on selected latitude): **{tilt:.1f}°**")

    st.markdown("---")
    
    # panel catalog
    catalog = [
        {"name": "400W", "Wp": 400.0, "area": 2.0},
        {"name": "330W", "Wp": 330.0, "area": 1.7},
        {"name": "275W", "Wp": 275.0, "area": 1.6},
        {"name": "200W", "Wp": 200.0, "area": 1.2},
        {"name": "100W", "Wp": 100.0, "area": 0.6},
        {"name": "50W",  "Wp": 50.0,  "area": 0.3},
    ]

    st.subheader("3) Compute")
    
    # --- Manual Yield Input Section ---
    st.info(f"Using a general calculation (no external API). Default yield set to **{DEFAULT_YIELD:.1f} kWh/kWp/yr**.")
    
    old_yearly_per_kw = st.session_state.yearly_per_kw
    
    st.session_state.yearly_per_kw = st.number_input(
        "Specific yield (kWh/kWp/year)", 
        value=st.session_state.yearly_per_kw, 
        min_value=200.0, 
        step=10.0, 
        format="%.1f",
        key="manual_yield_input"
    )
    
    if old_yearly_per_kw != st.session_state.yearly_per_kw:
        st.session_state.yield_source = "Manual"
        st.session_state.computation_done = False

    # Compute button logic
    if st.button("Compute"):
        if st.session_state.yearly_per_kw <= 0:
            st.error("Please enter a valid Specific Yield (> 0).")
            st.session_state.computation_done = False
        else:
            if st.session_state.yield_source == "Default":
                st.session_state.yield_source = f"Default Value ({DEFAULT_YIELD})"

            st.success("Computation finished using user-defined specific yield value.")
            st.session_state.computation_done = True
        
    # --- Results Display Section ---
    if st.session_state.computation_done:
        
        yearly_per_kw = st.session_state.yearly_per_kw
        monthly_per_kw = yearly_per_kw / 12.0
        losses = losses_pct / 100.0
        
        st.success(f"Site yield ≈ **{yearly_per_kw:.0f}** kWh/kWp/yr (Source: {st.session_state.yield_source})")
        st.info(f"Equivalent monthly yield: **{monthly_per_kw:.1f}** kWh/kWp/month")

        required_kWp = monthly * 12.0 / (yearly_per_kw * (1.0 - losses)) if yearly_per_kw > 0 else float("inf")
        st.markdown(f"**Required installed (incl. {losses_pct}% losses):** **{required_kWp:.2f} kWp**")

        # Calculation of panels and results dataframe
        rows = []
        for p in catalog:
            max_fit = int(math.floor(eff_area / p["area"])) if p["area"] > 0 else 0
            installed_if_full = max_fit * p["Wp"] / 1000.0
            prod_month_full = installed_if_full * monthly_per_kw * (1.0 - losses)
            panels_needed = int(math.ceil(required_kWp * 1000.0 / p["Wp"])) if p["Wp"] > 0 else 10**9
            fits = panels_needed <= max_fit
            rows.append({
                "type": p["name"], "Wp": p["Wp"], "area_m2": p["area"], "max_fit": max_fit,
                "installed_kWp_if_full": round(installed_if_full, 2), "monthly_prod_if_full": round(prod_month_full, 1),
                "coverage_if_full_pct": round(prod_month_full / monthly * 100.0, 1) if monthly > 0 else 0.0,
                "panels_needed_for_target": panels_needed, "fits_target": fits
            })
        df = pd.DataFrame(rows)
        st.dataframe(df)
        
        # Ensure best calculation is safe
        if rows:
            best = max(rows, key=lambda r: r["coverage_if_full_pct"])
            st.markdown(f"**Best single-panel when filling roof:** {best['type']} — coverage {best['coverage_if_full_pct']}%")

        # partial plan
        st.markdown("---")
        st.subheader("Partial install")
        pick = st.selectbox("Pick panel type", [p["name"] for p in catalog], key="panel_type_picker")
        spec = next(p for p in catalog if p["name"] == pick)
        max_fit = int(math.floor(eff_area / spec["area"])) if spec["area"] > 0 else 0
        st.write(f"Max that fit: {max_fit} pcs")
        if max_fit > 0:
            n = st.number_input("Number to install", min_value=0, max_value=max_fit, value=min(max_fit, 4), step=1, format="%d", key="num_panels_to_install")
            n = int(n)
            inst_kw = n * spec["Wp"] / 1000.0
            prod_year = inst_kw * yearly_per_kw * (1.0 - losses)
            prod_month = prod_year / 12.0
            st.write(f"- Installed: **{inst_kw:.2f} kWp**, monthly est: **{prod_month:.1f} kWh**, covers **{prod_month/monthly*100.0:.1f}%**")
            out = pd.DataFrame([{"metric": "panel_type", "value": spec["name"]},
                                {"metric": "panels", "value": n},
                                {"metric": "installed_kWp", "value": round(inst_kw, 3)},
                                {"metric": "monthly_prod_kWh", "value": round(prod_month, 2)}])
            st.download_button("Download partial plan (CSV)", out.to_csv(index=False).encode("utf-8"), "partial_plan.csv", "text/csv")
        else:
            st.error("No panels of that type fit the effective area.")

        # summary download
        summary = pd.DataFrame({
            "metric": ["required_kWp", "effective_area_m2", "tilt_deg_suggested", "losses_pct", "site_yearly_kWh_per_kWp", "yield_source"],
            "value": [round(required_kWp, 3), round(eff_area, 3), round(tilt, 1), losses_pct, round(yearly_per_kw, 1), st.session_state.yield_source]
        })
        st.download_button("Download summary (CSV)", summary.to_csv(index=False).encode("utf-8"), "summary.csv", "text/csv")


if __name__ == "__main__":
    render()
