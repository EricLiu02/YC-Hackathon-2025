#!/usr/bin/env python3
"""
Simple test script for the Flight MCP Agent Server
"""

import asyncio
import json
from datetime import date, timedelta

from .models import FlightSearchRequest, FlightPricingRequest
from .amadeus_client import AmadeusFlightClient


async def test_demo_client():
    """Test the flight client in demo mode"""
    print("=== Testing Flight MCP Agent in Demo Mode ===\n")
    
    client = AmadeusFlightClient(use_demo_data=True)
    
    # Test flight search
    print("1. Testing flight search...")
    search_request = FlightSearchRequest(
        origin="JFK",
        destination="LAX", 
        departure_date=date.today() + timedelta(days=30),
        adults=1,
        travel_class="ECONOMY",
        max_results=3
    )
    
    search_result = await client.search_flights(search_request)
    print(f"   Found {len(search_result.flights)} flights")
    print(f"   Search ID: {search_result.search_id}")
    
    if search_result.flights:
        first_flight = search_result.flights[0]
        print(f"   Sample flight: {first_flight.airline_name} {first_flight.flight_id}")
        print(f"   Price: ${first_flight.price} {first_flight.currency}")
        print(f"   Departure: {first_flight.departure_time}")
    
    # Test flight pricing
    print("\n2. Testing flight pricing...")
    if search_result.flights:
        flight_ids = [flight.flight_id for flight in search_result.flights[:2]]
        pricing_request = FlightPricingRequest(flight_ids=flight_ids)
        
        pricing_results = await client.get_flight_pricing(pricing_request)
        print(f"   Got pricing for {len(pricing_results)} flights")
        
        for pricing in pricing_results:
            print(f"   Flight {pricing.flight_id}: ${pricing.price_breakdown.total} {pricing.price_breakdown.currency}")
            print(f"     Base fare: ${pricing.price_breakdown.base_fare}")
            print(f"     Taxes: ${pricing.price_breakdown.taxes}")
            print(f"     Fees: ${pricing.price_breakdown.fees}")


async def test_real_api():
    """Test with real Amadeus API (requires valid credentials)"""
    print("\n=== Testing Flight MCP Agent with Real API ===\n")
    
    try:
        client = AmadeusFlightClient(use_demo_data=False)
        
        # Test a simple flight search
        search_request = FlightSearchRequest(
            origin="NYC",
            destination="LAX",
            departure_date=date.today() + timedelta(days=30),
            adults=1,
            max_results=5
        )
        
        search_result = await client.search_flights(search_request)
        print(f"Real API search returned {len(search_result.flights)} flights")
        
        if search_result.flights:
            first_flight = search_result.flights[0]
            print(f"Sample real flight: {first_flight.airline_name}")
            print(f"Price: ${first_flight.price} {first_flight.currency}")
        
    except ValueError as e:
        print(f"API credentials not available: {e}")
        print("Skipping real API test...")
    except Exception as e:
        print(f"API test failed (falling back to demo data): {e}")


def test_json_serialization():
    """Test that all models can be properly JSON serialized"""
    print("\n=== Testing JSON Serialization ===\n")
    
    from .fixtures import get_demo_flight_search_response, get_demo_flight_pricing
    
    # Test flight search response serialization
    search_response = get_demo_flight_search_response("JFK", "LAX")
    
    # Convert to dict and handle datetime serialization
    flights_data = []
    for flight in search_response.flights:
        flight_dict = flight.model_dump()
        flight_dict["departure_time"] = flight.departure_time.isoformat()
        flight_dict["arrival_time"] = flight.arrival_time.isoformat()
        flights_data.append(flight_dict)
    
    result = {
        "flights": flights_data,
        "search_id": search_response.search_id,
        "total_results": search_response.total_results
    }
    
    json_str = json.dumps(result, indent=2)
    print("Flight search JSON serialization: ✓")
    print(f"JSON length: {len(json_str)} characters")
    
    # Test pricing response serialization
    pricing_response = get_demo_flight_pricing("AA123_2025_01_15")
    pricing_dict = pricing_response.model_dump()
    pricing_dict["last_ticketing_date"] = pricing_response.last_ticketing_date.isoformat()
    
    pricing_json = json.dumps(pricing_dict, indent=2)
    print("Flight pricing JSON serialization: ✓")
    print(f"Pricing JSON length: {len(pricing_json)} characters")


async def main():
    """Run all tests"""
    await test_demo_client()
    await test_real_api()
    test_json_serialization()
    print("\n=== All tests completed ===")


if __name__ == "__main__":
    asyncio.run(main())