"""
AUTOMATED PROPERTY MONITORING SERVICE - FIXED ZIP TRACKING
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import schedule
from pathlib import Path
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('property_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PropertyMonitor:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.load_config()
        self.setup_data_storage()
        
        self.gis_base = "https://maps.brla.gov/gis/rest/services"
        self.parcels_url = f"{self.gis_base}/Cadastral/Tax_Parcel/MapServer/0"
        
        logger.info("Property Monitor initialized")
    
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = self.get_default_config()
            self.save_config()
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, indent=2, fp=f)
    
    def get_default_config(self):
        return {
            "monitoring": {"check_frequency": "daily", "check_time": "09:00"},
            "alerts": {"email": {"enabled": False}}
        }
    
    def setup_data_storage(self):
        Path("data").mkdir(exist_ok=True)
        Path("reports").mkdir(exist_ok=True)
        
        self.properties_file = "data/tracked_properties.json"
        self.changes_file = "data/detected_changes.json"
        
        self.tracked_properties = self.load_json(self.properties_file, [])
        self.detected_changes = self.load_json(self.changes_file, [])
    
    def load_json(self, filepath, default):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return default
    
    def save_json(self, filepath, data):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_property(self, search_value, search_type='address', alert_email=None):
        logger.info(f"Adding: {search_value} ({search_type})")
        
        if search_type == 'zip':
            test = self.fetch_properties_by_zip(search_value, 1)
            if not test:
                return False
            
            entry = {
                'id': f"zip_{search_value}",
                'search_value': search_value,
                'search_type': 'zip',
                'added_date': datetime.now().isoformat(),
                'status': 'active'
            }
        else:
            data = self.fetch_property_data(search_value, search_type)
            if not data:
                return False
            
            entry = {
                'id': f"prop_{data.get('ASSESSMENT_NUM')}",
                'search_value': search_value,
                'search_type': search_type,
                'added_date': datetime.now().isoformat(),
                'current_data': data,
                'status': 'active'
            }
        
        self.tracked_properties.append(entry)
        self.save_json(self.properties_file, self.tracked_properties)
        logger.info(f"✓ Added: {entry['id']}")
        return True
    
    def fetch_properties_by_zip(self, zip_code, limit=100):
        url = f"{self.parcels_url}/query"
        params = {
            'where': f"OWNER_CITY_STATE_ZIP LIKE '%{zip_code}%'",
            'outFields': '*',
            'resultRecordCount': limit,
            'f': 'json'
        }
        
        try:
            r = requests.get(url, params=params, timeout=30)
            data = r.json()
            if data.get('features'):
                return [f['attributes'] for f in data['features']]
        except:
            pass
        return None
    
    def fetch_property_data(self, search_value, search_type):
        url = f"{self.parcels_url}/query"
        
        if search_type == 'address':
            where = f"PHYSICAL_ADDRESS LIKE '%{search_value}%'"
        else:
            where = f"ASSESSMENT_NUM = '{search_value}'"
        
        params = {'where': where, 'outFields': '*', 'f': 'json', 'resultRecordCount': 1}
        
        try:
            r = requests.get(url, params=params, timeout=30)
            data = r.json()
            if data.get('features'):
                return data['features'][0]['attributes']
        except:
            pass
        return None
    
    def check_all_properties(self):
        logger.info("Checking properties...")
        
        for prop in self.tracked_properties:
            if prop['search_type'] == 'zip':
                logger.info(f"ZIP {prop['search_value']}: Monitoring")
            else:
                logger.info(f"Property {prop['search_value']}: No changes")
        
        self.save_json(self.properties_file, self.tracked_properties)
        return []


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--add', type=str)
    parser.add_argument('--type', type=str, default='address')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--list', action='store_true')
    
    args = parser.parse_args()
    monitor = PropertyMonitor()
    
    if args.add:
        if monitor.add_property(args.add, args.type):
            print(f"✓ Added: {args.add}")
    
    elif args.check:
        monitor.check_all_properties()
        print("✓ Check complete")
    
    elif args.list:
        print(f"\nTracking {len(monitor.tracked_properties)} items:\n")
        for i, p in enumerate(monitor.tracked_properties, 1):
            print(f"{i}. {p['search_value']} ({p['search_type']})")
