import streamlit as st
import pandas as pd

# ==================================================
# NORMALIZATION FUNCTION
# Converts French / mixed issue labels to English
# ==================================================
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

        # English (already OK)
        "heat": "Heat",
        "noise": "Noise",
        "air quality": "Air quality",
        "odor": "Odor",
        "cycling / walking": "Cycling / Walking",
        "mobility": "Cycling / Walking"
    }

    return mapping.get(t, "Other")


# ==================================================
# SOLUTION KNOWLEDGE BASE (ENGLISH STANDARD)
# ==================================================
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
        "Sound barriers near major roads",
        "Restricted traffic hours"
    ],
    "Air quality": [
        "Low-emission zones",
        "Encouraging public transport use",
        "Green buffers along roads",
        "Continuous air-quality monitoring"
    ],
    "Cycling / Walking": [
        "Protected cycling lanes",
        "Wider and safer sidewalks",
        "Traffic reduction in city centers",
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
        "On-site surveys and citizen feedback"
    ]
}


# ==================================================
# MAIN RENDER FUNCTION
# Called from app.py as: solutions_page.render(df_all)
# ==================================================
def render(df):
    st.title("💡 Urban Solutions & Recommendations")

    st.markdown(
        """
        This page proposes **urban solutions** based on the types of problems
        reported by citizens.  
        It illustrates how **participatory data** can support
        **Smart City decision-making**.
        """
    )

    # --------------------------------------------------
    # BASIC DATA VALIDATION
    # --------------------------------------------------
    if df is None or df.empty:
        st.warning("No complaint data available.")
        return

    # --------------------------------------------------
    # DETECT ISSUE COLUMN (CRITICAL FIX)
    # --------------------------------------------------
    possible_cols = ["type", "category", "issue", "problem", "complaint_type"]
    issue_col = None

    for col in possible_cols:
        if col in df.columns:
            issue_col = col
            break

    if issue_col is None:
        st.error(
            "No complaint category column found.\n\n"
            "Expected one of: type, category, issue, problem, complaint_type."
        )
        st.write("Available columns:", list(df.columns))
        return

    # --------------------------------------------------
    # NORMALIZE ISSUE TYPES
    # --------------------------------------------------
    df = df.copy()
    df["issue"] = df[issue_col].apply(normalize_issue)

    # --------------------------------------------------
    # ISSUE SELECTION UI
    # --------------------------------------------------
    st.subheader("Select an issue type")

    issues = sorted(df["issue"].unique())
    selected_issue = st.selectbox("Urban issue", issues)

    # --------------------------------------------------
    # STATISTICS
    # --------------------------------------------------
    count = df[df["issue"] == selected_issue].shape[0]
    st.info(f"Number of reported cases: **{count}**")

    # --------------------------------------------------
    # DISPLAY SOLUTIONS
    # --------------------------------------------------
    st.subheader("Recommended solutions")

    solutions = SOLUTIONS.get(selected_issue, SOLUTIONS["Other"])
    for sol in solutions:
        st.markdown(f"- {sol}")

    # --------------------------------------------------
    # SMART CITY CONTEXT
    # --------------------------------------------------
    st.markdown("---")
    st.subheader("Smart City perspective")

    st.markdown(
        """
        These solutions are inspired by **Smart City best practices**.

        They demonstrate how:
        - Citizen-reported problems can be structured and analyzed
        - Urban challenges can be translated into concrete actions
        - Data-driven tools can support city planners and decision-makers
        """
    )


# ==================================================
# LOCAL TESTING (optional)
# ==================================================
if __name__ == "__main__":
    st.warning("This page is intended to be called from app.py with a DataFrame.")
