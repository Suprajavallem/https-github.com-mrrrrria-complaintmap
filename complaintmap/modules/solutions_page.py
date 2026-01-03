import streamlit as st
import pandas as pd

# --------------------------------------------------
# NORMALIZATION LAYER
# Converts French / mixed inputs → English standard
# --------------------------------------------------
def normalize_issue(raw_type):
    if not isinstance(raw_type, str):
        return "Other"

    t = raw_type.strip().lower()

    mapping = {
        # French → English
        "air": "Air quality",
        "chaleur": "Heat",
        "bruit": "Noise",
        "mobilité": "Cycling / Walking",
        "mobilite": "Cycling / Walking",
        "odeur": "Odor",

        # English (already acceptable)
        "heat": "Heat",
        "noise": "Noise",
        "air quality": "Air quality",
        "odor": "Odor",
        "cycling / walking": "Cycling / Walking",
        "mobility": "Cycling / Walking"
    }

    return mapping.get(t, "Other")


# --------------------------------------------------
# SOLUTION DATABASE (ENGLISH ONLY)
# --------------------------------------------------
SOLUTIONS = {
    "Heat": [
        "Planting trees and increasing urban greenery",
        "Solar canopies for shading public spaces",
        "Cool roofs and reflective materials",
        "Shaded pedestrian corridors"
    ],
    "Noise": [
        "Low-noise road surfaces",
        "Traffic calming measures",
        "Sound barriers near main roads",
        "Restricted traffic hours"
    ],
    "Air quality": [
        "Low-emission zones",
        "Encouraging public transport use",
        "Green buffers along roads",
        "Monitoring air pollution levels"
    ],
    "Cycling / Walking": [
        "Protected cycling lanes",
        "Wider and safer sidewalks",
        "Reduced car lanes in city centers",
        "Improved street lighting"
    ],
    "Odor": [
        "Improved waste management",
        "Industrial odor monitoring",
        "Better sewage ventilation",
        "Regular inspection of facilities"
    ],
    "Other": [
        "Further investigation required",
        "Field surveys and citizen feedback"
    ]
}


# --------------------------------------------------
# MAIN RENDER FUNCTION
# --------------------------------------------------
def render():
    st.title("💡 Urban Solutions & Recommendations")

    st.markdown(
        """
        This page suggests **urban solutions** based on the types of problems
        reported by citizens.  
        The goal is to support **data-driven decision-making** in smart cities.
        """
    )

    # --------------------------------------------------
    # LOAD COMPLAINT DATA
    # --------------------------------------------------
    try:
        df = pd.read_csv("data/complaints.csv")
    except Exception:
        st.error("No complaint data found.")
        return

    if df.empty or "type" not in df.columns:
        st.warning("No valid complaint data available.")
        return

    # --------------------------------------------------
    # NORMALIZE ISSUE TYPES
    # --------------------------------------------------
    df["issue"] = df["type"].apply(normalize_issue)

    # --------------------------------------------------
    # ISSUE SELECTION
    # --------------------------------------------------
    st.subheader("Select an issue type")

    issues = sorted(df["issue"].unique())
    selected_issue = st.selectbox("Urban issue", issues)

    # --------------------------------------------------
    # DISPLAY STATISTICS
    # --------------------------------------------------
    issue_count = df[df["issue"] == selected_issue].shape[0]
    st.info(f"Number of reported cases: **{issue_count}**")

    # --------------------------------------------------
    # DISPLAY SOLUTIONS
    # --------------------------------------------------
    st.subheader("Recommended solutions")

    solutions = SOLUTIONS.get(selected_issue, SOLUTIONS["Other"])
    for s in solutions:
        st.markdown(f"- {s}")

    # --------------------------------------------------
    # SMART CITY CONTEXT
    # --------------------------------------------------
    st.markdown("---")
    st.subheader("Why these solutions?")

    st.markdown(
        """
        These recommendations are inspired by **Smart City practices** and aim to:

        - Improve quality of life  
        - Reduce environmental impact  
        - Encourage sustainable mobility  
        - Support evidence-based urban planning  

        They show how **citizen-reported data** can be translated into
        **concrete urban actions**.
        """
    )


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------
if __name__ == "__main__":
    render()
