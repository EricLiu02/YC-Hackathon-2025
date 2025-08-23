import asyncio
import json
from typing import Any, Sequence
from datetime import date, datetime

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import AnyUrl

from .models import FlightSearchRequest, FlightPricingRequest
from .amadeus_client import AmadeusFlightClient
from .fixtures import get_demo_flight_search_response


class FlightMCPServer:
    def __init__(self, use_demo_data: bool = False):
        self.server = Server("flight-mcp-agent")
        self.client = AmadeusFlightClient(use_demo_data=use_demo_data)
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="search_flights",
                    description="Search for flights based on trip constraints",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "Origin airport code (e.g., JFK, LAX)"
                            },
                            "destination": {
                                "type": "string", 
                                "description": "Destination airport code (e.g., JFK, LAX)"
                            },
                            "departure_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Departure date in YYYY-MM-DD format"
                            },
                            "return_date": {
                                "type": "string",
                                "format": "date", 
                                "description": "Return date in YYYY-MM-DD format (optional for round trip)"
                            },
                            "adults": {
                                "type": "integer",
                                "default": 1,
                                "description": "Number of adult passengers"
                            },
                            "children": {
                                "type": "integer", 
                                "default": 0,
                                "description": "Number of child passengers"
                            },
                            "infants": {
                                "type": "integer",
                                "default": 0,
                                "description": "Number of infant passengers"
                            },
                            "travel_class": {
                                "type": "string",
                                "enum": ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
                                "default": "ECONOMY",
                                "description": "Travel class preference"
                            },
                            "max_results": {
                                "type": "integer",
                                "default": 10,
                                "description": "Maximum number of flight options to return"
                            }
                        },
                        "required": ["origin", "destination", "departure_date"]
                    }
                ),
                Tool(
                    name="get_flight_pricing",
                    description="Get detailed pricing information for specific flight IDs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "flight_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of flight IDs to get pricing for"
                            }
                        },
                        "required": ["flight_ids"]
                    }
                ),
                Tool(
                    name="get_cached_flights",
                    description="Get cached/demo flight data for testing purposes",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "Origin airport code"
                            },
                            "destination": {
                                "type": "string",
                                "description": "Destination airport code"
                            }
                        },
                        "required": ["origin", "destination"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            try:
                if name == "search_flights":
                    # Parse the date strings
                    if "departure_date" in arguments:
                        arguments["departure_date"] = date.fromisoformat(arguments["departure_date"])
                    if "return_date" in arguments and arguments["return_date"]:
                        arguments["return_date"] = date.fromisoformat(arguments["return_date"])
                    
                    request = FlightSearchRequest(**arguments)
                    response = await self.client.search_flights(request)
                    
                    # Convert datetime objects to ISO strings for JSON serialization
                    flights_data = []
                    for flight in response.flights:
                        flight_dict = flight.model_dump()
                        flight_dict["departure_time"] = flight.departure_time.isoformat()
                        flight_dict["arrival_time"] = flight.arrival_time.isoformat()
                        flights_data.append(flight_dict)
                    
                    result = {
                        "flights": flights_data,
                        "search_id": response.search_id,
                        "total_results": response.total_results
                    }
                    
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "get_flight_pricing":
                    request = FlightPricingRequest(**arguments)
                    responses = await self.client.get_flight_pricing(request)
                    
                    # Convert to JSON-serializable format
                    pricing_data = []
                    for pricing in responses:
                        pricing_dict = pricing.model_dump()
                        if pricing_dict.get("last_ticketing_date"):
                            pricing_dict["last_ticketing_date"] = pricing.last_ticketing_date.isoformat()
                        pricing_data.append(pricing_dict)
                    
                    return [TextContent(type="text", text=json.dumps(pricing_data, indent=2))]
                
                elif name == "get_cached_flights":
                    response = get_demo_flight_search_response(
                        arguments["origin"], 
                        arguments["destination"]
                    )
                    
                    # Convert datetime objects to ISO strings
                    flights_data = []
                    for flight in response.flights:
                        flight_dict = flight.model_dump()
                        flight_dict["departure_time"] = flight.departure_time.isoformat()
                        flight_dict["arrival_time"] = flight.arrival_time.isoformat()
                        flights_data.append(flight_dict)
                    
                    result = {
                        "flights": flights_data,
                        "search_id": response.search_id,
                        "total_results": response.total_results
                    }
                    
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
                    
            except Exception as e:
                error_msg = f"Error calling tool {name}: {str(e)}"
                return [TextContent(type="text", text=error_msg)]

    async def run(self):
        # Import here to avoid issues with event loop
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="flight-mcp-agent",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main():
    import sys
    use_demo_data = "--demo" in sys.argv
    server = FlightMCPServer(use_demo_data=use_demo_data)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())