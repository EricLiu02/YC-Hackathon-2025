import asyncio
from backend.budgeteer_mcp_agent.fast_server import (
    test_claude_connection,
    analyze_budget_with_claude, 
    optimize_budget_with_claude,
    get_demo_trip_plan, 
    get_demo_daily_spend_estimates
)

async def main():
    # Test connection first
    print("Testing Claude connection...")
    conn = await test_claude_connection()
    print(f"Connection: {conn['status']}")
    
    if conn['status'] == 'ok':
        # Get demo data
        trip = await get_demo_trip_plan()
        daily = await get_demo_daily_spend_estimates()
        
        # Test analyze
        print("\nTesting analyze_budget_with_claude...")
        r1 = await analyze_budget_with_claude(trip, daily, "find savings")
        print(f"Analyze status: {r1.get('status')}")
        if r1.get('result'):
            print(f"Result keys: {list(r1['result'].keys())}")
        
        # Test optimize
        print("\nTesting optimize_budget_with_claude...")
        r2 = await optimize_budget_with_claude(trip, daily, 4000, ["keep hotel"])
        print(f"Optimize status: {r2.get('status')}")
        if r2.get('result'):
            print(f"Result keys: {list(r2['result'].keys())}")

asyncio.run(main())
