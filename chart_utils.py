import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class ChartUtils:
    def __init__(self):
        self.color_palette = {
            'primary': '#2E7D32',
            'secondary': '#1976D2',
            'accent': '#FFA726',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336'
        }
    
    def create_monthly_consumption_chart(self, electricity_df):
        """Create monthly consumption trends chart"""
        # Get monthly columns
        monthly_columns = [col for col in electricity_df.columns if 'KwH' in col and col != 'Year_total_KwH']
        
        # Calculate monthly totals by year
        yearly_monthly_data = []
        
        for year in electricity_df['Year'].unique():
            year_data = electricity_df[electricity_df['Year'] == year]
            for col in monthly_columns:
                month_name = col.replace('_KwH', '').replace('__KwH', '').replace('_', ' ').title()
                total = year_data[col].sum()
                yearly_monthly_data.append({
                    'Year': year,
                    'Month': month_name,
                    'Total_KwH': total
                })
        
        monthly_df = pd.DataFrame(yearly_monthly_data)
        
        if not monthly_df.empty:
            fig = px.line(
                monthly_df, 
                x='Month', 
                y='Total_KwH', 
                color='Year',
                title='Monthly Energy Consumption Trends',
                labels={'Total_KwH': 'Total Consumption (kWh)', 'Month': 'Month'}
            )
            
            fig.update_layout(
                xaxis_title='Month',
                yaxis_title='Total Consumption (kWh)',
                hovermode='x unified'
            )
            
            return fig
        else:
            # Return empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(title='Monthly Energy Consumption Trends')
            return fig
    
    def create_top_consumers_chart(self, electricity_df):
        """Create top consumers bar chart"""
        # Group by project and sum annual consumption
        project_consumption = electricity_df.groupby('project_name')['Year_total_KwH'].sum().reset_index()
        project_consumption = project_consumption.sort_values('Year_total_KwH', ascending=False).head(10)
        
        fig = px.bar(
            project_consumption,
            x='Year_total_KwH',
            y='project_name',
            orientation='h',
            title='Top 10 Energy Consumers',
            labels={'Year_total_KwH': 'Annual Consumption (kWh)', 'project_name': 'Project'},
            color='Year_total_KwH',
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False
        )
        
        return fig
    
    def create_efficiency_chart(self, electricity_df, static_df):
        """Create efficiency metrics chart"""
        # Merge data
        from data_processor import DataProcessor
        processor = DataProcessor()
        merged_df = processor.merge_consumption_with_static(electricity_df, static_df)
        
        # Filter out projects with no consumption or capacity data
        efficiency_df = merged_df[
            (merged_df['Year_total_KwH'] > 0) & 
            (merged_df['total_HE'] > 0) & 
            (merged_df['kwh_per_student'] > 0)
        ].copy()
        
        if not efficiency_df.empty:
            fig = px.scatter(
                efficiency_df,
                x='total_HE',
                y='kwh_per_student',
                size='Year_total_KwH',
                color='City',
                hover_data=['project_name', 'Year_total_KwH'],
                title='Energy Efficiency: kWh per Student vs Number of Students',
                labels={
                    'total_HE': 'Number of Students (HE)',
                    'kwh_per_student': 'kWh per Student',
                    'Year_total_KwH': 'Total Consumption'
                }
            )
            
            fig.update_layout(
                xaxis_title='Number of Students (HE)',
                yaxis_title='kWh per Student'
            )
            
            return fig
        else:
            fig = go.Figure()
            fig.add_annotation(
                text="No efficiency data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(title='Energy Efficiency Analysis')
            return fig
    
    def create_temperature_correlation_chart(self, temp_df, electricity_df):
        """Create temperature vs consumption correlation chart"""
        # This is a simplified correlation - in practice, you'd need to align dates properly
        try:
            # Get monthly averages
            monthly_temp = temp_df.groupby(['City', 'Time'])['Temperature'].mean().reset_index()
            
            # Get electricity data by month (this would need proper date alignment)
            monthly_columns = [col for col in electricity_df.columns if 'KwH' in col and col != 'Year_total_KwH']
            
            # Create a simplified correlation chart
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add temperature line
            cities = temp_df['City'].unique()
            for city in cities:
                city_temp = monthly_temp[monthly_temp['City'] == city]
                if not city_temp.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=city_temp['Time'],
                            y=city_temp['Temperature'],
                            name=f"{city} Temperature",
                            line=dict(color=self.color_palette['secondary'])
                        ),
                        secondary_y=False
                    )
            
            fig.update_xaxes(title_text="Time Period")
            fig.update_yaxes(title_text="Temperature (°C)", secondary_y=False)
            fig.update_layout(title="Temperature Trends by City")
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating correlation chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=14
            )
            fig.update_layout(title='Temperature vs Consumption Correlation')
            return fig
    
    def prepare_comparison_data(self, electricity_df, static_df):
        """Prepare data for comparative analysis"""
        from data_processor import DataProcessor
        processor = DataProcessor()
        merged_df = processor.merge_consumption_with_static(electricity_df, static_df)
        
        # Calculate additional metrics
        comparison_df = merged_df[merged_df['Year_total_KwH'] > 0].copy()
        comparison_df['total_consumption'] = comparison_df['Year_total_KwH']
        comparison_df['city'] = comparison_df['City']
        
        return comparison_df[['project_name', 'city', 'total_consumption', 'kwh_per_student', 'kwh_per_m2']].dropna()
    
    def create_efficiency_scatter(self, comparison_df):
        """Create efficiency scatter plot"""
        if not comparison_df.empty:
            fig = px.scatter(
                comparison_df,
                x='kwh_per_m2',
                y='kwh_per_student',
                size='total_consumption',
                color='city',
                hover_data=['project_name'],
                title='Energy Efficiency: kWh per Student vs kWh per m²',
                labels={
                    'kwh_per_m2': 'kWh per m²',
                    'kwh_per_student': 'kWh per Student'
                }
            )
            
            # Add quadrant lines
            if comparison_df['kwh_per_m2'].notna().any() and comparison_df['kwh_per_student'].notna().any():
                avg_per_m2 = comparison_df['kwh_per_m2'].mean()
                avg_per_student = comparison_df['kwh_per_student'].mean()
                
                fig.add_hline(y=avg_per_student, line_dash="dash", line_color="gray", 
                             annotation_text="Avg kWh/student")
                fig.add_vline(x=avg_per_m2, line_dash="dash", line_color="gray", 
                             annotation_text="Avg kWh/m²")
            
            return fig
        else:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for efficiency comparison",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(title='Energy Efficiency Comparison')
            return fig
    
    def prepare_export_data(self, electricity_df, static_df, temp_df):
        """Prepare comprehensive data for export"""
        from data_processor import DataProcessor
        processor = DataProcessor()
        
        # Merge all relevant data
        merged_df = processor.merge_consumption_with_static(electricity_df, static_df)
        
        # Add temperature data summary
        temp_summary = temp_df.groupby('City')['Temperature'].agg(['mean', 'min', 'max']).reset_index()
        temp_summary.columns = ['City', 'avg_temperature', 'min_temperature', 'max_temperature']
        
        # Final merge
        export_df = pd.merge(merged_df, temp_summary, on='City', how='left')
        
        return export_df
    
    def create_efficiency_chart_from_merged(self, merged_df):
        """Create efficiency chart from merged data"""
        # Filter out projects with no consumption or capacity data
        efficiency_df = merged_df[
            (merged_df['Year_total_KwH'] > 0) & 
            (merged_df['total_HE'] > 0) & 
            (merged_df['kwh_per_student'] > 0)
        ].copy()
        
        if not efficiency_df.empty:
            fig = px.scatter(
                efficiency_df,
                x='total_HE',
                y='kwh_per_student',
                size='Year_total_KwH',
                color='City',
                hover_data=['project_name', 'Year_total_KwH'],
                title='Energieffektivitet: kWh per Student vs Antall Studenter',
                labels={
                    'total_HE': 'Antall Studenter (HE)',
                    'kwh_per_student': 'kWh per Student',
                    'Year_total_KwH': 'Totalt Forbruk'
                }
            )
            
            fig.update_layout(
                xaxis_title='Antall Studenter (HE)',
                yaxis_title='kWh per Student'
            )
            
            return fig
        else:
            fig = go.Figure()
            fig.add_annotation(
                text="Ingen effektivitetsdata tilgjengelig",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(title='Energieffektivitetsanalyse')
            return fig
