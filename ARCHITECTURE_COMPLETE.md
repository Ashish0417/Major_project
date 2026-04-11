# Multi-Itinerary Selection System - Complete Architecture Guide

## System Overview

The multi-itinerary selection system allows users to view and select from multiple optimized itineraries generated using different strategies, rather than being forced to accept a single "best" option.

---

## Architecture Components

### 1. Strategy Methods (llm_orchestrator.py)

Three independent itinerary generation strategies:

#### A. One-by-One Expansion (`_fetch_with_expansion`)
- **Approach**: Cycle through agents (flight → ground → hotel → restaurant → activity)
- **Strategy**: Expand one agent at a time, try to optimize after each expansion
- **Best for**: Finding creative combinations where we cycle through different options
- **Future output**: List of 3 best itineraries

#### B. Parallel Expansion (`_fetch_with_parallel_expansion`)
- **Approach**: Expand all agents together each round
- **Strategy**: Increase all search spaces equally, try to optimize with expanded pool
- **Best for**: Quick exploration of broader solution space
- **Future output**: List of 2 best itineraries

#### C. Sequential Generation (`_fetch_with_sequential_generation`)
- **Approach**: Start with minimum required options, gradually expand
- **Strategy**: Request only what's needed (restaurants for all days, activities for all days), gradually increase diversity
- **Best for**: Memory-efficient generation, realistic minimum options
- **Future output**: List of 1 best itinerary (already simplest)

---

### 2. Selection Module (itinerary_selector.py)

#### ItineraryRanker
```
Input: List of (strategy_name, itinerary_data) tuples
        [
            ("One-by-One #1", {...}),
            ("One-by-One #2", {...}),
            ("Parallel #1", {...}),
            ("Sequential #1", {...}),
        ]

Process:
  1. Extract cost, duration, and metadata from each
  2. Calculate ranking score based on:
     - Budget efficiency (stay within budget)
     - Cost per day (value for money)
     - Optimization score (if available)
  3. Sort all itineraries by score (best first)

Output: List of (strategy_name, ItinerarySummary) tuples, sorted
        [
            ("One-by-One #1", summary1),  ← Best
            ("Parallel #1", summary2),
            ("One-by-One #2", summary3),
        ]
```

#### ItinerarySelector
```
Input: Ranked list of itineraries

Display:
  1. Group by strategy (show all One-by-One, then Parallel, then Sequential)
  2. Show cost and status for each
  3. Display top 3 ranked overall with detailed comparison
  4. Get user selection (1-3)

Output: (strategy_name, full_itinerary_data)
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────── ┐
│ USER INPUT (extract_trip_details)                             │
│ • Origin & Destination                                         │
│ • Dates (start, duration, or end)                             │
│ • Budget                                                       │
│ • Interests & Dietary Restrictions                            │
└──────────────────────┬──────────────────────────────────────── ┘
                        │
         ┌──────────────┴──────────────┐
         │ generate_itinerary()         │
         │ Performance Monitor starts   │
         │                              │
    ┌────▼─────────────────────────────┐
    │ ANALYSIS PHASE                    │
    │ • Trend analysis                  │
    │ • Seasonal suggestions            │
    └────┬──────────────────────────────┘
         │
    ┌────▼────────────────────────────────────────────────────┐
    │ THREE PARALLEL STRATEGIES                               │
    │                                                           │
    │ ┌──────────────────────────────────────────────────────┐│
    │ │ Strategy 1: One-by-One Expansion                    ││
    │ │   • Fetch agents iteratively                        ││
    │ │   • Expand one at a time                            ││
    │ │   → Returns: List of 3 itineraries [pending Phase 2]││
    │ └─────────────┬────────────────────────────────────────┘│
    │               │                                           │
    │ ┌──────────────▼────────────────────────────────────────┐│
    │ │ Strategy 2: Parallel Expansion                        ││
    │ │   • Fetch agents in parallel                         ││
    │ │   • Expand all together                              ││
    │ │   → Returns: List of 2 itineraries [pending Phase 2]││
    │ └─────────────┬────────────────────────────────────────┘│
    │               │                                           │
    │ ┌──────────────▼────────────────────────────────────────┐│
    │ │ Strategy 3: Sequential Generation                     ││
    │ │   • Start with minimum requirements                  ││
    │ │   • Gradually add diversity                          ││
    │ │   → Returns: List of 1 itinerary [pending Phase 2]  ││
    │ └─────────────┬────────────────────────────────────────┘│
    │               │                                           │
    └───────────────┼───────────────────────────────────────── ┘
                    │ (6 itineraries total)
         ┌──────────▼──────────────┐
         │ SELECTION PHASE          │
         │                          │
    ┌────▼──────────────────────────────────┐
    │ handle_itinerary_selection()           │
    │                                        │
    │ 1. Flatten results to:                 │
    │    [("One-by-One #1", {...}),          │
    │     ("One-by-One #2", {...}),          │
    │     ...]                               │
    │                                        │
    │ 2. Pass to ItineraryRanker             │
    └────┬───────────────────────────────────┘
         │ (Returns ranked list)
    ┌────▼──────────────────────────────────┐
    │ ItineraryRanker.rank_itineraries()     │
    │                                        │
    │ • Calculate efficiency scores          │
    │ • Sort by score                        │
    │ • Return sorted list                   │
    └────┬───────────────────────────────────┘
         │ (Ranked by cost/efficiency)
    ┌────▼──────────────────────────────────┐
    │ ItinerarySelector.display_and_select() │
    │                                        │
    │ Display:                               │
    │ 1. All grouped by strategy             │
    │ 2. Top 3 ranked overall                │
    │ 3. Detailed breakdown                  │
    │                                        │
    │ Get: User selection (1-3)              │
    └────┬───────────────────────────────────┘
         │ (Selected itinerary data)
    ┌────▼──────────────────────────────────┐
    │ OUTPUT PHASE                           │
    │                                        │
    │ 1. Save to MongoDB via                │
    │    HistoryManager.store_itinerary()   │
    │                                        │
    │ 2. Display day-by-day                 │
    │    display_itinerary()                 │
    │                                        │
    │ 3. Show performance metrics           │
    │    PerformanceMonitor.report()        │
    └────────────────────────────────────────┘
```

---

## Current Implementation Status (Phase 1 - Complete)

### What's Working Now ✅

1. **Itinerary Selector Module** (itinerary_selector.py)
   - Ranks itineraries by multiple criteria
   - Displays grouped by strategy + top 3 ranked
   - Interactive selection (choose 1-3)
   - Saves to database

2. **Integration in Orchestrator** (llm_orchestrator.py)
   - `handle_itinerary_selection()` method complete
   - Converts dict → flat list format
   - Calls ranker and selector
   - Saves selected option

3. **Database Storage** (history_manager.py)
   - Stores complete itinerary with metadata
   - Associates with user_id
   - Tracks selection timestamp

### Current Behavior

- Each of 3 strategies returns **1 itinerary**
- Total displayed: 3 options
- User selects best one
- **Flow works end-to-end**

---

## Pending Implementation (Phase 2 - Ready to Start)

### What's Needed

**Modify 3 methods to return MULTIPLE itineraries**:

1. `_fetch_with_expansion()` → Returns **3 best** (top 1%, 2%, 3% cost-efficient)
2. `_fetch_with_parallel_expansion()` → Returns **2 best** (top 1%, 2%)
3. `_fetch_with_sequential_generation()` → Returns **1 best**

**Total**: 6 options for user to compare

### Why This Matters

**Before**: User sees only 3 options (one per strategy)
- Can't compare variants within a strategy
- Less informed decision-making

**After**: User sees 6 options (best variants from each strategy)
- Can compare "one-by-one" strategy's alternatives
- See different cost/benefit tradeoffs
- More informed selection

---

## Example Workflow

### Scenario
```
Trip: Mumbai → Paris
Duration: 7 days
Budget: ₹200,000
Interests: Culture, Food
```

### Phase 1: Generation (Current)
```
┌─ One-by-One Expansion
│   └─ ✓ Found: ₹1,85,000 (1 best)
│
├─ Parallel Expansion  
│   └─ ✓ Found: ₹1,92,000 (1 best)
│
└─ Sequential Generation
    └─ ✓ Found: ₹1,78,000 (1 best)
    
Total: 3 options
```

### Phase 2: Generation (After Phase 2)
```
┌─ One-by-One Expansion
│   ├─ ✓ Found: ₹1,85,000 (most efficient)
│   ├─ ✓ Found: ₹1,88,000 (slightly less efficient)
│   └─ ✓ Found: ₹1,92,000 (least efficient but more variety)
│
├─ Parallel Expansion
│   ├─ ✓ Found: ₹1,82,000 (better than one-by-one #1)
│   └─ ✓ Found: ₹1,95,000 (similar to parallel #1 but different activities)
│
└─ Sequential Generation
    └─ ✓ Found: ₹1,78,000 (most budget-efficient overall)

Total: 6 options
```

### Phase 3: Ranking
```
Ranking Score Calculation:
  Option 1: Sequential #1     → ₹178,000 (Rank 1 - lowest cost)
  Option 2: Parallel #1       → ₹182,000 (Rank 2 - very close)
  Option 3: One-by-One #1     → ₹185,000 (Rank 3 - good value)
  Option 4: One-by-One #2     → ₹188,000 (Rank 4)
  Option 5: Parallel #2       → ₹195,000 (Rank 5)
  Option 6: One-by-One #3     → ₹192,000 (Rank 6 - highest)
```

### Phase 4: Display

```
📊 ALL GENERATED ITINERARIES (Grouped by Strategy)

🔹 ONE-BY-ONE
  One-by-One #1     | Cost: ₹1,85,000 | /Day: ₹26,429  | ✅ (Within Budget)
  One-by-One #2     | Cost: ₹1,88,000 | /Day: ₹26,857  | ✅ (Within Budget)
  One-by-One #3     | Cost: ₹1,92,000 | /Day: ₹27,429  | ✅ (Within Budget)

🔹 PARALLEL
  Parallel #1       | Cost: ₹1,82,000 | /Day: ₹26,000  | ✅ (Within Budget)
  Parallel #2       | Cost: ₹1,95,000 | /Day: ₹27,857  | ⚠️ (Slight Over)

🔹 SEQUENTIAL
  Sequential #1     | Cost: ₹1,78,000 | /Day: ₹25,429  | ✅ (Within Budget)

═════════════════════════════════════════════════════════════════════════════

🏆 TOP 3 BEST OPTIONS (Ranked Across All Strategies)

Rank | Strategy       | Total Cost | Cost/Day   | Status
─────┼────────────────┼────────────┼────────────┼──────────────
1️⃣   | Sequential #1  | ₹1,78,000  | ₹25,429   | ✅ Within
2️⃣   | Parallel #1    | ₹1,82,000  | ₹26,000   | ✅ Within  
3️⃣   | One-by-One #1  | ₹1,85,000  | ₹26,429   | ✅ Within
```

### Phase 5: Selection
```
User selects: One-by-One #1

Why? "I like the cultural focus even though it's slightly more expensive.
      The Louvre tour and cooking class match my interests perfectly."
```

### Phase 6: Storage & Display
```
✅ Itinerary saved to MongoDB
   
📋 SELECTED ITINERARY: One-by-One #1
═════════════════════════════════════════════════════════════

💵 Total Cost: ₹1,85,000
📅 Duration: 7 days
  
📋 Day-by-Day Itinerary:

DAY 1
  ✈️ 06:00 • Air India BOM→CDG | 12h 30m | ₹45,000
  🏨 15:00 • Hotel Le Marais Paris | Check-in | ₹12,000
  🍽️ 19:30 • Dinner - French bistro | ₹2,500

... (continue for 7 days)

Total Cost Breakdown:
  🛫 Transport     : ₹45,000
  🏨 Accommodation : ₹84,000
  🍽️ Restaurants   : ₹35,000
  🎭 Activities    : ₹21,000
  ─────────────────────────
  Total            : ₹1,85,000
```

---

## Code Examples

### Using the System (After Phase 2)

```python
from llm_orchestrator import TravelItineraryOrchestrator

orchestrator = TravelItineraryOrchestrator()

trip = {
    'origin_city': 'Mumbai',
    'destination_city': 'Paris',
    'departure_date': '2025-04-01',
    'num_days': 7,
    'budget_inr': 200000,
    'interests': ['culture', 'food'],
    'dietary_restrictions': ['vegetarian'],
    'user_id': 'user123'
}

# Generate itinerary
# Behind the scenes:
# 1. Each strategy generates multiple variants
# 2. Combines them all (6 total)
# 3. Ranks by efficiency
# 4. Displays top 3 + all grouped
# 5. Gets user selection
itinerary = orchestrator.generate_itinerary(trip)

# Returns:
# {
#   'total_cost': 185000,
#   'currency': 'INR',
#   'num_days': 7,
#   'itinerary': { 0: [...], 1: [...], ... },
#   'optimizer_metadata': { ... }
# }
```

---

## Performance Metrics

| Metric | Current | After Phase 2 | Impact |
|--------|---------|---------------|--------|
| Time per strategy | 30s | 90-150s | +3-5x (6 optimizations vs 1-3) |
| Total time (3 strategies) | ~90s | ~270-450s | +3-5x |
| Memory per strategy | ~5-10MB | ~15-30MB | +2-3x |
| Options shown to user | 3 | 6 | +100% |
| Optimization calls | 3-6 | 15-20 | +3-4x |

### Optimization Potential
- Early stopping if N plans found
- Parallel execution of strategies (currently sequential)
- Caching between optimization calls
- Adjusting expansion rates

---

## Error Handling

### Scenarios

1. **All strategies return None** (budget impossible)
   - User sees: "Budget too low, minimum suggested: ₹X"
   - Fallback: Return closest option (within 20% over)

2. **Some strategies fail**
   - Display: Only successful strategies' results
   - Minimum 2-3 options still shown

3. **No valid selection made** (user cancels)
   - Return: None
   - In workflow: Fall back to best single option

4. **Database save fails**
   - Display warning but continue
   - Show itinerary anyway, logged for retry

---

## Future Enhancements

### Phase 3: Advanced Features
- [ ] Export selected itinerary to PDF
- [ ] Email itinerary to user
- [ ] Share itinerary with friends
- [ ] Compare side-by-side details

### Phase 4: Refinements
- [ ] Post-selection itinerary editing
- [ ] "Similar options" recommendations
- [ ] Price change alerts
- [ ] Booking integration

### Phase 5: Personalization
- [ ] Learn user preferences from selections
- [ ] Suggest optimizations proactively
- [ ] Group discounts/packages
- [ ] Corporate group planning

---

## Testing Checklist

- [ ] Selection module imports without errors
- [ ] Ranking calculates scores correctly
- [ ] Display formats correctly with multiple options
- [ ] User selection returns correct itinerary
- [ ] Database stores selected option
- [ ] Each strategy returns correct number of plans
- [ ] All 6 plans sort and rank correctly
- [ ] Top 3 display prominently
- [ ] Budget overage penalties work
- [ ] Performance is acceptable

---

## Troubleshooting

### Issue: "Itinerary selector not available"
- **Cause**: `itinerary_selector.py` not imported
- **Fix**: Ensure imports at top of `llm_orchestrator.py`
- **Location**: Lines ~49

### Issue: "No valid itineraries after ranking"
- **Cause**: All strategies returned None or over budget
- **Fix**: Increase budget or adjust strategy parameters
- **Diagnostic**: Check individual strategy output

### Issue: Selection shows only 1-2 options
- **Cause**: Phase 2 modifications not yet applied
- **Fix**: Modify fetch methods to collect multiple plans
- **Reference**: `STRATEGY_MODIFICATION_GUIDE.md`

