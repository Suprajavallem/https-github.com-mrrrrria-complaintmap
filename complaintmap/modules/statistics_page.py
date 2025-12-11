import streamlit as st
import matplotlib.pyplot as plt

def render(df_all):
    st.header("📊 Statistics & Distributions")

    if df_all.empty:
        st.info("No data available yet to compute statistics.")
        return

    # -----------------------------
    # 1) PIE CHART + PERCENTAGES
    # -----------------------------
    st.subheader("Complaint Types Distribution")

    counts = df_all["type"].value_counts()
    percentages = (counts / counts.sum() * 100).round(1)

    col_pie, col_info = st.columns([1.2, 1])
    with col_pie:
        fig, ax = plt.subplots(figsize=(4,4), facecolor="none")  # figure transparent
        ax.set_facecolor("none")  # axes transparent
        ax.pie(counts, labels=counts.index, autopct="%1.1f%%")
        ax.set_title("Types of Complaints")
        st.pyplot(fig)

    with col_info:
        st.markdown("### Percentages")
        for t, pct in percentages.items():
            st.write(f"**{t}**: {pct}%")

    st.markdown("---")

    # -----------------------------
    # 2) SELECT COMPLAINT TYPE
    # -----------------------------
    st.subheader("Filter by Complaint Type")

    types = ["All"] + sorted(df_all["type"].unique())
    selected_type = st.selectbox("Select Complaint Type", types)

    if selected_type == "All":
        df_filtered = df_all.copy()
    else:
        df_filtered = df_all[df_all["type"] == selected_type]

    st.markdown("---")

    # -----------------------------
    # 3) HISTOGRAMS: NUMBER OF COMPLAINTS
    # -----------------------------
    st.subheader(f"Number of Complaints ({selected_type})")

    # Prepare time columns
    df_filtered["day"] = df_filtered["date_heure"].dt.day
    df_filtered["month"] = df_filtered["date_heure"].dt.month
    df_filtered["year"] = df_filtered["date_heure"].dt.year

    col_d, col_m, col_y = st.columns(3)

    # ---- Complaints per Day (1–31) ----
    with col_d:
        st.write("#### Per Day")
        counts_day = df_filtered["day"].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(4,3), facecolor="none")
        ax.set_facecolor("none")
        ax.bar(counts_day.index, counts_day.values)
        ax.set_xlabel("Day of Month")
        ax.set_ylabel("Number of Reports")
        ax.set_xticks(range(1,32))
        st.pyplot(fig)

    # ---- Complaints per Month (1–12) ----
    with col_m:
        st.write("#### Per Month")
        counts_month = df_filtered["month"].value_counts().sort_index()
        month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        fig, ax = plt.subplots(figsize=(4,3), facecolor="none")
        ax.set_facecolor("none")
        ax.bar(counts_month.index, counts_month.values)
        ax.set_xlabel("Month")
        ax.set_ylabel("Number of Reports")
        ax.set_xticks(range(1,13))
        ax.set_xticklabels(month_labels, rotation=45)
        st.pyplot(fig)

    # ---- Complaints per Year (last 5 even years) ----
    with col_y:
        st.write("#### Per Year (Last 5 Even Years)")
        all_years = sorted(df_filtered["year"].unique())
        even_years = [y for y in all_years if y % 2 == 0]
        last_5_even_years = even_years[-5:]
        counts_year = df_filtered[df_filtered["year"].isin(last_5_even_years)]["year"].value_counts().reindex(last_5_even_years, fill_value=0)
        fig, ax = plt.subplots(figsize=(4,3), facecolor="none")
        ax.set_facecolor("none")
        ax.bar(counts_year.index, counts_year.values, width=0.6)
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of Reports")
        ax.set_xticks(last_5_even_years)
        st.pyplot(fig)

    st.markdown("---")

    # -----------------------------
    # 4) HISTOGRAMS: INTENSITY (X=1–5, Y=counts)
    # -----------------------------
    st.subheader(f"Intensity Distribution ({selected_type})")

    col_id, col_im, col_iy = st.columns(3)

    # Count intensities per day/month/year
    counts_day_int = df_filtered.groupby(df_filtered["date_heure"].dt.date)["intensite"].value_counts().unstack(fill_value=0)
    counts_month_int = df_filtered.groupby(df_filtered["date_heure"].dt.to_period("M"))["intensite"].value_counts().unstack(fill_value=0)
    counts_year_int = df_filtered.groupby(df_filtered["date_heure"].dt.to_period("Y"))["intensite"].value_counts().unstack(fill_value=0)

    # Ensure columns 1–5 exist
    for df_group in [counts_day_int, counts_month_int, counts_year_int]:
        for i in range(1,6):
            if i not in df_group.columns:
                df_group[i] = 0
        df_group.sort_index(axis=1, inplace=True)

    # ---- Intensity per Day ----
    with col_id:
        st.write("#### Per Day")
        total_per_intensity = counts_day_int.sum(axis=0)
        fig, ax = plt.subplots(figsize=(4,3), facecolor="none")
        ax.set_facecolor("none")
        ax.bar(total_per_intensity.index, total_per_intensity.values)
        ax.set_xlabel("Intensity")
        ax.set_ylabel("Number of Reports")
        ax.set_xticks(range(1,6))
        ax.set_ylim(0, total_per_intensity.values.max()+1)
        st.pyplot(fig)

    # ---- Intensity per Month ----
    with col_im:
        st.write("#### Per Month")
        total_per_intensity = counts_month_int.sum(axis=0)
        fig, ax = plt.subplots(figsize=(4,3), facecolor="none")
        ax.set_facecolor("none")
        ax.bar(total_per_intensity.index, total_per_intensity.values)
        ax.set_xlabel("Intensity")
        ax.set_ylabel("Number of Reports")
        ax.set_xticks(range(1,6))
        ax.set_ylim(0, total_per_intensity.values.max()+1)
        st.pyplot(fig)

    # ---- Intensity per Year (last 5 even years) ----
    with col_iy:
        st.write("#### Per Year (Last 5 Even Years)")
        counts_year_int = counts_year_int[counts_year_int.index.year.isin(last_5_even_years)]
        total_per_intensity = counts_year_int.sum(axis=0)
        fig, ax = plt.subplots(figsize=(4,3), facecolor="none")
        ax.set_facecolor("none")
        ax.bar(total_per_intensity.index, total_per_intensity.values)
        ax.set_xlabel("Intensity")
        ax.set_ylabel("Number of Reports")
        ax.set_xticks(range(1,6))
        ax.set_ylim(0, total_per_intensity.values.max()+1)
        st.pyplot(fig)
