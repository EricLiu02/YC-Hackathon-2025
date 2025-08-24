"""
Simple test for schemas without pytest dependency.
Run with: python simple_test.py
"""

from schemas import (
    # Raw models
    FlightOptionRaw, HotelRaw, HotelLocationRaw, HotelReviewRaw,
    HotelPricingResponseRaw, PricingDetailsRaw, BudgetCalculationResponseRaw,
    BudgetCategoryBreakdownRaw,
    # Normalized models
    FlightOption, HotelOption, TripComponent, BudgetResult,
    # Mappers
    normalize_flight, normalize_hotel_from_search, normalize_hotel_from_pricing,
    flight_to_component, hotel_to_component, budget_raw_to_normalized,
    # Envelope models
    Traveler, TripWindow, Trip, Constraints, InterAgentMessage
)
from datetime import date, datetime


def test_basic_models():
    """Test basic model creation."""
    print("Testing basic model creation...")
    
    # Test envelope models
    traveler = Traveler(adults=2, children=1)
    trip_window = TripWindow(start=date(2025, 4, 1), end=date(2025, 4, 5))
    trip = Trip(origin="SFO", destinations=["LAX"], dates=trip_window)
    constraints = Constraints(budget_usd=5000)
    
    message = InterAgentMessage(
        trace_id="test123",
        traveler=traveler,
        trip=trip,
        constraints=constraints
    )
    print("✅ Envelope models created successfully")
    
    # Test raw models
    flight_raw = FlightOptionRaw(
        flight_id="TEST001",
        airline_code="TEST",
        airline_name="Test Airlines",
        departure_time=datetime.now(),
        arrival_time=datetime.now(),
        duration="2h",
        stops=0,
        price=100.0,
        departure_airport="SFO",
        arrival_airport="LAX"
    )
    print("✅ Raw flight model created successfully")
    
    # Test normalized models
    flight_norm = FlightOption(
        id="TEST001",
        carrier="Test Airlines",
        number="001",
        origin="SFO",
        destination="LAX",
        depart_iso=datetime.now(),
        arrive_iso=datetime.now(),
        stops=0,
        price_usd=100.0
    )
    print("✅ Normalized flight model created successfully")
    
    print("\n🎉 All basic schema tests passed!")


def test_mapping_functions():
    """Test the mapping functions."""
    print("\nTesting mapping functions...")
    
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
    print(f"✅ Flight normalization: {normalized_flight.redeye=}")
    
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
    print(f"✅ Hotel normalization: {normalized_hotel.stars=}")
    
    # Test component conversion
    flight_component = flight_to_component(normalized_flight)
    print(f"✅ Flight component: {flight_component.category=}")
    
    hotel_component = hotel_to_component(normalized_hotel, date(2025, 3, 15))
    print(f"✅ Hotel component: {hotel_component.category=}")
    
    print("\n🎉 All mapping function tests passed!")


def test_budget_mapping():
    """Test budget mapping functions."""
    print("\nTesting budget mapping...")
    
    raw = BudgetCalculationResponseRaw(
        trip_id="trip123",
        total_planned_cost=2500.0,
        total_estimated_cost=3000.0,
        total_budget=3500.0,
        surplus_shortfall=500.0,
        budget_status="on_budget",
        breakdown_by_category=[
            BudgetCategoryBreakdownRaw(
                category="flights",
                planned_cost=1200.0,
                total_category_cost=1200.0
            ),
            BudgetCategoryBreakdownRaw(
                category="hotels",
                planned_cost=800.0,
                total_category_cost=800.0
            )
        ]
    )
    
    normalized = budget_raw_to_normalized(raw)
    print(f"✅ Budget normalization: {normalized.status=}, {normalized.over_under_usd=}")
    
    print("\n🎉 All budget mapping tests passed!")


if __name__ == "__main__":
    print("🚀 Running schema validation tests...\n")
    
    try:
        test_basic_models()
        test_mapping_functions()
        test_budget_mapping()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("="*50)
        print("\nThe schemas module is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
