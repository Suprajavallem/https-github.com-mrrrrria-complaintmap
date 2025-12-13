import os
from datetime import datetime

import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium

from config import (
    setup,
    DEFAULT_LAT,
    DEFAULT_LON,
    DEFAULT_ZOOM,
    UPLOAD_DIR,
    COLOR_MAP,
)
from db import init_db, load_complaints, add_complaint

# Import pages from the "modules" folder
from modules import (
    map_heatmap,
    statistics_page,
    solutions_page,
    air_heatmap_page,
    solar_canopy,
    about_page,
)

# --------------------------------------------------------------------
# GLOBAL STYLES
# --------------------------------------------------------------------

def apply_global_style():
    """Apply global CSS styles for the layout, colors and banner."""
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #f1ffe8;
            padding-top: 4.5rem;
        }

        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0);
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #e1f5dd;
            border-right: 1px solid #c4e4be;
            margin-top: 4.5rem !important;
        }

        /* Top banner */
        .top-banner {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background-color: #d5f5c8;
            padding: 0.75rem 2rem;
            border-bottom: 1px solid #b9e6ae;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        }

        .top-banner-title {
            margin: 0;
            font-size: 1.6rem;
        }

        .top-banner-subtitle {
            margin: 0.1rem 0 0 0;
            font-size: 0.95rem;
        }

        /* Report card box */
        .report-card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            border: 1px solid #cfe7c7;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-top: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_banner():
    """Display a fixed banner at the top of the app."""
    st.markdown(
        """
        <div class="top-banner">
            <h1 class="top-banner-title">🌱 Smart Complaint Map</h1>
            <p class="top-banner-subtitle">
                A citizen-powered platform to map urban environmental issues
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------
# MAIN REPORT PAGE (MAP + COMPLAINT FORM)
# --------------------------------------------------------------------

def render_report_home():
    """Main home page: interactive map on the left and reporting form on the right."""
    st.subheader("🗺️ Report an issue on the map")

    df_all = load_complaints()
    clicked = st.session_state.get("clicked_location", None)

    # Default map center
    center = [DEFAULT_LAT, DEFAULT_LON]
    if not df_all.empty:
        center = [df_all["lat"].mean(), df_all["lon"].mean()]

    # Initialize the Folium map
    m = folium.Map(location=center, zoom_start=DEFAULT_ZOOM)

    # Display previous complaints
    if not df_all.empty:
        cluster = MarkerCluster().add_to(m)
        for _, row in df_all.iterrows():
            color = COLOR_MAP.get(row["issue_type"], "#5c7cfa")
            popup_text = (
                f"{row['issue_type']} (Intensity {row['intensity']})"
                f"<br>{row['description'] or ''}"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=5,
                color=color,
                fill=True,
                fill_opacity=0.8,
                popup=popup_text,
            ).add_to(cluster)

    # Display marker at the clicked position
    if clicked is not None:
        folium.Marker(
            location=[clicked["lat"], clicked["lon"]],
            popup="New issue here",
            icon=folium.Icon(color="green", icon="plus"),
        ).add_to(m)

    # Streamlit layout
    left, right = st.columns([2.5, 1])

    with left:
        st.write("Click on the map to select the issue location:")
        map_data = st_folium(m, width=750, height=550)

    # Update clicked position
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.session_state["clicked_location"] = {"lat": lat, "lon": lon}
        clicked = st.session_state["clicked_location"]

    # Right panel: form
    with right:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)

        if clicked is None:
            st.info("Click a location on the map to start reporting an issue.")
        else:
            st.markdown("### 📍 Report an issue")

            st.markdown(
                f"**Selected position:** `lat = {clicked['lat']:.5f}`, "
                f"`lon = {clicked['lon']:.5f}`"
            )

            ISSUE_TYPES = [
                "Air quality",
                "Noise",
                "Heat",
                "Cycling / Walking",
                "Odor",
                "Other",
            ]

            col1, col2 = st.columns(2)

            with col1:
                issue_type = st.selectbox(
                "Issue type",
                ISSUE_TYPES,
                key="issue_type_home",
            )

                intensity = st.slider(
                    "Perceived intensity (1 = low, 5 = high)",
                    1,
                    5,
                    3,
                    key="intensity_home",
                )

            with col2:
                description = st.text_area(
                    "Description (optional)",
                    placeholder="Example: strong odor, heavy traffic, loud engines…",
                    key="description_home",
                )

                photo_file = st.file_uploader(
                    "Upload a photo (optional)",
                    type=["png", "jpg", "jpeg"],
                    key="photo_home",
                )

            c1, c2 = st.columns(2)

            with c1:
                cancel = st.button("❌ Cancel / choose another location")
            with c2:
                submit = st.button("✅ Submit report")

            # Cancel
            if cancel:
                st.session_state["clicked_location"] = None
                st.experimental_rerun()

            # Submit
            if submit:
                lat = clicked["lat"]
                lon = clicked["lon"]

                photo_path = None
                if photo_file is not None:
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{ts}_{photo_file.name}"
                    save_path = os.path.join(UPLOAD_DIR, filename)
                    with open(save_path, "wb") as f:
                        f.write(photo_file.getbuffer())
                    photo_path = save_path

                add_complaint(
                    issue_type,
                    intensity,
                    lat,
                    lon,
                    description,
                    photo_path,
                )

                st.success("Thank you! Your report has been submitted. ✅")
                st.session_state["clicked_location"] = None

        st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------
# MAIN APP
# --------------------------------------------------------------------

def main():
    setup()
    init_db()

    apply_global_style()
    render_banner()

    # ---------------- SIDEBAR NAVIGATION ---------------- #
    st.sidebar.markdown("## 🌿 Menu")

    pages = {
        "🏠 Report": "home",
        "Map & Heatmap": "map",
        "Statistics": "stats",
        "Proposed solutions": "solutions",
        "Air heatmap": "air",
        "Solar canopy": "solar",
        "About": "about",
    }

    choice = st.sidebar.radio("Go to", list(pages.keys()))
    page_key = pages[choice]

    # ---------------- PAGE RENDERING ---------------- #
    if page_key == "home":
        render_report_home()

    else:
        df_all = load_complaints()

        if page_key == "map":
            map_heatmap.render(df_all)
        elif page_key == "stats":
            statistics_page.render(df_all)
        elif page_key == "solutions":
            solutions_page.render(df_all)
        elif page_key == "air":
            air_heatmap_page.render()
        elif page_key == "solar":
            solar_canopy.render()
        elif page_key == "about":
            about_page.render()
        else:
            st.error("Unknown page selected.")


if __name__ == "__main__":
    main()

# streamlit run /Users/maria/Desktop/complaintmap/app.py
