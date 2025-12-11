"""
config.py

Fichier de configuration globale de l'application Smart Complaint Map.
On centralise ici :
- les chemins (base de données, uploads),
- les constantes géographiques,
- les couleurs / thème,
- la configuration Streamlit (setup()).
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
DEFAULT_LAT = 45.4510
DEFAULT_LON = 4.5021

# Niveau de zoom par défaut pour les cartes
DEFAULT_ZOOM = 13


# ---------------- COLORS ---------------- #

# Main website colours : light green
PRIMARY_BG = "#f1ffe8"   
PRIMARY_ACCENT = "#d5f5c8"
PRIMARY_BORDER = "#b9e6ae"

# Colours for cards and graphs
COLOR_MAP = {
    "Air": "#ff6961",            # rouge doux
    "Bruit": "#5c7cfa",          # bleu
    "Chaleur": "#ffa94d",        # orange
    "Vélo / Piéton": "#51cf66",  # vert
    "Odeur": "#9b5de5",          # violet
    "Autre": "#6c757d",          # gris
}


# ---------------- CONFIGURATION STREAMLIT ---------------- #

def setup():
    """
    Configure Streamlit au démarrage de l'application.

    - Définition du titre et de la mise en page
    - Création du dossier d'uploads si besoin
    """
    st.set_page_config(
        page_title="Smart Complaint Map",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # S'assurer que le dossier des uploads existe
    os.makedirs(UPLOAD_DIR, exist_ok=True)
