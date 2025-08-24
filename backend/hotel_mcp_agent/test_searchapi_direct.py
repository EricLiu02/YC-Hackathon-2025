#!/usr/bin/env python3
"""
Direct test of SearchAPI to debug the issue
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_searchapi_direct():
    api_key = os.getenv('SEARCHAPI_KEY') or os.getenv('SEARCH_API_KEY')
    print(f"🔑 API Key: {'✅ Found' if api_key else '❌ Not found'}")
    
    if not api_key:
        print("❌ No API key found!")
        return
    
    # Test SearchAPI directly
    base_url = "https://www.searchapi.io/api/v1/search"
    
    params = {
        'api_key': api_key,
        'engine': 'google_hotels',
        'q': 'hotels in Boston',
        'check_in_date': '2025-08-24',
        'check_out_date': '2025-08-25',
        'adults': 2,
        'currency': 'USD',
        'gl': 'us',
        'hl': 'en'
    }
    
    print(f"🔍 Testing SearchAPI with params: {params}")
    print(f"🌐 URL: {base_url}")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        print(f"📡 Response status: {response.status_code}")
        print(f"📊 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got response")
            print(f"🏨 Properties found: {len(data.get('properties', []))}")
            
            # Show first property
            properties = data.get('properties', [])
            if properties:
                first = properties[0]
                print(f"🏨 First hotel: {first.get('name', 'Unknown')}")
                print(f"📍 Location: {first.get('address', 'Unknown')}")
                print(f"⭐ Rating: {first.get('overall_rating', 'N/A')}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_searchapi_direct()