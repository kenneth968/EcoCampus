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

def get_merged_data(processor, electricity_data, static_data, selected_year):
    """Get merged data based on selected year"""
    return processor.merge_consumption_with_static(electricity_data, static_data, selected_year)

def main():
    st.title("🌿 Miljøfyrtårn Miljøledelsessystem")
    st.markdown("*Energiforbruk i Studentboliger*")
    
    # Load data
    try:
        data = load_data()
        temp_data = data['temperature']
        static_data = data['static']
        electricity_data = data['electricity']
        
        # Initialize utilities
        map_utils = MapUtils()
        chart_utils = ChartUtils()
        processor = DataProcessor()
        
        # Sidebar filters
        st.sidebar.header("🔍 Filter")
        
        # Show all data toggle
        show_all_data = st.sidebar.checkbox("📊 Vis all data samtidig", help="Vis all data for å identifisere unormalt høyt forbruk")
        
        # Year filter (put first so it affects merged data)
        if not show_all_data:
            # Filter out 2020 as it's incomplete
            years = sorted([str(year) for year in electricity_data['Year'].unique() if year != 2020])
            selected_year = st.sidebar.radio("Velg år", years, horizontal=True)
        else:
            selected_year = 'Alle'
        
        # Get merged data based on selected year
        merged_data = get_merged_data(processor, electricity_data, static_data, selected_year)
        
        # City filter
        if not show_all_data:
            cities = sorted(merged_data['City'].dropna().unique().tolist())
            selected_city = st.sidebar.radio("Velg by", cities)
        else:
            selected_city = 'Alle'
        
        # Filter merged data by city first
        if selected_city != 'Alle':
            city_filtered_data = merged_data[merged_data['City'] == selected_city]
        else:
            city_filtered_data = merged_data
        
        # Project filter - only show projects from selected city
        if not show_all_data:
            projects = ['Alle'] + sorted(city_filtered_data['project_name'].unique().tolist())
            # Use session state to maintain selection
            if 'selected_project' not in st.session_state:
                st.session_state.selected_project = 'Alle'
            selected_project = st.sidebar.selectbox(
                "Velg prosjekt", 
                projects, 
                index=projects.index(st.session_state.selected_project) if st.session_state.selected_project in projects else 0,
                key="project_selector"
            )
            st.session_state.selected_project = selected_project
        else:
            selected_project = 'Alle'
        
        # Map color metric toggle
        st.sidebar.markdown("---")
        st.sidebar.subheader("🗺️ Kartfarge")
        color_metric = st.sidebar.radio(
            "Vis kart basert på:",
            ['kwh_per_m2', 'kwh_per_student'],
            format_func=lambda x: 'kWh per m²' if x == 'kwh_per_m2' else 'kWh per student'
        )
        
        # Calculate global min/max for color scaling (from all data)
        global_values = merged_data[merged_data[color_metric] > 0][color_metric]
        if not global_values.empty:
            global_min = global_values.min()
            global_max = global_values.max()
        else:
            global_min = global_max = 0
        
        # Filter data based on selections
        filtered_merged = city_filtered_data.copy()  # Use already city-filtered data
        filtered_electricity = electricity_data.copy()
        filtered_temp = temp_data.copy()
        
        if selected_city != 'Alle':
            filtered_electricity = filtered_electricity[filtered_electricity['City'] == selected_city]
            filtered_temp = filtered_temp[filtered_temp['City'] == selected_city]
        
        if selected_year != 'Alle':
            filtered_electricity = filtered_electricity[filtered_electricity['Year'] == int(selected_year)]
            filtered_temp = filtered_temp[filtered_temp['Year'] == int(selected_year)]
        
        if selected_project != 'Alle':
            filtered_merged = filtered_merged[filtered_merged['project_name'] == selected_project]
            # Also filter electricity and temperature data by project location if specific project is selected
            if not filtered_merged.empty:
                project_city = filtered_merged['City'].iloc[0]
                project_year = filtered_merged['Year'].iloc[0] if 'Year' in filtered_merged.columns else None
                
                # Filter temperature data by city and year if available
                filtered_temp = temp_data[temp_data['City'] == project_city]
                if project_year and selected_year != 'Alle':
                    filtered_temp = filtered_temp[filtered_temp['Year'] == int(selected_year)]
                
                # Filter electricity data by project name
                filtered_electricity = electricity_data[electricity_data['project_name'] == selected_project]
                if selected_year != 'Alle':
                    filtered_electricity = filtered_electricity[filtered_electricity['Year'] == int(selected_year)]
        
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
                # Create map with selected color metric using global min/max
                folium_map, _, _ = map_utils.create_energy_map(filtered_merged, color_metric, (global_min, global_max))
                st_folium(folium_map, width=700, height=500)
                
                # Dynamic map legend based on global data range
                metric_name = 'kWh per m²' if color_metric == 'kwh_per_m2' else 'kWh per student'
                st.markdown(f"""
                **Kartforklaring ({metric_name}) - basert på alle prosjekter:**
                - 🟢 Lavt forbruk: {global_min:.1f} {metric_name}
                - 🟡 Middels forbruk: {(global_min + global_max) / 2:.1f} {metric_name}
                - 🔴 Høyt forbruk: {global_max:.1f} {metric_name}
                
                Farger viser posisjon i forhold til alle prosjekter i datasettet.
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
                    top_consumers_chart = chart_utils.create_top_consumers_chart(filtered_merged)
                    st.plotly_chart(top_consumers_chart, use_container_width=True)
                
                with col2:
                    # Use merged data for efficiency chart
                    if not filtered_merged.empty:
                        efficiency_chart = chart_utils.create_efficiency_chart_from_merged(filtered_merged)
                        st.plotly_chart(efficiency_chart, use_container_width=True)
            else:
                st.warning("Ingen strømforbruksdata tilgjengelig for de valgte filtrene.")
        
        with tab3:
            st.subheader("Temperatur og Graddager Analyse")
            
            if not filtered_temp.empty and not filtered_electricity.empty:
                # Enhanced temperature vs consumption correlation with degree days
                correlation_chart = chart_utils.create_temperature_correlation_chart(
                    filtered_temp, filtered_electricity
                )
                st.plotly_chart(correlation_chart, use_container_width=True)
                
                # Explanation of degree days
                st.info("""
                **Graddager (HDD_17):** Mål på oppvarmingsbehov basert på temperatur under 17°C. 
                Høyere graddager = kaldere vær = mer oppvarmingsbehov = høyere strømforbruk.
                """)
                
                # Show correlation statistics if available
                correlation_data = chart_utils.merge_temp_consumption_data(filtered_temp, filtered_electricity)
                if not correlation_data.empty and len(correlation_data) > 1:
                    import scipy.stats as stats
                    
                    # Calculate correlations
                    temp_corr = stats.pearsonr(correlation_data['Temperature'], correlation_data['Monthly_Consumption'])
                    hdd_corr = stats.pearsonr(correlation_data['Monthly_HDD'], correlation_data['Monthly_Consumption'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Korrelasjon: Temperatur vs Forbruk", 
                            f"{temp_corr[0]:.3f}",
                            help="Negativ verdi = lavere temperatur gir høyere forbruk"
                        )
                    with col2:
                        st.metric(
                            "Korrelasjon: Graddager vs Forbruk", 
                            f"{hdd_corr[0]:.3f}",
                            help="Positiv verdi = flere graddager gir høyere forbruk"
                        )
            else:
                st.warning("Utilstrekkelige data for temperaturanalyse.")
        
        with tab4:
            st.subheader("Sammenligning")
            
            # Multi-project selection for comparison
            st.write("**Velg prosjekter å sammenligne:**")
            available_projects = city_filtered_data['project_name'].unique().tolist()
            
            if 'comparison_projects' not in st.session_state:
                st.session_state.comparison_projects = []
            
            comparison_projects = st.multiselect(
                "Prosjekter for sammenligning:",
                available_projects,
                default=st.session_state.comparison_projects,
                key="comparison_selector",
                placeholder="Velg prosjekter..."
            )
            st.session_state.comparison_projects = comparison_projects
            
            if comparison_projects:
                # Filter data for selected projects
                comparison_data = city_filtered_data[
                    city_filtered_data['project_name'].isin(comparison_projects)
                ]
                
                if not comparison_data.empty:
                    # Comparison table
                    st.write(f"**Sammenligning av {len(comparison_projects)} prosjekt(er):**")
                    comparison_table = comparison_data[[
                        'project_name', 'City', 'Year_total_KwH', 
                        'kwh_per_student', 'kwh_per_m2'
                    ]].round(1).copy()
                    
                    # Rename columns to Norwegian
                    comparison_table.columns = ['Studentby', 'By', 'Årlig kWh', 'kWh per student', 'kWh per m²']
                    
                    st.dataframe(comparison_table, use_container_width=True, hide_index=True)
                    
                    # Comparison charts side by side
                    col1, col2 = st.columns(2)
                    with col1:
                        comparison_chart_student = chart_utils.create_project_comparison_chart_student(comparison_data)
                        st.plotly_chart(comparison_chart_student, use_container_width=True)
                    with col2:
                        comparison_chart_m2 = chart_utils.create_project_comparison_chart_m2(comparison_data)
                        st.plotly_chart(comparison_chart_m2, use_container_width=True)
                else:
                    st.warning("Ingen data tilgjengelig for de valgte prosjektene.")
            else:
                # Default view - show high vs low consumption
                if not filtered_merged.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Høyt forbruk (Topp 25%)**")
                        high_consumption = filtered_merged.nlargest(max(1, len(filtered_merged)//4), 'Year_total_KwH')
                        st.dataframe(high_consumption[['project_name', 'City', 'Year_total_KwH', 'kwh_per_student', 'kwh_per_m2']])
                    
                    with col2:
                        st.write("**Lavt forbruk (Bunn 25%)**")
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
