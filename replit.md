# Miljøfyrtårn Environmental Management Dashboard

## Overview

This is a Streamlit-based environmental management dashboard for analyzing student housing energy consumption in Norway. The application provides interactive data visualization and mapping capabilities for the Miljøfyrtårn (Environmental Lighthouse) certification program. The dashboard processes temperature, electricity consumption, and static building data to create comprehensive analytics for environmental performance monitoring.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit for web application interface
- **Visualization**: Plotly Express and Plotly Graph Objects for interactive charts and graphs
- **Mapping**: Folium with Streamlit-Folium integration for interactive maps
- **Layout**: Wide layout with expandable sidebar for filters and controls

### Data Processing Architecture
- **Modular Design**: Separate utility classes for different functionalities
  - `DataProcessor`: Handles data loading and cleaning operations
  - `ChartUtils`: Manages chart creation and visualization logic
  - `MapUtils`: Handles geographical data visualization and mapping
- **Data Pipeline**: CSV file processing with error handling and data validation
- **Caching**: Streamlit caching for improved performance when loading data

### Data Storage
- **File-based Storage**: CSV files stored in `attached_assets` directory
- **Data Types**: 
  - Temperature data with time-series information
  - Static building data including coordinates and building specifications
  - Electricity consumption data with monthly and yearly totals
- **Data Processing**: Pandas for data manipulation with numeric type conversion and NaN handling

### Visualization Components
- **Interactive Charts**: Monthly consumption trends, comparative analysis, and time-series visualizations
- **Geographic Mapping**: Color-coded markers based on energy consumption levels with popup information
- **Filtering System**: City and year-based filtering capabilities through sidebar controls

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for Python
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing support
- **Plotly**: Interactive plotting and visualization library

### Visualization and Mapping
- **Folium**: Python wrapper for Leaflet.js mapping
- **Streamlit-Folium**: Integration between Streamlit and Folium maps
- **OpenStreetMap**: Base map tiles for geographical visualization

### Data Processing
- **CSV File Format**: Semicolon-separated values with UTF-8 encoding support
- **Error Handling**: Built-in exception handling for file loading and data processing operations

The application follows a clean separation of concerns with utility classes handling specific functionality areas, making it maintainable and extensible for future environmental monitoring features.