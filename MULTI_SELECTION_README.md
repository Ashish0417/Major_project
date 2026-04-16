# 🎯 Multi-Itinerary Selection Feature

This document describes the new itinerary selection system that allows users to view and choose from the top 3 generated itineraries.

## Overview

The system now generates **3 different itineraries** using different strategies:
1. **One-by-One Expansion** - Cycles through agents, expanding one at a time
2. **Parallel Expansion** - Expands all agents together each round
3. **Sequential Generation** - Memory-optimized approach with early stopping

After generating all three, the system **ranks them** and shows the user the **top 3 options**. The user can then **select one** to view in detail and **save to the database**.

## Architecture

### New Modules

#### `itinerary_selector.py`
Contains the core selection logic:

- **`ItinerarySummary`**: Data class for itinerary summary with cost calculations
- **`ItineraryRanker`**: Ranks itineraries based on:
  - Budget efficiency (how close to budget)
  - Cost per day
  - Optimization score
  - Returns top-ranked itineraries

- **`ItinerarySelector`**: CLI interface for:
  - Displaying top 3 itineraries in a formatted table
  - Showing detailed breakdown for each option
  - Getting user selection via interactive input

- **`SaveItineraryHandler`**: Prepares itinerary data for database storage:
  - Extracts daily schedules
  - Formats costs and details
  - Prepares MongoDB/in-memory storage format

### Modified Files

#### `llm_orchestrator.py`
Added methods:
- `handle_itinerary_selection()` - Main orchestrator for ranking and selection
- `save_selected_itinerary()` - Saves chosen itinerary to database
- Updated `generate_itinerary()` to use new selection system

Modified workflow:
1. Generate 3 itineraries using different strategies
2. Call `handle_itinerary_selection()` to rank and display options
3. Get user's selection
4. Save selected itinerary using history_manager

## Usage

### Method 1: Using the new example script

```bash
python example_multi_selection.py
```

Choose from 3 modes:
- Structured: Enter trip details explicitly
- Interactive: Use natural language queries
- Demo: Run with sample data

### Method 2: Programmatic usage

```python
from llm_orchestrator import TravelItineraryOrchestrator

orchestrator = TravelItineraryOrchestrator()

trip_details = {
    'origin_city': 'Bangalore',
    'destination_city': 'Paris',
    'departure_date': '2026-04-15',
    'num_days': 7,
    'budget_inr': 200000,
    'interests': ['museums', 'food', 'architecture'],
    'dietary_restrictions': ['vegetarian'],
    'user_id': 'user123'  # For database storage
}

result = orchestrator.generate_itinerary(trip_details)
# User will be prompted to select from top 3 itineraries
# Selected itinerary is automatically saved to database
```

### Method 3: Interactive mode

```bash
python llm_orchestrator.py
```

Then choose:
- Type natural language queries like "Plan a trip from Mumbai to Singapore for 5 days with ₹100000 budget"
- System generates 3 options and lets you select

## User Workflow

1. **Input Trip Details**
   ```
   📋 TRIP SUMMARY
   From: Bangalore → To: Paris
   Duration: 7 days
   Budget: ₹200,000
   ```

2. **Generation Progress** (2-5 minutes)
   ```
   [1/6] 🔍 ANALYZING SEASONAL TRENDS
   [2-6/6] 🔍 SEARCH + OPTIMIZE
     - Strategy 1: One-by-One Expansion...
     - Strategy 2: Parallel Expansion...
     - Strategy 3: Sequential Generation...
   ```

3. **Selection Interface**
   ```
   🏆 TOP 3 RECOMMENDED ITINERARIES
   
   Rank | Strategy         | Total Cost    | Cost/Day      | Status
   ─────────────────────────────────────────────────────────────────
   1    | Parallel         | ₹185,000      | ₹26,428       | ✅ Within Budget
   2    | One-by-One       | ₹188,000      | ₹26,857       | ✅ Within Budget
   3    | Sequential       | ₹195,000      | ₹27,857       | ⚠️  Slightly Over
   
   📊 Detailed Breakdown:
   
   Option 1: Parallel
     💵 Total Cost: ₹185,000.00
     💰 Per Day: ₹26,428.57
     🔍 Optimizer: langgraph
     📈 Combinations Evaluated: 1250
     ✨ Budget Remaining: ₹15,000.00
   
   ...
   
   🎯 Select an itinerary (1-3) or 'c' to cancel:
   ```

4. **Selection & Confirmation**
   ```
   ✅ Selected: Parallel
   
   ✅ SELECTED ITINERARY: Parallel
   ════════════════════════════════════════════════════════════════
   
   💵 Total Cost: ₹185,000.00
   📅 Duration: 7 days
   
   📋 Day-by-Day Preview:
     Day 1: AI Flight DL-123, Hilton Paris, Eiffel Tower Tour, ...
     Day 2: Louvre Museum, Bistro le Petit, ...
   
   ✅ Itinerary saved successfully!
   ```

5. **Database Storage**
   ```
   ✅ Itinerary saved successfully!
      Strategy: Parallel
      User: user123
      Cost: ₹185,000.00
   ```

## Database Schema

The selected itinerary is stored with:

```python
{
    'user_id': 'user123',
    'strategy_used': 'Parallel',  # Which strategy was selected
    'origin': 'Bangalore',
    'destination': 'Paris',
    'departure_date': '2026-04-15',
    'return_date': '2026-04-22',
    'num_days': 7,
    'total_budget_inr': 200000,
    'total_cost_inr': 185000,
    'currency': 'INR',
    'optimization_score': 0.92,
    'combinations_evaluated': 1250,
    'optimizer': 'langgraph',
    'daily_schedules': [
        {
            'day': 1,
            'items': [
                {
                    'name': 'Flight AI-123',
                    'type': 'flight',
                    'cost': 45000,
                    'time': '08:00',
                    'description': 'Delhi to Paris'
                },
                ...
            ]
        },
        ...
    ],
    'interests': ['museums', 'food', 'architecture'],
    'dietary_restrictions': ['vegetarian'],
    'trip_details': {...}
}
```

## Ranking Algorithm

Itineraries are ranked based on:

1. **Budget Efficiency** (Primary)
   - Within budget: Lower cost = better score
   - Over budget: Penalized heavily (multiplier of 2x)

2. **Cost Per Day** (Secondary)
   - Better value for money

3. **Optimization Score** (Tertiary)
   - Quality of the plan if available

## Configuration

### Feature Flags

In `tlm_orchestrator.py`:

```python
class TravelItineraryOrchestrator:
    # Use LangGraph optimizer (parallel + dynamic)
    USE_LANGGRAPH = True
    
    # Select expansion strategy (affects all 3 methods)
    DELTA = 5  # Extra options per expansion step
```

### Disabling Selection System

If you want to use the old single-itinerary system:

```python
# In generate_itinerary(), comment out the selection:
# selection_result = self.handle_itinerary_selection(...)

# And use direct optimization:
# optimized = self._optimize_with_langgraph(...)
```

## Error Handling

- **No valid itineraries**: Shows error and suggests budget increase
- **User cancels selection**: Returns None gracefully
- **Database connection fails**: Falls back to in-memory storage
- **Missing dependencies**: Falls back to single-itinerary mode

## Performance

- **Generation Time**: 2-5 minutes (depends on API availability)
  - Trend analysis: ~30 seconds
  - One-by-One expansion: ~60 seconds
  - Parallel expansion: ~60 seconds  
  - Sequential generation: ~30 seconds
  - Selection & display: ~5 seconds

- **Database Storage**: < 1 second

## Future Enhancements

1. **Web UI Integration**
   - Display itineraries with images
   - Interactive map-based selection
   - Real-time itinerary customization

2. **Advanced Ranking**
   - Machine learning-based scoring
   - Personalized ranking based on user history
   - A/B testing of ranking algorithms

3. **Comparison Features**
   - Side-by-side comparison of selected options
   - Highlight differences in itineraries
   - Show why one is cheaper/better

4. **User Feedback Loop**
   - Rate selected itinerary
   - Provide feedback on strategies
   - Improve future recommendations

## Troubleshooting

### Q: How do I just get the best itinerary without selection?
A: Modify `generate_itinerary()` to skip `handle_itinerary_selection()` and use the old logic.

### Q: Can I modify an itinerary after selection?
A: Yes, after saving, you can query the database and manually edit items or regenerate.

### Q: How are the 3 strategies different?
A:
- **One-by-One**: Most thorough, expands agents one at a time (more optimization calls)
- **Parallel**: Faster, expands all agents together (fewer optimization calls)
- **Sequential**: Most memory-efficient, early stopping when feasible found

### Q: Why might I prefer one strategy over another?
A:
- **One-by-One**: When you have time and want maximum exploration
- **Parallel**: When you want balanced speed vs quality
- **Sequential**: When memory is limited or you want quick results

---

**Questions?** Check [main_README.md](README.md) or review the source files:
- [itinerary_selector.py](itinerary_selector.py) - Selection logic
- [llm_orchestrator.py](llm_orchestrator.py) - Integration point
- [history_manager.py](history_manager.py) - Database storage
