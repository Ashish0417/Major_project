# LangGraph Integration - Visual Architecture Guide

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     TravelItineraryOrchestrator                 │
│                     (llm_orchestrator.py)                       │
│                                                                 │
│  USE_LANGGRAPH = True/False  ← FEATURE FLAG (YOUR CONTROL)    │
│                                                                 │
│  Public: generate_itinerary(trip_details)                       │
│    ├─ Search agents (same as before)                            │
│    ├─ Convert to optimizer format                               │
│    ├─ ┌─────────────────────────────────────────────┐           │
│    │ │ IF USE_LANGGRAPH:                            │           │
│    │ │   └─> _optimize_with_langgraph()             │           │
│    │ │       └─> LangGraphItineraryOptimizer       │           │
│    │ │           (new, dynamic, parallel)           │           │
│    │ │                                              │           │
│    │ │ ELSE:                                        │           │
│    │ │   └─> _optimize_with_ortools()               │           │
│    │ │       └─> ItineraryOptimizer                 │           │
│    │ │           (existing, hardcoded, sequential)  │           │
│    │ └─────────────────────────────────────────────┘           │
│    ├─ Add return journey                                        │
│    └─ Display formatted itinerary                               │
│                                                                 │
│  Methods:                                                       │
│    • _optimize_with_langgraph() [NEW]                           │
│    • _optimize_with_ortools() [NEW]                             │
│    • _convert_to_langgraph_format() [NEW]                       │
│    • _convert_langgraph_result() [NEW]                          │
│    • display_itinerary_with_transport() [EXISTING]              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │                                    │
         ↓                                    ↓
    ┌──────────────────┐           ┌────────────────────┐
    │   LangGraph      │           │    OR-Tools        │
    │   Optimizer      │           │    Optimizer       │
    │   [NEW]          │           │    [EXISTING]      │
    └──────────────────┘           └────────────────────┘
```

---

## Detailed LangGraph Optimizer Flow

```
LangGraphItineraryOptimizer
│
├─ __init__(budget_constraint, preferences, num_days)
│  ├─ Create BudgetConstraint
│  │  ├─ total_budget: 150000
│  │  ├─ transport_min: 5000, max: 30000
│  │  ├─ accommodation_min: 10000, max: 80000  ← NOT HARDCODED!
│  │  ├─ restaurant_min: 0, max: 25000
│  │  └─ activity_min: 0, max: 25000
│  │
│  ├─ Create UserPreferences
│  │  ├─ priority: 'value', 'cost', or 'experience'
│  │  ├─ hotel_min_rating: 3.5
│  │  ├─ activity_interests: [...]
│  │  └─ dietary_restrictions: [...]
│  │
│  ├─ Create ConstraintEvaluator
│  │  └─ Validates plans against constraints
│  │
│  └─ Build StateGraph
│     └─ Defines optimization flow
│
├─ optimize(transport_options, accommodation_options, ...)
│  │
│  ├─ [validate_input]
│  │  └─ Check options provided
│  │
│  ├─ [generate_candidates] ← PARALLEL STARTS HERE
│  │  ├─ Select top N options from each category
│  │  ├─ Generate combinations:
│  │  │  ├─ Transport[0] + Hotel[0] + Restaurant[0] + Activity[0]
│  │  │  ├─ Transport[0] + Hotel[0] + Restaurant[0] + Activity[1]
│  │  │  ├─ Transport[0] + Hotel[0] + Restaurant[1] + Activity[0]
│  │  │  ├─ ...
│  │  │  └─ Transport[3] + Hotel[3] + Restaurant[3] + Activity[3]
│  │  │
│  │  └─ Limit to MAX_COMBINATIONS (e.g., 50)
│  │     (Smart limitation: doesn't try all 100×100×100×100)
│  │
│  ├─ [evaluate_single] ← PARALLEL EACH COMBINATION
│  │  └─ For each candidate plan:
│  │     ├─ Calculate costs per category
│  │     ├─ Check budget bounds
│  │     ├─ Check quality ratings
│  │     ├─ Check activity distribution
│  │     ├─ Score based on user priority
│  │     └─ Generate violation list
│  │
│  ├─ [compare_plans]
│  │  ├─ Track best score so far
│  │  └─ Decide: continue / backtrack / finalize
│  │
│  ├─ [backtrack] ← INTELLIGENT RECOVERY
│  │  └─ If too many violations:
│  │     ├─ Relax constraints
│  │     ├─ Try different combinations
│  │     └─ Increment backtrack counter
│  │
│  └─ [finalize]
│     └─ Return best plan found
│        ├─ best_plan: {...}
│        ├─ best_score: 87.5
│        ├─ evaluated_combinations: 42
│        └─ backtrack_attempts: 2
│
└─ Return Result Dictionary
   └─ Success = True/False with metadata
```

---

## Constraint Evaluation Process

```
Plan Candidate:
├─ Transport: Flight A (20,000)
├─ Hotel: Hotel B (50,000)
├─ Restaurant: Restaurant C (15,000)
└─ Activity: Activity D (12,000)
   └─ Total: 97,000

                    ↓

ConstraintEvaluator.evaluate_plan()
│
├─ Check Total Budget
│  ├─ 97,000 <= 150,000? ✓
│  └─ Score: 100
│
├─ Check Transport Bounds
│  ├─ 20,000 min 5,000? ✓
│  ├─ 20,000 max 30,000? ✓
│  └─ Score: 100
│
├─ Check Accommodation Bounds
│  ├─ 50,000 min 10,000? ✓
│  ├─ 50,000 max 80,000? ✓ ← FLEXIBLE, NOT HARDCODED!
│  └─ Score: 100
│
├─ Check Ratings
│  ├─ Hotel rating 4.2 >= 3.5? ✓
│  ├─ Restaurant rating 3.8 >= 3.0? ✓
│  └─ Score: 100
│
├─ Check Activity Distribution
│  ├─ 1 activity / 7 days = 0.14 per day
│  ├─ >= min (1)? ✗ (only 1 activity)
│  └─ Score: -10 (penalty)
│
└─ Final Score = 90/100
   Violations = ["Not enough activities"]

                    ↓

Decision:
├─ Score > 70? → Keep this plan
├─ If violations:
│  ├─ Critical? → Backtrack
│  └─ Minor? → Continue exploring
└─ Best plan so far? → Save it
```

---

## Feature Flag Logic

```
generate_itinerary(trip_details)
│
└─ Check Feature Flag
   │
   ├─ USE_LANGGRAPH == True
   │  │
   │  ├─ LANGGRAPH_AVAILABLE?
   │  │  │
   │  │  ├─ Yes → Use LangGraph optimizer
   │  │  │        ├─ Flexible constraints
   │  │  │        ├─ Parallel exploration
   │  │  │        └─ Return with score
   │  │  │
   │  │  └─ No → Fallback to OR-Tools
   │  │         └─ Print warning
   │  │
   │  └─ (This allows graceful degradation)
   │
   └─ USE_LANGGRAPH == False
      │
      └─ Use OR-Tools optimizer (existing)
         ├─ Hardcoded ratios
         ├─ Sequential fitting
         └─ Return standard result
```

---

## Comparison: Single Plan Evaluation

```
SCENARIO: Paris trip, 150K budget

OLD APPROACH (OR-Tools):
┌─────────────────────────────────┐
│ Step 1: Allocate budgets        │
├─────────────────────────────────┤
│ Transport = 150K × 0.30 = 45K   │  ← HARDCODED
│ Hotel = 150K × 0.30 = 45K       │  ← HARDCODED
│ Food = 150K × 0.20 = 30K        │  ← HARDCODED
│ Activity = 150K × 0.20 = 30K    │  ← HARDCODED
├─────────────────────────────────┤
│ Step 2: Fit best options        │
├─────────────────────────────────┤
│ Cheapest flight ≤ 45K? ✓ (40K)  │
│ Best hotel ≤ 45K? ✗ (55K!)      │
│ (Cannot fit - must downgrade)    │
├─────────────────────────────────┤
│ Step 3: Compromise              │
├─────────────────────────────────┤
│ Flight 40K + Budget Hotel 45K... │  ← Not ideal!
│                                 │
│ Result: Lower hotel quality      │
└─────────────────────────────────┘

NEW APPROACH (LangGraph):
┌─────────────────────────────────┐
│ Step 1: Define flexible bounds   │
├─────────────────────────────────┤
│ Transport: 5K - 30K ← FLEXIBLE  │
│ Hotel: 10K - 80K ← FLEXIBLE    │
│ Food: 0 - 25K ← FLEXIBLE       │
│ Activity: 0 - 25K ← FLEXIBLE   │
├─────────────────────────────────┤
│ Step 2: Generate combinations   │
├─────────────────────────────────┤
│ Plan A: 20K + 70K + 20K + 25K = 135K ✓
│ Plan B: 15K + 65K + 25K + 20K = 125K ✓
│ Plan C: 25K + 50K + 25K + 30K = 130K ✓
├─────────────────────────────────┤
│ Step 3: Score & rank            │
├─────────────────────────────────┤
│ Plan A: score 92 (best hotel)   │
│ Plan B: score 85 (balance)      │
│ Plan C: score 78 (budget)       │
├─────────────────────────────────┤
│ Step 4: Select best             │
├─────────────────────────────────┤
│ Flight 20K + Premium Hotel 70K  │  ← Perfect match!
│ + Good Food 20K + Activities 25K│
│                                 │
│ Result: Best plan for Paris     │
└─────────────────────────────────┘
```

---

## State Graph Visualization

```
    START
      │
      ↓
┌─────────────────┐
│ validate_input  │
└────────┬────────┘
         │
         ↓
┌──────────────────────┐
│ generate_candidates  │
└────────┬─────────────┘
         │
         ↓ (if candidates)
    ╔════════════════════════╗
    ║ Parallel Branch        ║
    ║ (for each candidate)   ║
    ╚════════════════════════╝
         │
         ├─────────────────────────────┐
         │                             │
    [evaluate_single]            [evaluate_single]
         │                             │
         └──────────┬──────────────────┘
                    │
                    ↓
            ┌──────────────────┐
            │  compare_plans   │
            └────────┬─────────┘
                     │
         ┌───────────┼────────────┐
         │           │            │
    Continue?   Backtrack?    Finalize?
         │           │            │
         ↓           ↓            ↓
    [generate]  [backtrack]  [finalize]
         │           │            │
         └───────────┴────────────→
                     │
                     ↓
                   END
```

---

## Budget Constraint Flexibility

```
OLD (Hardcoded):
┌────────────────────────────────┐
│         150K Budget             │
├────────────────────────────────┤
│ Transport: [45K] (30% fixed)    │
│ Hotel:     [45K] (30% fixed)    │
│ Food:      [30K] (20% fixed)    │
│ Activity:  [30K] (20% fixed)    │
└────────────────────────────────┘
Can't change = inflexible

NEW (Dynamic):
┌────────────────────────────────┐
│         150K Budget             │
├────────────────────────────────┤
│ Transport: [5K ←→ 30K]          │
│ Hotel:     [10K ←→ 80K]         │
│ Food:      [0K ←→ 25K]          │
│ Activity:  [0K ←→ 25K]          │
└────────────────────────────────┘
Can adjust = flexible

Example Uses:
├─ Budget trip: Hotel: 5K-20K
├─ Luxury trip: Hotel: 50K-150K
├─ Food-focused: Food: 0-40K
└─ Activity-focused: Activity: 0-40K
```

---

## Integration Points with Existing Code

```
TravelItineraryOrchestrator (existing class)
│
├─ __init__() [MODIFIED]
│  └─ Added: USE_LANGGRAPH flag
│
├─ generate_itinerary() [MODIFIED]
│  ├─ Search agents (unchanged)
│  ├─ NEW: Feature flag decision point
│  │   ├─ if USE_LANGGRAPH → _optimize_with_langgraph()
│  │   └─ else → _optimize_with_ortools()
│  └─ Display result (unchanged)
│
├─ _optimize_with_langgraph() [NEW]
│  └─ Calls LangGraphItineraryOptimizer
│
├─ _optimize_with_ortools() [NEW]
│  └─ Calls existing ItineraryOptimizer
│
├─ _convert_to_langgraph_format() [NEW]
│  └─ Helper to format data
│
└─ ... rest of methods unchanged ...
```

---

## Deployment Stages

```
Stage 1: CURRENT (Testing)
┌─────────────────────────────────┐
│ USE_LANGGRAPH = False           │
│ (Old optimizer by default)      │
│ LangGraph available but unused  │
│ ✓ Existing code works as-is     │
└─────────────────────────────────┘
                │
                ↓ (when ready)
                
Stage 2: ROLLOUT (Gradual)
┌─────────────────────────────────┐
│ USE_LANGGRAPH = [Configurable]  │
│ (Choice per trip or user)       │
│ Both optimizers active          │
│ ✓ Gradual migration             │
└─────────────────────────────────┘
                │
                ↓ (when confident)
                
Stage 3: PRODUCTION (Default)
┌─────────────────────────────────┐
│ USE_LANGGRAPH = True            │
│ (New default)                   │
│ OR-Tools fallback               │
│ ✓ Full transition complete      │
└─────────────────────────────────┘
```

---

## Error Handling & Fallback

```
LangGraph Optimization Attempt
│
├─ Success?
│  ├─ Yes → Return LangGraph result ✓
│  └─ No → Check error type
│         │
│         ├─ Missing langgraph module?
│         │  └─ Fallback to OR-Tools
│         │
│         ├─ No feasible solution?
│         │  └─ Fallback to OR-Tools
│         │
│         ├─ Timeout?
│         │  └─ Fallback to OR-Tools
│         │
│         └─ Other error?
│            └─ Fallback to OR-Tools
│
└─ Always return valid itinerary
   (User gets result either way!)
```

---

## Data Flow Diagram

```
Input: trip_details
├─ origin, destination
├─ dates, budget
├─ interests, dietary
└─ other preferences
        │
        ↓
┌─────────────────────────────────┐
│ Search Agents                   │
├─────────────────────────────────┤
│ • FlightAgent.search_flights()  │
│ • HotelAgent.search_hotels()    │
│ • RestaurantAgent.search()      │
│ • ActivityAgent.search()        │
└─────────────────────────────────┘
        │
        ├─ flights: [{...}, {...}, ...]
        ├─ hotels: [{...}, {...}, ...]
        ├─ restaurants: [{...}, {...}, ...]
        └─ activities: [{...}, {...}, ...]
        │
        ↓
┌─────────────────────────────────┐
│ Feature Flag Decision            │
├─────────────────────────────────┤
│ if USE_LANGGRAPH:               │
│   → Convert to LangGraph format │
│   → Call LangGraphOptimizer     │
│ else:                           │
│   → Convert to OR-Tools format  │
│   → Call ORToolsOptimizer       │
└─────────────────────────────────┘
        │
        ↓
       Result
├─ selected options
├─ total cost
├─ day-by-day schedule
└─ metadata (optimizer info)
        │
        ↓
┌─────────────────────────────────┐
│ Display & Return                 │
├─────────────────────────────────┤
│ • Format itinerary              │
│ • Show optimization metadata    │
│ • Return to user                │
└─────────────────────────────────┘
```

---

**Note**: All diagrams are text-based for easy reference in documentation.
Use this guide to understand the integration at a glance!
