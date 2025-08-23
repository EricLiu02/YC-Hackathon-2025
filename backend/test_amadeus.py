#!/usr/bin/env python3
"""
Quick test script to verify Amadeus API connectivity
"""
import os
import sys
from amadeus import Client, ResponseError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_amadeus_connection():
    # Get credentials
    api_key = os.getenv('AMADEUS_API_KEY')
    api_secret = os.getenv('AMADEUS_API_SECRET')
    
    print(f"API Key: {api_key[:10]}..." if api_key else "API Key: None")
    print(f"API Secret: {api_secret[:5]}..." if api_secret else "API Secret: None")
    
    if not api_key or not api_secret:
        print("❌ Missing Amadeus credentials in .env file")
        return False
    
    try:
        # Create Amadeus client - try test environment first
        amadeus = Client(
            client_id=api_key,
            client_secret=api_secret,
            hostname='test'  # Use test environment
        )
        print("✅ Amadeus client created successfully")
        
        # Test simple API call - get airport info for SFO
        print("🔍 Testing API call: airport info for SFO...")
        response = amadeus.reference_data.locations.get(
            keyword='SFO',
            subType='AIRPORT'
        )
        
        if response.data:
            airport = response.data[0]
            print(f"✅ API call successful! Found: {airport.get('name')} ({airport.get('iataCode')})")
            return True
        else:
            print("⚠️ API call returned no data")
            return False
            
    except ResponseError as error:
        print(f"❌ Amadeus API error: Status {error.response.status_code}")
        print(f"   Response body: {error.response.body}")
        return False
    except Exception as error:
        print(f"❌ Unexpected error: {type(error).__name__}: {str(error)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Amadeus API connection...\n")
    success = test_amadeus_connection()
    sys.exit(0 if success else 1)