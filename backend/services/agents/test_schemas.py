"""
Unit tests for schema mappings.
Run with: python -m pytest test_schemas.py
"""

import pytest
from datetime import date, datetime
from schemas import (
    # Raw models
    FlightOptionRaw, HotelRaw, HotelLocationRaw, HotelReviewRaw,
    HotelPricingResponseRaw, PricingDetailsRaw, BudgetCalculationResponseRaw,
    BudgetCategoryBreakdownRaw,
    # Normalized models
    FlightOption, HotelOption, TripComponent, BudgetResult,
    # Mappers
    normalize_flight, normalize_hotel_from_search, normalize_hotel_from_pricing,
    flight_to_component, hotel_to_component, budget_raw_to_normalized
)


class TestFlightNormalization:
    """Test flight raw to normalized mapping."""
    
    def test_basic_flight_normalization(self):
        """Test basic flight mapping."""
        raw = FlightOptionRaw(
            flight_id="UA456",
            airline_code="UA",
            airline_name="United Airlines",
            departure_time=datetime(2025, 4, 1, 14, 30),
            arrival_time=datetime(2025, 4, 1, 18, 45),
            duration="4h15m",
            stops=0,
            price=450.50,
            currency="USD",
            fare_class="ECONOMY",
            departure_airport="SFO",
            arrival_airport="LAX"
        )
        
        normalized = normalize_flight(raw)
        
        assert normalized.id == "UA456"
        assert normalized.carrier == "United Airlines"
        assert normalized.number == "456"
        assert normalized.origin == "SFO"
        assert normalized.destination == "LAX"
        assert normalized.stops == 0
        assert normalized.price_usd == 450.50
        assert normalized.redeye is False
    
    def test_redeye_detection_late_departure(self):
        """Test red eye detection for late night departure."""
        raw = FlightOptionRaw(
            flight_id="AA100",
            airline_code="AA",
            airline_name="American Airlines",
            departure_time=datetime(2025, 4, 1, 23, 30),  # 11:30 PM
            arrival_time=datetime(2025, 4, 2, 7, 30),
            duration="8h00m",
            stops=0,
            price=850.0,
            currency="USD",
            fare_class="ECONOMY",
            departure_airport="JFK",
            arrival_airport="LHR"
        )
        
        normalized = normalize_flight(raw)
        assert normalized.redeye is True
    
    def test_redeye_detection_early_morning(self):
        """Test red eye detection for early morning departure."""
        raw = FlightOptionRaw(
            flight_id="DL200",
            airline_code="DL",
            airline_name="Delta",
            departure_time=datetime(2025, 4, 1, 1, 30),  # 1:30 AM
            arrival_time=datetime(2025, 4, 1, 5, 30),
            duration="4h00m",
            stops=0,
            price=350.0,
            currency="USD",
            fare_class="ECONOMY",
            departure_airport="LAX",
            arrival_airport="JFK"
        )
        
        normalized = normalize_flight(raw)
        assert normalized.redeye is True


class TestHotelNormalization:
    """Test hotel raw to normalized mapping."""
    
    def test_hotel_from_search(self):
        """Test hotel normalization from search results."""
        raw = HotelRaw(
            hotel_id="H456",
            name="Marriott Downtown",
            location=HotelLocationRaw(
                address="123 Main St",
                latitude=40.7128,
                longitude=-74.0060
            ),
            star_rating=4,
            review=HotelReviewRaw(rating=4.3, total_reviews=850),
            images=["img1.jpg", "img2.jpg"],
            price_range="$180-$250"
        )
        
        normalized = normalize_hotel_from_search(raw, date(2025, 4, 1))
        
        assert normalized.id == "H456"
        assert normalized.name == "Marriott Downtown"
        assert normalized.stars == 4.0
        assert normalized.price_total_usd == 180.0  # Takes lower bound
        assert len(normalized.images) == 2
    
    def test_hotel_from_pricing(self):
        """Test hotel normalization from pricing response."""
        raw = HotelPricingResponseRaw(
            hotel_id="H456",
            hotel_name="Marriott Downtown",
            room_type="King Suite",
            pricing=PricingDetailsRaw(
                base_price=800.0,
                taxes_and_fees=160.0,
                total_price=960.0,
                currency="USD",
                price_per_night=240.0,
                total_nights=4
            )
        )
        
        normalized = normalize_hotel_from_pricing(
            raw, 
            city="New York",
            stars=4.0,
            images=["img1.jpg"]
        )
        
        assert normalized.id == "H456"
        assert normalized.name == "Marriott Downtown"
        assert normalized.city == "New York"
        assert normalized.stars == 4.0
        assert normalized.price_total_usd == 960.0
        assert normalized.bed_type == "King Suite"


class TestComponentConversion:
    """Test normalized to component mapping."""
    
    def test_flight_to_component(self):
        """Test flight to component conversion."""
        flight = FlightOption(
            id="AA100",
            carrier="American Airlines",
            number="100",
            origin="JFK",
            destination="LAX",
            depart_iso=datetime(2025, 4, 1, 10, 0),
            arrive_iso=datetime(2025, 4, 1, 13, 0),
            stops=0,
            price_usd=450.0,
            redeye=False
        )
        
        component = flight_to_component(flight)
        
        assert component.component_id == "AA100"
        assert component.category == "FLIGHTS"
        assert component.name == "American Airlines 100"
        assert component.cost == 450.0
        assert component.date == date(2025, 4, 1)
        assert component.meta["stops"] == 0
        assert component.meta["redeye"] is False
    
    def test_hotel_to_component(self):
        """Test hotel to component conversion."""
        hotel = HotelOption(
            id="H789",
            name="Hilton Garden Inn",
            city="Boston",
            stars=3.5,
            price_total_usd=600.0,
            bed_type="Queen"
        )
        
        check_in = date(2025, 4, 1)
        component = hotel_to_component(hotel, check_in)
        
        assert component.component_id == "H789"
        assert component.category == "HOTELS"
        assert component.name == "Hilton Garden Inn"
        assert component.cost == 600.0
        assert component.date == check_in
        assert component.meta["stars"] == 3.5


class TestBudgetNormalization:
    """Test budget raw to normalized mapping."""
    
    def test_budget_mapping(self):
        """Test budget response normalization."""
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
        
        assert normalized.status == "ok"
        assert normalized.over_under_usd == 500.0
        assert normalized.totals.flights == 1200.0
        assert normalized.totals.lodging == 800.0
        assert normalized.totals.tee == 2500.0  # Uses total_planned_cost
    
    def test_budget_status_mapping(self):
        """Test budget status normalization."""
        test_cases = [
            ("under_budget", "ok"),
            ("on_budget", "ok"),
            ("warning", "warning"),
            ("near_limit", "warning"),
            ("over_budget", "critical"),
            ("critical", "critical"),
        ]
        
        for raw_status, expected_status in test_cases:
            raw = BudgetCalculationResponseRaw(
                trip_id="test",
                budget_status=raw_status
            )
            normalized = budget_raw_to_normalized(raw)
            assert normalized.status == expected_status


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running schema tests...")
    
    # Test basic model creation
    try:
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
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        raise
