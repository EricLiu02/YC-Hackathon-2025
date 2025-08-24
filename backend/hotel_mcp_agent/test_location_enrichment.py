#!/usr/bin/env python3
"""
Test script for location enrichment integration
"""

import asyncio
import os
from dotenv import load_dotenv
from location_enricher import PerplexityLocationEnricher

load_dotenv()


async def test_location_enrichment():
    """Test the Perplexity location enrichment"""
    
    try:
        enricher = PerplexityLocationEnricher()
        
        # Test queries
        test_queries = [
            "hotels in Paris",
            "New York City hotels",
            "hotels in Tokyo, Japan",
            "London accommodation"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            try:
                location_info = await enricher.enrich_location(query)
                
                print(f"  ✅ City: {location_info.city}")
                print(f"  ✅ Country: {location_info.country} ({location_info.country_code})")
                print(f"  ✅ Currency: {location_info.currency}")
                if location_info.coordinates:
                    print(f"  ✅ Coordinates: {location_info.coordinates}")
                if location_info.bounding_box:
                    print(f"  ✅ Bounding box: {location_info.bounding_box}")
                if location_info.popular_areas:
                    print(f"  ✅ Popular areas: {', '.join(location_info.popular_areas)}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to initialize enricher: {e}")
        print("Make sure PERPLEXITY_API_KEY is set in your .env file")


if __name__ == "__main__":
    asyncio.run(test_location_enrichment())