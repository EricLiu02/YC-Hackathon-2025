from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date


class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    adults: int = 1
    children: int = 0
    infants: int = 0
    travel_class: Optional[str] = "ECONOMY"
    max_results: int = 10


class FlightOption(BaseModel):
    flight_id: str
    airline_code: str
    airline_name: str
    departure_time: datetime
    arrival_time: datetime
    duration: str
    stops: int
    price: float
    currency: str
    fare_class: str
    departure_airport: str
    arrival_airport: str
    aircraft_type: Optional[str] = None
    booking_class: Optional[str] = None


class FlightSearchResponse(BaseModel):
    flights: List[FlightOption]
    search_id: str
    total_results: int


class FlightPricingRequest(BaseModel):
    flight_ids: List[str]


class PriceBreakdown(BaseModel):
    base_fare: float
    taxes: float
    fees: float
    total: float
    currency: str


class FlightPricingResponse(BaseModel):
    flight_id: str
    price_breakdown: PriceBreakdown
    fare_rules: Optional[Dict[str, Any]] = None
    last_ticketing_date: Optional[date] = None


class FlightCalendarRequest(BaseModel):
    origin: str
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    adults: int = 1
    children: int = 0
    infants: int = 0
    travel_class: str = "ECONOMY"


class CalendarPrice(BaseModel):
    date: str
    price: float
    currency: str = "USD"


class FlightCalendarResponse(BaseModel):
    origin: str
    destination: str
    calendar_prices: List[CalendarPrice]
    search_id: str