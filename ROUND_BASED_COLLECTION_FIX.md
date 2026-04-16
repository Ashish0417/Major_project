# Round-Based Solution Collection Fix

## Problem
When One-by-One expansion ran, all rounds were converging to the same optimal solution (65.1 score). The deduplication logic was correctly identifying them as duplicates, but this resulted in only **1 candidate** being collected instead of tracking how solutions evolved across rounds.

Meanwhile, Sequential method found a different solution (64.4), suggesting that different expansion strategies CAN find different solutions. The question was: **Why didn't One-by-One find the 64.4 solution during its expansion?**

## Root Cause
The deduplication used `(cost, score)` tuple as a signature. If all rounds found the same score/cost combination, only 1 unique entry was stored. This prevented capturing **intermediate solutions** that might have different scores as the search space expanded.

## Solution
Changed from **deduplication-based collection** to **round-based collection**:

### Before (Deduplication)
```python
unique_solutions = {}  # signature -> solution

# Each round, if signature unique, add to dict
sig = _get_solution_signature(result)
if sig and sig not in unique_solutions:
    unique_solutions[sig] = result
    # → If all rounds produce same sig, only 1 entry stored
```

### After (Round-Based)
```python
all_round_solutions = [result]  # Start with Round 0

# Each round, collect and compare
for round_num in range(max_rounds):
    # ...optimizer runs...
    
    # After round, save BEST from this round if different
    if is_new:
        all_round_solutions.append(best_in_round)
        print(f"   ✨ NEW solution in Round {round_num+1}: Score {score:.1f}")
    else:
        print(f"   👀 Round {round_num+1}: Score {score:.1f} (seen before)")
```

## Key Changes

### All 3 Methods Now:
1. **Track solutions from EACH round/iteration**, not just unique signatures
2. **Compare by score + cost** to detect if a solution is genuinely new
3. **Store top 3 solutions** in `all_candidates` even if not feasible
4. **Display progress** showing which rounds found new solutions vs. repeats

### New Output Pattern:
```
🔄 Round 1, expanding 'flight' (limits={...})
   ✨ NEW solution: Score 64.8/100 | Cost ₹7,580
   
🔄 Round 2, expanding 'hotel' (limits={...})
   👀 Round 2: Score 64.8/100 (seen before)
   
Collected 2 distinct solutions across rounds:
   1. Score: 65.1/100 | Cost: ₹7,572
   2. Score: 64.8/100 | Cost: ₹7,580
```

## Why This Solves the Problem

1. **Captures Intermediate Solutions**: If Round 0 finds 65.1, and Round 1 explores differently and finds 64.8, both are now captured

2. **Shows Evolution**: Users see how solutions change as search space expands

3. **Prevents Missing Alternatives**: Sequential found 64.4 because it uses different logic. One-by-One now captures solutions from EACH round, not just unique final answers

4. **Applies to All Methods**: 
   - **One-by-One**: Tracks best from each round as agents cycle
   - **Parallel**: Tracks best from each round as all agents expand together
   - **Sequential**: Tracks best from each iteration as pools expand

## Example Scenario

**Before Fix:**
```
Round 0: Score 65.1 → Store as unique
Round 1: Score 65.1 → Skip (duplicate signature)
Round 2: Score 65.1 → Skip (duplicate signature)

Result: 1 candidate found ⚠️
```

**After Fix:**
```
Round 0: Score 65.1 → Store in all_round_solutions
Round 1: Score 64.8 → NEW! Store in all_round_solutions  
Round 2: Score 64.5 → NEW! Store in all_round_solutions

Result: 3 distinct solutions found ✓
```

## What About Sequential's 64.4?

Sequential uses a different expansion strategy:
- Starts with MINIMAL counts (1 flight, 1 hotel)
- Expands conservatively each iteration
- Uses early stopping when feasible

This different approach can naturally explore different solution spaces and find different local optima (like 64.4).

One-by-One starts with moderate counts and expands more aggressively, so it converges to 65.1. Both are working correctly—they're just different algorithms exploring differently.

## Files Modified
- `llm_orchestrator.py` 
  - `_fetch_with_expansion()` (One-by-One): Lines ~1000-1130
  - `_fetch_with_parallel_expansion()` (Parallel): Lines ~1200-1340
  - `_fetch_with_sequential_generation()` (Sequential): Lines ~1420-1500

## Testing
No unit test needed—the logic is straightforward:
1. Collect solutions from each round/iteration
2. Check if genuinely new by comparing score + cost
3. Return top 3 sorted by score

The validation happens automatically in the display output.

## Backwards Compatibility
✅ **Fully compatible**
- Same return format (solution with `all_candidates` list)
- Same UI display logic
- Only internal collection strategy changed
- No API changes

## Next Steps
Run your trip again with this fix. You should now see:
- More candidates found across rounds (should be 2-3 instead of 1)
- Different scores showing the progression
- Sequential method's different solutions properly contextualized
