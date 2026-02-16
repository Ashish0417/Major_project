"""Test the itinerary display improvements"""
from dataclasses import dataclass

# Mock object to test display
@dataclass
class MockItem:
    name: str
    item_type: str
    cost: float = 0
    rating: float = 0
    duration_minutes: int = 0
    departure_time: str = ""
    carrier: str = ""

# Create test itinerary with distribution
day_itinerary = {
    0: [  # Day 1
        MockItem("IndiGo Flight BLR-CDG", "flight", 24885.82, 4.5, 399, "2026-03-01T08:00:00", "6E"),
        MockItem("Hôtel Montpensier", "accommodation", 3289.41, 4.2),
        MockItem("Café Moderne", "restaurant", 800, 4.0),
        MockItem("Grande Arche", "activity", 898.65, 4.0, 135)
    ],
    1: [  # Day 2
        MockItem("Hôtel Montpensier", "accommodation", 3289.41, 4.2),
        MockItem("Le Jules Verne", "restaurant", 2500, 4.5),
        MockItem("Louvre Museum", "activity", 1200, 4.8, 180),
        MockItem("Musée d'Orsay", "activity", 1000, 4.7, 120)
    ],
    2: [  # Day 3
        MockItem("Hôtel Montpensier", "accommodation", 3289.41, 4.2),
        MockItem("L'Astrance", "restaurant", 1800, 4.6),
        MockItem("Notre-Dame", "activity", 1500, 5.0, 90),
        MockItem("Air India Flight CDG-BLR", "flight", 25694.52, 4.5, 480, "2026-03-03T17:03:00", "AI"),
    ]
}

itinerary = {
    'total_cost': 54768.40,
    'currency': 'INR',
    'num_days': 3,
    'itinerary': day_itinerary,
    'optimizer_metadata': {
        'optimizer': 'langgraph',
        'score': 70.0,
        'combinations_evaluated': 15,
        'backtrack_attempts': 2,
    }
}

trip_details = {
    'origin_city': 'Bangalore',
    'destination_city': 'Paris',
    'departure_date': '2026-03-01',
    'num_days': 3,
}

# Import and test the display function
import sys
sys.path.insert(0, '.')

from llm_orchestrator import TravelItineraryOrchestrator

orch = TravelItineraryOrchestrator()

# Test display with our mock itinerary
print("\n" + "="*80)
print("TESTING UPDATED DISPLAY FUNCTION")
print("="*80)
orch.display_itinerary(itinerary, trip_details)
