# Phase 2 Implementation - Exact Code Changes

This document shows the exact code changes needed for Phase 2.

---

## Modification 1: `_fetch_with_expansion()` (Lines ~800-900)

### Step 1: Add collection at method start

**Location**: First lines after method definition

```python
# BEFORE (OLD CODE):
def _fetch_with_expansion(
    self,
    origin_code: str,
    # ... parameters ...
) -> Optional[dict]:
    
    # ── PRE-CHECK: estimate minimum possible cost ──────────────────────────
    def _estimate_min_cost(destination, departure_date, return_date, num_days):
        # ... existing code ...
    
# AFTER (NEW CODE):
def _fetch_with_expansion(
    self,
    origin_code: str,
    # ... parameters ...
) -> Optional[dict]:  # NOTE: Return type CHANGES to List[dict] after Phase 2
    
    # ┌──────────── ADD THIS ──────────────┐
    # │ Collection for multiple itineraries │
    # └─────────────────────────────────────┘
    valid_itineraries = []  # ← ADD THIS LINE
    best_plan_overall = None
    best_cost_overall = float('inf')
    
    # ── PRE-CHECK: estimate minimum possible cost ──────────────────────────
    def _estimate_min_cost(destination, departure_date, return_date, num_days):
        # ... existing code (unchanged) ...
```

### Step 2: Change early returns in expansion rounds

**Location**: Round 0 and Rounds 1+ sections

```python
# ──────────── CHANGE #1: Round 0 ──────────────

# BEFORE:
if is_feasible:
    print(f"   ✅ Round 0: feasible plan found with initial search!")
    return result

# AFTER:
if is_feasible:
    valid_itineraries.append(result)  # ← CHANGE: Append instead of return
    print(f"   ✅ Round 0: found feasible plan #{len(valid_itineraries)}")
    # Don't return - continue to find more alternatives


# ──────────── CHANGE #2: Rounds 1+ (in expansion loop) ──────────────

# BEFORE (find in the middle of the rounds loop):
if is_feasible:
    print(f"   ✅ Sub-method 1: feasible plan found "
        f"(round {round_num+1}, agent '{expanding_agent}')")
    if perf_monitor:
        perf_monitor.finish_step("Expansion Rounds")
    return result

# AFTER (same location, replace the entire if block):
if is_feasible:
    valid_itineraries.append(result)  # ← CHANGE: Append instead of return
    print(f"   ✅ Found feasible plan #{len(valid_itineraries)} "
        f"(round {round_num+1}, agent '{expanding_agent}')")
    # Don't return yet - continue expanding for more alternatives
```

### Step 3: Replace final return with list return

**Location**: Very end of method (after all rounds complete)

```python
# BEFORE:
print("   ❌ Sub-method 1: no feasible plan after "
    f"{max_rounds} rounds")
print(f"   💡 Best effort cost: INR {best_cost_overall:.0f} (budget: INR {budget:.0f})")
print(f"   📊 Shortfall: INR {best_cost_overall - budget:.0f}")

if perf_monitor:
    perf_monitor.finish_step("Expansion Rounds")

# Return best effort if close enough (within 20% of budget)
if best_cost_overall <= budget * 1.2:
    print(f"   ✓ Returning best effort (only {((best_cost_overall / budget - 1) * 100):.0f}% over)")
    return best_plan_overall

# Budget is impossible - suggest realistic budget
print(f"   💰 Suggested minimum budget: INR {best_cost_overall:.0f}")
return None   # caller decides what to do


# AFTER (replace the entire ending):
if perf_monitor:
    perf_monitor.finish_step("Expansion Rounds")

# Return collected plans instead of None/single
if valid_itineraries:
    # Sort by cost (lowest first = best value)
    valid_itineraries.sort(key=lambda p: p.get('total_cost', float('inf')))
    
    print(f"   ✅ Sub-method 1: found {len(valid_itineraries)} feasible plan(s)")
    print(f"   📊 Costs: ", end="")
    for i, plan in enumerate(valid_itineraries[:3]):  # Show top 3 costs
        print(f"Plan #{i+1}: ₹{plan.get('total_cost', 0):.0f}", end=" | " if i < 2 else "\n")
    
    # Return top 3 plans
    result_to_return = valid_itineraries[:3]
    print(f"   🎯 Returning top 3 plans: {[p.get('total_cost') for p in result_to_return]}")
    return result_to_return

# No feasible plans found
print("   ❌ Sub-method 1: no feasible plan after "
    f"{max_rounds} rounds")
print(f"   💡 Best effort cost: INR {best_cost_overall:.0f} (budget: INR {budget:.0f})")

if best_cost_overall <= budget * 1.2:
    print(f"   ✓ Returning best effort as single plan")
    return [best_plan_overall]  # Return as list with 1 item

# Budget is impossible
print(f"   💰 Suggested minimum budget: INR {best_cost_overall:.0f}")
return None
```

---

## Modification 2: `_fetch_with_parallel_expansion()` (Lines ~1100-1200)

### Step 1: Add collection at method start

```python
# AFTER the minimum cost check:
if min_possible > budget:
    # ... existing check code ...
    return {"error": "budget_too_low", "min_required": min_possible}

# ┌──────────── ADD THIS ──────────────┐
valid_itineraries = []  # ← ADD THIS LINE
best_plan_overall = None
best_cost_overall = float('inf')
# └───────────────────────────────────┘

if initial_counts is None:
    # ... rest of existing code ...
```

### Step 2: Change early returns in parallel rounds

```python
# ──────────── CHANGE #1: Round 0 ──────────────

# BEFORE:
if is_feasible:
    print(f"   ✅ Parallel expansion: feasible plan found in Round 0")
    return result

# AFTER:
if is_feasible:
    valid_itineraries.append(result)
    print(f"   ✅ Parallel expansion: found plan #{len(valid_itineraries)} in Round 0")
    # Continue to find more alternatives


# ──────────── CHANGE #2: Rounds 1+ (in rounds loop) ──────────────

# BEFORE:
if is_feasible:
    print(f"   ✅ Parallel expansion: feasible plan found in Round {round_num+1}")
    if perf_monitor:
        perf_monitor.finish_step("Parallel Expansion Rounds")
    return result

# AFTER:
if is_feasible:
    valid_itineraries.append(result)
    print(f"   ✅ Parallel expansion: found plan #{len(valid_itineraries)} in Round {round_num+1}")
    # Don't return - continue expanding
```

### Step 3: Replace final return

```python
# BEFORE:
if perf_monitor:
    perf_monitor.finish_step("Parallel Expansion Rounds")

print("   ❌ Parallel expansion: no feasible plan after "
    f"{max_rounds} rounds")
print(f"   💡 Best effort cost: INR {best_cost_overall:.0f} (budget: INR {budget:.0f})")
print(f"   📊 Shortfall: INR {best_cost_overall - budget:.0f}")

if best_cost_overall <= budget * 1.2:
    print(f"   ✓ Returning best effort (only {((best_cost_overall / budget - 1) * 100):.0f}% over)")
    return best_plan_overall

print(f"   💰 Suggested minimum budget: INR {best_cost_overall:.0f}")
return None


# AFTER:
if perf_monitor:
    perf_monitor.finish_step("Parallel Expansion Rounds")

# Return collected plans
if valid_itineraries:
    valid_itineraries.sort(key=lambda p: p.get('total_cost', float('inf')))
    
    print(f"   ✅ Parallel expansion: found {len(valid_itineraries)} feasible plan(s)")
    print(f"   📊 Costs: ", end="")
    for i, plan in enumerate(valid_itineraries[:2]):  # Top 2 for parallel
        print(f"Plan #{i+1}: ₹{plan.get('total_cost', 0):.0f}", end=" | " if i < 1 else "\n")
    
    # Return top 2 plans (parallel returns 2)
    result_to_return = valid_itineraries[:2]
    print(f"   🎯 Returning top 2 plans")
    return result_to_return

print("   ❌ Parallel expansion: no feasible plan after "
    f"{max_rounds} rounds")
print(f"   💡 Best effort cost: INR {best_cost_overall:.0f} (budget: INR {budget:.0f})")

if best_cost_overall <= budget * 1.2:
    print(f"   ✓ Returning best effort as single plan")
    return [best_plan_overall]

print(f"   💰 Suggested minimum budget: INR {best_cost_overall:.0f}")
return None
```

---

## Modification 3: `_fetch_with_sequential_generation()` (Lines ~1400-1500)

### Step 1: Add collection at method start

```python
# AFTER the minimum cost check:
if min_possible > budget:
    # ... existing check code ...
    return {"error": "budget_too_low", "min_required": min_possible}

# ┌──────────── ADD THIS ──────────────┐
valid_itineraries = []  # ← ADD THIS LINE
best_plan_overall = None
best_cost_overall = float('inf')
# └───────────────────────────────────┘

def _sequential_init_counts(num_days, MEALS_PER_DAY=2, ACTIVITIES_PER_DAY=2):
    # ... rest of existing code ...
```

### Step 2: Change early returns in iterations

```python
# ──────────── CHANGE in iterations loop ──────────────

# BEFORE:
if is_feasible:
    print(f"   ✅ Sequential generation: feasible plan found in iteration {iteration + 1}")
    return result

# AFTER:
if is_feasible:
    valid_itineraries.append(result)
    print(f"   ✅ Sequential generation: found plan in iteration {iteration + 1}")
    # For sequential, could early-exit here if only want 1:
    # But continue to find alternative if available
    # (keeps same behavior but with potential for alternatives)
```

### Step 3: Replace final return

```python
# BEFORE:
print(f"   ❌ Sequential generation: no feasible plan after {iteration + 1} iterations")
print(f"   💡 Best effort cost: INR {best_cost_overall:.0f} (budget: INR {budget:.0f})")
print(f"   📊 Shortfall: INR {best_cost_overall - budget:.0f}")

if best_cost_overall <= budget * 1.2:
    print(f"   ✓ Returning best effort (only {((best_cost_overall / budget - 1) * 100):.0f}% over)")
    return best_plan_overall

print(f"   💰 Suggested minimum budget: INR {best_cost_overall:.0f}")
return None


# AFTER:
# Return collected plans (or best effort)
if valid_itineraries:
    valid_itineraries.sort(key=lambda p: p.get('total_cost', float('inf')))
    
    print(f"   ✅ Sequential generation: found {len(valid_itineraries)} feasible plan(s)")
    print(f"   📊 Cost: ₹{valid_itineraries[0].get('total_cost', 0):.0f}")
    
    # Sequential returns 1 (simplest)
    result_to_return = valid_itineraries[:1]
    print(f"   🎯 Returning best plan")
    return result_to_return

print(f"   ❌ Sequential generation: no feasible plan after {iteration + 1} iterations")
print(f"   💡 Best effort cost: INR {best_cost_overall:.0f} (budget: INR {budget:.0f})")

if best_cost_overall <= budget * 1.2:
    print(f"   ✓ Returning best effort as single plan")
    return [best_plan_overall]

print(f"   💰 Suggested minimum budget: INR {best_cost_overall:.0f}")
return None
```

---

## Summary of Changes

### Pattern Applied to All 3 Methods

1. **Add at start**:
   ```python
   valid_itineraries = []
   ```

2. **Change early returns to**:
   ```python
   valid_itineraries.append(result)  # Don't return
   ```

3. **Change final return to**:
   ```python
   if valid_itineraries:
       valid_itineraries.sort(key=lambda p: p.get('total_cost', float('inf')))
       return valid_itineraries[:N]  # N = 3, 2, or 1
   ```

### Lines to Search For

Use these search strings in your editor to find exact locations:

- `_fetch_with_expansion(` → Find method start
- `Round 0 not feasible` → Find round 0 return
- `✅ Sub-method 1: feasible plan found` → Find round N+ return  
- `❌ Sub-method 1: no feasible plan after` → Find final return

- `_fetch_with_parallel_expansion(` → Find method start
- `✅ Parallel expansion: feasible plan found in Round` → Find returns
- `❌ Parallel expansion: no feasible plan` → Find final return

- `_fetch_with_sequential_generation(` → Find method start
- `✅ Sequential generation: feasible plan found` → Find return
- `❌ Sequential generation: no feasible plan` → Find final return

---

## Testing After Each Modification

```python
# Quick test for One-by-One:
result = orchestrator._fetch_with_expansion(...)
assert isinstance(result, list), "Should return list"
assert len(result) <= 3, f"Should return max 3, got {len(result)}"
print(f"✅ Returns {len(result)} itineraries")

# Quick test for Parallel:
result = orchestrator._fetch_with_parallel_expansion(...)
assert isinstance(result, list), "Should return list"
assert len(result) <= 2, f"Should return max 2, got {len(result)}"
print(f"✅ Returns {len(result)} itineraries")

# Quick test for Sequential:
result = orchestrator._fetch_with_sequential_generation(...)
assert isinstance(result, list), "Should return list"
assert len(result) <= 1, f"Should return max 1, got {len(result)}"
print(f"✅ Returns {len(result)} itineraries")
```

---

## Rollback Strategy

If changes break the system:

1. **Revert to single return**:
   ```python
   # Change back:
   if is_feasible:
       return result  # Single item
   ```

2. **Comment out collection**:
   ```python
   # valid_itineraries = []  # Disable collection
   ```

3. **Test with revert** to confirm system works again

4. **Then try alternative approach** (e.g., call methods multiple times)

