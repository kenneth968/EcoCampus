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
    data = processor.load_all_data()
    # Merge consumption with static data for easier handling
    merged_data = processor.merge_consumption_with_static(data['electricity'], data['static'])
    return {
        'temperature': data['temperature'],
        'static': data['static'], 
        'electricity': data['electricity'],
        'merged': merged_data
    }

def main():
    st.title("🌿 Miljøfyrtårn Miljøledelsessystem")
    st.markdown("*Energiforbruk i Studentboliger*")
    
    # Load data
    try:
        data = load_data()
        temp_data = data['temperature']
        static_data = data['static']
        electricity_data = data['electricity']
        merged_data = data['merged']
        
        # Initialize utilities
        map_utils = MapUtils()
        chart_utils = ChartUtils()
        
        # Sidebar filters
        st.sidebar.header("🔍 Filter")
        
        # City filter
        cities = ['Alle'] + sorted(merged_data['City'].dropna().unique().tolist())
        selected_city = st.sidebar.selectbox("Velg by", cities)
        
        # Year filter
        years = ['Alle'] + sorted([str(year) for year in electricity_data['Year'].unique()])
        selected_year = st.sidebar.selectbox("Velg år", years)
        
        # Project filter (instead of project type)
        projects = ['Alle'] + sorted(merged_data['project_name'].unique().tolist())
        selected_project = st.sidebar.selectbox("Velg prosjekt", projects)
        
        # Map color metric toggle
        st.sidebar.markdown("---")
        st.sidebar.subheader("🗺️ Kartfarge")
        color_metric = st.sidebar.radio(
            "Vis kart basert på:",
            ['kwh_per_m2', 'kwh_per_student'],
            format_func=lambda x: 'kWh per m²' if x == 'kwh_per_m2' else 'kWh per student'
        )
        
        # Filter data based on selections
        filtered_merged = merged_data.copy()
        filtered_electricity = electricity_data.copy()
        filtered_temp = temp_data.copy()
        
        if selected_city != 'Alle':
            filtered_merged = filtered_merged[filtered_merged['City'] == selected_city]
            filtered_electricity = filtered_electricity[filtered_electricity['City'] == selected_city]
            filtered_temp = filtered_temp[filtered_temp['City'] == selected_city]
        
        if selected_year != 'Alle':
            filtered_electricity = filtered_electricity[filtered_electricity['Year'] == int(selected_year)]
        
        if selected_project != 'Alle':
            filtered_merged = filtered_merged[filtered_merged['project_name'] == selected_project]
        
        # Main dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate KPIs
        total_projects = len(filtered_merged)
        total_consumption = filtered_merged['Year_total_KwH'].sum() if not filtered_merged.empty else 0
        total_students = filtered_merged['total_HE'].sum() if not filtered_merged.empty else 0
        total_area = filtered_merged['Total_BRA'].sum() if not filtered_merged.empty else 0
        
        avg_consumption_per_student = total_consumption / total_students if total_students > 0 else 0
        avg_consumption_per_m2 = total_consumption / total_area if total_area > 0 else 0
        
        with col1:
            st.metric("Totalt antall prosjekter", f"{total_projects:,}")
        
        with col2:
            st.metric("Totalt forbruk", f"{total_consumption:,.0f} kWh")
        
        with col3:
            st.metric("kWh per student", f"{avg_consumption_per_student:.1f}")
        
        with col4:
            st.metric("kWh per m²", f"{avg_consumption_per_m2:.1f}")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Interaktivt kart", "📊 Energianalyse", "🌡️ Temperaturanalyse", "📈 Sammenligning"])
        
        with tab1:
            st.subheader("Studentboliger - Interaktivt kart")
            
            if not filtered_merged.empty:
                # Create map with selected color metric
                folium_map = map_utils.create_energy_map(filtered_merged, color_metric)
                st_folium(folium_map, width=700, height=500)
                
                # Map legend based on selected metric
                if color_metric == 'kwh_per_m2':
                    st.markdown("""
                    **Kartforklaring (kWh per m²):**
                    - 🔴 Høyt forbruk (>50 kWh/m²)
                    - 🟡 Middels forbruk (30-50 kWh/m²)
                    - 🟢 Lavt forbruk (<30 kWh/m²)
                    - ⚫ Ingen forbruksdata tilgjengelig
                    """)
                else:
                    st.markdown("""
                    **Kartforklaring (kWh per student):**
                    - 🔴 Høyt forbruk (>4000 kWh/student)
                    - 🟡 Middels forbruk (2000-4000 kWh/student)
                    - 🟢 Lavt forbruk (<2000 kWh/student)
                    - ⚫ Ingen forbruksdata tilgjengelig
                    """)
            else:
                st.warning("Ingen data tilgjengelig for de valgte filtrene.")
        
        with tab2:
            st.subheader("Energiforbruksanalyse")
            
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
                    # Use merged data for efficiency chart
                    if not filtered_merged.empty:
                        efficiency_chart = chart_utils.create_efficiency_chart_from_merged(filtered_merged)
                        st.plotly_chart(efficiency_chart, use_container_width=True)
            else:
                st.warning("Ingen strømforbruksdata tilgjengelig for de valgte filtrene.")
        
        with tab3:
            st.subheader("Temperaturanalyse")
            
            if not filtered_temp.empty and not filtered_electricity.empty:
                # Temperature vs consumption correlation
                correlation_chart = chart_utils.create_temperature_correlation_chart(
                    filtered_temp, filtered_electricity
                )
                st.plotly_chart(correlation_chart, use_container_width=True)
                
                # HDD analysis would go here if HDD data was available
                st.info("Merk: Graddager (HDD_17) analyse ville blitt vist her med ytterligere temperaturbehandling.")
            else:
                st.warning("Utilstrekkelige data for temperaturkorrelasjon analyse.")
        
        with tab4:
            st.subheader("Sammenligning")
            
            if not filtered_merged.empty:
                # High vs Low consumption comparison
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Høyt forbruk (Topp 25%)**")
                    high_consumption = filtered_merged.nlargest(max(1, len(filtered_merged)//4), 'Year_total_KwH')
                    st.dataframe(high_consumption[['project_name', 'City', 'Year_total_KwH', 'kwh_per_student', 'kwh_per_m2']])
                
                with col2:
                    st.write("**Lavt forbruk (Bunn 25%)**")
                    # Filter out projects with 0 consumption for bottom comparison
                    filtered_for_low = filtered_merged[filtered_merged['Year_total_KwH'] > 0]
                    if not filtered_for_low.empty:
                        low_consumption = filtered_for_low.nsmallest(max(1, len(filtered_for_low)//4), 'Year_total_KwH')
                        st.dataframe(low_consumption[['project_name', 'City', 'Year_total_KwH', 'kwh_per_student', 'kwh_per_m2']])
                    else:
                        st.write("Ingen data med forbruk > 0")
                
                # Efficiency scatter plot
                efficiency_scatter = chart_utils.create_efficiency_scatter(filtered_merged)
                st.plotly_chart(efficiency_scatter, use_container_width=True)
            else:
                st.warning("Utilstrekkelige data for sammenligning.")
        
        # Export functionality
        st.sidebar.markdown("---")
        st.sidebar.subheader("📥 Eksporter data")
        
        if st.sidebar.button("Last ned analyseresultater"):
            # Prepare export data using merged data
            csv = filtered_merged.to_csv(index=False)
            st.sidebar.download_button(
                label="Last ned CSV",
                data=csv,
                file_name=f"miljofyrtarn_analyse_{selected_city}_{selected_year}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please ensure all required data files are available in the attached_assets directory.")

if __name__ == "__main__":
    main()
