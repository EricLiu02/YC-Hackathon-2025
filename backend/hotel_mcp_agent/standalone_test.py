#!/usr/bin/env python3
"""
Standalone test for hotel chat wrapper entity extraction logic
"""

import json
import re
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel


class HotelEntities(BaseModel):
    intent: str = "chitchat"
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
    hotel_id: Optional[str] = None
    room_type: Optional[str] = None


def normalize_entities_from_text(user_text: str, ent: HotelEntities) -> HotelEntities:
    """Extract hotel entities from natural language text"""
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

    # Extract hotel ID for pricing requests
    if not ent.hotel_id:
        hotel_id_match = re.search(r"hotel[_\s]+([a-zA-Z0-9]+)", text)
        if hotel_id_match:
            ent.hotel_id = hotel_id_match.group(1)
            ent.intent = "get_hotel_pricing"
    
    # Set intent based on content
    if not ent.intent or ent.intent == "chitchat":
        if ent.hotel_id:
            ent.intent = "get_hotel_pricing"
        elif any([ent.city, "hotel" in text, "find" in text, "search" in text]):
            ent.intent = "search_hotels"

    return ent


def test_entity_extraction():
    """Test entity extraction functionality"""
    
    print("🏨 Hotel Chat Wrapper Entity Extraction Test")
    print("=" * 60)
    
    test_cases = [
        {
            "input": "Find hotels in Paris tomorrow for 2 nights",
            "expected": {"city": "Paris", "intent": "search_hotels"}
        },
        {
            "input": "4 star hotels in New York under $200 with pool and gym",
            "expected": {"city": "New York", "hotel_class": "4", "max_price": 200.0, "amenities": ["pool", "gym"]}
        },
        {
            "input": "Hotels in Tokyo next week for 3 adults and 1 child",
            "expected": {"city": "Tokyo", "adults": 3, "children": 1}
        },
        {
            "input": "Luxury hotels in London 01/15-01/18",
            "expected": {"city": "London", "hotel_class": "5"}
        },
        {
            "input": "Budget hotels in San Francisco with wifi and breakfast",
            "expected": {"city": "San Francisco", "hotel_class": "3", "amenities": ["wifi", "breakfast"]}
        },
        {
            "input": "Find 2 rooms in Miami for 4 adults",
            "expected": {"city": "Miami", "rooms": 2, "adults": 4}
        },
        {
            "input": "Get pricing for hotel abc123",
            "expected": {"hotel_id": "abc123", "intent": "get_hotel_pricing"}
        },
        {
            "input": "cheapest hotels in Las Vegas",
            "expected": {"city": "Las Vegas", "sort_by": "price"}
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case['input']}'")
        
        # Extract entities
        entities = HotelEntities()
        result = normalize_entities_from_text(test_case["input"], entities)
        
        # Show what was extracted
        extracted = {k: v for k, v in result.model_dump().items() if v is not None and v != "chitchat"}
        print(f"   Extracted: {json.dumps(extracted, indent=14)}")
        
        # Check if expected values are present
        expected = test_case["expected"]
        test_passed = True
        for key, expected_value in expected.items():
            actual_value = getattr(result, key)
            if actual_value != expected_value:
                print(f"   ❌ FAIL: Expected {key}={expected_value}, got {actual_value}")
                test_passed = False
        
        if test_passed:
            print(f"   ✅ PASS")
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Test Results")
    print("=" * 20)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    return failed == 0


def test_date_parsing():
    """Test specific date parsing scenarios"""
    
    print(f"\n🗓️  Date Parsing Tests")
    print("=" * 30)
    
    test_cases = [
        "hotels tomorrow for 2 nights",
        "hotels next week for 3 nights", 
        "hotels 01/20-01/25",
        "hotels today for 1 night"
    ]
    
    for text in test_cases:
        entities = HotelEntities()
        result = normalize_entities_from_text(text, entities)
        print(f"'{text}'")
        print(f"  Check-in: {result.check_in_date}")
        print(f"  Check-out: {result.check_out_date}")
        print()


if __name__ == "__main__":
    success = test_entity_extraction()
    test_date_parsing()
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
    
    print(f"\n💡 Next Steps:")
    print("   1. Fix any failed tests above")
    print("   2. Set up environment variables (OPENAI_API_KEY, SONAR_API_KEY)")
    print("   3. Install dependencies: pip install openai python-dotenv requests")
    print("   4. Test MCP server: python -m hotel_mcp_agent")
    print("   5. Run full chat: python chat_wrapper.py")