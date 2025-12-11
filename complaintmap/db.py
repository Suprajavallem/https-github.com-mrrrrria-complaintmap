import sqlite3
from datetime import datetime

import pandas as pd

from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            intensite INTEGER,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            date_heure TEXT NOT NULL,
            description TEXT,
            photo_path TEXT,
            votes INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect(DB_PATH)


def add_complaint(type_prob, intensite, lat, lon, description, photo_path):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO complaints (type, intensite, lat, lon, date_heure, description, photo_path, votes)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (type_prob, intensite, lat, lon, datetime.now().isoformat(), description, photo_path),
    )
    conn.commit()
    conn.close()


def load_complaints():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM complaints", conn)
    conn.close()
    if not df.empty:
        df["date_heure"] = pd.to_datetime(df["date_heure"])
    return df


def update_votes(complaint_id, delta=1):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE complaints SET votes = votes + ? WHERE id = ?", (delta, complaint_id))
    conn.commit()
    conn.close()
