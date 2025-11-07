import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ------------------ Page Setup ------------------
st.set_page_config(page_title="Bakery Sales Dashboard", layout="wide")

# ------------------ Header ------------------
st.title("🥐 Bakery Sales & Marketing Dashboard")
st.image("https://i.pinimg.com/originals/2a/45/18/2a45189ec8766a4604178eb41b059cb1.jpg", use_container_width=True)
st.markdown("### Gain insights into sales, revenue, profit, and marketing performance")

# ------------------ File Upload ------------------
uploaded_file = st.file_uploader("Upload your dataset (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    # Load data
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    # ------------------ Data Preparation ------------------
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["month"] = df["date"].dt.month_name()
        df["day"] = df["date"].dt.day_name()

    # ------------------ Column Mapping ------------------
    col_map = {
        "sales": "sales",
        "profit": "profit",
        "revenue": "revenue" if "revenue" in df.columns else "sales",
        "ad_spend": "ad_spend" if "ad_spend" in df.columns else "cost",
        "conversions": "conversions" if "conversions" in df.columns else None,
        "category": "category" if "category" in df.columns else None,
        "product": "product" if "product" in df.columns else None
    }

    # ------------------ Sidebar Filters ------------------
    st.sidebar.header("Filters")
    month_filter = st.sidebar.multiselect("Select Month(s)", df["month"].dropna().unique())
    day_filter = st.sidebar.multiselect("Select Day(s)", df["day"].dropna().unique())

    if month_filter:
        df = df[df["month"].isin(month_filter)]
    if day_filter:
        df = df[df["day"].isin(day_filter)]

    # ------------------ KPIs ------------------
    total_sales = df[col_map["sales"]].sum()
    total_profit = df[col_map["profit"]].sum()
    total_revenue = df[col_map["revenue"]].sum()
    total_conversions = df[col_map["conversions"]].sum() if col_map["conversions"] else 0

    st.markdown("### 📊 Key Metrics")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("💰 Total Sales", f"${total_sales:,.0f}")
    kpi2.metric("🏦 Total Revenue", f"${total_revenue:,.0f}")
    kpi3.metric("📈 Total Profit", f"${total_profit:,.0f}")
    kpi4.metric("🎯 Total Conversions", f"{total_conversions:,.0f}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ------------------ Visualizations ------------------
    st.subheader("📉 Visual Insights")

    # 1️⃣ Sales Trend
    if "date" in df.columns:
        fig_sales = px.line(df, x="date", y=col_map["sales"], title="Sales Trend Over Time")
        st.plotly_chart(fig_sales, use_container_width=True)

    # 2️⃣ Profit by Month
    fig_profit = px.bar(df.groupby("month")[col_map["profit"]].sum().reset_index(),
                        x="month", y=col_map["profit"], title="Profit by Month")
    st.plotly_chart(fig_profit, use_container_width=True)

    # 3️⃣ Revenue by Category
    if col_map["category"]:
        fig_cat = px.bar(df.groupby(col_map["category"])[col_map["revenue"]].sum().reset_index(),
                         x=col_map["category"], y=col_map["revenue"],
                         color=col_map["category"], title="Revenue by Category")
        st.plotly_chart(fig_cat, use_container_width=True)

    # 4️⃣ Top 10 Products by Sales
    if col_map["product"]:
        top_products = df.groupby(col_map["product"])[col_map["sales"]].sum().nlargest(10).reset_index()
        fig_top = px.bar(top_products, x=col_map["product"], y=col_map["sales"],
                         title="Top 10 Products by Sales", color=col_map["sales"])
        st.plotly_chart(fig_top, use_container_width=True)

    # 5️⃣ Ad Spend vs Revenue (Bubble)
    if col_map["ad_spend"] and col_map["revenue"]:
        scatter_df = df[[col_map["ad_spend"], col_map["revenue"], col_map["profit"]]].dropna()
        fig_sc = px.scatter(scatter_df, x=col_map["ad_spend"], y=col_map["revenue"],
                            size=col_map["profit"], color=col_map["profit"],
                            hover_data=[col_map["profit"]],
                            title="Ad Spend vs Revenue (Bubble = Profit)")
        st.plotly_chart(fig_sc, use_container_width=True)

    # 6️⃣ Correlation Heatmap
    num_cols = df.select_dtypes(include='number')
    if len(num_cols.columns) > 1:
        corr = num_cols.corr()
        fig_corr = px.imshow(corr, text_auto=True, title="Correlation Heatmap")
        st.plotly_chart(fig_corr, use_container_width=True)

    # 7️⃣ Daily Average Profit
    if "day" in df.columns:
        fig_day = px.bar(df.groupby("day")[col_map["profit"]].mean().reset_index(),
                         x="day", y=col_map["profit"], title="Average Profit by Day")
        st.plotly_chart(fig_day, use_container_width=True)

else:
    st.info("👆 Please upload a dataset to start analysis.")
