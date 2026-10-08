import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="E-Commerce Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

@st.cache_data
def load_data():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Load dashboard ready data
    df_customers = pd.read_csv(os.path.join(project_root, 'data', 'dashboard_ready', 'dim_customers.csv'))
    df_products = pd.read_csv(os.path.join(project_root, 'data', 'dashboard_ready', 'dim_products.csv'))
    df_rfm = pd.read_csv(os.path.join(project_root, 'data', 'dashboard_ready', 'rfm_segments.csv'))
    df_features = pd.read_csv(os.path.join(project_root, 'data', 'dashboard_ready', 'customer_features.csv'))
    
    # Merge datasets for easier plotting
    df_merged = df_rfm.merge(df_features, on='CustomerID', how='inner')
    df_merged = df_merged.merge(df_customers, on='CustomerID', how='inner')
    
    return df_customers, df_products, df_rfm, df_features, df_merged

st.title("🛒 E-Commerce Executive Dashboard")

df_customers, df_products, df_rfm, df_features, df_merged = load_data()

# Calculate some high-level metrics
total_customers = df_customers['CustomerID'].nunique()
total_revenue = df_features['total_revenue'].sum()
avg_order_value = df_features['total_revenue'].sum() / df_features['total_orders'].sum()
total_orders = df_features['total_orders'].sum()
repeat_rate = (df_features['is_repeat_customer'] == 1).mean() * 100

# ----------------- SIDEBAR FILTERS -----------------
st.sidebar.header("Filters")
selected_segments = st.sidebar.multiselect("Select RFM Segments", options=df_merged['Segment'].unique(), default=df_merged['Segment'].unique())
selected_countries = st.sidebar.multiselect("Select Countries", options=df_merged['Country'].unique(), default=df_merged['Country'].value_counts().head(5).index.tolist())

# Apply Filters
filtered_df = df_merged[(df_merged['Segment'].isin(selected_segments)) & (df_merged['Country'].isin(selected_countries))]

st.markdown("### 📈 Executive Summary")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Revenue", f"£{filtered_df['total_revenue'].sum():,.0f}")
col2.metric("Total Orders", f"{filtered_df['total_orders'].sum():,.0f}")
col3.metric("Total Customers", f"{filtered_df['CustomerID'].nunique():,}")
col4.metric("Avg Order Value", f"£{filtered_df['total_revenue'].sum() / filtered_df['total_orders'].sum():,.2f}" if filtered_df['total_orders'].sum() > 0 else "£0")
col5.metric("Repeat Customer Rate", f"{(filtered_df['is_repeat_customer'] == 1).mean() * 100:.1f}%")

st.markdown("---")

# ----------------- TABS -----------------
tab1, tab2, tab3, tab4 = st.tabs(["Customer Segmentation (RFM)", "Geographic Analysis", "Buying Behaviors", "Product & Revenue Insights"])

with tab1:
    st.subheader("Customer Segmentation & Value")
    col_rfm1, col_rfm2 = st.columns(2)
    
    with col_rfm1:
        rfm_counts = filtered_df['Segment'].value_counts().reset_index()
        rfm_counts.columns = ['Segment', 'Count']
        fig_rfm = px.bar(rfm_counts, x='Count', y='Segment', orientation='h', 
                         title="Customers by RFM Segment", color='Segment', 
                         template="plotly_dark")
        st.plotly_chart(fig_rfm, use_container_width=True)
        
    with col_rfm2:
        rfm_revenue = filtered_df.groupby('Segment')['total_revenue'].sum().reset_index()
        fig_rev = px.pie(rfm_revenue, values='total_revenue', names='Segment', 
                         title="Revenue Contribution by Segment", template="plotly_dark", hole=0.4)
        st.plotly_chart(fig_rev, use_container_width=True)
        
    st.markdown("#### Recency vs Monetary Value")
    fig_scatter = px.scatter(filtered_df, x='Recency', y='total_revenue', 
                             color='Segment', size='total_orders', hover_name='CustomerID',
                             title="Recency vs Revenue (Bubble size = Total Orders)",
                             labels={'total_revenue': 'Total Revenue (£)', 'Recency': 'Recency (Days Since Last Order)'},
                             template="plotly_dark", log_y=True)
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.subheader("Geographic Performance")
    geo_revenue = filtered_df.groupby('Country').agg({'total_revenue': 'sum', 'CustomerID': 'nunique'}).reset_index()
    geo_revenue.rename(columns={'CustomerID': 'Total Customers'}, inplace=True)
    geo_revenue = geo_revenue.sort_values('total_revenue', ascending=False)
    
    col_geo1, col_geo2 = st.columns([2, 1])
    with col_geo1:
        fig_geo_bar = px.bar(geo_revenue.head(15), x='Country', y='total_revenue', 
                             title="Top 15 Countries by Revenue", text_auto='.2s',
                             color='total_revenue', color_continuous_scale="Viridis", template="plotly_dark")
        st.plotly_chart(fig_geo_bar, use_container_width=True)
    with col_geo2:
        fig_geo_scatter = px.scatter(geo_revenue, x='Total Customers', y='total_revenue', 
                                     hover_name='Country', title="Customers vs Revenue by Country", 
                                     template="plotly_dark")
        st.plotly_chart(fig_geo_scatter, use_container_width=True)

with tab3:
    st.subheader("Customer Buying Behaviors")
    col_beh1, col_beh2 = st.columns(2)
    
    with col_beh1:
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Sunday'] # Saturday usually missing in this dataset
        if 'preferred_day' in filtered_df.columns:
            day_counts = filtered_df['preferred_day'].value_counts().reset_index()
            day_counts.columns = ['Day', 'Customers']
            fig_day = px.bar(day_counts, x='Day', y='Customers', title="Preferred Shopping Day", 
                             template="plotly_dark", color='Customers', color_continuous_scale="Plasma")
            st.plotly_chart(fig_day, use_container_width=True)
            
    with col_beh2:
        if 'preferred_hour' in filtered_df.columns:
            fig_hour = px.histogram(filtered_df, x='preferred_hour', nbins=24, 
                                    title="Distribution of Preferred Shopping Hours",
                                    template="plotly_dark", color_discrete_sequence=['#FF7F0E'])
            fig_hour.update_layout(xaxis_title="Hour of Day (24H)", yaxis_title="Number of Customers")
            st.plotly_chart(fig_hour, use_container_width=True)
            
    fig_hist = px.histogram(filtered_df, x='avg_order_value', nbins=50, 
                            title="Distribution of Average Order Value",
                            template="plotly_dark", color_discrete_sequence=['#2CA02C'])
    fig_hist.update_xaxes(range=[0, filtered_df['avg_order_value'].quantile(0.95)]) # Clip outliers
    st.plotly_chart(fig_hist, use_container_width=True)

with tab4:
    st.subheader("Detailed Analytics & Distributions")
    col_dist1, col_dist2 = st.columns(2)
    
    with col_dist1:
        fig_items = px.box(filtered_df, x='Segment', y='avg_items_per_order', 
                           title="Avg Items Per Order by Segment", template="plotly_dark", color='Segment')
        fig_items.update_yaxes(range=[0, filtered_df['avg_items_per_order'].quantile(0.95)])
        st.plotly_chart(fig_items, use_container_width=True)
        
    with col_dist2:
        fig_tenure = px.histogram(filtered_df, x='customer_tenure_days', color='Segment', 
                                  title="Customer Tenure Distribution", template="plotly_dark")
        st.plotly_chart(fig_tenure, use_container_width=True)
