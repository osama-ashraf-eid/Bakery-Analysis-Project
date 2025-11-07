# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Bakery Analytics Dashboard", layout="wide")

# ---------------------------
# Background image (Unsplash) - bakery theme, subtle and faded
# ---------------------------
BG_URL = "https://images.unsplash.com/photo-1542831371-d531d36971e6"  # bakery photo (Unsplash)
st.markdown(
    f"""
    <style>
    .stApp {{
      background: linear-gradient(rgba(255,255,255,0.86), rgba(255,255,255,0.86)),
                  url("{BG_URL}?auto=format&fit=crop&w=1400&q=80") no-repeat center;
      background-size: cover;
    }}
    /* Card/box transparency adjustments so text remains readable */
    .stContainer, .css-1lcbmhc, .css-1d391kg {{
      background: rgba(255,255,255,0.72);
      backdrop-filter: blur(4px);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Title & Banner
# ---------------------------
st.title("🍞 Bakery Performance Analysis")
st.markdown("Interactive dashboard — compares **Revenue** vs **Profit**, supports smart column detection & multiple filters.")

# ---------------------------
# Upload / Load data
# ---------------------------
st.sidebar.header("Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is None:
    st.sidebar.info("Upload a dataset to start. Expected fields (any variant of): Date, Channel, Service Type, Revenue, Ad Spend, Conversions, Season, Time of Day.")
    st.stop()

# load file
try:
    if uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Error reading file: {e}")
    st.stop()

# ---------------------------
# Smart column detection (robust to small name variations)
# ---------------------------
def detect_column(df, possible_names):
    for col in df.columns:
        col_norm = col.lower().strip()
        for p in possible_names:
            if p.lower() in col_norm:
                return col
    return None

col_map = {
    "date": detect_column(df, ["date", "day", "order date", "timestamp"]),
    "channel": detect_column(df, ["channel", "platform", "marketing"]),
    "service": detect_column(df, ["service", "service type", "product", "category"]),
    "revenue": detect_column(df, ["revenue", "sales", "income"]),
    "ad_spend": detect_column(df, ["ad spend", "spend", "cost", "advertising"]),
    "conversions": detect_column(df, ["conversion", "conversions", "orders", "transactions", "purchases"]),
    "season": detect_column(df, ["season", "quarter", "period"]),
    "time_of_day": detect_column(df, ["time of day", "hour", "session"]),
}

# safe defaults / info
missing = [k for k, v in col_map.items() if v is None]
if len(missing) > 0:
    st.sidebar.info("Detected columns: " + ", ".join([f"{k}→{v}" for k, v in col_map.items() if v]))
    st.sidebar.info("Missing (optional) detections: " + ", ".join(missing))

# ---------------------------
# Preprocess / Derived columns
# ---------------------------
# Date parsing and Year column
if col_map["date"]:
    df[col_map["date"]] = pd.to_datetime(df[col_map["date"]], errors="coerce")
    df["Year"] = df[col_map["date"]].dt.year
else:
    df["Year"] = np.nan

# Ensure numeric columns for revenue/ad_spend/conversions
if col_map["revenue"]:
    df[col_map["revenue"]] = pd.to_numeric(df[col_map["revenue"]], errors="coerce")
if col_map["ad_spend"]:
    df[col_map["ad_spend"]] = pd.to_numeric(df[col_map["ad_spend"]], errors="coerce")
if col_map["conversions"]:
    df[col_map["conversions"]] = pd.to_numeric(df[col_map["conversions"]], errors="coerce")

# Compute Profit (Revenue - Ad Spend) if possible
if col_map["revenue"] and col_map["ad_spend"]:
    df["Profit"] = df[col_map["revenue"]].fillna(0) - df[col_map["ad_spend"]].fillna(0)
else:
    # create Profit but filled with NaN so code doesn't break
    df["Profit"] = np.nan

# Compute ROAS safely
if col_map["revenue"] and col_map["ad_spend"]:
    df["ROAS"] = df[col_map["revenue"]] / df[col_map["ad_spend"]].replace({0: np.nan})
else:
    df["ROAS"] = np.nan

# Compute VPC (value per conversion) safely
if col_map["revenue"] and col_map["conversions"]:
    df["VPC"] = df[col_map["revenue"]] / (df[col_map["conversions"]].replace({0: np.nan}))
else:
    df["VPC"] = np.nan

# ---------------------------
# Sidebar Filters (multiple)
# ---------------------------
st.sidebar.header("Filters")

# Channel filter
if col_map["channel"]:
    channel_vals = df[col_map["channel"]].dropna().unique().tolist()
    selected_channels = st.sidebar.multiselect("Channel", options=sorted(channel_vals), default=sorted(channel_vals))
else:
    selected_channels = []

# Service filter
if col_map["service"]:
    service_vals = df[col_map["service"]].dropna().unique().tolist()
    selected_services = st.sidebar.multiselect("Service Type", options=sorted(service_vals), default=sorted(service_vals))
else:
    selected_services = []

# Season filter
if col_map["season"]:
    season_vals = df[col_map["season"]].dropna().unique().tolist()
    selected_seasons = st.sidebar.multiselect("Season", options=sorted(season_vals), default=sorted(season_vals))
else:
    selected_seasons = []

# Time of Day filter
if col_map["time_of_day"]:
    tod_vals = df[col_map["time_of_day"]].dropna().unique().tolist()
    selected_tods = st.sidebar.multiselect("Time of Day", options=sorted(tod_vals), default=sorted(tod_vals))
else:
    selected_tods = []

# Year filter (range if numeric)
if "Year" in df.columns and df["Year"].notna().any():
    years = sorted(df["Year"].dropna().unique().astype(int).tolist())
    if years:
        min_y, max_y = min(years), max(years)
        selected_years = st.sidebar.slider("Year range", min_value=min_y, max_value=max_y, value=(min_y, max_y))
    else:
        selected_years = None
else:
    selected_years = None

# Custom text search (optional)
text_search_col = None
# if a column named 'Customer' or 'Name' exists, allow search
for candidate in ["customer", "name", "client"]:
    found = detect_column(df, [candidate])
    if found:
        text_search_col = found
        break

text_query = None
if text_search_col:
    text_query = st.sidebar.text_input(f"Search {text_search_col}")

# ---------------------------
# Apply Filters to dataframe
# ---------------------------
filtered = df.copy()

if col_map["channel"] and selected_channels:
    filtered = filtered[filtered[col_map["channel"]].isin(selected_channels)]
if col_map["service"] and selected_services:
    filtered = filtered[filtered[col_map["service"]].isin(selected_services)]
if col_map["season"] and selected_seasons:
    filtered = filtered[filtered[col_map["season"]].isin(selected_seasons)]
if col_map["time_of_day"] and selected_tods:
    filtered = filtered[filtered[col_map["time_of_day"]].isin(selected_tods)]
if selected_years:
    filtered = filtered[(filtered["Year"] >= selected_years[0]) & (filtered["Year"] <= selected_years[1])]
if text_query and text_search_col:
    filtered = filtered[filtered[text_search_col].astype(str).str.contains(text_query, case=False, na=False)]

if filtered.empty:
    st.warning("No rows remain after applying filters — please relax filters or upload a dataset with matching values.")
    st.stop()

# ---------------------------
# KPI cards at top
# ---------------------------
col_k1, col_k2, col_k3 = st.columns(3)
total_revenue = filtered[col_map["revenue"]].sum() if col_map["revenue"] in filtered.columns else np.nan
total_profit = filtered["Profit"].sum()
avg_roas = filtered["ROAS"].mean()

col_k1.metric("Total Revenue", f"${total_revenue:,.2f}" if not np.isnan(total_revenue) else "N/A")
col_k2.metric("Total Profit", f"${total_profit:,.2f}" if not np.isnan(total_profit) else "N/A")
col_k3.metric("Average ROAS", f"{avg_roas:.2f}" if not np.isnan(avg_roas) else "N/A")

# ---------------------------
# Tabs: Channel & Service | Time Series | Descriptive
# ---------------------------
tab1, tab2, tab3 = st.tabs(["Channel & Service Analysis", "Time-Series Trends", "Descriptive Statistics"])

# Helper to create side-by-side bars (Revenue vs Profit) and sort descending by Revenue
def plot_compare_bar(df_summary, group_col, revenue_col="Revenue", profit_col="Profit", top_n=None, ax=None, title=""):
    """
    df_summary: dataframe with group_col, revenue_col, profit_col
    group_col: name string
    revenue_col / profit_col: column names in df_summary
    top_n: optional integer to keep only top_n by revenue
    """
    # sort by revenue descending
    df_sorted = df_summary.sort_values(by=revenue_col, ascending=False)
    if top_n:
        df_sorted = df_sorted.head(top_n)

    # melt to wide->long for seaborn hue
    plot_df = df_sorted[[group_col, revenue_col, profit_col]].melt(id_vars=[group_col], value_vars=[revenue_col, profit_col],
                                                                 var_name="Metric", value_name="Value")
    sns.barplot(data=plot_df, x=group_col, y="Value", hue="Metric", order=df_sorted[group_col].tolist(), ax=ax)
    ax.set_title(title)
    ax.set_xlabel(group_col)
    ax.set_ylabel("Value ($)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="Metric")

# === TAB 1 ===
with tab1:
    st.markdown("### Performance by Channel and Service (Revenue vs Profit)")
    c1, c2 = st.columns(2)

    # Channel plot
    with c1:
        if col_map["channel"] and (col_map["revenue"] or "Profit" in filtered.columns):
            grp = filtered.groupby(col_map["channel"]).agg(
                Revenue=(col_map["revenue"], "sum") if col_map["revenue"] else (col_map["revenue"], lambda x: np.nan),
                Profit=("Profit", "sum")
            ).reset_index()
            fig, ax = plt.subplots(figsize=(8, 4))
            plot_compare_bar(grp, group_col=col_map["channel"], revenue_col="Revenue", profit_col="Profit",
                             title="Revenue vs Profit by Channel", ax=ax)
            st.pyplot(fig)
        else:
            st.info("Missing channel or revenue columns for channel plot.")

    # Service plot
    with c2:
        if col_map["service"] and (col_map["revenue"] or "Profit" in filtered.columns):
            grp = filtered.groupby(col_map["service"]).agg(
                Revenue=(col_map["revenue"], "sum") if col_map["revenue"] else (col_map["revenue"], lambda x: np.nan),
                Profit=("Profit", "sum")
            ).reset_index()
            fig, ax = plt.subplots(figsize=(8, 4))
            plot_compare_bar(grp, group_col=col_map["service"], revenue_col="Revenue", profit_col="Profit",
                             title="Revenue vs Profit by Service Type", ax=ax)
            st.pyplot(fig)
        else:
            st.info("Missing service or revenue columns for service plot.")

    # Optionally show top-N selector
    st.markdown("### Top N groups (by Revenue)")
    top_n = st.slider("Show top N groups", min_value=3, max_value=20, value=8)

    # Combined top-N chart across selected grouping (let user choose)
    group_choice = st.selectbox("Group by (for top-N chart)", options=[opt for opt in [col_map["channel"], col_map["service"], col_map["season"]] if opt], index=0 if any([col_map["channel"], col_map["service"], col_map["season"]]) else None)
    if group_choice:
        grp = filtered.groupby(group_choice).agg(
            Revenue=(col_map["revenue"], "sum") if col_map["revenue"] else (col_map["revenue"], lambda x: np.nan),
            Profit=("Profit", "sum")
        ).reset_index()
        fig, ax = plt.subplots(figsize=(10, 5))
        plot_compare_bar(grp, group_col=group_choice, revenue_col="Revenue", profit_col="Profit", top_n=top_n, ax=ax,
                         title=f"Top {top_n} {group_choice} by Revenue (compare Revenue vs Profit)")
        st.pyplot(fig)

# === TAB 2 ===
with tab2:
    st.markdown("### Monthly / Time Trends (Revenue vs Profit)")

    if col_map["date"] and (col_map["revenue"] or "Profit" in filtered.columns):
        # resample monthly
        ts = filtered.set_index(col_map["date"]).resample("M").agg(
            Revenue=(col_map["revenue"], "sum") if col_map["revenue"] else (col_map["revenue"], lambda x: np.nan),
            Profit=("Profit", "sum")
        ).reset_index()
        ts["Month"] = ts[col_map["date"]].dt.strftime("%Y-%m")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.lineplot(data=ts, x="Month", y="Revenue", marker="o", label="Revenue", ax=ax)
        sns.lineplot(data=ts, x="Month", y="Profit", marker="o", label="Profit", ax=ax)
        ax.set_title("Monthly Trend: Revenue vs Profit")
        ax.set_xlabel("Month")
        ax.tick_params(axis="x", rotation=45)
        ax.set_ylabel("Value ($)")
        ax.legend()
        st.pyplot(fig)

        # Also show cumulative or year-over-year if Year exists
        if selected_years:
            st.markdown(f"Showing years {selected_years[0]} to {selected_years[1]}.")
    else:
        st.info("Date column or Revenue/Profit missing — time series not available.")

    # Optional interactive Plotly comparison for detail
    if col_map["date"] and (col_map["revenue"] or "Profit" in filtered.columns):
        st.markdown("#### Interactive chart")
        plot_df = filtered.copy()
        if col_map["date"]:
            plot_df["Month"] = plot_df[col_map["date"]].dt.to_period("M").astype(str)
        else:
            plot_df["Month"] = "Unknown"

        agg = plot_df.groupby("Month").agg(
            Revenue=(col_map["revenue"], "sum") if col_map["revenue"] else (col_map["revenue"], lambda x: np.nan),
            Profit=("Profit", "sum")
        ).reset_index().sort_values("Month")
        fig_px = px.line(agg, x="Month", y=["Revenue", "Profit"], markers=True, title="Interactive Monthly Revenue vs Profit")
        st.plotly_chart(fig_px, use_container_width=True)

# === TAB 3 ===
with tab3:
    st.markdown("### Descriptive Statistics & Distributions")

    # Select numeric columns for summary (smart)
    numeric_candidates = []
    for c in [col_map["revenue"], col_map["ad_spend"], col_map["conversions"], "Profit", "ROAS", "VPC"]:
        if c and c in filtered.columns:
            numeric_candidates.append(c)

    if numeric_candidates:
        st.dataframe(filtered[numeric_candidates].describe().T)
    else:
        st.info("No numeric columns detected for summary statistics.")

    # Distribution plots (Revenue and Profit)
    dist_cols = [c for c in ["Profit", col_map["revenue"]] if c and c in filtered.columns]
    for c in dist_cols:
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.histplot(filtered[c].dropna(), kde=True, ax=ax)
        ax.set_title(f"Distribution: {c}")
        st.pyplot(fig)

    # Revenue by Time of Day and Season (sorted)
    st.markdown("#### Revenue by Time of Day and by Season")
    two_col_1, two_col_2 = st.columns(2)

    with two_col_1:
        if col_map["time_of_day"] and col_map["revenue"]:
            grp = filtered.groupby(col_map["time_of_day"]).agg(Revenue=(col_map["revenue"], "sum"), Profit=("Profit", "sum")).reset_index()
            grp = grp.sort_values("Revenue", ascending=False)
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.barplot(data=grp, x=col_map["time_of_day"], y="Revenue", order=grp[col_map["time_of_day"]].tolist(), ax=ax)
            ax.set_title("Revenue by Time of Day (sorted)")
            ax.tick_params(axis="x", rotation=45)
            st.pyplot(fig)
        else:
            st.info("Time of Day or Revenue column not detected.")

    with two_col_2:
        if col_map["season"] and col_map["revenue"]:
            grp = filtered.groupby(col_map["season"]).agg(Revenue=(col_map["revenue"], "sum"), Profit=("Profit", "sum")).reset_index()
            grp = grp.sort_values("Revenue", ascending=False)
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.barplot(data=grp, x=col_map["season"], y="Revenue", order=grp[col_map["season"]].tolist(), ax=ax)
            ax.set_title("Revenue by Season (sorted)")
            ax.tick_params(axis="x", rotation=45)
            st.pyplot(fig)
        else:
            st.info("Season or Revenue column not detected.")

# ---------------------------
# Footer / data preview
# ---------------------------
st.markdown("---")
st.markdown("### Sample of filtered data")
st.dataframe(filtered.head(50))

st.caption("Tip: If some charts are empty, check your column names or try uploading a dataset with columns like Date, Channel, Service Type, Revenue, Ad Spend.")
