#!/usr/bin/env python3
"""
Debug the SearchAPI request
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def debug_api():
    api_key = os.getenv('SEARCHAPI_KEY')
    base_url = "https://www.searchapi.io/api/v1/search"
    
    params = {
        'api_key': api_key,
        'engine': 'google_hotels',
        'q': 'hotels in Boston',
        'check_in_date': '2025-08-31',
        'check_out_date': '2025-09-01',
        'adults': 2,
        'children': 0,
        'rooms': 1,
        'currency': 'USD',
        'gl': 'us',
        'hl': 'en',
        'sort_by': '1'
    }
    
    print("🔍 Making request with params:")
    for k, v in params.items():
        if k != 'api_key':
            print(f"   {k}: {v}")
    
    response = requests.get(base_url, params=params)
    print(f"\n📡 Response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Response text: {response.text}")
        
        # Try with minimal params
        print("\n🔄 Trying with minimal params...")
        minimal_params = {
            'api_key': api_key,
            'engine': 'google_hotels',
            'q': 'hotels in Boston',
            'check_in_date': '2025-08-31',
            'check_out_date': '2025-09-01'
        }
        
        response2 = requests.get(base_url, params=minimal_params)
        print(f"📡 Minimal request status: {response2.status_code}")
        if response2.status_code != 200:
            print(f"❌ Minimal response text: {response2.text}")
        else:
            print("✅ Minimal request worked!")
    else:
        print("✅ Request successful!")

if __name__ == "__main__":
    debug_api()