# Schema Refinements Summary

This document outlines the key refinements made to the inter-agent schemas for consistency with flight/hotel/budget agents and fixtures.

## Key Improvements

### 1. **Currency Handling**
- Added `Currency` enum (currently only USD supported)
- Normalized all currency fields to use `Currency.USD` as default
- Added `validate_currency()` helper for future multi-currency support
- Ensured consistency across all agents

### 2. **Added Missing Enums**
- `TravelClass`: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
- `HotelSortBy`: price, rating, distance  
- `BudgetStatus`: under_budget, on_budget, over_budget, critical
- `TravelCategory`: flights, hotels, transportation, food, activities, shopping, misc

### 3. **Tightened Optional/Required Fields**

#### Flight Agent
- Made `airline_code` length 2-3 chars
- Made airport codes exactly 3 chars
- Added validation for `stops` (0-3)
- Added validation for `price` (>0)

#### Hotel Agent  
- Made `city` required (based on fixtures)
- Made `address` required in location
- Added `HotelAmenityRaw` model to match fixture format
- Added demo fields: `vibe`, `near_transit_min`
- Added validation for star ratings (1-5)

#### Budget Agent
- Added validation for percentage_of_budget (0-100)
- Made surplus_shortfall nullable (can be negative)
- Improved category mapping with fallbacks

### 4. **Date/DateTime Consistency**
- Used `DateType` alias to avoid conflicts with Python's `date`
- Consistent datetime handling for flight times
- Added date validation (end after start)
- Fixed Optional date field handling

### 5. **New Models Added**
- `ActivityRaw`: For activity fixtures
- `ActivityOption`: Normalized activity model
- `activity_to_component()`: Activity to budget component mapper
- Added activities to `ItineraryCandidate`

### 6. **Enhanced Validation**
- Field validators for date ranges
- Min/max constraints on numeric fields
- Required field enforcement
- Airport code format validation

### 7. **Improved Mapping Functions**
- Better fare class enum mapping
- Robust price extraction from price ranges
- Enhanced red-eye detection logic
- Added nights parameter to hotel component
- Status string to enum mapping with fallbacks

### 8. **Fixture Compatibility**
- Added fields from fixtures (vibe, near_transit_min)
- Support for amenity dict format
- City field now required to match fixtures
- Image URL handling for activities

## Usage Examples

### Currency Validation
```python
# All currency fields default to USD
flight = FlightOptionRaw(currency="USD")  # Valid
validate_currency("EUR")  # Raises ValueError
```

### Enum Usage
```python
# Travel class with validation
preferences = Preferences(travel_class=TravelClass.BUSINESS)

# Budget status mapping
status = BudgetStatus.OVER_BUDGET
```

### Required Fields
```python
# City is now required for hotels
hotel = HotelOption(
    id="H1",
    name="Test Hotel", 
    city="Tokyo",  # Required!
    price_total_usd=100.0
)
```

### Activity Support
```python
# New activity models
activity = ActivityOption(
    id="ACT1",
    name="Temple Tour",
    city="Kyoto",
    themes=["culture", "history"],
    price_usd=50.0,
    duration_hours=3.0
)
```

## Migration Notes

1. **Currency**: All agents should use "USD" for now
2. **Hotels**: Must include `city` field in all responses
3. **Activities**: Use new `ActivityRaw` model for fixtures
4. **Dates**: Import as `DateType` to avoid conflicts
5. **Enums**: Use enum values instead of strings where applicable

## Testing

Run the refined schemas to see all improvements:
```bash
cd backend
python services/agents/schemas_refined.py
```

The output shows:
- All enums and their values
- Complete schema definitions
- Successful mapping tests
- Component conversions with metadata
