# nsw_dashboard.py - Complete NSW Interactive Mapping Dashboard
import ipyleaflet
from ipyleaflet import Map, GeoJSON, Choropleth, LayersControl, FullScreenControl
from ipywidgets import (
    VBox, HBox, Dropdown, IntSlider, SelectMultiple,
    Button, Output, HTML, Layout, GridspecLayout
)
import geopandas as gpd
import pandas as pd
import numpy as np
import json
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class NSWMappingDashboard:
    """Interactive mapping dashboard for NSW data visualization"""

    def __init__(self):
        # NSW center coordinates (Sydney)
        self.nsw_center = (-33.8688, 151.2093)
        self.map_zoom = 7

        # Initialize components
        self.setup_data()
        self.create_widgets()
        self.create_map()
        self.create_data_table()
        self.setup_layout()
        self.connect_events()

    def setup_data(self):
        """Load NSW boundaries and sample demographic data"""
        # Load NSW LGA boundaries
        # In production, replace with actual NSW boundary file
        self.lga_url = "https://data.gov.au/geoserver/nsw-local-government-areas/wfs?request=GetFeature&typeName=ckan_1_f64b8c4dd871409d92a4ae7ed8365786&outputFormat=json"

        try:
            # Load LGA boundaries
            self.nsw_lga = gpd.read_file(self.lga_url)

            # Ensure correct CRS for web mapping
            if self.nsw_lga.crs != 'EPSG:4326':
                self.nsw_lga = self.nsw_lga.to_crs('EPSG:4326')

            # Create sample demographic data
            self.demographic_data = self.create_sample_demographics()

            # Merge geographic and demographic data
            self.merged_data = self.nsw_lga.merge(
                self.demographic_data,
                left_on='nsw_lga__3',
                right_on='lga_name',
                how='left'
            )

        except Exception as e:
            print(f"Error loading data: {e}")
            # Create fallback sample data
            self.create_fallback_data()

    def create_sample_demographics(self):
        """Generate sample demographic data for NSW LGAs"""
        # Sample LGA names from NSW
        lga_names = [
            'Sydney', 'Newcastle', 'Wollongong', 'Central Coast',
            'Lake Macquarie', 'Blacktown', 'Canterbury-Bankstown',
            'Parramatta', 'Northern Beaches', 'Sutherland Shire',
            'Hills Shire', 'Liverpool', 'Penrith', 'Fairfield',
            'Campbelltown', 'Cumberland', 'Georges River', 'Bayside',
            'Inner West', 'Randwick', 'Waverley', 'Woollahra'
        ]

        np.random.seed(42)

        data = {
            'lga_name': lga_names,
            'population': np.random.randint(50000, 500000, len(lga_names)),
            'median_income': np.random.randint(40000, 120000, len(lga_names)),
            'unemployment_rate': np.random.uniform(2, 8, len(lga_names)),
            'housing_median': np.random.randint(400000, 2000000, len(lga_names)),
            'crime_rate': np.random.uniform(20, 100, len(lga_names))
        }

        return pd.DataFrame(data)

    def create_fallback_data(self):
        """Create fallback data if API is unavailable"""
        # Create simple polygon data for demonstration
        from shapely.geometry import Point

        # Major NSW cities with approximate coordinates
        cities = {
            'Sydney': (-33.8688, 151.2093),
            'Newcastle': (-32.9283, 151.7817),
            'Wollongong': (-34.4248, 150.8931),
            'Central Coast': (-33.3208, 151.3442),
            'Albury': (-36.0737, 146.9135),
            'Wagga Wagga': (-35.1082, 147.3598),
            'Coffs Harbour': (-30.2963, 153.1157),
            'Port Macquarie': (-31.4333, 152.9000),
            'Tamworth': (-31.0927, 150.9320),
            'Orange': (-33.2833, 149.1000)
        }

        # Create GeoDataFrame
        geometry = [Point(lon, lat).buffer(0.1) for lat, lon in cities.values()]
        self.nsw_lga = gpd.GeoDataFrame({
            'nsw_lga__3': list(cities.keys()),
            'geometry': geometry
        }, crs='EPSG:4326')

        # Create demographic data
        self.demographic_data = pd.DataFrame({
            'lga_name': list(cities.keys()),
            'population': np.random.randint(20000, 500000, len(cities)),
            'median_income': np.random.randint(40000, 100000, len(cities)),
            'unemployment_rate': np.random.uniform(2, 8, len(cities)),
            'housing_median': np.random.randint(300000, 1500000, len(cities)),
            'crime_rate': np.random.uniform(20, 100, len(cities))
        })

        self.merged_data = self.nsw_lga.merge(
            self.demographic_data,
            left_on='nsw_lga__3',
            right_on='lga_name',
            how='left'
        )

    def create_widgets(self):
        """Create interactive control widgets"""
        # Metric selection dropdown
        self.metric_dropdown = Dropdown(
            options=[
                ('Population', 'population'),
                ('Median Income', 'median_income'),
                ('Unemployment Rate (%)', 'unemployment_rate'),
                ('Housing Median Price', 'housing_median'),
                ('Crime Rate', 'crime_rate')
            ],
            value='population',
            description='Metric:',
            style={'description_width': 'initial'}
        )

        # Year slider (simulated)
        self.year_slider = IntSlider(
            value=2024,
            min=2020,
            max=2025,
            step=1,
            description='Year:',
            continuous_update=False
        )

        # Region filter
        self.region_filter = SelectMultiple(
            options=['All'] + sorted(self.merged_data['lga_name'].dropna().unique().tolist()),
            value=['All'],
            description='Regions:',
            rows=8,
            style={'description_width': 'initial'}
        )

        # Update button
        self.update_button = Button(
            description='Update Map',
            button_style='primary',
            icon='refresh'
        )

        # Output widgets
        self.map_output = Output()
        self.table_output = Output()
        self.stats_output = Output()

        # Info panel
        self.info_html = HTML(
            value="<p>Click on a region to see details</p>",
            layout=Layout(padding='10px')
        )

    def create_map(self):
        """Create the interactive ipyleaflet map"""
        # Base map
        self.map = Map(
            center=self.nsw_center,
            zoom=self.map_zoom,
            basemap=ipyleaflet.basemaps.CartoDB.Positron,
            layout=Layout(height='500px', width='100%')
        )

        # Add controls
        self.map.add_control(FullScreenControl())
        self.map.add_control(LayersControl(position='topright'))

        # Initial choropleth layer
        self.update_choropleth()

        # Map interaction handler
        def handle_interaction(**kwargs):
            if kwargs.get('type') == 'click':
                self.handle_map_click(kwargs.get('coordinates'))

        self.map.on_interaction(handle_interaction)

    def create_data_table(self):
        """Create the data table display"""
        with self.table_output:
            self.update_table()

    def update_choropleth(self):
        """Update the choropleth layer based on selected metric"""
        # Clear existing layers
        for layer in self.map.layers[1:]:  # Keep base layer
            if isinstance(layer, GeoJSON):
                self.map.remove_layer(layer)

        # Get selected metric
        metric = self.metric_dropdown.value

        # Filter data based on region selection
        if 'All' not in self.region_filter.value:
            filtered_data = self.merged_data[
                self.merged_data['lga_name'].isin(self.region_filter.value)
            ]
        else:
            filtered_data = self.merged_data

        # Create color mapping
        if len(filtered_data) > 0 and metric in filtered_data.columns:
            min_val = filtered_data[metric].min()
            max_val = filtered_data[metric].max()

            # Create GeoJSON with properties
            geojson_data = json.loads(filtered_data.to_json())

            # Style function
            def style_function(feature):
                value = feature['properties'].get(metric, 0)
                # Normalize value for color mapping
                if max_val > min_val:
                    normalized = (value - min_val) / (max_val - min_val)
                else:
                    normalized = 0.5

                # Color gradient from light yellow to dark red
                color = self.get_color(normalized)

                return {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7
                }

            # Create GeoJSON layer
            geojson_layer = GeoJSON(
                data=geojson_data,
                style={'style_function': style_function},
                hover_style={'fillOpacity': 0.9, 'weight': 2},
                name=f'{self.metric_dropdown.label} Choropleth'
            )

            self.map.add_layer(geojson_layer)

    def get_color(self, value):
        """Get color for normalized value (0-1)"""
        # Color gradient from light yellow to dark red
        colors = ['#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C',
                  '#FC4E2A', '#E31A1C', '#BD0026', '#800026']

        index = int(value * (len(colors) - 1))
        return colors[min(index, len(colors) - 1)]

    def update_table(self):
        """Update the data table display"""
        self.table_output.clear_output()

        with self.table_output:
            # Filter data
            if 'All' not in self.region_filter.value:
                display_data = self.merged_data[
                    self.merged_data['lga_name'].isin(self.region_filter.value)
                ][['lga_name', 'population', 'median_income',
                   'unemployment_rate', 'housing_median', 'crime_rate']]
            else:
                display_data = self.merged_data[
                    ['lga_name', 'population', 'median_income',
                     'unemployment_rate', 'housing_median', 'crime_rate']
                ]

            # Sort by selected metric
            display_data = display_data.sort_values(
                self.metric_dropdown.value,
                ascending=False
            ).head(20)

            # Format display
            display_html = display_data.to_html(
                index=False,
                float_format=lambda x: f'{x:,.0f}' if x > 100 else f'{x:.1f}',
                classes='table table-striped table-hover',
                table_id='data-table'
            )

            # Add custom styling
            styled_html = f"""
            <style>
                #data-table {{
                    font-size: 12px;
                    width: 100%;
                }}
                #data-table th {{
                    background-color: #f0f0f0;
                    position: sticky;
                    top: 0;
                }}
            </style>
            <div style="height: 400px; overflow-y: auto;">
                {display_html}
            </div>
            """

            display(HTML(styled_html))

    def update_stats(self):
        """Update statistics display"""
        self.stats_output.clear_output()

        with self.stats_output:
            # Calculate statistics
            if 'All' not in self.region_filter.value:
                stats_data = self.merged_data[
                    self.merged_data['lga_name'].isin(self.region_filter.value)
                ]
            else:
                stats_data = self.merged_data

            metric = self.metric_dropdown.value

            if len(stats_data) > 0 and metric in stats_data.columns:
                mean_val = stats_data[metric].mean()
                median_val = stats_data[metric].median()
                min_val = stats_data[metric].min()
                max_val = stats_data[metric].max()

                stats_html = f"""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                    <h4>📊 {self.metric_dropdown.label} Statistics</h4>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                        <div>
                            <strong>Mean:</strong><br>
                            {mean_val:,.0f}
                        </div>
                        <div>
                            <strong>Median:</strong><br>
                            {median_val:,.0f}
                        </div>
                        <div>
                            <strong>Min:</strong><br>
                            {min_val:,.0f}
                        </div>
                        <div>
                            <strong>Max:</strong><br>
                            {max_val:,.0f}
                        </div>
                    </div>
                    <p style="margin-top: 10px; color: #666;">
                        Year: {self.year_slider.value} |
                        Regions: {len(stats_data)} selected
                    </p>
                </div>
                """

                display(HTML(stats_html))

    def handle_map_click(self, coordinates):
        """Handle map click events"""
        lat, lon = coordinates

        # Find clicked region (simplified - in production use proper point-in-polygon)
        clicked_region = None
        for idx, row in self.merged_data.iterrows():
            if row.geometry and row.geometry.contains(Point(lon, lat)):
                clicked_region = row
                break

        if clicked_region is not None:
            info_text = f"""
            <div style="padding: 10px;">
                <h4>{clicked_region['lga_name']}</h4>
                <ul style="list-style: none; padding-left: 0;">
                    <li><strong>Population:</strong> {clicked_region['population']:,.0f}</li>
                    <li><strong>Median Income:</strong> ${clicked_region['median_income']:,.0f}</li>
                    <li><strong>Unemployment:</strong> {clicked_region['unemployment_rate']:.1f}%</li>
                    <li><strong>Housing Median:</strong> ${clicked_region['housing_median']:,.0f}</li>
                    <li><strong>Crime Rate:</strong> {clicked_region['crime_rate']:.1f}</li>
                </ul>
            </div>
            """
            self.info_html.value = info_text

    def connect_events(self):
        """Connect widget events to update functions"""
        def update_all(change=None):
            self.update_choropleth()
            self.update_table()
            self.update_stats()

        # Connect widgets
        self.metric_dropdown.observe(update_all, 'value')
        self.year_slider.observe(update_all, 'value')
        self.region_filter.observe(update_all, 'value')
        self.update_button.on_click(update_all)

        # Initial update
        update_all()

    def setup_layout(self):
        """Create the dashboard layout"""
        # Control panel
        controls = VBox([
            HTML('<h3>🎛️ Dashboard Controls</h3>'),
            self.metric_dropdown,
            self.year_slider,
            HTML('<p><strong>Select Regions:</strong></p>'),
            self.region_filter,
            self.update_button
        ], layout=Layout(padding='10px'))

        # Map panel with info
        map_panel = VBox([
            self.map,
            self.info_html
        ])

        # Create grid layout
        self.dashboard = GridspecLayout(3, 3, height='800px')

        # Header
        self.dashboard[0, :] = HTML(
            '<h1 style="text-align: center;">🗺️ NSW Interactive Mapping Dashboard</h1>'
        )

        # Stats bar
        self.dashboard[1, :] = self.stats_output

        # Controls (left sidebar)
        self.dashboard[2, 0] = controls

        # Map (center)
        self.dashboard[2, 1] = map_panel

        # Table (right)
        self.dashboard[2, 2] = self.table_output

    def display(self):
        """Display the complete dashboard"""
        return self.dashboard

# Create and display the dashboard
dashboard = NSWMappingDashboard()
dashboard.display()