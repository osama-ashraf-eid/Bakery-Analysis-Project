# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="Bakery Analytics Dashboard", layout="wide")

# ---------------------------
# Background Image (Bakery Theme)
# ---------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(rgba(255,255,255,0.92), rgba(255,255,255,0.95)),
                    url("https://images.unsplash.com/photo-1608198093002-ad4e005484ec?fm=jpg&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8YmFrZXJ5JTIwcHJvZHVjdHN8ZW58MHx8MHx8fDA%3D&ixlib=rb-4.1.0&q=60&w=3000");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Segoe UI', sans-serif;
    }
    h1, h2, h3, h4 {
        color: #5c4033;
        font-weight: 600;
    }
    .stMetric, .stDataFrame, .stPlotlyChart, .stMarkdown {
        background: rgba(255,255,255,0.9);
        border-radius: 10px;
        padding: 10px;
    }
    #bakery-logo {
        position: absolute;
        top: 25px;
        right: 35px;
        width: 70px;
        opacity: 0.9;
    }
    </style>
    <img id="bakery-logo" src="https://cdn-icons-png.flaticon.com/512/3075/3075977.png" alt="Bakery Logo">
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Header
# ---------------------------
st.title("🥖 Bakery Performance Dashboard")
st.caption("Interactive insights comparing **Revenue** and **Profit** across multiple dimensions")

# ---------------------------
# Upload Data
# ---------------------------
st.sidebar.header("📊 Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded_file is None:
    st.sidebar.info("Please upload your dataset (with columns like Date, Channel, Service Type, Revenue, Ad Spend).")
    st.stop()

if uploaded_file.name.endswith(".csv"):
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_excel(uploaded_file)

# ---------------------------
# Detect columns automatically
# ---------------------------
def detect_col(df, keywords):
    for col in df.columns:
        name = col.lower().strip()
        if any(k in name for k in keywords):
            return col
    return None

col_map = {
    "date": detect_col(df, ["date", "order"]),
    "channel": detect_col(df, ["channel", "platform", "marketing"]),
    "service": detect_col(df, ["service", "category", "product"]),
    "revenue": detect_col(df, ["revenue", "sales", "income"]),
    "ad_spend": detect_col(df, ["ad spend", "spend", "cost", "advertising"]),
    "season": detect_col(df, ["season", "quarter"]),
    "time_of_day": detect_col(df, ["time", "session"]),
}

# ---------------------------
# Data prep
# ---------------------------
if col_map["date"]:
    df[col_map["date"]] = pd.to_datetime(df[col_map["date"]], errors="coerce")
    df["Month"] = df[col_map["date"]].dt.month_name()
    df["Day"] = df[col_map["date"]].dt.day
else:
    df["Month"], df["Day"] = np.nan, np.nan

df["Profit"] = df[col_map["revenue"]] - df[col_map["ad_spend"]]
df["ROAS"] = df[col_map["revenue"]] / df[col_map["ad_spend"]].replace({0: np.nan})

# ---------------------------
# Sidebar Filters
# ---------------------------
st.sidebar.header("🎛️ Filters")

def multi_filter(df, col, name):
    if col and col in df.columns:
        opts = sorted(df[col].dropna().unique().tolist())
        return st.sidebar.multiselect(name, opts, default=opts)
    return []

filters = {
    "channel": multi_filter(df, col_map["channel"], "Channel"),
    "service": multi_filter(df, col_map["service"], "Service Type"),
    "season": multi_filter(df, col_map["season"], "Season"),
    "time": multi_filter(df, col_map["time_of_day"], "Time of Day"),
    "month": multi_filter(df, "Month", "Month"),
    "day": multi_filter(df, "Day", "Day")
}

filtered = df.copy()
for key, vals in filters.items():
    col = col_map.get(key) if key in col_map else key.capitalize()
    if vals and col in filtered.columns:
        filtered = filtered[filtered[col].isin(vals)]

if filtered.empty:
    st.warning("⚠️ No data matches your filter selections.")
    st.stop()

# ---------------------------
# KPIs
# ---------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${filtered[col_map['revenue']].sum():,.2f}")
col2.metric("Total Profit", f"${filtered['Profit'].sum():,.2f}")
col3.metric("Avg ROAS", f"{filtered['ROAS'].mean():.2f}")

# ---------------------------
# Tabs
# ---------------------------
tab1, tab2, tab3 = st.tabs(["📊 Channel & Service", "📈 Trends", "📉 Statistics"])

def compare_bar(df_grouped, group_col, title):
    df_grouped = df_grouped.sort_values("Revenue", ascending=False)
    melted = df_grouped.melt(id_vars=[group_col], value_vars=["Revenue", "Profit"], var_name="Metric", value_name="Value")
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=melted, x=group_col, y="Value", hue="Metric", ax=ax)
    ax.set_title(title)
    ax.set_xlabel(group_col)
    ax.set_ylabel("Value ($)")
    ax.tick_params(axis="x", rotation=45)
    st.pyplot(fig)

with tab1:
    st.markdown("### Revenue vs Profit by Channel & Service")

    c1, c2 = st.columns(2)
    if col_map["channel"]:
        grp = filtered.groupby(col_map["channel"]).agg(Revenue=(col_map["revenue"], "sum"), Profit=("Profit", "sum")).reset_index()
        with c1:
            compare_bar(grp, col_map["channel"], "Revenue vs Profit by Channel")

    if col_map["service"]:
        grp = filtered.groupby(col_map["service"]).agg(Revenue=(col_map["revenue"], "sum"), Profit=("Profit", "sum")).reset_index()
        with c2:
            compare_bar(grp, col_map["service"], "Revenue vs Profit by Service Type")

with tab2:
    st.markdown("### Monthly Revenue vs Profit Trend")
    if col_map["date"]:
        df_month = filtered.set_index(col_map["date"]).resample("M").agg({
            col_map["revenue"]: "sum",
            "Profit": "sum"
        }).reset_index()
        df_month["Month"] = df_month[col_map["date"]].dt.strftime("%Y-%m")
        fig = px.line(df_month, x="Month", y=[col_map["revenue"], "Profit"], markers=True, title="Monthly Revenue vs Profit")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### Descriptive Statistics")
    st.dataframe(filtered[[col_map["revenue"], "Profit", "ROAS"]].describe().T)

    st.markdown("### Profit & Revenue Distribution")
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    sns.histplot(filtered[col_map["revenue"]], kde=True, color="skyblue", ax=ax[0])
    ax[0].set_title("Revenue Distribution")
    sns.histplot(filtered["Profit"], kde=True, color="orange", ax=ax[1])
    ax[1].set_title("Profit Distribution")
    st.pyplot(fig)
