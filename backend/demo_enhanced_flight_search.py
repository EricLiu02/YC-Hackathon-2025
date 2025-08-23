#!/usr/bin/env python3
"""
Demo script showing the enhanced flight search with Perplexity location research
and improved summarization showing the best 5 flight options.
"""
import asyncio
import sys
from flight_mcp_agent.chat_wrapper import enhanced_search_with_location_research, _summarize, FlightEntities

async def demo_enhanced_search():
    """Demonstrate the enhanced flight search system."""
    
    print("🚀 Enhanced Flight Search Demo")
    print("=" * 60)
    
    # Test case: "SFO to Shanghai today" - the original problem case
    print("\n📍 Test Case: SFO to Shanghai today")
    print("This would previously default to LAX, now it should find both PVG and SHA airports")
    
    entities = FlightEntities(
        intent='search_flights',
        origin='SFO',
        destination=None,  # Missing destination triggers research
        departure_date='2025-08-23'
    )
    
    original_text = "sfo to shanghai today"
    
    try:
        print(f"🔍 Researching airports for: '{original_text}'")
        result = await enhanced_search_with_location_research(entities, original_text)
        
        route_count = result.get('route_combinations', 0)
        total_flights = result.get('total_results', 0)
        
        print(f"✅ Found {route_count} route combinations with {total_flights} total flights")
        
        if route_count > 0:
            print("\n🛩️  Routes searched:")
            for route in result.get('routes', []):
                route_name = route['route'] 
                flight_count = route.get('flight_count', len(route.get('flights', [])))
                print(f"  • {route_name}: {flight_count} flights found")
        
        # Generate enhanced summary
        if total_flights > 0:
            print(f"\n📋 Enhanced Summary (Best 5 Options):")
            print("-" * 50)
            summary = _summarize(result, entities)
            print(summary)
            print("-" * 50)
        else:
            print("\n⚠️  No flights found for this route combination")
            
    except Exception as e:
        print(f"❌ Error during enhanced search: {e}")

async def demo_static_mapping():
    """Demo showing static mapping works for common locations"""
    
    print(f"\n📍 Test Case: SFO to Tokyo next week")
    print("Should find both NRT and HND airports via static mapping")
    
    entities = FlightEntities(
        intent='search_flights',
        origin='SFO',
        destination=None,
        departure_date='2025-08-30'
    )
    
    original_text = "sfo to tokyo next week"
    
    try:
        result = await enhanced_search_with_location_research(entities, original_text)
        
        route_count = result.get('route_combinations', 0)
        print(f"✅ Found {route_count} route combinations")
        
        for route in result.get('routes', []):
            route_name = route['route']
            flight_count = route.get('flight_count', 0)
            print(f"  • {route_name}: {flight_count} flights")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Run the demo"""
    await demo_enhanced_search()
    await demo_static_mapping()
    
    print(f"\n🎉 Demo Complete!")
    print("\nKey Improvements:")
    print("• ✅ Location Research: Shanghai → PVG, SHA airports")
    print("• ✅ Multiple Routes: Searches all relevant airport combinations")  
    print("• ✅ Best 5 Options: Summarization shows top flights by price")
    print("• ✅ Perplexity Integration: Handles unknown locations via AI")
    print("• ✅ Static Mapping: 100+ cities/countries for instant lookup")

if __name__ == "__main__":
    asyncio.run(main())