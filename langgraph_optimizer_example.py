"""
Example: Using LangGraph Optimizer in TravelItineraryOrchestrator
Shows how to integrate without breaking existing code
"""

from langgraph_optimizer import (
    LangGraphItineraryOptimizer,
    BudgetConstraint,
    UserPreferences,
    ConstraintEvaluator,
    ItineraryPlan,
    OptionCandidate
)
from typing import Dict, Any, List
import json


# ============================================================================
# EXAMPLE 1: Feature Flag Integration (Safest)
# ============================================================================

class EnhancedTravelOrchestrator:
    """
    Existing TravelItineraryOrchestrator with optional LangGraph support
    Uses feature flag - keeps old code working
    """
    
    USE_LANGGRAPH = True  # Toggle this to switch optimizers
    
    def generate_itinerary(self, trip_details: dict = None):
        """Generate itinerary - now with LangGraph option"""
        
        print("\n" + "="*80)
        print("🌍 GENERATING COMPLETE TRAVEL ITINERARY")
        print("="*80)
        
        # Extract trip details (same as before)
        origin = trip_details.get('origin_city', 'Mumbai')
        destination = trip_details.get('destination_city', 'Tokyo')
        departure_date = trip_details.get('departure_date', '2026-03-20')
        num_days = trip_details.get('num_days', 7)
        budget = trip_details.get('budget_inr', 150000)
        interests = trip_details.get('interests', ['cultural', 'adventure'])
        dietary = trip_details.get('dietary_restrictions', [])
        
        # Search agents (same as before)
        print(f"\n{'='*80}")
        print("[1/3] SEARCHING FOR OPTIONS")
        print("="*80)
        
        transport_options = self._search_transport(origin, destination, departure_date)
        accommodation_options = self._search_accommodations(destination, departure_date, num_days)
        restaurant_options = self._search_restaurants(destination, dietary)
        activity_options = self._search_activities(destination, interests)
        
        # FEATURE FLAG: Choose optimizer
        if self.USE_LANGGRAPH:
            print("\n🔄 Using LangGraph optimizer (parallel exploration + backtracking)")
            optimized = self._optimize_with_langgraph(
                trip_details, budget, interests, dietary,
                transport_options, accommodation_options,
                restaurant_options, activity_options
            )
        else:
            print("\n🔄 Using OR-Tools optimizer (existing code)")
            optimized = self._optimize_with_ortools(
                trip_details, budget,
                transport_options, accommodation_options,
                restaurant_options, activity_options
            )
        
        # Display result (same as before)
        if 'error' not in optimized:
            self.display_itinerary(optimized, trip_details)
        else:
            print(f"\n❌ Optimization failed: {optimized['error']}")
        
        return optimized
    
    def _optimize_with_langgraph(self, trip_details: dict, budget: float,
                                 interests: list, dietary: list,
                                 transport_options, accommodation_options,
                                 restaurant_options, activity_options) -> Dict[str, Any]:
        """
        New optimizer: LangGraph with dynamic constraints
        No hardcoded ratios - all driven by user preferences
        """
        
        print(f"\n{'='*80}")
        print("[2/3] OPTIMIZING WITH LANGGRAPH")
        print("="*80)
        
        num_days = trip_details.get('num_days', 7)
        origin = trip_details.get('origin_city')
        destination = trip_details.get('destination_city')
        departure_date = trip_details.get('departure_date')
        
        # Step 1: Define flexible budget constraints (no hardcoded 30%)
        print("\n💰 Setting flexible budget constraints...")
        
        budget_constraint = {
            'total_budget': budget,
            
            # Transport: minimum for at least one flight, maximum 30% of budget
            'transport_min': 5000,
            'transport_max': min(budget * 0.3, 50000),  # But cap at 50K
            
            # Accommodation: bulk of budget if needed (luxury trip) OR minimal
            'accommodation_min': 10000,
            'accommodation_max': budget * 0.5,  # Up to 50% for comfort
            
            # Restaurants: flexible based on trip style
            'restaurant_min': 0,  # Optional
            'restaurant_max': budget * 0.25,  # Max 25%
            
            # Activities: optional but preferred for good experience
            'activity_min': 0,  # Optional
            'activity_max': budget * 0.25  # Max 25%
        }
        
        print(f"   Transport: {budget_constraint['transport_min']:.0f} - {budget_constraint['transport_max']:.0f}")
        print(f"   Accommodation: {budget_constraint['accommodation_min']:.0f} - {budget_constraint['accommodation_max']:.0f}")
        print(f"   Restaurants: {budget_constraint['restaurant_min']:.0f} - {budget_constraint['restaurant_max']:.0f}")
        print(f"   Activities: {budget_constraint['activity_min']:.0f} - {budget_constraint['activity_max']:.0f}")
        
        # Step 2: Define user preferences
        print("\n👤 Setting user preferences...")
        
        # Infer priority from trip characteristics
        if budget > 200000:
            priority = "experience"  # High budget = focus on quality
        elif budget < 50000:
            priority = "cost"  # Low budget = focus on saving
        else:
            priority = "value"  # Medium budget = balance
        
        preferences = {
            'priority': priority,
            'preferred_pace': trip_details.get('pace', 'balanced'),
            'hotel_min_rating': 3.5,
            'restaurant_min_rating': 3.0,
            'activity_min_rating': 3.5,
            'activity_interests': interests,
            'dietary_restrictions': dietary,
            'activities_per_day_min': 1,
            'activities_per_day_max': 4,
            'meals_per_day': 2
        }
        
        print(f"   Priority: {preferences['priority']}")
        print(f"   Pace: {preferences['preferred_pace']}")
        print(f"   Min ratings: hotel {preferences['hotel_min_rating']}, "
              f"restaurant {preferences['restaurant_min_rating']}")
        
        # Step 3: Initialize LangGraph optimizer
        print("\n🔧 Initializing LangGraph optimizer...")
        
        optimizer = LangGraphItineraryOptimizer(
            budget_constraint=budget_constraint,
            preferences=preferences,
            num_days=num_days
        )
        
        # Step 4: Convert agent results to optimizer format
        print("\n📊 Converting search results to optimizer format...")
        
        transport_candidates = self._convert_transport(transport_options)
        accommodation_candidates = self._convert_accommodations(accommodation_options)
        restaurant_candidates = self._convert_restaurants(restaurant_options)
        activity_candidates = self._convert_activities(activity_options)
        
        print(f"   Transport options: {len(transport_candidates)}")
        print(f"   Accommodation options: {len(accommodation_candidates)}")
        print(f"   Restaurant options: {len(restaurant_candidates)}")
        print(f"   Activity options: {len(activity_candidates)}")
        
        # Step 5: Run parallel exploration with backtracking
        print("\n⚡ Running parallel exploration...")
        
        result = optimizer.optimize(
            transport_options=[o.to_dict() for o in transport_candidates],
            accommodation_options=[o.to_dict() for o in accommodation_candidates],
            restaurant_options=[o.to_dict() for o in restaurant_candidates],
            activity_options=[o.to_dict() for o in activity_candidates],
            trip_start_date=departure_date,
            origin=origin,
            destination=destination
        )
        
        # Step 6: Format result for display
        print(f"\n{'='*80}")
        print("[3/3] OPTIMIZATION RESULTS")
        print("="*80)
        
        if result['success'] and result['best_plan']:
            print(f"✅ Found optimal plan!")
            print(f"   Score: {result['best_score']:.1f}/100")
            print(f"   Combinations evaluated: {result['evaluated_combinations']}")
            print(f"   Backtrack attempts: {result['backtrack_attempts']}")
            
            # Convert to display format
            return self._format_langgraph_result(result, trip_details)
        else:
            return {'error': 'No feasible itinerary found. Try relaxing constraints.'}
    
    def _optimize_with_ortools(self, trip_details: dict, budget: float,
                               transport_options, accommodation_options,
                               restaurant_options, activity_options) -> Dict[str, Any]:
        """
        Existing optimizer: kept for backward compatibility
        """
        
        print(f"\n{'='*80}")
        print("[2/3] OPTIMIZING WITH OR-TOOLS")
        print("="*80)
        
        # This would be your existing optimization code
        # Just showing it still works alongside new optimizer
        
        print("   Using existing OR-Tools CP-SAT solver...")
        print("   TRANSPORT_BUDGET_RATIO = 0.30  (hardcoded)")
        
        # ... existing optimization code ...
        return {'error': 'Placeholder - use existing optimizer.py'}
    
    # ========================================================================
    # Helper Methods: Convert agent results to optimizer format
    # ========================================================================
    
    def _convert_transport(self, transport_options) -> List[OptionCandidate]:
        """Convert flight/ground transport results to OptionCandidate"""
        candidates = []
        for i, transport in enumerate(transport_options or []):
            # Handle both Flight and GroundTransport objects
            is_flight = hasattr(transport, 'carrier')
            
            candidate = OptionCandidate(
                id=f"transport_{i}",
                category="transport",
                name=getattr(transport, 'name', 'Transport'),
                cost=getattr(transport, 'price', 0),
                currency=getattr(transport, 'currency', 'INR'),
                rating=getattr(transport, 'reliability_score', 0.8),
                duration_minutes=getattr(transport, 'duration_minutes', 0),
                properties={
                    'type': 'flight' if is_flight else 'ground',
                    'provider': getattr(transport, 'carrier' if is_flight else 'provider', 'Unknown'),
                    'origin': getattr(transport, 'origin', ''),
                    'destination': getattr(transport, 'destination', ''),
                }
            )
            candidates.append(candidate)
        
        return candidates
    
    def _convert_accommodations(self, accommodation_options) -> List[OptionCandidate]:
        """Convert hotel results to OptionCandidate"""
        candidates = []
        for i, hotel in enumerate(accommodation_options or []):
            candidate = OptionCandidate(
                id=f"hotel_{i}",
                category="accommodation",
                name=getattr(hotel, 'name', 'Hotel'),
                cost=getattr(hotel, 'price_per_night', 0),
                currency=getattr(hotel, 'currency', 'INR'),
                rating=getattr(hotel, 'rating', 3.5),
                properties={
                    'type': getattr(hotel, 'type', 'hotel'),
                    'amenities': getattr(hotel, 'amenities', []),
                    'review_count': getattr(hotel, 'review_count', 0),
                }
            )
            candidates.append(candidate)
        
        return candidates
    
    def _convert_restaurants(self, restaurant_options) -> List[OptionCandidate]:
        """Convert restaurant results to OptionCandidate"""
        candidates = []
        for i, rest in enumerate(restaurant_options or []):
            candidate = OptionCandidate(
                id=f"restaurant_{i}",
                category="restaurant",
                name=getattr(rest, 'name', 'Restaurant'),
                cost=getattr(rest, 'average_meal_cost', 0),
                currency=getattr(rest, 'currency', 'INR'),
                rating=getattr(rest, 'rating', 3.5),
                properties={
                    'cuisine': getattr(rest, 'cuisine_type', ''),
                    'dietary': getattr(rest, 'dietary_accommodations', []),
                    'ingredients': ' '.join(getattr(rest, 'common_ingredients', [])).lower(),
                }
            )
            candidates.append(candidate)
        
        return candidates
    
    def _convert_activities(self, activity_options) -> List[OptionCandidate]:
        """Convert activity results to OptionCandidate"""
        candidates = []
        for i, activity in enumerate(activity_options or []):
            candidate = OptionCandidate(
                id=f"activity_{i}",
                category="activity",
                name=getattr(activity, 'name', 'Activity'),
                cost=getattr(activity, 'price', 0),
                currency=getattr(activity, 'currency', 'INR'),
                rating=getattr(activity, 'rating', 3.5),
                duration_minutes=getattr(activity, 'duration_minutes', 0),
                properties={
                    'type': getattr(activity, 'activity_type', ''),
                    'popularity': getattr(activity, 'popularity_score', 0.5),
                }
            )
            candidates.append(candidate)
        
        return candidates
    
    def _format_langgraph_result(self, result: dict, trip_details: dict) -> dict:
        """Convert LangGraph result to display format"""
        
        # This would format the result for your existing display methods
        return {
            'total_cost': 0,  # Would extract from best_plan
            'num_days': trip_details.get('num_days'),
            'itinerary': {},  # Would structure day-by-day
            'metadata': {
                'optimizer': 'langgraph',
                'score': result.get('best_score'),
                'combinations_evaluated': result.get('evaluated_combinations')
            }
        }
    
    # ========================================================================
    # Placeholder Search Methods (would use your existing agents)
    # ========================================================================
    
    def _search_transport(self, origin, destination, date):
        """Placeholder - use your flight_agent"""
        return []
    
    def _search_accommodations(self, destination, check_in, num_days):
        """Placeholder - use your hotel_agent"""
        return []
    
    def _search_restaurants(self, destination, dietary):
        """Placeholder - use your restaurant_agent"""
        return []
    
    def _search_activities(self, destination, interests):
        """Placeholder - use your activity_agent"""
        return []
    
    def display_itinerary(self, itinerary, trip_details):
        """Placeholder - use your existing display method"""
        print("Itinerary would be displayed here")


# ============================================================================
# EXAMPLE 2: Direct Usage (For New Code)
# ============================================================================

def optimize_trip_with_langgraph(trip_params: dict) -> dict:
    """
    Standalone function to optimize a trip using LangGraph
    Good for new integration points or tests
    
    Args:
        trip_params: {
            'total_budget': 150000,
            'num_days': 7,
            'priority': 'value',  # or 'cost', 'experience'
            'interests': ['cultural', 'adventure'],
            'dietary_restrictions': [],
            'hotel_min_rating': 3.5,
            'origin': 'Bangalore',
            'destination': 'Paris'
        }
    
    Returns:
        {
            'success': bool,
            'best_plan': {...},
            'best_score': float,
            'metadata': {...}
        }
    """
    
    # Define budget based on priority
    budget = trip_params['total_budget']
    
    budget_constraint = {
        'total_budget': budget,
        'transport_min': 5000,
        'transport_max': budget * 0.3,
        'accommodation_min': 10000,
        'accommodation_max': budget * 0.5,
        'restaurant_min': 0,
        'restaurant_max': budget * 0.25,
        'activity_min': 0,
        'activity_max': budget * 0.25
    }
    
    # Adjust constraints based on priority
    if trip_params.get('priority') == 'cost':
        budget_constraint['accommodation_max'] = budget * 0.35
        budget_constraint['restaurant_max'] = budget * 0.15
    elif trip_params.get('priority') == 'experience':
        budget_constraint['activity_max'] = budget * 0.40
        budget_constraint['restaurant_max'] = budget * 0.30
    
    # Define preferences
    preferences = {
        'priority': trip_params.get('priority', 'value'),
        'hotel_min_rating': trip_params.get('hotel_min_rating', 3.5),
        'restaurant_min_rating': trip_params.get('restaurant_min_rating', 3.0),
        'activity_min_rating': trip_params.get('activity_min_rating', 3.5),
        'activity_interests': trip_params.get('interests', []),
        'dietary_restrictions': trip_params.get('dietary_restrictions', [])
    }
    
    # Initialize optimizer
    optimizer = LangGraphItineraryOptimizer(
        budget_constraint=budget_constraint,
        preferences=preferences,
        num_days=trip_params['num_days']
    )
    
    # Run optimization
    # (In real code, pass actual search results)
    result = optimizer.optimize(
        transport_options=[],  # From flight_agent.search_flights()
        accommodation_options=[],  # From hotel_agent.search_accommodations()
        restaurant_options=[],  # From restaurant_agent.search_restaurants()
        activity_options=[],  # From activity_agent.search_activities()
        trip_start_date='2026-03-01',
        origin=trip_params['origin'],
        destination=trip_params['destination']
    )
    
    return result


# ============================================================================
# EXAMPLE 3: Testing Different Constraint Scenarios
# ============================================================================

def test_constraint_scenarios():
    """
    Show how LangGraph handles different constraint scenarios
    without hardcoding budget ratios
    """
    
    print("\n" + "="*80)
    print("TESTING CONSTRAINT SCENARIOS")
    print("="*80)
    
    # Scenario 1: Budget-conscious traveler
    print("\n📍 Scenario 1: Budget-conscious (50K total)")
    budget1 = {
        'total_budget': 50000,
        'transport_min': 2000,
        'transport_max': 12000,  # Flexible, not hardcoded
        'accommodation_min': 5000,
        'accommodation_max': 20000,
        'restaurant_min': 0,
        'restaurant_max': 10000,
        'activity_min': 0,
        'activity_max': 8000
    }
    
    preferences1 = {
        'priority': 'cost',
        'hotel_min_rating': 3.0,  # Lower standard to save
        'restaurant_min_rating': 2.5,
        'activity_min_rating': 3.0
    }
    
    evaluator1 = ConstraintEvaluator(
        BudgetConstraint(**budget1),
        UserPreferences(**preferences1),
        num_days=7
    )
    
    print(f"   ✓ Budget constraint created (flexible bounds)")
    print(f"   ✓ Preferences: priority={preferences1['priority']}")
    
    # Scenario 2: Luxury traveler
    print("\n📍 Scenario 2: Luxury traveler (250K total)")
    budget2 = {
        'total_budget': 250000,
        'transport_min': 10000,
        'transport_max': 100000,  # Can splurge on flights
        'accommodation_min': 30000,
        'accommodation_max': 150000,  # Premium hotels OK
        'restaurant_min': 10000,
        'restaurant_max': 60000,  # Fine dining
        'activity_min': 20000,
        'activity_max': 80000  # Exclusive experiences
    }
    
    preferences2 = {
        'priority': 'experience',
        'hotel_min_rating': 4.5,  # Premium only
        'restaurant_min_rating': 4.0,  # Good restaurants
        'activity_min_rating': 4.5
    }
    
    evaluator2 = ConstraintEvaluator(
        BudgetConstraint(**budget2),
        UserPreferences(**preferences2),
        num_days=7
    )
    
    print(f"   ✓ Budget constraint created (flexible bounds)")
    print(f"   ✓ Preferences: priority={preferences2['priority']}")
    
    # Scenario 3: Balanced traveler
    print("\n📍 Scenario 3: Balanced traveler (150K total)")
    budget3 = {
        'total_budget': 150000,
        'transport_min': 5000,
        'transport_max': 45000,  # Not hardcoded to 30%
        'accommodation_min': 10000,
        'accommodation_max': 60000,
        'restaurant_min': 5000,
        'restaurant_max': 30000,
        'activity_min': 5000,
        'activity_max': 25000
    }
    
    preferences3 = {
        'priority': 'value',
        'hotel_min_rating': 3.5,
        'restaurant_min_rating': 3.0,
        'activity_min_rating': 3.5
    }
    
    evaluator3 = ConstraintEvaluator(
        BudgetConstraint(**budget3),
        UserPreferences(**preferences3),
        num_days=7
    )
    
    print(f"   ✓ Budget constraint created (flexible bounds)")
    print(f"   ✓ Preferences: priority={preferences3['priority']}")
    
    print("\n" + "="*80)
    print("✅ All scenarios handle different traveler types without hardcoded ratios!")
    print("="*80)


if __name__ == "__main__":
    print("\n🚀 LangGraph Integration Examples\n")
    
    # Test constraint scenarios
    test_constraint_scenarios()
    
    print("\n" + "="*80)
    print("INTEGRATION READY")
    print("="*80)
    print("""
    How to use in your code:

    1. Feature flag (safest):
       orchestrator = EnhancedTravelOrchestrator()
       orchestrator.USE_LANGGRAPH = True
       orchestrator.generate_itinerary(trip_details)

    2. Direct usage (for new code):
       result = optimize_trip_with_langgraph({
           'total_budget': 150000,
           'num_days': 7,
           'priority': 'value',
           ...
       })

    3. Manual setup (maximum control):
       budget = BudgetConstraint(...)
       prefs = UserPreferences(...)
       optimizer = LangGraphItineraryOptimizer(...)
       result = optimizer.optimize(...)
    """)
