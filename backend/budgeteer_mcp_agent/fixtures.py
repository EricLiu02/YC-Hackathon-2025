from datetime import date, datetime
from models import (
    TripPlan, TripComponent, DailySpendEstimate, TravelCategory,
    BudgetCalculationResponse, BudgetBreakdown, BudgetStatus,
    BudgetSwapSuggestion, BudgetSwapResponse
)


# Demo trip components
DEMO_FLIGHT_COMPONENTS = [
    TripComponent(
        component_id="flight_nyc_london",
        category=TravelCategory.FLIGHTS,
        name="Round-trip NYC to London",
        cost=850.00,
        description="Economy class, direct flight",
        date=date(2025, 3, 15)
    ),
    TripComponent(
        component_id="flight_london_nyc",
        category=TravelCategory.FLIGHTS,
        name="Return flight London to NYC",
        cost=850.00,
        description="Economy class, direct flight",
        date=date(2025, 3, 22)
    )
]

DEMO_HOTEL_COMPONENTS = [
    TripComponent(
        component_id="hotel_london_7_nights",
        category=TravelCategory.HOTELS,
        name="London Marriott Hotel",
        cost=1400.00,
        description="7 nights, 4-star hotel in city center",
        date=date(2025, 3, 15)
    )
]

DEMO_TRANSPORT_COMPONENTS = [
    TripComponent(
        component_id="airport_transfer",
        category=TravelCategory.TRANSPORTATION,
        name="Airport transfers",
        cost=120.00,
        description="Round-trip airport transfers",
        date=date(2025, 3, 15)
    ),
    TripComponent(
        component_id="tube_pass",
        category=TravelCategory.TRANSPORTATION,
        name="7-day London Underground pass",
        cost=70.00,
        description="Unlimited travel on London public transport",
        date=date(2025, 3, 15)
    )
]

DEMO_ACTIVITY_COMPONENTS = [
    TripComponent(
        component_id="british_museum",
        category=TravelCategory.ACTIVITIES,
        name="British Museum tickets",
        cost=0.00,
        description="Free entry, but booking required",
        date=date(2025, 3, 16)
    ),
    TripComponent(
        component_id="tower_of_london",
        category=TravelCategory.ACTIVITIES,
        name="Tower of London",
        cost=80.00,
        description="Guided tour for 2 people",
        date=date(2025, 3, 17)
    ),
    TripComponent(
        component_id="west_end_show",
        category=TravelCategory.ACTIVITIES,
        name="West End theater show",
        cost=150.00,
        description="Premium seats for 2 people",
        date=date(2025, 3, 18)
    )
]

# Demo daily spend estimates
DEMO_DAILY_SPEND_ESTIMATES = [
    DailySpendEstimate(
        category=TravelCategory.FOOD,
        per_person_per_day=75.00
    ),
    DailySpendEstimate(
        category=TravelCategory.SHOPPING,
        per_person_per_day=50.00
    ),
    DailySpendEstimate(
        category=TravelCategory.MISC,
        per_person_per_day=25.00
    )
]

# Demo trip plan
DEMO_TRIP_PLAN = TripPlan(
    trip_id="london_spring_2025",
    destination="London, UK",
    start_date=date(2025, 3, 15),
    end_date=date(2025, 3, 22),
    num_travelers=2,
    components=(
        DEMO_FLIGHT_COMPONENTS + 
        DEMO_HOTEL_COMPONENTS + 
        DEMO_TRANSPORT_COMPONENTS + 
        DEMO_ACTIVITY_COMPONENTS
    ),
    total_budget=4000.00,
    currency="USD"
)


def get_demo_budget_calculation_response(trip_plan: TripPlan) -> BudgetCalculationResponse:
    """Generate demo budget calculation response."""
    
    # Calculate planned costs
    total_planned_cost = sum(comp.cost for comp in trip_plan.components)
    
    # Calculate daily costs
    trip_duration = (trip_plan.end_date - trip_plan.start_date).days
    daily_costs = {}
    
    for estimate in DEMO_DAILY_SPEND_ESTIMATES:
        daily_costs[estimate.category] = estimate.per_person_per_day * trip_plan.num_travelers * trip_duration
    
    # Calculate breakdown by category
    breakdown_by_category = []
    category_costs = {}
    
    # Group planned costs by category
    for component in trip_plan.components:
        if component.category not in category_costs:
            category_costs[component.category] = 0
        category_costs[component.category] += component.cost
    
    # Create breakdown for each category
    for category in TravelCategory:
        planned_cost = category_costs.get(category, 0.0)
        estimated_daily_cost = daily_costs.get(category, 0.0)
        total_category_cost = planned_cost + estimated_daily_cost
        
        if total_category_cost > 0:
            percentage = (total_category_cost / trip_plan.total_budget) * 100
            breakdown_by_category.append(BudgetBreakdown(
                category=category,
                planned_cost=planned_cost,
                estimated_daily_cost=estimated_daily_cost,
                total_category_cost=total_category_cost,
                percentage_of_budget=percentage
            ))
    
    total_estimated_cost = sum(daily_costs.values())
    total_cost = total_planned_cost + total_estimated_cost
    surplus_shortfall = trip_plan.total_budget - total_cost
    
    # Determine budget status
    if surplus_shortfall > 500:
        budget_status = BudgetStatus.UNDER_BUDGET
    elif surplus_shortfall > 0:
        budget_status = BudgetStatus.ON_BUDGET
    elif surplus_shortfall > -500:
        budget_status = BudgetStatus.OVER_BUDGET
    else:
        budget_status = BudgetStatus.CRITICAL
    
    return BudgetCalculationResponse(
        trip_id=trip_plan.trip_id,
        total_planned_cost=total_planned_cost,
        total_estimated_cost=total_estimated_cost,
        total_budget=trip_plan.total_budget,
        surplus_shortfall=surplus_shortfall,
        budget_status=budget_status,
        breakdown_by_category=breakdown_by_category,
        currency=trip_plan.currency,
        calculation_timestamp=datetime.now()
    )


def get_demo_budget_swap_suggestions(trip_plan: TripPlan) -> BudgetSwapResponse:
    """Generate demo budget swap suggestions."""
    
    suggestions = []
    
    # Hotel swap suggestion
    hotel_swap = BudgetSwapSuggestion(
        original_component=next(comp for comp in trip_plan.components if comp.category == TravelCategory.HOTELS),
        alternative_component=TripComponent(
            component_id="hotel_london_budget",
            category=TravelCategory.HOTELS,
            name="Premier Inn London",
            cost=980.00,
            description="3-star hotel, good location, budget-friendly",
            date=date(2025, 3, 15)
        ),
        cost_savings=420.00,
        risk_level="low",
        constraint_violations=[],
        recommendation_score=0.85
    )
    suggestions.append(hotel_swap)
    
    # Flight swap suggestion
    flight_swap = BudgetSwapSuggestion(
        original_component=next(comp for comp in trip_plan.components if comp.category == TravelCategory.FLIGHTS and "nyc_london" in comp.component_id),
        alternative_component=TripComponent(
            component_id="flight_nyc_london_budget",
            category=TravelCategory.FLIGHTS,
            name="Budget round-trip NYC to London",
            cost=650.00,
            description="Economy class, 1 stop, longer travel time",
            date=date(2025, 3, 15)
        ),
        cost_savings=200.00,
        risk_level="medium",
        constraint_violations=["Longer travel time", "1 stop required"],
        recommendation_score=0.70
    )
    suggestions.append(flight_swap)
    
    # Activity swap suggestion
    activity_swap = BudgetSwapSuggestion(
        original_component=next(comp for comp in trip_plan.components if comp.component_id == "west_end_show"),
        alternative_component=TripComponent(
            component_id="west_end_show_budget",
            category=TravelCategory.ACTIVITIES,
            name="West End theater show (matinee)",
            cost=90.00,
            description="Standard seats, afternoon performance",
            date=date(2025, 3, 18)
        ),
        cost_savings=60.00,
        risk_level="low",
        constraint_violations=["Afternoon instead of evening"],
        recommendation_score=0.80
    )
    suggestions.append(activity_swap)
    
    total_potential_savings = sum(suggestion.cost_savings for suggestion in suggestions)
    
    return BudgetSwapResponse(
        trip_id=trip_plan.trip_id,
        suggestions=suggestions,
        total_potential_savings=total_potential_savings,
        currency=trip_plan.currency,
        risk_alerts=["Budget flight has longer travel time", "Hotel change reduces luxury level"],
        constraint_violations=["Some alternatives require schedule adjustments"]
    )
