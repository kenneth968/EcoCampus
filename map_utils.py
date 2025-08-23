import folium
import pandas as pd
import numpy as np

class MapUtils:
    def __init__(self):
        self.default_center = [63.4305, 10.3951]  # Trondheim coordinates
        self.zoom_start = 10
    
    def get_efficiency_color_gradient(self, efficiency_value, min_val, max_val):
        """Get color based on efficiency metric using continuous gradient from green to red"""
        if pd.isna(efficiency_value) or efficiency_value == 0:
            return 'black'
        
        if min_val >= max_val:
            return 'green'  # Default if no variation
        
        # Normalize value to 0-1 scale
        normalized = (efficiency_value - min_val) / (max_val - min_val)
        normalized = max(0, min(1, normalized))  # Clamp to 0-1
        
        # Create gradient from green (low) to red (high)
        # Green to Yellow to Orange to Red
        if normalized <= 0.33:
            # Green to Yellow
            factor = normalized / 0.33
            r = int(factor * 255)
            g = 255
            b = 0
        elif normalized <= 0.66:
            # Yellow to Orange
            factor = (normalized - 0.33) / 0.33
            r = 255
            g = int(255 * (1 - factor * 0.5))  # Fade from 255 to 128
            b = 0
        else:
            # Orange to Red
            factor = (normalized - 0.66) / 0.34
            r = 255
            g = int(128 * (1 - factor))  # Fade from 128 to 0
            b = 0
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
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
    
    def create_energy_map(self, merged_df, color_metric='kwh_per_m2'):
        """Create an interactive map showing energy efficiency"""
        # Calculate center based on available coordinates
        if not merged_df.empty and merged_df['lat'].notna().any():
            center_lat = merged_df['lat'].mean()
            center_lon = merged_df['lon'].mean()
        else:
            center_lat, center_lon = self.default_center
        
        # Create the map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=self.zoom_start,
            tiles='OpenStreetMap'
        )
        
        # Calculate min and max values for the selected metric
        valid_values = merged_df[merged_df[color_metric] > 0][color_metric]
        if not valid_values.empty:
            min_val = valid_values.min()
            max_val = valid_values.max()
        else:
            min_val = max_val = 0
        
        # Add markers for each project
        for idx, row in merged_df.iterrows():
            if pd.notna(row['lat']) and pd.notna(row['lon']):
                project_name = row['project_name']
                consumption = row['Year_total_KwH'] if pd.notna(row['Year_total_KwH']) else 0
                students = row['total_HE'] if pd.notna(row['total_HE']) else 0
                kwh_per_student = row['kwh_per_student'] if pd.notna(row['kwh_per_student']) else 0
                kwh_per_m2 = row['kwh_per_m2'] if pd.notna(row['kwh_per_m2']) else 0
                
                # Create popup content in Norwegian
                popup_content = f"""
                <b>{project_name}</b><br>
                By: {row['City']}<br>
                Studenter: {students:.0f}<br>
                Årlig forbruk: {consumption:,.1f} kWh<br>
                kWh per student: {kwh_per_student:.1f}<br>
                kWh per m²: {kwh_per_m2:.1f}<br>
                Byggeår: {row['year_built'] if pd.notna(row['year_built']) else 'N/A'}
                """
                
                # Get color based on selected metric using gradient
                efficiency_value = row[color_metric] if pd.notna(row[color_metric]) else 0
                color = self.get_efficiency_color_gradient(efficiency_value, min_val, max_val)
                
                # Add marker
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=self.get_consumption_size(consumption),
                    popup=folium.Popup(popup_content, max_width=300),
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7,
                    weight=2
                ).add_to(m)
        
        return m, min_val, max_val
    
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
