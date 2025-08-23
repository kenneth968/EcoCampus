import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_processor import DataProcessor
from map_utils import MapUtils
from chart_utils import ChartUtils
import folium
from streamlit_folium import st_folium

# Set page configuration
st.set_page_config(
    page_title="Miljøfyrtårn EMS Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize data processor
@st.cache_data
def load_data():
    """Load and process all data files"""
    processor = DataProcessor()
    return processor.load_all_data()

def main():
    st.title("🌿 Miljøfyrtårn Environmental Management Dashboard")
    st.markdown("*Student Housing Energy Consumption Analytics*")
    
    # Load data
    try:
        data = load_data()
        temp_data = data['temperature']
        static_data = data['static']
        electricity_data = data['electricity']
        
        # Initialize utilities
        map_utils = MapUtils()
        chart_utils = ChartUtils()
        
        # Sidebar filters
        st.sidebar.header("🔍 Filters")
        
        # City filter
        cities = ['All'] + sorted(static_data['City'].dropna().unique().tolist())
        selected_city = st.sidebar.selectbox("Select City", cities)
        
        # Year filter
        years = ['All'] + sorted([str(year) for year in electricity_data['Year'].unique()])
        selected_year = st.sidebar.selectbox("Select Year", years)
        
        # Project type filter
        project_types = ['All'] + sorted(static_data['project_type'].unique().tolist())
        selected_project_type = st.sidebar.selectbox("Select Project Type", project_types)
        
        # Filter data based on selections
        filtered_static = static_data.copy()
        filtered_electricity = electricity_data.copy()
        filtered_temp = temp_data.copy()
        
        if selected_city != 'All':
            filtered_static = filtered_static[filtered_static['City'] == selected_city]
            filtered_electricity = filtered_electricity[filtered_electricity['City'] == selected_city]
            filtered_temp = filtered_temp[filtered_temp['City'] == selected_city]
        
        if selected_year != 'All':
            filtered_electricity = filtered_electricity[filtered_electricity['Year'] == int(selected_year)]
        
        if selected_project_type != 'All':
            filtered_static = filtered_static[filtered_static['project_type'] == selected_project_type]
        
        # Main dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate KPIs
        total_projects = len(filtered_static)
        total_consumption = filtered_electricity['Year_total_KwH'].sum() if not filtered_electricity.empty else 0
        avg_consumption_per_student = (
            filtered_electricity['Year_total_KwH'].sum() / filtered_static['total_HE'].sum() 
            if not filtered_static.empty and filtered_static['total_HE'].sum() > 0 else 0
        )
        avg_consumption_per_m2 = (
            filtered_electricity['Year_total_KwH'].sum() / filtered_static['Total_BRA'].sum() 
            if not filtered_static.empty and filtered_static['Total_BRA'].sum() > 0 else 0
        )
        
        with col1:
            st.metric("Total Projects", f"{total_projects:,}")
        
        with col2:
            st.metric("Total Consumption", f"{total_consumption:,.0f} kWh")
        
        with col3:
            st.metric("kWh per Student", f"{avg_consumption_per_student:.1f}")
        
        with col4:
            st.metric("kWh per m²", f"{avg_consumption_per_m2:.1f}")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Interactive Map", "📊 Energy Analytics", "🌡️ Temperature Analysis", "📈 Comparative Analysis"])
        
        with tab1:
            st.subheader("Student Housing Projects Map")
            
            if not filtered_static.empty:
                # Create map
                folium_map = map_utils.create_energy_map(filtered_static, filtered_electricity)
                st_folium(folium_map, width=700, height=500)
                
                # Map legend
                st.markdown("""
                **Map Legend:**
                - 🔴 High consumption (>1M kWh/year)
                - 🟡 Medium consumption (100k-1M kWh/year)
                - 🟢 Low consumption (<100k kWh/year)
                - ⚫ No consumption data available
                """)
            else:
                st.warning("No data available for the selected filters.")
        
        with tab2:
            st.subheader("Energy Consumption Analytics")
            
            if not filtered_electricity.empty:
                # Monthly consumption trends
                monthly_chart = chart_utils.create_monthly_consumption_chart(filtered_electricity)
                st.plotly_chart(monthly_chart, use_container_width=True)
                
                # Top consumers
                col1, col2 = st.columns(2)
                
                with col1:
                    top_consumers_chart = chart_utils.create_top_consumers_chart(filtered_electricity)
                    st.plotly_chart(top_consumers_chart, use_container_width=True)
                
                with col2:
                    # Efficiency metrics
                    if not filtered_static.empty:
                        efficiency_chart = chart_utils.create_efficiency_chart(filtered_electricity, filtered_static)
                        st.plotly_chart(efficiency_chart, use_container_width=True)
            else:
                st.warning("No electricity consumption data available for the selected filters.")
        
        with tab3:
            st.subheader("Temperature Correlation Analysis")
            
            if not filtered_temp.empty and not filtered_electricity.empty:
                # Temperature vs consumption correlation
                correlation_chart = chart_utils.create_temperature_correlation_chart(
                    filtered_temp, filtered_electricity
                )
                st.plotly_chart(correlation_chart, use_container_width=True)
                
                # HDD analysis would go here if HDD data was available
                st.info("Note: Heating Degree Days (HDD_17) analysis would be displayed here with additional temperature processing.")
            else:
                st.warning("Insufficient data for temperature correlation analysis.")
        
        with tab4:
            st.subheader("Comparative Analysis")
            
            if not filtered_electricity.empty and not filtered_static.empty:
                # Comparative metrics
                comparison_data = chart_utils.prepare_comparison_data(filtered_electricity, filtered_static)
                
                if not comparison_data.empty:
                    # High vs Low consumption comparison
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**High Consumption Properties (Top 25%)**")
                        high_consumption = comparison_data.nlargest(max(1, len(comparison_data)//4), 'total_consumption')
                        st.dataframe(high_consumption[['project_name', 'city', 'total_consumption', 'kwh_per_student', 'kwh_per_m2']])
                    
                    with col2:
                        st.write("**Low Consumption Properties (Bottom 25%)**")
                        low_consumption = comparison_data.nsmallest(max(1, len(comparison_data)//4), 'total_consumption')
                        st.dataframe(low_consumption[['project_name', 'city', 'total_consumption', 'kwh_per_student', 'kwh_per_m2']])
                    
                    # Efficiency scatter plot
                    efficiency_scatter = chart_utils.create_efficiency_scatter(comparison_data)
                    st.plotly_chart(efficiency_scatter, use_container_width=True)
                else:
                    st.warning("Insufficient data for comparative analysis.")
            else:
                st.warning("Insufficient data for comparative analysis.")
        
        # Export functionality
        st.sidebar.markdown("---")
        st.sidebar.subheader("📥 Export Data")
        
        if st.sidebar.button("Download Analysis Results"):
            # Prepare export data
            export_data = chart_utils.prepare_export_data(filtered_electricity, filtered_static, filtered_temp)
            csv = export_data.to_csv(index=False)
            st.sidebar.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"miljofyrtarn_analysis_{selected_city}_{selected_year}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please ensure all required data files are available in the attached_assets directory.")

if __name__ == "__main__":
    main()
