# Budgeteer MCP Agent Service

A standalone MCP (Model Context Protocol) server that provides travel budgeting and cost estimation capabilities. This service can calculate comprehensive trip budgets, suggest cost-saving alternatives, and integrate with budget management systems. It's designed to work alongside flight and hotel MCP agents in travel planning orchestrators.

## Features

- **Budget Calculation**: Comprehensive trip budget analysis with category breakdowns
- **Cost Optimization**: Suggest budget-friendly alternatives with risk assessment
- **Multi-Category Support**: Covers flights, hotels, food, activities, transportation, shopping, and misc expenses
- **Demo Mode**: Use synthetic data for testing without external API dependencies
- **Stateless Design**: Fast, independent request processing for each calculation
- **MCP Compatible**: Full MCP server implementation with tool metadata
- **Risk Analysis**: Evaluate trade-offs between cost savings and quality/comfort

## Tools Exposed

### 1. `calculate_trip_budget`
Calculate comprehensive trip budget including planned costs and daily spending estimates.

**Parameters:**
- `trip_plan` (required): Complete trip plan with components, dates, budget, and traveler count
  ```json
  {
    "trip_id": "london_2025",
    "destination": "London, UK",
    "start_date": "2025-03-15",
    "end_date": "2025-03-22",
    "num_travelers": 2,
    "total_budget": 4000.0,
    "components": [...],
    "currency": "USD"
  }
  ```
- `daily_spend_estimates` (required): Daily spending estimates per category per person
  ```json
  [
    {
      "category": "food",
      "per_person_per_day": 75.0,
      "currency": "USD"
    }
  ]
  ```
- `additional_costs` (optional): Additional costs not included in main trip plan
- `demo` (optional): Whether to use demo data for testing

**Returns:**
Budget calculation with breakdown by category, status, and surplus/shortfall analysis.

### 2. `suggest_budget_swaps`
Suggest budget-friendly alternatives for trip components with cost savings and risk analysis.

**Parameters:**
- `trip_plan` (required): Current trip plan to analyze for budget optimization
- `target_categories` (optional): Specific travel categories to focus on (e.g., ["hotels", "flights"])
- `max_risk_level` (optional, default: "medium"): Maximum acceptable risk level ("low", "medium", "high")
- `min_savings_threshold` (optional, default: 0.0): Minimum cost savings required to suggest alternatives
- `demo` (optional): Whether to use demo data for testing

**Returns:**
List of budget swap suggestions with cost savings, risk analysis, and constraint violations.

### 3. `get_demo_trip_plan`
Get a demo trip plan for testing and development purposes.

**Parameters:** None

**Returns:**
Sample trip plan with realistic components and costs for London trip.

### 4. `get_demo_daily_spend_estimates`
Get demo daily spend estimates for testing and development purposes.

**Parameters:** None

**Returns:**
Sample daily spending estimates by travel category.

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

### Trip Component Structure
```json
{
  "component_id": "hotel_london_7_nights",
  "category": "hotels",
  "name": "London Marriott Hotel",
  "cost": 1400.0,
  "currency": "USD",
  "description": "7 nights, 4-star hotel in city center",
  "date": "2025-03-15"
}
```

## Setup

1. **Install Dependencies:**
   ```bash
   cd backend/budgeteer_mcp_agent
   pip install -e .
   ```

2. **No External API Keys Required:**
   This service currently runs entirely on synthetic/demo data for speed and testing purposes.

3. **Future API Integration:**
   When ready to integrate with real budget APIs, update the tool implementations in `fast_server.py`.

## Usage

### Run as MCP Server (Production)
```bash
python -m budgeteer_mcp_agent
```

### Run in Demo Mode (Testing)
```bash
python -m budgeteer_mcp_agent --demo
```

### Integration with MCP Clients
Add this server to your MCP client configuration:

```json
{
  "mcpServers": {
    "budgeteer-agent": {
      "command": "python",
      "args": ["-m", "budgeteer_mcp_agent"],
      "env": {}
    }
  }
}
```

### Integration with LangGraph Orchestrators
```python
from langgraph.graph import StateGraph
from mcp import ClientSession

# Initialize MCP client
async with ClientSession() as session:
    # Add budgeteer agent
    await session.add_mcp_server("budgeteer-agent", "python -m budgeteer_mcp_agent")
    
    # Use budget calculation tool
    result = await session.call_tool("budgeteer-agent", "calculate_trip_budget", {
        "trip_plan": trip_plan_data,
        "daily_spend_estimates": daily_estimates
    })
```

## API Integration

This service is designed for easy integration with budget management APIs:

### Current Implementation
- **Demo Data**: Uses realistic synthetic data for immediate testing
- **Stateless Processing**: Each request is processed independently
- **Fast Response**: No external API calls for instant results

### Future API Integration Points
When ready to connect to real APIs, update these functions in `fast_server.py`:

```python
# Replace demo logic with real API calls
async def calculate_trip_budget(...):
    if use_demo:
        response = get_demo_budget_calculation_response(request.trip_plan)
    else:
        # Call your budget calculation API
        response = await your_budget_api.calculate(request.trip_plan)
    
    return _serialize_budget_calculation_response(response)
```

### Example API Endpoints to Integrate
- **Budget Calculation APIs**: Trip cost estimation services
- **Hotel Price APIs**: Alternative accommodation pricing
- **Flight Price APIs**: Alternative flight pricing
- **Activity Cost APIs**: Local attraction and experience pricing
- **Currency Conversion APIs**: Multi-currency support

## Error Handling

The service includes robust error handling:
- Invalid request formats return structured error responses
- Date parsing errors are handled gracefully
- Demo mode fallback ensures service availability
- JSON serialization errors are caught and reported

## Development

The codebase is structured as follows:
- `models.py`: Pydantic models for request/response validation and data structures
- `fixtures.py`: Demo data and test fixtures for realistic scenarios
- `fast_server.py`: FastMCP server implementation with tool definitions
- `mcp_metadata.json`: Service discovery metadata and tool schemas
- `test_tools.py`: Tool testing script for development verification
- `requirements.txt`: Python dependencies (minimal - only MCP essentials)

## Testing

### Test Individual Tools
```bash
python test_tools.py
```

### Test Server Functionality
```bash
python -m budgeteer_mcp_agent.test_fast_server
```

### Demo Mode Testing
```bash
python -m budgeteer_mcp_agent --demo
```

## Example Workflows

### 1. Basic Budget Calculation
```python
# Calculate budget for a trip
result = await calculate_trip_budget(
    trip_plan=my_trip_plan,
    daily_spend_estimates=my_daily_estimates,
    demo=True
)

# Check budget status
if result["budget_status"] == "critical":
    # Get optimization suggestions
    suggestions = await suggest_budget_swaps(
        trip_plan=my_trip_plan,
        target_categories=["hotels", "flights"],
        min_savings_threshold=100.0
    )
```

### 2. Budget Optimization Workflow
```python
# 1. Calculate current budget
current_budget = await calculate_trip_budget(...)

# 2. If over budget, get suggestions
if current_budget["budget_status"] in ["over_budget", "critical"]:
    swaps = await suggest_budget_swaps(
        trip_plan=trip_plan,
        max_risk_level="low"
    )
    
    # 3. Apply selected optimizations
    for suggestion in swaps["suggestions"]:
        if suggestion["recommendation_score"] > 0.8:
            # Apply this swap
            apply_budget_swap(suggestion)
```

## Integration with Other MCP Agents

This service is designed to work alongside:
- **Flight MCP Agent**: For flight cost data and alternatives
- **Hotel MCP Agent**: For accommodation cost data and alternatives
- **Other Travel Agents**: For comprehensive trip planning

### Multi-Agent Workflow Example
```python
# 1. Get flight options from flight agent
flights = await flight_agent.search_flights(...)

# 2. Get hotel options from hotel agent  
hotels = await hotel_agent.search_hotels(...)

# 3. Calculate budget with budgeteer agent
budget = await budgeteer_agent.calculate_trip_budget(
    trip_plan=create_trip_plan(flights, hotels),
    daily_spend_estimates=default_estimates
)

# 4. Optimize if needed
if budget["budget_status"] == "critical":
    optimizations = await budgeteer_agent.suggest_budget_swaps(...)
```

## Performance Characteristics

- **Response Time**: <100ms for demo data, scalable for API integration
- **Concurrent Requests**: Stateless design supports high concurrency
- **Memory Usage**: Minimal - only processes current request
- **Scalability**: Horizontal scaling ready with load balancers

## Future Enhancements

1. **Real API Integration**: Connect to actual budget calculation services
2. **Machine Learning**: Implement intelligent cost prediction models
3. **Multi-Currency**: Support for international travel budgets
4. **Historical Data**: Learn from past trips for better estimates
5. **Advanced Analytics**: Spending pattern analysis and recommendations
6. **Real-time Pricing**: Live price updates from travel APIs

## Support and Contributing

- **Documentation**: This README and inline code comments
- **Testing**: Comprehensive test suite with demo data
- **Error Handling**: Graceful fallbacks and clear error messages
- **Extensibility**: Easy to add new tools and integrate APIs

---

**Status**: ✅ Production Ready with Demo Data  
**Last Updated**: August 23, 2025  
**Implementation**: YC Hackathon Team  
**MCP Version**: 1.0.0
