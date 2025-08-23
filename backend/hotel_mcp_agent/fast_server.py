#!/usr/bin/env python3
"""
Hotel MCP Agent Service using FastMCP Architecture
"""

import os
import sys
from datetime import date
from typing import List, Optional, Dict, Any

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from models import HotelSearchRequest, HotelPricingRequest
from searchapi_client import SearchAPIHotelClient

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Hotel Search & Pricing Agent 🏨")

# Initialize the hotel client
use_demo_data = "--demo" in sys.argv
hotel_client = SearchAPIHotelClient(use_demo_data=use_demo_data)


class HotelSearchParams(BaseModel):
    """Hotel search parameters for FastMCP tool"""
    city: str = Field(..., description="City or destination to search for hotels (e.g., 'New York', 'Paris')")
    check_in_date: str = Field(..., description="Check-in date in YYYY-MM-DD format")
    check_out_date: str = Field(..., description="Check-out date in YYYY-MM-DD format")
    adults: int = Field(2, description="Number of adult guests")
    children: int = Field(0, description="Number of children")
    rooms: int = Field(1, description="Number of rooms needed")
    hotel_class: Optional[str] = Field(None, description="Hotel star rating filter (3, 4, or 5 stars)")
    max_price: Optional[float] = Field(None, description="Maximum price per night in USD")
    amenities: Optional[List[str]] = Field(None, description="Desired amenities (e.g., ['wifi', 'pool', 'gym', 'spa'])")
    sort_by: str = Field("price", description="Sort results by price, rating, or distance")
    max_results: int = Field(10, description="Maximum number of hotels to return")


class HotelPricingParams(BaseModel):
    """Hotel pricing parameters for FastMCP tool"""
    hotel_id: str = Field(..., description="Hotel ID from search results")
    room_type: Optional[str] = Field(None, description="Specific room type (optional)")
    check_in_date: str = Field(..., description="Check-in date in YYYY-MM-DD format")
    check_out_date: str = Field(..., description="Check-out date in YYYY-MM-DD format")
    adults: int = Field(2, description="Number of adult guests")
    children: int = Field(0, description="Number of children")
    rooms: int = Field(1, description="Number of rooms needed")


@mcp.tool
async def search_hotels(params: HotelSearchParams, ctx: Context) -> Dict[str, Any]:
    """
    Search for hotels based on city, dates, and preferences.
    
    Returns comprehensive hotel information including pricing, amenities, location,
    reviews, and available room types for the specified search criteria.
    """
    try:
        await ctx.info(f"🔍 Searching for hotels in {params.city} from {params.check_in_date} to {params.check_out_date}")
        
        # Convert string dates to date objects
        check_in = date.fromisoformat(params.check_in_date)
        check_out = date.fromisoformat(params.check_out_date)
        
        # Create search request
        search_request = HotelSearchRequest(
            city=params.city,
            check_in_date=check_in,
            check_out_date=check_out,
            adults=params.adults,
            children=params.children,
            rooms=params.rooms,
            hotel_class=params.hotel_class,
            max_price=params.max_price,
            amenities=params.amenities,
            sort_by=params.sort_by,
            max_results=params.max_results
        )
        
        # Search for hotels
        response = await hotel_client.search_hotels(search_request)
        
        await ctx.info(f"✅ Found {len(response.hotels)} hotels")
        
        # Convert to JSON-serializable format
        hotels_data = []
        for hotel in response.hotels:
            hotel_dict = hotel.model_dump()
            hotels_data.append(hotel_dict)
        
        result = {
            "hotels": hotels_data,
            "search_id": response.search_id,
            "total_results": response.total_results,
            "city": response.city,
            "check_in_date": response.check_in_date.isoformat(),
            "check_out_date": response.check_out_date.isoformat()
        }
        
        return result
        
    except Exception as e:
        await ctx.error(f"❌ Error searching hotels: {str(e)}")
        raise


@mcp.tool  
async def get_hotel_pricing(params: HotelPricingParams, ctx: Context) -> Dict[str, Any]:
    """
    Get detailed pricing information for a specific hotel and room type.
    
    Returns comprehensive pricing breakdown including base price, taxes, fees,
    total cost, cancellation policy, and booking conditions.
    """
    try:
        await ctx.info(f"💰 Getting pricing for hotel {params.hotel_id} from {params.check_in_date} to {params.check_out_date}")
        
        # Convert string dates to date objects
        check_in = date.fromisoformat(params.check_in_date)
        check_out = date.fromisoformat(params.check_out_date)
        
        # Create pricing request
        pricing_request = HotelPricingRequest(
            hotel_id=params.hotel_id,
            room_type=params.room_type,
            check_in_date=check_in,
            check_out_date=check_out,
            adults=params.adults,
            children=params.children,
            rooms=params.rooms
        )
        
        # Get hotel pricing
        response = await hotel_client.get_hotel_pricing(pricing_request)
        
        await ctx.info(f"✅ Retrieved pricing for {response.hotel_name}")
        
        # Convert to JSON-serializable format
        pricing_dict = response.model_dump()
        if pricing_dict.get("cancellation_policy", {}).get("cancellation_deadline"):
            pricing_dict["cancellation_policy"]["cancellation_deadline"] = response.cancellation_policy.cancellation_deadline.isoformat()
        
        return pricing_dict
        
    except Exception as e:
        await ctx.error(f"❌ Error getting hotel pricing: {str(e)}")
        raise


@mcp.resource("hotels://demo/nyc")
async def demo_nyc_hotels():
    """Demo hotel data for New York City"""
    from fixtures import get_demo_hotel_search_response
    from datetime import timedelta
    
    check_in = date.today() + timedelta(days=30)
    check_out = date.today() + timedelta(days=32)
    
    demo_response = get_demo_hotel_search_response("New York", check_in, check_out)
    return {
        "description": "Demo hotel data for New York City",
        "hotels_count": len(demo_response.hotels),
        "hotels": [{"name": h.name, "price_range": h.price_range} for h in demo_response.hotels]
    }


@mcp.resource("hotels://config")
async def hotel_config():
    """Hotel service configuration"""
    return {
        "service_name": "Hotel MCP Agent",
        "version": "1.0.0",
        "api_provider": "SearchAPI Google Hotels",
        "demo_mode": use_demo_data,
        "supported_features": [
            "Hotel Search",
            "Pricing Details", 
            "Room Types",
            "Amenities Filter",
            "Star Rating Filter",
            "Price Sorting"
        ]
    }


def main():
    """Run the Hotel MCP Agent server"""
    global use_demo_data
    
    # Check for demo mode
    if "--demo" in sys.argv:
        use_demo_data = True
        print("🏨 Starting Hotel MCP Agent in DEMO mode...")
    else:
        use_demo_data = True  # Default to demo for now
        # In production, check for API key:
        # api_key = os.getenv('SEARCH_API_KEY')
        # if not api_key:
        #     print("⚠️  No SEARCH_API_KEY found, using demo mode")
        #     use_demo_data = True
        # else:
        #     use_demo_data = False
        #     print("🏨 Starting Hotel MCP Agent with SearchAPI...")
    
    # Reinitialize client with correct mode
    global hotel_client
    hotel_client = SearchAPIHotelClient(use_demo_data=use_demo_data)
    
    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()