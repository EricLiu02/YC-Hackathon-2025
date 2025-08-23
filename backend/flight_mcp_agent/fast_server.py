import asyncio
import sys
from datetime import date
from typing import Any, List

from fastmcp import FastMCP

from .models import (
    FlightSearchRequest,
    FlightSearchResponse,
    FlightPricingRequest,
    FlightPricingResponse,
    FlightCalendarRequest,
    FlightCalendarResponse,
)
from .searchapi_client import SearchAPIFlightClient


app = FastMCP(name="flight-mcp-agent")


def _ensure_dates(arguments: dict[str, Any]) -> dict[str, Any]:
    updated = dict(arguments)
    if "departure_date" in updated and isinstance(updated["departure_date"], str):
        updated["departure_date"] = date.fromisoformat(updated["departure_date"])
    if "return_date" in updated and updated["return_date"] and isinstance(updated["return_date"], str):
        updated["return_date"] = date.fromisoformat(updated["return_date"])
    return updated


def _serialize_flight_search_response(response: FlightSearchResponse) -> dict:
    flights_data = []
    for flight in response.flights:
        flight_dict = flight.model_dump()
        # Convert datetime values to ISO strings for JSON-safe content
        flight_dict["departure_time"] = flight.departure_time.isoformat()
        flight_dict["arrival_time"] = flight.arrival_time.isoformat()
        flights_data.append(flight_dict)
    return {
        "flights": flights_data,
        "search_id": response.search_id,
        "total_results": response.total_results,
    }


@app.tool()
async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    travel_class: str = "ECONOMY",
    max_results: int = 10,
) -> dict:
    """Search for flights using Google Flights API via SearchAPI with automatic fallback to Travel Explore API.
    
    This tool searches for flights between two airports and returns detailed flight information including
    prices, airlines, departure/arrival times, and stops. If no specific flights are found for the 
    requested route, it automatically falls back to the Travel Explore API to suggest alternative destinations.
    
    Args:
        origin: Origin airport IATA code (3 letters, e.g., 'SFO', 'JFK', 'LAX')
        destination: Destination airport IATA code (3 letters, e.g., 'HNL', 'GRU', 'CDG') 
        departure_date: Departure date in YYYY-MM-DD format (e.g., '2025-08-23')
        return_date: Return date for round-trip (YYYY-MM-DD format, optional)
        adults: Number of adult passengers (1-9, default: 1)
        children: Number of child passengers (0-8, default: 0)  
        infants: Number of infant passengers (0-4, default: 0)
        travel_class: Cabin class ('ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST')
        max_results: Maximum flights to return (1-50, default: 10)
    
    Returns:
        Dictionary with flight search results including flights list, search_id, and total_results
    """
    args = _ensure_dates(
        {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "adults": adults,
            "children": children,
            "infants": infants,
            "travel_class": travel_class,
            "max_results": max_results,
        }
    )
    request = FlightSearchRequest(**args)
    client = SearchAPIFlightClient()
    response = await client.search_flights(request)
    return _serialize_flight_search_response(response)


@app.tool()
async def get_flight_pricing(flight_ids: List[str]) -> List[dict]:
    """Get detailed pricing breakdown for specific flights.
    
    NOTE: This feature is currently not implemented for SearchAPI. The search_flights tool
    already includes comprehensive pricing information in its results. This tool will return 
    an error message indicating that pricing data is available in the flight search results.
    
    Args:
        flight_ids: List of flight IDs from previous search results
        
    Returns:
        Error message indicating to use search_flights for pricing information
    """
    client = SearchAPIFlightClient()
    request = FlightPricingRequest(flight_ids=flight_ids)
    responses = await client.get_flight_pricing(request)
    pricing_data: List[dict] = []
    for pricing in responses:
        pricing_dict = pricing.model_dump()
        if pricing.last_ticketing_date:
            pricing_dict["last_ticketing_date"] = pricing.last_ticketing_date.isoformat()
        pricing_data.append(pricing_dict)
    return pricing_data


@app.tool()
async def search_flight_calendar(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    travel_class: str = "ECONOMY",
) -> dict:
    """Search for flight prices across different dates using Google Flights Calendar API.
    
    This tool shows price trends over time, helping users find the cheapest dates to fly around 
    their preferred departure date. Perfect for flexible travelers who want to see price variations
    across multiple days or weeks to get the best deals.
    
    Args:
        origin: Origin airport IATA code (3 letters, e.g., 'SFO', 'JFK', 'LAX')
        destination: Destination airport IATA code (3 letters, e.g., 'HNL', 'GRU', 'CDG') 
        departure_date: Reference departure date in YYYY-MM-DD format (calendar shows prices around this date)
        return_date: Return date for round-trip calendar (YYYY-MM-DD format, optional)
        adults: Number of adult passengers (1-9, default: 1)
        children: Number of child passengers (0-8, default: 0)  
        infants: Number of infant passengers (0-4, default: 0)
        travel_class: Cabin class ('ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST')
    
    Returns:
        Dictionary with calendar pricing data including origin, destination, and price calendar
    """
    args = _ensure_dates(
        {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "adults": adults,
            "children": children,
            "infants": infants,
            "travel_class": travel_class,
        }
    )
    request = FlightCalendarRequest(**args)
    client = SearchAPIFlightClient()
    response = await client.search_flight_calendar(request)
    
    return {
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


def main():
    # fastmcp manages its own event loop
    app.run()


if __name__ == "__main__":
    main()


