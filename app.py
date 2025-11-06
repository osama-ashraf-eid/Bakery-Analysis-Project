import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Function to load and preprocess data
@st.cache_data
def load_data(file):
    """Loads CSV or Excel file into a DataFrame and prepares it for analysis."""
    try:
        # Assuming the uploaded file is CSV based on the mime type
        df = pd.read_csv(file)
    except Exception as e:
        st.error(f"Error loading the file: {e}")
        return pd.DataFrame()

    # Data Cleaning and Preparation
    # Convert 'Date' column to datetime format
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Ensure financial columns are numeric
    numeric_cols = ['Revenue', 'Ad Spend', 'Conversions']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows with missing values in key columns
    df.dropna(subset=['Date', 'Revenue', 'Ad Spend', 'Conversions', 'Channel', 'Service Type', 'Season', 'Time of Day'], inplace=True)

    # Adding new analytical columns
    df['Profit'] = df['Revenue'] - df['Ad Spend']
    
    # Calculate Return on Ad Spend (ROAS)
    # Avoid division by zero
    df['ROAS'] = df.apply(lambda row: row['Revenue'] / row['Ad Spend'] if row['Ad Spend'] > 0 else 0, axis=1)

    # Calculate Value Per Conversion (VPC)
    df['VPC'] = df.apply(lambda row: row['Revenue'] / row['Conversions'] if row['Conversions'] > 0 else 0, axis=1)

    return df

# Streamlit App Configuration
st.set_page_config(
    page_title="Crust & Crumb Bakery Data Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main Title
st.markdown("""
# 🥐 Crust & Crumb Bakery Data Analysis
A professional application for analyzing operational and marketing performance data.
""", unsafe_allow_html=True)

# -----------------
# 1. Sidebar and File Uploader
# -----------------
with st.sidebar:
    st.header("Data Upload")
    uploaded_file = st.file_uploader(
        "Please upload the data file (CSV)",
        type=['csv']
    )
    st.markdown("---")
    st.header("Data Filtering")
    # Filter options will be populated after data upload

# -----------------
# 2. Analysis Display
# -----------------
if uploaded_file is not None:
    df = load_data(uploaded_file)

    if df.empty:
        st.warning("The application could not read or process the data successfully. Please check the file format.")
        st.stop()

    # Create filter elements in the sidebar
    all_channels = ['All'] + list(df['Channel'].unique())
    selected_channel = st.sidebar.selectbox("Filter by Marketing Channel:", all_channels)

    all_services = ['All'] + list(df['Service Type'].unique())
    selected_service = st.sidebar.selectbox("Filter by Service Type:", all_services)

    all_seasons = ['All'] + list(df['Season'].unique())
    selected_season = st.sidebar.selectbox("Filter by Season:", all_seasons)

    # Apply Filtering
    filtered_df = df.copy()
    if selected_channel != 'All':
        filtered_df = filtered_df[filtered_df['Channel'] == selected_channel]
    if selected_service != 'All':
        filtered_df = filtered_df[filtered_df['Service Type'] == selected_service]
    if selected_season != 'All':
        filtered_df = filtered_df[filtered_df['Season'] == selected_season]

    # Display filtered data preview
    st.subheader("📊 Quick Data Overview (Filtered)")
    st.dataframe(filtered_df.head(), use_container_width=True)
    st.markdown(f"**Total Filtered Records:** {len(filtered_df):,}")

    st.markdown("---")

    # -----------------
    # 3. Key Performance Indicators (KPIs)
    # -----------------
    st.subheader("🔥 Key Performance Indicators (KPIs)")

    # Calculate Metrics
    total_revenue = filtered_df['Revenue'].sum()
    total_ad_spend = filtered_df['Ad Spend'].sum()
    total_conversions = filtered_df['Conversions'].sum()

    # Calculate Derived Metrics
    # Avoid division by zero
    overall_roas = total_revenue / total_ad_spend if total_ad_spend > 0 else 0
    avg_vpc = total_revenue / total_conversions if total_conversions > 0 else 0
    total_profit = filtered_df['Profit'].sum()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total Revenue",
            value=f"${total_revenue:,.2f}",
            delta=f"Profit: ${total_profit:,.2f}",
            delta_color="normal"
        )
    with col2:
        st.metric(
            label="Total Ad Spend",
            value=f"${total_ad_spend:,.2f}"
        )
    with col3:
        st.metric(
            label="Total Conversions",
            value=f"{int(total_conversions):,}"
        )
    with col4:
        st.metric(
            label="Avg. Return on Ad Spend (ROAS)",
            value=f"{overall_roas:.2f}x",
            help="Revenue generated for every $1 spent on ads. Should be > 1.0"
        )
    with col5:
        st.metric(
            label="Avg. Value Per Conversion (VPC)",
            value=f"${avg_vpc:,.2f}",
            help="Average revenue generated by each successful conversion."
        )

    st.markdown("---")

    # -----------------
    # 4. Interactive Visualizations
    # -----------------
    st.subheader("📈 Comparative Analysis and Trends")

    tab1, tab2, tab3 = st.tabs(["Channel & Service Analysis", "Time-Series Trends", "Descriptive Statistics"])

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

            fig_channel = px.bar(
                channel_summary,
                x='Channel',
                y='Total_Revenue',
                color='Avg_ROAS',
                title='Total Revenue by Marketing Channel (Colored by Avg. ROAS)',
                labels={'Total_Revenue': 'Revenue ($)', 'Channel': 'Channel', 'Avg_ROAS': 'Avg. ROAS'},
                template='plotly_white'
            )
            fig_channel.update_layout(xaxis_title='Channel', yaxis_title='Revenue ($)')
            st.plotly_chart(fig_channel, use_container_width=True)

        with col_b:
            # Revenue Distribution by Service Type Pie Chart
            service_summary = filtered_df.groupby('Service Type').agg(
                Total_Revenue=('Revenue', 'sum'),
                Total_Conversions=('Conversions', 'sum'),
                Avg_VPC=('VPC', 'mean')
            ).reset_index().sort_values('Total_Revenue', ascending=False)

            fig_service = px.pie(
                service_summary,
                names='Service Type',
                values='Total_Revenue',
                title='Revenue Distribution by Service Type',
                template='plotly_white',
                hole=0.4 # Donut chart
            )
            fig_service.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
            st.plotly_chart(fig_service, use_container_width=True)

    with tab2:
        st.markdown("#### Monthly Performance Trends")

        # Aggregate data monthly
        df_monthly = filtered_df.set_index('Date').resample('M').agg({
            'Revenue': 'sum',
            'Ad Spend': 'sum',
            'Conversions': 'sum'
        }).reset_index()
        df_monthly['Month'] = df_monthly['Date'].dt.to_period('M').astype(str)

        # Calculate Monthly ROAS
        df_monthly['ROAS'] = df_monthly.apply(
            lambda row: row['Revenue'] / row['Ad Spend'] if row['Ad Spend'] > 0 else 0, axis=1
        )

        # Combined Line Plot for Revenue, Ad Spend, and ROAS
        fig_time = go.Figure()
        fig_time.add_trace(go.Scatter(x=df_monthly['Month'], y=df_monthly['Revenue'], name='Revenue', mode='lines+markers', line=dict(color='#4c72b0')))
        fig_time.add_trace(go.Scatter(x=df_monthly['Month'], y=df_monthly['Ad Spend'], name='Ad Spend', mode='lines+markers', line=dict(color='#dd8452')))

        # Add ROAS on a secondary axis
        fig_time.add_trace(go.Scatter(x=df_monthly['Month'], y=df_monthly['ROAS'], name='ROAS', mode='lines', yaxis='y2', line=dict(color='#55a868', dash='dot')))

        fig_time.update_layout(
            title='Monthly Trend of Revenue, Ad Spend, and ROAS',
            xaxis_title='Month',
            yaxis=dict(title='Value ($)', side='left', showgrid=False),
            yaxis2=dict(title='ROAS', side='right', overlaying='y', showgrid=True),
            template='plotly_white',
            hovermode="x unified"
        )
        st.plotly_chart(fig_time, use_container_width=True)

    with tab3:
        st.markdown("#### Descriptive Statistics for Filtered Data")
        st.dataframe(filtered_df[['Revenue', 'Ad Spend', 'Conversions', 'Profit', 'ROAS', 'VPC']].describe().T)

        st.markdown("#### Revenue Distribution by Time of Day and Season")
        col_c, col_d = st.columns(2)

        with col_c:
            # Revenue by Time of Day
            time_summary = filtered_df.groupby('Time of Day')['Revenue'].sum().reset_index()
            fig_time_of_day = px.bar(
                time_summary,
                x='Time of Day',
                y='Revenue',
                title='Revenue by Time of Day',
                labels={'Revenue': 'Revenue ($)', 'Time of Day': 'Time'},
                color='Revenue',
                template='plotly_white'
            )
            st.plotly_chart(fig_time_of_day, use_container_width=True)

        with col_d:
            # Revenue by Season
            season_summary = filtered_df.groupby('Season')['Revenue'].sum().reset_index()
            fig_season = px.bar(
                season_summary,
                x='Season',
                y='Revenue',
                title='Revenue by Season',
                labels={'Revenue': 'Revenue ($)', 'Season': 'Season'},
                color='Revenue',
                template='plotly_white'
            )
            st.plotly_chart(fig_season, use_container_width=True)


else:
    st.info("Please upload a data file to start the professional analysis.")

st.markdown("---")
st.markdown("**Note:** ROAS is calculated as (Revenue / Ad Spend) and VPC as (Revenue / Conversions).")