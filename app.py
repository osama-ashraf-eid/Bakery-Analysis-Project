import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Bakery Analytics Dashboard", layout="wide")

st.title("🍞 Bakery Performance Analysis Dashboard")
st.markdown("Upload your dataset to explore sales, ad spend, and performance trends interactively.")

# -----------------
# 1️⃣ Upload Data
# -----------------
st.sidebar.header("📂 Data Source")
uploaded_file = st.sidebar.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        st.stop()
else:
    st.warning("Please upload a dataset file to start.")
    st.stop()

# -----------------
# 2️⃣ Auto-detect important columns
# -----------------
def detect_column(possible_names):
    """Return the first matching column name from the dataset."""
    for name in df.columns:
        for possible in possible_names:
            if possible.lower() in name.lower().strip():
                return name
    return None

col_map = {
    "date": detect_column(["date", "day", "time"]),
    "channel": detect_column(["channel", "marketing", "platform"]),
    "service": detect_column(["service", "product", "category"]),
    "revenue": detect_column(["revenue", "sales", "income"]),
    "ad_spend": detect_column(["ad spend", "spend", "cost", "advertising"]),
    "profit": detect_column(["profit", "margin", "gain"]),
    "conversions": detect_column(["conversion", "purchase", "transactions"]),
    "time_of_day": detect_column(["time of day", "hour", "session"]),
    "season": detect_column(["season", "quarter", "period"]),
}

# -----------------
# 3️⃣ Data preparation
# -----------------
if col_map["date"]:
    df[col_map["date"]] = pd.to_datetime(df[col_map["date"]], errors="coerce")

if col_map["revenue"] and col_map["ad_spend"]:
    df["ROAS"] = df[col_map["revenue"]] / df[col_map["ad_spend"]].replace(0, np.nan)

if col_map["revenue"] and col_map["conversions"]:
    df["VPC"] = df[col_map["revenue"]] / (df[col_map["conversions"]] + 1)

# -----------------
# 4️⃣ Sidebar Filters
# -----------------
st.sidebar.header("🔍 Filters")

if col_map["channel"]:
    channels = df[col_map["channel"]].dropna().unique().tolist()
    selected_channels = st.sidebar.multiselect("Select Channel(s)", channels, default=channels)
else:
    selected_channels = []

if col_map["service"]:
    services = df[col_map["service"]].dropna().unique().tolist()
    selected_services = st.sidebar.multiselect("Select Service Type(s)", services, default=services)
else:
    selected_services = []

filtered_df = df.copy()
if col_map["channel"] and selected_channels:
    filtered_df = filtered_df[filtered_df[col_map["channel"]].isin(selected_channels)]
if col_map["service"] and selected_services:
    filtered_df = filtered_df[filtered_df[col_map["service"]].isin(selected_services)]

# -----------------
# 5️⃣ Dashboard Tabs
# -----------------
st.subheader("📊 Comparative Analysis and Trends")

tab1, tab2, tab3 = st.tabs(["Channel & Service Analysis", "Time-Series Trends", "Descriptive Statistics"])

# === TAB 1: Channel & Service Analysis ===
with tab1:
    st.markdown("#### Performance Comparison by Channel and Service Type")
    col1, col2 = st.columns(2)

    with col1:
        if col_map["channel"] and col_map["revenue"]:
            channel_summary = filtered_df.groupby(col_map["channel"]).agg(
                Total_Revenue=(col_map["revenue"], "sum"),
                Total_Spend=(col_map["ad_spend"], "sum") if col_map["ad_spend"] else ("dummy", "sum"),
                Avg_ROAS=("ROAS", "mean") if "ROAS" in filtered_df.columns else ("dummy", "sum")
            ).reset_index().sort_values("Total_Revenue", ascending=False)

            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(data=channel_summary, x=col_map["channel"], y="Total_Revenue", palette="Blues_d", ax=ax)
            ax.set_title("Total Revenue by Channel", fontsize=12)
            ax.set_xlabel("Channel")
            ax.set_ylabel("Revenue ($)")
            ax.tick_params(axis="x", rotation=45)
            st.pyplot(fig)
        else:
            st.info("⚠️ Missing 'Channel' or 'Revenue' column in dataset.")

    with col2:
        if col_map["service"] and col_map["revenue"]:
            service_summary = filtered_df.groupby(col_map["service"])[col_map["revenue"]].sum().reset_index()
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.pie(
                service_summary[col_map["revenue"]],
                labels=service_summary[col_map["service"]],
                autopct="%1.1f%%",
                startangle=90,
                wedgeprops={"edgecolor": "white"}
            )
            ax.set_title("Revenue Distribution by Service Type")
            st.pyplot(fig)
        else:
            st.info("⚠️ Missing 'Service Type' or 'Revenue' column.")

# === TAB 2: Time-Series Trends ===
with tab2:
    st.markdown("#### Monthly Performance Trends")

    if not col_map["date"]:
        st.warning("⚠️ No 'Date' column detected for time-series analysis.")
    else:
        monthly_df = filtered_df.set_index(col_map["date"]).resample("M").agg({
            col_map["revenue"]: "sum",
            col_map["ad_spend"]: "sum" if col_map["ad_spend"] else "sum"
        }).reset_index()

        monthly_df["Month"] = monthly_df[col_map["date"]].dt.strftime("%Y-%m")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.lineplot(data=monthly_df, x="Month", y=col_map["revenue"], marker="o", label="Revenue", ax=ax)
        if col_map["ad_spend"]:
            sns.lineplot(data=monthly_df, x="Month", y=col_map["ad_spend"], marker="o", label="Ad Spend", ax=ax)
        ax.set_title("Monthly Trend of Revenue and Ad Spend")
        ax.set_xlabel("Month")
        ax.set_ylabel("Value ($)")
        ax.tick_params(axis="x", rotation=45)
        ax.legend()
        st.pyplot(fig)

# === TAB 3: Descriptive Statistics ===
with tab3:
    st.markdown("#### Descriptive Statistics for Filtered Data")

    expected_cols = [col_map["revenue"], col_map["ad_spend"], col_map["conversions"], col_map["profit"], "ROAS", "VPC"]
    available_cols = [c for c in expected_cols if c and c in filtered_df.columns]

    if available_cols:
        st.dataframe(filtered_df[available_cols].describe().T)
    else:
        st.warning("⚠️ No numeric columns available for descriptive statistics.")

    st.markdown("#### Revenue Distribution by Time of Day and Season")
    col3, col4 = st.columns(2)

    with col3:
        if col_map["time_of_day"] and col_map["revenue"]:
            time_summary = filtered_df.groupby(col_map["time_of_day"])[col_map["revenue"]].sum().reset_index()
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(data=time_summary, x=col_map["time_of_day"], y=col_map["revenue"], palette="viridis", ax=ax)
            ax.set_title("Revenue by Time of Day")
            ax.set_xlabel("Time of Day")
            ax.set_ylabel("Revenue ($)")
            st.pyplot(fig)
        else:
            st.info("⚠️ No 'Time of Day' column detected.")

    with col4:
        if col_map["season"] and col_map["revenue"]:
            season_summary = filtered_df.groupby(col_map["season"])[col_map["revenue"]].sum().reset_index()
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(data=season_summary, x=col_map["season"], y=col_map["revenue"], palette="mako", ax=ax)
            ax.set_title("Revenue by Season")
            ax.set_xlabel("Season")
            ax.set_ylabel("Revenue ($)")
            st.pyplot(fig)
        else:
            st.info("⚠️ No 'Season' column detected.")
