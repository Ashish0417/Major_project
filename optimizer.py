"""
Itinerary Optimizer Module
Uses OR-Tools CP-SAT solver for constraint-based optimization
FIXED: Corrected CpSolverStatus enum access
"""

from ortools.sat.python import cp_model
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class ItineraryItem:
    """Single itinerary item"""
    item_id: str
    item_type: str  # flight, accommodation, restaurant, activity
    name: str
    day: int
    start_time: int  # Minutes from day start (0-1440)
    duration: int  # Minutes
    cost: float
    latitude: float
    longitude: float
    preference_score: float  # 0-1
    popularity_score: float  # 0-1
    mandatory: bool = False


class ItineraryOptimizer:
    """
    Unified Planner Agent with Budget-Aware Optimization
    Uses OR-Tools CP-SAT solver
    """

    def __init__(self, user_profile):
        """Initialize optimizer with user profile"""
        self.user_profile = user_profile
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.last_solve_status = None  # Store the solve status

        # Weights for objective function (user-adjustable)
        self.weight_cost = 0.3
        self.weight_time = 0.2
        self.weight_preference = 0.3
        self.weight_popularity = 0.2

    def optimize_itinerary(self,
                          flights: List[Any],
                          accommodations: List[Any],
                          restaurants: List[Any],
                          activities: List[Any],
                          num_days: int) -> Dict[str, Any]:
        """
        Main optimization function

        Returns:
            Optimized itinerary with day-by-day breakdown
        """
        print("Starting itinerary optimization...")

        # Prepare items
        all_items = self._prepare_items(flights, accommodations, restaurants, 
                                       activities, num_days)

        if not all_items:
            return {"error": "No items to optimize"}

        print(f"Prepared {len(all_items)} items for optimization")

        # Create decision variables using item_id as key
        item_vars = {}
        items_by_id = {}  # Map item_id to item object

        for item in all_items:
            var_name = f"{item.item_type}_{item.item_id}"
            item_vars[item.item_id] = self.model.NewBoolVar(var_name)
            items_by_id[item.item_id] = item

        # Add constraints
        self._add_budget_constraint(all_items, item_vars)
        self._add_time_constraints(all_items, item_vars, num_days)
        self._add_activity_limit_constraint(all_items, item_vars, num_days)
        self._add_mandatory_constraints(all_items, item_vars)
        self._add_logical_constraints(all_items, item_vars, num_days)

        # Define objective function
        self._set_objective(all_items, item_vars)

        # Solve
        print("Solving optimization problem...")
        self.last_solve_status = self.solver.Solve(self.model)

        # FIXED: Use integer comparison and get status name safely
        status_name = self._get_status_name(self.last_solve_status)

        # Check if solution is optimal (4) or feasible (2)
        if self.last_solve_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"Solution found! Status: {status_name}")
            return self._extract_solution(all_items, item_vars, items_by_id, num_days)
        else:
            print(f"No solution found. Status: {status_name}")
            return {"error": "No feasible solution found", "status": status_name}

    def _get_status_name(self, status_code: int) -> str:
        """
        Convert solver status code to string name
        FIXED: Direct mapping instead of using enum

        Status codes:
        0 = UNKNOWN
        1 = MODEL_INVALID
        2 = FEASIBLE
        3 = INFEASIBLE
        4 = OPTIMAL
        """
        status_names = {
            0: "UNKNOWN",
            1: "MODEL_INVALID",
            2: "FEASIBLE",
            3: "INFEASIBLE",
            4: "OPTIMAL"
        }
        return status_names.get(status_code, f"UNKNOWN_STATUS_{status_code}")

    def _prepare_items(self, flights, accommodations, restaurants, 
                      activities, num_days) -> List[ItineraryItem]:
        """Convert agent proposals to ItineraryItems"""
        items = []

        # Add flights (day 0 for outbound, last day for return)
        for i, flight in enumerate(flights[:3]):  # Top 3 flights
            item = ItineraryItem(
                item_id=f"flight_{i}",
                item_type="flight",
                name=f"{flight.carrier} {flight.origin}-{flight.destination}",
                day=0,
                start_time=0,
                duration=flight.duration_minutes,
                cost=flight.price,
                latitude=0, longitude=0,  # Not used for flights
                preference_score=0.8,
                popularity_score=flight.reliability_score,
                mandatory=True if i == 0 else False
            )
            items.append(item)

        # Add accommodations (one per day)
        for i, acc in enumerate(accommodations[:5]):
            for day in range(num_days):
                item = ItineraryItem(
                    item_id=f"acc_{i}_day{day}",
                    item_type="accommodation",
                    name=acc.name,
                    day=day,
                    start_time=0,
                    duration=1440,  # Full day
                    cost=acc.price_per_night,
                    latitude=acc.latitude,
                    longitude=acc.longitude,
                    preference_score=acc.rating / 5.0,
                    popularity_score=min(1.0, acc.review_count / 500),
                    mandatory=False
                )
                items.append(item)

        # Add restaurants (multiple per day possible)
        for i, rest in enumerate(restaurants[:10]):
            for day in range(1, num_days):  # Skip day 0 (arrival)
                for meal_time in [720, 1080]:  # Lunch at 12:00, Dinner at 18:00
                    item = ItineraryItem(
                        item_id=f"rest_{i}_day{day}_t{meal_time}",
                        item_type="restaurant",
                        name=rest.name,
                        day=day,
                        start_time=meal_time,
                        duration=rest.average_meal_time_minutes,
                        cost=rest.average_meal_cost,
                        latitude=rest.latitude,
                        longitude=rest.longitude,
                        preference_score=rest.rating / 5.0,
                        popularity_score=min(1.0, rest.review_count / 300),
                        mandatory=False
                    )
                    items.append(item)

        # Add activities
        for i, act in enumerate(activities):
            for day in range(1, num_days):
                # Morning, afternoon slots
                for start_time in [540, 840]:  # 09:00, 14:00
                    item = ItineraryItem(
                        item_id=f"act_{i}_day{day}_t{start_time}",
                        item_type="activity",
                        name=act.name,
                        day=day,
                        start_time=start_time,
                        duration=act.duration_minutes,
                        cost=act.price,
                        latitude=act.latitude,
                        longitude=act.longitude,
                        preference_score=act.rating / 5.0,
                        popularity_score=act.popularity_score,
                        mandatory=False
                    )
                    items.append(item)

        return items

    def _add_budget_constraint(self, items, item_vars):
        """Budget constraint: total cost <= budget"""
        prefs = self.user_profile.travel_preferences
        if not prefs:
            return

        total_budget = prefs.budget_total

        # Calculate total cost
        cost_terms = []
        for item in items:
            cost_int = int(item.cost * 100)  # Convert to integer cents
            cost_terms.append(cost_int * item_vars[item.item_id])

        if cost_terms:
            self.model.Add(sum(cost_terms) <= int(total_budget * 100))
            print(f"  ✓ Added budget constraint: <= INR {total_budget:,.2f}")

    def _add_time_constraints(self, items, item_vars, num_days):
        """Time and sequencing constraints"""
        constraint_count = 0
        for day in range(num_days):
            day_items = [item for item in items if item.day == day]

            # No overlapping activities on same day
            for i, item1 in enumerate(day_items):
                for item2 in day_items[i+1:]:
                    if item1.item_type in ['activity', 'restaurant'] and \
                       item2.item_type in ['activity', 'restaurant']:
                        # Check if they overlap
                        overlap = not (item1.start_time + item1.duration <= item2.start_time or
                                     item2.start_time + item2.duration <= item1.start_time)
                        if overlap:
                            # At most one can be selected
                            self.model.Add(item_vars[item1.item_id] + item_vars[item2.item_id] <= 1)
                            constraint_count += 1

        if constraint_count > 0:
            print(f"  ✓ Added {constraint_count} time constraints (no overlaps)")

    def _add_activity_limit_constraint(self, items, item_vars, num_days):
        """Limit activities per day"""
        prefs = self.user_profile.travel_preferences
        if not prefs:
            max_activities = 4
        else:
            max_activities = prefs.max_activities_per_day

        constraint_count = 0
        for day in range(num_days):
            day_activities = [item for item in items 
                            if item.day == day and item.item_type == 'activity']

            if day_activities:
                self.model.Add(
                    sum(item_vars[item.item_id] for item in day_activities) <= max_activities
                )
                constraint_count += 1

        if constraint_count > 0:
            print(f"  ✓ Added activity limit: max {max_activities} per day")

    def _add_mandatory_constraints(self, items, item_vars):
        """Mandatory items must be selected"""
        mandatory_count = 0
        for item in items:
            if item.mandatory:
                self.model.Add(item_vars[item.item_id] == 1)
                mandatory_count += 1

        if mandatory_count > 0:
            print(f"  ✓ Added {mandatory_count} mandatory item constraints")

    def _add_logical_constraints(self, items, item_vars, num_days):
        """Logical constraints (e.g., exactly one accommodation per day)"""
        accommodation_constraints = 0
        for day in range(num_days):
            day_accommodations = [item for item in items 
                                if item.day == day and item.item_type == 'accommodation']

            if day_accommodations:
                # Exactly one accommodation per day
                self.model.Add(
                    sum(item_vars[item.item_id] for item in day_accommodations) == 1
                )
                accommodation_constraints += 1

        if accommodation_constraints > 0:
            print(f"  ✓ Added {accommodation_constraints} accommodation constraints (1 per day)")

    def _set_objective(self, items, item_vars):
        """Set multi-objective optimization function"""
        # Normalize values
        max_cost = max(item.cost for item in items) if items else 1
        max_duration = max(item.duration for item in items) if items else 1

        objective_terms = []

        for item in items:
            # Normalized scores
            cost_score = int((1 - item.cost / max_cost) * 1000) if max_cost > 0 else 0
            time_score = int((1 - item.duration / max_duration) * 1000) if max_duration > 0 else 0
            pref_score = int(item.preference_score * 1000)
            pop_score = int(item.popularity_score * 1000)

            # Weighted sum
            score = int(
                self.weight_cost * cost_score +
                self.weight_time * time_score +
                self.weight_preference * pref_score +
                self.weight_popularity * pop_score
            )

            objective_terms.append(score * item_vars[item.item_id])

        # Maximize total score
        if objective_terms:
            self.model.Maximize(sum(objective_terms))
            print(f"  ✓ Objective function set (maximize weighted score)")

    def _extract_solution(self, items, item_vars, items_by_id, num_days) -> Dict[str, Any]:
        """Extract and format the solution"""
        selected_items = [item for item in items 
                         if self.solver.Value(item_vars[item.item_id]) == 1]

        # Organize by day
        itinerary_by_day = {day: [] for day in range(num_days)}

        for item in selected_items:
            itinerary_by_day[item.day].append(item)

        # Sort each day by start time
        for day in itinerary_by_day:
            itinerary_by_day[day].sort(key=lambda x: x.start_time)

        # Calculate totals
        total_cost = sum(item.cost for item in selected_items)

        # Get status name safely
        status_name = self._get_status_name(self.last_solve_status)

        # Build result
        result = {
            'itinerary': itinerary_by_day,
            'total_cost': round(total_cost, 2),
            'currency': 'INR',
            'num_days': num_days,
            'num_activities': sum(1 for item in selected_items if item.item_type == 'activity'),
            'num_restaurants': sum(1 for item in selected_items if item.item_type == 'restaurant'),
            'num_accommodations': sum(1 for item in selected_items if item.item_type == 'accommodation'),
            'budget_remaining': self.user_profile.travel_preferences.budget_total - total_cost if self.user_profile.travel_preferences else 0,
            'solver_stats': {
                'status': status_name,
                'objective_value': self.solver.ObjectiveValue(),
                'solve_time': self.solver.WallTime(),
                'total_items': len(selected_items)
            }
        }

        return result


if __name__ == "__main__":
    print("Itinerary Optimizer Module")
    print("This module requires data from agents to run.")
    print("Use main.py to run the full system.")
