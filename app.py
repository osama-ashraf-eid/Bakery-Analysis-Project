# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

from typing import Optional

st.set_page_config(page_title="Bakery Master Dashboard", layout="wide")

# ---------------------------
# Header + Banner
# ---------------------------
st.title("🥖 Bakery Master Dashboard")
st.markdown("**Fresh insights — Revenue vs Profit — multiple filters & advanced visuals**")

# banner image (under title)
BANNER = "https://images.unsplash.com/photo-1608198093002-ad4e005484ec?fm=jpg&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8YmFrZXJ5JTIwcHJvZHVjdHN8ZW58MHx8MHx8fDA%3D&ixlib=rb-4.1.0&q=60&w=2000"
st.image(BANNER, use_container_width=True, caption="Delicious insights baked fresh 🍞")

# ---------------------------
# Upload / Load data
# ---------------------------
st.sidebar.header("1) Upload dataset")
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel (recommended columns: Date, Channel, Service Type, Revenue, Ad Spend, Conversions, Region, Time)", type=["csv", "xlsx"])

if uploaded_file is None:
    st.sidebar.info("Upload a CSV/XLSX file to start. You can still interact when file is uploaded.")
    st.stop()

try:
    if uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Error reading file: {e}")
    st.stop()

# ---------------------------
# Smart column detection
# ---------------------------
def detect_col(df: pd.DataFrame, keywords) -> Optional[str]:
    if df is None:
        return None
    for col in df.columns:
        col_norm = col.lower().strip()
        for kw in keywords:
            if kw.lower() in col_norm:
                return col
    return None

col_map = {
    "date": detect_col(df, ["date", "order", "timestamp"]),
    "channel": detect_col(df, ["channel", "platform", "marketing"]),
    "service": detect_col(df, ["service", "service type", "product", "item", "category"]),
    "product": detect_col(df, ["product", "item", "sku", "name"]),
    "revenue": detect_col(df, ["revenue", "sales", "income", "amount"]),
    "ad_spend": detect_col(df, ["ad spend", "spend", "cost", "advertising"]),
    "conversions": detect_col(df, ["conversion", "conversions", "orders", "purchases", "transactions"]),
    "region": detect_col(df, ["region", "country", "city", "area"]),
    "time": detect_col(df, ["time of day", "time", "hour", "session"]),
    "season": detect_col(df, ["season", "quarter", "period"]),
}

# show detected mapping in sidebar
st.sidebar.subheader("Detected columns")
for k, v in col_map.items():
    st.sidebar.write(f"- **{k}** → `{v}`" if v else f"- **{k}** → _not found_")

# ---------------------------
# Data cleaning & derived columns
# ---------------------------
# Date -> datetime, Year, Month, Day, DayName, Hour if possible
if col_map["date"]:
    df[col_map["date"]] = pd.to_datetime(df[col_map["date"]], errors="coerce")
    df["Year"] = df[col_map["date"]].dt.year
    df["Month"] = df[col_map["date"]].dt.strftime("%b %Y")
    df["Month_name"] = df[col_map["date"]].dt.month_name()
    df["Day"] = df[col_map["date"]].dt.day
    df["DayName"] = df[col_map["date"]].dt.day_name()
    try:
        df["Hour"] = df[col_map["date"]].dt.hour
    except Exception:
        df["Hour"] = np.nan
else:
    df["Year"] = np.nan
    df["Month"] = np.nan
    df["Month_name"] = np.nan
    df["Day"] = np.nan
    df["DayName"] = np.nan
    df["Hour"] = np.nan

# numeric coercion
if col_map["revenue"]:
    df[col_map["revenue"]] = pd.to_numeric(df[col_map["revenue"]], errors="coerce")
if col_map["ad_spend"]:
    df[col_map["ad_spend"]] = pd.to_numeric(df[col_map["ad_spend"]], errors="coerce")
if col_map["conversions"]:
    df[col_map["conversions"]] = pd.to_numeric(df[col_map["conversions"]], errors="coerce")

# Profit
if col_map["revenue"] and col_map["ad_spend"]:
    df["Profit"] = df[col_map["revenue"]].fillna(0) - df[col_map["ad_spend"]].fillna(0)
else:
    # try compute Profit column if exists already, else NaN
    if "Profit" not in df.columns:
        df["Profit"] = np.nan

# ROAS and VPC
if col_map["revenue"] and col_map["ad_spend"]:
    df["ROAS"] = df[col_map["revenue"]] / df[col_map["ad_spend"]].replace({0: np.nan})
else:
    df["ROAS"] = np.nan

if col_map["revenue"] and col_map["conversions"]:
    df["VPC"] = df[col_map["revenue"]] / (df[col_map["conversions"]].replace({0: np.nan}))
else:
    df["VPC"] = np.nan

# ---------------------------
# Sidebar: filters (many)
# ---------------------------
st.sidebar.header("Filters")

# helper to create multiselect with "All" default
def ms(colname, label):
    if colname and colname in df.columns:
        opts = sorted(df[colname].dropna().unique().tolist())
        return st.sidebar.multiselect(label, options=opts, default=opts)
    return []

filters = {}
filters["Channel"] = ms(col_map["channel"], "Channel")
filters["Service"] = ms(col_map["service"], "Service Type")
filters["Product"] = ms(col_map["product"], "Product / Item")
filters["Region"] = ms(col_map["region"], "Region / City / Country")
filters["Season"] = ms(col_map["season"], "Season")
filters["Month"] = ms("Month", "Month")
filters["DayName"] = ms("DayName", "Day of Week")
# Hour filter (if present)
if df["Hour"].notna().any():
    hour_opts = sorted(df["Hour"].dropna().unique().astype(int).tolist())
    filters["Hour"] = st.sidebar.multiselect("Hour (0-23)", options=hour_opts, default=hour_opts)
else:
    filters["Hour"] = []

# Numeric range filters (Revenue / Profit / Ad Spend)
def numeric_range(col):
    if col and col in df.columns and pd.to_numeric(df[col], errors="coerce").notna().any():
        min_v = float(pd.to_numeric(df[col], errors="coerce").min(skipna=True))
        max_v = float(pd.to_numeric(df[col], errors="coerce").max(skipna=True))
        if np.isfinite(min_v) and np.isfinite(max_v):
            return st.sidebar.slider(f"{col} range", min_value=min_v, max_value=max_v, value=(min_v, max_v))
    return None

rev_range = numeric_range(col_map["revenue"])
profit_min = float(df["Profit"].min(skipna=True)) if df["Profit"].notna().any() else 0.0
profit_max = float(df["Profit"].max(skipna=True)) if df["Profit"].notna().any() else 0.0
profit_range = st.sidebar.slider("Profit range", min_value=profit_min, max_value=profit_max, value=(profit_min, profit_max)) if (df["Profit"].notna().any()) else None
ad_range = numeric_range(col_map["ad_spend"])

# Date range filter
date_range = None
if col_map["date"]:
    min_date = df[col_map["date"]].min()
    max_date = df[col_map["date"]].max()
    date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

# text search
search_col = detect_col(df, ["customer", "client", "name"])
search_text = st.sidebar.text_input(f"Search {search_col}" if search_col else "Search text (no column auto-detected)")

# ---------------------------
# Apply filters
# ---------------------------
filtered = df.copy()
# apply multiselect filters
if filters["Channel"] and col_map["channel"]:
    filtered = filtered[filtered[col_map["channel"]].isin(filters["Channel"])]
if filters["Service"] and col_map["service"]:
    filtered = filtered[filtered[ col_map["service"] ].isin(filters["Service"])]
if filters["Product"] and col_map["product"]:
    filtered = filtered[filtered[col_map["product"]].isin(filters["Product"])]
if filters["Region"] and col_map["region"]:
    filtered = filtered[filtered[col_map["region"]].isin(filters["Region"])]
if filters["Season"] and col_map["season"]:
    filtered = filtered[filtered[col_map["season"]].isin(filters["Season"])]
if filters["Month"]:
    filtered = filtered[filtered["Month"].isin(filters["Month"])]
if filters["DayName"]:
    filtered = filtered[filtered["DayName"].isin(filters["DayName"])]
if filters.get("Hour"):
    filtered = filtered[filtered["Hour"].isin(filters["Hour"])]

# numeric ranges
if rev_range and col_map["revenue"] in filtered.columns:
    filtered = filtered[(filtered[col_map["revenue"]] >= rev_range[0]) & (filtered[col_map["revenue"]] <= rev_range[1])]
if profit_range is not None and "Profit" in filtered.columns:
    filtered = filtered[(filtered["Profit"] >= profit_range[0]) & (filtered["Profit"] <= profit_range[1])]
if ad_range and col_map["ad_spend"] in filtered.columns:
    filtered = filtered[(filtered[col_map["ad_spend"]] >= ad_range[0]) & (filtered[col_map["ad_spend"]] <= ad_range[1])]

# date range
if date_range and col_map["date"]:
    start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = filtered[(filtered[col_map["date"]] >= start_d) & (filtered[col_map["date"]] <= end_d)]

# text search
if search_text and search_col:
    filtered = filtered[filtered[search_col].astype(str).str.contains(search_text, case=False, na=False)]

if filtered.empty:
    st.warning("No data after applying filters. Relax filters or check your dataset.")
    st.stop()

# ---------------------------
# Top-level KPIs
# ---------------------------
st.header("Overview KPIs")
k1, k2, k3, k4, k5 = st.columns(5)
total_revenue = float(filtered[col_map["revenue"]].sum()) if col_map["revenue"] and col_map["revenue"] in filtered.columns else np.nan
total_profit = float(filtered["Profit"].sum()) if "Profit" in filtered.columns else np.nan
total_ad = float(filtered[col_map["ad_spend"]].sum()) if col_map["ad_spend"] and col_map["ad_spend"] in filtered.columns else np.nan
avg_roas = float(filtered["ROAS"].mean()) if "ROAS" in filtered.columns else np.nan
total_conv = int(filtered[col_map["conversions"]].sum()) if col_map["conversions"] and col_map["conversions"] in filtered.columns else np.nan

k1.metric("Total Revenue", f"${total_revenue:,.2f}" if not np.isnan(total_revenue) else "N/A")
k2.metric("Total Profit", f"${total_profit:,.2f}" if not np.isnan(total_profit) else "N/A")
k3.metric("Total Ad Spend", f"${total_ad:,.2f}" if not np.isnan(total_ad) else "N/A")
k4.metric("Avg ROAS", f"{avg_roas:.2f}" if not np.isnan(avg_roas) else "N/A")
k5.metric("Conversions", f"{total_conv:,}" if not pd.isna(total_conv) else "N/A")

st.markdown("---")

# ---------------------------
# Tabs with many visualizations
# ---------------------------
tab_overview, tab_sales, tab_trends, tab_rel, tab_geo = st.tabs([
    "Overview", "Sales & Breakdown", "Trends", "Relationships", "Geography"
])

# ---------- Tab: Overview ----------
with tab_overview:
    st.subheader("Summary table & top groups")
    c1, c2 = st.columns([2, 1])
    with c1:
        # Show summary aggregated by Channel/Service/Region in pivot if present
        group_cols = [col_map.get("channel"), col_map.get("service"), col_map.get("region")]
        group_cols = [c for c in group_cols if c]
        if group_cols:
            agg = filtered.groupby(group_cols).agg(
                Revenue=(col_map["revenue"], "sum") if col_map["revenue"] in filtered.columns else ("Profit", "sum"),
                Profit=("Profit", "sum")
            ).reset_index().sort_values("Revenue", ascending=False).head(200)
            st.dataframe(agg.style.format({ "Revenue":"${:,.2f}", "Profit":"${:,.2f}" }), use_container_width=True)
        else:
            st.info("No grouping columns detected for summary table.")
    with c2:
        st.markdown("Top Filters Snapshot")
        st.write("Channels:", filters["Channel"][:5])
        st.write("Services:", filters["Service"][:5])
        st.write("Regions:", filters["Region"][:5])

    st.markdown("### Top N by Revenue / Profit")
    top_n = st.slider("Top N", min_value=3, max_value=30, value=10)

    col_a, col_b = st.columns(2)
    with col_a:
        if col_map["channel"]:
            grp = filtered.groupby(col_map["channel"]).agg(Revenue=(col_map["revenue"], "sum"), Profit=("Profit", "sum")).reset_index()
            grp = grp.sort_values("Revenue", ascending=False).head(top_n)
            fig = px.bar(grp, x=col_map["channel"], y=["Revenue", "Profit"], barmode="group", title=f"Top {top_n} Channels by Revenue")
            st.plotly_chart(fig, use_container_width=True)
    with col_b:
        if col_map["service"]:
            grp2 = filtered.groupby(col_map["service"]).agg(Revenue=(col_map["revenue"], "sum"), Profit=("Profit", "sum")).reset_index()
            grp2 = grp2.sort_values("Profit", ascending=False).head(top_n)
            fig2 = px.treemap(grp2, path=[col_map["service"]], values="Revenue", title=f"Top {top_n} Services by Revenue (Treemap)")
            st.plotly_chart(fig2, use_container_width=True)

# ---------- Tab: Sales & Breakdown ----------
with tab_sales:
    st.subheader("Revenue & Profit breakdowns")

    # Revenue share pie
    if col_map["service"]:
        svc = filtered.groupby(col_map["service"]).agg(Revenue=(col_map["revenue"], "sum")).reset_index().sort_values("Revenue", ascending=False)
        fig_p = px.pie(svc, names=col_map["service"], values="Revenue", title="Revenue share by Service Type", hole=0.35)
        st.plotly_chart(fig_p, use_container_width=True)

    # Top products by profit if product col available
    if col_map["product"]:
        prod = filtered.groupby(col_map["product"]).agg(Revenue=(col_map["revenue"], "sum"), Profit=("Profit", "sum")).reset_index()
        prod = prod.sort_values("Profit", ascending=False).head(15)
        fig_prod = px.bar(prod, x="Profit", y=col_map["product"], orientation="h", title="Top Products by Profit")
        st.plotly_chart(fig_prod, use_container_width=True)

    # Stacked bar by region/service if both exist
    if col_map["region"] and col_map["service"]:
        stacked = filtered.groupby([col_map["region"], col_map["service"]]).agg(Revenue=(col_map["revenue"], "sum")).reset_index()
        pivot = stacked.pivot(index=col_map["region"], columns=col_map["service"], values="Revenue").fillna(0)
        fig_heat = px.imshow(pivot, labels=dict(x="Service", y="Region", color="Revenue"), title="Revenue heat (Region x Service)")
        st.plotly_chart(fig_heat, use_container_width=True)

# ---------- Tab: Trends ----------
with tab_trends:
    st.subheader("Time Trends & Seasonality")

    if col_map["date"] and col_map["revenue"]:
        df_month = filtered.set_index(col_map["date"]).resample("M").agg(
            Revenue=(col_map["revenue"], "sum"),
            Profit=("Profit", "sum"),
            AdSpend=(col_map["ad_spend"], "sum") if col_map["ad_spend"] else ("Profit", "sum")
        ).reset_index().sort_values(col_map["date"])

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_month[col_map["date"]], y=df_month["Revenue"], name="Revenue", mode="lines+markers"))
        fig_line.add_trace(go.Scatter(x=df_month[col_map["date"]], y=df_month["Profit"], name="Profit", mode="lines+markers"))
        if col_map["ad_spend"]:
            fig_line.add_trace(go.Bar(x=df_month[col_map["date"]], y=df_month["AdSpend"], name="Ad Spend", opacity=0.4, yaxis="y2"))
            fig_line.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False))
        fig_line.update_layout(title="Monthly Revenue vs Profit (and Ad Spend)")
        st.plotly_chart(fig_line, use_container_width=True)

        # cumulative
        df_month["cum_revenue"] = df_month["Revenue"].cumsum()
        fig_area = px.area(df_month, x=col_map["date"], y="cum_revenue", title="Cumulative Revenue Over Time")
        st.plotly_chart(fig_area, use_container_width=True)

    # Day-of-week & Hour patterns
    c1, c2 = st.columns(2)
    with c1:
        if "DayName" in filtered.columns:
            dow = filtered.groupby("DayName").agg(Revenue=(col_map["revenue"], "sum"), Profit=("Profit", "sum")).reset_index()
            # order days
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dow["DayName"] = pd.Categorical(dow["DayName"], categories=days_order, ordered=True)
            dow = dow.sort_values("DayName")
            fig_dow = px.bar(dow, x="DayName", y=["Revenue", "Profit"], barmode="group", title="Revenue & Profit by Day of Week")
            st.plotly_chart(fig_dow, use_container_width=True)
    with c2:
        if "Hour" in filtered.columns and filtered["Hour"].notna().any():
            hr = filtered.groupby("Hour").agg(Revenue=(col_map["revenue"], "sum"), Profit=("Profit", "sum")).reset_index().sort_values("Hour")
            fig_hr = px.line(hr, x="Hour", y=["Revenue", "Profit"], markers=True, title="Hour of Day Performance")
            st.plotly_chart(fig_hr, use_container_width=True)

# ---------- Tab: Relationships ----------
with tab_rel:
    st.subheader("Ad Spend vs Revenue (bubble) & Correlations")

    # scatter bubble: AdSpend vs Revenue, size by Profit
    if col_map["ad_spend"] and col_map["revenue"]:
        scatter_df = filtered[[col_map["ad_spend"], col_map["revenue"], "Profit"]].dropna()
        if not scatter_df.empty:
            fig_sc = px.scatter(scatter_df, x=col_map["ad_spend"], y=col_map["revenue"],
                                size="Profit", hover_data=["Profit"], title="Ad Spend vs Revenue (bubble size = Profit)")
            st.plotly_chart(fig_sc, use_container_width=True)
    else:
        st.info("Need both Ad Spend and Revenue columns for scatter chart.")

    # correlation heatmap
    corr_cols = []
    for c in [col_map["revenue"], col_map["ad_spend"], "Profit", "ROAS", col_map["conversions"]]:
        if c and c in filtered.columns:
            corr_cols.append(c)
    if corr_cols:
        corr = filtered[corr_cols].corr()
        fig_corr = px.imshow(corr, text_auto=True, title="Correlation Matrix")
        st.plotly_chart(fig_corr, use_container_width=True)

    # Profit distribution
    st.markdown("### Profit distribution")
    fig_hist, ax = plt.subplots(figsize=(8, 3))
    sns.histplot(filtered["Profit"].dropna(), kde=True, ax=ax)
    ax.set_xlabel("Profit")
    st.pyplot(fig_hist)

# ---------- Tab: Geography ----------
with tab_geo:
    st.subheader("Geographic view (if region/country present)")

    if col_map["region"] and col_map["region"] in filtered.columns:
        # aggregated revenue by region
        agg_reg = filtered.groupby(col_map["region"]).agg(Revenue=(col_map["revenue"], "sum"), Profit=("Profit", "sum")).reset_index().sort_values("Revenue", ascending=False)
        st.dataframe(agg_reg.head(100).style.format({"Revenue":"${:,.2f}", "Profit":"${:,.2f}"}), use_container_width=True)

        # if region values look like countries, attempt choropleth
        sample_vals = agg_reg[col_map["region"]].astype(str).head(20).tolist()
        # Try choropleth if country names
        try:
            fig_map = px.choropleth(agg_reg, locations=col_map["region"], locationmode="country names",
                                     color="Revenue", hover_name=col_map["region"], title="Revenue by Country (if country names detected)")
            st.plotly_chart(fig_map, use_container_width=True)
        except Exception:
            st.info("Region column detected but not suitable for world choropleth. Showing table instead.")
    else:
        st.info("No region column detected. If you have latitude/longitude, we can plot points — add columns like 'lat' and 'lon'.")

# ---------------------------
# Footer: sample of filtered data & download
# ---------------------------
st.markdown("---")
st.subheader("Filtered data sample")
st.dataframe(filtered.head(200), use_container_width=True)

# CSV download
@st.cache_data
def convert_df_to_csv(df_in):
    return df_in.to_csv(index=False).encode('utf-8')

csv_bytes = convert_df_to_csv(filtered)
st.download_button("Download filtered data (CSV)", data=csv_bytes, file_name="filtered_data.csv", mime="text/csv")

st.caption("Tip: If some charts are empty, check dataset column names or try uploading a dataset with typical columns: Date, Channel, Service Type, Revenue, Ad Spend, Conversions, Region.")
