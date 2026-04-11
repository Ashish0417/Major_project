# 🚀 Quick Start Guide - Multi-Itinerary Selection

This guide shows you how to get started with the new multi-itinerary selection feature.

## What's New

✅ **3 Strategy Generation**: System now generates 3 different itineraries  
✅ **Smart Ranking**: Automatically ranks by budget efficiency & cost/day  
✅ **User Selection**: Pick from top 3 options with detailed comparison  
✅ **Database Storage**: Selected itinerary automatically saved to database  

## Installation

No additional packages needed! The feature uses existing dependencies.

### Verify Installation

```bash
# Check that all modules import correctly
cd Major_project
python -c "from itinerary_selector import ItineraryRanker, ItinerarySelector, SaveItineraryHandler; print('✅ Ready!')"
```

## Basic Usage

### Option 1: Run Example Script (Easiest)

```bash
python example_multi_selection.py
```

Follow the menu:
- **Option 1**: Structured input (enter trip details)
- **Option 2**: Interactive (natural language queries)  
- **Option 3**: Demo with sample Paris trip

### Option 2: Programmatic Usage

```python
from llm_orchestrator import TravelItineraryOrchestrator

# Initialize
orchestrator = TravelItineraryOrchestrator()

# Define your trip
trip_details = {
    'origin_city': 'Bangalore',
    'destination_city': 'Tokyo',
    'departure_date': '2026-05-01',
    'num_days': 5,
    'budget_inr': 150000,
    'interests': ['temples', 'shopping', 'food'],
    'user_id': 'user123'
}

# Generate - automatically shows selection UI
result = orchestrator.generate_itinerary(trip_details)

# Selected itinerary is already in result and saved to DB
print(f"Total Cost: ₹{result['total_cost']:,.0f}")
```

### Option 3: Interactive Chat

```bash
python llm_orchestrator.py
```

Type natural language queries:
```
You: Plan a 7-day trip from Bangalore to Singapore with ₹120000 budget
```

System will:
1. Parse your query
2. Generate 3 itineraries
3. Show top 3 options
4. Let you select & save

## What Happens Behind the Scenes

```
Your Input
    ↓
[Parse Trip Details]
    ↓
[Generate 3 Strategies]
  ├─ One-by-One Expansion
  ├─ Parallel Expansion
  └─ Sequential Generation
    ↓
[Rank by Budget Efficiency]
    ↓
[Display Top 3 Options]
    ↓
[User Selects One]
    ↓
[Save to Database]
    ↓
[Display Selected Itinerary]
```

## Understanding the Selection UI

```
🏆 TOP 3 RECOMMENDED ITINERARIES

Rank | Strategy         | Total Cost    | Cost/Day      | Status
─────────────────────────────────────────────────────────────────
1    | Parallel         | ₹185,000      | ₹26,428       | ✅ Within Budget
2    | One-by-One       | ₹188,000      | ₹26,857       | ✅ Within Budget
3    | Sequential       | ₹195,000      | ₹27,857       | ⚠️  Slightly Over
```

**What each column means:**
- **Rank**: Sorted by value (budget efficiency)
- **Strategy**: Which algorithm was used
- **Total Cost**: INR amount for entire trip
- **Cost/Day**: Average daily cost
- **Status**: Whether within or over budget

## Features Explained

### 1. Smart Ranking
```python
# Factors considered:
- Budget efficiency (stays within budget = better)
- Cost per day (lower = better value)
- Optimization score (quality of plan)
```

### 2. Three Generation Strategies

| Strategy | Speed | Quality | Use When |
|----------|-------|---------|----------|
| **Parallel** | ⚡ Fast | 👍 Good | You want balanced speed & quality |
| **One-by-One** | 🐢 Slow | ⭐ Best | You have time and want thorough search |
| **Sequential** | ⚡ Very Fast | 👌 OK | Memory is limited or quick results needed |

### 3. Database Integration

Selected itinerary is automatically saved with:
- Strategy used
- All costs breakdown
- Daily schedules
- Your preferences
- Timestamp

Retrieve later:
```python
# Get past itineraries
history = orchestrator.history_manager.get_trip_history(user_id)
```

## Common Scenarios

### Scenario 1: Low Budget
```
Trip: 5 days to Bali with ₹50000 budget

Result:
❌ Budget INR 50,000 is below estimated minimum INR 45,000
💡 Suggested minimum: INR 45,000

Fix: Increase budget or reduce days
```

### Scenario 2: Comparing Strategies
```
Shows all three options with costs:
- Parallel: ₹185,000 ✅ Cheapest, within budget!
- One-by-One: ₹188,000 ✅ More thorough search
- Sequential: ₹195,000 ⚠️ Over budget but fastest

You pick the best value ✨
```

### Scenario 3: Natural Language Input
```
You: "I want to visit Goa for 3 days from Bangalore with max ₹40000"

System: Extracts details and generates itineraries
Shows: Top 3 options
You: Select Option 1
Done: Saved to database!
```

## Troubleshooting

### Q: "ModuleNotFoundError: No module named 'itinerary_selector'"
**A:** Make sure you're in the `Major_project` directory when running:
```bash
cd c:\Users\tanvi\Personal\TravelPlanner\Major_project
python example_multi_selection.py
```

### Q: "GOOGLE_API_KEY not found"
**A:** Create a `.env` file in `Major_project`:
```
GOOGLE_API_KEY=your_key_here
```
Get free key from: https://makersuite.google.com/app/apikey

### Q: Selection UI doesn't appear, just shows best itinerary
**A:** The system falls back to single-option if selector is unavailable. Check:
```bash
cd Major_project
python -c "from itinerary_selector import ItineraryRanker; print('✅ OK')"
```

### Q: Takes too long (> 5 minutes)
**A:** Normal for first run. Reduce scope:
- Use fewer days (e.g., 3 instead of 7)
- Reduce budget (less options to search)
- Use Sequential strategy (fastest)

### Q: Can't decide between options?
**A:** Consider:
1. **Cost**: Pick the cheapest within budget
2. **Quality**: Look at optimization score
3. **Strategy**: Parallel = balanced, One-by-One = thorough, Sequential = fast

## Next Steps

### View Documentation
- Full docs: [MULTI_SELECTION_README.md](MULTI_SELECTION_README.md)
- Implementation: [itinerary_selector.py](itinerary_selector.py)
- Integration: [llm_orchestrator.py](llm_orchestrator.py)

### Retrieve Saved Itineraries
```python
from llm_orchestrator import TravelItineraryOrchestrator

orchestrator = TravelItineraryOrchestrator()

# Get all itineraries for a user
trips = orchestrator.history_manager.get_trip_history('user123')

for trip in trips:
    print(f"{trip['destination']}: ₹{trip['total_cost_inr']:,.0f}")
```

### Customize Ranking
Edit [itinerary_selector.py](itinerary_selector.py):
```python
def _compute_rank_score(self, summary):
    # Adjust weights here:
    efficiency_score = summary.total_cost / self.budget  # 0.6 weight
    cost_per_day_score = summary.get_cost_per_day() / 10000  # 0.3 weight
    # Add your own scoring logic
```

## Performance Tips

- **First run**: Takes 2-5 minutes (API calls)
- **Subsequent runs**: Faster due to caching
- **Tips to speed up**:
  1. Reduce number of days
  2. Reduce interests (more specific)
  3. Use Sequential strategy
  4. Reduce budget (fewer options)

## Support

Need help?
1. Check [MULTI_SELECTION_README.md](MULTI_SELECTION_README.md) for detailed docs
2. Review example: [example_multi_selection.py](example_multi_selection.py)
3. Check error messages - they're detailed!

---

**Ready?** Start with:
```bash
python example_multi_selection.py
```

Then choose your adventure! 🌍✈️🎯
