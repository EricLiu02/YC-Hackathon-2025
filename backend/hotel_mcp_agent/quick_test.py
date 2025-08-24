#!/usr/bin/env python3
"""
Quick test of specific hotel chat inputs
"""

from demo_chat import simulate_openai_intent_detection, simulate_hotel_search, simulate_hotel_pricing, simulate_openai_summarize, simulate_chitchat

def quick_test(user_input: str):
    """Test a single input quickly"""
    print(f"🧪 Testing: '{user_input}'")
    print("=" * 50)
    
    # Process the input
    detection_result = simulate_openai_intent_detection(user_input)
    intent = detection_result["intent"]
    entities = detection_result["entities"]
    
    print(f"📝 Intent: {intent}")
    filtered_entities = {k: v for k, v in entities.items() if v is not None and v != "chitchat"}
    if filtered_entities:
        print(f"📋 Entities: {filtered_entities}")
    
    # Get response
    if intent == "search_hotels":
        data = simulate_hotel_search(entities)
        summary = simulate_openai_summarize(data, intent)
    elif intent == "get_hotel_pricing":
        data = simulate_hotel_pricing(entities)
        summary = simulate_openai_summarize(data, intent)
    else:
        summary = simulate_chitchat(user_input)
    
    print(f"\n🤖 Agent Response:")
    print(summary)
    print()

if __name__ == "__main__":
    # Test a few examples quickly
    examples = [
        "Find luxury hotels in Las Vegas for next week",
        "cheapest hotels in Miami with pool",
        "Get pricing for hotel demo_hotel_2"
    ]
    
    for example in examples:
        quick_test(example)
        print("-" * 60)
        print()