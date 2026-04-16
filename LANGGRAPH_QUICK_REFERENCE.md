# LangGraph Integration - Quick Reference

## 🎯 One-Liner Summary
LangGraph optimizer replaces hardcoded budget ratios (30% transport) with **flexible dynamic constraints** that adapt to each trip, using **parallel exploration** and **intelligent backtracking**.

---

## ⚡ 30-Second Setup

```python
# Step 1: In llm_orchestrator.py, line 71
class TravelItineraryOrchestrator:
    USE_LANGGRAPH = True  # ✅ Enable LangGraph

# Step 2: Run your code
orchestrator = TravelItineraryOrchestrator()
result = orchestrator.generate_itinerary({...})

# Done! Now uses LangGraph with dynamic constraints 🚀
```

---

## 📊 Old vs New (Side-by-Side)

```
OLD (Hardcoded)                   NEW (Dynamic)
├─ Transport: 30% fixed      ├─ Transport: 5K-50K flexible
├─ Hotel: 30% fixed          ├─ Hotel: 10K-80K flexible
├─ Food: 20% fixed           ├─ Food: 0-25K optional
├─ Activities: 20% fixed     ├─ Activities: 0-25K optional
├─ Sequential evaluation     ├─ Parallel evaluation
└─ Single path               └─ Multiple paths + backtracking
```

**Result**: Better plans for each destination ✨

---

## 🔧 Key Components

| File | What | When to Use |
|------|------|-------------|
| `langgraph_optimizer.py` | Core optimizer | Never import directly (use feature flag) |
| `llm_orchestrator.py` | Main entry | Always use (handles both optimizers) |
| `langgraph_optimizer_example.py` | Examples | For reference only |
| `LANGGRAPH_INTEGRATION_GUIDE.md` | Detailed docs | For deep understanding |

---

## 💡 Budget Constraint Example

### OLD (Hardcoded ❌)
```python
TRANSPORT_BUDGET_RATIO = 0.30  # Always 30%
# Problem: Paris hotels are expensive!
# Paris trip (150K): Transport = 45K, Hotel = 45K (INSUFFICIENT!)
```

### NEW (Flexible ✅)
```python
budget_constraint = {
    'total_budget': 150000,
    'transport_max': 30000,    # Not hardcoded %, actual amount
    'accommodation_max': 80000, # Can exceed 30% if needed!
    'restaurant_max': 25000,
    'activity_max': 25000
}
# Paris trip (150K): Transport = 20K, Hotel = 70K (PERFECT!)
```

---

## 📍 Existing Code Still Works

```python
# Your existing code - NO CHANGES NEEDED
orchestrator = TravelItineraryOrchestrator()
orchestrator.USE_LANGGRAPH = False  # Uses old optimizer

result = orchestrator.generate_itinerary({
    'destination_city': 'Tokyo',
    'num_days': 7,
    'budget_inr': 150000
})

# Still gets good itinerary with OR-Tools ✅
```

---

## 🚀 Enable LangGraph (3 ways)

### Way 1: Feature Flag (Recommended)
```python
orchestrator = TravelItineraryOrchestrator()
orchestrator.USE_LANGGRAPH = True
result = orchestrator.generate_itinerary(...)
```

### Way 2: Direct Usage (Advanced)
```python
from langgraph_optimizer import LangGraphItineraryOptimizer

optimizer = LangGraphItineraryOptimizer(budget, prefs, num_days)
result = optimizer.optimize(flights, hotels, restaurants, activities, ...)
```

### Way 3: Examples (For Learning)
```python
# See langgraph_optimizer_example.py
# EnhancedTravelOrchestrator class shows integration pattern
```

---

## ✨ What's Different in Output

### Old Output
```
✅ Optimization complete!
Total cost: INR 145,000
```

### New Output
```
✅ LangGraph found optimal plan!
Score: 87.5/100
Combinations evaluated: 42
Backtrack attempts: 2

✅ Optimization complete!
Total cost: INR 142,000
```

---

## 🧪 Quick Test

```python
# Test that both optimizers work
orchestrator = TravelItineraryOrchestrator()

# Test old
orchestrator.USE_LANGGRAPH = False
result1 = orchestrator.generate_itinerary(trip_details)
print(f"OR-Tools: {result1['total_cost']}")

# Test new
orchestrator.USE_LANGGRAPH = True
result2 = orchestrator.generate_itinerary(trip_details)
print(f"LangGraph: {result2['total_cost']}")
print(f"Score: {result2['optimizer_metadata']['score']}")

# Compare results!
```

---

## 📋 File Checklist

- ✅ `langgraph_optimizer.py` - Created
- ✅ `langgraph_optimizer_example.py` - Created
- ✅ `LANGGRAPH_INTEGRATION_GUIDE.md` - Created
- ✅ `LANGGRAPH_IMPLEMENTATION_SUMMARY.md` - Created (this)
- ✅ `llm_orchestrator.py` - Modified (backward compatible)
- ✅ `requirements.txt` - Updated

---

## 🎯 Common Use Cases

### 1. Try LangGraph on a test trip
```python
orchestrator.USE_LANGGRAPH = True
# Run one trip to see results
```

### 2. Compare both optimizers
```python
# Run same trip with both, compare scores/costs
```

### 3. Custom budget allocation
```python
budget = {
    'total_budget': 200000,
    'transport_min': 10000,
    'transport_max': 100000,  # Flexible!
    'accommodation_min': 50000,
    'accommodation_max': None,  # No upper limit!
    # ...
}
# Customize for each trip!
```

### 4. Different traveler types
```python
# Budget traveler
budget['accommodation_max'] = 20000

# Luxury traveler
budget['accommodation_max'] = 150000

# Same optimizer, different constraints
```

---

## ❓ FAQ

**Q: Does this break existing trips?**
A: No. `USE_LANGGRAPH = False` by default. Old optimizer still works.

**Q: How do I switch back if something goes wrong?**
A: Just set `USE_LANGGRAPH = False`. Takes 1 second.

**Q: Do I need to install anything?**
A: `pip install langgraph` (already done if you followed setup).

**Q: Will it be slower?**
A: Typically faster (smart exploration vs brute force).

**Q: Can I customize constraints?**
A: Yes! See `BudgetConstraint` and `UserPreferences` classes.

---

## 📞 Quick Troubleshoot

| Problem | Solution |
|---------|----------|
| ImportError: langgraph | `pip install langgraph` |
| "No feasible solution" | Increase `_max` budget bounds |
| Slow optimization | Reduce `max_combinations` limit |
| Want old behavior | Set `USE_LANGGRAPH = False` |

---

## 🎓 Architecture (5-Minute Version)

```
Your Code
    ↓
llm_orchestrator.py (generate_itinerary)
    ↓
Feature Flag Check (USE_LANGGRAPH)
    ├─ True → langgraph_optimizer.py
    │         ├─ Define flexible budget constraints
    │         ├─ Generate combinations (parallel)
    │         ├─ Evaluate each plan
    │         ├─ Backtrack if needed
    │         └─ Return best plan with score
    └─ False → optimizer.py
              ├─ Define hardcoded budget ratios
              ├─ Fit options into percentages
              └─ Return optimized itinerary
    ↓
Result (same format either way)
```

---

## 🚀 Deployment Roadmap

```
Week 1-2: Test locally
├─ Enable USE_LANGGRAPH = True
├─ Run sample trips
└─ Compare results with OR-Tools

Week 3-4: Gradual rollout
├─ Enable for beta users
├─ Collect feedback
└─ Monitor performance

Week 5+: Full deployment
├─ Make LangGraph default
├─ Keep OR-Tools as fallback
└─ Deprecate hardcoded ratios
```

---

## 💾 Remember

1. **Backward compatible** - Old code still works
2. **Feature flagged** - Easy to switch
3. **No hardcoded ratios** - Dynamic constraints
4. **Intelligent exploration** - Parallel + backtracking
5. **User-aware** - Adapts to priorities

---

## 📖 For More Details

- **Integration details**: See `LANGGRAPH_INTEGRATION_GUIDE.md`
- **Full implementation**: See `LANGGRAPH_IMPLEMENTATION_SUMMARY.md`
- **Code examples**: See `langgraph_optimizer_example.py`
- **Core optimizer**: See `langgraph_optimizer.py`

---

**Status**: ✅ Ready to use
**Last Updated**: February 12, 2026
