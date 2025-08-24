import asyncio
import sys
import json
from datetime import date
from typing import Any, List, Optional, Dict

# Graceful MCP import (server still requires mcp to run)
try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    class FastMCP:  # no-op so tools can be imported for tests
        def __init__(self, name: str): self.name = name
        def tool(self, *a, **k):
            def deco(fn): return fn
            return deco
        def run(self):
            raise RuntimeError("MCP not installed. Install: pip install mcp modelcontextprotocol")

from models import (
    TripPlan, TripComponent, DailySpendEstimate, TravelCategory,
    BudgetCalculationRequest, BudgetCalculationResponse,
    BudgetSwapRequest, BudgetSwapResponse
)
from fixtures import (
    DEMO_TRIP_PLAN, DEMO_DAILY_SPEND_ESTIMATES,
    get_demo_budget_calculation_response, get_demo_budget_swap_suggestions
)
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

app = FastMCP(name="budgeteer-mcp-agent")
DEFAULT_DEMO: bool = True  # demo-first behavior

import os, json
try:
    from anthropic import AsyncAnthropic
    _ANTHROPIC_OK = True
except Exception:
    _ANTHROPIC_OK = False

def _get_claude_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    return AsyncAnthropic(api_key=api_key), os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

@app.tool()
async def test_claude_connection() -> dict:
    if not _ANTHROPIC_OK:
        return {"status": "error", "message": "anthropic not installed. pip install anthropic"}
    try:
        client, model = _get_claude_client()
        resp = await client.messages.create(
            model=model,
            max_tokens=20,
            messages=[{"role": "user", "content": "Respond with OK"}]
        )
        text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "")
        return {"status": "ok" if text.strip().upper().startswith("OK") else "unexpected", "model": model, "response": text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _ensure_dates(arguments: dict[str, Any]) -> dict[str, Any]:
    updated = dict(arguments)
    if "trip_plan" in updated and isinstance(updated["trip_plan"], dict):
        trip_plan = updated["trip_plan"]
        if "start_date" in trip_plan and isinstance(trip_plan["start_date"], str):
            trip_plan["start_date"] = date.fromisoformat(trip_plan["start_date"])
        if "end_date" in trip_plan and isinstance(trip_plan["end_date"], str):
            trip_plan["end_date"] = date.fromisoformat(trip_plan["end_date"])
        if "components" in trip_plan:
            for component in trip_plan["components"]:
                if "date" in component and component["date"] and isinstance(component["date"], str):
                    component["date"] = date.fromisoformat(component["date"])
    return updated

def _serialize_budget_calculation_response(response: BudgetCalculationResponse) -> dict:
    d = response.model_dump()
    if hasattr(response, "calculation_timestamp"):
        try:
            d["calculation_timestamp"] = response.calculation_timestamp.isoformat()
        except Exception:
            pass
    return d

def _serialize_budget_swap_response(response: BudgetSwapResponse) -> dict:
    return response.model_dump()

@app.tool()
async def calculate_trip_budget(
    trip_plan: dict | None = None,
    daily_spend_estimates: List[dict] | None = None,
    additional_costs: Optional[List[dict]] = None,
    demo: bool | None = None,
) -> dict:
    if trip_plan is None:
        trip_plan = DEMO_TRIP_PLAN.model_dump()
    if daily_spend_estimates is None:
        daily_spend_estimates = [e.model_dump() for e in DEMO_DAILY_SPEND_ESTIMATES]

    args = _ensure_dates({
        "trip_plan": trip_plan,
        "daily_spend_estimates": daily_spend_estimates,
        "additional_costs": additional_costs or []
    })
    try:
        _ = BudgetCalculationRequest(**args)
    except Exception as e:
        return {"error": f"Invalid request format: {str(e)}", "trip_id": trip_plan.get("trip_id", "unknown"), "status": "error"}

    response = get_demo_budget_calculation_response(DEMO_TRIP_PLAN)
    return _serialize_budget_calculation_response(response)

@app.tool()
async def suggest_budget_swaps(
    trip_plan: dict | None = None,
    target_budget: Optional[float] = None,
    target_categories: Optional[List[str]] = None,
    demo: bool | None = None,
) -> dict:
    if trip_plan is None:
        trip_plan = DEMO_TRIP_PLAN.model_dump()

    args = _ensure_dates({
        "trip_plan": trip_plan,
        "target_budget": target_budget,
        "target_categories": target_categories or []
    })
    try:
        _ = BudgetSwapRequest(**args)
    except Exception as e:
        return {"error": f"Invalid request format: {str(e)}", "trip_id": trip_plan.get("trip_id", "unknown"), "status": "error"}

    response = get_demo_budget_swap_suggestions(DEMO_TRIP_PLAN)
    return _serialize_budget_swap_response(response)

@app.tool()
async def get_demo_trip_plan() -> dict:
    return DEMO_TRIP_PLAN.model_dump()

@app.tool()
async def get_demo_daily_spend_estimates() -> List[dict]:
    return [e.model_dump() for e in DEMO_DAILY_SPEND_ESTIMATES]

@app.tool()
async def analyze_budget_with_claude(
    trip_plan: dict,
    daily_spend_estimates: List[dict],
    analysis_focus: Optional[str] = None
) -> dict:
    if not _ANTHROPIC_OK:
        return {"status": "error", "message": "anthropic not installed. pip install anthropic"}
    try:
        client, model = _get_claude_client()
        # Convert dates to strings for JSON serialization
        trip_plan_json = json.dumps(trip_plan, default=str)
        daily_spends_json = json.dumps(daily_spend_estimates, default=str)
        
        prompt = (
            "You are a travel budgeting expert. Analyze the trip plan and daily spends.\n"
            "Return concise JSON with fields: summary, risks[], savings_opportunities[], focus.\n\n"
            f"Focus: {analysis_focus or 'general'}\n"
            f"Trip plan JSON:\n{trip_plan_json}\n"
            f"Daily spends JSON:\n{daily_spends_json}\n"
            "Respond ONLY with JSON."
        )
        resp = await client.messages.create(
            model=model, max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "{}")
        try:
            return {"status": "ok", "model": model, "result": json.loads(text)}
        except Exception:
            return {"status": "ok_text", "model": model, "raw": text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.tool()
async def optimize_budget_with_claude(
    trip_plan: dict,
    daily_spend_estimates: List[dict],
    target_budget: float,
    optimization_constraints: Optional[List[str]] = None
) -> dict:
    if not _ANTHROPIC_OK:
        return {"status": "error", "message": "anthropic not installed. pip install anthropic"}
    try:
        client, model = _get_claude_client()
        # Convert dates to strings for JSON serialization
        trip_plan_json = json.dumps(trip_plan, default=str)
        daily_spends_json = json.dumps(daily_spend_estimates, default=str)
        
        prompt = (
            "You are a travel budgeting optimizer. Propose concrete swaps to reach target budget.\n"
            "Return JSON: {suggestions:[{component, current_cost, proposed, new_cost, savings, risk}], total_savings, notes[]}.\n\n"
            f"Target budget: {target_budget}\n"
            f"Constraints: {optimization_constraints or []}\n"
            f"Trip plan JSON:\n{trip_plan_json}\n"
            f"Daily spends JSON:\n{daily_spends_json}\n"
            "Respond ONLY with JSON."
        )
        resp = await client.messages.create(
            model=model, max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "{}")
        try:
            return {"status": "ok", "model": model, "result": json.loads(text)}
        except Exception:
            return {"status": "ok_text", "model": model, "raw": text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    if not MCP_AVAILABLE:
        print("❌ MCP not installed. Install with: pip install mcp modelcontextprotocol")
        return
    print("🚀 Starting Budgeteer MCP Agent...")
    app.run()

if __name__ == "__main__":
    main()
