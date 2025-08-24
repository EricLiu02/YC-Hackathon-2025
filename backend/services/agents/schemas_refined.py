"""
Inter-agent I/O schemas for the Trip Planning Office - REFINED VERSION.

This module defines the frozen contract for inter-agent communication:
1. Raw models that exactly match current agent outputs/inputs
2. Normalized models the Manager uses to compose plans
3. Pure mapping helpers for raw → normalized conversion

Python 3.11, Pydantic v2

REFINEMENTS:
- Consistent currency handling (always "USD" for now)
- Added missing enums (FareClass, SortBy, etc.)
- Tightened optional/required fields based on actual agent usage
- Fixed date/datetime handling consistency
- Added missing fields from fixtures (vibe, near_transit_min)
"""

from typing import Literal, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import date as DateType, datetime
from enum import Enum


# ============================================================================
# COMMON ENUMS
# ============================================================================

class Currency(str, Enum):
    """Supported currencies - currently USD only."""
    USD = "USD"


class TravelClass(str, Enum):
    """Flight travel classes."""
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"


class HotelSortBy(str, Enum):
    """Hotel search sorting options."""
    PRICE = "price"
    RATING = "rating"
    DISTANCE = "distance"


class BudgetStatus(str, Enum):
    """Budget health status."""
    UNDER_BUDGET = "under_budget"
    ON_BUDGET = "on_budget"
    OVER_BUDGET = "over_budget"
    CRITICAL = "critical"


class TravelCategory(str, Enum):
    """Travel expense categories."""
    FLIGHTS = "flights"
    HOTELS = "hotels"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    ACTIVITIES = "activities"
    SHOPPING = "shopping"
    MISC = "misc"


# ============================================================================
# 1) ENVELOPE & SHARED INPUTS
# ============================================================================

class Traveler(BaseModel):
    """Traveler composition for the trip."""
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0, le=9)
    infants: int = Field(default=0, ge=0, le=9)
    profiles: list[str] = Field(default_factory=list)


class TripWindow(BaseModel):
    """Date range for the trip."""
    start: DateType
    end: DateType
    
    @field_validator('end')
    @classmethod
    def end_after_start(cls, v: DateType, info) -> DateType:
        if 'start' in info.data and v < info.data['start']:
            raise ValueError('end date must be after start date')
        return v


class Trip(BaseModel):
    """Core trip parameters."""
    origin: str = Field(..., min_length=3, max_length=3)  # Airport codes
    destinations: list[str] = Field(..., min_items=1)     # Airport/city codes
    dates: TripWindow


class Constraints(BaseModel):
    """Hard constraints that must be respected."""
    budget_usd: int = Field(..., gt=0)
    no_redeyes: bool = False
    nonstop_only: bool = False
    walk_max_km_per_day: Optional[float] = Field(default=None, ge=0)


class Preferences(BaseModel):
    """Soft preferences that guide selection."""
    hotel_vibe: Optional[str] = None
    bed_type: Optional[str] = None
    diet: Optional[str] = None
    travel_class: TravelClass = TravelClass.ECONOMY


class DeliverableRequest(BaseModel):
    """What the Manager wants from an agent."""
    kind: Literal["flight_options","lodging_options","activities","itinerary"]
    k: int = Field(default=3, ge=1, le=20)


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
    airline_code: str = Field(..., min_length=2, max_length=3)
    airline_name: str
    departure_time: datetime    # Agent returns datetime objects
    arrival_time: datetime
    duration: str              # e.g., "11h50m"
    stops: int = Field(..., ge=0, le=3)
    price: float = Field(..., gt=0)
    currency: str = Field(default=Currency.USD)
    fare_class: str = Field(default=TravelClass.ECONOMY)
    departure_airport: str = Field(..., min_length=3, max_length=3)
    arrival_airport: str = Field(..., min_length=3, max_length=3)
    aircraft_type: Optional[str] = None
    booking_class: Optional[str] = None


class FlightSearchResponseRaw(BaseModel):
    """Raw response from flight_mcp_agent search_flights."""
    flights: list[FlightOptionRaw]
    search_id: str
    total_results: int = Field(..., ge=0)


# --- Hotel Agent Raw Models ---

class HotelLocationRaw(BaseModel):
    """Raw hotel location data."""
    address: str               # Required in fixtures
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_to_center: Optional[str] = None


class HotelReviewRaw(BaseModel):
    """Raw hotel review data."""
    rating: float = Field(..., ge=0, le=5)
    total_reviews: int = Field(..., ge=0)
    source: str = Field(default="Demo")


class HotelAmenityRaw(BaseModel):
    """Raw hotel amenity data - matches fixture format."""
    name: str
    available: bool = True


class HotelRaw(BaseModel):
    """Raw hotel as returned by hotel_mcp_agent search."""
    hotel_id: str
    name: str
    city: str                  # Required in fixtures
    location: HotelLocationRaw
    star_rating: Optional[int] = Field(default=None, ge=1, le=5)
    review: Optional[HotelReviewRaw] = None
    amenities: list[HotelAmenityRaw | dict] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    rooms: list[dict] = Field(default_factory=list)
    price_range: Optional[str] = None  # e.g., "$150-$220"
    description: Optional[str] = None
    # Demo-specific fields from fixtures
    vibe: Optional[str] = None
    near_transit_min: Optional[int] = Field(default=None, ge=0)


class HotelSearchResponseRaw(BaseModel):
    """Raw response from hotel_mcp_agent search_hotels."""
    hotels: list[HotelRaw]
    search_id: str
    total_results: int = Field(..., ge=0)
    city: str
    check_in_date: DateType
    check_out_date: DateType


class PricingDetailsRaw(BaseModel):
    """Raw pricing details from hotel agent."""
    base_price: float = Field(..., gt=0)
    taxes_and_fees: float = Field(..., ge=0)
    total_price: float = Field(..., gt=0)
    currency: str = Field(default=Currency.USD)
    price_per_night: Optional[float] = Field(default=None, gt=0)
    total_nights: Optional[int] = Field(default=None, gt=0)


class CancellationPolicyRaw(BaseModel):
    """Raw cancellation policy from hotel agent."""
    is_refundable: Optional[bool] = None
    cancellation_deadline: Optional[DateType] = None
    penalty_amount: Optional[float] = Field(default=None, ge=0)
    policy_description: Optional[str] = None


class HotelPricingResponseRaw(BaseModel):
    """Raw response from hotel_mcp_agent get_hotel_pricing."""
    hotel_id: str
    hotel_name: str
    room_type: Optional[str] = None
    pricing: PricingDetailsRaw
    cancellation_policy: Optional[CancellationPolicyRaw] = None
    booking_conditions: list[str] = Field(default_factory=list)
    last_updated: Optional[str] = None


# --- Budgeteer Agent Raw Models ---

class BudgetCategoryBreakdownRaw(BaseModel):
    """Raw budget breakdown by category."""
    category: str              # Maps to TravelCategory enum values
    planned_cost: Optional[float] = Field(default=None, ge=0)
    estimated_daily_cost: Optional[float] = Field(default=None, ge=0)
    total_category_cost: Optional[float] = Field(default=None, ge=0)
    percentage_of_budget: Optional[float] = Field(default=None, ge=0, le=100)


class BudgetCalculationResponseRaw(BaseModel):
    """Raw response from budgeteer_mcp_agent calculate_trip_budget."""
    trip_id: str
    total_planned_cost: Optional[float] = Field(default=None, ge=0)
    total_estimated_cost: Optional[float] = Field(default=None, ge=0)
    total_budget: Optional[float] = Field(default=None, ge=0)
    surplus_shortfall: Optional[float] = None  # Can be negative
    budget_status: Optional[str] = None  # Maps to BudgetStatus enum
    breakdown_by_category: list[BudgetCategoryBreakdownRaw] = Field(default_factory=list)
    currency: str = Field(default=Currency.USD)
    calculation_timestamp: Optional[datetime] = None


# --- Activity Models (from fixtures) ---

class ActivityRaw(BaseModel):
    """Raw activity data from fixtures."""
    id: str
    name: str
    city: str
    theme: list[str] = Field(..., min_items=1)
    price_usd: float = Field(..., ge=0)
    duration_hr: float = Field(..., gt=0)
    image: str


# ============================================================================
# 3) NORMALIZED (MANAGER-FRIENDLY) MODELS
# ============================================================================

class FlightOption(BaseModel):
    """Normalized flight option for Manager use."""
    id: str
    carrier: str
    number: str
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    depart_iso: datetime
    arrive_iso: datetime
    stops: int = Field(..., ge=0)
    price_usd: float = Field(..., gt=0)
    redeye: bool = False
    fare_class: TravelClass = TravelClass.ECONOMY


class HotelOption(BaseModel):
    """Normalized hotel option for Manager use."""
    id: str
    name: str
    city: str                  # Now required based on fixtures
    stars: Optional[float] = Field(default=None, ge=1, le=5)
    vibe: Optional[str] = None
    near_transit_min: Optional[int] = Field(default=None, ge=0)
    price_total_usd: float = Field(..., gt=0)
    bed_type: Optional[str] = None
    images: list[str] = Field(default_factory=list)


class ActivityOption(BaseModel):
    """Normalized activity option for Manager use."""
    id: str
    name: str
    city: str
    themes: list[str] = Field(..., min_items=1)
    price_usd: float = Field(..., ge=0)
    duration_hours: float = Field(..., gt=0)
    image_url: Optional[str] = None


class TripComponent(BaseModel):
    """Normalized component for budget calculations."""
    component_id: str
    category: Literal["FLIGHTS","HOTELS","ACTIVITIES","OTHER"]
    name: str
    cost: float = Field(..., ge=0)
    currency: Literal["USD"] = Currency.USD
    date: Optional[DateType] = None
    meta: dict[str, Any] = Field(default_factory=dict)


class BudgetBreakdown(BaseModel):
    """Normalized budget breakdown."""
    flights: float = Field(default=0.0, ge=0)
    lodging: float = Field(default=0.0, ge=0)
    daily: float = Field(default=0.0, ge=0)
    contingency: float = Field(default=0.0, ge=0)
    tee: float = Field(default=0.0, ge=0)  # Total Experience Estimate


class BudgetResult(BaseModel):
    """Normalized budget calculation result."""
    totals: BudgetBreakdown
    status: BudgetStatus = BudgetStatus.ON_BUDGET
    over_under_usd: float = 0.0
    notes: list[str] = Field(default_factory=list)


class DailyPlan(BaseModel):
    """Single day's activities."""
    date: DateType
    items: list[str] = Field(..., min_items=1)
    fatigue_score: int = Field(..., ge=1, le=10)


class ItineraryCandidate(BaseModel):
    """Complete itinerary option."""
    id: str
    flight: FlightOption
    hotel: HotelOption
    activities: list[ActivityOption] = Field(default_factory=list)
    daily: list[DailyPlan] = Field(default_factory=list)
    totals_usd: dict[str, float] = Field(default_factory=dict)
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
    
    # Map fare_class string to enum
    fare_class = TravelClass.ECONOMY
    if raw.fare_class:
        try:
            fare_class = TravelClass(raw.fare_class.upper())
        except ValueError:
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
        fare_class=fare_class,
    )


def normalize_hotel_from_search(raw: HotelRaw, check_in: DateType, total_price_fallback: Optional[float] = None) -> HotelOption:
    """Map HotelRaw from search results to normalized HotelOption."""
    stars = float(raw.star_rating) if raw.star_rating is not None else None
    
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
    
    # Ensure we have a valid price
    if price <= 0:
        price = 100.0  # Default fallback
    
    return HotelOption(
        id=raw.hotel_id,
        name=raw.name,
        city=raw.city,  # Now required
        stars=stars,
        vibe=raw.vibe,
        near_transit_min=raw.near_transit_min,
        price_total_usd=float(price),
        images=raw.images or [],
    )


def normalize_hotel_from_pricing(raw: HotelPricingResponseRaw, city: str, 
                                stars: Optional[float] = None, images: Optional[list[str]] = None) -> HotelOption:
    """Map HotelPricingResponseRaw to normalized HotelOption."""
    return HotelOption(
        id=raw.hotel_id,
        name=raw.hotel_name,
        city=city,  # Now required
        stars=stars,
        price_total_usd=float(raw.pricing.total_price),
        bed_type=raw.room_type,
        images=images or [],
    )


def normalize_activity(raw: ActivityRaw) -> ActivityOption:
    """Map ActivityRaw to normalized ActivityOption."""
    return ActivityOption(
        id=raw.id,
        name=raw.name,
        city=raw.city,
        themes=raw.theme,
        price_usd=raw.price_usd,
        duration_hours=raw.duration_hr,
        image_url=raw.image if raw.image else None,
    )


def flight_to_component(f: FlightOption) -> TripComponent:
    """Convert normalized FlightOption to TripComponent for budgeting."""
    return TripComponent(
        component_id=f.id,
        category="FLIGHTS",
        name=f"{f.carrier} {f.number}",
        cost=f.price_usd,
        date=f.depart_iso.date(),
        meta={
            "stops": f.stops, 
            "redeye": f.redeye,
            "fare_class": f.fare_class.value
        }
    )


def hotel_to_component(h: HotelOption, check_in: DateType, nights: int = 1) -> TripComponent:
    """Convert normalized HotelOption to TripComponent for budgeting."""
    return TripComponent(
        component_id=h.id,
        category="HOTELS",
        name=h.name,
        cost=h.price_total_usd,
        date=check_in,
        meta={
            "stars": h.stars, 
            "near_transit_min": h.near_transit_min,
            "vibe": h.vibe,
            "nights": nights,
            "city": h.city
        }
    )


def activity_to_component(a: ActivityOption) -> TripComponent:
    """Convert normalized ActivityOption to TripComponent for budgeting."""
    return TripComponent(
        component_id=a.id,
        category="ACTIVITIES",
        name=a.name,
        cost=a.price_usd,
        date=None,  # Activities don't have fixed dates
        meta={
            "duration_hours": a.duration_hours,
            "themes": a.themes,
            "city": a.city
        }
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
    daily = buckets.get("food", 0.0) + buckets.get("transportation", 0.0) + buckets.get("activities", 0.0)
    
    # Map budget status string to enum
    status = BudgetStatus.ON_BUDGET
    if raw.budget_status:
        status_map = {
            "under_budget": BudgetStatus.UNDER_BUDGET,
            "on_budget": BudgetStatus.ON_BUDGET,
            "over_budget": BudgetStatus.OVER_BUDGET,
            "critical": BudgetStatus.CRITICAL,
            "warning": BudgetStatus.OVER_BUDGET,  # Map warning to over_budget
            "near_limit": BudgetStatus.ON_BUDGET,  # Map near_limit to on_budget
        }
        status = status_map.get(raw.budget_status.lower(), BudgetStatus.ON_BUDGET)
    
    # Calculate TEE (Total Experience Estimate)
    tee = raw.total_planned_cost or raw.total_estimated_cost or (flights + lodging + daily)
    
    return BudgetResult(
        totals=BudgetBreakdown(
            flights=flights,
            lodging=lodging,
            daily=daily,
            contingency=0.0,  # Let Manager compute if needed
            tee=float(tee)
        ),
        status=status,
        over_under_usd=float(raw.surplus_shortfall or 0.0),
        notes=[]
    )


# ============================================================================
# 5) VALIDATION HELPERS
# ============================================================================

def validate_currency(currency: str) -> str:
    """Ensure currency is valid - currently only USD supported."""
    if currency != Currency.USD:
        raise ValueError(f"Unsupported currency: {currency}. Only USD is currently supported.")
    return currency


def validate_airport_code(code: str) -> str:
    """Validate airport code format."""
    if not code or len(code) != 3 or not code.isalpha():
        raise ValueError(f"Invalid airport code: {code}. Must be 3 letters.")
    return code.upper()


# ============================================================================
# 6) SELF-CHECK BLOCK
# ============================================================================

if __name__ == "__main__":
    from pprint import pprint
    
    print("=== REFINED SCHEMAS ===")
    print("\nEnums:")
    print(f"- Currency: {[e.value for e in Currency]}")
    print(f"- TravelClass: {[e.value for e in TravelClass]}")
    print(f"- BudgetStatus: {[e.value for e in BudgetStatus]}")
    print(f"- TravelCategory: {[e.value for e in TravelCategory]}")
    
    print("\n=== RAW SCHEMAS ===")
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
    
    print("\n--- ActivityOption ---")
    pprint(ActivityOption.model_json_schema())
    
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
        city="London",
        location=HotelLocationRaw(address="123 Park Lane"),
        star_rating=4,
        review=HotelReviewRaw(rating=4.5, total_reviews=1200),
        images=["https://example.com/img1.jpg"],
        price_range="$200-$300",
        vibe="luxury business",
        near_transit_min=5
    )
    
    normalized_hotel = normalize_hotel_from_search(sample_hotel_raw, DateType(2025, 3, 15))
    print(f"\nNormalized hotel: {normalized_hotel.model_dump_json(indent=2)}")
    
    # Test activity normalization
    sample_activity_raw = ActivityRaw(
        id="ACT123",
        name="Tower of London Tour",
        city="London",
        theme=["history", "culture"],
        price_usd=35.0,
        duration_hr=2.5,
        image="https://example.com/tower.jpg"
    )
    
    normalized_activity = normalize_activity(sample_activity_raw)
    print(f"\nNormalized activity: {normalized_activity.model_dump_json(indent=2)}")
    
    # Test component conversions
    flight_component = flight_to_component(normalized_flight)
    print(f"\nFlight as component: {flight_component.model_dump_json(indent=2)}")
    
    hotel_component = hotel_to_component(normalized_hotel, DateType(2025, 3, 15), nights=3)
    print(f"\nHotel as component: {hotel_component.model_dump_json(indent=2)}")
    
    activity_component = activity_to_component(normalized_activity)
    print(f"\nActivity as component: {activity_component.model_dump_json(indent=2)}")
