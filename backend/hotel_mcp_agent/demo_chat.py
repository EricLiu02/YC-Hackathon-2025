#!/usr/bin/env python3
"""
Demo hotel chat wrapper that simulates the full functionality without external dependencies
"""

import json
from standalone_test import HotelEntities, normalize_entities_from_text

def simulate_openai_intent_detection(message: str) -> dict:
    """Simulate GPT-5 intent detection"""
    text = message.lower()
    
    # Simple rule-based intent detection for demo
    if any(word in text for word in ["pricing", "price for hotel", "cost of hotel"]):
        intent = "get_hotel_pricing"
    elif any(word in text for word in ["find", "search", "hotel", "stay"]):
        intent = "search_hotels" 
    else:
        intent = "chitchat"
    
    # Extract basic entities using our tested logic
    entities = HotelEntities(intent=intent)
    entities = normalize_entities_from_text(message, entities)
    
    return {
        "intent": intent,
        "entities": entities.model_dump()
    }

def simulate_hotel_search(entities: dict) -> dict:
    """Simulate hotel search results"""
    city = entities.get("city", "Demo City")
    check_in = entities.get("check_in_date", "2025-01-15")
    check_out = entities.get("check_out_date", "2025-01-16")
    
    return {
        "hotels": [
            {
                "hotel_id": "demo_hotel_1",
                "name": f"Grand {city} Hotel",
                "location": {"address": f"123 Main St, {city}"},
                "star_rating": 4,
                "review": {"rating": 4.5, "total_reviews": 1250},
                "price_range": "$150-300 per night",
                "amenities": [{"name": "Pool", "available": True}, {"name": "WiFi", "available": True}],
                "rooms": [{
                    "room_id": "deluxe_1",
                    "room_name": "Deluxe Room",
                    "price_per_night": 200,
                    "total_price": 200,
                    "currency": "USD"
                }]
            },
            {
                "hotel_id": "demo_hotel_2", 
                "name": f"Budget Inn {city}",
                "location": {"address": f"456 Oak Ave, {city}"},
                "star_rating": 3,
                "review": {"rating": 3.8, "total_reviews": 890},
                "price_range": "$80-150 per night",
                "amenities": [{"name": "WiFi", "available": True}, {"name": "Breakfast", "available": True}],
                "rooms": [{
                    "room_id": "standard_1",
                    "room_name": "Standard Room", 
                    "price_per_night": 120,
                    "total_price": 120,
                    "currency": "USD"
                }]
            }
        ],
        "total_results": 2,
        "city": city,
        "check_in_date": check_in,
        "check_out_date": check_out
    }

def simulate_hotel_pricing(entities: dict) -> dict:
    """Simulate hotel pricing results"""
    hotel_id = entities.get("hotel_id", "demo_hotel_1")
    
    return {
        "pricing": {
            "hotel_id": hotel_id,
            "hotel_name": "Grand Demo Hotel",
            "room_type": "Deluxe Room",
            "pricing": {
                "base_price": 200.0,
                "taxes_and_fees": 30.0,
                "total_price": 230.0,
                "currency": "USD",
                "price_per_night": 230.0,
                "total_nights": 1
            },
            "cancellation_policy": {
                "is_refundable": True,
                "policy_description": "Free cancellation until 24 hours before check-in"
            }
        }
    }

def simulate_openai_summarize(data: dict, intent: str) -> str:
    """Simulate GPT-5 result summarization"""
    if intent == "search_hotels":
        hotels = data.get("hotels", [])
        city = data.get("city", "Unknown")
        check_in = data.get("check_in_date", "")
        check_out = data.get("check_out_date", "")
        
        summary = f"🏨 Found {len(hotels)} hotels in {city}"
        if check_in and check_out:
            summary += f" from {check_in} to {check_out}"
        summary += ":\n\n"
        
        for i, hotel in enumerate(hotels[:5], 1):
            name = hotel.get("name", "Unknown Hotel")
            stars = "⭐" * hotel.get("star_rating", 0)
            rating = hotel.get("review", {}).get("rating", 0)
            price_range = hotel.get("price_range", "Price not available")
            amenities = [a.get("name") for a in hotel.get("amenities", []) if a.get("available")]
            
            summary += f"{i}. **{name}** {stars}\n"
            summary += f"   📍 {hotel.get('location', {}).get('address', 'Address not available')}\n"
            summary += f"   ⭐ Rating: {rating}/5\n"
            summary += f"   💰 {price_range}\n"
            summary += f"   🏊 Amenities: {', '.join(amenities[:3])}\n\n"
        
        return summary
    
    elif intent == "get_hotel_pricing":
        pricing_data = data.get("pricing", {})
        hotel_name = pricing_data.get("hotel_name", "Unknown Hotel")
        room_type = pricing_data.get("room_type", "Standard Room")
        pricing = pricing_data.get("pricing", {})
        
        summary = f"💰 Pricing for {hotel_name} - {room_type}:\n\n"
        summary += f"Base Price: ${pricing.get('base_price', 0):.2f}\n"
        summary += f"Taxes & Fees: ${pricing.get('taxes_and_fees', 0):.2f}\n"
        summary += f"**Total: ${pricing.get('total_price', 0):.2f}** per night\n\n"
        
        cancellation = pricing_data.get("cancellation_policy", {})
        if cancellation.get("is_refundable"):
            summary += "✅ " + cancellation.get("policy_description", "Refundable")
        else:
            summary += "❌ Non-refundable"
            
        return summary
    
    return "No summary available."

def simulate_chitchat(message: str) -> str:
    """Simulate chitchat responses"""
    responses = {
        "hello": "Hi! I'm your hotel assistant. I can help you search for hotels or get pricing information.",
        "help": "I can help you with:\n• Hotel searches: 'Find hotels in Paris tomorrow'\n• Pricing: 'Get pricing for hotel abc123'\n• Just ask me naturally!",
        "thanks": "You're welcome! Let me know if you need help finding hotels.",
    }
    
    text = message.lower()
    for key, response in responses.items():
        if key in text:
            return response
    
    return "I'm a hotel assistant. Try asking me to find hotels in a city or get pricing for a specific hotel!"

def demo_chat():
    """Run the demo hotel chat"""
    print("🏨 Hotel Chat Demo (Simulated)")
    print("=" * 50)
    print("This demo simulates the full chat wrapper functionality.")
    print("Try these examples:")
    print("• Find hotels in Paris tomorrow for 2 nights")
    print("• 4 star hotels in New York under $200")
    print("• Get pricing for hotel demo_hotel_1")
    print("• Type 'quit' to exit")
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            break
        
        if user_input.lower() in ["quit", "exit"]:
            break
        
        print(f"\n🤖 Processing: '{user_input}'")
        
        # Step 1: Intent detection
        detection_result = simulate_openai_intent_detection(user_input)
        intent = detection_result["intent"]
        entities = detection_result["entities"]
        
        print(f"📝 Intent: {intent}")
        print(f"📋 Entities: {json.dumps({k: v for k, v in entities.items() if v is not None}, indent=2)}")
        
        # Step 2: Execute based on intent
        if intent == "search_hotels":
            data = simulate_hotel_search(entities)
            summary = simulate_openai_summarize(data, intent)
        elif intent == "get_hotel_pricing":
            data = simulate_hotel_pricing(entities)
            summary = simulate_openai_summarize(data, intent)
        else:
            summary = simulate_chitchat(user_input)
        
        print(f"\n🤖 Agent: {summary}")
        print("-" * 50)

if __name__ == "__main__":
    demo_chat()