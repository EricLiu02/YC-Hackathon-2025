"""
Inter-agent I/O schemas for the Trip Planning Office.

This module defines the frozen contract for inter-agent communication:
1. Raw models that exactly match current agent outputs/inputs
2. Normalized models the Manager uses to compose plans
3. Pure mapping helpers for raw → normalized conversion

Python 3.11, Pydantic v2
"""

from typing import Literal, Any
from pydantic import BaseModel, Field
from datetime import date, datetime


# ============================================================================
# 1) ENVELOPE & SHARED INPUTS
# ============================================================================

class Traveler(BaseModel):
    """Traveler composition for the trip."""
    adults: int = 1
    children: int = 0
    profiles: list[str] = []


class TripWindow(BaseModel):
    """Date range for the trip."""
    start: date
    end: date


class Trip(BaseModel):
    """Core trip parameters."""
    origin: str                 # e.g., "SFO"
    destinations: list[str]     # e.g., ["HND","KIX"]
    dates: TripWindow


class Constraints(BaseModel):
    """Hard constraints that must be respected."""
    budget_usd: int
    no_redeyes: bool = False
    nonstop_only: bool = False
    walk_max_km_per_day: float | None = None


class Preferences(BaseModel):
    """Soft preferences that guide selection."""
    hotel_vibe: str | None = None
    bed_type: str | None = None
    diet: str | None = None


class DeliverableRequest(BaseModel):
    """What the Manager wants from an agent."""
    kind: Literal["flight_options","lodging_options","activities","itinerary"]
    k: int = 3


class InterAgentMessage(BaseModel):
    """Request envelope shared across agents and the Manager."""
    trace_id: str
    traveler: Traveler
    trip: Trip
    constraints: Constraints
    preferences: Preferences = Field(default_factory=Preferences)
    assumptions: list[str] = Field(default_factory=list)
    deliverables: list[DeliverableRequest] = Field(default_factory=list)
    status: Literal["queued","in_progress","blocked","done","needs_approval"] = "queued"
    demo: bool = True  # Required field for demo mode


# ============================================================================
# 2) RAW (AGENT-NATIVE) MODELS - RETAIN EXISTING NAMES
# ============================================================================

# --- Flight Agent Raw Models ---

class FlightOptionRaw(BaseModel):
    """Raw flight option as returned by flight_mcp_agent."""
    flight_id: str
    airline_code: str
    airline_name: str
    departure_time: datetime    # ISO string in agent; parse to datetime
    arrival_time: datetime
    duration: str
    stops: int
    price: float
    currency: str = "USD"
    fare_class: str = "ECONOMY"
    departure_airport: str
    arrival_airport: str
    aircraft_type: str | None = None
    booking_class: str | None = None


class FlightSearchResponseRaw(BaseModel):
    """Raw response from flight_mcp_agent search_flights."""
    flights: list[FlightOptionRaw]
    search_id: str
    total_results: int


# --- Hotel Agent Raw Models ---

class HotelLocationRaw(BaseModel):
    """Raw hotel location data."""
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_to_center: str | None = None


class HotelReviewRaw(BaseModel):
    """Raw hotel review data."""
    rating: float | None = None
    total_reviews: int | None = None
    source: str | None = None


class HotelRaw(BaseModel):
    """Raw hotel as returned by hotel_mcp_agent search."""
    hotel_id: str
    name: str
    location: HotelLocationRaw
    star_rating: int | None = None
    review: HotelReviewRaw | None = None
    amenities: list[dict] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    rooms: list[dict] = Field(default_factory=list)
    price_range: str | None = None  # e.g., "$150-$220"
    description: str | None = None


class HotelSearchResponseRaw(BaseModel):
    """Raw response from hotel_mcp_agent search_hotels."""
    hotels: list[HotelRaw]
    search_id: str
    total_results: int
    city: str
    check_in_date: date
    check_out_date: date


class PricingDetailsRaw(BaseModel):
    """Raw pricing details from hotel agent."""
    base_price: float
    taxes_and_fees: float
    total_price: float
    currency: str = "USD"
    price_per_night: float | None = None
    total_nights: int | None = None


class CancellationPolicyRaw(BaseModel):
    """Raw cancellation policy from hotel agent."""
    is_refundable: bool | None = None
    cancellation_deadline: date | None = None
    penalty_amount: float | None = None
    policy_description: str | None = None


class HotelPricingResponseRaw(BaseModel):
    """Raw response from hotel_mcp_agent get_hotel_pricing."""
    hotel_id: str
    hotel_name: str
    room_type: str | None = None
    pricing: PricingDetailsRaw
    cancellation_policy: CancellationPolicyRaw | None = None
    booking_conditions: list[str] = Field(default_factory=list)
    last_updated: str | None = None


# --- Budgeteer Agent Raw Models ---

class BudgetCategoryBreakdownRaw(BaseModel):
    """Raw budget breakdown by category."""
    category: str                 # "flights", "hotels", ...
    planned_cost: float | None = None
    estimated_daily_cost: float | None = None
    total_category_cost: float | None = None
    percentage_of_budget: float | None = None


class BudgetCalculationResponseRaw(BaseModel):
    """Raw response from budgeteer_mcp_agent calculate_trip_budget."""
    trip_id: str
    total_planned_cost: float | None = None
    total_estimated_cost: float | None = None
    total_budget: float | None = None
    surplus_shortfall: float | None = None
    budget_status: str | None = None  # "under_budget", "on_budget", "over_budget", "critical"
    breakdown_by_category: list[BudgetCategoryBreakdownRaw] = Field(default_factory=list)
    currency: str = "USD"
    calculation_timestamp: datetime | None = None


# ============================================================================
# 3) NORMALIZED (MANAGER-FRIENDLY) MODELS
# ============================================================================

class FlightOption(BaseModel):
    """Normalized flight option for Manager use."""
    id: str
    carrier: str
    number: str
    origin: str
    destination: str
    depart_iso: datetime
    arrive_iso: datetime
    stops: int
    price_usd: float
    redeye: bool = False


class HotelOption(BaseModel):
    """Normalized hotel option for Manager use."""
    id: str
    name: str
    city: str | None = None
    stars: float | None = None
    vibe: str | None = None
    near_transit_min: int | None = None
    price_total_usd: float
    bed_type: str | None = None
    images: list[str] = Field(default_factory=list)


class TripComponent(BaseModel):
    """Normalized component for budget calculations."""
    component_id: str
    category: Literal["FLIGHTS","HOTELS","ACTIVITIES","OTHER"]
    name: str
    cost: float
    currency: Literal["USD"] = "USD"
    date: Any = None
    meta: dict[str, Any] = Field(default_factory=dict)


class BudgetBreakdown(BaseModel):
    """Normalized budget breakdown."""
    flights: float = 0.0
    lodging: float = 0.0
    daily: float = 0.0
    contingency: float = 0.0
    tee: float = 0.0  # Total Experience Estimate


class BudgetResult(BaseModel):
    """Normalized budget calculation result."""
    totals: BudgetBreakdown
    status: Literal["ok","warning","critical"] = "ok"
    over_under_usd: float = 0.0
    notes: list[str] = Field(default_factory=list)


class DailyPlan(BaseModel):
    """Single day's activities."""
    date: date
    items: list[str]
    fatigue_score: int = Field(ge=1, le=10)  # 1..10


class ItineraryCandidate(BaseModel):
    """Complete itinerary option."""
    id: str
    flight: FlightOption
    hotel: HotelOption
    daily: list[DailyPlan] = Field(default_factory=list)
    totals_usd: dict[str, float] = Field(default_factory=dict)  # {"flights":..,"lodging":..,"daily":..,"contingency":..,"tee":..}
    tradeoffs: list[str] = Field(default_factory=list)
    confidence: Literal["low","medium","high"] = "medium"


# ============================================================================
# 4) MAPPING HELPERS (RAW → NORMALIZED)
# ============================================================================

def normalize_flight(raw: FlightOptionRaw) -> FlightOption:
    """
    Map FlightOptionRaw (agent fields) to normalized FlightOption.
    Red eye heuristic: depart between 22:00-02:59 local OR arrive next day early morning.
    """
    # Extract carrier + number from airline_code / flight_id when parseable
    number = raw.flight_id.replace(raw.airline_code, "") if raw.flight_id.startswith(raw.airline_code) else raw.flight_id
    
    # Red eye detection
    redeye = False
    try:
        dep_hour = raw.departure_time.hour
        arr_day_diff = (raw.arrival_time.date() - raw.departure_time.date()).days
        redeye = (22 <= dep_hour or dep_hour <= 2) or (arr_day_diff >= 1 and raw.arrival_time.hour < 8)
    except Exception:
        pass
    
    return FlightOption(
        id=raw.flight_id,
        carrier=raw.airline_name or raw.airline_code,
        number=number,
        origin=raw.departure_airport,
        destination=raw.arrival_airport,
        depart_iso=raw.departure_time,
        arrive_iso=raw.arrival_time,
        stops=raw.stops,
        price_usd=float(raw.price),
        redeye=redeye,
    )


def normalize_hotel_from_search(raw: HotelRaw, check_in: date, total_price_fallback: float | None = None) -> HotelOption:
    """Map HotelRaw from search results to normalized HotelOption."""
    stars = float(raw.star_rating) if raw.star_rating is not None else None
    
    # Extract city from raw data if available
    city = None
    if hasattr(raw, 'city'):
        city = raw.city
    
    # Parse price from price_range if no fallback provided
    price = total_price_fallback or 0.0
    if not total_price_fallback and raw.price_range:
        # Try to extract from "$150-$220" format
        try:
            price_parts = raw.price_range.replace('$', '').split('-')
            if price_parts:
                price = float(price_parts[0])
        except:
            pass
    
    return HotelOption(
        id=raw.hotel_id,
        name=raw.name,
        city=city,
        stars=stars,
        vibe=None,
        near_transit_min=None,  # Unknown from raw search; can be filled by ranking logic later
        price_total_usd=float(price),
        images=raw.images or [],
    )


def normalize_hotel_from_pricing(raw: HotelPricingResponseRaw, city: str | None = None, 
                                stars: float | None = None, images: list[str] | None = None) -> HotelOption:
    """Map HotelPricingResponseRaw to normalized HotelOption."""
    return HotelOption(
        id=raw.hotel_id,
        name=raw.hotel_name,
        city=city,
        stars=stars,
        price_total_usd=float(raw.pricing.total_price),
        bed_type=raw.room_type,
        images=images or [],
    )


def flight_to_component(f: FlightOption) -> TripComponent:
    """Convert normalized FlightOption to TripComponent for budgeting."""
    return TripComponent(
        component_id=f.id,
        category="FLIGHTS",
        name=f"{f.carrier} {f.number}",
        cost=f.price_usd,
        date=f.depart_iso.date(),
        meta={"stops": f.stops, "redeye": f.redeye}
    )


def hotel_to_component(h: HotelOption, check_in: date) -> TripComponent:
    """Convert normalized HotelOption to TripComponent for budgeting."""
    return TripComponent(
        component_id=h.id,
        category="HOTELS",
        name=h.name,
        cost=h.price_total_usd,
        date=check_in,
        meta={"stars": h.stars, "near_transit_min": h.near_transit_min}
    )


def budget_raw_to_normalized(raw: BudgetCalculationResponseRaw) -> BudgetResult:
    """Translate Budgeteer's raw response into our normalized BudgetResult."""
    # Try to extract categories; default to zeros
    buckets = {}
    for b in (raw.breakdown_by_category or []):
        cat = (b.category or "").lower()
        # Use total_category_cost if available, otherwise try planned_cost or estimated_daily_cost
        value = b.total_category_cost or b.planned_cost or b.estimated_daily_cost or 0.0
        buckets[cat] = float(value)
    
    flights = buckets.get("flights", 0.0)
    lodging = buckets.get("hotels", buckets.get("lodging", buckets.get("accommodation", 0.0)))
    
    # Map budget status
    status = "ok"
    if raw.budget_status:
        if raw.budget_status.lower() in ["warning", "near_limit"]:
            status = "warning"
        elif raw.budget_status.lower() in ["critical", "over_budget"]:
            status = "critical"
        elif raw.budget_status.lower() in ["ok", "on_budget", "under_budget"]:
            status = "ok"
    
    # Calculate TEE (Total Experience Estimate)
    tee = raw.total_planned_cost or raw.total_estimated_cost or (flights + lodging)
    
    return BudgetResult(
        totals=BudgetBreakdown(
            flights=flights,
            lodging=lodging,
            daily=0.0,  # Daily + contingency may not exist in raw; let Manager compute
            contingency=0.0,
            tee=float(tee)
        ),
        status=status,
        over_under_usd=float(raw.surplus_shortfall or 0.0),
        notes=[]
    )


# ============================================================================
# 5) SELF-CHECK BLOCK
# ============================================================================

if __name__ == "__main__":
    from pprint import pprint
    
    print("=== RAW SCHEMAS ===")
    print("\n--- FlightSearchResponseRaw ---")
    pprint(FlightSearchResponseRaw.model_json_schema(), depth=3)
    
    print("\n--- HotelSearchResponseRaw ---")
    pprint(HotelSearchResponseRaw.model_json_schema(), depth=3)
    
    print("\n--- BudgetCalculationResponseRaw ---")
    pprint(BudgetCalculationResponseRaw.model_json_schema(), depth=3)
    
    print("\n=== NORMALIZED SCHEMAS ===")
    print("\n--- FlightOption ---")
    pprint(FlightOption.model_json_schema())
    
    print("\n--- HotelOption ---")
    pprint(HotelOption.model_json_schema())
    
    print("\n--- ItineraryCandidate ---")
    pprint(ItineraryCandidate.model_json_schema(), depth=3)
    
    # Test mapping with sample data
    print("\n=== MAPPING TESTS ===")
    
    # Test flight normalization
    sample_flight_raw = FlightOptionRaw(
        flight_id="AA100",
        airline_code="AA",
        airline_name="American Airlines",
        departure_time=datetime(2025, 3, 15, 23, 30),  # Red eye
        arrival_time=datetime(2025, 3, 16, 7, 30),
        duration="8h00m",
        stops=0,
        price=850.0,
        currency="USD",
        fare_class="ECONOMY",
        departure_airport="JFK",
        arrival_airport="LHR"
    )
    
    normalized_flight = normalize_flight(sample_flight_raw)
    print(f"\nNormalized flight: {normalized_flight.model_dump_json(indent=2)}")
    print(f"Red eye detected: {normalized_flight.redeye}")
    
    # Test hotel normalization
    sample_hotel_raw = HotelRaw(
        hotel_id="H123",
        name="Hilton London",
        location=HotelLocationRaw(address="123 Park Lane"),
        star_rating=4,
        review=HotelReviewRaw(rating=4.5, total_reviews=1200),
        images=["https://example.com/img1.jpg"],
        price_range="$200-$300"
    )
    
    normalized_hotel = normalize_hotel_from_search(sample_hotel_raw, date(2025, 3, 15))
    print(f"\nNormalized hotel: {normalized_hotel.model_dump_json(indent=2)}")
    
    # Test component conversion
    flight_component = flight_to_component(normalized_flight)
    print(f"\nFlight as component: {flight_component.model_dump_json(indent=2)}")
    
    hotel_component = hotel_to_component(normalized_hotel, date(2025, 3, 15))
    print(f"\nHotel as component: {hotel_component.model_dump_json(indent=2)}")
