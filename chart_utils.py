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
        """Create comprehensive temperature and consumption correlation analysis"""
        try:
            # Prepare monthly consumption data
            monthly_consumption = self.prepare_monthly_consumption_data(electricity_df)
            
            # Create subplots with multiple charts
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("Temperatur og Graddager", "Månedlig Strømforbruk", 
                               "Graddager vs Forbruk", "Temperatur vs Forbruk"),
                specs=[[{"secondary_y": True}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]],
                vertical_spacing=0.12
            )
            
            # Chart 1: Temperature and Degree Days over time
            cities = temp_df['City'].unique()
            for city in cities:
                city_temp = temp_df[temp_df['City'] == city].copy()
                if not city_temp.empty:
                    # Sort by year and month for proper time series
                    city_temp = city_temp.sort_values(['Year', 'Month'])
                    
                    # Add temperature line
                    fig.add_trace(
                        go.Scatter(
                            x=city_temp['Time'],
                            y=city_temp['Temperature'],
                            name=f"{city} Temperatur",
                            line=dict(color='blue', width=2),
                            legendgroup=city
                        ),
                        row=1, col=1, secondary_y=False
                    )
                    
                    # Add degree days line
                    fig.add_trace(
                        go.Scatter(
                            x=city_temp['Time'],
                            y=city_temp['Monthly_HDD'],
                            name=f"{city} Graddager",
                            line=dict(color='red', width=2, dash='dash'),
                            legendgroup=city
                        ),
                        row=1, col=1, secondary_y=True
                    )
            
            # Chart 2: Monthly consumption trends
            if not monthly_consumption.empty:
                fig.add_trace(
                    go.Bar(
                        x=monthly_consumption['Month'],
                        y=monthly_consumption['Total_Consumption'],
                        name="Totalt Forbruk",
                        marker_color='green',
                        opacity=0.7
                    ),
                    row=1, col=2
                )
            
            # Chart 3: Degree Days vs Consumption scatter
            correlation_data = self.merge_temp_consumption_data(temp_df, electricity_df)
            if not correlation_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=correlation_data['Monthly_HDD'],
                        y=correlation_data['Monthly_Consumption'],
                        mode='markers',
                        name="Graddager vs Forbruk",
                        marker=dict(
                            size=8,
                            color=correlation_data['Temperature'],
                            colorscale='RdYlBu_r',
                            showscale=True,
                            colorbar=dict(title="Temp (°C)", x=1.1)
                        ),
                        text=correlation_data['Time'],
                        hovertemplate="<b>%{text}</b><br>" +
                                     "Graddager: %{x:.0f}<br>" +
                                     "Forbruk: %{y:,.0f} kWh<br>" +
                                     "Temperatur: %{marker.color:.1f}°C<extra></extra>"
                    ),
                    row=2, col=1
                )
            
            # Chart 4: Temperature vs Consumption scatter
            if not correlation_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=correlation_data['Temperature'],
                        y=correlation_data['Monthly_Consumption'],
                        mode='markers',
                        name="Temperatur vs Forbruk",
                        marker=dict(
                            size=10,
                            color='orange',
                            opacity=0.7
                        ),
                        text=correlation_data['Time'],
                        hovertemplate="<b>%{text}</b><br>" +
                                     "Temperatur: %{x:.1f}°C<br>" +
                                     "Forbruk: %{y:,.0f} kWh<extra></extra>"
                    ),
                    row=2, col=2
                )
            
            # Update layout
            fig.update_layout(
                title="Temperatur og Energiforbruk Analyse",
                height=800,
                showlegend=True,
                legend=dict(x=1.05, y=1)
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Tid", row=1, col=1)
            fig.update_yaxes(title_text="Temperatur (°C)", row=1, col=1, secondary_y=False)
            fig.update_yaxes(title_text="Graddager", row=1, col=1, secondary_y=True, color='red')
            
            fig.update_xaxes(title_text="Måned", row=1, col=2)
            fig.update_yaxes(title_text="Forbruk (kWh)", row=1, col=2)
            
            fig.update_xaxes(title_text="Graddager", row=2, col=1)
            fig.update_yaxes(title_text="Forbruk (kWh)", row=2, col=1)
            
            fig.update_xaxes(title_text="Temperatur (°C)", row=2, col=2)
            fig.update_yaxes(title_text="Forbruk (kWh)", row=2, col=2)
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Feil ved oppretting av temperaturanalyse: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=14
            )
            fig.update_layout(title='Temperatur og Forbruk Korrelasjon')
            return fig
    
    def prepare_monthly_consumption_data(self, electricity_df):
        """Prepare monthly consumption data for analysis"""
        try:
            monthly_columns = [col for col in electricity_df.columns if 'KwH' in col and col != 'Year_total_KwH']
            monthly_data = []
            
            month_map = {
                'Jan_KwH': 'Januar', 'Feb_KwH': 'Februar', 'Mar_KwH': 'Mars',
                'Apr__KwH': 'April', 'may__KwH': 'Mai', 'Jun_KwH': 'Juni',
                'Jul_KwH': 'Juli', 'Aug_KwH': 'August', 'Sep_KwH': 'September',
                'Oct_KwH': 'Oktober', 'Nov_KwH': 'November', 'Dec_KwH': 'Desember'
            }
            
            for col in monthly_columns:
                month_name = month_map.get(col, col.replace('_KwH', '').replace('__KwH', ''))
                total = electricity_df[col].sum()
                monthly_data.append({
                    'Month': month_name,
                    'Total_Consumption': total
                })
            
            return pd.DataFrame(monthly_data)
        except:
            return pd.DataFrame()
    
    def merge_temp_consumption_data(self, temp_df, electricity_df):
        """Merge temperature and consumption data for correlation analysis"""
        try:
            # Get monthly consumption by city and month
            monthly_columns = [col for col in electricity_df.columns if 'KwH' in col and col != 'Year_total_KwH']
            
            correlation_data = []
            
            for _, temp_row in temp_df.iterrows():
                city = temp_row['City']
                year = temp_row['Year']
                month = temp_row['Month']
                
                # Find matching electricity data
                city_elec = electricity_df[
                    (electricity_df['City'] == city) & 
                    (electricity_df['Year'] == year)
                ]
                
                if not city_elec.empty:
                    # Map month number to consumption column
                    month_col_map = {
                        1: 'Jan_KwH', 2: 'Feb_KwH', 3: 'Mar_KwH', 4: 'Apr__KwH',
                        5: 'may__KwH', 6: 'Jun_KwH', 7: 'Jul_KwH', 8: 'Aug_KwH',
                        9: 'Sep_KwH', 10: 'Oct_KwH', 11: 'Nov_KwH', 12: 'Dec_KwH'
                    }
                    
                    consumption_col = month_col_map.get(month)
                    if consumption_col and consumption_col in city_elec.columns:
                        monthly_consumption = city_elec[consumption_col].sum()
                        
                        correlation_data.append({
                            'City': city,
                            'Year': year,
                            'Month': month,
                            'Time': temp_row['Time'],
                            'Temperature': temp_row['Temperature'],
                            'HDD_17': temp_row['HDD_17'],
                            'Monthly_HDD': temp_row['Monthly_HDD'],
                            'Monthly_Consumption': monthly_consumption
                        })
            
            return pd.DataFrame(correlation_data)
        except:
            return pd.DataFrame()
    
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
    
    def create_efficiency_scatter(self, merged_df):
        """Create efficiency scatter plot"""
        # Filter for valid data
        scatter_df = merged_df[
            (merged_df['Year_total_KwH'] > 0) & 
            (merged_df['kwh_per_m2'] > 0) & 
            (merged_df['kwh_per_student'] > 0)
        ].copy()
        
        if not scatter_df.empty:
            fig = px.scatter(
                scatter_df,
                x='kwh_per_m2',
                y='kwh_per_student',
                size='Year_total_KwH',
                color='City',
                hover_data=['project_name'],
                title='Energieffektivitet: kWh per Student vs kWh per m²',
                labels={
                    'kwh_per_m2': 'kWh per m²',
                    'kwh_per_student': 'kWh per Student',
                    'Year_total_KwH': 'Totalt Forbruk'
                }
            )
            
            # Add quadrant lines
            if scatter_df['kwh_per_m2'].notna().any() and scatter_df['kwh_per_student'].notna().any():
                avg_per_m2 = scatter_df['kwh_per_m2'].mean()
                avg_per_student = scatter_df['kwh_per_student'].mean()
                
                fig.add_hline(y=avg_per_student, line_dash="dash", line_color="gray", 
                             annotation_text="Snitt kWh/student")
                fig.add_vline(x=avg_per_m2, line_dash="dash", line_color="gray", 
                             annotation_text="Snitt kWh/m²")
            
            return fig
        else:
            fig = go.Figure()
            fig.add_annotation(
                text="Ingen data tilgjengelig for effektivitetssammenligning",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(title='Energieffektivitetssammenligning')
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
