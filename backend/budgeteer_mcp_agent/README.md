# Budgeteer MCP Agent Service

A Model Context Protocol (MCP) compliant service for travel budgeting and cost estimation logic. This service provides intelligent budget calculations and cost optimization suggestions for trip planning.

## Features

- **Comprehensive Budget Calculation**: Calculate total trip costs including planned expenses and daily spending estimates
- **Budget Optimization**: Suggest lower-cost alternatives with risk analysis and constraint validation
- **Category-based Breakdown**: Detailed cost analysis by travel category (flights, hotels, food, activities, etc.)
- **Fast & Stateless**: Designed for quick responses with no external API dependencies
- **Demo Mode**: Built-in synthetic data for testing and development

## Tools

### 1. `calculate_trip_budget`

Calculates comprehensive trip budget including planned costs and daily spending estimates.

**Inputs:**
- `trip_plan`: Complete trip plan with components, dates, budget, and traveler count
- `daily_spend_estimates`: Daily spending estimates per category per person
- `additional_costs`: Optional additional costs not in main plan
- `demo`: Whether to use demo data (defaults to global setting)

**Outputs:**
- Total planned cost vs. estimated cost
- Budget breakdown by category
- Surplus/shortfall status
- Budget health indicators

### 2. `suggest_budget_swaps`

Suggests budget-friendly alternatives for trip components with cost savings and risk analysis.

**Inputs:**
- `trip_plan`: Current trip plan to analyze
- `target_categories`: Specific categories to focus on (optional)
- `max_risk_level`: Maximum acceptable risk level (low/medium/high)
- `min_savings_threshold`: Minimum savings required to suggest alternatives
- `demo`: Whether to use demo data

**Outputs:**
- List of alternative components with cost savings
- Risk level assessment
- Constraint violation warnings
- Recommendation scores

### 3. `get_demo_trip_plan`

Returns a sample trip plan for testing and development.

### 4. `get_demo_daily_spend_estimates`

Returns sample daily spending estimates by travel category.

## Installation

```bash
cd backend/budgeteer_mcp_agent
pip install -e .
```

## Usage

### Running the Service

```bash
# Normal mode
python -m budgeteer_mcp_agent

# Demo mode (uses synthetic data)
python -m budgeteer_mcp_agent --demo
```

### Testing

```bash
# Run the test suite
python -m budgeteer_mcp_agent.test_fast_server
```

## Data Models

### Travel Categories
- `flights`: Air travel costs
- `hotels`: Accommodation expenses
- `transportation`: Local transport (taxis, public transit, etc.)
- `food`: Dining and meal costs
- `activities`: Entertainment and sightseeing
- `shopping`: Retail purchases
- `misc`: Other expenses

### Budget Status
- `under_budget`: Significant surplus (>$500)
- `on_budget`: Within budget (<$500 surplus)
- `over_budget`: Exceeds budget (<$500 overage)
- `critical`: Significantly over budget (>$500 overage)

## Example Usage

### Basic Budget Calculation

```python
from budgeteer_mcp_agent.fast_server import calculate_trip_budget

# Create a trip plan
trip_plan = {
    "trip_id": "london_2025",
    "destination": "London, UK",
    "start_date": "2025-03-15",
    "end_date": "2025-03-22",
    "num_travelers": 2,
    "components": [...],  # Flight, hotel, activity components
    "total_budget": 4000.00
}

# Daily spending estimates
daily_estimates = [
    {"category": "food", "per_person_per_day": 75.00},
    {"category": "shopping", "per_person_per_day": 50.00}
]

# Calculate budget
result = await calculate_trip_budget(
    trip_plan=trip_plan,
    daily_spend_estimates=daily_estimates,
    demo=True
)
```

### Budget Optimization

```python
from budgeteer_mcp_agent.fast_server import suggest_budget_swaps

# Get budget optimization suggestions
suggestions = await suggest_budget_swaps(
    trip_plan=trip_plan,
    target_categories=["hotels", "flights"],
    max_risk_level="medium",
    min_savings_threshold=100.0,
    demo=True
)
```

## Architecture

The service is built using:
- **FastMCP**: For MCP protocol compliance and tool definitions
- **Pydantic**: For data validation and serialization
- **Async/Await**: For non-blocking operations
- **Stateless Design**: Each request is processed independently

## Integration

This service can be integrated with:
- Travel planning applications
- Budget management systems
- AI travel assistants
- MCP-compliant orchestrators

## Development

### Adding New Tools

1. Define the tool function in `fast_server.py`
2. Add the tool schema to `mcp_metadata.json`
3. Update the models if new data structures are needed
4. Add test coverage in `test_fast_server.py`

### Extending Data Models

1. Modify the appropriate model in `models.py`
2. Update fixtures in `fixtures.py` if needed
3. Ensure serialization handles new fields properly

## License

MIT License - see LICENSE file for details.

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive test coverage
3. Update documentation for any new features
4. Ensure MCP compliance is maintained
