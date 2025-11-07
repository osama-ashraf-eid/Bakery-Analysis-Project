import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Bakery Performance Dashboard 🍞", layout="wide")

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

    df.columns = df.columns.str.strip()

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

    # Sidebar filters
    filters = {
        "Channel": st.sidebar.multiselect("Select Channel(s):", sorted(df["Channel"].dropna().unique())) if "Channel" in df.columns else [],
        "Service Type": st.sidebar.multiselect("Select Service Type(s):", sorted(df["Service Type"].dropna().unique())) if "Service Type" in df.columns else [],
        "Month": st.sidebar.multiselect("Select Month(s):", sorted(df["Month"].dropna().unique())),
        "Day": st.sidebar.multiselect("Select Day(s):", sorted(df["Day"].dropna().unique())),
        "Season": st.sidebar.multiselect("Select Season(s):", sorted(df["Season"].dropna().unique())) if "Season" in df.columns else [],
        "Time of Day": st.sidebar.multiselect("Select Time(s) of Day:", sorted(df["Time of Day"].dropna().unique())) if "Time of Day" in df.columns else [],
    }

    if "Revenue" in df.columns and "Profit" in df.columns:
        min_rev, max_rev = st.sidebar.slider("Revenue Range ($):", float(df["Revenue"].min()), float(df["Revenue"].max()), (float(df["Revenue"].min()), float(df["Revenue"].max())))
        min_profit, max_profit = st.sidebar.slider("Profit Range ($):", float(df["Profit"].min()), float(df["Profit"].max()), (float(df["Profit"].min()), float(df["Profit"].max())))
    else:
        min_rev, max_rev, min_profit, max_profit = 0, 0, 0, 0

    # Filter Data
    filtered_df = df.copy()
    for key, val in filters.items():
        if val and key in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[key].isin(val)]

    if "Revenue" in filtered_df.columns and "Profit" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["Revenue"].between(min_rev, max_rev)) &
            (filtered_df["Profit"].between(min_profit, max_profit))
        ]

    st.markdown("### 📊 Data Overview")
    st.dataframe(filtered_df.head())

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🏠 Overview", "💵 Revenue & Profit", "📈 Trends", "📊 Relationships",
        "🧍 Customers", "🌤️ Time & Season", "🌍 Regional"
    ])

    # -------------------- TAB 4 — RELATIONSHIPS --------------------
    with tab4:
        st.subheader("Correlations & Relationships")

        # Clean numeric columns
        num_cols = ["Ad Spend", "Revenue", "Profit"]
        num_cols = [col for col in num_cols if col in filtered_df.columns]
        scatter_df = filtered_df[num_cols + ([c for c in ["Channel", "Service Type"] if c in filtered_df.columns])]
        scatter_df = scatter_df.dropna()

        # Convert to numeric safely
        for col in num_cols:
            scatter_df[col] = pd.to_numeric(scatter_df[col], errors="coerce")

        # Remove invalid values for size
        scatter_df = scatter_df[scatter_df["Profit"] > 0]

        if not scatter_df.empty:
            fig_sc = px.scatter(
                scatter_df,
                x="Ad Spend",
                y="Revenue",
                size="Profit",
                color="Channel" if "Channel" in scatter_df.columns else None,
                hover_data=[col for col in ["Service Type", "Profit"] if col in scatter_df.columns],
                title="Ad Spend vs Revenue (Bubble Size = Profit)",
            )
            st.plotly_chart(fig_sc, use_container_width=True)
        else:
            st.warning("⚠️ Not enough valid data for scatter plot.")

        # Correlation Heatmap
        num_df = filtered_df.select_dtypes(include=np.number)
        if not num_df.empty:
            st.markdown("#### Correlation Heatmap")
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.heatmap(num_df.corr(), annot=True, cmap="Blues", ax=ax)
            st.pyplot(fig)

else:
    st.info("📤 Please upload a dataset to begin.")
