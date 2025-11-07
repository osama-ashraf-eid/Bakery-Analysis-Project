import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

# --------------------------------
# PAGE CONFIGURATION
# --------------------------------
st.set_page_config(page_title="Bakery Performance Dashboard 🍞", layout="wide")

st.title("🥖 Bakery Performance Analytics Dashboard")
st.image(
    "https://images.unsplash.com/photo-1608198093002-ad4e005484ec?fm=jpg&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8YmFrc2Vy/products&lib=rb-4.1.0&q=60&w=2000",
    use_container_width=True,
    caption="Bakery Operations & Sales Insights",
)
st.markdown("---")

# --------------------------------
# SIDEBAR SETUP (PAGES FIRST)
# --------------------------------
st.sidebar.header("🔍 Filters")

# --------------------------------
# 1. DASHBOARD PAGE NAVIGATION (MOVED TO TOP OF SIDEBAR)
# --------------------------------
st.sidebar.markdown("#### Select Analysis Page")
page_selection = st.sidebar.radio(
    " ", # Empty label for cleaner appearance
    ("🏠 Overview & Key Performance Indicators (KPIs)", "📈 Trends & Performance", "💸 In-Depth Financial Analysis", "📊 Relationships & Comparisons")
)
st.sidebar.markdown("---")


# --------------------------------
# 2. DATA LOADING AND FILTERS
# --------------------------------
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    
    @st.cache_data
    def load_data(uploaded_file):
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
        except Exception as e:
            st.error(f"❌ Error reading data: {e}")
            return pd.DataFrame()

        df.columns = df.columns.str.strip()

        # Date column processing
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df.dropna(subset=['Date'], inplace=True)
            if not df.empty:
                df["Month"] = df["Date"].dt.month_name()
                df["Day"] = df["Date"].dt.day_name()
            else:
                return pd.DataFrame()
        else:
            return pd.DataFrame()

        # Profit calculation (Profit = Revenue - Ad Spend)
        if "Revenue" in df.columns and "Ad Spend" in df.columns:
            for col in ["Revenue", "Ad Spend", "Conversions"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            df["Profit"] = df["Revenue"] - df["Ad Spend"]
        
        # Order days of the week for visualization
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if 'Day' in df.columns:
            if df['Day'].dtype != 'category':
                df['Day'] = pd.Categorical(df['Day'], categories=day_order, ordered=True)

        return df

    df = load_data(uploaded_file)
    
    if df.empty or "Date" not in df.columns:
        st.error("❌ Could not load data or 'Date' column is missing/invalid.")
        st.stop()
    
    st.sidebar.markdown("#### Categorical Filters")
    
    # ----------------------
    # Sidebar Filters (All unique values are included by default)
    # ----------------------
    filters = {}
    if "Channel" in df.columns: filters["Channel"] = st.sidebar.multiselect("Select Channel(s):", options=sorted(df["Channel"].dropna().unique()), default=sorted(df["Channel"].dropna().unique()))
    if "Service Type" in df.columns: filters["Service Type"] = st.sidebar.multiselect("Select Service Type(s):", options=sorted(df["Service Type"].dropna().unique()), default=sorted(df["Service Type"].dropna().unique()))
    if "Month" in df.columns: filters["Month"] = st.sidebar.multiselect("Select Month(s):", options=sorted(df["Month"].dropna().unique()), default=sorted(df["Month"].dropna().unique()))
    if "Day" in df.columns: filters["Day"] = st.sidebar.multiselect("Select Day(s):", options=df["Day"].cat.categories.tolist() if 'category' in str(df['Day'].dtype) else sorted(df["Day"].dropna().unique()), default=df["Day"].cat.categories.tolist() if 'category' in str(df['Day'].dtype) else sorted(df["Day"].dropna().unique()))
    if "Season" in df.columns: filters["Season"] = st.sidebar.multiselect("Select Season(s):", options=sorted(df["Season"].dropna().unique()), default=sorted(df["Season"].dropna().unique()))
    if "Time of Day" in df.columns: filters["Time of Day"] = st.sidebar.multiselect("Select Time(s) of Day:", options=sorted(df["Time of Day"].dropna().unique()), default=sorted(df["Time of Day"].dropna().unique()))
    if "Customer Type" in df.columns: filters["Customer Type"] = st.sidebar.multiselect("Select Customer Type(s):", options=sorted(df["Customer Type"].dropna().unique()), default=sorted(df["Customer Type"].dropna().unique()))

    # NOTE: Revenue and Profit Range Sliders have been removed as requested.

    # ----------------------
    # Apply Filtering
    # ----------------------
    filtered_df = df.copy()
    for key, val in filters.items():
        if val and key in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[key].isin(val)]

    # NOTE: The range filtering logic has been removed as requested.
        
    if filtered_df.empty:
        st.warning("⚠️ No data matches the selected filters. Please adjust your selections.")
        st.stop()


    # --------------------------------
    # KPI CARD FUNCTION
    # --------------------------------
    def kpi_card(label, value, is_currency=True, color='blue', help_text=""):
        formatted_value = f"${value:,.2f}" if is_currency else f"{value:,.0f}"
        st.metric(label=label, value=formatted_value, help=help_text)

    st.markdown("### 🔍 Filtered Data Sample")
    st.dataframe(filtered_df.head())
    st.markdown("---")

    # --------------------------------
    # PAGE 1: OVERVIEW & KPIS
    # --------------------------------
    if page_selection == "🏠 Overview & Key Performance Indicators (KPIs)":
        st.header("🏠 Overview & Business Performance")
        
        # ----------------------
        # Key Performance Indicators (KPIs)
        # ----------------------
        total_revenue = filtered_df["Revenue"].sum()
        total_profit = filtered_df["Profit"].sum()
        total_conversions = filtered_df["Conversions"].sum()
        total_ad_spend = filtered_df["Ad Spend"].sum()
        profit_margin = (total_profit / total_revenue) if total_revenue > 0 else 0
        roas = (total_revenue / total_ad_spend) if total_ad_spend > 0 else 0
        aov = (total_revenue / filtered_df.shape[0]) if filtered_df.shape[0] > 0 else 0
        
        st.markdown("#### Key Performance Indicators (KPIs)")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1: kpi_card("Total Revenue", total_revenue)
        with col2: kpi_card("Total Profit", total_profit)
        with col3: kpi_card("Total Conversions", total_conversions, is_currency=False)
        with col4: kpi_card("Profit Margin (%)", profit_margin * 100, is_currency=False, help_text="Profit / Revenue", color='green')
        with col5: kpi_card("ROAS", roas, is_currency=False, help_text="Revenue / Ad Spend", color='green')
        with col6: kpi_card("AOV", aov, help_text="Total Revenue / Transactions")
        
        st.markdown("---")
        
        # ----------------------
        # 7 Visualizations for the Page
        # ----------------------
        st.markdown("#### Analysis by Channel, Customer, and Service (7 Charts)")
        
        col_a, col_b = st.columns(2)
        
        # 1. Total Revenue by Channel - Bar Chart
        with col_a:
            if "Channel" in filtered_df.columns:
                channel_rev = filtered_df.groupby("Channel")["Revenue"].sum().sort_values(ascending=False).reset_index()
                fig_channel_rev = px.bar(channel_rev, x="Channel", y="Revenue", 
                                          title="1. Total Revenue by Channel", color="Channel",
                                          template="plotly_white")
                st.plotly_chart(fig_channel_rev, use_container_width=True)
            else: st.info("Channel column is not available for analysis.")
            
        # 2. Conversion Distribution by Customer Type - Pie Chart
        with col_b:
            if "Customer Type" in filtered_df.columns:
                cust_type_dist = filtered_df["Customer Type"].value_counts().reset_index()
                cust_type_dist.columns = ['Customer Type', 'Count']
                fig_cust_type = px.pie(cust_type_dist, names="Customer Type", values="Count", 
                                       title="2. Conversion Distribution by Customer Type", 
                                       template="plotly_white")
                st.plotly_chart(fig_cust_type, use_container_width=True)
            else: st.info("Customer Type column is not available for analysis.")

        col_c, col_d, col_e = st.columns(3)
        
        # 3. Total Profit by Service Type - Bar Chart
        with col_c:
            if "Service Type" in filtered_df.columns:
                service_profit = filtered_df.groupby("Service Type")["Profit"].sum().sort_values(ascending=False).reset_index()
                fig_service_profit = px.bar(service_profit, x="Service Type", y="Profit", 
                                          title="3. Total Profit by Service Type", color="Service Type",
                                          template="plotly_white")
                st.plotly_chart(fig_service_profit, use_container_width=True)
            else: st.info("Service Type column is not available for analysis.")

        # 4. Average Conversions by Channel - Bar Chart
        with col_d:
            if "Channel" in filtered_df.columns:
                channel_conv_avg = filtered_df.groupby("Channel")["Conversions"].mean().sort_values(ascending=False).reset_index()
                fig_channel_conv_avg = px.bar(channel_conv_avg, x="Channel", y="Conversions", 
                                            title="4. Avg Conversions by Channel", color="Channel",
                                            template="plotly_white", labels={'Conversions':'Avg Conversions'})
                st.plotly_chart(fig_channel_conv_avg, use_container_width=True)
            else: st.info("Channel column is not available for analysis.")
            
        # 5. Total Ad Spend by Customer Type - Bar Chart
        with col_e:
            if "Customer Type" in filtered_df.columns:
                cust_ad_spend = filtered_df.groupby("Customer Type")["Ad Spend"].sum().sort_values(ascending=False).reset_index()
                fig_cust_ad_spend = px.bar(cust_ad_spend, x="Customer Type", y="Ad Spend", 
                                            title="5. Total Ad Spend by Customer Type", color="Customer Type",
                                            template="plotly_white")
                st.plotly_chart(fig_cust_ad_spend, use_container_width=True)
            else: st.info("Customer Type column is not available for analysis.")

        col_f, col_g = st.columns(2)

        # 6. Average Revenue: Service & Customer Type - Bar Chart
        with col_f:
            if "Service Type" in filtered_df.columns and "Customer Type" in filtered_df.columns:
                service_cust_rev = filtered_df.groupby(["Service Type", "Customer Type"])["Revenue"].mean().reset_index()
                fig_service_cust_rev = px.bar(service_cust_rev, x="Service Type", y="Revenue", 
                                              color="Customer Type", title="6. Avg Revenue: Service & Customer Type",
                                              barmode='group', template="plotly_white")
                st.plotly_chart(fig_service_cust_rev, use_container_width=True)
            else: st.info("Service Type or Customer Type columns are not available.")

        # 7. Cumulative Profit by Channel - Area Chart
        with col_g:
            if "Channel" in filtered_df.columns:
                channel_profit_sum = filtered_df.groupby("Channel")["Profit"].sum().reset_index()
                fig_funnel_area = px.area(channel_profit_sum, x="Channel", y="Profit", 
                                          title="7. Cumulative Profit by Channel", 
                                          template="plotly_white", line_group="Channel")
                st.plotly_chart(fig_funnel_area, use_container_width=True)
            else: st.info("Channel column is not available for analysis.")
            
    # --------------------------------
    # PAGE 2: TRENDS & PERFORMANCE
    # --------------------------------
    elif page_selection == "📈 Trends & Performance":
        st.header("📈 Performance Trends Over Time")
        
        # Aggregate data by Date
        daily_trends = filtered_df.groupby("Date")[["Revenue", "Profit", "Ad Spend", "Conversions"]].sum().reset_index()
        
        # 1. Daily Revenue and Profit Trend - Line Chart
        st.markdown("#### 1. Daily Revenue and Profit Trend (7 Charts)")
        fig_rev_trend = px.line(daily_trends, x="Date", y=["Revenue", "Profit"], 
                                title="Daily Revenue and Profit Trend",
                                labels={"value": "Amount ($)", "variable": "Metric"},
                                template="plotly_white")
        st.plotly_chart(fig_rev_trend, use_container_width=True)
        st.markdown("---")

        col1, col2 = st.columns(2)
        
        # 2. Daily Conversions Trend - Line Chart
        with col1:
            fig_conv_trend = px.line(daily_trends, x="Date", y="Conversions", 
                                     title="2. Daily Conversions Trend",
                                     template="plotly_white")
            st.plotly_chart(fig_conv_trend, use_container_width=True)

        # 3. Daily Ad Spend Trend - Line Chart
        with col2:
            fig_ad_trend = px.line(daily_trends, x="Date", y="Ad Spend", 
                                   title="3. Daily Ad Spend Trend",
                                   template="plotly_white", color_discrete_sequence=['red'])
            st.plotly_chart(fig_ad_trend, use_container_width=True)

        st.markdown("---")

        col3, col4, col5 = st.columns(3)
        
        # 4. Total Profit by Day of Week - Bar Chart
        with col3:
            day_profit = filtered_df.groupby("Day")["Profit"].sum().reset_index()
            # Ensure correct day of week order
            day_profit['Day'] = pd.Categorical(day_profit['Day'], categories=df['Day'].cat.categories, ordered=True)
            day_profit = day_profit.sort_values('Day')

            fig_day_profit = px.bar(day_profit, x="Day", y="Profit", 
                                    title="4. Total Profit by Day of Week", 
                                    template="plotly_white")
            st.plotly_chart(fig_day_profit, use_container_width=True)

        # 5. Total Revenue by Time of Day - Bar Chart
        with col4:
            if "Time of Day" in filtered_df.columns:
                time_rev = filtered_df.groupby("Time of Day")["Revenue"].sum().reset_index()
                fig_time_rev = px.bar(time_rev, x="Time of Day", y="Revenue", 
                                      title="5. Total Revenue by Time of Day", 
                                      template="plotly_white", color="Time of Day")
                st.plotly_chart(fig_time_rev, use_container_width=True)
            else: st.info("Time of Day column is not available.")
            
        # 6. Average Cost Per Conversion (CPC) by Channel - Bar Chart
        with col5:
            if "Channel" in filtered_df.columns:
                cpc_data = filtered_df.groupby("Channel").agg(
                    Total_Ad_Spend=('Ad Spend', 'sum'),
                    Total_Conversions=('Conversions', 'sum')
                ).reset_index()
                cpc_data['CPC'] = np.where(cpc_data['Total_Conversions'] > 0, cpc_data['Total_Ad_Spend'] / cpc_data['Total_Conversions'], 0)
                cpc_data = cpc_data.sort_values('CPC', ascending=False)
                
                fig_cpc = px.bar(cpc_data, x="Channel", y="CPC", 
                                title="6. Avg Cost Per Conversion (CPC) by Channel", 
                                template="plotly_white", color="Channel")
                st.plotly_chart(fig_cpc, use_container_width=True)
            else: st.info("Channel column is not available.")

        # 7. Total Profit by Month - Bar Chart
        if "Month" in filtered_df.columns:
            st.markdown("#### 7. Monthly Profit Distribution")
            month_profit = filtered_df.groupby("Month")["Profit"].sum().reset_index()
            fig_month_profit = px.bar(month_profit, x="Month", y="Profit", 
                                    title="Total Profit by Month", 
                                    template="plotly_white")
            st.plotly_chart(fig_month_profit, use_container_width=True)
        else: st.info("Month column is not available.")
        
    # --------------------------------
    # PAGE 3: IN-DEPTH FINANCIAL ANALYSIS
    # --------------------------------
    elif page_selection == "💸 In-Depth Financial Analysis":
        st.header("💸 Financial Performance & Profit Analysis")

        # 1. Ad Spend vs. Revenue (Bubble Size = Profit) - Scatter Plot
        st.markdown("#### 1. Ad Spend vs. Revenue (Bubble Size = Profit) (7 Charts)")
        
        num_cols = ["Ad Spend", "Revenue", "Profit"]
        scatter_df = filtered_df[num_cols + ([c for c in ["Channel", "Service Type"] if c in filtered_df.columns])]
        scatter_df = scatter_df.dropna(subset=num_cols)

        # Remove invalid values for size (Profit <= 0)
        scatter_df = scatter_df[scatter_df["Profit"] > 0]
        
        if not scatter_df.empty:
            fig_sc = px.scatter(
                scatter_df,
                x="Ad Spend",
                y="Revenue",
                size="Profit",
                color="Channel" if "Channel" in scatter_df.columns else None,
                hover_data=[col for col in ["Service Type", "Profit"] if col in scatter_df.columns],
                title="Ad Spend vs Revenue Relationship (Bubble Size = Profit)",
                template="plotly_white"
            )
            st.plotly_chart(fig_sc, use_container_width=True)
        else:
            st.warning("⚠️ Not enough valid data for scatter plot.")
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        # 2. Average Revenue by Season - Bar Chart
        with col1:
            if "Season" in filtered_df.columns:
                season_rev_avg = filtered_df.groupby("Season")["Revenue"].mean().reset_index()
                fig_season_rev = px.bar(season_rev_avg, x="Season", y="Revenue", 
                                         title="2. Average Revenue by Season", color="Season",
                                         template="plotly_white", labels={'Revenue':'Avg Revenue'})
                st.plotly_chart(fig_season_rev, use_container_width=True)
            else: st.info("Season column is not available.")
            
        # 3. Revenue Distribution - Histogram
        with col2:
            fig_hist_rev = px.histogram(filtered_df, x="Revenue", nbins=20, 
                                        title="3. Revenue Distribution", 
                                        template="plotly_white")
            st.plotly_chart(fig_hist_rev, use_container_width=True)
            
        # 4. Profit Distribution by Channel - Box Plot
        with col3:
            if "Channel" in filtered_df.columns:
                fig_box_profit = px.box(filtered_df, x="Channel", y="Profit", 
                                        title="4. Profit Distribution by Channel", 
                                        template="plotly_white")
                st.plotly_chart(fig_box_profit, use_container_width=True)
            else: st.info("Channel column is not available.")

        st.markdown("---")

        col4, col5 = st.columns(2)
        
        # 5. Correlation Heatmap
        with col4:
            st.markdown("#### 5. Correlation Heatmap")
            num_df = filtered_df.select_dtypes(include=np.number)
            if not num_df.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                sns.heatmap(num_df.corr(), annot=True, cmap="Blues", fmt=".2f", linewidths=.5, ax=ax)
                plt.title("Correlation Heatmap")
                st.pyplot(fig)
            else:
                st.warning("⚠️ Not enough numeric columns for correlation calculation.")
                
        # 6. Ad Spend and Conversions by Channel - Bar Chart
        with col5:
            if "Channel" in filtered_df.columns:
                ad_conv_by_channel = filtered_df.groupby("Channel")[["Ad Spend", "Conversions"]].sum().reset_index()
                fig_ad_conv = px.bar(ad_conv_by_channel, x="Channel", y=["Ad Spend", "Conversions"], 
                                     title="6. Ad Spend and Conversions by Channel", 
                                     barmode='group', template="plotly_white")
                st.plotly_chart(fig_ad_conv, use_container_width=True)
            else: st.info("Channel column is not available.")
        
        # 7. Average Return on Ad Spend (ROAS) by Service Type - Bar Chart
        st.markdown("#### 7. Average ROAS by Service Type")
        if "Service Type" in filtered_df.columns:
            roas_data = filtered_df.groupby("Service Type").agg(
                Total_Revenue=('Revenue', 'sum'),
                Total_Ad_Spend=('Ad Spend', 'sum')
            ).reset_index()
            roas_data['ROAS'] = np.where(roas_data['Total_Ad_Spend'] > 0, roas_data['Total_Revenue'] / roas_data['Total_Ad_Spend'], 0)
            roas_data = roas_data.sort_values('ROAS', ascending=False)
            
            fig_roas = px.bar(roas_data, x="Service Type", y="ROAS", 
                            title="Average ROAS by Service Type", 
                            template="plotly_white", color="Service Type")
            st.plotly_chart(fig_roas, use_container_width=True)
        else: st.info("Service Type column is not available.")

    # --------------------------------
    # PAGE 4: RELATIONSHIPS & COMPARISONS
    # --------------------------------
    elif page_selection == "📊 Relationships & Comparisons":
        st.header("📊 Variable Comparisons and Interactions")
        
        col1, col2 = st.columns(2)
        
        # 1. Monthly Revenue by Channel - Stacked Bar Chart
        with col1:
            if "Month" in filtered_df.columns and "Channel" in filtered_df.columns:
                monthly_channel_rev = filtered_df.groupby(["Month", "Channel"])["Revenue"].sum().reset_index()
                fig_monthly_channel_rev = px.bar(monthly_channel_rev, x="Month", y="Revenue", color="Channel", 
                                                 title="1. Monthly Revenue by Channel", 
                                                 template="plotly_white")
                st.plotly_chart(fig_monthly_channel_rev, use_container_width=True)
            else: st.info("Month and Channel columns are not available.")

        # 2. Profit by Season and Service Type - Stacked Bar Chart
        with col2:
            if "Season" in filtered_df.columns and "Service Type" in filtered_df.columns:
                season_service_profit = filtered_df.groupby(["Season", "Service Type"])["Profit"].sum().reset_index()
                fig_season_service_profit = px.bar(season_service_profit, x="Season", y="Profit", color="Service Type", 
                                                   title="2. Profit by Season and Service Type", 
                                                   template="plotly_white")
                st.plotly_chart(fig_season_service_profit, use_container_width=True)
            else: st.info("Season and Service Type columns are not available.")

        st.markdown("---")

        col3, col4, col5 = st.columns(3)
        
        # 3. Average Revenue: Day of Week & Customer Type - Grouped Bar Chart
        with col3:
            if "Day" in filtered_df.columns and "Customer Type" in filtered_df.columns:
                day_cust_rev = filtered_df.groupby(["Day", "Customer Type"])["Revenue"].mean().reset_index()
                # Ensure correct day of week order
                day_cust_rev['Day'] = pd.Categorical(day_cust_rev['Day'], categories=df['Day'].cat.categories, ordered=True)
                day_cust_rev = day_cust_rev.sort_values('Day')
                
                fig_day_cust_rev = px.bar(day_cust_rev, x="Day", y="Revenue", color="Customer Type", 
                                          title="3. Avg Revenue: Day of Week & Customer Type", barmode='group',
                                          template="plotly_white")
                st.plotly_chart(fig_day_cust_rev, use_container_width=True)
            else: st.info("Day and Customer Type columns are not available.")

        # 4. Profit Distribution: Time of Day & Channel - Violin Plot
        with col4:
            if "Time of Day" in filtered_df.columns and "Channel" in filtered_df.columns:
                fig_violin_profit = px.violin(filtered_df, y="Profit", x="Time of Day", color="Channel", 
                                              box=True, points="all", title="4. Profit Distribution: Time of Day & Channel",
                                              template="plotly_white")
                st.plotly_chart(fig_violin_profit, use_container_width=True)
            else: st.info("Time of Day and Channel columns are not available.")
            
        # 5. Ad Spend vs. Conversions by Service Type - Scatter Plot
        with col5:
            if "Service Type" in filtered_df.columns:
                fig_sc_ad_conv = px.scatter(
                    filtered_df,
                    x="Ad Spend",
                    y="Conversions",
                    color="Service Type",
                    title="5. Ad Spend vs. Conversions by Service Type",
                    template="plotly_white"
                )
                st.plotly_chart(fig_sc_ad_conv, use_container_width=True)
            else: st.info("Service Type column is not available.")
            
        st.markdown("---")
        
        col6, col7 = st.columns(2)

        # 6. Ad Spend Distribution: Season & Service Type - Box Plot
        with col6:
            if "Season" in filtered_df.columns and "Service Type" in filtered_df.columns:
                fig_box_ad_spend = px.box(filtered_df, x="Season", y="Ad Spend", color="Service Type",
                                          title="6. Ad Spend Distribution: Season & Service Type",
                                          template="plotly_white")
                st.plotly_chart(fig_box_ad_spend, use_container_width=True)
            else: st.info("Season and Service Type columns are not available.")
            
        # 7. Treemap: Revenue by Channel & Customer Type
        with col7:
            if "Channel" in filtered_df.columns and "Customer Type" in filtered_df.columns:
                fig_treemap_rev = px.treemap(filtered_df, path=['Channel', 'Customer Type'], values='Revenue',
                                             title='7. Treemap: Revenue by Channel & Customer Type',
                                             template="plotly_white")
                st.plotly_chart(fig_treemap_rev, use_container_width=True)
            else: st.info("Channel and Customer Type columns are not available.")


else:
    st.info("📤 Please upload a dataset to begin.")
