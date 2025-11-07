# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="Bakery Performance Dashboard", layout="wide")

# ---------------------------
# Header Section
# ---------------------------
st.title("🥖 Bakery Performance Dashboard")
st.caption("Interactive insights comparing **Revenue**, **Profit**, and **Ad Spend** across multiple dimensions")

# ✅ Add image banner below the title
st.image(
    "https://images.unsplash.com/photo-1608198093002-ad4e005484ec?fm=jpg&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8YmFrZXJ5JTIwcHJvZHVjdHN8ZW58MHx8MHx8fDA%3D&ixlib=rb-4.1.0&q=60&w=2000",
    use_container_width=True,
    caption="Freshly baked insights 🍞"
)

# ---------------------------
# Sidebar Data Upload
# ---------------------------
st.sidebar.header("📊 Upload Dataset")
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded_file is None:
    st.sidebar.info("Please upload your dataset (CSV or Excel) containing sales, revenue, profit, etc.")
    st.stop()

if uploaded_file.name.endswith(".csv"):
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_excel(uploaded_file)

# ---------------------------
# Auto column detection
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
    "ad_spend": detect_col(df, ["ad spend", "spend", "cost"]),
    "region": detect_col(df, ["region", "area", "country"]),
}

# ---------------------------
# Data Preparation
# ---------------------------
if col_map["date"]:
    df[col_map["date"]] = pd.to_datetime(df[col_map["date"]], errors="coerce")
    df["Month"] = df[col_map["date"]].dt.strftime("%b %Y")

df["Profit"] = df[col_map["revenue"]] - df[col_map["ad_spend"]]
df["ROAS"] = df[col_map["revenue"]] / df[col_map["ad_spend"]].replace({0: np.nan})

# ---------------------------
# Filters
# ---------------------------
st.sidebar.header("🎛️ Filters")

def multiselect_filter(df, col, label):
    if col and col in df.columns:
        options = sorted(df[col].dropna().unique())
        return st.sidebar.multiselect(label, options, default=options)
    return []

filters = {
    "channel": multiselect_filter(df, col_map["channel"], "Channel"),
    "service": multiselect_filter(df, col_map["service"], "Service Type"),
    "region": multiselect_filter(df, col_map["region"], "Region"),
    "month": multiselect_filter(df, "Month", "Month"),
}

filtered = df.copy()
for key, vals in filters.items():
    col = col_map.get(key) if key in col_map else key
    if vals and col in filtered.columns:
        filtered = filtered[filtered[col].isin(vals)]

if filtered.empty:
    st.warning("⚠️ No data found with the selected filters.")
    st.stop()

# ---------------------------
# KPI Metrics
# ---------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${filtered[col_map['revenue']].sum():,.2f}")
col2.metric("Total Profit", f"${filtered['Profit'].sum():,.2f}")
col3.metric("Total Ad Spend", f"${filtered[col_map['ad_spend']].sum():,.2f}")
col4.metric("Average ROAS", f"{filtered['ROAS'].mean():.2f}")

st.markdown("---")

# ---------------------------
# Tabs with Multiple Visualizations
# ---------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Revenue & Profit Breakdown",
    "📈 Trends & Performance",
    "🗺️ Regions & Channels",
    "📉 Correlations & Insights"
])

# Tab 1 - Revenue vs Profit by Categories
with tab1:
    st.subheader("Revenue vs Profit by Category / Channel")

    if col_map["channel"]:
        grp = filtered.groupby(col_map["channel"]).agg({
            col_map["revenue"]: "sum",
            "Profit": "sum"
        }).reset_index()

        fig = px.bar(
            grp, x=col_map["channel"], y=[col_map["revenue"], "Profit"],
            barmode="group", title="Revenue vs Profit by Channel"
        )
        st.plotly_chart(fig, use_container_width=True)

    if col_map["service"]:
        grp2 = filtered.groupby(col_map["service"]).agg({
            col_map["revenue"]: "sum",
            "Profit": "sum"
        }).reset_index()

        fig2 = px.pie(grp2, names=col_map["service"], values=col_map["revenue"],
                      title="Revenue Share by Service Type", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)

# Tab 2 - Trend Analysis
with tab2:
    st.subheader("Monthly Revenue & Profit Trend")

    if col_map["date"]:
        df_month = filtered.set_index(col_map["date"]).resample("M").agg({
            col_map["revenue"]: "sum",
            "Profit": "sum",
            col_map["ad_spend"]: "sum"
        }).reset_index()

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=df_month[col_map["date"]], y=df_month[col_map["revenue"]], mode='lines+markers', name='Revenue'))
        fig3.add_trace(go.Scatter(x=df_month[col_map["date"]], y=df_month["Profit"], mode='lines+markers', name='Profit'))
        fig3.add_trace(go.Bar(x=df_month[col_map["date"]], y=df_month[col_map["ad_spend"]], name='Ad Spend', opacity=0.5))
        fig3.update_layout(title="Revenue, Profit, and Ad Spend Over Time")
        st.plotly_chart(fig3, use_container_width=True)

# Tab 3 - Region / Channel Visuals
with tab3:
    st.subheader("Performance by Region and Channel")

    if col_map["region"] and col_map["channel"]:
        pivot = filtered.pivot_table(
            index=col_map["region"], columns=col_map["channel"],
            values=col_map["revenue"], aggfunc="sum"
        )
        st.dataframe(pivot.style.format("{:,.2f}"))

        fig4 = px.imshow(pivot, text_auto=True, title="Revenue Heatmap by Region & Channel")
        st.plotly_chart(fig4, use_container_width=True)

# Tab 4 - Correlations & Distribution
with tab4:
    st.subheader("Correlations and Distribution Insights")

    corr = filtered[[col_map["revenue"], "Profit", "ROAS", col_map["ad_spend"]]].corr()
    fig5 = px.imshow(corr, text_auto=True, title="Correlation Matrix")
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("### Profit Distribution")
    fig6, ax = plt.subplots(figsize=(6, 3))
    sns.histplot(filtered["Profit"], kde=True, ax=ax)
    st.pyplot(fig6)
