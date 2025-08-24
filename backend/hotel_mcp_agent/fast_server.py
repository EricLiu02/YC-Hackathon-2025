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

# Try absolute imports first (when run from within the directory)
try:
    from models import HotelSearchRequest, HotelPricingRequest
    from searchapi_client import SearchAPIHotelClient
except ImportError:
    # Fall back to relative imports (when run as module from parent directory)
    from .models import HotelSearchRequest, HotelPricingRequest
    from .searchapi_client import SearchAPIHotelClient

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Hotel Search & Pricing Agent 🏨")

# Initialize hotel client - will be created on first use
hotel_client = None


def _ensure_client_initialized():
    """Ensure hotel client is initialized - requires valid API key"""
    global hotel_client
    
    if hotel_client is None:
        # Check for API key - required for operation
        api_key = os.getenv('SEARCH_API_KEY') or os.getenv('SEARCHAPI_KEY')
        if not api_key:
            raise ValueError("SearchAPI key required. Set SEARCH_API_KEY or SEARCHAPI_KEY environment variable.")
        
        hotel_client = SearchAPIHotelClient()
        print("🔧 Hotel client initialized with live SearchAPI data")


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
    sort_by: str = Field("rating", description="Sort results by rating (top hotels), price, or distance")  
    max_results: int = Field(10, description="Maximum number of top hotels to return")


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
    Search for the top 10 hotels based on city, dates, and preferences.
    
    This tool automatically enriches location information using Perplexity Sonar research
    to provide accurate geographical context, currency, and regional data for better
    search results from Google Hotels API via SearchAPI.io.
    
    By default, returns the top 10 highest-rated hotels. Results can be sorted by 
    rating (default), price, or distance. Returns comprehensive hotel information 
    including pricing, amenities, location, reviews, and available room types.
    """
    try:
        # Ensure client is initialized with proper API key detection
        _ensure_client_initialized()
        
        await ctx.info(f"🔍 Searching for hotels in {params.city} from {params.check_in_date} to {params.check_out_date}")
        await ctx.info("✨ Enriching location data with Perplexity research...")
        
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
    
    Note: SearchAPI Google Hotels includes pricing in search results. 
    This tool will search for the specific hotel to get current pricing.
    """
    try:
        # Ensure client is initialized with proper API key detection
        _ensure_client_initialized()
        
        await ctx.info(f"💰 Getting pricing for hotel {params.hotel_id} from {params.check_in_date} to {params.check_out_date}")
        await ctx.info("ℹ️  Pricing data is included in hotel search results")
        
        return {
            "message": "Pricing information is included in hotel search results",
            "hotel_id": params.hotel_id,
            "suggestion": "Use search_hotels to get current pricing and availability for this hotel"
        }
        
    except Exception as e:
        await ctx.error(f"❌ Error: {str(e)}")
        raise


@mcp.resource("hotels://config")
async def hotel_config():
    """Hotel service configuration"""
    return {
        "service_name": "Hotel MCP Agent",
        "version": "1.0.0",
        "api_provider": "SearchAPI Google Hotels",
        "mode": "LIVE",
        "supported_features": [
            "Hotel Search",
            "Pricing Details", 
            "Room Types",
            "Amenities Filter",
            "Star Rating Filter",
            "Price Sorting",
            "Location Enrichment"
        ]
    }


def main():
    """Run the Hotel MCP Agent server"""
    # Check for API key - required for operation
    api_key = os.getenv('SEARCH_API_KEY') or os.getenv('SEARCHAPI_KEY')
    if not api_key:
        print("❌ SearchAPI key required. Set SEARCH_API_KEY or SEARCHAPI_KEY environment variable.")
        sys.exit(1)
    
    print("🏨 Starting Hotel MCP Agent with LIVE SearchAPI data...")
    
    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()