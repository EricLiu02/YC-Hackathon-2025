#!/usr/bin/env python3
"""
Test script for FastMCP Hotel Agent
"""

import asyncio
from datetime import date, timedelta

def test_fastmcp_import():
    """Test that FastMCP server imports correctly"""
    try:
        from .fast_server import mcp, search_hotels, get_hotel_pricing
        print("✅ FastMCP server imports successfully")
        print(f"   Server name: {mcp.name}")
        return True
    except Exception as e:
        print(f"❌ FastMCP import failed: {e}")
        return False


def test_models_and_fixtures():
    """Test that models and fixtures work"""
    try:
        from .models import HotelSearchRequest, HotelPricingRequest
        from .fixtures import get_demo_hotel_search_response
        
        check_in = date.today() + timedelta(days=30)
        check_out = date.today() + timedelta(days=32)
        
        # Test model creation
        search_req = HotelSearchRequest(
            city="New York",
            check_in_date=check_in,
            check_out_date=check_out,
            adults=2
        )
        print("✅ HotelSearchRequest model works")
        
        # Test fixtures
        demo_response = get_demo_hotel_search_response("New York", check_in, check_out)
        print(f"✅ Demo fixtures work: {len(demo_response.hotels)} hotels")
        
        return True
    except Exception as e:
        print(f"❌ Models/fixtures test failed: {e}")
        return False


async def test_tool_functions():
    """Test that tool functions work directly"""
    try:
        from .fast_server import HotelSearchParams, HotelPricingParams, search_hotels, get_hotel_pricing
        from fastmcp import Context
        
        # Mock context for testing
        class MockContext:
            async def info(self, msg): pass
            async def error(self, msg): pass
        
        ctx = MockContext()
        
        # Test search_hotels
        search_params = HotelSearchParams(
            city="New York",
            check_in_date="2025-03-15",
            check_out_date="2025-03-17",
            adults=2
        )
        
        search_result = await search_hotels(search_params, ctx)
        print(f"✅ search_hotels function works: {len(search_result['hotels'])} hotels found")
        
        # Test get_hotel_pricing
        if search_result['hotels']:
            hotel_id = search_result['hotels'][0]['hotel_id']
            pricing_params = HotelPricingParams(
                hotel_id=hotel_id,
                check_in_date="2025-03-15", 
                check_out_date="2025-03-17",
                adults=2
            )
            
            pricing_result = await get_hotel_pricing(pricing_params, ctx)
            print(f"✅ get_hotel_pricing function works: {pricing_result['hotel_name']}")
        
        return True
    except Exception as e:
        print(f"❌ Tool functions test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🏨 Testing FastMCP Hotel Agent\n")
    
    tests_passed = 0
    total_tests = 3
    
    if test_fastmcp_import():
        tests_passed += 1
    
    if test_models_and_fixtures():
        tests_passed += 1
        
    if await test_tool_functions():
        tests_passed += 1
    
    print(f"\n📊 Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! FastMCP Hotel Agent is ready.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())