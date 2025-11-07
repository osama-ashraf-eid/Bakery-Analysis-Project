import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Bakery Analytics Dashboard", layout="wide")

st.title("🍞 Bakery Performance Analysis Dashboard")
st.markdown("This interactive dashboard allows you to analyze bakery sales, ad spend, and performance trends.")

# -----------------
# 1. Data Upload / Loading Section
# -----------------
st.sidebar.header("📂 Data Source")

uploaded_file = st.sidebar.file_uploader("Upload your dataset (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()
else:
    st.warning("Please upload a dataset file to begin.")
    st.stop()

# -----------------
# 2. Basic Data Cleaning
# -----------------
if 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

df = df.dropna(subset=['Revenue', 'Ad Spend'])
df['ROAS'] = df['Revenue'] / df['Ad Spend']
df['VPC'] = df['Revenue'] / (df['Conversions'] + 1)

# -----------------
# 3. Filters
# -----------------
st.sidebar.header("🔍 Filters")

channels = df['Channel'].unique() if 'Channel' in df.columns else []
services = df['Service Type'].unique() if 'Service Type' in df.columns else []

selected_channel = st.sidebar.multiselect("Select Channel(s)", channels, default=channels)
selected_service = st.sidebar.multiselect("Select Service Type(s)", services, default=services)

filtered_df = df[
    (df['Channel'].isin(selected_channel)) &
    (df['Service Type'].isin(selected_service))
]

# -----------------
# 4. Interactive Visualizations (Matplotlib + Seaborn)
# -----------------
st.subheader("📈 Comparative Analysis and Trends")

tab1, tab2, tab3 = st.tabs(["Channel & Service Analysis", "Time-Series Trends", "Descriptive Statistics"])

# TAB 1 — Channel & Service Analysis
with tab1:
    st.markdown("#### Performance Comparison by Channel and Service Type")

    col_a, col_b = st.columns(2)

    with col_a:
        # Revenue by Marketing Channel Bar Chart
        channel_summary = filtered_df.groupby('Channel').agg(
            Total_Revenue=('Revenue', 'sum'),
            Total_Spend=('Ad Spend', 'sum'),
            Avg_ROAS=('ROAS', 'mean')
        ).reset_index().sort_values('Total_Revenue', ascending=False)

        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(
            data=channel_summary,
            x='Channel',
            y='Total_Revenue',
            palette='Blues_d',
            ax=ax
        )
        ax.set_title('Total Revenue by Marketing Channel', fontsize=12)
        ax.set_xlabel('Channel')
        ax.set_ylabel('Revenue ($)')
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    with col_b:
        # Revenue Distribution by Service Type Pie Chart
        service_summary = filtered_df.groupby('Service Type')['Revenue'].sum().reset_index()

        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(
            service_summary['Revenue'],
            labels=service_summary['Service Type'],
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'edgecolor': 'white'}
        )
        ax.set_title('Revenue Distribution by Service Type')
        st.pyplot(fig)

# TAB 2 — Time-Series Trends
with tab2:
    st.markdown("#### Monthly Performance Trends")

    if 'Date' not in filtered_df.columns:
        st.error("⚠️ The dataset must include a 'Date' column for time-series analysis.")
    else:
        # Aggregate data monthly
        df_monthly = filtered_df.set_index('Date').resample('M').agg({
            'Revenue': 'sum',
            'Ad Spend': 'sum'
        }).reset_index()

        df_monthly['Month'] = df_monthly['Date'].dt.strftime('%Y-%m')

        fig, ax1 = plt.subplots(figsize=(8, 4))
        sns.lineplot(data=df_monthly, x='Month', y='Revenue', marker='o', label='Revenue', ax=ax1)
        sns.lineplot(data=df_monthly, x='Month', y='Ad Spend', marker='o', label='Ad Spend', ax=ax1)
        ax1.set_title('Monthly Trend of Revenue and Ad Spend')
        ax1.set_xlabel('Month')
        ax1.set_ylabel('Value ($)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend()
        st.pyplot(fig)

# TAB 3 — Descriptive Statistics
with tab3:
    st.markdown("#### Descriptive Statistics for Filtered Data")
    st.dataframe(filtered_df[['Revenue', 'Ad Spend', 'Conversions', 'Profit', 'ROAS', 'VPC']].describe().T)

    st.markdown("#### Revenue Distribution by Time of Day and Season")
    col_c, col_d = st.columns(2)

    with col_c:
        if 'Time of Day' in filtered_df.columns:
            time_summary = filtered_df.groupby('Time of Day')['Revenue'].sum().reset_index()
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(data=time_summary, x='Time of Day', y='Revenue', palette='viridis', ax=ax)
            ax.set_title('Revenue by Time of Day')
            ax.set_xlabel('Time of Day')
            ax.set_ylabel('Revenue ($)')
            st.pyplot(fig)
        else:
            st.info("No 'Time of Day' column found.")

    with col_d:
        if 'Season' in filtered_df.columns:
            season_summary = filtered_df.groupby('Season')['Revenue'].sum().reset_index()
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(data=season_summary, x='Season', y='Revenue', palette='mako', ax=ax)
            ax.set_title('Revenue by Season')
            ax.set_xlabel('Season')
            ax.set_ylabel('Revenue ($)')
            st.pyplot(fig)
        else:
            st.info("No 'Season' column found.")
