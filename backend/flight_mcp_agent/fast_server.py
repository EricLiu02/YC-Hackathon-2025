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
)
from .amadeus_client import AmadeusFlightClient
from .fixtures import get_demo_flight_search_response


app = FastMCP(name="flight-mcp-agent")
DEFAULT_DEMO: bool = False


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
    demo: bool | None = None,
) -> dict:
    """Search for flights based on trip constraints."""
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
    use_demo = demo if demo is not None else DEFAULT_DEMO
    client = AmadeusFlightClient(use_demo_data=use_demo)
    response = await client.search_flights(request)
    return _serialize_flight_search_response(response)


@app.tool()
async def get_flight_pricing(flight_ids: List[str], demo: bool | None = None) -> List[dict]:
    """Get detailed pricing information for specific flight IDs."""
    use_demo = demo if demo is not None else DEFAULT_DEMO
    client = AmadeusFlightClient(use_demo_data=use_demo)
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
async def get_cached_flights(origin: str, destination: str) -> dict:
    """Get cached/demo flight data for testing purposes."""
    response = get_demo_flight_search_response(origin, destination)
    return _serialize_flight_search_response(response)


def main():
    global DEFAULT_DEMO
    if "--demo" in sys.argv:
        DEFAULT_DEMO = True
    # fastmcp manages its own event loop
    app.run()


if __name__ == "__main__":
    main()


