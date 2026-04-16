# Modifying Strategy Methods to Return Multiple Itineraries

## Overview
Currently each of the 3 strategy methods returns a single best itinerary. We need to modify them to collect and return multiple feasible itineraries.

---

## Strategy Method Specifications

| Method | Expected to Return | Logic |
|--------|-------------------|-------|
| `_fetch_with_expansion()` | 3 itineraries | Collect top 3 cost-efficient plans during expansion rounds |
| `_fetch_with_parallel_expansion()` | 2 itineraries | Collect top 2 cost-efficient plans during parallel rounds |
| `_fetch_with_sequential_generation()` | 1 itinerary | Can return single, but designed for flexible return |

---

## Modification Pattern for Each Method

### Common Pattern
Each method currently has this structure:

```python
def _fetch_with_X(...):
    # ... initialization ...
    
    for round_num in range(max_rounds):
        # ... fetch agents ...
        result = optimize(...)
        is_feasible = result.get('total_cost') <= budget
        
        if is_feasible:
            print("FOUND ONE!")
            return result  # ← EARLY EXIT, MUST CHANGE
        
        # ... continue loop ...
    
    print("NO PLANS FOUND")
    return None  # ← RETURN NONE AT END
```

### Required Changes Pattern

```python
def _fetch_with_X(...):
    valid_plans = []  # ← NEW: collect plans
    
    # ... initialization ...
    
    for round_num in range(max_rounds):
        # ... fetch agents ...
        result = optimize(...)
        is_feasible = result.get('total_cost') <= budget
        
        if is_feasible:
            valid_plans.append(result)  # ← APPEND, don't return
            print(f"Found plan #{len(valid_plans)}")
            
            # Continue expanding (don't return yet)
        
        # ... continue loop ...
    
    # Return collected plans instead of None
    if valid_plans:
        return valid_plans[:N]  # Return top N
    return None
```

---

## Detailed Modifications

### 1. `_fetch_with_expansion()` - Collect Top 3

**Location**: Lines ~800+ in llm_orchestrator.py

**Current Return**:
```python
if is_feasible:
    return result  # Returns 1 dict

# ... later ...
return None  # Returns None
```

**New Return**:
```python
if is_feasible:
    valid_plans.append(result)  # Collect, don't return

# ... after expansion loop ...
if valid_plans:
    # Sort by cost and return top 3
    valid_plans.sort(key=lambda p: p.get('total_cost', float('inf')))
    return valid_plans[:3]  # Top 3
return None
```

**Implementation Steps**:

1. **Initialize collection list at method start**:
```python
def _fetch_with_expansion(...):
    valid_plans = []  # ← ADD THIS
    best_plan_overall = None
    best_cost_overall = float('inf')
    
    # ... rest of method ...
```

2. **Change early return to append**:
```python
# OLD:
if is_feasible:
    print(f"   ✅ Sub-method 1: feasible plan found...")
    return result

# NEW:
if is_feasible:
    valid_plans.append(result)  # Append to collection
    print(f"   ✅ Found feasible plan #{len(valid_plans)}")
    # Continue looping to find more alternatives
```

3. **Update best tracking** (keep tracking for reference):
```python
# This already exists, just ensure it runs:
if current_cost < best_cost_overall:
    best_plan_overall = result
    best_cost_overall = current_cost
```

4. **Return collected plans at end**:
```python
# OLD:
print("❌ Sub-method 1: no feasible plan after...")
return None

# NEW:
if valid_plans:
    # Sort by cost (lowest first = best)
    valid_plans.sort(key=lambda p: p.get('total_cost', float('inf')))
    print(f"   ✅ Returning top {min(3, len(valid_plans))} plans")
    return valid_plans[:3]  # Top 3
else:
    print("❌ Sub-method 1: no feasible plan after...")
    if best_plan_overall and best_cost_overall <= budget * 1.2:
        print(f"   ✓ Returning best effort plan")
        return [best_plan_overall]  # Return as list with 1 item
    return None
```

---

### 2. `_fetch_with_parallel_expansion()` - Collect Top 2

**Location**: Lines ~1100+ in llm_orchestrator.py

**Same pattern as #1, but return top 2**:

```python
def _fetch_with_parallel_expansion(...):
    valid_plans = []  # ← ADD
    
    # ... initialization and rounds ...
    
    if is_feasible:
        valid_plans.append(result)  # ← APPEND
        print(f"   ✅ Found feasible plan #{len(valid_plans)}")
        # Continue looping
    
    # ... end of method ...
    
    if valid_plans:
        valid_plans.sort(key=lambda p: p.get('total_cost', float('inf')))
        print(f"   ✅ Returning top {min(2, len(valid_plans))} plans")
        return valid_plans[:2]  # ← Return top 2
    return None
```

---

### 3. `_fetch_with_sequential_generation()` - Collect Top 1

**Location**: Lines ~1400+ in llm_orchestrator.py

**Same pattern, but return just 1** (simplest change):

```python
def _fetch_with_sequential_generation(...):
    valid_plans = []  # ← ADD
    
    # ... initialization and iterations ...
    
    for iteration in range(5):
        # ... fetch and optimize ...
        
        if is_feasible:
            valid_plans.append(result)  # ← APPEND
            print(f"   ✅ Found feasible plan in iteration {iteration+1}")
            # Can early return here if only want 1:
            # return [result]
        
        # ... continue ...
    
    # ... end of method ...
    
    if valid_plans:
        valid_plans.sort(key=lambda p: p.get('total_cost', float('inf')))
        return valid_plans[:1]  # ← Return top 1 (as list)
    return None
```

---

## Key Changes Summary

| Aspect | Before | After |
|--------|--------|-------|
| Return type | `dict` or `None` | `List[dict]` or `None` |
| On finding feasible | Return immediately | Append to list, continue |
| End behavior | Return single result | Return sorted top-N |
| Example return | `{'total_cost': 5000, ...}` | `[{'total_cost': 4500, ...}, {'total_cost': 5200, ...}, ...]` |

---

## Updating `handle_itinerary_selection()`

The method has already been updated to handle both formats!

**Current code handles**:
```python
# If method returns dict (single)
if result_onebyones and "error" not in result_onebyones:
    flat_itineraries.append(("One-by-One #1", result_onebyones))

# Future-ready for list return:
if isinstance(result_onebyones, list):
    for i, plan in enumerate(result_onebyones):
        flat_itineraries.append((f"One-by-One #{i+1}", plan))
```

---

## Testing Individual Methods

### Test One-by-One Returns List

```python
from llm_orchestrator import TravelItineraryOrchestrator

orchestrator = TravelItineraryOrchestrator()

trip = {
    'origin_city': 'Mumbai',
    'destination_city': 'Paris',
    'departure_date': '2025-04-01',
    'num_days': 7,
    'budget_inr': 200000,
    'interests': ['culture', 'adventure']
}

# Should return list of 3
result = orchestrator._fetch_with_expansion(
    origin_code='BOM',
    dest_code='CDG',
    destination='Paris',
    departure_date='2025-04-01',
    return_date='2025-04-08',
    interests=['culture'],
    dietary=[],
    budget=200000,
    num_days=7,
    user_profile=None,
    trip_details=trip,
    max_rounds=2
)

assert isinstance(result, list), f"Expected list, got {type(result)}"
assert len(result) <= 3, f"Expected <=3 results, got {len(result)}"
print(f"✅ Got {len(result)} plans")
for i, plan in enumerate(result):
    print(f"  Plan #{i+1}: ₹{plan['total_cost']:,.0f}")
```

---

## Rollback Plan

If modifications cause issues:

1. **Revert individual method** back to returning single result:
```python
# Quickly revert to:
if is_feasible:
    return result  # Single item
```

2. **Revert return at end**:
```python
# Instead of list:
return best_plan_overall  # Single dict
```

3. **Update handle_itinerary_selection()** to handle None case

---

## Performance Considerations

### Memory Impact
- Currently: 1 itinerary stored per method = 3 total
- After changes: 3 + 2 + 1 = 6 itineraries
- Each itinerary dict is ~5-10KB, so ~30-60KB additional memory
- **Impact**: Negligible

### Execution Time
- Each method runs optimization ~3-5x more times
- Time per method: 30s → 90-150s
- Total time for 3 methods: 90s → 270-450s
- **Impact**: Moderate increase (3-5x), mostly due to optimization calls

### Optimization
If performance becomes issue:
1. Reduce max_rounds in each method
2. Set stricter "close enough" threshold (e.g., budget * 1.1 instead of 1.2)
3. Cache optimization results between round

---

## Backward Compatibility

The changes are **forward compatible**:
- Old code expecting single dict still works if we update `handle_itinerary_selection()` 
- Already done! Method checks for both list and dict
- No breaks to existing APIs

---

## Next Steps

1. Apply modifications to `_fetch_with_expansion()` ✓ Ready
2. Apply modifications to `_fetch_with_parallel_expansion()` ✓ Ready  
3. Apply modifications to `_fetch_with_sequential_generation()` ✓ Ready
4. Test end-to-end with sample trip
5. Verify UI displays all 6 options correctly
6. Verify ranking works as expected
7. Verify selection saves correctly

