import folium
import pandas as pd
import numpy as np

class MapUtils:
    def __init__(self):
        self.default_center = [63.4305, 10.3951]  # Trondheim coordinates
        self.zoom_start = 10
    
    def get_consumption_color(self, consumption):
        """Get color based on consumption level"""
        if pd.isna(consumption) or consumption == 0:
            return 'black'
        elif consumption > 1000000:  # > 1M kWh
            return 'red'
        elif consumption > 100000:  # 100k - 1M kWh
            return 'orange'
        else:  # < 100k kWh
            return 'green'
    
    def get_consumption_size(self, consumption):
        """Get marker size based on consumption level"""
        if pd.isna(consumption) or consumption == 0:
            return 5
        elif consumption > 1000000:
            return 15
        elif consumption > 100000:
            return 10
        else:
            return 7
    
    def create_energy_map(self, static_df, electricity_df):
        """Create an interactive map showing energy consumption"""
        # Calculate center based on available coordinates
        if not static_df.empty and static_df['lat'].notna().any():
            center_lat = static_df['lat'].mean()
            center_lon = static_df['lon'].mean()
        else:
            center_lat, center_lon = self.default_center
        
        # Create the map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=self.zoom_start,
            tiles='OpenStreetMap'
        )
        
        # Aggregate electricity data by project
        consumption_by_project = electricity_df.groupby('project_name')['Year_total_KwH'].sum().to_dict()
        
        # Add markers for each project
        for idx, row in static_df.iterrows():
            if pd.notna(row['lat']) and pd.notna(row['lon']):
                project_name = row['project_name']
                consumption = consumption_by_project.get(project_name, 0)
                
                # Create popup content
                popup_content = f"""
                <b>{project_name}</b><br>
                City: {row['City']}<br>
                Type: {row['project_type']}<br>
                Students: {row['total_HE'] if pd.notna(row['total_HE']) else 'N/A'}<br>
                Area: {row['Total_BRA'] if pd.notna(row['Total_BRA']) else 'N/A'} m²<br>
                Annual Consumption: {consumption:,.0f} kWh<br>
                Built: {row['year_built'] if pd.notna(row['year_built']) else 'N/A'}
                """
                
                # Add marker
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=self.get_consumption_size(consumption),
                    popup=folium.Popup(popup_content, max_width=300),
                    color=self.get_consumption_color(consumption),
                    fill=True,
                    fillColor=self.get_consumption_color(consumption),
                    fillOpacity=0.7,
                    weight=2
                ).add_to(m)
        
        return m
    
    def create_city_overview_map(self, static_df, electricity_df):
        """Create a map showing city-level consumption overview"""
        # Group data by city
        city_consumption = electricity_df.groupby('City').agg({
            'Year_total_KwH': 'sum',
            'project_name': 'count'
        }).reset_index()
        city_consumption.columns = ['City', 'Total_Consumption', 'Project_Count']
        
        # Get average coordinates for each city
        city_coords = static_df.groupby('City').agg({
            'lat': 'mean',
            'lon': 'mean'
        }).reset_index()
        
        # Merge consumption data with coordinates
        city_data = pd.merge(city_coords, city_consumption, on='City', how='inner')
        
        # Create map centered on Norway
        m = folium.Map(
            location=[63.0, 10.0],
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Add markers for each city
        for idx, row in city_data.iterrows():
            if pd.notna(row['lat']) and pd.notna(row['lon']):
                popup_content = f"""
                <b>{row['City']}</b><br>
                Projects: {row['Project_Count']}<br>
                Total Consumption: {row['Total_Consumption']:,.0f} kWh
                """
                
                # Size based on consumption
                marker_size = min(30, max(10, row['Total_Consumption'] / 100000))
                
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=marker_size,
                    popup=folium.Popup(popup_content, max_width=200),
                    color='blue',
                    fill=True,
                    fillColor='lightblue',
                    fillOpacity=0.6,
                    weight=2
                ).add_to(m)
        
        return m
