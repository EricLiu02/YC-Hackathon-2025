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

from .models import FlightSearchRequest, FlightPricingRequest, FlightCalendarRequest
from .searchapi_client import SearchAPIFlightClient


class FlightMCPServer:
    def __init__(self):
        self.server = Server("flight-mcp-agent")
        self.client = SearchAPIFlightClient()
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="search_flights",
                    description="Search for flights using Google Flights API via SearchAPI. Automatically falls back to Travel Explore API if no specific flights found. Supports both one-way and round-trip searches. Always provide origin and destination as 3-letter IATA airport codes (e.g., SFO, LAX, JFK, HNL). For destinations mentioned as cities or countries, convert to major airport codes (e.g., 'Brasil' -> 'GRU' for São Paulo, 'Hawaii' -> 'HNL' for Honolulu).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "Origin airport IATA code (3 letters). Examples: SFO (San Francisco), JFK (New York), LAX (Los Angeles). REQUIRED."
                            },
                            "destination": {
                                "type": "string", 
                                "description": "Destination airport IATA code (3 letters). Examples: HNL (Hawaii), GRU (São Paulo, Brazil), CDG (Paris). Convert city/country names to major airport codes. REQUIRED."
                            },
                            "departure_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Departure date in YYYY-MM-DD format. Use actual date, not relative terms. REQUIRED."
                            },
                            "return_date": {
                                "type": "string",
                                "format": "date", 
                                "description": "Return date in YYYY-MM-DD format. Only include for round-trip flights. Leave empty for one-way trips."
                            },
                            "adults": {
                                "type": "integer",
                                "default": 1,
                                "minimum": 1,
                                "maximum": 9,
                                "description": "Number of adult passengers (age 12+). Default: 1"
                            },
                            "children": {
                                "type": "integer", 
                                "default": 0,
                                "minimum": 0,
                                "maximum": 8,
                                "description": "Number of child passengers (age 2-11). Default: 0"
                            },
                            "infants": {
                                "type": "integer",
                                "default": 0,
                                "minimum": 0,
                                "maximum": 4,
                                "description": "Number of infant passengers (under 2). Default: 0"
                            },
                            "travel_class": {
                                "type": "string",
                                "enum": ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
                                "default": "ECONOMY",
                                "description": "Cabin class preference. Default: ECONOMY"
                            },
                            "max_results": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50,
                                "description": "Maximum number of flight options to return. Default: 10"
                            }
                        },
                        "required": ["origin", "destination", "departure_date"]
                    }
                ),
                Tool(
                    name="get_flight_pricing",
                    description="Get detailed pricing breakdown for specific flights. Note: This feature is currently not implemented for SearchAPI. Use the search_flights tool instead, which already includes pricing information in the flight results. This tool will return an error indicating that pricing is included in search results.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "flight_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of flight IDs from previous search_flights results. Format examples: 'searchapi_UA123_SFO_HNL_2025-08-23'"
                            }
                        },
                        "required": ["flight_ids"]
                    }
                ),
                Tool(
                    name="search_flight_calendar",
                    description="Search for flight prices across different dates using Google Flights Calendar API. This tool shows price trends over time, helping users find the cheapest dates to fly. Ideal for flexible travel dates or when users want to see price variations across multiple days/weeks.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "Origin airport IATA code (3 letters). Examples: SFO (San Francisco), JFK (New York), LAX (Los Angeles). REQUIRED."
                            },
                            "destination": {
                                "type": "string", 
                                "description": "Destination airport IATA code (3 letters). Examples: HNL (Hawaii), GRU (São Paulo, Brazil), CDG (Paris). Convert city/country names to major airport codes. REQUIRED."
                            },
                            "departure_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Reference departure date in YYYY-MM-DD format. Calendar will show prices around this date. REQUIRED."
                            },
                            "return_date": {
                                "type": "string",
                                "format": "date", 
                                "description": "Return date in YYYY-MM-DD format. Only include for round-trip calendar searches. Leave empty for one-way trips."
                            },
                            "adults": {
                                "type": "integer",
                                "default": 1,
                                "minimum": 1,
                                "maximum": 9,
                                "description": "Number of adult passengers (age 12+). Default: 1"
                            },
                            "children": {
                                "type": "integer", 
                                "default": 0,
                                "minimum": 0,
                                "maximum": 8,
                                "description": "Number of child passengers (age 2-11). Default: 0"
                            },
                            "infants": {
                                "type": "integer",
                                "default": 0,
                                "minimum": 0,
                                "maximum": 4,
                                "description": "Number of infant passengers (under 2). Default: 0"
                            },
                            "travel_class": {
                                "type": "string",
                                "enum": ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
                                "default": "ECONOMY",
                                "description": "Cabin class preference. Default: ECONOMY"
                            }
                        },
                        "required": ["origin", "destination", "departure_date"]
                    }
                ),
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
                
                elif name == "search_flight_calendar":
                    # Parse the date strings
                    if "departure_date" in arguments:
                        arguments["departure_date"] = date.fromisoformat(arguments["departure_date"])
                    if "return_date" in arguments and arguments["return_date"]:
                        arguments["return_date"] = date.fromisoformat(arguments["return_date"])
                    
                    request = FlightCalendarRequest(**arguments)
                    response = await self.client.search_flight_calendar(request)
                    
                    # Convert to JSON-serializable format
                    calendar_data = {
                        "origin": response.origin,
                        "destination": response.destination,
                        "search_id": response.search_id,
                        "calendar_prices": [
                            {
                                "date": price.date,
                                "price": price.price,
                                "currency": price.currency
                            }
                            for price in response.calendar_prices
                        ]
                    }
                    
                    return [TextContent(type="text", text=json.dumps(calendar_data, indent=2))]
                
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
    server = FlightMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())