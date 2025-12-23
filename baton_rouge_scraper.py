"""
BATON ROUGE PROPERTY SCRAPER
Uses official ArcGIS REST API
"""

import requests
import pandas as pd
from datetime import datetime
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class BatonRougePropertyScraper:
    def __init__(self):
        self.gis_base = "https://maps.brla.gov/gis/rest/services"
        self.parcels_url = f"{self.gis_base}/Cadastral/Parcels/MapServer/0"
        self.session = requests.Session()
        self.properties = []
        logger.info("Initialized Baton Rouge Property Scraper")
    
    def get_parcel_by_address(self, address):
        """Find a parcel by address."""
        geocode_url = f"{self.gis_base}/EBR_Composite_Locator/GeocodeServer/findAddressCandidates"
        
        params = {
            'SingleLine': address,
            'f': 'json',
            'outFields': '*'
        }
        
        try:
            response = requests.get(geocode_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('candidates'):
                best_match = data['candidates'][0]
                location = best_match.get('location', {})
                return self.get_parcel_by_location(location.get('x'), location.get('y'))
            
            return None
        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
            return None
    
    def get_parcel_by_location(self, x, y):
        """Get parcel at specific coordinates."""
        query_url = f"{self.parcels_url}/query"
        
        params = {
            'geometry': f"{x},{y}",
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'returnGeometry': 'false',
            'f': 'json'
        }
        
        try:
            response = requests.get(query_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('features'):
                return data['features'][0]['attributes']
            return None
        except Exception as e:
            logger.error(f"Error querying parcel: {e}")
            return None
    
    def search_parcels_by_zip(self, zip_code):
        """Get all parcels in a ZIP code."""
        query_url = f"{self.parcels_url}/query"
        
        params = {
            'where': f"ZIP = '{zip_code}'",
            'outFields': '*',
            'returnGeometry': 'false',
            'f': 'json',
            'resultRecordCount': 1000
        }
        
        try:
            logger.info(f"Searching parcels in ZIP {zip_code}...")
            response = requests.get(query_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            parcels = []
            for feature in data.get('features', []):
                parcels.append(feature['attributes'])
            
            logger.info(f"Found {len(parcels)} parcels")
            return parcels
        except Exception as e:
            logger.error(f"Error searching parcels: {e}")
            return []
    
    def export_to_csv(self, data, filename=None):
        """Export to CSV."""
        if not data:
            logger.warning("No data to export")
            return None
        
        if filename is None:
            filename = f"baton_rouge_parcels_{datetime.now().strftime('%Y%m%d')}.csv"
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        logger.info(f"Exported {len(data)} records to {filename}")
        return filename


if __name__ == "__main__":
    scraper = BatonRougePropertyScraper()
    
    # Example: Search by ZIP
    parcels = scraper.search_parcels_by_zip("70808")
    if parcels:
        scraper.export_to_csv(parcels)
        print(f"Found {len(parcels)} properties in ZIP 70808")
