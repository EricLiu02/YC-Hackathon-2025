from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date as date_type, datetime
from enum import Enum


class TravelCategory(str, Enum):
    FLIGHTS = "flights"
    HOTELS = "hotels"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    ACTIVITIES = "activities"
    SHOPPING = "shopping"
    MISC = "misc"


class BudgetStatus(str, Enum):
    UNDER_BUDGET = "under_budget"
    ON_BUDGET = "on_budget"
    OVER_BUDGET = "over_budget"
    CRITICAL = "critical"


class TripComponent(BaseModel):
    component_id: str
    category: TravelCategory
    name: str
    cost: float
    currency: str = "USD"
    description: str | None = None
    date: date_type | None = None


class TripPlan(BaseModel):
    trip_id: str
    destination: str
    start_date: date_type
    end_date: date_type
    num_travelers: int
    components: List[TripComponent]
    total_budget: float
    currency: str = "USD"


class DailySpendEstimate(BaseModel):
    category: TravelCategory
    per_person_per_day: float
    currency: str = "USD"


class BudgetCalculationRequest(BaseModel):
    trip_plan: TripPlan
    daily_spend_estimates: List[DailySpendEstimate]
    additional_costs: List[TripComponent] | None = None


class BudgetBreakdown(BaseModel):
    category: TravelCategory
    planned_cost: float
    estimated_daily_cost: float
    total_category_cost: float
    percentage_of_budget: float


class BudgetCalculationResponse(BaseModel):
    trip_id: str
    total_planned_cost: float
    total_estimated_cost: float
    total_budget: float
    surplus_shortfall: float
    budget_status: BudgetStatus
    breakdown_by_category: List[BudgetBreakdown]
    currency: str = "USD"
    calculation_timestamp: datetime


class BudgetSwapSuggestion(BaseModel):
    original_component: TripComponent
    alternative_component: TripComponent
    cost_savings: float
    risk_level: str
    constraint_violations: List[str]
    recommendation_score: float


class BudgetSwapRequest(BaseModel):
    trip_plan: TripPlan
    target_categories: List[TravelCategory] | None = None
    max_risk_level: str = "medium"
    min_savings_threshold: float = 0.0


class BudgetSwapResponse(BaseModel):
    trip_id: str
    suggestions: List[BudgetSwapSuggestion]
    total_potential_savings: float
    currency: str = "USD"
    risk_alerts: List[str]
    constraint_violations: List[str]
