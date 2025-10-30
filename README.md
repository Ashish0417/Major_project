# AI-Driven Personalized Travel Itinerary Generator

A sophisticated multi-agent AI system for generating personalized travel itineraries using constraint optimization, collaborative filtering, and real-time trend analysis.

## Project Overview

This project implements a hybrid multi-agent AI framework that integrates:
- **Large Language Model (LLM) concepts** for preference modeling
- **Specialized agents** for flights, accommodations, dining, and activities
- **OR-Tools CP-SAT solver** for constraint-based optimization
- **MongoDB** for history storage and learning
- **Collaborative filtering** for personalized recommendations
- **Trend analysis** for seasonal and popular suggestions

## Features

✅ **User Preference Modeling** - Structured JSON-based user profiles  
✅ **Multi-Agent System** - Specialized agents for different travel components  
✅ **Constraint Optimization** - OR-Tools CP-SAT solver for itinerary optimization  
✅ **Budget Management** - Dynamic budget allocation and cost optimization  
✅ **History Learning** - User clustering and collaborative filtering  
✅ **Trend Analysis** - Seasonal attractions and popular events  
✅ **Real-time Data** - Support for live API integration  

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   User Profile Manager                       │
│            (Preferences, History, Constraints)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Flight   │    │Accommoda-│    │Restaurant│    │ Activity │
│ Agent    │    │tion Agent│    │  Agent   │    │  Agent   │
└─────┬────┘    └─────┬────┘    └─────┬────┘    └─────┬────┘
      │               │               │               │
      └───────────────┼───────────────┼───────────────┘
                      │
                      ▼
          ┌───────────────────────┐
          │  Unified Planner      │
          │  (OR-Tools CP-SAT)    │
          │  Budget Optimizer     │
          └──────────┬────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ History  │ │  Trend   │ │Optimized │
  │ Manager  │ │ Analyzer │ │Itinerary │
  └──────────┘ └──────────┘ └──────────┘
```

## File Structure

```
project/
│
├── user_profile.py          # User preference modeling
├── flight_agent.py          # Flight search agent
├── accommodation_agent.py   # Accommodation search agent
├── restaurant_agent.py      # Restaurant recommendation agent
├── activity_agent.py        # Activity & experience agent
├── optimizer.py             # OR-Tools optimization engine
├── history_manager.py       # History storage & collaborative filtering
├── trend_analyzer.py        # Trend analysis & seasonal suggestions
├── main.py                  # Main application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: (Optional) Set up API Keys

Create a `.env` file in the project root:

```bash
# Amadeus API (for flights)
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret

# Google Places API (for restaurants)
GOOGLE_PLACES_API_KEY=your_google_places_key

# Booking.com API (for accommodations)
BOOKING_API_KEY=your_booking_api_key

# MongoDB (for history storage)
MONGO_URI=mongodb://localhost:27017
```

**Note:** The system works with mock data by default, so API keys are optional for testing.

## Usage

### Basic Usage

Run the main application:

```bash
python main.py
```

This will:
1. Load a sample user profile
2. Search for flights, accommodations, restaurants, and activities
3. Optimize the itinerary using OR-Tools
4. Display a complete day-by-day itinerary

### Custom User Profile

Create a custom profile:

```python
from user_profile import UserProfile, TravelPreferences, TripDates, ContactInfo

# Create profile
profile = UserProfile(user_id="user_001")
profile.name = "John Doe"
profile.contact = ContactInfo(email="john@example.com", phone="+1-xxx-xxx-xxxx")
profile.destinations = ["Paris, France"]
profile.dates = TripDates(start="2026-06-01", end="2026-06-07")
profile.default_currency = "EUR"

# Set preferences
profile.travel_preferences = TravelPreferences(
    budget_total=3000,
    budget_per_day=500,
    comfort_level="premium",
    transport_pref=["flight"],
    accommodation_pref=["hotel"],
    dietary_restrictions=["vegetarian"],
    activity_interests=["museums", "art", "culinary"],
    avoid=["late-night travel"],
    max_daily_travel_minutes=60,
    max_activities_per_day=3
)

# Generate itinerary
from main import TravelItineraryGenerator
generator = TravelItineraryGenerator()
itinerary = generator.generate_itinerary(profile)
generator.display_itinerary(itinerary)
```

### Using Real APIs

To use real APIs instead of mock data:

```python
generator = TravelItineraryGenerator(
    use_mock_data=False,  # Use real APIs
    use_mongodb=True      # Use MongoDB for storage
)
```

## Modules

### 1. User Profile (`user_profile.py`)

Manages user preferences and travel constraints:
- Budget and comfort level
- Dietary restrictions
- Activity interests
- Historical trips

### 2. Flight Agent (`flight_agent.py`)

Searches and ranks flight options:
- Amadeus API integration
- Price and duration optimization
- Red-eye flight filtering
- Multi-segment support

### 3. Accommodation Agent (`accommodation_agent.py`)

Finds suitable accommodations:
- Hotels, apartments, hostels
- Location-based filtering
- Amenity matching
- Cancellation policies

### 4. Restaurant Agent (`restaurant_agent.py`)

Recommends dining options:
- Dietary restriction filtering
- Price level matching
- Opening hours checking
- Cuisine type preferences

### 5. Activity Agent (`activity_agent.py`)

Curates activities and experiences:
- Museums, tours, outdoor activities
- Interest-based filtering
- Duration and difficulty matching
- Popularity scoring

### 6. Optimizer (`optimizer.py`)

**Core optimization engine using OR-Tools CP-SAT:**

**Decision Variables:**
- Binary variables for each item selection

**Objective Function:**
```
Minimize: w1*cost + w2*time + w3*(-preference) + w4*(-popularity)
```

**Constraints:**
1. Budget: ∑(cost × selected) ≤ total_budget
2. Time: No overlapping activities per day
3. Activity limit: ≤ max_activities_per_day
4. Logical: Exactly one accommodation per day
5. User preferences: Avoid specific items/times

### 7. History Manager (`history_manager.py`)

Manages user history and learning:
- MongoDB integration
- K-Means clustering for user segmentation
- Collaborative filtering
- Trip history storage

### 8. Trend Analyzer (`trend_analyzer.py`)

Provides trend-based suggestions:
- Seasonal attractions
- Popular events
- Weather-based recommendations
- Trending destinations

## Optimization Details

The system uses **Google OR-Tools CP-SAT solver** for constraint satisfaction:

### Variables
- Binary decision variables for each potential itinerary item
- Variables represent: flights, accommodations, restaurants, activities

### Constraints
1. **Budget Constraint:** Total cost ≤ user budget
2. **Time Constraints:** No overlapping activities
3. **Activity Limits:** Max activities per day
4. **Mandatory Items:** Selected flights and one accommodation per day
5. **User Preferences:** Respect dietary restrictions, avoid lists

### Objective
Maximize weighted score:
- 30% - Cost efficiency (lower cost = higher score)
- 20% - Time efficiency (shorter duration = higher score)
- 30% - User preference match
- 20% - Popularity/rating score

## Collaborative Filtering

The system implements **user-based collaborative filtering**:

1. **User Clustering:** K-Means algorithm groups similar users
2. **Similarity Metric:** Jaccard similarity on activity interests
3. **Recommendation:** Suggest highly-rated trips from similar users
4. **Cold Start Handling:** Use trend-based suggestions for new users

## Example Output

```
======================================================================
YOUR PERSONALIZED ITINERARY
======================================================================

Total Cost: INR 48,523.50
Budget Remaining: INR 1,476.50
Number of Days: 7
Number of Activities: 12

----------------------------------------------------------------------
DAY-BY-DAY BREAKDOWN
----------------------------------------------------------------------

Day 1:
--------------------------------------------------
  [00:00] AI Flight DEL-NRT
    Type: Flight
    Duration: 9h 15m
    Cost: INR 32,450.00

  [14:00] Grand Palace Hotel
    Type: Accommodation
    Duration: 24h 0m
    Cost: INR 4,200.00

Day 2:
--------------------------------------------------
  [09:00] Tokyo National Museum
    Type: Activity
    Duration: 3h 0m
    Cost: INR 1,200.00

  [12:00] Vegetarian Delight
    Type: Restaurant
    Duration: 1h 15m
    Cost: INR 850.00

  [14:00] Asakusa Walking Tour
    Type: Activity
    Duration: 2h 30m
    Cost: INR 1,200.00

...
```

## Performance

- **Solver Time:** < 5 seconds for typical 7-day itinerary
- **API Calls:** Parallelizable agent queries
- **Memory:** < 100MB for standard usage
- **Scalability:** Handles 100+ activity options

## Testing

Run individual module tests:

```bash
# Test user profile
python user_profile.py

# Test flight agent
python flight_agent.py

# Test accommodation agent
python accommodation_agent.py

# Test restaurant agent
python restaurant_agent.py

# Test activity agent
python activity_agent.py

# Test trend analyzer
python trend_analyzer.py
```

## Future Enhancements

- [ ] Real-time traffic and weather integration
- [ ] Multi-city trip support
- [ ] Group travel coordination
- [ ] Social media integration for reviews
- [ ] Mobile app interface
- [ ] Deep reinforcement learning for adaptive planning
- [ ] Natural language query interface

## References

Based on research from:
1. TravelAgent (Chen et al., 2024)
2. Personal Travel Solver (Shao et al., 2025)
3. Vaiage (Liu et al., 2025)
4. Travel Optix (Singh, 2025)
5. TravelPlanner Benchmark (OSU-NLP Group, 2024)

## License

This project is for academic and educational purposes.

## Contributors

- Ashish R Kalgutkar (221IT012)
- Tanvi Poddar (221IT071)
- Uggumudi Sai Lasya Reddy (221IT074)

**Guide:** Prof. Ananthnarayana V.S.

**Institution:** National Institute of Technology Karnataka, Surathkal

---

**Note:** This is an implementation of the project described in the Midsem Report for Major Project-I (September 2025).
