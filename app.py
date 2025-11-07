import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Bakery Performance Dashboard 🍞", layout="wide")

# ------------------------------
# Header & Image Banner
# ------------------------------
st.title("🥖 Bakery Performance Analytics Dashboard")
st.image(
    "https://images.unsplash.com/photo-1608198093002-ad4e005484ec?fm=jpg&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8YmFrZXJ5JTIwcHJvZHVjdHN8ZW58MHx8MHx8fDA%3D&ixlib=rb-4.1.0&q=60&w=2000",
    use_container_width=True,
    caption="Bakery Operations & Sales Insights",
)

st.markdown("---")

# ------------------------------
# Load Data
# ------------------------------
st.sidebar.header("🔍 Filters")

uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Clean columns
    df.columns = df.columns.str.strip()

    # Ensure Date column
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Month"] = df["Date"].dt.month_name()
        df["Day"] = df["Date"].dt.day_name()
    else:
        st.error("❌ Column 'Date' not found.")
        st.stop()

    # Profit calculation
    if "Revenue" in df.columns and "Ad Spend" in df.columns:
        df["Profit"] = df["Revenue"] - df["Ad Spend"]

    # --- Sidebar Filters ---
    channels = st.sidebar.multiselect("Select Channel(s):", sorted(df["Channel"].dropna().unique())) if "Channel" in df.columns else []
    services = st.sidebar.multiselect("Select Service Type(s):", sorted(df["Service Type"].dropna().unique())) if "Service Type" in df.columns else []
    months = st.sidebar.multiselect("Select Month(s):", sorted(df["Month"].dropna().unique()))
    days = st.sidebar.multiselect("Select Day(s):", sorted(df["Day"].dropna().unique()))
    seasons = st.sidebar.multiselect("Select Season(s):", sorted(df["Season"].dropna().unique())) if "Season" in df.columns else []
    times = st.sidebar.multiselect("Select Time(s) of Day:", sorted(df["Time of Day"].dropna().unique())) if "Time of Day" in df.columns else []

    # Range filters
    min_rev, max_rev = st.sidebar.slider("Revenue Range ($):", float(df["Revenue"].min()), float(df["Revenue"].max()), (float(df["Revenue"].min()), float(df["Revenue"].max())))
    min_profit, max_profit = st.sidebar.slider("Profit Range ($):", float(df["Profit"].min()), float(df["Profit"].max()), (float(df["Profit"].min()), float(df["Profit"].max())))

    # Filter data
    filtered_df = df.copy()
    if channels:
        filtered_df = filtered_df[filtered_df["Channel"].isin(channels)]
    if services:
        filtered_df = filtered_df[filtered_df["Service Type"].isin(services)]
    if months:
        filtered_df = filtered_df[filtered_df["Month"].isin(months)]
    if days:
        filtered_df = filtered_df[filtered_df["Day"].isin(days)]
    if seasons:
        filtered_df = filtered_df[filtered_df["Season"].isin(seasons)]
    if times:
        filtered_df = filtered_df[filtered_df["Time of Day"].isin(times)]
    filtered_df = filtered_df[(filtered_df["Revenue"].between(min_rev, max_rev)) & (filtered_df["Profit"].between(min_profit, max_profit))]

    st.markdown("### 📊 Data Overview")
    st.dataframe(filtered_df.head())

    # ------------------------------
    # Tabs
    # ------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Overview", "💵 Revenue & Profit", "📈 Trends", "📊 Relationships", "🌍 Regional Insights"
    ])

    # ------------------------------
    # TAB 1 — OVERVIEW
    # ------------------------------
    with tab1:
        st.subheader("Business KPIs")

        total_rev = filtered_df["Revenue"].sum()
        total_profit = filtered_df["Profit"].sum()
        total_spend = filtered_df["Ad Spend"].sum()
        avg_roas = (filtered_df["Revenue"] / filtered_df["Ad Spend"]).mean() if "Ad Spend" in filtered_df.columns else 0
        avg_conv = filtered_df["Conversions"].mean() if "Conversions" in filtered_df.columns else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Revenue", f"${total_rev:,.0f}")
        c2.metric("Total Profit", f"${total_profit:,.0f}")
        c3.metric("Total Ad Spend", f"${total_spend:,.0f}")
        c4.metric("Avg ROAS", f"{avg_roas:.2f}x")
        c5.metric("Avg Conversions", f"{avg_conv:.0f}")

        st.markdown("#### Revenue vs Profit by Channel")
        if "Channel" in filtered_df.columns:
            summary = filtered_df.groupby("Channel")[["Revenue", "Profit"]].sum().reset_index().sort_values("Revenue", ascending=False)
            fig = px.bar(summary, x="Channel", y=["Revenue", "Profit"], barmode="group", title="Revenue vs Profit by Channel")
            st.plotly_chart(fig, use_container_width=True)

    # ------------------------------
    # TAB 2 — Revenue & Profit Visuals
    # ------------------------------
    with tab2:
        st.subheader("Revenue & Profit Insights")

        col1, col2 = st.columns(2)

        if "Service Type" in filtered_df.columns:
            with col1:
                svc_summary = filtered_df.groupby("Service Type")[["Revenue", "Profit"]].sum().reset_index().sort_values("Revenue", ascending=False)
                fig = px.bar(svc_summary, x="Service Type", y=["Revenue", "Profit"], barmode="group", title="Revenue vs Profit by Service Type")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if "Channel" in filtered_df.columns:
                pie_data = filtered_df.groupby("Channel")["Revenue"].sum().reset_index()
                fig = px.pie(pie_data, names="Channel", values="Revenue", title="Revenue Share by Channel")
                st.plotly_chart(fig, use_container_width=True)

        # Treemap
        if "Region" in filtered_df.columns:
            st.subheader("Revenue Distribution by Region & Service")
            fig_tree = px.treemap(filtered_df, path=["Region", "Service Type"], values="Revenue", color="Profit", color_continuous_scale="Blues")
            st.plotly_chart(fig_tree, use_container_width=True)

    # ------------------------------
    # TAB 3 — TRENDS
    # ------------------------------
    with tab3:
        st.subheader("Time Trends")

        monthly = filtered_df.set_index("Date").resample("M")[["Revenue", "Profit", "Ad Spend"]].sum().reset_index()
        fig_line = px.line(monthly, x="Date", y=["Revenue", "Profit", "Ad Spend"], markers=True, title="Monthly Trends (Revenue, Profit, Ad Spend)")
        st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("#### Day-of-Week Performance")
        day_perf = filtered_df.groupby("Day")[["Revenue", "Profit"]].sum().reset_index().sort_values("Revenue", ascending=False)
        fig_bar = px.bar(day_perf, x="Day", y=["Revenue", "Profit"], barmode="group")
        st.plotly_chart(fig_bar, use_container_width=True)

    # ------------------------------
    # TAB 4 — RELATIONSHIPS
    # ------------------------------
    with tab4:
        st.subheader("Ad Spend vs Revenue vs Profit")

        scatter_df = filtered_df.copy()
        scatter_df = scatter_df.dropna(subset=["Revenue", "Ad Spend", "Profit"])
        scatter_df = scatter_df[scatter_df["Profit"] >= 0]

        fig_sc = px.scatter(
            scatter_df,
            x="Ad Spend",
            y="Revenue",
            size="Profit",
            color="Channel" if "Channel" in scatter_df.columns else None,
            hover_data=["Service Type", "Profit"] if "Service Type" in scatter_df.columns else ["Profit"],
            title="Ad Spend vs Revenue (Bubble Size = Profit)"
        )
        st.plotly_chart(fig_sc, use_container_width=True)

        st.markdown("#### Correlation Heatmap")
        num_cols = filtered_df.select_dtypes(include=np.number)
        if not num_cols.empty:
            corr = num_cols.corr()
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.heatmap(corr, annot=True, cmap="Blues", ax=ax)
            st.pyplot(fig)

    # ------------------------------
    # TAB 5 — REGIONAL INSIGHTS
    # ------------------------------
    with tab5:
        if "Region" in filtered_df.columns:
            st.subheader("Geographic Revenue / Profit View")
            fig_map = px.bar(filtered_df.groupby("Region")[["Revenue", "Profit"]].sum().reset_index(), x="Region", y=["Revenue", "Profit"], barmode="group", title="Performance by Region")
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("🌍 Region data not available in your dataset.")

else:
    st.info("📤 Please upload a dataset to begin.")
