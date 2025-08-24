#!/usr/bin/env python3
"""
Debug the SearchAPI response structure
"""

import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def debug_response():
    api_key = os.getenv('SEARCHAPI_KEY')
    base_url = "https://www.searchapi.io/api/v1/search"
    
    params = {
        'api_key': api_key,
        'engine': 'google_hotels',
        'q': 'hotels in Boston',
        'check_in_date': '2025-08-31',
        'check_out_date': '2025-09-01'
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Response received")
        
        properties = data.get('properties', [])
        print(f"📊 Found {len(properties)} properties")
        
        if properties:
            first_property = properties[0]
            print("\n🏨 First property structure:")
            print(json.dumps(first_property, indent=2))
            
            print("\n🔍 Available keys:")
            for key in sorted(first_property.keys()):
                print(f"   {key}: {type(first_property[key])}")
                
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    debug_response()