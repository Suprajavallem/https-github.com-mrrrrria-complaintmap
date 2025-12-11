import os
import streamlit as st
import requests
from folium import Map
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# ---------- MAP DEFAULT CENTER ---------- #
try:
    from config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_ZOOM
except Exception:
    DEFAULT_LAT, DEFAULT_LON, DEFAULT_ZOOM = 45.76, 4.84, 11  # Lyon center

# Bounding box for the city of Lyon (approx, slightly expanded)
LYON_LAT_MIN = 45.6
LYON_LAT_MAX = 45.9
LYON_LON_MIN = 4.7
LYON_LON_MAX = 5.1

MAX_FR_LOCATIONS = 1000


# ---------- OPENAQ CONFIG ---------- #

def get_openaq_api_key() -> str | None:
    """Retrieve the OpenAQ API key from env or config.py."""
    env_key = os.getenv("OPENAQ_API_KEY")
    if env_key:
        return env_key

    try:
        from config import OPENAQ_API_KEY  # type: ignore
        return OPENAQ_API_KEY
    except Exception:
        return None


# Parameter IDs on OpenAQ v3
# Only pm25 and pm10 now
PARAM_IDS = {
    "pm25": 2,
    "pm10": 1,
}


# ---------- API FUNCTIONS (LYON) ---------- #

def fetch_locations_for_parameter_lyon(parameter: str):
    """
    Retrieves all French locations measuring the chosen pollutant,
    then filters them to those located inside the bounding box of Lyon.
    """
    if parameter not in PARAM_IDS:
        raise ValueError(f"Unknown pollutant: {parameter}")

    param_id = PARAM_IDS[parameter]
    api_key = get_openaq_api_key()
    if not api_key:
        raise RuntimeError(
            "Missing OpenAQ API key. Add OPENAQ_API_KEY in config.py "
            "or define it as an environment variable."
        )

    url = "https://api.openaq.org/v3/locations"
    params = {
        "parameters_id": param_id,
        "limit": MAX_FR_LOCATIONS,
        "order_by": "id",
        "sort_order": "asc",
        "iso": "FR",
    }
    headers = {"X-API-Key": api_key}

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    locations = []
    for loc in data.get("results", []):
        coords = loc.get("coordinates") or {}
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        if lat is None or lon is None:
            continue

        lat = float(lat)
        lon = float(lon)

        # Lyon filter
        if not (LYON_LAT_MIN <= lat <= LYON_LAT_MAX and LYON_LON_MIN <= lon <= LYON_LON_MAX):
            continue

        locations.append({"id": loc.get("id"), "lat": lat, "lon": lon})

    return locations


def fetch_sensor_for_location(location_id: int, parameter: str):
    """Return the sensor ID that measures the pollutant for this location, or None."""
    param_id = PARAM_IDS[parameter]
    api_key = get_openaq_api_key()
    if not api_key:
        return None

    url = f"https://api.openaq.org/v3/locations/{location_id}/sensors"
    params = {"parameters_id": param_id, "limit": 1}
    headers = {"X-API-Key": api_key}

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    return results[0].get("id") if results else None


def fetch_latest_value_for_sensor(sensor_id: int):
    """Retrieve the most recent hourly measurement for a sensor."""
    api_key = get_openaq_api_key()
    if not api_key:
        return None

    url = f"https://api.openaq.org/v3/sensors/{sensor_id}/measurements/hourly"
    params = {"limit": 1, "sort_order": "desc"}
    headers = {"X-API-Key": api_key}

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return None

    value = results[0].get("value")
    return float(value) if value is not None else None


def fetch_points_with_values_lyon(parameter: str):
    """Combine all steps to retrieve [lat, lon, value] for Lyon."""
    locations = fetch_locations_for_parameter_lyon(parameter)
    api_key = get_openaq_api_key()
    if not api_key:
        raise RuntimeError("Missing OpenAQ API key.")

    points = []
    for loc in locations:
        try:
            sensor_id = fetch_sensor_for_location(loc["id"], parameter)
            if sensor_id is None:
                continue

            value = fetch_latest_value_for_sensor(sensor_id)
            if value is None:
                continue

            points.append([loc["lat"], loc["lon"], value])

        except requests.RequestException:
            continue

    return points


# ---------- STREAMLIT PAGE ---------- #

def render():
    st.header("🌍 Air Quality Heatmap – City of Lyon (OpenAQ v3)")

    st.markdown(
        """
This map displays a **heatmap of the most recent pollutant values**
measured within the **city of Lyon**.

Pollutants available: **PM2.5** and **PM10**  
Low values = green, high values = red.
        """
    )

    parameter = st.selectbox("Pollutant", ["pm25", "pm10"], index=0)

    if not get_openaq_api_key():
        st.error(
            "🔑 Missing OpenAQ API key.\n\n"
            "Add `OPENAQ_API_KEY = \"your_key\"` in config.py or set env var."
        )
        return

    if "value_points_lyon" not in st.session_state:
        st.session_state["value_points_lyon"] = None
        st.session_state["value_meta_lyon"] = {}

    if st.button("🔄 Load / Refresh Data (Lyon)"):
        with st.spinner("Fetching latest measurements for Lyon (OpenAQ)…"):
            try:
                pts = fetch_points_with_values_lyon(parameter=parameter)
            except Exception as e:
                st.error(f"❌ Failed to retrieve data:\n\n{e}")
                return

        st.session_state["value_points_lyon"] = pts
        st.session_state["value_meta_lyon"] = {"parameter": parameter}

    points = st.session_state["value_points_lyon"]

    if points is None:
        st.info("Click **Load / Refresh Data (Lyon)** to display the heatmap.")
        return

    if not points:
        st.warning("No measurements found for the Lyon area for this pollutant.")
        return

    # Normalize values
    values = [p[2] for p in points]
    vmin, vmax = min(values), max(values)

    weighted_points = (
        [[p[0], p[1], 1.0] for p in points]
        if vmax == vmin
        else [[p[0], p[1], (p[2] - vmin) / (vmax - vmin)] for p in points]
    )

    # Map center
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    center = [sum(lats) / len(lats), sum(lons) / len(lons)]

    m = Map(location=center, zoom_start=DEFAULT_ZOOM)

    # Color gradient green → yellow → red
    gradient = {0.0: "green", 0.5: "yellow", 1.0: "red"}

    HeatMap(weighted_points, radius=18, blur=15, max_zoom=13, gradient=gradient).add_to(m)

    st_folium(m, width=900, height=600)

    st.caption(
        f"Stations used: **{len(points)}** · Pollutant: **{parameter}**\n\n"
        f"Min value: **{vmin:.2f}** · Max value: **{vmax:.2f}**"
    )
