#!/usr/bin/env python3
"""
Direct test of the hotel search functionality
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import date
from searchapi_client import SearchAPIHotelClient
from models import HotelSearchRequest

load_dotenv()

async def test_direct_search():
    """Test hotel search directly without MCP server"""
    
    try:
        client = SearchAPIHotelClient()
        print("✅ Client initialized successfully")
        
        # Create search request for hotels (not guest houses)
        request = HotelSearchRequest(
            city="Boston",
            check_in_date=date(2025, 8, 31),
            check_out_date=date(2025, 9, 1),
            adults=2,
            children=0,
            rooms=1,
            hotel_class="4,5",  # Filter for 4-5 star hotels only
            max_results=5,
            sort_by="rating"
        )
        
        print(f"🔍 Searching for hotels in {request.city}...")
        response = await client.search_hotels(request)
        
        print(f"✅ Found {len(response.hotels)} hotels:")
        for hotel in response.hotels[:3]:  # Show first 3
            print(f"  🏨 {hotel.name}")
            print(f"     ⭐ {hotel.star_rating} stars")
            print(f"     💰 {hotel.price_range}")
            if hotel.location.address:
                print(f"     📍 {hotel.location.address}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_search())