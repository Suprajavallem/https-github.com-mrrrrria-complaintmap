import folium
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from config import COLOR_MAP, DEFAULT_ZOOM


def render(df_all):
    st.header("🗺️ Map of Reported Environmental Issues")

    if df_all.empty:
        st.info("No reports yet. Add one in the 'Report an Issue' section.")
        return

    st.subheader("Filters")

    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        type_filter = st.multiselect(
            "Issue types",
            options=sorted(df_all["type"].unique()),
            default=list(sorted(df_all["type"].unique())),
        )
    with colf2:
        intensite_min = st.slider("Minimum intensity", 1, 5, 1)
    with colf3:
        date_min = st.date_input(
            "From date",
            value=df_all["date_heure"].min().date() if not df_all.empty else None,
        )

    df = df_all[
        (df_all["type"].isin(type_filter))
        & (df_all["intensite"] >= intensite_min)
        & (df_all["date_heure"].dt.date >= date_min)
    ]

    if df.empty:
        st.warning("No reports match these filters.")
        return

    center = [df["lat"].mean(), df["lon"].mean()]
    base_map = folium.Map(location=center, zoom_start=DEFAULT_ZOOM)

    for _, row in df.iterrows():
        popup_lines = [
            f"<b>Type:</b> {row['type']}",
            f"<b>Intensity:</b> {row['intensite']} / 5",
            f"<b>Date:</b> {row['date_heure']}",
        ]
        if row["description"]:
            popup_lines.append(f"<b>Description:</b> {row['description']}")
        if row["photo_path"]:
            popup_lines.append(f"<b>Photo:</b> {row['photo_path']}")
        popup_html = "<br>".join(popup_lines)

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6,
            color=COLOR_MAP.get(row["type"], "black"),
            fill=True,
            fill_opacity=0.8,
            popup=popup_html,
        ).add_to(base_map)

    st.markdown("### Display options")
    use_heatmap = st.checkbox("Also display heatmap (density of issues)")
    if use_heatmap:
        heat_data = [
            [row["lat"], row["lon"], row["intensite"]] for _, row in df.iterrows()
        ]
        HeatMap(heat_data, radius=15, blur=10).add_to(base_map)

    st_folium(base_map, width=900, height=600)
