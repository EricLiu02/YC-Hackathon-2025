# Flight MCP Agent Service

A standalone MCP (Model Context Protocol) server that provides flight search and pricing capabilities using the Amadeus API. This service can be integrated into LangGraph orchestrators and other MCP-compatible systems.

## Features

- **Flight Search**: Search for flights with flexible parameters (origin, destination, dates, passengers, class)
- **Flight Pricing**: Get detailed pricing breakdowns for specific flights
- **Demo Mode**: Use cached flight data for testing without API calls
- **Error Handling**: Automatic fallback to demo data on API failures
- **MCP Compatible**: Full MCP server implementation with tool metadata

## Tools Exposed

### 1. `search_flights`
Search for flights based on trip constraints.

**Parameters:**
- `origin` (required): Origin airport code (e.g., "JFK", "LAX")
- `destination` (required): Destination airport code
- `departure_date` (required): Departure date in YYYY-MM-DD format
- `return_date` (optional): Return date for round trip
- `adults` (default: 1): Number of adult passengers
- `children` (default: 0): Number of child passengers 
- `infants` (default: 0): Number of infant passengers
- `travel_class` (default: "ECONOMY"): Travel class preference
- `max_results` (default: 10): Maximum flight options to return

### 2. `get_flight_pricing`
Get detailed pricing information for specific flight IDs.

**Parameters:**
- `flight_ids` (required): Array of flight IDs to get pricing for

### 3. `get_cached_flights`
Get demo flight data for testing purposes.

**Parameters:**
- `origin` (required): Origin airport code
- `destination` (required): Destination airport code

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables:**
   Create a `.env` file or set these environment variables:
   ```bash
   AMADEUS_API_KEY=your_amadeus_api_key
   AMADEUS_API_SECRET=your_amadeus_api_secret
   ```

3. **Get Amadeus API Credentials:**
   - Sign up at [Amadeus for Developers](https://developers.amadeus.com)
   - Create a new application
   - Get your API Key and Secret

## Usage

### Run as MCP Server (Production)
```bash
python -m flight_mcp_agent.server
```

### Run in Demo Mode (Testing)
```bash
python -m flight_mcp_agent.server --demo
```

### Integration with MCP Clients
Add this server to your MCP client configuration:

```json
{
  "mcpServers": {
    "flight-agent": {
      "command": "python",
      "args": ["-m", "flight_mcp_agent.server"],
      "env": {
        "AMADEUS_API_KEY": "your_key_here",
        "AMADEUS_API_SECRET": "your_secret_here"
      }
    }
  }
}
```

## API Integration

This service integrates with the Amadeus Self-Service APIs:
- **Flight Offers Search API**: For searching available flights
- **Flight Offers Pricing API**: For getting detailed pricing (fallback to demo data)

## Error Handling

The service includes robust error handling:
- API rate limiting and error responses trigger fallback to demo data
- Invalid parameters return helpful error messages
- Network issues are handled gracefully with demo data fallback

## Development

The codebase is structured as follows:
- `models.py`: Pydantic models for request/response validation
- `amadeus_client.py`: Amadeus API client with error handling
- `fixtures.py`: Demo data for testing and fallback scenarios
- `server.py`: MCP server implementation
- `mcp_metadata.json`: Service discovery metadata

## Testing

Use the demo mode for testing without API calls:
```bash
python -m flight_mcp_agent.server --demo
```

This uses static fixture data that mimics real flight search results.