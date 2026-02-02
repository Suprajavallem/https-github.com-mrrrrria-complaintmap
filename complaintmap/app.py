import os
from datetime import datetime
import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium
import urllib.parse
import requests

# ---------------------------------------------------------
# PAGE CONFIG (must be first)
# ---------------------------------------------------------
st.set_page_config(layout="wide")

from modules import (
    solution_heat_map,
    statistics_page,
    air_heatmap_page,
    about_page,
)
from config import (
    setup,
    DEFAULT_LAT,
    DEFAULT_LON,
    DEFAULT_ZOOM,
    UPLOAD_DIR,
    COLOR_MAP,
)
from db import init_db, load_complaints, add_complaint

from modules import (
    solution_heat_map, # <--- New file name (without .py)
    statistics_page,
    air_heatmap_page,
    about_page,
)

# ---------------------------------------------------------
# AUTHORITY CONTACTS (Hyderabad)
# ---------------------------------------------------------
AUTHORITY_CONTACTS = {
    "Air quality": {
        "dept": "Telangana Pollution Control Board",
        "email": "pcb@telangana.gov.in",
        "phone": "040-23887500",
    },
    "Noise": {
        "dept": "Hyderabad Traffic Police",
        "email": "trafficpolice@hyderabad.gov.in",
        "phone": "100",
    },
    "Heat": {
        "dept": "GHMC – Environment Wing",
        "email": "environment-ghmc@telangana.gov.in",
        "phone": "040-21111111",
    },
    "Cycling / Walking": {
        "dept": "GHMC – Urban Planning",
        "email": "planning-ghmc@telangana.gov.in",
        "phone": "040-21111111",
    },
    "Odor": {
        "dept": "GHMC – Sanitation",
        "email": "sanitation-ghmc@telangana.gov.in",
        "phone": "040-21111111",
    },
    "Other": {
        "dept": "Greater Hyderabad Municipal Corporation",
        "email": "info.ghmc@telangana.gov.in",
        "phone": "040-21111111",
    },
}

# ---------------------------------------------------------
# GLOBAL STYLE
# ---------------------------------------------------------
def apply_global_style():
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"] {
            height: 0px;
            visibility: hidden;
        }

        [data-testid="stAppViewContainer"] {
            background-color: #f1ffe8;
            /* Reduced from 10rem to 8.5rem to bring content closer to banner */
            padding-top: 7.5rem; 
        }

        [data-testid="stSidebar"] {
            background-color: #e1f5dd;
            border-right: 1px solid #c4e4be;
        }

        /* Shifted upward by reducing padding-top from 10rem to 7.5rem */
        [data-testid="stSidebarContent"] {
            padding-top: 6.0rem !important;
        }

        /* Increase font size for the sidebar radio labels */
        [data-testid="stWidgetLabel"] p {
            font-size: 1.4rem !important;
            font-weight: 600 !important;
            color: #2e4a2e !important;
        }
        
        /* Increase font size for the radio button options specifically */
        div[data-testid="stRadio"] label {
            font-size: 1.4rem !important;
        }

        .top-banner {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 999999;
            background-color: #d5f5c8;
            padding: 0.75rem 2rem;
            border-bottom: 1px solid #b9e6ae;
            height: 10rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .top-banner h1 {
            margin: 0;
            padding: 0;
            line-height: 1.1;
            font-size: 3.2rem;
            color: #2e4a2e;
            font-weight: 800;
        }

        .top-banner p {st
            margin: 5px 0 0 0;
            padding: 0;
            font-size: 1.2rem;
            color: #444;
        }

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
    st.markdown(
        """
        <div class="top-banner">
            <h1>🌱 Smart Complaint Map</h1>
            <p>Citizen-powered urban issue reporting – Hyderabad</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------
def render_report_home():
    st.subheader("Report an issue on the map")

    # ---------------- Search ----------------
    search_query = st.text_input("🔎 Search address / area (type at least 3 chars)")

    if "addr_suggestions" not in st.session_state:
        st.session_state["addr_suggestions"] = []

    if search_query and len(search_query) >= 3:
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": search_query, "format": "json", "limit": 5},
                headers={"User-Agent": "smart-complaint-map"},
                timeout=5,
            )
            if r.ok:
                st.session_state["addr_suggestions"] = r.json()
        except Exception:
            st.session_state["addr_suggestions"] = []

    if st.session_state["addr_suggestions"]:
        options = [s["display_name"] for s in st.session_state["addr_suggestions"]]
        selected = st.selectbox("Select suggestion", options)
        if selected:
            loc = st.session_state["addr_suggestions"][options.index(selected)]
            st.session_state["clicked_location"] = {
                "lat": float(loc["lat"]),
                "lon": float(loc["lon"]),
            }

    # ---------------- Map ----------------
    df_all = load_complaints()
    clicked = st.session_state.get("clicked_location")

    center = [DEFAULT_LAT, DEFAULT_LON]
    if clicked:
        center = [clicked["lat"], clicked["lon"]]

    m = folium.Map(location=center, zoom_start=DEFAULT_ZOOM)

    if not df_all.empty:
        cluster = MarkerCluster().add_to(m)
        for _, row in df_all.iterrows():
            folium.CircleMarker(
                [row["lat"], row["lon"]],
                radius=5,
                color=COLOR_MAP.get(row["issue_type"], "#4caf50"),
                fill=True,
                fill_opacity=0.8,
            ).add_to(cluster)

    if clicked:
        folium.Marker(
            [clicked["lat"], clicked["lon"]],
            icon=folium.Icon(color="green", icon="plus"),
        ).add_to(m)

    left, right = st.columns([2.5, 1])

    with left:
        returned = st_folium(
            m,
            height=600,
            use_container_width=True,
            returned_objects=["last_clicked"],
        )

        if returned and returned.get("last_clicked"):
            st.session_state["clicked_location"] = {
                "lat": returned["last_clicked"]["lat"],
                "lon": returned["last_clicked"]["lng"],
            }

    # ---------------- Form ----------------
    with right:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)

        if "clicked_location" not in st.session_state:
            st.info("Click on the map or search to report an issue.")
        else:
            ISSUE_TYPES = [
                "Air quality",
                "Noise",
                "Heat",
                "Cycling / Walking",
                "Odor",
                "Other",
            ]

            issue_type = st.selectbox("Issue type", ISSUE_TYPES)
            intensity = st.slider("Intensity (1–5)", 1, 5, 3)
            description = st.text_area("Description (optional)")
            photo_file = st.file_uploader(
                "Upload a photo (optional)", ["jpg", "jpeg", "png"]
            )

            authority = AUTHORITY_CONTACTS.get(issue_type)
            if authority:
                st.write(f"🏛️ {authority['dept']}")
                st.write(f"📞 {authority['phone']}")
                st.write(f"📧 {authority['email']}")

            send_email = st.checkbox("Generate email to send this complaint")

            if st.button("✅ Submit"):
                photo_path = None
                if photo_file:
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(UPLOAD_DIR, f"{ts}_{photo_file.name}")
                    with open(save_path, "wb") as f:
                        f.write(photo_file.getbuffer())
                    photo_path = save_path

                add_complaint(
                    issue_type,
                    intensity,
                    st.session_state["clicked_location"]["lat"],
                    st.session_state["clicked_location"]["lon"],
                    description,
                    photo_path,
                )

                st.success("Complaint submitted successfully!")

                # =====================================================
                # ✅ IMPROVED EMAIL CONTENT (ONLY CHANGE)
                # =====================================================
                if send_email and authority:
                    timestamp = datetime.now().strftime("%d %B %Y, %H:%M")

                    subject = f"Citizen Complaint: {issue_type} issue reported in Hyderabad"

                    body = f"""
Dear {authority['dept']},

I am writing to formally report an environmental issue observed in Hyderabad.

Issue type:
{issue_type}

Location:
Latitude: {st.session_state["clicked_location"]["lat"]:.5f}
Longitude: {st.session_state["clicked_location"]["lon"]:.5f}

Date & Time:
{timestamp}

Severity (1–5):
{intensity}

Description:
{description if description else "No additional description provided."}

This complaint was submitted through the Smart Complaint Map platform.

Kindly take appropriate action.

Sincerely,
A concerned citizen
"""

                    mailto = (
                        f"mailto:{authority['email']}?"
                        f"subject={urllib.parse.quote(subject)}&"
                        f"body={urllib.parse.quote(body)}"
                    )

                    st.markdown("### 📧 Send complaint")
                    st.markdown(
                        f"[Click here to open your email client and send the complaint]({mailto})"
                    )

                st.session_state["clicked_location"] = None

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------
def main():
    setup()
    init_db()
    apply_global_style()
    render_banner()

    st.sidebar.markdown("## 🌿 Menu")

    pages = {
        "🏠 Report": "home",
        "Solutions & Heatmap": "map", #change of name 
        "Statistics": "stats",
        "Air heatmap": "air",
        "About": "about",
    }

    choice = st.sidebar.radio("Go to", list(pages.keys()))
    key = pages[choice]

    if key == "home":
        render_report_home()
    else:
        df_all = load_complaints()
        if key == "map":
            solution_heat_map.render(df_all)
        elif key == "stats":
            statistics_page.render(df_all)
        elif key == "air":
            air_heatmap_page.render()
        elif key == "about":
            about_page.render()


if __name__ == "__main__":
    main()
