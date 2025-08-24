# Inter-Agent Schemas

This module provides the frozen contract for inter-agent communication in the Trip Planning Office.

## Overview

The schemas module defines two layers of data models:

1. **Raw Models**: Exact replicas of current agent outputs (preserving all field names)
2. **Normalized Models**: Clean, manager-friendly models for orchestration
3. **Mapping Helpers**: Pure functions to convert raw → normalized

## Structure

```
services/agents/
├── schemas.py          # Main schema definitions and mappers
├── test_schemas.py     # Unit tests for validation
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## Usage

### For MCP Agents (Raw Models)

Import the raw models that match your current agent outputs:

```python
from services.agents.schemas import (
    FlightOptionRaw,
    HotelRaw,
    BudgetCalculationResponseRaw
)

# Use these models to parse agent responses
flight_data = FlightOptionRaw.model_validate(agent_response)
```

### For Manager/Orchestrator (Normalized Models)

Import the normalized models and mappers:

```python
from services.agents.schemas import (
    FlightOption,
    HotelOption,
    normalize_flight,
    normalize_hotel_from_search
)

# Convert raw agent responses to normalized format
normalized_flight = normalize_flight(raw_flight_data)
normalized_hotel = normalize_hotel_from_search(raw_hotel_data, check_in_date)
```

## Key Models

### Envelope & Shared Inputs

- `InterAgentMessage`: Common request envelope for all agents
- `Traveler`: Traveler composition (adults, children, profiles)
- `Trip`: Core trip parameters (origin, destinations, dates)
- `Constraints`: Hard constraints (budget, no redeyes, etc.)
- `Preferences`: Soft preferences (hotel vibe, bed type, etc.)

### Raw Models (Agent-Native)

- `FlightOptionRaw`: Flight data from flight_mcp_agent
- `HotelRaw`: Hotel data from hotel_mcp_agent  
- `BudgetCalculationResponseRaw`: Budget data from budgeteer_mcp_agent

### Normalized Models (Manager-Friendly)

- `FlightOption`: Clean flight representation
- `HotelOption`: Clean hotel representation
- `TripComponent`: Budget component for calculations
- `BudgetResult`: Normalized budget calculation
- `ItineraryCandidate`: Complete itinerary option

## Mapping Functions

### Flight Normalization

```python
def normalize_flight(raw: FlightOptionRaw) -> FlightOption:
    """Convert raw flight data to normalized format with red-eye detection."""
```

### Hotel Normalization

```python
def normalize_hotel_from_search(raw: HotelRaw, check_in: date) -> HotelOption:
    """Convert hotel search results to normalized format."""

def normalize_hotel_from_pricing(raw: HotelPricingResponseRaw, ...) -> HotelOption:
    """Convert hotel pricing response to normalized format."""
```

### Component Conversion

```python
def flight_to_component(f: FlightOption) -> TripComponent:
    """Convert flight to budget component."""

def hotel_to_component(h: HotelOption, check_in: date) -> TripComponent:
    """Convert hotel to budget component."""
```

### Budget Normalization

```python
def budget_raw_to_normalized(raw: BudgetCalculationResponseRaw) -> BudgetResult:
    """Convert budgeteer response to normalized format."""
```

## Testing

Run the self-check block:

```bash
cd backend/services/agents
python schemas.py
```

Run unit tests:

```bash
cd backend/services/agents
python -m pytest test_schemas.py
```

Or run basic validation:

```bash
cd backend/services/agents
python test_schemas.py
```

## Schema Validation

The `__main__` block in `schemas.py` provides:

1. **Schema Dumps**: JSON schemas for all models
2. **Mapping Tests**: Sample data conversion examples
3. **Validation**: Basic model creation tests

## Integration

This schema module serves as the contract between:

- **Flight Agent** → Manager
- **Hotel Agent** → Manager  
- **Budgeteer Agent** → Manager
- **Manager** → Frontend/Orchestrator

The Manager imports only normalized models and mappers, while MCP clients continue using raw models to parse agent responses.

## Dependencies

- Python 3.11+
- Pydantic v2+
- python-dateutil

## Notes

- All existing field names are preserved in raw models
- Normalized models provide clean, stable interfaces
- Mappers handle edge cases and data transformations
- Demo mode is supported via `demo: bool` field
