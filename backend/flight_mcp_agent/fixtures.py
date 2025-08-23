from datetime import datetime, date
from .models import FlightOption, FlightSearchResponse, FlightPricingResponse, PriceBreakdown


DEMO_FLIGHTS = [
    FlightOption(
        flight_id="AA123_2025_01_15",
        airline_code="AA",
        airline_name="American Airlines",
        departure_time=datetime(2025, 1, 15, 8, 30),
        arrival_time=datetime(2025, 1, 15, 11, 45),
        duration="3h 15m",
        stops=0,
        price=299.00,
        currency="USD",
        fare_class="Main Cabin",
        departure_airport="JFK",
        arrival_airport="LAX",
        aircraft_type="Boeing 737",
        booking_class="Y"
    ),
    FlightOption(
        flight_id="DL456_2025_01_15",
        airline_code="DL", 
        airline_name="Delta Air Lines",
        departure_time=datetime(2025, 1, 15, 10, 15),
        arrival_time=datetime(2025, 1, 15, 13, 30),
        duration="3h 15m",
        stops=0,
        price=325.00,
        currency="USD",
        fare_class="Main Cabin",
        departure_airport="JFK",
        arrival_airport="LAX",
        aircraft_type="Airbus A320",
        booking_class="Y"
    ),
    FlightOption(
        flight_id="UA789_2025_01_15",
        airline_code="UA",
        airline_name="United Airlines", 
        departure_time=datetime(2025, 1, 15, 14, 45),
        arrival_time=datetime(2025, 1, 15, 19, 15),
        duration="4h 30m",
        stops=1,
        price=275.00,
        currency="USD",
        fare_class="Economy",
        departure_airport="JFK",
        arrival_airport="LAX",
        aircraft_type="Boeing 757",
        booking_class="Y"
    )
]


def get_demo_flight_search_response(origin: str, destination: str) -> FlightSearchResponse:
    return FlightSearchResponse(
        flights=DEMO_FLIGHTS,
        search_id=f"demo_search_{origin}_{destination}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        total_results=len(DEMO_FLIGHTS)
    )


def get_demo_flight_pricing(flight_id: str) -> FlightPricingResponse:
    base_prices = {
        "AA123_2025_01_15": 249.00,
        "DL456_2025_01_15": 275.00, 
        "UA789_2025_01_15": 225.00
    }
    
    base_fare = base_prices.get(flight_id, 250.00)
    taxes = base_fare * 0.15
    fees = 25.00
    total = base_fare + taxes + fees
    
    return FlightPricingResponse(
        flight_id=flight_id,
        price_breakdown=PriceBreakdown(
            base_fare=base_fare,
            taxes=taxes,
            fees=fees,
            total=total,
            currency="USD"
        ),
        last_ticketing_date=date(2025, 1, 10)
    )