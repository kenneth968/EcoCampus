import pandas as pd
import numpy as np
from datetime import datetime
import os

class DataProcessor:
    def __init__(self):
        self.data_dir = "attached_assets"
    
    def load_temperature_data(self):
        """Load and process temperature data"""
        try:
            file_path = os.path.join(self.data_dir, "temperature_data_1755935412803.csv")
            df = pd.read_csv(file_path)
            
            # Clean and process the data
            df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
            
            # Parse time column to create proper date
            df['Month_Year'] = df['Time'].str.replace('.', '/20')  # Convert aug.20 to aug/2020
            
            # Standardize city names to match other datasets
            if 'City' in df.columns:
                df['City'] = df['City'].str.upper().str.strip()
            
            return df
        except Exception as e:
            raise Exception(f"Error loading temperature data: {str(e)}")
    
    def load_static_data(self):
        """Load and process static project data"""
        try:
            file_path = os.path.join(self.data_dir, "static_data_1755935412803.csv")
            df = pd.read_csv(file_path)
            
            # Filter only student housing projects
            df = df[df['project_type'] == 'studentboliger']
            
            # Clean numeric columns
            numeric_columns = ['year_built', 'lat', 'lon', 'total_HE', 'Total_BRA']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Standardize city column name to match electricity data
            if 'city' in df.columns:
                df = df.rename(columns={'city': 'City'})
            
            # Clean city names to match electricity data format
            if 'City' in df.columns:
                df['City'] = df['City'].str.upper().str.strip()
            
            # Add approximate coordinates for properties missing them
            city_coordinates = {
                'ÅLESUND': (62.4722, 6.1495),
                'GJØVIK': (60.7957, 10.6915),
                'TRONDHEIM': (63.4305, 10.3951)
            }
            
            for idx, row in df.iterrows():
                if pd.isna(row['lat']) or pd.isna(row['lon']):
                    city = row['City']
                    if city in city_coordinates:
                        # Add small random offset to avoid exact overlap
                        base_lat, base_lon = city_coordinates[city]
                        offset = (idx % 10) * 0.001  # Small offset based on row index
                        df.at[idx, 'lat'] = base_lat + offset
                        df.at[idx, 'lon'] = base_lon + offset
            
            # Remove rows that still don't have coordinates
            df_with_coords = df.dropna(subset=['lat', 'lon'])
            
            return df_with_coords
        except Exception as e:
            raise Exception(f"Error loading static data: {str(e)}")
    
    def load_electricity_data(self):
        """Load and process electricity consumption data"""
        try:
            file_path = os.path.join(self.data_dir, "Electricity_data_1755935412803.csv")
            # Use semicolon separator and handle encoding
            df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert numeric columns
            numeric_columns = [col for col in df.columns if 'KwH' in col or col == 'Year']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Clean city names
            df['City'] = df['City'].str.upper().str.strip()
            
            # Fix city name mappings to match static data
            city_mapping = {
                'JAKOBSLI': 'TRONDHEIM',  # Jakobsliveien 55 is actually in Trondheim
                'ÅLESUND': 'ÅLESUND',
                'GJØVIK': 'GJØVIK',
                'TRONDHEIM': 'TRONDHEIM'
            }
            df['City'] = df['City'].map(city_mapping).fillna(df['City'])
            
            # Rename columns for consistency
            if 'project_name' in df.columns:
                df = df.rename(columns={'project_name': 'project_name'})
            elif '﻿project_name' in df.columns:
                df = df.rename(columns={'﻿project_name': 'project_name'})
            
            return df
        except Exception as e:
            raise Exception(f"Error loading electricity data: {str(e)}")
    
    def load_all_data(self):
        """Load all data files and return as dictionary"""
        return {
            'temperature': self.load_temperature_data(),
            'static': self.load_static_data(),
            'electricity': self.load_electricity_data()
        }
    
    def calculate_monthly_totals(self, electricity_df):
        """Calculate monthly totals across all projects"""
        monthly_columns = [col for col in electricity_df.columns if 'KwH' in col and col != 'Year_total_KwH']
        
        monthly_data = []
        for col in monthly_columns:
            month_name = col.replace('_KwH', '').replace('__KwH', '')
            total = electricity_df[col].sum()
            monthly_data.append({
                'Month': month_name,
                'Total_KwH': total
            })
        
        return pd.DataFrame(monthly_data)
    
    def merge_consumption_with_static(self, electricity_df, static_df, selected_year=None):
        """Merge electricity consumption with static data for analysis"""
        # Filter by year if specified
        if selected_year and selected_year != 'Alle':
            electricity_filtered = electricity_df[electricity_df['Year'] == int(selected_year)]
        else:
            # If no year specified or "Alle", group by project and sum all years
            electricity_filtered = electricity_df
        
        # Group electricity data by project
        if selected_year and selected_year != 'Alle':
            # For specific year, just take the values (no summing needed)
            consumption_summary = electricity_filtered.groupby('project_name').agg({
                'Year_total_KwH': 'first',  # Use first since there should be only one row per project per year
                'City': 'first'
            }).reset_index()
        else:
            # For "Alle" years, sum across all years
            consumption_summary = electricity_filtered.groupby('project_name').agg({
                'Year_total_KwH': 'sum',
                'City': 'first'
            }).reset_index()
        
        # Merge with static data
        merged_df = pd.merge(
            static_df, 
            consumption_summary, 
            on='project_name', 
            how='left',
            suffixes=('', '_elec')
        )
        
        # Use the City column from static data and drop the duplicate
        if 'City_elec' in merged_df.columns:
            merged_df = merged_df.drop('City_elec', axis=1)
        
        # Calculate efficiency metrics
        merged_df['kwh_per_student'] = np.where(
            (merged_df['total_HE'] > 0) & (merged_df['Year_total_KwH'].notna()),
            merged_df['Year_total_KwH'] / merged_df['total_HE'],
            0
        )
        
        merged_df['kwh_per_m2'] = np.where(
            (merged_df['Total_BRA'] > 0) & (merged_df['Year_total_KwH'].notna()),
            merged_df['Year_total_KwH'] / merged_df['Total_BRA'],
            0
        )
        
        # Fill NaN values in consumption data with 0
        merged_df['Year_total_KwH'] = merged_df['Year_total_KwH'].fillna(0)
        
        return merged_df
