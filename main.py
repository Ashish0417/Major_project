# """
# AI-Driven Personalized Travel Itinerary Generator
# Main Application Module

# This is the main entry point that integrates all components:
# - User Profile Management
# - Multi-Agent System (Flight, Accommodation, Restaurant, Activity)
# - Optimization Engine
# - History Management
# - Trend Analysis
# """

# import sys
# from datetime import datetime, timedelta
# from typing import Dict, Any

# # Import all modules
# from user_profile import UserProfile, create_sample_profile
# from flight_agent import FlightAgent
# from accommodation_agent import AccommodationAgent
# from restaurant_agent import RestaurantAgent
# from activity_agent import ActivityAgent
# from optimizer import ItineraryOptimizer
# from history_manager import HistoryManager
# from trend_analyzer import TrendAnalyzer


# class TravelItineraryGenerator:
#     """Main application class that coordinates all components"""

#     def __init__(self, use_mock_data: bool = True, use_mongodb: bool = False):
#         """
#         Initialize the Travel Itinerary Generator

#         Args:
#             use_mock_data: Use mock data instead of real APIs
#             use_mongodb: Use MongoDB for history storage
#         """
#         print("="*70)
#         print("AI-DRIVEN PERSONALIZED TRAVEL ITINERARY GENERATOR")
#         print("="*70)

#         self.use_mock_data = use_mock_data

#         # Initialize all agents
#         print("\nInitializing agents...")
#         self.flight_agent = FlightAgent(use_mock=use_mock_data)
#         self.accommodation_agent = AccommodationAgent(use_mock=use_mock_data)
#         self.restaurant_agent = RestaurantAgent(use_mock=use_mock_data)
#         self.activity_agent = ActivityAgent(use_mock=use_mock_data)

#         # Initialize support modules
#         self.history_manager = HistoryManager(use_mongodb=use_mongodb)
#         self.trend_analyzer = TrendAnalyzer()

#         print("✓ All agents initialized successfully!")

#     def generate_itinerary(self, user_profile: UserProfile) -> Dict[str, Any]:
#         """
#         Generate complete travel itinerary

#         Args:
#             user_profile: User profile with preferences

#         Returns:
#             Complete itinerary with all details
#         """
#         print("\n" + "="*70)
#         print("GENERATING PERSONALIZED ITINERARY")
#         print("="*70)

#         # Validate user profile
#         is_valid, errors = user_profile.validate()
#         if not is_valid:
#             return {'error': 'Invalid user profile', 'details': errors}

#         # Extract key information
#         destination = user_profile.destinations[0] if user_profile.destinations else "Tokyo"
#         start_date = user_profile.dates.start
#         end_date = user_profile.dates.end

#         # Calculate trip duration
#         start_dt = datetime.strptime(start_date, '%Y-%m-%d')
#         end_dt = datetime.strptime(end_date, '%Y-%m-%d')
#         num_days = (end_dt - start_dt).days + 1

#         print(f"\nTrip Details:")
#         print(f"  User: {user_profile.name}")
#         print(f"  Destination: {destination}")
#         print(f"  Duration: {num_days} days ({start_date} to {end_date})")
#         print(f"  Budget: {user_profile.default_currency} {user_profile.travel_preferences.budget_total}")

#         # Step 1: Get trend-based suggestions
#         print("\n[1/6] Analyzing trends and seasonal attractions...")
#         seasonal_suggestions = self.trend_analyzer.get_seasonal_suggestions(destination, start_date)
#         popular_events = self.trend_analyzer.get_popular_events(destination, start_date)

#         if seasonal_suggestions:
#             print(f"  Found {len(seasonal_suggestions)} seasonal attractions")
#         if popular_events:
#             print(f"  Found {len(popular_events)} popular events")

#         # Step 2: Search flights
#         print("\n[2/6] Searching flights...")
#         flights = self.flight_agent.search_flights(
#             origin="DEL",  # Delhi
#             destination="NRT",  # Tokyo Narita
#             departure_date=start_date,
#             travel_class=user_profile.travel_preferences.comfort_level.upper(),
#             max_results=5
#         )
#         print(f"  Found {len(flights)} flight options")

#         # Filter and rank flights
#         flights = self.flight_agent.filter_by_preferences(
#             flights,
#             avoid_night='red-eye flights' in user_profile.travel_preferences.avoid,
#             max_price=user_profile.travel_preferences.budget_total * 0.3  # Max 30% of budget
#         )
#         flights = self.flight_agent.rank_flights(flights)
#         print(f"  Ranked to {len(flights)} suitable options")

#         # Step 3: Search accommodations
#         print("\n[3/6] Searching accommodations...")
#         accommodations = self.accommodation_agent.search_accommodations(
#             destination=destination,
#             check_in=start_date,
#             check_out=end_date,
#             accommodation_types=user_profile.travel_preferences.accommodation_pref,
#             max_price=user_profile.travel_preferences.budget_per_day * 0.4,  # Max 40% of daily budget
#             max_results=10
#         )
#         print(f"  Found {len(accommodations)} accommodation options")

#         accommodations = self.accommodation_agent.rank_accommodations(accommodations)

#         # Step 4: Search restaurants
#         print("\n[4/6] Searching restaurants...")
#         restaurants = self.restaurant_agent.search_restaurants(
#             location=destination,
#             dietary_restrictions=user_profile.travel_preferences.dietary_restrictions,
#             max_price_level=2 if user_profile.travel_preferences.comfort_level == 'economy' else 3,
#             max_results=15
#         )
#         print(f"  Found {len(restaurants)} restaurant options")

#         restaurants = self.restaurant_agent.rank_restaurants(restaurants)

#         # Step 5: Search activities
#         print("\n[5/6] Searching activities...")
#         activities = self.activity_agent.search_activities(
#             location=destination,
#             interests=user_profile.travel_preferences.activity_interests,
#             max_duration_minutes=user_profile.travel_preferences.max_daily_travel_minutes * 2,
#             max_results=20
#         )
#         print(f"  Found {len(activities)} activity options")

#         # Filter by interests
#         activities = self.activity_agent.filter_by_interests(
#             activities,
#             user_profile.travel_preferences.activity_interests
#         )
#         activities = self.activity_agent.rank_activities(activities)
#         print(f"  Filtered to {len(activities)} matching interests")

#         # Step 6: Optimize itinerary
#         print("\n[6/6] Optimizing itinerary with OR-Tools CP-SAT solver...")
#         print("  This may take a few moments...")

#         optimizer = ItineraryOptimizer(user_profile)
#         optimized_itinerary = optimizer.optimize_itinerary(
#             flights=flights,
#             accommodations=accommodations,
#             restaurants=restaurants,
#             activities=activities,
#             num_days=num_days
#         )

#         if 'error' not in optimized_itinerary:
#             print("  ✓ Optimization complete!")
#             print(f"  Total Cost: {optimized_itinerary['currency']} {optimized_itinerary['total_cost']}")
#             print(f"  Activities Included: {optimized_itinerary['num_activities']}")
#             print(f"  Budget Remaining: {optimized_itinerary['currency']} {optimized_itinerary['budget_remaining']:.2f}")
#         else:
#             print(f"  ✗ Optimization failed: {optimized_itinerary['error']}")

#         # Add trend suggestions to result
#         optimized_itinerary['seasonal_suggestions'] = seasonal_suggestions
#         optimized_itinerary['popular_events'] = popular_events
#         optimized_itinerary['user_profile'] = user_profile.to_dict()

#         # Store in history (if consent given)
#         if user_profile.consent.get('store_history'):
#             print("\n[Saving to history...]")
#             self.history_manager.store_user_profile(user_profile)

#         return optimized_itinerary

#     def display_itinerary(self, itinerary: Dict[str, Any]):
#         """Display itinerary in a readable format"""
#         if 'error' in itinerary:
#             print(f"\nError: {itinerary['error']}")
#             return

#         print("\n" + "="*70)
#         print("YOUR PERSONALIZED ITINERARY")
#         print("="*70)

#         # Summary
#         print(f"\nTotal Cost: {itinerary['currency']} {itinerary['total_cost']}")
#         print(f"Budget Remaining: {itinerary['currency']} {itinerary['budget_remaining']:.2f}")
#         print(f"Number of Days: {itinerary['num_days']}")
#         print(f"Number of Activities: {itinerary['num_activities']}")

#         # Day-by-day itinerary
#         print("\n" + "-"*70)
#         print("DAY-BY-DAY BREAKDOWN")
#         print("-"*70)

#         for day in range(itinerary['num_days']):
#             if day not in itinerary['itinerary']:
#                 continue

#             items = itinerary['itinerary'][day]

#             print(f"\nDay {day + 1}:")
#             print("-" * 50)

#             if not items:
#                 print("  (Rest day / Free time)")
#                 continue

#             for item in items:
#                 time_str = f"{item.start_time // 60:02d}:{item.start_time % 60:02d}"
#                 duration_hrs = item.duration // 60
#                 duration_mins = item.duration % 60

#                 print(f"  [{time_str}] {item.name}")
#                 print(f"    Type: {item.item_type.capitalize()}")
#                 print(f"    Duration: {duration_hrs}h {duration_mins}m")
#                 print(f"    Cost: {itinerary['currency']} {item.cost:.2f}")
#                 print()

#         # Seasonal suggestions
#         if itinerary.get('seasonal_suggestions'):
#             print("\n" + "-"*70)
#             print("SEASONAL ATTRACTIONS")
#             print("-"*70)
#             for sugg in itinerary['seasonal_suggestions']:
#                 print(f"  • {sugg['name']} ({sugg['season']})")

#         # Popular events
#         if itinerary.get('popular_events'):
#             print("\n" + "-"*70)
#             print("POPULAR EVENTS DURING YOUR VISIT")
#             print("-"*70)
#             for event in itinerary['popular_events']:
#                 print(f"  • {event['name']} (Popularity: {event['popularity']:.0%})")

#         # Solver statistics
#         if 'solver_stats' in itinerary:
#             print("\n" + "-"*70)
#             print("OPTIMIZATION STATISTICS")
#             print("-"*70)
#             stats = itinerary['solver_stats']
#             print(f"  Status: {stats['status']}")
#             print(f"  Objective Value: {stats['objective_value']:.2f}")
#             print(f"  Solve Time: {stats['solve_time']:.4f} seconds")

#         print("\n" + "="*70)


# def main():
#     """Main function"""
#     print("\nStarting Travel Itinerary Generator...")

#     # Create or load user profile
#     print("\nLoading user profile...")
#     user_profile = create_sample_profile()

#     # Initialize generator
#     generator = TravelItineraryGenerator(
#         use_mock_data=True,  # Set to False to use real APIs
#         use_mongodb=False     # Set to True to use MongoDB
#     )

#     # Generate itinerary
#     itinerary = generator.generate_itinerary(user_profile)

#     # Display results
#     generator.display_itinerary(itinerary)

#     print("\n" + "="*70)
#     print("Thank you for using the AI-Driven Travel Itinerary Generator!")
#     print("="*70)
#     print()


# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         print("\n\nProcess interrupted by user.")
#         sys.exit(0)
#     except Exception as e:
#         print(f"\n\nAn error occurred: {e}")
#         import traceback
#         traceback.print_exc()
#         sys.exit(1)
"""
AI-Driven Personalized Travel Itinerary Generator
Main Application - WITH LANGCHAIN INTEGRATION

Modes:
1. Traditional: Direct API orchestration (original)
2. LangChain: AI-powered with LLM reasoning (new)
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import all modules
from user_profile import UserProfile, create_sample_profile
from flight_agent import FlightAgent
from accommodation_agent import AccommodationAgent
from restaurant_agent import RestaurantAgent
from activity_agent import ActivityAgent
from optimizer import ItineraryOptimizer
from history_manager import HistoryManager
from trend_analyzer import TrendAnalyzer


class TravelItineraryGenerator:
    """Main application class"""

    def __init__(self):
        """Initialize"""
        print("="*70)
        print("🌍 AI-DRIVEN PERSONALIZED TRAVEL ITINERARY GENERATOR")
        print("="*70)
        print("\nAvailable Modes:")
        print("  1. TRADITIONAL: Direct API orchestration")
        print("  2. LANGCHAIN: AI-powered with LLM reasoning (NEW!)")
        print("\nConfigure by setting MODE in environment or code")

        self.mode = os.getenv("ITINERARY_MODE", "langchain").lower()

        if self.mode == "langchain":
            print("\n✅ Running in LANGCHAIN MODE")
            self._init_langchain()
        else:
            print("\n✅ Running in TRADITIONAL MODE")
            self._init_traditional()

    def _init_langchain(self):
        """Initialize LangChain mode"""
        try:
            from llm_orchestrator import LangChainOrchestrator

            print("  🤖 Initializing LangChain orchestrator...")
            self.orchestrator = LangChainOrchestrator()

            if self.orchestrator.llm:
                print("  ✅ LangChain ready!")
                self.use_langchain = True
            else:
                print("  ⚠️  LangChain initialization failed")
                print("  Falling back to TRADITIONAL mode")
                self.use_langchain = False
                self._init_traditional()
        except ImportError:
            print("  ❌ LangChain not installed")
            print("  Run: pip install langchain langchain-groq groq")
            self.use_langchain = False
            self._init_traditional()

    def _init_traditional(self):
        """Initialize traditional mode"""
        print("  Initializing REAL API agents...")

        self.flight_agent = FlightAgent(use_real_api=True)
        self.accommodation_agent = AccommodationAgent()
        self.restaurant_agent = RestaurantAgent()
        self.activity_agent = ActivityAgent(use_mock=True)

        self.history_manager = HistoryManager(use_mongodb=False)
        self.trend_analyzer = TrendAnalyzer()

        self.use_langchain = False
        print("  ✅ Traditional agents initialized!")

    def run(self):
        """Run the application"""

        if self.use_langchain:
            print("\n" + "="*70)
            print("LANGCHAIN MODE - Interactive AI Chatbot")
            print("="*70)
            self.orchestrator.interactive_mode()
        else:
            print("\n" + "="*70)
            print("TRADITIONAL MODE - Auto Generate Itinerary")
            print("="*70)
            self.generate_itinerary()

    def generate_itinerary(self):
        """Generate itinerary in traditional mode"""

        # Load user profile
        print("\nLoading user profile...")
        user_profile = create_sample_profile()

        # Generate
        itinerary = self._generate_itinerary(user_profile)

        # Display
        self.display_itinerary(itinerary)

    def _generate_itinerary(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Generate complete itinerary"""

        print("\n" + "="*70)
        print("GENERATING PERSONALIZED ITINERARY (REAL APIs)")
        print("="*70)

        # Validate profile
        is_valid, errors = user_profile.validate()
        if not is_valid:
            return {'error': 'Invalid user profile', 'details': errors}

        # Extract information
        destination = user_profile.destinations[0] if user_profile.destinations else "Tokyo, Japan"
        start_date = user_profile.dates.start
        end_date = user_profile.dates.end

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        num_days = (end_dt - start_dt).days + 1

        print(f"\nTrip Details:")
        print(f"  👤 User: {user_profile.name}")
        print(f"  📍 Destination: {destination}")
        print(f"  📅 Duration: {num_days} days ({start_date} to {end_date})")
        print(f"  💰 Budget: {user_profile.default_currency} {user_profile.travel_preferences.budget_total:,.2f}")

        # Step 1: Trends
        print("\n[1/6] Analyzing trends...")
        seasonal_suggestions = self.trend_analyzer.get_seasonal_suggestions(destination, start_date)
        popular_events = self.trend_analyzer.get_popular_events(destination, start_date)

        # Step 2: Flights
        print("\n[2/6] Searching flights with REAL Amadeus TEST API...")
        origin_code = "BOM"
        dest_code = self._get_airport_code(destination)

        flights = self.flight_agent.search_flights(
            origin=origin_code,
            destination=dest_code,
            departure_date=start_date,
            travel_class=user_profile.travel_preferences.comfort_level.upper(),
            max_results=5
        )

        if flights:
            print(f"  ✅ Found {len(flights)} real flights")
            flights = self.flight_agent.filter_by_preferences(flights)
            flights = self.flight_agent.rank_flights(flights)

        # Step 3: Accommodations
        print("\n[3/6] Searching accommodations with REAL OpenStreetMap API...")
        accommodations = self.accommodation_agent.search_accommodations(
            destination=destination,
            check_in=start_date,
            check_out=end_date,
            accommodation_types=user_profile.travel_preferences.accommodation_pref,
            max_results=10
        )

        if accommodations:
            print(f"  ✅ Found {len(accommodations)} real accommodations")
            accommodations = self.accommodation_agent.rank_accommodations(accommodations)

        # Step 4: Restaurants
        print("\n[4/6] Searching restaurants with REAL OpenStreetMap API...")
        restaurants = self.restaurant_agent.search_restaurants(
            location=destination,
            dietary_restrictions=user_profile.travel_preferences.dietary_restrictions,
            max_results=15
        )

        if restaurants:
            print(f"  ✅ Found {len(restaurants)} real restaurants")
            restaurants = self.restaurant_agent.rank_restaurants(restaurants)

        # Step 5: Activities
        print("\n[5/6] Searching activities...")
        activities = self.activity_agent.search_activities(
            location=destination,
            interests=user_profile.travel_preferences.activity_interests,
            max_results=20
        )

        if activities:
            print(f"  ✅ Found {len(activities)} activities")

        # Step 6: Optimize
        print("\n[6/6] Optimizing itinerary...")
        optimizer = ItineraryOptimizer(user_profile)
        optimized_itinerary = optimizer.optimize_itinerary(
            flights=flights,
            accommodations=accommodations,
            restaurants=restaurants,
            activities=activities,
            num_days=num_days
        )

        if 'error' not in optimized_itinerary:
            print("  ✅ Optimization complete!")
            print(f"  💰 Total Cost: {optimized_itinerary['currency']} {optimized_itinerary['total_cost']:,.2f}")

        # Add metadata
        optimized_itinerary['seasonal_suggestions'] = seasonal_suggestions
        optimized_itinerary['popular_events'] = popular_events
        optimized_itinerary['api_sources'] = {
            'flights': 'Amadeus TEST API (Real)',
            'accommodations': 'OpenStreetMap (Real)',
            'restaurants': 'OpenStreetMap (Real)',
            'activities': 'Mock Database',
            'optimization': 'Google OR-Tools (Real)',
            'orchestration': 'LangChain with GROQ LLM (AI)'
        }

        return optimized_itinerary

    def _get_airport_code(self, destination: str) -> str:
        """Get airport code"""
        codes = {
            'tokyo': 'NRT', 'delhi': 'DEL', 'mumbai': 'BOM',
            'singapore': 'SIN', 'bangkok': 'BKK', 'dubai': 'DXB'
        }
        for city, code in codes.items():
            if city in destination.lower():
                return code
        return 'DEL'

    def display_itinerary(self, itinerary: Dict[str, Any]):
        """Display itinerary"""
        if 'error' in itinerary:
            print(f"\n❌ Error: {itinerary['error']}")
            return

        print("\n" + "="*70)
        print("YOUR PERSONALIZED ITINERARY")
        print("="*70)

        # Summary
        print(f"\n💰 Total Cost: {itinerary['currency']} {itinerary['total_cost']:,.2f}")
        print(f"📅 Number of Days: {itinerary['num_days']}")

        # API Sources
        if 'api_sources' in itinerary:
            print("\n📊 Data Sources:")
            for key, source in itinerary['api_sources'].items():
                print(f"  • {key.title()}: {source}")

        # Day-by-day (abbreviated for clarity)
        print("\n" + "-"*70)
        print("DAY-BY-DAY BREAKDOWN (First 3 days)")
        print("-"*70)

        for day in range(min(3, itinerary['num_days'])):
            if day not in itinerary['itinerary']:
                continue

            items = itinerary['itinerary'][day]
            print(f"\nDay {day + 1}:")

            if not items:
                print("  (Rest day)")
                continue

            for item in items[:2]:  # Show first 2 items per day
                print(f"  • {item.name} ({item.item_type}) - INR {item.cost:,.0f}")

        print("\n" + "="*70)


def main():
    """Main function"""
    print("\n🌍 Starting Travel Itinerary Generator...")

    generator = TravelItineraryGenerator()
    generator.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)