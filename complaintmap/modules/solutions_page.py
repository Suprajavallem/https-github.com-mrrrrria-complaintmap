import streamlit as st

def classify_solution(row):
    """
    Return a simple proposed technical solution based on the issue type.

    Parameters
    ----------
    row : pandas.Series
        One complaint row, with at least a 'type' column.

    Returns
    -------
    str
        A short English description of a possible solution.
    """
    issue_type = row["type"]

    if issue_type == "Air":
        return (
            "Reduce motorized traffic, create continuous cycling corridors "
            "and add trees or green buffers along the street."
        )

    if issue_type == "Bruit":
        return (
            "Introduce a 30 km/h zone, use noise-reducing pavement and, where needed, "
            "install acoustic barriers or green walls."
        )

    if issue_type == "Chaleur":
        return (
            "Increase vegetation (trees, shrubs), add shading structures or solar canopies, "
            "and use light-colored, reflective materials."
        )

    if issue_type == "Vélo / Piéton":
        return (
            "Build protected cycling lanes, secure pedestrian crossings and improve "
            "street lighting and visibility."
        )

    if issue_type == "Odeur":
        return (
            "Identify the odor source (waste, industry, traffic) and improve emission control, "
            "storage conditions and local ventilation."
        )

    return (
        "A more detailed analysis is required to define the most appropriate interventions."
    )



# Mapping from internal French types to nicer English labels for display
TYPE_LABELS = {
    "Air": "Air quality",
    "Bruit": "Noise",
    "Chaleur": "Heat",
    "Vélo / Piéton": "Cycling / Walking",
    "Odeur": "Odor",
    "Autre": "Other",
}


def render(df_all):
    st.header("💡 Technical Solutions Based on Reported Issues")

    if df_all.empty:
        st.info("Add some reports first to see suggested solutions.")
        return

    # Copy data and compute proposed solution for each report
    df_sol = df_all.copy()
    df_sol["proposed_solution"] = df_sol.apply(classify_solution, axis=1)

    # Add a nice display label for type
    df_sol["issue_type_label"] = df_sol["type"].map(TYPE_LABELS).fillna(df_sol["type"])

    # ----------------- FILTERS ----------------- #
    st.subheader("🎛️ Filters")

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        type_options = sorted(df_sol["issue_type_label"].unique())
        selected_types = st.multiselect(
            "Issue types",
            options=type_options,
            default=type_options,
        )

    with col_f2:
        min_intensity, max_intensity = st.slider(
            "Intensity range",
            min_value=1,
            max_value=5,
            value=(1, 5),
        )

    with col_f3:
        high_priority_only = st.checkbox(
            "Show only high-priority reports (intensity ≥ 4)"
        )

    # Apply filters
    df_filtered = df_sol[
        df_sol["issue_type_label"].isin(selected_types)
        & (df_sol["intensite"] >= min_intensity)
        & (df_sol["intensite"] <= max_intensity)
    ]

    if high_priority_only:
        df_filtered = df_filtered[df_filtered["intensite"] >= 4]

    if df_filtered.empty:
        st.warning("No reports match the selected filters.")
        return

    # ----------------- TABS LAYOUT ----------------- #
    tab_overview, tab_by_type, tab_reco = st.tabs(
        ["🔍 Overview", "📊 By issue type", "🛠️ Recommendations"]
    )

    # ========== TAB 1: OVERVIEW ========== #
    with tab_overview:
        st.subheader("Latest reports and proposed solutions")

        # Prepare a nicer display dataframe
        df_display = df_filtered[
            ["date_heure", "issue_type_label", "intensite", "description", "proposed_solution"]
        ].copy()

        df_display.rename(
            columns={
                "date_heure": "Date & time",
                "issue_type_label": "Issue type",
                "intensite": "Intensity (1–5)",
                "description": "Description",
                "proposed_solution": "Proposed solution",
            },
            inplace=True,
        )

        # Show only the last N rows for readability
        st.dataframe(df_display.tail(30), use_container_width=True)

        # Optional: small "card view" for the last few reports
        st.markdown("#### Highlighted recent reports")
        for _, row in df_display.tail(5).iterrows():
            with st.container():
                st.markdown(
                    f"""
                    **{row['Issue type']}** – intensity **{row['Intensity (1–5)']}**  
                    _{row['Date & time']}_  

                    - **Description:** {row['Description'] or '—'}
                    - **Proposed solution:** {row['Proposed solution'] or '—'}
                    """
                )
                st.markdown("---")

    # ========== TAB 2: BY ISSUE TYPE ========== #
    with tab_by_type:
        st.subheader("Summary by issue type")

        summary = (
            df_filtered.groupby(["type", "issue_type_label"])
            .agg(
                reports=("id", "count"),
                avg_intensity=("intensite", "mean"),
            )
            .reset_index()
        )

        summary_display = summary[["issue_type_label", "reports", "avg_intensity"]].copy()
        summary_display.rename(
            columns={
                "issue_type_label": "Issue type",
                "reports": "Number of reports",
                "avg_intensity": "Average intensity (1–5)",
            },
            inplace=True,
        )

        st.dataframe(summary_display, use_container_width=True)

        st.markdown(
            """
            Higher average intensity and a large number of reports usually indicate
            **priority areas for intervention**.
            """
        )

    # ========== TAB 3: RECOMMENDATIONS ========== #
    with tab_reco:
        st.subheader("Targeted recommendations")

        st.markdown(
            """
            Below are example interventions, tailored to the types of issues currently visible
            with the selected filters. Use these as inspiration for urban planning, pilot projects
            or communication campaigns.
            """
        )

        # Determine which types are present in the filtered data
        types_present = sorted(df_filtered["type"].unique())

        # For each type present, show a recommendation block
        for t in types_present:
            label = TYPE_LABELS.get(t, t)
            st.markdown(f"### {label}")

            if t == "Air":
                st.markdown(
                    """
                    **Main objectives:** reduce local emissions and exposure to pollutants.

                    **Possible measures:**
                    - Low-emission or car-free zones at the most impacted streets.
                    - Continuous cycling corridors to shift short trips away from cars.
                    - Electrification of buses and delivery vehicles on key routes.
                    - Installation of fixed and mobile air quality sensors.
                    - Green buffers (trees, hedges) between traffic and sidewalks.

                    **Quick wins:**
                    - Pilot “school street” projects at peak hours.
                    - Temporary traffic calming during high pollution episodes.
                    """
                )

            elif t == "Bruit":
                st.markdown(
                    """
                    **Main objectives:** reduce noise peaks and chronic exposure.

                    **Possible measures:**
                    - 30 km/h zones on residential streets and near schools.
                    - Noise-reducing road surfaces on noisy axes.
                    - Acoustic barriers or green walls where space is limited.
                    - Night-time delivery planning and quiet logistics.
                    - Enforcing limits for motorcycles and modified exhausts.

                    **Quick wins:**
                    - Targeted controls on the streets most frequently reported.
                    - Communication campaign about noise and health.
                    """
                )

            elif t == "Chaleur":
                st.markdown(
                    """
                    **Main objectives:** reduce urban heat islands and increase shade.

                    **Possible measures:**
                    - Planting trees and shrubs along sidewalks and squares.
                    - Installing PV solar canopies above parking lots or open areas.
                    - Light-colored or reflective roofs and façades.
                    - Removing unnecessary asphalt and creating permeable surfaces.
                    - Creating shaded resting spots with benches and water points.

                    **Quick wins:**
                    - Temporary shading (sails, pergolas) in hotspots.
                    - “Cool routes” maps to guide pedestrians during heat waves.
                    """
                )

            elif t == "Vélo / Piéton":
                st.markdown(
                    """
                    **Main objectives:** improve safety and comfort for walking and cycling.

                    **Possible measures:**
                    - Separated, continuous cycling lanes on main routes.
                    - Safe pedestrian crossings with good visibility and signal timing.
                    - Improved lighting along sidewalks and bikeways.
                    - Reduced car speeds at conflict points.
                    - Secure bike parking near public transport and services.

                    **Quick wins:**
                    - Tactical urbanism (temporary markings, bollards, paint).
                    - Quick fixes on the most dangerous intersections reported.
                    """
                )

            elif t == "Odeur":
                st.markdown(
                    """
                    **Main objectives:** identify sources and reduce nuisance odours.

                    **Possible measures:**
                    - Improved waste collection frequency and bin design.
                    - Better management of restaurant and industrial exhausts.
                    - Detection and repair of sewer or drainage issues.
                    - Creation of ventilation corridors and air circulation paths.

                    **Quick wins:**
                    - Targeted inspections in hotspots repeatedly reported.
                    - Communication with nearby businesses to adapt practices.
                    """
                )

            else:  # "Autre" or anything else
                st.markdown(
                    """
                    **Main objectives:** investigate the specific nature of the issue.

                    **Possible measures:**
                    - Field visits to clarify the problem with residents.
                    - Combining this map with other datasets (traffic, land use, etc.).
                    - Small-scale pilots to test improvements.
                    """
                )

            st.markdown("---")
