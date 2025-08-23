#!/usr/bin/env python3
"""
Test script for SearchAPI Google Flights integration
"""
import asyncio
import os
from datetime import date
from dotenv import load_dotenv

from flight_mcp_agent.searchapi_client import SearchAPIFlightClient
from flight_mcp_agent.models import FlightSearchRequest

load_dotenv()

async def test_searchapi():
    print("🧪 Testing SearchAPI Google Flights integration...\n")
    
    # Check API key
    api_key = os.getenv('SEARCHAPI_KEY')
    if not api_key:
        print("❌ Missing SEARCHAPI_KEY in .env file")
        return False
    
    print(f"✅ SearchAPI Key found: {api_key[:10]}...")
    
    try:
        # Create client
        client = SearchAPIFlightClient()
        print("✅ SearchAPI client created successfully")
        
        # Create test flight search request
        request = FlightSearchRequest(
            origin='SFO',
            destination='HNL',
            departure_date=date(2025, 9, 10),
            adults=1,
            children=0,
            infants=0,
            travel_class='ECONOMY',
            max_results=5
        )
        
        print(f"🔍 Searching flights: {request.origin} → {request.destination} on {request.departure_date}")
        
        # Search flights
        response = await client.search_flights(request)
        
        print(f"✅ Search successful! Found {len(response.flights)} flights")
        print(f"   Search ID: {response.search_id}")
        
        # Display first few flights
        for i, flight in enumerate(response.flights[:3], 1):
            print(f"   Flight {i}: {flight.airline_name} - ${flight.price} ({flight.stops} stops)")
            
        return True
        
    except Exception as error:
        print(f"❌ Error: {type(error).__name__}: {str(error)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_searchapi())
    print(f"\n{'✅ Test passed!' if success else '❌ Test failed!'}")