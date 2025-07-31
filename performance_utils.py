# performance_utils.py - Performance optimization utilities
from functools import lru_cache
import pickle
import os

class PerformanceOptimizer:
    """Utilities for optimizing dashboard performance"""

    @staticmethod
    @lru_cache(maxsize=128)
    def load_cached_boundaries(cache_file='nsw_boundaries.pkl'):
        """Load boundaries with caching"""
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

        # Load from source
        gdf = gpd.read_file("YOUR_BOUNDARY_URL")

        # Simplify for web display
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.001)

        # Cache for future use
        with open(cache_file, 'wb') as f:
            pickle.dump(gdf, f)

        return gdf

    @staticmethod
    def create_spatial_index(gdf):
        """Create spatial index for faster queries"""
        return gdf.sindex

    @staticmethod
    def progressive_loading(gdf, zoom_level):
        """Load features based on zoom level"""
        if zoom_level < 8:
            # Show only major regions
            return gdf[gdf['population'] > 100000]
        elif zoom_level < 10:
            # Show medium and large regions
            return gdf[gdf['population'] > 50000]
        else:
            # Show all regions
            return gdf

# Voila configuration for production
# voila_config.py
c.VoilaConfiguration.template = 'material'
c.VoilaConfiguration.enable_nbextensions = True
c.VoilaConfiguration.file_whitelist = ['.*\.(png|jpg|gif|svg|geojson|json)']

# Enable kernel pooling for better performance
c.VoilaConfiguration.preheat_kernel = True
c.VoilaConfiguration.pool_size = 3