# Hotel MCP Agent Service

A standalone MCP (Model Context Protocol) server that provides hotel search and pricing capabilities using the SearchAPI Google Hotels integration. This service can be integrated into LangGraph orchestrators and other MCP-compatible systems.

## Features

- **Hotel Search**: Search for hotels with flexible parameters (city, dates, guests, class, amenities)
- **Hotel Pricing**: Get detailed pricing breakdowns for specific hotels and room types
- **Demo Mode**: Use cached hotel data for testing without API calls
- **Error Handling**: Automatic fallback to demo data on API failures
- **MCP Compatible**: Full MCP server implementation with tool metadata
- **SearchAPI Integration**: Real hotel data from Google Hotels via SearchAPI

## Tools Exposed

### 1. `search_hotels`
Search for hotels based on location, dates, and preferences.

**Parameters:**
- `city` (required): City or destination to search for hotels (e.g., "New York", "Paris")
- `check_in_date` (required): Check-in date in YYYY-MM-DD format
- `check_out_date` (required): Check-out date in YYYY-MM-DD format
- `adults` (default: 2): Number of adult guests
- `children` (default: 0): Number of children
- `rooms` (default: 1): Number of rooms needed
- `hotel_class` (optional): Hotel star rating filter ("3", "4", "5")
- `max_price` (optional): Maximum price per night in USD
- `amenities` (optional): Desired amenities array (e.g., ["wifi", "pool", "gym", "spa"])
- `sort_by` (default: "price"): Sort by "price", "rating", or "distance"
- `max_results` (default: 10): Maximum number of hotels to return

### 2. `get_hotel_pricing`
Get detailed pricing information for a specific hotel and room type.

**Parameters:**
- `hotel_id` (required): Hotel ID from search results
- `room_type` (optional): Specific room type
- `check_in_date` (required): Check-in date in YYYY-MM-DD format
- `check_out_date` (required): Check-out date in YYYY-MM-DD format
- `adults` (default: 2): Number of adult guests
- `children` (default: 0): Number of children
- `rooms` (default: 1): Number of rooms needed

## Setup

1. **Install Dependencies:**
   ```bash
   uv pip install -r hotel_mcp_agent/requirements.txt
   ```

2. **Environment Variables:**
   Add to your `.env` file or set these environment variables:
   ```bash
   SEARCH_API_KEY=your_searchapi_key
   ```

3. **Get SearchAPI Key:**
   - Sign up at [SearchAPI.io](https://www.searchapi.io/)
   - Get your API key from the dashboard
   - The service uses Google Hotels API engine

## Usage

### Run as MCP Server (Production)
```bash
export PATH="$HOME/.local/bin:$PATH"
source flight_mcp_venv/bin/activate
python -m hotel_mcp_agent.server
```

### Run in Demo Mode (Testing)
```bash
export PATH="$HOME/.local/bin:$PATH"
source flight_mcp_venv/bin/activate
python -m hotel_mcp_agent.server --demo
```

### Integration with MCP Clients
Add this server to your MCP client configuration:

```json
{
  "mcpServers": {
    "hotel-agent": {
      "command": "python",
      "args": ["-m", "hotel_mcp_agent.server"],
      "env": {
        "SEARCH_API_KEY": "your_key_here"
      }
    }
  }
}
```

## API Integration

This service integrates with SearchAPI's Google Hotels engine:
- **Google Hotels Search API**: For searching available hotels with real-time data
- **Hotel Details & Pricing**: Comprehensive hotel information including amenities, reviews, and room types

## Error Handling

The service includes robust error handling:
- API rate limiting and error responses trigger fallback to demo data
- Invalid parameters return helpful error messages
- Network issues are handled gracefully with demo data fallback

## Development

The codebase is structured as follows:
- `models.py`: Pydantic models for request/response validation
- `searchapi_client.py`: SearchAPI Google Hotels client with error handling
- `fixtures.py`: Demo data for testing and fallback scenarios
- `server.py`: MCP server implementation
- `mcp_metadata.json`: Service discovery metadata

## Demo Data

The demo mode includes realistic hotel data for testing:
- **Grand Plaza Hotel NYC**: 4-star luxury hotel with multiple room types
- **Boutique Central Hotel**: 3-star boutique hotel with cozy accommodations  
- **Luxury Manhattan Resort**: 5-star resort with premium amenities

Each hotel includes:
- Location details with coordinates
- Guest reviews and ratings
- Amenity lists
- Multiple room types with pricing
- Cancellation policies
- High-quality images

## Testing

Use the demo mode for testing without API calls:
```bash
python -m hotel_mcp_agent.server --demo
```

This uses static fixture data that mimics real hotel search results with comprehensive details.