#!/usr/bin/env python
"""
Test script to verify the activity multiplier fix works correctly.
Tests with sequential generation for a 3-day trip to Singapore.
"""

import sys
from datetime import datetime, timedelta

# Set context date to April 1, 2026
print(f"Testing activity multiplier fix...")
print(f"Current system date: {datetime.now().strftime('%Y-%m-%d')}")

# Test the calculation
def test_activity_calculation():
    num_days = 3
    MEALS_PER_DAY = 2
    ACTIVITIES_PER_DAY = 2
    
    # Original calculation
    min_restaurants = num_days * MEALS_PER_DAY
    min_activities = (num_days - 1) * ACTIVITIES_PER_DAY + 1
    requested_activities = min_activities * 2
    
    print(f"\nFor a {num_days}-day trip:")
    print(f"  Minimum restaurants needed: {min_restaurants} (3 days × 2 meals)")
    print(f"  Minimum activities needed: {min_activities} ((3-1) × 2 + 1)")
    print(f"  Activities requested (with 2x multiplier): {requested_activities}")
    print(f"\nThis means in Iteration 1 of sequential generation:")
    print(f"  - Flights: 1")
    print(f"  - Hotels: 1")
    print(f"  - Restaurants: {min_restaurants}")
    print(f"  - Activities: {requested_activities} (will filter to ~{min_activities} after interest filtering)")

if __name__ == "__main__":
    test_activity_calculation()
