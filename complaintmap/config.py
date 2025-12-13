"""
config.py
Global configuration file of the Smart Complaint Map.
- paths (database, uploads)
- geographic constants
- colors/theme
- Streamlit and open API configuration
"""

import os
import streamlit as st


# ---------------- PATHS & FILES ---------------- #

# DATABASE SQLite
DB_PATH = "complaints.db"

# File where pictures are uploaded
UPLOAD_DIR = "uploads"

# OPEN DATABASE API KEY
OPENAQ_API_KEY = "2ce5f5f19f575442fd61aa19b94b50b0bcfbeef41e821b17173f6427e8c4ddf9"


# ---------------- GEOGRAPHICAL PARAMETERS ---------------- #

# Default position (Lyon)
DEFAULT_LAT = 45.76
DEFAULT_LON = 4.85

# Niveau de zoom par défaut pour les cartes
DEFAULT_ZOOM = 13

# ---------------- COLORS ---------------- #

# Main website colours : light green
PRIMARY_BG = "#f1ffe8"   
PRIMARY_ACCENT = "#d5f5c8"
PRIMARY_BORDER = "#b9e6ae"

# Colours for cards and graphs
COLOR_MAP = {
    "Air quality": "#ff6961",         # soft red
    "Noise": "#5c7cfa",               # blue
    "Heat": "#ffa94d",                # orange
    "Cycling / Walking": "#51cf66",   # green
    "Odor": "#9b5de5",                # purple
    "Other": "#6c757d",               # grey
}

# ---------------- CONFIGURATION STREAMLIT ---------------- #

def setup():
    st.set_page_config(
        page_title="Smart Complaint Map",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
