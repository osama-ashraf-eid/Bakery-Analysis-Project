import streamlit as st
import pandas as pd
import plotly.express as px

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

    # Clean columns
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Detect columns automatically
    def find_col(possible_names):
        for name in possible_names:
            for col in df.columns:
                if name in col:
                    return col
        return None

    sales_col = find_col(["sales", "amount", "revenue"])
    profit_col = find_col(["profit", "margin"])
    revenue_col = find_col(["revenue", "income"])
    ad_col = find_col(["ad", "marketing", "spend", "cost"])
    conversion_col = find_col(["conversion", "order", "purchase"])
    category_col = find_col(["category", "type", "group"])
    product_col = find_col(["product", "item", "name"])
    date_col = find_col(["date", "time"])

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["month"] = df[date_col].dt.month_name()
        df["day"] = df[date_col].dt.day_name()

    # Sidebar Filters
    st.sidebar.header("Filters")
    month_filter = st.sidebar.multiselect("Select Month(s)", df["month"].dropna().unique() if "month" in df else [])
    day_filter = st.sidebar.multiselect("Select Day(s)", df["day"].dropna().unique() if "day" in df else [])

    if "month" in df and month_filter:
        df = df[df["month"].isin(month_filter)]
    if "day" in df and day_filter:
        df = df[df["day"].isin(day_filter)]

    # KPIs
    total_sales = df[sales_col].sum() if sales_col else 0
    total_profit = df[profit_col].sum() if profit_col else 0
    total_revenue = df[revenue_col].sum() if revenue_col else total_sales
    total_conversions = df[conversion_col].sum() if conversion_col else 0

    st.markdown("### 📊 Key Metrics")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Sales", f"${total_sales:,.0f}")
    k2.metric("🏦 Total Revenue", f"${total_revenue:,.0f}")
    k3.metric("📈 Total Profit", f"${total_profit:,.0f}")
    k4.metric("🎯 Total Conversions", f"{total_conversions:,.0f}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ------------------ Visualizations ------------------
    st.subheader("📈 Visual Insights")

    # 1️⃣ Sales Trend
    if date_col and sales_col:
        fig_sales = px.line(df, x=date_col, y=sales_col, title="Sales Trend Over Time")
        st.plotly_chart(fig_sales, use_container_width=True)

    # 2️⃣ Profit by Month
    if profit_col and "month" in df:
        fig_profit = px.bar(df.groupby("month")[profit_col].sum().reset_index(),
                            x="month", y=profit_col, title="Profit by Month", color=profit_col)
        st.plotly_chart(fig_profit, use_container_width=True)

    # 3️⃣ Revenue by Category
    if category_col and revenue_col:
        fig_cat = px.bar(df.groupby(category_col)[revenue_col].sum().reset_index(),
                         x=category_col, y=revenue_col, color=category_col, title="Revenue by Category")
        st.plotly_chart(fig_cat, use_container_width=True)

    # 4️⃣ Top Products by Sales
    if product_col and sales_col:
        top_prod = df.groupby(product_col)[sales_col].sum().nlargest(10).reset_index()
        fig_top = px.bar(top_prod, x=product_col, y=sales_col,
                         title="Top 10 Products by Sales", color=sales_col)
        st.plotly_chart(fig_top, use_container_width=True)

    # 5️⃣ Ad Spend vs Revenue (Bubble)
    if ad_col and revenue_col and profit_col:
        fig_sc = px.scatter(df, x=ad_col, y=revenue_col, size=profit_col, color=profit_col,
                            hover_data=[profit_col], title="Ad Spend vs Revenue (Bubble = Profit)")
        st.plotly_chart(fig_sc, use_container_width=True)

    # 6️⃣ Correlation Heatmap
    num_cols = df.select_dtypes(include='number')
    if len(num_cols.columns) > 1:
        corr = num_cols.corr()
        fig_corr = px.imshow(corr, text_auto=True, title="Correlation Heatmap")
        st.plotly_chart(fig_corr, use_container_width=True)

    # 7️⃣ Daily Average Profit
    if "day" in df and profit_col:
        fig_day = px.bar(df.groupby("day")[profit_col].mean().reset_index(),
                         x="day", y=profit_col, title="Average Profit by Day")
        st.plotly_chart(fig_day, use_container_width=True)

    # 8️⃣ Profit Margin by Category
    if category_col and sales_col and profit_col:
        df["profit_margin"] = df[profit_col] / df[sales_col]
        fig_margin = px.bar(df.groupby(category_col)["profit_margin"].mean().reset_index(),
                            x=category_col, y="profit_margin", title="Average Profit Margin by Category")
        st.plotly_chart(fig_margin, use_container_width=True)

    # 9️⃣ Sales vs Conversions Trend
    if date_col and sales_col and conversion_col:
        temp = df.groupby(date_col)[[sales_col, conversion_col]].sum().reset_index()
        fig_conv = px.line(temp, x=date_col, y=[sales_col, conversion_col],
                           title="Sales vs Conversions Over Time")
        st.plotly_chart(fig_conv, use_container_width=True)

else:
    st.info("👆 Please upload a dataset to start analysis.")
