"""
AI-Driven Personalized Travel Itinerary Generator
Main Application - WITH INTERACTIVE USER INPUT

Modes:
1. Interactive Profile Creation (NEW!)
2. Traditional: Direct API orchestration
3. LangChain: AI-powered with LLM reasoning
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
from interactive_profile_builder import InteractiveProfileBuilder
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

        self.mode = os.getenv("ITINERARY_MODE", "traditional").lower()
        self._init_traditional()

    def _init_traditional(self):
        """Initialize traditional mode"""
        print("\n🔧 Initializing agents...")

        self.flight_agent = FlightAgent(use_real_api=True)
        self.accommodation_agent = AccommodationAgent()
        self.restaurant_agent = RestaurantAgent()
        self.activity_agent = ActivityAgent(use_mock=True)
        self.history_manager = HistoryManager(
            use_mongodb=True,
            mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017")
        )
        self.trend_analyzer = TrendAnalyzer()

        print("  ✅ All agents initialized!")

    def run_interactive(self) -> UserProfile:
        """Run interactive profile creation"""
        print("\n" + "="*70)
        print("📋 INTERACTIVE PROFILE CREATION")
        print("="*70)
        print("\nLet's create your personalized travel profile!")
        print("This will take about 3-5 minutes.\n")

        builder = InteractiveProfileBuilder()
        profile = builder.build_profile()

        # Optionally save the profile
        if builder.ask_yes_no("\n💾 Would you like to save this profile for future use?", default=True):
            filename = input("\nFilename [my_profile.json]: ").strip() or "my_profile.json"
            builder.save_profile(filename)
            print(f"\n✅ Profile saved! You can load it later from {filename}")

        return profile

    def run_with_profile(self, profile: UserProfile):
        """Generate itinerary with given profile"""
        itinerary = self._generate_itinerary(profile)
        self.display_itinerary(itinerary)

    def _generate_itinerary(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Generate complete itinerary"""

        print("\n" + "="*70)
        print("🚀 GENERATING YOUR PERSONALIZED ITINERARY")
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

        print(f"\n📋 Trip Summary:")
        print(f"  👤 Traveler: {user_profile.name}")
        print(f"  📍 Destination: {destination}")
        print(f"  📅 Duration: {num_days} days ({start_date} to {end_date})")
        print(f"  💰 Budget: {user_profile.default_currency} {user_profile.travel_preferences.budget_total:,.2f}")
        print(f"  🎨 Interests: {', '.join(user_profile.travel_preferences.activity_interests[:3])}")

        # Step 1: Trends
        print("\n[1/6] 🔍 Analyzing seasonal trends and attractions...")
        seasonal_suggestions = self.trend_analyzer.get_seasonal_suggestions(destination, start_date)
        popular_events = self.trend_analyzer.get_popular_events(destination, start_date)

        if seasonal_suggestions:
            print(f"  ✅ Found {len(seasonal_suggestions)} seasonal attractions")
        if popular_events:
            print(f"  ✅ Found {len(popular_events)} popular events")

        # Step 2: Flights
        print("\n[2/6] ✈️ Searching flights with Amadeus TEST API...")
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
        else:
            print("  ⚠️ No flights found, using alternatives")

        # Step 3: Accommodations
        print("\n[3/6] 🏨 Searching accommodations with OpenStreetMap API...")
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
        else:
            print("  ⚠️ No accommodations found")

        # Step 4: Restaurants
        print("\n[4/6] 🍽️ Searching restaurants with OpenStreetMap API...")
        restaurants = self.restaurant_agent.search_restaurants(
            location=destination,
            dietary_restrictions=user_profile.travel_preferences.dietary_restrictions,
            max_results=15
        )

        if restaurants:
            print(f"  ✅ Found {len(restaurants)} real restaurants")
            restaurants = self.restaurant_agent.rank_restaurants(restaurants)
        else:
            print("  ⚠️ No restaurants found")

        # Step 5: Activities
        print("\n[5/6] 🎯 Searching activities matching your interests...")
        activities = self.activity_agent.search_activities(
            location=destination,
            interests=user_profile.travel_preferences.activity_interests,
            max_results=20
        )

        if activities:
            print(f"  ✅ Found {len(activities)} activities")
            activities = self.activity_agent.filter_by_interests(
                activities,
                user_profile.travel_preferences.activity_interests
            )

        # Step 6: Optimize
        print("\n[6/6] 🎯 Optimizing your itinerary...")
        print("       (This may take a few seconds...)")
        
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
            print(f"  🎯 Activities: {optimized_itinerary['num_activities']}")
            print(f"  💵 Budget Remaining: {optimized_itinerary['currency']} {optimized_itinerary.get('budget_remaining', 0):,.2f}")
        else:
            print(f"  ❌ Optimization failed: {optimized_itinerary['error']}")

        # Add metadata
        optimized_itinerary['seasonal_suggestions'] = seasonal_suggestions
        optimized_itinerary['popular_events'] = popular_events
        optimized_itinerary['user_profile'] = user_profile.to_dict()

        # Store in history if consent given
        if user_profile.consent.get('store_history'):
            print("\n💾 Saving trip to your history...")
            self.history_manager.store_user_profile(user_profile)

        return optimized_itinerary

    def _get_airport_code(self, destination: str) -> str:
        """Get airport code"""
        codes = {
            'tokyo': 'NRT', 'delhi': 'DEL', 'mumbai': 'BOM',
            'singapore': 'SIN', 'bangkok': 'BKK', 'dubai': 'DXB',
            'london': 'LHR', 'paris': 'CDG', 'new york': 'JFK',
            'rome': 'FCO', 'barcelona': 'BCN', 'amsterdam': 'AMS'
        }
        for city, code in codes.items():
            if city in destination.lower():
                return code
        return 'DEL'

    def display_itinerary(self, itinerary: Dict[str, Any]):
        """Display itinerary in a beautiful format"""
        if 'error' in itinerary:
            print(f"\n❌ Error: {itinerary['error']}")
            if 'details' in itinerary:
                for detail in itinerary['details']:
                    print(f"   - {detail}")
            return

        print("\n" + "="*70)
        print("🎉 YOUR PERSONALIZED TRAVEL ITINERARY")
        print("="*70)

        # Summary Section
        print(f"\n📊 TRIP SUMMARY")
        print("-" * 70)
        print(f"💰 Total Cost: {itinerary['currency']} {itinerary['total_cost']:,.2f}")
        print(f"💵 Budget Remaining: {itinerary['currency']} {itinerary.get('budget_remaining', 0):,.2f}")
        print(f"📅 Duration: {itinerary['num_days']} days")
        print(f"🎯 Activities: {itinerary['num_activities']}")
        print(f"🍽️ Restaurants: {itinerary.get('num_restaurants', 0)}")
        print(f"🏨 Accommodations: {itinerary.get('num_accommodations', 0)}")

        # Day-by-day breakdown
        print("\n" + "="*70)
        print("📅 DAY-BY-DAY ITINERARY")
        print("="*70)

        for day_num in range(itinerary['num_days']):
            if day_num not in itinerary.get('itinerary', {}):
                continue

            items = itinerary['itinerary'][day_num]

            print(f"\n{'='*70}")
            print(f"📆 DAY {day_num + 1}")
            print(f"{'='*70}")

            if not items:
                print("  🛌 Free day / Rest day")
                continue

            day_cost = sum(getattr(item, 'cost', 0) for item in items)
            print(f"💰 Daily Cost: {itinerary['currency']} {day_cost:,.2f}\n")

            for i, item in enumerate(items, 1):
                # Get item details
                item_name = getattr(item, 'name', 'Unknown')
                item_type = getattr(item, 'item_type', 'Unknown')

                # Time
                if hasattr(item, 'start_time'):
                    hours = item.start_time // 60
                    mins = item.start_time % 60
                    time_str = f"{hours:02d}:{mins:02d}"
                else:
                    time_str = "00:00"

                # Icon based on type
                icons = {
                    'flight': '✈️',
                    'accommodation': '🏨',
                    'restaurant': '🍽️',
                    'activity': '🎯'
                }
                icon = icons.get(item_type.lower(), '📍')

                print(f"{i}. [{time_str}] {icon} {item_name}")
                print(f"   Type: {item_type.title()}")

                # Duration
                if hasattr(item, 'duration'):
                    duration_hours = item.duration // 60
                    duration_mins = item.duration % 60
                    if duration_hours > 0:
                        print(f"   Duration: {duration_hours}h {duration_mins}m")
                    else:
                        print(f"   Duration: {duration_mins}m")

                # Cost
                cost = getattr(item, 'cost', 0)
                print(f"   Cost: {itinerary['currency']} {cost:,.2f}")

                # Location (if available)
                if hasattr(item, 'latitude') and hasattr(item, 'longitude'):
                    if item.latitude != 0 and item.longitude != 0:
                        print(f"   📍 Location: {item.latitude:.4f}, {item.longitude:.4f}")

                print()

        # Seasonal suggestions
        if itinerary.get('seasonal_suggestions'):
            print("\n" + "="*70)
            print("🌸 SEASONAL ATTRACTIONS")
            print("="*70)
            for sugg in itinerary['seasonal_suggestions']:
                print(f"  • {sugg['name']} ({sugg['season'].title()})")

        # Popular events
        if itinerary.get('popular_events'):
            print("\n" + "="*70)
            print("🎊 POPULAR EVENTS DURING YOUR VISIT")
            print("="*70)
            for event in itinerary['popular_events']:
                print(f"  • {event['name']} (Popularity: {event['popularity']:.0%})")

        # Optimization stats
        if 'solver_stats' in itinerary:
            print("\n" + "="*70)
            print("📈 OPTIMIZATION STATISTICS")
            print("="*70)
            stats = itinerary['solver_stats']
            print(f"  Status: {stats['status']}")
            print(f"  Objective Value: {stats['objective_value']:.2f}")
            print(f"  Solve Time: {stats['solve_time']:.4f} seconds")
            print(f"  Items Selected: {stats['total_items']}")

        print("\n" + "="*70)
        print("✅ Itinerary Generation Complete!")
        print("="*70)


def show_menu():
    """Display main menu"""
    print("\n" + "="*70)
    print("🌍 TRAVEL ITINERARY GENERATOR - MAIN MENU")
    print("="*70)
    print("\nChoose an option:")
    print("  1. 📝 Create NEW profile (Interactive)")
    print("  2. 📂 Load EXISTING profile from file")
    print("  3. 🎲 Use SAMPLE profile (Quick test)")
    print("  4. 🤖 Use LangChain AI Mode (Advanced)")
    print("  5. ❌ Exit")
    print("="*70)

    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return choice
        print("❌ Invalid choice. Please enter 1, 2, 3, 4, or 5.")


def main():
    """Main function"""
    print("\n🌟 Welcome to the AI-Driven Travel Itinerary Generator!")
    print("   Your personal AI travel assistant")

    generator = TravelItineraryGenerator()

    while True:
        choice = show_menu()

        if choice == '1':
            # Interactive profile creation
            profile = generator.run_interactive()
            if profile:
                generator.run_with_profile(profile)
            break

        elif choice == '2':
            # Load from file
            filename = input("\nEnter profile filename [my_profile.json]: ").strip()
            filename = filename or "my_profile.json"

            try:
                profile = UserProfile.from_json(filepath=filename)
                print(f"✅ Profile loaded: {profile.name}")
                generator.run_with_profile(profile)
                break
            except FileNotFoundError:
                print(f"❌ File not found: {filename}")
                print("   Please create a profile first (Option 1)")
            except Exception as e:
                print(f"❌ Error loading profile: {e}")

        elif choice == '3':
            # Use sample profile
            print("\n📋 Loading sample profile...")
            profile = create_sample_profile()
            print(f"✅ Sample profile loaded: {profile.name}")
            print(f"   Destination: {profile.destinations[0]}")
            print(f"   Budget: {profile.default_currency} {profile.travel_preferences.budget_total:,.2f}")

            if input("\nProceed with sample profile? (y/n) [y]: ").strip().lower() != 'n':
                generator.run_with_profile(profile)
                break

        elif choice == '4':
            # LangChain mode
            print("\n🤖 Launching LangChain AI Mode...")
            try:
                from llm_orchestrator import CompleteLangChainAgenticAI
                ai = CompleteLangChainAgenticAI()
                if ai.genai_model:
                    ai.interactive_with_agents()
                else:
                    print("❌ LangChain mode requires GOOGLE_API_KEY in .env file")
            except ImportError:
                print("❌ LangChain modules not found")
                print("   Install with: pip install -r requirements.txt")
            break

        elif choice == '5':
            print("\n👋 Thank you for using Travel Itinerary Generator!")
            print("   Safe travels! 🌍✈️")
            return

    print("\n" + "="*70)
    print("🎉 Thank you for using the AI Travel Itinerary Generator!")
    print("   We hope you have an amazing trip!")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
        print("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
