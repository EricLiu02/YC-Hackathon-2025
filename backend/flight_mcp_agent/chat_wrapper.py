import os
import json
import logging
from typing import Optional, Any, Dict, List
import requests

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession


load_dotenv()


def _init_logging() -> logging.Logger:
    logger = logging.getLogger("flight_chat")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
    os.makedirs(log_dir, exist_ok=True)
    file_path = os.path.join(log_dir, "flight_chat.log")

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(file_path)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info("Initialized flight chat logging at %s", file_path)
    return logger


LOGGER = _init_logging()


class FlightEntities(BaseModel):
    intent: str = "chitchat"  # search_flights | get_flight_pricing | chitchat
    # Search params
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    infants: Optional[int] = None
    travel_class: Optional[str] = None
    max_results: Optional[int] = None
    # Pricing params
    flight_ids: Optional[list[str]] = None


SYSTEM_DETECT = (
    "Extract intent and entities for a flight tool. Output ONLY JSON: {intent, entities}.\n"
    "- intent: one of 'search_flights', 'get_flight_pricing', 'chitchat'\n"
    "- entities: may include origin, destination, departure_date, return_date, adults, children, infants, travel_class, max_results, flight_ids\n"
    "Rules:\n"
    "1) Respect prepositions: 'from <X>' is origin, 'to <Y>' is destination.\n"
    "2) Accept city names and map to IATA codes when obvious: 'SFO'->SFO, 'San Francisco'->SFO.\n"
    "   Hawaii defaults to HNL (Honolulu) unless a specific island is named: Maui->OGG, Kauai->LIH, Big Island/Kona->KOA.\n"
    "3) Dates: parse natural phrases relative to today's date (YYYY-MM-DD):\n"
    "   - 'today' => departure_date = today.\n"
    "   - 'tomorrow' => departure_date = today + 1 day.\n"
    "   - 'in the next 3 days' / 'within the next 3 days' => departure_date = today, return_date = today + 3 days.\n"
    "   - 'in the next week' / 'next week' => departure_date = today, return_date = today + 7 days.\n"
    "   - 'MM/DD' => departure_date = current_year-MM-DD.\n"
    "   - 'MM/DD-MM/DD' => departure_date = first date, return_date = second date (current year).\n"
    "   If unsure, leave dates null; never invent far-future dates.\n"
    "4) If unsure, leave a field null. Do NOT fabricate or default to JFK/LAX.\n"
    "Examples (assume today is 2025-01-15; do not copy these to output):\n"
    " - Input: 'SFO to LAX tomorrow'\n"
    "   Output: {\"intent\":\"search_flights\",\"entities\":{\"origin\":\"SFO\",\"destination\":\"LAX\",\"departure_date\":\"2025-01-16\"}}\n"
    " - Input: 'from Boston to Miami in the next three days for 2 adults'\n"
    "   Output: {\"intent\":\"search_flights\",\"entities\":{\"origin\":\"BOS\",\"destination\":\"MIA\",\"adults\":2,\"departure_date\":\"2025-01-15\",\"return_date\":\"2025-01-18\"}}\n"
    " - Input: 'San Francisco to Hawaii next week'\n"
    "   Output: {\"intent\":\"search_flights\",\"entities\":{\"origin\":\"SFO\",\"destination\":\"HNL\",\"departure_date\":\"2025-01-15\",\"return_date\":\"2025-01-22\"}}\n"
)


def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    return OpenAI(api_key=api_key)


def detect_intent_entities(message: str) -> FlightEntities:
    client = _openai_client()
    completion = client.responses.create(
        model="gpt-5",
        instructions=SYSTEM_DETECT,
        input=message,
    )
    text = getattr(completion, "output_text", None) or "{}"
    try:
        data = json.loads(text)
        ent = FlightEntities(**{
            "intent": data.get("intent", "chitchat"),
            **(data.get("entities") or {}),
        })
        LOGGER.info("Detected intent=%s, entities=%s", ent.intent, {k: v for k, v in ent.model_dump().items() if k != 'intent'})
        return ent
    except Exception:
        LOGGER.exception("Failed to parse intent/entities from model output: %s", text)
        return FlightEntities()


def _extract_json_from_result(call_result: Any) -> Dict[str, Any] | list | None:
    # Try structured content first
    structured = getattr(call_result, "structuredContent", None)
    if structured is not None:
        return structured
    # Fallback: try textual content
    content = getattr(call_result, "content", None)
    if isinstance(content, list) and content:
        first = content[0]
        text = None
        # Pydantic object with .text
        text = getattr(first, "text", None)
        if text is None and isinstance(first, dict):  # dict fallback
            text = first.get("text")
        if text:
            try:
                return json.loads(text)
            except Exception:
                LOGGER.warning("Tool returned non-JSON text; wrapping as raw. text_len=%s", len(text))
                return {"raw": text}
    return None


async def call_search_flights(entities: FlightEntities) -> Dict[str, Any]:
    args = {
        "origin": entities.origin or "JFK",
        "destination": entities.destination or "LAX",
        "departure_date": entities.departure_date or "2025-09-10",
        "return_date": entities.return_date,
        "adults": entities.adults or 1,
        "children": entities.children or 0,
        "infants": entities.infants or 0,
        "travel_class": (entities.travel_class or "ECONOMY").upper(),
        "max_results": entities.max_results or 5,
    }
    LOGGER.info("Calling search_flights with args=%s", args)
    server = StdioServerParameters(command="python3", args=["-m", "flight_mcp_agent"])
    async with stdio_client(server) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            result = await s.call_tool("search_flights", args)
            data = _extract_json_from_result(result) or {}
            if isinstance(data, dict):
                # Log first 1-2 flights with route for debugging
                flights = data.get("flights", []) or []
                sample = [
                    {
                        "flight_id": f.get("flight_id"),
                        "route": f"{f.get('departure_airport')}->{f.get('arrival_airport')}",
                        "price": f.get("price"),
                    }
                    for f in flights[:2]
                ]
                LOGGER.info(
                    "search_flights returned %s flights (total_results=%s), sample=%s",
                    len(flights), data.get("total_results"), sample,
                )
                return data
            LOGGER.info("search_flights returned non-dict payload type=%s", type(data).__name__)
            return {"data": data}


async def call_get_pricing(entities: FlightEntities) -> Dict[str, Any]:
    flight_ids = entities.flight_ids or []
    if not flight_ids:
        # If no IDs provided, first search, then take top 2
        search = await call_search_flights(entities)
        flights = search.get("flights", [])
        flight_ids = [f.get("flight_id") for f in flights[:2] if f.get("flight_id")]
    args = {"flight_ids": flight_ids}
    LOGGER.info("Calling get_flight_pricing with flight_ids=%s", flight_ids)
    server = StdioServerParameters(command="python3", args=["-m", "flight_mcp_agent"])
    async with stdio_client(server) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            result = await s.call_tool("get_flight_pricing", args)
            data = _extract_json_from_result(result) or []
            LOGGER.info("get_flight_pricing returned %s items", len(data) if isinstance(data, list) else 1)
            return {"pricing": data}


def _summarize(data: Dict[str, Any], ent: FlightEntities) -> str:
    """Summarize results while pinning the exact route and date to prevent drift."""
    client = _openai_client()
    
    # Check if this is an enhanced search with multiple routes
    if data.get("enhanced_search"):
        instructions = (
            "Summarize flight search results for multiple airport combinations.\n"
            f"Original search date: {ent.departure_date or 'today'}.\n"
            "IMPORTANT: Show the BEST 5 FLIGHT OPTIONS overall, sorted by price (cheapest first).\n"
            "For each flight, include: Route, Airline, Price, Departure Time, Duration, Stops.\n"
            "After the top 5, briefly mention other available routes if any.\n"
            "Format should be clear and easy to compare options."
        )
        
        # Collect all flights across routes and sort by price
        all_flights_detailed = []
        routes_summary = []
        
        for route_data in data.get("routes", []):
            route_flights = route_data.get("flights", [])
            
            # Add route info to each flight for better tracking
            for flight in route_flights:
                flight_detailed = {
                    "flight_id": flight.get("flight_id"),
                    "route": route_data.get("route"),
                    "departure_airport": flight.get("departure_airport"),
                    "arrival_airport": flight.get("arrival_airport"),
                    "departure_time": flight.get("departure_time"),
                    "arrival_time": flight.get("arrival_time"),
                    "stops": flight.get("stops"),
                    "price": flight.get("price", float('inf')),  # Handle missing prices
                    "currency": flight.get("currency"),
                    "airline_name": flight.get("airline_name"),
                    "duration": flight.get("duration"),
                }
                all_flights_detailed.append(flight_detailed)
            
            # Keep route summary for context
            routes_summary.append({
                "route": route_data.get("route"),
                "flight_count": len(route_flights),
                "total_available": route_data.get("total_results", 0)
            })
        
        # Sort all flights by price (cheapest first)
        all_flights_detailed.sort(key=lambda x: x.get("price", float('inf')))
        
        # Take top 10 flights for analysis (summarizer will pick best 5)
        top_flights = all_flights_detailed[:10]
        
        payload = json.dumps({
            "enhanced_search": True,
            "departure_date": ent.departure_date,
            "route_combinations": data.get("route_combinations"),
            "routes": routes_summary,
            "all_flights_sorted": top_flights,  # All flights sorted by price
            "total_flights": data.get("total_results")
        })
        
        LOGGER.info("Enhanced summarizer: %d routes, %d total flights", 
                   data.get("route_combinations", 0), data.get("total_results", 0))
    
    else:
        # Regular single-route summary
        origin = ent.origin or (data.get("flights", [{}])[0].get("departure_airport") if data.get("flights") else None)
        destination = ent.destination or (data.get("flights", [{}])[0].get("arrival_airport") if data.get("flights") else None)
        dep_date = ent.departure_date

        # Compact payload: only include the first few flights with explicit route fields
        flights = data.get("flights") or []
        compact = [
            {
                "flight_id": f.get("flight_id"),
                "departure_airport": f.get("departure_airport"),
                "arrival_airport": f.get("arrival_airport"),
                "departure_time": f.get("departure_time"),
                "arrival_time": f.get("arrival_time"),
                "stops": f.get("stops"),
                "price": f.get("price"),
                "currency": f.get("currency"),
                "airline_name": f.get("airline_name"),
                "duration": f.get("duration"),
            }
            for f in flights[:5]
        ]

        instructions = (
            f"Summarize flights for route {origin or ''} → {destination or ''}.\n"
            + (f"Date: {dep_date}.\n" if dep_date else "")
            + "IMPORTANT: Show the BEST 5 FLIGHT OPTIONS sorted by price (cheapest first).\n"
            + "For each flight include: Airline, Price, Departure Time, Duration, Stops.\n"
            + "Format clearly for easy comparison. Do NOT change the route airports."
        )

        payload = json.dumps({
            "origin": origin,
            "destination": destination,
            "departure_date": dep_date,
            "flights": compact,
            "total_results": data.get("total_results"),
        })

        LOGGER.info("Summarizer route lock: %s->%s on %s; flights_sample=%s", origin, destination, dep_date, [
            f"{f.get('departure_airport')}->{f.get('arrival_airport')}" for f in compact
        ])

    completion = client.responses.create(
        model="gpt-5",
        instructions=instructions,
        input=payload,
    )
    return getattr(completion, "output_text", None) or ""


def _normalize_entities_from_text(user_text: str, ent: FlightEntities) -> FlightEntities:
    """Best-effort normalization: map city names to IATA and normalize mm/dd date ranges.

    This avoids falling back to JFK/LAX when extraction misses IATA codes.
    """
    import re
    from datetime import datetime, timedelta

    text = user_text.lower()

    def map_city(token: str) -> Optional[str]:
        token = token.strip().lower()
        mapping = [
            # US Cities
            ("san francisco", "SFO"),
            ("sfo", "SFO"),
            ("los angeles", "LAX"),
            ("lax", "LAX"),
            ("new york", "JFK"),
            ("jfk", "JFK"),
            ("chicago", "ORD"),
            ("miami", "MIA"),
            ("boston", "BOS"),
            ("seattle", "SEA"),
            
            # Hawaii
            ("hawaii", "HNL"),
            ("honolulu", "HNL"),
            ("oahu", "HNL"),
            ("maui", "OGG"),
            ("kauai", "LIH"),
            ("lihue", "LIH"),
            ("big island", "KOA"),
            ("kona", "KOA"),
            
            # International
            ("brasil", "GRU"),
            ("brazil", "GRU"),
            ("sao paulo", "GRU"),
            ("são paulo", "GRU"),
            ("rio", "GIG"),
            ("rio de janeiro", "GIG"),
            ("london", "LHR"),
            ("paris", "CDG"),
            ("tokyo", "NRT"),
            ("rome", "FCO"),
            ("madrid", "MAD"),
            ("barcelona", "BCN"),
            ("amsterdam", "AMS"),
            ("frankfurt", "FRA"),
            ("zurich", "ZUR"),
            ("dubai", "DXB"),
            ("singapore", "SIN"),
            ("hong kong", "HKG"),
            ("sydney", "SYD"),
            ("melbourne", "MEL"),
            ("toronto", "YYZ"),
            ("vancouver", "YVR"),
            ("mexico city", "MEX"),
            ("mumbai", "BOM"),
            ("delhi", "DEL"),
            ("bangkok", "BKK"),
            ("istanbul", "IST"),
        ]
        for key, code in mapping:
            if key in token:
                return code
        return None

    # Extract explicit from/to phrases
    m_from = re.search(r"\bfrom\s+([a-zA-Z\s]+?)(?=\s+to\b|$)", text)
    m_to = re.search(r"\bto\s+([a-zA-Z\s]+)", text)
    if not ent.origin and m_from:
        code = map_city(m_from.group(1))
        if code:
            ent.origin = code
    if not ent.destination and m_to:
        code = map_city(m_to.group(1))
        if code:
            ent.destination = code

    # If 'hawaii' mentioned anywhere, prefer HNL as destination
    if not ent.destination and "hawaii" in text:
        ent.destination = "HNL"

    # Avoid origin=destination
    if ent.origin and ent.destination and ent.origin == ent.destination:
        # If both same and hawaii mentioned, push destination to HNL
        if "hawaii" in text:
            ent.destination = "HNL"

    # Natural date words
    now = datetime.now()
    if not ent.departure_date:
        if "today" in text:
            ent.departure_date = now.strftime("%Y-%m-%d")
        elif "tomorrow" in text:
            ent.departure_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    # Date range parsing like 09/12-09/20
    if not ent.departure_date or not ent.return_date:
        m = re.search(r"(\d{1,2})\/(\d{1,2})\s*[-–]\s*(\d{1,2})\/(\d{1,2})", text)
        if m:
            mm1, dd1, mm2, dd2 = m.groups()
            year = now.year
            try:
                dep = datetime(year, int(mm1), int(dd1)).strftime("%Y-%m-%d")
                ret = datetime(year, int(mm2), int(dd2)).strftime("%Y-%m-%d")
                if not ent.departure_date:
                    ent.departure_date = dep
                if not ent.return_date:
                    ent.return_date = ret
            except Exception:
                pass

    return ent


async def research_locations_with_perplexity(location_text: str) -> List[str]:
    """Use Perplexity as the PRIMARY method to find all possible airport codes for a location."""
    
    # Try Perplexity API first (now the default)
    api_key = os.getenv("SONAR_API_KEY")
    if api_key:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            query = f"""What are all the major airport codes (IATA codes) for flights to/from {location_text}? 
            Include international airports, major domestic airports, and nearby alternatives.
            For example, if the location is "Shanghai", include PVG (Shanghai Pudong) and SHA (Shanghai Hongqiao).
            If it's "New York", include JFK, LGA, and EWR.
            If it's "Chicago", include ORD and MDW.
            Return only the 3-letter IATA codes in a simple comma-separated list format like: PVG, SHA, JFK"""
            
            data = {
                "model": "sonar-pro",  # Fast model for airport code lookup
                "messages": [
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 150
            }
            
            LOGGER.info("Researching airport codes for location: %s", location_text)
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=data,
                timeout=15  # Reduced timeout for faster fallback
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # Extract 3-letter airport codes from the response
                import re
                codes = re.findall(r'\b[A-Z]{3}\b', content)
                # Remove duplicates while preserving order
                unique_codes = []
                for code in codes:
                    if code not in unique_codes:
                        unique_codes.append(code)
                
                if unique_codes:
                    LOGGER.info("Found airport codes via Perplexity for '%s': %s", location_text, unique_codes)
                    return unique_codes[:5]  # Limit to top 5 codes
                    
            else:
                LOGGER.warning("Perplexity API error: %s - %s", response.status_code, response.text)
                
        except Exception as e:
            LOGGER.warning("Perplexity API failed for '%s': %s", location_text, str(e))
    
    # Static fallback ONLY if Perplexity fails
    LOGGER.info("Using static fallback for location: %s", location_text)
    static_mapping = {
        # Asia
        "shanghai": ["PVG", "SHA"],  # Pudong and Hongqiao
        "beijing": ["PEK", "PKX"],   # Capital and Daxing
        "tokyo": ["NRT", "HND"],     # Narita and Haneda  
        "hong kong": ["HKG"],
        "singapore": ["SIN"],
        "bangkok": ["BKK", "DMK"],   # Suvarnabhumi and Don Mueang
        "mumbai": ["BOM"],
        "delhi": ["DEL"],
        "seoul": ["ICN", "GMP"],     # Incheon and Gimpo
        "kuala lumpur": ["KUL"],
        "jakarta": ["CGK"],
        "manila": ["MNL"],
        "ho chi minh": ["SGN"],
        "hanoi": ["HAN"],
        
        # Europe  
        "london": ["LHR", "LGW", "STN", "LTN"],  # Heathrow, Gatwick, Stansted, Luton
        "paris": ["CDG", "ORY"],     # Charles de Gaulle and Orly
        "amsterdam": ["AMS"],
        "frankfurt": ["FRA"],
        "zurich": ["ZUR"],
        "madrid": ["MAD"],
        "barcelona": ["BCN"],
        "rome": ["FCO", "CIA"],      # Fiumicino and Ciampino
        "milan": ["MXP", "LIN"],     # Malpensa and Linate
        "moscow": ["SVO", "DME", "VKO"],  # Sheremetyevo, Domodedovo, Vnukovo
        "istanbul": ["IST", "SAW"],  # Istanbul Airport and Sabiha Gökçen
        "budapest": ["BUD"],
        "prague": ["PRG"],
        "vienna": ["VIE"],
        "berlin": ["BER"],
        "munich": ["MUC"],
        "copenhagen": ["CPH"],
        "stockholm": ["ARN"],
        "oslo": ["OSL"],
        "helsinki": ["HEL"],
        "warsaw": ["WAW"],
        "athens": ["ATH"],
        "lisbon": ["LIS"],
        
        # North America
        "new york": ["JFK", "LGA", "EWR"],  # JFK, LaGuardia, Newark
        "los angeles": ["LAX", "BUR", "LGB"],  # LAX, Burbank, Long Beach
        "chicago": ["ORD", "MDW"],   # O'Hare and Midway
        "toronto": ["YYZ", "YTZ"],   # Pearson and Billy Bishop
        "vancouver": ["YVR"],
        "montreal": ["YUL"],
        "san francisco": ["SFO"],
        "seattle": ["SEA"],
        "boston": ["BOS"],
        "miami": ["MIA"],
        "atlanta": ["ATL"],
        "denver": ["DEN"],
        "phoenix": ["PHX"],
        "las vegas": ["LAS"],
        "washington": ["DCA", "IAD", "BWI"],  # Reagan, Dulles, Baltimore
        "mexico city": ["MEX"],
        
        # Middle East & Africa
        "dubai": ["DXB", "DWC"],     # Dubai International and Al Maktoum
        "doha": ["DOH"],
        "abu dhabi": ["AUH"],
        "kuwait": ["KWI"],
        "riyadh": ["RUH"],
        "jeddah": ["JED"],
        "cairo": ["CAI"],
        "casablanca": ["CMN"],
        "johannesburg": ["JNB"],
        "cape town": ["CPT"],
        "nairobi": ["NBO"],
        "addis ababa": ["ADD"],
        
        # South America
        "rio de janeiro": ["GIG", "SDU"],  # Galeão and Santos Dumont
        "sao paulo": ["GRU", "CGH"],  # Guarulhos and Congonhas
        "buenos aires": ["EZE", "AEP"],  # Ezeiza and Jorge Newbery
        "lima": ["LIM"],
        "bogota": ["BOG"],
        "santiago": ["SCL"],
        "caracas": ["CCS"],
        
        # Oceania
        "sydney": ["SYD"],
        "melbourne": ["MEL"],
        "brisbane": ["BNE"],
        "perth": ["PER"],
        "auckland": ["AKL"],
        "wellington": ["WLG"],
        
        # Common aliases and countries
        "brazil": ["GRU", "GIG"],    # São Paulo and Rio
        "china": ["PEK", "PVG"],     # Beijing and Shanghai
        "japan": ["NRT", "HND"],     # Tokyo airports
        "india": ["DEL", "BOM"],     # Delhi and Mumbai
        "korea": ["ICN"],            # Seoul
        "thailand": ["BKK"],         # Bangkok
        "germany": ["FRA", "MUC"],   # Frankfurt and Munich
        "italy": ["FCO", "MXP"],     # Rome and Milan
        "spain": ["MAD", "BCN"],     # Madrid and Barcelona
        "netherlands": ["AMS"],      # Amsterdam
        "switzerland": ["ZUR"],      # Zurich
        "australia": ["SYD", "MEL"], # Sydney and Melbourne
        "canada": ["YYZ", "YVR"],    # Toronto and Vancouver
        "uae": ["DXB", "AUH"],       # Dubai and Abu Dhabi
        "russia": ["SVO", "DME"],    # Moscow airports
        "turkey": ["IST"],           # Istanbul
        "egypt": ["CAI"],            # Cairo
        "south africa": ["JNB", "CPT"],  # Johannesburg and Cape Town
        "argentina": ["EZE"],        # Buenos Aires
        "chile": ["SCL"],            # Santiago
        "peru": ["LIM"],             # Lima
        "colombia": ["BOG"],         # Bogotá
    }
    
    location_lower = location_text.lower()
    for key, codes in static_mapping.items():
        if key in location_lower:
            LOGGER.info("Found static mapping for '%s': %s", location_text, codes)
            return codes
    
    # Note: API key should be in .env file as SONAR_API_KEY
    api_key = os.getenv("SONAR_API_KEY")
    if not api_key:
        LOGGER.warning("SONAR_API_KEY not found in .env file, using empty fallback")
        return []
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        query = f"""What are all the major airport codes (IATA codes) for flights to/from {location_text}? 
        Include international airports, major domestic airports, and nearby alternatives.
        For example, if the location is "Shanghai", include PVG (Shanghai Pudong) and SHA (Shanghai Hongqiao).
        If it's "New York", include JFK, LGA, and EWR.
        Return only the 3-letter IATA codes in a simple comma-separated list format like: PVG, SHA, JFK"""
        
        data = {
            "model": "sonar-pro",  # Faster model, good for airport code lookup
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.1,
            "max_tokens": 150
        }
        
        LOGGER.info("Researching airport codes for location: %s", location_text)
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=data,
            timeout=60  # Increased timeout for deep research
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Extract 3-letter airport codes from the response
            import re
            codes = re.findall(r'\b[A-Z]{3}\b', content)
            # Remove duplicates while preserving order
            unique_codes = []
            for code in codes:
                if code not in unique_codes:
                    unique_codes.append(code)
            
            LOGGER.info("Found airport codes for '%s': %s", location_text, unique_codes)
            return unique_codes[:5]  # Limit to top 5 codes
            
        else:
            LOGGER.warning("Perplexity API error: %s - %s", response.status_code, response.text)
            return []
            
    except Exception as e:
        LOGGER.exception("Error researching locations with Perplexity: %s", str(e))
        return []


async def enhanced_search_with_location_research(entities: FlightEntities, original_text: str) -> Dict[str, Any]:
    """Enhanced search that uses Perplexity to find all possible airports for ambiguous locations."""
    
    # Research origin if it's missing or ambiguous
    origin_codes = []
    if not entities.origin and "from" in original_text.lower():
        # Extract the origin from text
        import re
        m_from = re.search(r"\bfrom\s+([a-zA-Z\s]+?)(?=\s+to\b|$)", original_text.lower())
        if m_from:
            origin_text = m_from.group(1).strip()
            origin_codes = await research_locations_with_perplexity(origin_text)
    elif entities.origin:
        origin_codes = [entities.origin]
    
    # Research destination - always use Perplexity as default
    destination_codes = []
    if "to" in original_text.lower():
        # Extract the destination from text and research it
        import re
        m_to = re.search(r"\bto\s+([a-zA-Z\s]+)", original_text.lower())
        if m_to:
            destination_text = m_to.group(1).strip()
            destination_codes = await research_locations_with_perplexity(destination_text)
    
    # If no codes found from text extraction, but we have a destination entity, research it too
    if not destination_codes and entities.destination:
        # Research the destination entity (in case it's something like "CHI" that needs resolution)
        destination_codes = await research_locations_with_perplexity(entities.destination)
    
    # If no codes found through research, fall back to static mapping
    if not origin_codes and not destination_codes:
        LOGGER.info("No location research results, falling back to regular search")
        return await call_search_flights(entities)
    
    # Use defaults if one side is missing
    if not origin_codes:
        origin_codes = [entities.origin or "SFO"]
    if not destination_codes:  
        destination_codes = [entities.destination or "LAX"]
    
    LOGGER.info("Enhanced search with origins=%s, destinations=%s", origin_codes, destination_codes)
    
    # Search all combinations and collect results
    all_results = []
    search_count = 0
    max_searches = 10  # Limit total API calls
    
    for origin in origin_codes:
        for destination in destination_codes:
            if search_count >= max_searches:
                break
                
            if origin == destination:
                continue  # Skip same origin/destination
                
            # Create modified entities for this combination
            modified_entities = FlightEntities(**{
                **entities.model_dump(),
                "origin": origin,
                "destination": destination
            })
            
            try:
                result = await call_search_flights(modified_entities)
                flights = result.get("flights", [])
                
                if flights:  # Only include results with actual flights
                    all_results.append({
                        "route": f"{origin} → {destination}",
                        "origin": origin,
                        "destination": destination,
                        "flights": flights[:5],  # Top 5 flights per route
                        "total_results": result.get("total_results", 0)
                    })
                    
                search_count += 1
                LOGGER.info("Search %d: %s → %s found %d flights", search_count, origin, destination, len(flights))
                
            except Exception as e:
                LOGGER.warning("Search failed for %s → %s: %s", origin, destination, str(e))
                continue
                
        if search_count >= max_searches:
            break
    
    # Compile final results
    all_flights = []
    for result in all_results:
        all_flights.extend(result["flights"])
    
    return {
        "enhanced_search": True,
        "route_combinations": len(all_results),
        "routes": all_results,
        "flights": all_flights,
        "total_results": len(all_flights)
    }


def main():
    print("Flight Chat. Type 'quit' to exit.")
    while True:
        try:
            user = input("You: ").strip()
        except EOFError:
            break
        if user.lower() in {"quit", "exit"}:
            break

        LOGGER.info("User: %s", user)
        ent = detect_intent_entities(user)
        ent = _normalize_entities_from_text(user, ent)
        LOGGER.info("Normalized entities: %s", ent.model_dump())
        if ent.intent == "search_flights":
            import anyio
            
            # Use enhanced search with Perplexity as the default for location resolution
            needs_research = (
                not ent.origin or not ent.destination or 
                # Always research if we detect city names (even if they resolve to airport codes)
                any(city in user.lower() for city in [
                    "chicago", "shanghai", "beijing", "tokyo", "london", "paris", "new york", "los angeles",
                    "boston", "seattle", "miami", "atlanta", "denver", "phoenix", "las vegas", "washington",
                    "bangkok", "mumbai", "delhi", "singapore", "hong kong", "manila", "seoul", "kuala lumpur",
                    "jakarta", "amsterdam", "frankfurt", "zurich", "madrid", "barcelona", "rome", "milan",
                    "moscow", "istanbul", "budapest", "prague", "vienna", "berlin", "munich", "copenhagen",
                    "stockholm", "oslo", "helsinki", "warsaw", "athens", "lisbon", "dubai", "doha",
                    "abu dhabi", "cairo", "johannesburg", "cape town", "rio", "sao paulo", "buenos aires",
                    "santiago", "sydney", "melbourne", "toronto", "vancouver", "montreal", "brazil", "china",
                    "japan", "india", "korea", "thailand", "germany", "italy", "spain", "netherlands",
                    "switzerland", "australia", "canada", "uae", "russia", "turkey", "egypt", "south africa",
                    "argentina", "chile", "peru", "colombia", "philippines", "vietnam", "indonesia"
                ]) or
                # Research if destination appears to be invalid/ambiguous 3-letter code
                (ent.destination and len(ent.destination) == 3 and ent.destination in [
                    'CHI', 'NYC', 'LA', 'SF', 'DC', 'ATL', 'DEN', 'PHX', 'LAS', 'SEA', 'BOS', 'MIA'
                ])
            )
            
            if needs_research:
                LOGGER.info("Using enhanced search with location research")
                data = anyio.run(lambda: enhanced_search_with_location_research(ent, user))
            else:
                LOGGER.info("Using regular search")
                data = anyio.run(lambda: call_search_flights(ent))
                
            summary = _summarize(data, ent) if data else "No results."
            LOGGER.info("Summary generated (%s chars)", len(summary))
            print("Agent:", summary)
        elif ent.intent == "get_flight_pricing":
            import anyio
            data = anyio.run(lambda: call_get_pricing(ent))
            summary = _summarize(data, ent) if data else "No pricing."
            LOGGER.info("Pricing summary generated (%s chars)", len(summary))
            print("Agent:", summary)
        else:
            # Regular chitchat fallback
            client = _openai_client()
            completion = client.responses.create(
                model="gpt-5",
                instructions="You are a helpful flight assistant.",
                input=user,
            )
            reply = getattr(completion, "output_text", None) or ""
            LOGGER.info("Chitchat reply generated (%s chars)", len(reply))
            print("Agent:", reply)


if __name__ == "__main__":
    main()


