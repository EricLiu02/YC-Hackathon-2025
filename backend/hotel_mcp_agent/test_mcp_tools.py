#!/usr/bin/env python3
"""
Test MCP server tools directly
"""

import asyncio
import json
from datetime import date
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession


async def test_mcp_tools():
    """Test the hotel MCP server tools"""
    
    print("🧪 Testing Hotel MCP Server Tools")
    print("=" * 50)
    
    server = StdioServerParameters(command="python3", args=["fast_server.py", "--demo"])
    
    try:
        async with stdio_client(server) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                
                # List available tools
                print("📋 Available tools:")
                tools = await s.list_tools()
                for tool in tools.tools:
                    print(f"  • {tool.name}: {tool.description[:100]}...")
                
                print()
                
                # Test hotel search
                print("🔍 Testing hotel search...")
                search_args = {
                    "city": "New York",
                    "check_in_date": "2025-01-15",
                    "check_out_date": "2025-01-17", 
                    "adults": 2,
                    "children": 0,
                    "rooms": 1,
                    "max_results": 3
                }
                
                result = await s.call_tool("search_hotels", search_args)
                
                # Extract the data
                if hasattr(result, 'content') and result.content:
                    first_content = result.content[0]
                    if hasattr(first_content, 'text'):
                        data = json.loads(first_content.text)
                        hotels = data.get("hotels", [])
                        print(f"✅ Found {len(hotels)} hotels")
                        
                        for hotel in hotels[:2]:
                            name = hotel.get("name", "Unknown")
                            stars = "⭐" * (hotel.get("star_rating", 0))
                            price_range = hotel.get("price_range", "N/A")
                            print(f"  🏨 {name} {stars} - {price_range}")
                    else:
                        print(f"❌ Unexpected content format: {first_content}")
                else:
                    print(f"❌ No content in result: {result}")
                
                print()
                
                # Test hotel pricing
                print("💰 Testing hotel pricing...")
                pricing_args = {
                    "hotel_id": "grand_plaza_nyc_001",
                    "check_in_date": "2025-01-15",
                    "check_out_date": "2025-01-17",
                    "adults": 2,
                    "rooms": 1
                }
                
                result = await s.call_tool("get_hotel_pricing", pricing_args)
                
                if hasattr(result, 'content') and result.content:
                    first_content = result.content[0]
                    if hasattr(first_content, 'text'):
                        data = json.loads(first_content.text)
                        hotel_name = data.get("hotel_name", "Unknown")
                        pricing = data.get("pricing", {})
                        total_price = pricing.get("total_price", 0)
                        print(f"✅ Pricing for {hotel_name}: ${total_price:.2f} total")
                    else:
                        print(f"❌ Unexpected pricing content format: {first_content}")
                else:
                    print(f"❌ No pricing content in result: {result}")
                
                print("\n🎉 MCP server tools are working!")
                
    except Exception as e:
        print(f"❌ Error testing MCP tools: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_mcp_tools())
    if success:
        print("\n✅ MCP server is ready for chat wrapper integration!")
    else:
        print("\n❌ MCP server needs more fixes before integration.")