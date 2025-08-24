#!/usr/bin/env python3
"""
Quick test with manual input to see the exact response
"""

import asyncio
from chat_wrapper import call_search_hotels, HotelEntities

async def test_single_search():
    """Test a single hotel search to see what's returned"""
    
    print("🧪 Testing Single Hotel Search")
    print("=" * 40)
    
    # Create test entities
    entities = HotelEntities(
        intent="search_hotels",
        city="New York",
        check_in_date="2025-01-15",
        check_out_date="2025-01-17",
        adults=2,
        children=0,
        rooms=1,
        max_results=3
    )
    
    print(f"🔍 Searching for hotels with entities: {entities.model_dump()}")
    
    try:
        result = await call_search_hotels(entities)
        print(f"\n📋 Raw result type: {type(result)}")
        print(f"📋 Raw result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if 'data' in result:
            print(f"📋 'data' field type: {type(result['data'])}")
            print(f"📋 'data' content: {str(result['data'])[:200]}...")
        
        if 'hotels' in result:
            hotels = result.get('hotels', [])
            print(f"✅ Found {len(hotels)} hotels")
            if hotels:
                first_hotel = hotels[0]
                print(f"🏨 First hotel: {first_hotel.get('name', 'Unknown')} - {first_hotel.get('hotel_id', 'No ID')}")
        else:
            print("❌ No 'hotels' key in result")
            
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_single_search())
    
    if result:
        print(f"\n🎉 MCP server is responding!")
        print(f"💡 Now you can run the full chat: uv run python chat_wrapper.py")
    else:
        print(f"\n❌ MCP server needs more debugging")