# LangGraph Itinerary Optimizer - Integration Guide

## Overview

This guide explains how to integrate the new **LangGraph-based optimizer** into your existing TravelPlanner without breaking any existing code.

### Why LangGraph?

The new optimizer addresses limitations of hardcoded budget ratios:
- ✅ **Parallel exploration** of all option combinations
- ✅ **Dynamic constraint evaluation** - no hardcoded ratios
- ✅ **Intelligent backtracking** when constraints are violated
- ✅ **Flexible budget allocation** based on user preferences
- ✅ **Backward compatible** - existing code still works

---

## Architecture Comparison

### OLD APPROACH (Current - Still Works)
```
optimizer.py
├─ Hardcoded: TRANSPORT_BUDGET_RATIO = 0.30
├─ All budget distributions fixed
└─ Limited exploration of combinations
```

### NEW APPROACH (LangGraph)
```
langgraph_optimizer.py
├─ BudgetConstraint (flexible bounds)
├─ UserPreferences (dynamic priorities)
├─ ConstraintEvaluator (parallel checking)
└─ LangGraphItineraryOptimizer (explores all combinations)
```

---

## Key Components

### 1. **BudgetConstraint** - Flexible Budget Allocation
Instead of hardcoded ratios, define min/max for each category:

```python
from langgraph_optimizer import BudgetConstraint

# Old way (hardcoded ratio)
# transport_budget = total_budget * 0.30  ❌

# New way (flexible bounds)
budget = BudgetConstraint(
    total_budget=150000,
    
    # Define bounds for each category (None = unbounded)
    transport_min=5000,
    transport_max=30000,      # <- Can adjust based on situation
    
    accommodation_min=10000,
    accommodation_max=60000,  # <- Flexible, not hardcoded
    
    restaurant_min=3000,
    restaurant_max=20000,
    
    activity_min=2000,
    activity_max=15000
)
```

**Advantages:**
- Accommodations can be 50% of budget if needed (luxury trip)
- Activities can be 0% if user doesn't want them
- Transport is bounded but not locked to 30%
- User preferences drive allocation, not fixed ratios

### 2. **UserPreferences** - Define What Matters
```python
from langgraph_optimizer import UserPreferences

prefs = UserPreferences(
    # Travel style
    preferred_pace="balanced",        # fast, balanced, relaxed
    priority="value",                 # cost, time, experience, value
    
    # Quality constraints
    hotel_min_rating=3.5,
    restaurant_min_rating=3.0,
    activity_min_rating=3.5,
    
    # Activity distribution
    activity_interests=["cultural", "adventure"],
    dietary_restrictions=["vegetarian"],
    
    # Schedule constraints
    activities_per_day_min=1,
    activities_per_day_max=5,
    meals_per_day=2
)
```

### 3. **ConstraintEvaluator** - No Hardcoded Ratios
Evaluates plans based on:
- ✅ Budget constraints (min/max per category)
- ✅ Rating constraints (quality thresholds)
- ✅ Activity distribution (pace preferences)
- ✅ Dietary restrictions
- ✅ User priority (cost vs experience)

```python
from langgraph_optimizer import ConstraintEvaluator

evaluator = ConstraintEvaluator(budget, preferences, num_days=7)
score, violations = evaluator.evaluate_plan(plan)

# Returns:
# score: 0-100 (higher is better)
# violations: ["Transport over budget", "Hotel rating too low"]
```

### 4. **LangGraphItineraryOptimizer** - Parallel Exploration
```python
from langgraph_optimizer import LangGraphItineraryOptimizer

# Initialize
optimizer = LangGraphItineraryOptimizer(
    budget_constraint={
        'total_budget': 150000,
        'transport_min': 5000,
        'transport_max': 30000,
        # ... etc
    },
    preferences={
        'priority': 'value',
        'hotel_min_rating': 3.5,
        # ... etc
    },
    num_days=7
)

# Run optimization
result = optimizer.optimize(
    transport_options=[...],      # From flight_agent
    accommodation_options=[...],  # From hotel_agent
    restaurant_options=[...],     # From restaurant_agent
    activity_options=[...],       # From activity_agent
    trip_start_date='2026-03-01',
    origin='Bangalore',
    destination='Paris'
)

# Returns:
# {
#   'best_plan': {...},
#   'best_score': 87.5,
#   'evaluated_combinations': 42,
#   'backtrack_attempts': 2,
#   'success': True
# }
```

---

## Integration Steps (Non-Breaking)

### Step 1: Keep Existing Code Unchanged
The current `optimizer.py` and `llm_orchestrator.py` continue to work as-is.

### Step 2: Add LangGraph Import (Optional)
```python
# In llm_orchestrator.py
from langgraph_optimizer import LangGraphItineraryOptimizer

class TravelItineraryOrchestrator:
    def __init__(self):
        # ... existing code ...
        self.langgraph_optimizer = None  # Optional
```

### Step 3: Use Feature Flag (Recommended)
```python
# In generate_itinerary() method
USE_LANGGRAPH = True  # Toggle this to switch optimizers

if USE_LANGGRAPH:
    result = self._optimize_with_langgraph(trip_details)
else:
    result = self._optimize_with_ortools(trip_details)  # Current
```

### Step 4: Implement Wrapper Methods
```python
def _optimize_with_langgraph(self, trip_details):
    """Use LangGraph optimizer"""
    
    # Prepare budget constraint from trip details
    budget_constraint = {
        'total_budget': trip_details.get('budget_inr', 150000),
        'transport_min': 5000,
        'transport_max': 50000,
        'accommodation_min': 10000,
        'accommodation_max': None,  # Unbounded
        'restaurant_min': 0,
        'restaurant_max': 30000,
        'activity_min': 0,
        'activity_max': 20000
    }
    
    # Prepare preferences
    preferences = {
        'priority': trip_details.get('priority', 'value'),
        'activity_interests': trip_details.get('interests', []),
        'dietary_restrictions': trip_details.get('dietary', [])
    }
    
    # Run optimizer
    optimizer = LangGraphItineraryOptimizer(
        budget_constraint, preferences, trip_details.get('num_days', 7)
    )
    
    result = optimizer.optimize(
        transport_options=self.flight_agent.search_flights(...),
        accommodation_options=self.hotel_agent.search_accommodations(...),
        restaurant_options=self.restaurant_agent.search_restaurants(...),
        activity_options=self.activity_agent.search_activities(...),
        trip_start_date=trip_details.get('departure_date'),
        origin=trip_details.get('origin_city'),
        destination=trip_details.get('destination_city')
    )
    
    return result

def _optimize_with_ortools(self, trip_details):
    """Use existing OR-Tools optimizer"""
    # ... current code ...
    pass
```

---

## Workflow Comparison

### OLD: Hardcoded Ratios
```
Search all options
  ↓
Apply fixed budget distribution (30% transport, 30% hotel, etc.)
  ↓
Try to fit into these percentages
  ↓
If doesn't fit: relax constraints arbitrarily
```

### NEW: Dynamic Constraints
```
Search all options (parallel)
  ↓
Generate candidate combinations
  ↓
Evaluate each against flexible constraints
  ↓
Score based on user priority (cost/experience/balance)
  ↓
Backtrack and try alternatives if constraints violated
  ↓
Return best plan that satisfies all constraints
```

---

## Migration Path

### Phase 1: Coexist (Weeks 1-2)
- Keep old optimizer working
- Add LangGraph as optional feature
- Test with sample trips
- Feature flag controls which optimizer runs

### Phase 2: Gradual Adoption (Weeks 3-4)
- Have `llm_orchestrator.py` accept `optimizer_type` parameter
- Let users choose which optimizer to use
- Collect feedback on results

### Phase 3: Switch Default (Week 5+)
- Make LangGraph the default for new trips
- Keep old optimizer available as fallback
- Deprecate hardcoded ratios

---

## Example: How It Works

### Scenario
User: "Plan a trip to Tokyo for 7 days from Bangalore. I have 150K budget and love cultural experiences"

#### OLD APPROACH
```
Budget = 150K
Transport = 45K (30%)  ← HARDCODED
Hotel = 45K (30%)      ← HARDCODED
Food = 30K (20%)       ← HARDCODED
Activities = 30K (20%) ← HARDCODED

Problem: Cheapest hotel is 60K/night (420K total) - EXCEEDS!
Solution: Pick cheaper hotel with lower rating 😞
```

#### NEW APPROACH
```
BudgetConstraint:
  transport: 5K-30K
  accommodation: 10K-80K  ← Flexible upper bound
  restaurant: 5K-25K
  activity: 5K-30K        ← Flexible for experiences

Generate combinations:
  ✓ Cheap flight (10K) + Best hotel (70K) + Good restaurants (18K) + Activities (22K) = 120K ✓
  ✓ Mid flight (15K) + Mid hotel (50K) + Great restaurants (20K) + Activities (30K) = 115K ✓
  ✗ Expensive flight (25K) + Best hotel (70K) + ... = over budget

Score based on priority="experience":
  Plan 1: score 92 (best hotel + activities)
  Plan 2: score 88 (mid hotel + great restaurants)

Return Plan 1 (highest satisfaction for cultural experiences) 🎌
```

---

## Handling Complex Constraints

### Example: Multi-City Trip with Transport Between Cities

```python
# Current approach needs new hardcoded logic
# New approach: Just add more constraints

# Add inter-city transport constraint
evaluator.add_constraint({
    'type': 'distance_constraint',
    'max_travel_hours': 24,  # Max 1 day of travel
    'preferred_transport': 'flight'  # Between major cities
})

# Backtracking automatically handles this
# If 3 cities can't be reached in 7 days: suggests longer trip
```

### Example: Seasonal Pricing

```python
# Without hardcoding "shoulder season = X% more"
preferences.update({
    'season': 'peak',  # peak, shoulder, off-season
    'priority': 'experience'  # Willing to pay for best experience
})

# Evaluator scores plans based on:
# - Attraction quality (peak season better)
# - Price trade-off (user priority)
# - Activity availability
```

---

## Testing the New Optimizer

### Unit Test Example
```python
def test_langgraph_optimizer():
    """Test parallel exploration and backtracking"""
    
    budget = BudgetConstraint(
        total_budget=150000,
        transport_min=5000,
        transport_max=30000,
        accommodation_min=10000,
        accommodation_max=80000
    )
    
    prefs = UserPreferences(
        priority='value',
        hotel_min_rating=3.5
    )
    
    optimizer = LangGraphItineraryOptimizer(
        budget.__dict__,
        prefs.__dict__,
        num_days=7
    )
    
    result = optimizer.optimize(
        transport_options=[...],
        accommodation_options=[...],
        restaurant_options=[...],
        activity_options=[...],
        trip_start_date='2026-03-01',
        origin='Bangalore',
        destination='Paris'
    )
    
    assert result['success']
    assert result['best_plan'] is not None
    assert result['best_score'] > 0
    print(f"✅ Test passed! Found plan with score {result['best_score']}")
```

---

## Advantages Summary

| Feature | Old (Hardcoded Ratio) | New (LangGraph) |
|---------|----------------------|-----------------|
| Budget flexibility | Fixed % | Min/max per category |
| Constraint checking | Sequential | Parallel |
| Backtracking | Manual | Automatic |
| Score calculation | Simple sum | Priority-based |
| Exploration | Limited | Comprehensive |
| Customization | Hard-coded | Pydantic models |
| User priorities | Limited | Fully configurable |
| Dietary/restrictions | Basic | Full integration |
| Seasonal awareness | None | Integrated |

---

## Troubleshooting

### Issue: "No feasible solution found"
**Solution:** Relax constraints
```python
# Too strict: hotel_min_rating=4.5, budget_max=20000
# Relaxed: hotel_min_rating=3.5, budget_max=30000

budget.accommodation_max = 50000  # Increase if needed
prefs.hotel_min_rating = 3.0      # Relax quality requirement
```

### Issue: "Plan violates too many constraints"
**Solution:** Check priorities
```python
# If priority='cost' but user picks expensive activities
prefs.priority = 'balance'  # Mix cost and experience

# Backtracking will explore more combinations
```

### Issue: "Explored too many combinations"
**Solution:** Limit options provided
```python
# Don't search 100 flights, use top 10
transport_options = flight_results[:10]

# Optimizer will still find best combination efficiently
```

---

## Q&A

**Q: Does this replace the existing optimizer?**
A: No, it's optional. Use feature flag to choose which one to run.

**Q: Will it break existing trips?**
A: No, keep using old code if you prefer. New code is additive.

**Q: How much slower is parallel exploration?**
A: Actually faster because it evaluates combinations intelligently, not exhaustively.

**Q: Can I mix both optimizers?**
A: Yes! Use OR-Tools for simple trips, LangGraph for complex ones.

**Q: How do I debug constraint violations?**
A: `evaluator.evaluate_plan()` returns detailed violation list.

---

## Next Steps

1. **Try it:** Run `python langgraph_optimizer_example.py`
2. **Test:** Integration tests in `test_langgraph.py`
3. **Integrate:** Add to `llm_orchestrator.py` with feature flag
4. **Monitor:** Compare results with old optimizer
5. **Deploy:** Switch default when confident

---

## Support

For issues or questions:
1. Check constraint definitions (budget min/max reasonable?)
2. Print intermediate plans and scores
3. Enable logging: `logging.basicConfig(level=logging.DEBUG)`
4. Test with simpler constraints first

