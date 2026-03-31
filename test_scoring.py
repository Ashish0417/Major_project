#!/usr/bin/env python3
"""Test scoring logic to verify flight is preferred over bus with abundant budget"""

from langgraph_optimizer import (
    OptionCandidate, ItineraryPlan, ConstraintEvaluator, 
    UserPreferences, BudgetConstraint
)

# Create budget with abundant slack (150K for short trip)
budget = BudgetConstraint(
    total_budget=150000,
    min_transport=1000,
    max_transport=50000,
    min_accommodation=10000,
    max_accommodation=30000,
    min_restaurant=5000,
    max_restaurant=15000,
    min_activity=5000,
    max_activity=15000
)

prefs = UserPreferences()
evaluator = ConstraintEvaluator(budget, prefs, num_days=2)

# Test plan 1: Bus (cheap but slow 16h 54m)
bus_option = OptionCandidate(
    id='bus1',
    category='transport',
    name='Bus Bangalore→Mumbai',
    cost=980,
    currency='INR',
    rating=3.5,
    duration_minutes=1014  # 16h 54m
)

plan_bus = ItineraryPlan(
    transport_option=bus_option,
    accommodation_options=[
        OptionCandidate('h1', 'accommodation', 'Hotel Mumbai', 3000, 'INR', 4.2),
    ],
    restaurant_options=[
        OptionCandidate('r1', 'restaurant', 'Restaurant 1', 1000, 'INR', 4.0),
        OptionCandidate('r2', 'restaurant', 'Restaurant 2', 800, 'INR', 4.1),
    ],
    activity_options=[
        OptionCandidate('a1', 'activity', 'Activity 1', 2000, 'INR', 4.5),
        OptionCandidate('a2', 'activity', 'Activity 2', 1500, 'INR', 4.3),
    ],
    total_days=2
)

# Test plan 2: Flight (expensive but fast 2h)
flight_option = OptionCandidate(
    id='flight1',
    category='transport',
    name='Flight Bangalore→Mumbai',
    cost=8000,
    currency='INR',
    rating=4.5,
    duration_minutes=120  # 2h
)

plan_flight = ItineraryPlan(
    transport_option=flight_option,
    accommodation_options=[
        OptionCandidate('h1', 'accommodation', 'Hotel Mumbai', 3000, 'INR', 4.2),
    ],
    restaurant_options=[
        OptionCandidate('r1', 'restaurant', 'Restaurant 1', 1000, 'INR', 4.0),
        OptionCandidate('r2', 'restaurant', 'Restaurant 2', 800, 'INR', 4.1),
    ],
    activity_options=[
        OptionCandidate('a1', 'activity', 'Activity 1', 2000, 'INR', 4.5),
        OptionCandidate('a2', 'activity', 'Activity 2', 1500, 'INR', 4.3),
    ],
    total_days=2
)

# Evaluate both plans
score_bus, viol_bus = evaluator.evaluate_plan(plan_bus)
score_flight, viol_flight = evaluator.evaluate_plan(plan_flight)

bus_cost = sum(plan_bus.calculate_costs().values())
flight_cost = sum(plan_flight.calculate_costs().values())

print("\n" + "="*70)
print("SCORING TEST: Bus vs Flight with ABUNDANT Budget (150K INR)")
print("="*70)

print("\nBUS PLAN:")
print(f"  Transport: Bus Bangalore→Mumbai")
print(f"  Cost:             INR {bus_cost:.0f}")
print(f"  Duration:         16h 54m")
print(f"  Avg Rating:       3.5/5 (low)")
print(f"  Budget Slack:     {((budget.total_budget - bus_cost) / budget.total_budget * 100):.0f}%")
print(f"  SCORE:            {score_bus:.1f}/100")

print("\nFLIGHT PLAN (should score HIGHER):")
print(f"  Transport: Flight Bangalore→Mumbai")
print(f"  Cost:             INR {flight_cost:.0f}")
print(f"  Duration:         2h")
print(f"  Avg Rating:       4.5/5 (high)")
print(f"  Budget Slack:     {((budget.total_budget - flight_cost) / budget.total_budget * 100):.0f}%")
print(f"  SCORE:            {score_flight:.1f}/100")

print("\n" + "-"*70)
if score_flight > score_bus:
    print(f"SUCCESS! FLIGHT wins by {score_flight - score_bus:.1f} points")
    print("✓ With abundant budget, fast travel is now prioritized!")
else:
    print(f"FAIL: Bus scored {score_bus:.1f} vs Flight {score_flight:.1f}")
    print("✗ Budget-abundant preference not working correctly")
print("="*70 + "\n")
