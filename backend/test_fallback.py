#!/usr/bin/env python3
"""
Test script for SearchAPI fallback functionality
"""
import asyncio
from datetime import date
from dotenv import load_dotenv

from flight_mcp_agent.searchapi_client import SearchAPIFlightClient
from flight_mcp_agent.models import FlightSearchRequest

load_dotenv()

async def test_fallback():
    print("🧪 Testing SearchAPI with fallback functionality...\n")
    
    client = SearchAPIFlightClient()
    
    # Test 1: Normal flight search that should work (SFO to HNL)
    print("=== Test 1: Popular route (SFO → HNL) ===")
    request1 = FlightSearchRequest(
        origin='SFO',
        destination='HNL',
        departure_date=date(2025, 9, 10),
        adults=1,
        max_results=3
    )
    
    try:
        response1 = await client.search_flights(request1)
        print(f"✅ Found {len(response1.flights)} flights")
        for i, flight in enumerate(response1.flights, 1):
            print(f"   Flight {i}: {flight.airline_name} - ${flight.price}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Obscure route that might trigger fallback
    print("=== Test 2: Obscure route (might trigger fallback) ===")
    request2 = FlightSearchRequest(
        origin='SFO',
        destination='XYZ',  # Fake destination to potentially trigger fallback
        departure_date=date(2025, 9, 10),
        adults=1,
        max_results=3
    )
    
    try:
        response2 = await client.search_flights(request2)
        print(f"✅ Found {len(response2.flights)} flights")
        if response2.flights:
            print(f"   Search ID: {response2.search_id}")
            for i, flight in enumerate(response2.flights, 1):
                print(f"   Flight {i}: {flight.airline_name} - ${flight.price} ({flight.departure_airport} → {flight.arrival_airport})")
        else:
            print("   No flights found even with fallback")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "="*50 + "\n")
    
    # Test 3: Test Travel Explore directly (open destination from SFO)
    print("=== Test 3: Travel Explore direct test ===")
    request3 = FlightSearchRequest(
        origin='SFO',
        destination='',  # Empty destination should use Travel Explore
        departure_date=date(2025, 9, 10),
        adults=1,
        max_results=5
    )
    
    try:
        # Test the travel explore method directly
        response3 = await client._search_travel_explore(request3)
        print(f"✅ Travel Explore found {len(response3.flights)} destinations")
        for i, flight in enumerate(response3.flights[:3], 1):
            print(f"   Destination {i}: {flight.arrival_airport} - ${flight.price}")
    except Exception as e:
        print(f"❌ Travel Explore Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_fallback())