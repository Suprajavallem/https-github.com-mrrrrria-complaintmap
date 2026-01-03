import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd


# =========================================================
# COLUMN AUTO-DETECTION (ROBUST)
# =========================================================
def detect_column(df, possible_names):
    for col in possible_names:
        if col in df.columns:
            return col
    return None


# =========================================================
# NORMALIZE ISSUE NAMES (FRENCH → ENGLISH)
# =========================================================
def normalize_issue(raw_type):
    if not isinstance(raw_type, str):
        return "Other"

    t = raw_type.strip().lower()
    if t == "air":
        return "Air"
    if t == "chaleur":
        return "Heat"
    if t == "bruit":
        return "Noise"
    if t == "odeur":
        return "Odour"

    return raw_type.capitalize()


# =========================================================
# SOLUTION GENERATION LOGIC
# =========================================================
def get_solution(issue, intensity, variant_index):
    intensity = int(intensity)

    if issue == "Air":
        solutions = (
            [
                "Monitor air quality regularly and inform residents about pollution levels.",
                "Encourage reduced car usage and promote public transport or cycling."
            ]
            if intensity <= 3 else
            [
                "Restrict high-emission vehicles in the affected area during peak hours.",
                "Create urban green buffer zones to help absorb air pollutants.",
                "Introduce low-emission or electric-vehicle priority zones."
            ]
        )

    elif issue == "Heat":
        solutions = (
            [
                "Increase tree planting and shaded areas to reduce local heat exposure.",
                "Install shaded public seating and pedestrian shelters."
            ]
            if intensity <= 3 else
            [
                "Apply cool-roof technologies to reduce indoor and outdoor temperatures.",
                "Use heat-reflective materials for pavements and road surfaces.",
                "Redesign public spaces to improve airflow and reduce heat accumulation."
            ]
        )

    elif issue == "Noise":
        solutions = (
            [
                "Increase monitoring of noise levels and enforce existing regulations.",
                "Raise public awareness about noise pollution and its impacts."
            ]
            if intensity <= 3 else
            [
                "Install noise barriers along major roads or sensitive areas.",
                "Restrict heavy vehicle traffic during night-time hours.",
                "Implement speed limits and traffic calming measures."
            ]
        )

    elif issue == "Odour":
        solutions = (
            [
                "Inspect waste collection and sanitation practices in the area.",
                "Ensure regular cleaning and maintenance of nearby facilities."
            ]
            if intensity <= 3 else
            [
                "Improve waste management systems and enforce disposal regulations.",
                "Install odor treatment or filtering systems near the source."
            ]
        )

    else:
        solutions = ["Further assessment and monitoring of the reported issue is recommended."]

    return solutions[variant_index % len(solutions)]


# =========================================================
# MAIN RENDER FUNCTION
# =========================================================
def render(df_all: pd.DataFrame):
    st.title("🗺️ Smart Complaint Solution Map")
    st.markdown(
        "<h4 style='color: gray; margin-top: -10px;'>Proposed Solutions</h4>",
        unsafe_allow_html=True
    )

    if df_all is None or df_all.empty:
        st.warning("No complaint data available.")
        return

    df = df_all.copy()

    # --------------------------------------------------
    # AUTO-DETECT REQUIRED COLUMNS
    # --------------------------------------------------
    issue_col = detect_column(df, ["type", "categorie", "category", "probleme", "issue"])
    lat_col = detect_column(df, ["lat", "latitude"])
    lon_col = detect_column(df, ["lon", "longitude"])
    intensity_col = detect_column(df, ["intensite", "intensity"])
    date_col = detect_column(df, ["date_heure", "date", "timestamp"])

    if not all([issue_col, lat_col, lon_col, intensity_col, date_col]):
        st.error("Required columns not found in the complaint data.")
        st.write("Available columns:", df.columns.tolist())
        return

    # --------------------------------------------------
    # NORMALIZE DATA
    # --------------------------------------------------
    df["issue"] = df[issue_col].apply(normalize_issue)
    df["intensity"] = df[intensity_col].apply(lambda x: int(x) if int(x) > 0 else 1)

    # --------------------------------------------------
    # ISSUE FILTER
    # --------------------------------------------------
    issue_list = ["All"] + sorted(df["issue"].unique().tolist())
    selected_issue = st.selectbox("Reported Issue", issue_list)

    if selected_issue != "All":
        df = df[df["issue"] == selected_issue]

    if df.empty:
        st.info("No complaints found for the selected issue.")
        return

    # --------------------------------------------------
    # GROUP DATA (LATEST PER LOCATION & ISSUE)
    # --------------------------------------------------
    df_sorted = df.sort_values(date_col)

    grouped = (
        df_sorted
        .groupby([lat_col, lon_col, "issue"], as_index=False)
        .last()
    )

    latest_time = grouped[date_col].max()
    latest_row = grouped.loc[grouped[date_col].idxmax()]

    # --------------------------------------------------
    # MAP INITIALIZATION
    # --------------------------------------------------
    m = folium.Map(
        location=[latest_row[lat_col], latest_row[lon_col]],
        zoom_start=14
    )

    HeatMap(
        grouped[[lat_col, lon_col]].values.tolist(),
        radius=25,
        blur=18
    ).add_to(m)

    # --------------------------------------------------
    # ADD MARKERS
    # --------------------------------------------------
    for idx, row in grouped.iterrows():
        solution = get_solution(row["issue"], row["intensity"], idx)
        marker_color = "red" if row[date_col] == latest_time else "blue"

        popup_html = f"""
        <div style="width:330px; font-family:Arial; border-radius:12px; overflow:hidden;">
            <div style="background:#f2f2f2; padding:12px;">
                <b>Reported Issue:</b> {row['issue']}<br>
                <b>Intensity:</b> {row['intensity']}
            </div>
            <div style="background:#ffffff; padding:14px;">
                <b>Proposed Solution:</b><br><br>
                {solution}
            </div>
        </div>
        """

        folium.Marker(
            location=[row[lat_col], row[lon_col]],
            popup=popup_html,
            icon=folium.Icon(color=marker_color, icon="info-sign")
        ).add_to(m)

    st_folium(m, width=1400, height=650)

    # --------------------------------------------------
    # CURRENT REPORTED SOLUTION (BELOW MAP)
    # --------------------------------------------------
    st.subheader("📌 Current Reported Solution")

    current_solution = get_solution(
        latest_row["issue"],
        latest_row["intensity"],
        0
    )

    st.markdown(
        f"""
        <div style="background:#ffffff; padding:20px; border-radius:12px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.1); margin-top:10px;">
            <div style="background:#f2f2f2; padding:12px; border-radius:8px;">
                <b>Reported Issue:</b> {latest_row['issue']}<br>
                <b>Intensity:</b> {latest_row['intensity']}
            </div>
            <div style="margin-top:12px;">
                <b>Recommended Solution:</b><br><br>
                {current_solution}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
