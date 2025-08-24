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
    logger = logging.getLogger("hotel_chat")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
    os.makedirs(log_dir, exist_ok=True)
    file_path = os.path.join(log_dir, "hotel_chat.log")

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

    logger.info("Initialized hotel chat logging at %s", file_path)
    return logger


LOGGER = _init_logging()


class HotelEntities(BaseModel):
    intent: str = "chitchat"  # search_hotels | get_hotel_pricing | chitchat
    # Search params
    city: Optional[str] = None
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    rooms: Optional[int] = None
    hotel_class: Optional[str] = None
    max_price: Optional[float] = None
    amenities: Optional[List[str]] = None
    sort_by: Optional[str] = None
    max_results: Optional[int] = None
    # Pricing params
    hotel_id: Optional[str] = None
    room_type: Optional[str] = None


SYSTEM_DETECT = (
    "Extract intent and entities for a hotel tool. Output ONLY JSON: {intent, entities}.\n"
    "- intent: one of 'search_hotels', 'get_hotel_pricing', 'chitchat'\n"
    "- entities: may include city, check_in_date, check_out_date, adults, children, rooms, hotel_class, max_price, amenities, sort_by, max_results, hotel_id, room_type\n"
    "Rules:\n"
    "1) City: Extract destination city or location (e.g., 'New York', 'Paris', 'Tokyo', 'Los Angeles').\n"
    "2) Dates: parse natural phrases relative to today's date (YYYY-MM-DD):\n"
    "   - 'today' => check_in_date = today.\n"
    "   - 'tomorrow' => check_in_date = today + 1 day.\n"
    "   - 'next week' => check_in_date = today + 7 days.\n"
    "   - 'MM/DD' => check_in_date = current_year-MM-DD.\n"
    "   - 'MM/DD-MM/DD' => check_in_date = first date, check_out_date = second date (current year).\n"
    "   - 'for 2 nights' => check_out_date = check_in_date + 2 days.\n"
    "   - If only check_in provided, assume 1 night stay.\n"
    "3) Guests: extract number of adults, children, rooms from phrases like '2 adults', '1 child', '2 rooms'.\n"
    "4) Hotel class: extract star ratings like '4 star', '5-star', 'luxury' (map to '5'), 'budget' (map to '3').\n"
    "5) Price: extract max budget like 'under $200', 'less than 150' (extract numeric value).\n"
    "6) Amenities: extract desired features like 'pool', 'wifi', 'gym', 'spa', 'breakfast', 'parking'.\n"
    "7) Sort preferences: 'cheapest' -> sort_by='price', 'best rated' -> sort_by='rating', 'closest' -> sort_by='distance'.\n"
    "8) If unsure, leave a field null. Do NOT fabricate values.\n"
    "Examples (assume today is 2025-01-15; do not copy these to output):\n"
    " - Input: 'hotels in New York tomorrow for 2 nights'\n"
    "   Output: {\"intent\":\"search_hotels\",\"entities\":{\"city\":\"New York\",\"check_in_date\":\"2025-01-16\",\"check_out_date\":\"2025-01-18\"}}\n"
    " - Input: 'find 4 star hotels in Paris under $300 with pool and gym'\n"
    "   Output: {\"intent\":\"search_hotels\",\"entities\":{\"city\":\"Paris\",\"hotel_class\":\"4\",\"max_price\":300,\"amenities\":[\"pool\",\"gym\"]}}\n"
    " - Input: 'get pricing for hotel abc123'\n"
    "   Output: {\"intent\":\"get_hotel_pricing\",\"entities\":{\"hotel_id\":\"abc123\"}}\n"
)


def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    return OpenAI(api_key=api_key)


def detect_intent_entities(message: str) -> HotelEntities:
    client = _openai_client()
    completion = client.responses.create(
        model="gpt-5",
        instructions=SYSTEM_DETECT,
        input=message,
    )
    text = getattr(completion, "output_text", None) or "{}"
    try:
        data = json.loads(text)
        ent = HotelEntities(**{
            "intent": data.get("intent", "chitchat"),
            **(data.get("entities") or {}),
        })
        LOGGER.info("Detected intent=%s, entities=%s", ent.intent, {k: v for k, v in ent.model_dump().items() if k != 'intent'})
        return ent
    except Exception:
        LOGGER.exception("Failed to parse intent/entities from model output: %s", text)
        return HotelEntities()


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
                LOGGER.warning("Tool returned non-JSON text; wrapping as raw. text_len=%s, content: %s", len(text), text[:100])
                return {"raw": text}
    return None


async def call_search_hotels(entities: HotelEntities) -> Dict[str, Any]:
    from datetime import date, timedelta
    
    # Set defaults for required fields
    today = date.today()
    check_in = entities.check_in_date or (today + timedelta(days=1)).strftime("%Y-%m-%d")
    check_out = entities.check_out_date or (date.fromisoformat(check_in) + timedelta(days=1)).strftime("%Y-%m-%d")
    
    args = {
        "city": entities.city or "New York",
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": entities.adults or 2,
        "children": entities.children or 0,
        "rooms": entities.rooms or 1,
        "hotel_class": entities.hotel_class,
        "max_price": entities.max_price,
        "amenities": entities.amenities,
        "sort_by": entities.sort_by or "rating",
        "max_results": entities.max_results or 10,
    }
    LOGGER.info("Calling search_hotels with args=%s", args)
    server = StdioServerParameters(command="uv", args=["run", "python", "fast_server.py"])
    async with stdio_client(server) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            result = await s.call_tool("search_hotels", {"params": args})
            data = _extract_json_from_result(result) or {}
            if isinstance(data, dict):
                # Log first 1-2 hotels for debugging
                hotels = data.get("hotels", []) or []
                sample = [
                    {
                        "hotel_id": h.get("hotel_id"),
                        "name": h.get("name"),
                        "price_range": h.get("price_range"),
                        "star_rating": h.get("star_rating"),
                    }
                    for h in hotels[:2]
                ]
                LOGGER.info(
                    "search_hotels returned %s hotels (total_results=%s), sample=%s",
                    len(hotels), data.get("total_results"), sample,
                )
                return data
            LOGGER.info("search_hotels returned non-dict payload type=%s", type(data).__name__)
            return {"data": data}


async def call_get_hotel_pricing(entities: HotelEntities) -> Dict[str, Any]:
    from datetime import date, timedelta
    
    hotel_id = entities.hotel_id
    if not hotel_id:
        LOGGER.warning("No hotel_id provided for pricing request")
        return {"error": "hotel_id required for pricing"}
    
    # Set defaults for required fields
    today = date.today()
    check_in = entities.check_in_date or (today + timedelta(days=1)).strftime("%Y-%m-%d")
    check_out = entities.check_out_date or (date.fromisoformat(check_in) + timedelta(days=1)).strftime("%Y-%m-%d")
    
    args = {
        "hotel_id": hotel_id,
        "room_type": entities.room_type,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": entities.adults or 2,
        "children": entities.children or 0,
        "rooms": entities.rooms or 1,
    }
    LOGGER.info("Calling get_hotel_pricing with args=%s", args)
    server = StdioServerParameters(command="uv", args=["run", "python", "fast_server.py"])
    async with stdio_client(server) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            result = await s.call_tool("get_hotel_pricing", {"params": args})
            data = _extract_json_from_result(result) or {}
            LOGGER.info("get_hotel_pricing returned data for hotel_id=%s", hotel_id)
            return {"pricing": data}


def _summarize(data: Dict[str, Any], ent: HotelEntities) -> str:
    """Summarize hotel results while preserving key search criteria."""
    client = _openai_client()
    
    if ent.intent == "search_hotels":
        # Hotel search summary
        city = ent.city or data.get("city", "")
        check_in = ent.check_in_date or data.get("check_in_date", "")
        check_out = ent.check_out_date or data.get("check_out_date", "")
        
        # Compact payload: only include the first few hotels with key details
        hotels = data.get("hotels") or []
        compact = [
            {
                "hotel_id": h.get("hotel_id"),
                "name": h.get("name"),
                "location": h.get("location", {}).get("address"),
                "star_rating": h.get("star_rating"),
                "review": h.get("review"),
                "price_range": h.get("price_range"),
                "amenities": [a.get("name") for a in h.get("amenities", []) if a.get("available")],
                "rooms": h.get("rooms", [])[:2],  # First 2 room types
            }
            for h in hotels[:5]
        ]

        instructions = (
            f"Summarize hotels for {city}.\n"
            + (f"Dates: {check_in} to {check_out}.\n" if check_in and check_out else "")
            + "IMPORTANT: Show the BEST 5 HOTEL OPTIONS sorted by value (price and rating).\n"
            + "For each hotel include: Name, Star Rating, Price Range, Location, Key Amenities, Best Room Option.\n"
            + "Format clearly for easy comparison. Highlight unique features and value propositions."
        )

        payload = json.dumps({
            "city": city,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "hotels": compact,
            "total_results": data.get("total_results"),
        })

        LOGGER.info("Summarizer for %s hotels in %s from %s to %s", len(compact), city, check_in, check_out)

    else:
        # Hotel pricing summary
        pricing_data = data.get("pricing", {})
        
        instructions = (
            "Summarize hotel pricing information.\n"
            "IMPORTANT: Clearly show the pricing breakdown, cancellation policy, and booking conditions.\n"
            "Include: Total Price, Price per Night, Taxes/Fees, Cancellation Terms, Room Details.\n"
            "Format for easy understanding of total costs and terms."
        )

        payload = json.dumps(pricing_data)
        LOGGER.info("Pricing summarizer for hotel_id=%s", pricing_data.get("hotel_id"))

    completion = client.responses.create(
        model="gpt-5",
        instructions=instructions,
        input=payload,
    )
    return getattr(completion, "output_text", None) or ""


def _normalize_entities_from_text(user_text: str, ent: HotelEntities) -> HotelEntities:
    """Best-effort normalization: map city names and normalize date ranges."""
    import re
    from datetime import datetime, timedelta

    text = user_text.lower()

    # Extract city names
    if not ent.city:
        city_patterns = [
            r"\bin\s+([a-zA-Z\s]+?)(?=\s+(?:under|with|on|for|from|tomorrow|today|next|\d|$))",
            r"hotels?\s+in\s+([a-zA-Z\s]+?)(?=\s+(?:under|with|on|for|from|tomorrow|today|next|\d|$))",
            r"find\s+(?:hotels?\s+in\s+)?([a-zA-Z\s]+?)(?=\s+(?:under|with|hotels?|on|for|from|tomorrow|today|next|\d|$))",
            r"(?:cheapest|best|luxury|budget)\s+hotels?\s+in\s+([a-zA-Z\s]+?)(?=\s*$)",
        ]
        for pattern in city_patterns:
            match = re.search(pattern, text)
            if match:
                city = match.group(1).strip().title()
                if len(city) > 2:  # Avoid single letters
                    ent.city = city
                    break

    # Natural date words
    now = datetime.now()
    if not ent.check_in_date:
        if "today" in text:
            ent.check_in_date = now.strftime("%Y-%m-%d")
        elif "tomorrow" in text:
            ent.check_in_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "next week" in text:
            ent.check_in_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")

    # Extract nights duration
    if ent.check_in_date and not ent.check_out_date:
        nights_match = re.search(r"(\d+)\s*nights?", text)
        if nights_match:
            nights = int(nights_match.group(1))
            check_in = datetime.fromisoformat(ent.check_in_date)
            ent.check_out_date = (check_in + timedelta(days=nights)).strftime("%Y-%m-%d")
        else:
            # Default to 1 night if not specified
            check_in = datetime.fromisoformat(ent.check_in_date)
            ent.check_out_date = (check_in + timedelta(days=1)).strftime("%Y-%m-%d")

    # Date range parsing like 09/12-09/20
    if not ent.check_in_date or not ent.check_out_date:
        m = re.search(r"(\d{1,2})\/(\d{1,2})\s*[-–]\s*(\d{1,2})\/(\d{1,2})", text)
        if m:
            mm1, dd1, mm2, dd2 = m.groups()
            year = now.year
            try:
                check_in = datetime(year, int(mm1), int(dd1)).strftime("%Y-%m-%d")
                check_out = datetime(year, int(mm2), int(dd2)).strftime("%Y-%m-%d")
                if not ent.check_in_date:
                    ent.check_in_date = check_in
                if not ent.check_out_date:
                    ent.check_out_date = check_out
            except Exception:
                pass

    # Extract guests
    if not ent.adults:
        adults_match = re.search(r"(\d+)\s*adults?", text)
        if adults_match:
            ent.adults = int(adults_match.group(1))

    if not ent.children:
        children_match = re.search(r"(\d+)\s*(?:children?|kids?|child)", text)
        if children_match:
            ent.children = int(children_match.group(1))

    if not ent.rooms:
        rooms_match = re.search(r"(\d+)\s*rooms?", text)
        if rooms_match:
            ent.rooms = int(rooms_match.group(1))

    # Extract hotel class
    if not ent.hotel_class:
        star_match = re.search(r"(\d)\s*star", text)
        if star_match:
            ent.hotel_class = star_match.group(1)
        elif "luxury" in text:
            ent.hotel_class = "5"
        elif "budget" in text:
            ent.hotel_class = "3"

    # Extract max price
    if not ent.max_price:
        price_match = re.search(r"under\s*\$?(\d+)|less\s+than\s*\$?(\d+)|budget\s*\$?(\d+)", text)
        if price_match:
            price = next(g for g in price_match.groups() if g)
            ent.max_price = float(price)

    # Extract amenities
    if not ent.amenities:
        amenity_keywords = ["pool", "wifi", "gym", "spa", "breakfast", "parking", "fitness", "restaurant"]
        found_amenities = [amenity for amenity in amenity_keywords if amenity in text]
        if found_amenities:
            ent.amenities = found_amenities

    # Extract sort preference
    if not ent.sort_by:
        if "cheapest" in text or "lowest price" in text:
            ent.sort_by = "price"
        elif "best rated" in text or "highest rated" in text:
            ent.sort_by = "rating"
        elif "closest" in text or "nearest" in text:
            ent.sort_by = "distance"

    return ent


async def enhanced_search_with_location_research(entities: HotelEntities, original_text: str) -> Dict[str, Any]:
    """Enhanced search that uses Perplexity to find popular areas/districts in a city for hotel recommendations."""
    
    # Research popular areas/districts for the city
    api_key = os.getenv("SONAR_API_KEY")
    if api_key and entities.city:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            query = f"""What are the best areas/districts to stay in {entities.city} for tourists? 
            List the top 3-5 areas with brief descriptions of what makes each area good for different types of travelers.
            For example, if the city is "New York", mention areas like Midtown Manhattan (business/theatre), SoHo (shopping/trendy), Upper East Side (museums/upscale), etc.
            Keep it concise - just area names and key highlights."""
            
            data = {
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 200
            }
            
            LOGGER.info("Researching popular areas for city: %s", entities.city)
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # Log the full Perplexity response for debugging and analysis
                LOGGER.info("Perplexity research query: %s", query)
                LOGGER.info("Full Perplexity response for '%s': %s", entities.city, content)
                LOGGER.info("Found area recommendations for '%s': %s", entities.city, content[:200])
                
                # Get regular search results
                search_result = await call_search_hotels(entities)
                
                # Add area insights to the result
                search_result["area_insights"] = content
                search_result["enhanced_search"] = True
                
                return search_result
                
            else:
                LOGGER.warning("Perplexity API error for city '%s': status=%d, response=%s", entities.city, response.status_code, response.text[:500])
                
        except Exception as e:
            LOGGER.error("Perplexity location research failed for city '%s': %s", entities.city, str(e))
    else:
        if not api_key:
            LOGGER.info("Skipping location research: SONAR_API_KEY not found")
        elif not entities.city:
            LOGGER.info("Skipping location research: no city in entities")
    
    # Fallback to regular search
    LOGGER.info("Using regular search (without location enhancement)")
    return await call_search_hotels(entities)


def main():
    print("Hotel Chat. Type 'quit' to exit.")
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
        
        if ent.intent == "search_hotels":
            import anyio
            
            # Use enhanced search with area insights for better recommendations
            data = anyio.run(lambda: enhanced_search_with_location_research(ent, user))
            summary = _summarize(data, ent) if data else "No results."
            LOGGER.info("Summary generated (%s chars)", len(summary))
            print("Agent:", summary)
            
        elif ent.intent == "get_hotel_pricing":
            import anyio
            data = anyio.run(lambda: call_get_hotel_pricing(ent))
            summary = _summarize(data, ent) if data else "No pricing."
            LOGGER.info("Pricing summary generated (%s chars)", len(summary))
            print("Agent:", summary)
            
        else:
            # Regular chitchat fallback
            client = _openai_client()
            completion = client.responses.create(
                model="gpt-5",
                instructions="You are a helpful hotel assistant.",
                input=user,
            )
            reply = getattr(completion, "output_text", None) or ""
            LOGGER.info("Chitchat reply generated (%s chars)", len(reply))
            print("Agent:", reply)


if __name__ == "__main__":
    main()