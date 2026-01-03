import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import numpy as np

# UI STYLING

st.markdown(
    """
    <style>
        div[data-baseweb="select"] > div {
            width: 520px !important;
        }
        .solution-card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.1);
        }
        .solution-header {
            background-color: #f2f2f2;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True
)
# NORMALIZE ISSUE NAMES
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

# DESCRIPTIVE + VARIED SOLUTION LOGIC

def get_solution(issue, intensity, variant_index):
    intensity = int(intensity)

    if issue == "Air":
        solutions = (
            [
                "Conduct regular air quality monitoring in the locality and share pollution data with residents to encourage cleaner practices.",
                "Install temporary air quality sensors near roads and public areas to identify minor pollution sources.",
                "Organize public awareness programs to promote reduced vehicle usage and eco-friendly transportation."
            ]
            if intensity <= 3
            else [
                "Implement electric-vehicle-only zones in high-traffic areas to reduce emissions from conventional vehicles.",
                "Restrict the movement of high-emission vehicles during peak hours and enforce stricter pollution norms.",
                "Develop urban green buffer zones using trees and vegetation to absorb pollutants and improve air quality.",
                "Install permanent air quality monitoring stations for continuous pollution tracking and policy planning."
            ]
        )

    elif issue == "Heat":
        solutions = (
            [
                "Increase tree plantation along streets and public spaces to provide natural shade and cooling.",
                "Add shaded walkways, bus stops, and resting areas to protect pedestrians from direct heat exposure.",
                "Promote community awareness programs on heat safety and preventive measures during hot weather."
            ]
            if intensity <= 3
            else [
                "Apply cool roof technology on buildings to reflect sunlight and reduce indoor temperatures.",
                "Use heat-reflective materials on roads and pavements to minimize heat absorption.",
                "Redesign open urban spaces with greenery and water features to reduce the overall heat island effect."
            ]
        )

    elif issue == "Noise":
        solutions = (
            [
                "Issue noise regulation notices and ensure compliance with permissible sound limits.",
                "Conduct periodic noise level monitoring in residential and commercial zones.",
                "Run public awareness campaigns to educate citizens about noise pollution and its impacts."
            ]
            if intensity <= 3
            else [
                "Install permanent noise barriers along roadsides and residential boundaries to reduce traffic noise.",
                "Enforce strict speed limits and regulate heavy vehicle movement in sensitive areas.",
                "Divert heavy traffic away from residential zones through alternate routes and traffic planning."
            ]
        )

    elif issue == "Odour":
        solutions = (
            [
                "Inspect nearby waste disposal sites regularly to identify sources of unpleasant odours.",
                "Increase sanitation monitoring and ensure timely waste collection in affected areas."
            ]
            if intensity <= 3
            else [
                "Implement strict waste management controls and enforce penalties for improper disposal.",
                "Install odor neutralization and treatment systems near waste processing and sewage facilities."
            ]
        )

    else:
        solutions = ["Conduct routine monitoring and assessment of the reported issue."]

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
    df["issue"] = df["type"].apply(normalize_issue)

    issue_categories = ["All"] + sorted(df["issue"].unique().tolist())
    selected_issue = st.selectbox("Reported Issue", issue_categories)

    if selected_issue != "All":
        df = df[df["issue"] == selected_issue]

    if df.empty:
        st.info("No complaints found for selected issue.")
        return

    required_cols = ["lat", "lon", "intensite", "date_heure"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            return

    df_sorted = df.sort_values("date_heure")

    grouped = (
        df_sorted
        .groupby(["lat", "lon", "issue"], as_index=False)
        .last()
    )

    grouped["intensity"] = grouped["intensite"].apply(
        lambda x: int(x) if int(x) > 0 else 1
    )

    latest_time = grouped["date_heure"].max()
    latest_row = grouped.loc[grouped["date_heure"].idxmax()]

    # ---------------- MAP ----------------
    m = folium.Map(
        location=[latest_row["lat"], latest_row["lon"]],
        zoom_start=14
    )

    HeatMap(
        grouped[["lat", "lon"]].values.tolist(),
        radius=25,
        blur=18
    ).add_to(m)

    for idx, row in grouped.iterrows():
        solution = get_solution(row["issue"], row["intensity"], idx)
        color = "red" if row["date_heure"] == latest_time else "blue"

        popup_html = f"""
        <div style="width: 330px; font-family: Arial; border-radius: 12px; overflow: hidden;">
            <div style="background:#f2f2f2; padding:12px;">
                <b>Reported Issue :</b> {row['issue']}<br>
                <b>Intensity :</b> {row['intensity']}
            </div>
            <div style="background:#fff; padding:14px;">
                <b>Solution :</b><br>{solution}
            </div>
        </div>
        """

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=popup_html,
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    st_folium(m, width=1400, height=650)

    # ---------------- CURRENT SOLUTION BELOW MAP ----------------
    st.subheader("📌 Current Reported Solution")

    current_solution = get_solution(
        latest_row["issue"],
        latest_row["intensity"],
        0
    )

    st.markdown(
        f"""
        <div class="solution-card">
            <div class="solution-header">
                <b>Reported Issue :</b> {latest_row['issue']}<br>
                <b>Intensity :</b> {latest_row['intensity']}
            </div>
            <div>
                <b>Recommended Solution :</b><br><br>
                {current_solution}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
