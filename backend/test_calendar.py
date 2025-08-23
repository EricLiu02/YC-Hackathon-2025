#!/usr/bin/env python3
"""
Test script for Google Flights Calendar API integration
"""
import asyncio
from datetime import date
from dotenv import load_dotenv

from flight_mcp_agent.searchapi_client import SearchAPIFlightClient
from flight_mcp_agent.models import FlightCalendarRequest

load_dotenv()

async def test_calendar():
    print("🧪 Testing Google Flights Calendar API integration...\n")
    
    client = SearchAPIFlightClient()
    
    # Test 1: Calendar search for SFO to HNL
    print("=== Test 1: Calendar search (SFO → HNL) ===")
    request1 = FlightCalendarRequest(
        origin='SFO',
        destination='HNL',
        departure_date=date(2025, 9, 10),
        adults=1,
        travel_class='ECONOMY'
    )
    
    try:
        response1 = await client.search_flight_calendar(request1)
        print(f"✅ Calendar search successful!")
        print(f"   Origin: {response1.origin} → Destination: {response1.destination}")
        print(f"   Search ID: {response1.search_id}")
        print(f"   Found {len(response1.calendar_prices)} price points")
        
        # Show first few price points
        for i, price_point in enumerate(response1.calendar_prices[:5], 1):
            print(f"   Date {i}: {price_point.date} - ${price_point.price} {price_point.currency}")
            
        if response1.calendar_prices:
            # Find cheapest and most expensive
            cheapest = min(response1.calendar_prices, key=lambda x: x.price)
            most_expensive = max(response1.calendar_prices, key=lambda x: x.price)
            print(f"   💰 Cheapest: {cheapest.date} - ${cheapest.price}")
            print(f"   💸 Most expensive: {most_expensive.date} - ${most_expensive.price}")
        
    except Exception as e:
        print(f"❌ Calendar Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Calendar search for international route
    print("=== Test 2: Calendar search (SFO → GRU) ===")
    request2 = FlightCalendarRequest(
        origin='SFO',
        destination='GRU',
        departure_date=date(2025, 9, 15),
        adults=2,
        travel_class='ECONOMY'
    )
    
    try:
        response2 = await client.search_flight_calendar(request2)
        print(f"✅ International calendar search successful!")
        print(f"   Origin: {response2.origin} → Destination: {response2.destination}")
        print(f"   Found {len(response2.calendar_prices)} price points")
        
        # Show price range
        if response2.calendar_prices:
            prices = [p.price for p in response2.calendar_prices]
            avg_price = sum(prices) / len(prices)
            print(f"   📊 Average price: ${avg_price:.2f}")
            print(f"   📈 Price range: ${min(prices)} - ${max(prices)}")
        
    except Exception as e:
        print(f"❌ International Calendar Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_calendar())