#!/usr/bin/env python3
"""Interactive chat with Claude about budgets."""

import asyncio
import sys
sys.path.insert(0, 'backend/budgeteer_mcp_agent')

from fast_server import (
    get_demo_trip_plan, 
    get_demo_daily_spend_estimates,
    analyze_budget_with_claude,
    optimize_budget_with_claude
)

async def chat():
    # Load demo data
    trip = await get_demo_trip_plan()
    daily = await get_demo_daily_spend_estimates()
    
    print("🤖 Claude Budget Assistant")
    print("=" * 40)
    print("I have your London trip loaded. Ask me anything!")
    print("Commands: 'analyze', 'optimize [budget]', 'quit'\n")
    
    while True:
        query = input("You: ").strip().lower()
        
        if query == 'quit':
            break
            
        elif query == 'analyze' or 'analyze' in query:
            print("Claude: Analyzing your trip budget...")
            result = await analyze_budget_with_claude(trip, daily, query)
            if result['status'] == 'ok':
                analysis = result['result']
                print(f"\n💰 Total Cost: ${analysis['summary']['total_trip_cost']}")
                print(f"📊 Remaining: ${analysis['summary']['remaining_budget']}")
                print("\n⚠️  Risks:")
                for risk in analysis['risks']:
                    print(f"  - {risk}")
                print("\n💡 Savings Opportunities:")
                for opp in analysis['savings_opportunities'][:3]:
                    print(f"  - {opp}")
            else:
                print(f"Error: {result.get('message')}")
                
        elif 'optimize' in query:
            # Extract budget if provided
            parts = query.split()
            budget = 4000  # default
            for part in parts:
                if part.isdigit():
                    budget = int(part)
            
            print(f"Claude: Optimizing for ${budget} budget...")
            result = await optimize_budget_with_claude(trip, daily, budget, ["keep hotel"])
            if result['status'] == 'ok':
                suggestions = result['result']['suggestions']
                total_savings = result['result']['total_savings']
                print(f"\n💰 Total Savings Found: ${total_savings}")
                for s in suggestions[:3]:
                    print(f"\n📍 {s['component']}")
                    print(f"   Current: ${s['current_cost']}")
                    print(f"   Proposed: {s['proposed']} (${s['new_cost']})")
                    print(f"   Saves: ${s['savings']} - Risk: {s['risk']}")
            else:
                print(f"Error: {result.get('message')}")
                
        else:
            # General analysis with custom focus
            print(f"Claude: Analyzing with focus on '{query}'...")
            result = await analyze_budget_with_claude(trip, daily, query)
            if result['status'] == 'ok' and 'summary' in result.get('result', {}):
                print(f"\n{result['result']['summary']}")
                if 'focus' in result['result']:
                    print(f"\nFocus insights: {result['result']['focus']}")
            else:
                print("Try: 'analyze', 'optimize 3500', or ask about specific aspects like 'food costs'")
        
        print()

if __name__ == "__main__":
    asyncio.run(chat())
