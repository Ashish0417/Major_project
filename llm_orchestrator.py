# """
# Complete Travel Itinerary Orchestrator
# Generates day-by-day travel plans with flights, hotels, restaurants, and activities
# Uses direct tool calls (no parsing errors) + OR-Tools optimizer
# """

# import os
# from datetime import datetime, timedelta
# from dotenv import load_dotenv

# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.schema import HumanMessage

# # Import existing agents and utilities
# from flight_agent import FlightAgent
# from accommodation_agent import AccommodationAgent
# from restaurant_agent import RestaurantAgent
# from activity_agent import ActivityAgent
# from optimizer import ItineraryOptimizer
# from trend_analyzer import TrendAnalyzer
# from user_profile import create_sample_profile, UserProfile, TripDates

# load_dotenv()


# class TravelItineraryOrchestrator:
#     """Complete orchestrator that generates optimized day-by-day itineraries"""
    
#     def __init__(self):
#         api_key = os.getenv("GOOGLE_API_KEY")
        
#         if not api_key:
#             print("❌ GOOGLE_API_KEY not found in .env")
#             self.llm = None
#             return
        
#         print("🤖 Initializing Travel Itinerary Orchestrator...")
        
#         # Initialize LLM for query understanding
#         self.llm = ChatGoogleGenerativeAI(
#             model="gemini-2.5-flash",
#             temperature=0.2,
#             google_api_key=api_key
#         )
        
#         # Initialize all service agents
#         self.flight_agent = FlightAgent(use_real_api=True)
#         self.hotel_agent = AccommodationAgent()
#         self.restaurant_agent = RestaurantAgent()
#         self.activity_agent = ActivityAgent()
#         self.trend_analyzer = TrendAnalyzer()
        
#         # Airport code mapping
#         self.airport_codes = {
#             'bangalore': 'BLR', 'mumbai': 'BOM', 'delhi': 'DEL',
#             'tokyo': 'NRT', 'paris': 'CDG', 'london': 'LHR',
#             'singapore': 'SIN', 'dubai': 'DXB', 'new york': 'JFK',
#             'rome': 'FCO', 'barcelona': 'BCN', 'amsterdam': 'AMS',
#             'blr': 'BLR', 'bom': 'BOM', 'del': 'DEL',
#             'nrt': 'NRT', 'cdg': 'CDG', 'lhr': 'LHR'
#         }
        
#         self.conversation_history = []
#         print("✅ Orchestrator ready!")
    
#     def parse_date(self, date_str: str) -> str:
#         """Convert various date formats to YYYY-MM-DD"""
#         if not date_str:
#             return None
            
#         # Already in correct format
#         if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
#             return date_str
        
#         # Handle DD-MM-YYYY
#         if '-' in date_str:
#             parts = date_str.split('-')
#             if len(parts[0]) == 2:  # DD-MM-YYYY
#                 return f"{parts[2]}-{parts[1]}-{parts[0]}"
        
#         # Handle natural language dates
#         try:
#             from dateutil import parser
#             parsed = parser.parse(date_str)
#             return parsed.strftime("%Y-%m-%d")
#         except:
#             return date_str
    
#     def get_airport_code(self, city: str) -> str:
#         """Get airport code from city name"""
#         if not city:
#             return None
#         city_lower = city.lower().strip()
#         return self.airport_codes.get(city_lower, city.upper()[:3])
    
#     def extract_trip_details(self, query: str) -> dict:
#         """Extract trip details from natural language query"""
        
#         context = ""
#         if self.conversation_history:
#             context = "Previous conversation:\n"
#             for q, _ in self.conversation_history[-2:]:
#                 context += f"User: {q}\n"
        
#         prompt = f"""{context}

# Current query: {query}

# Extract trip planning information. Respond ONLY with valid JSON:

# {{
#     "origin_city": "city name or null",
#     "destination_city": "city name or null",
#     "departure_date": "YYYY-MM-DD or null",
#     "return_date": "YYYY-MM-DD or null",
#     "num_days": number or null,
#     "budget_inr": number or null,
#     "interests": ["interest1", "interest2"] or null,
#     "dietary_restrictions": ["restriction1"] or null
# }}

# Examples:
# "Plan a trip from Bangalore to Paris from March 1 to March 7"
# → {{"origin_city": "Bangalore", "destination_city": "Paris", "departure_date": "2026-03-01", "return_date": "2026-03-07", "num_days": 7}}

# "I want to visit Tokyo for 5 days starting Feb 9 from Mumbai"
# → {{"origin_city": "Mumbai", "destination_city": "Tokyo", "departure_date": "2026-02-09", "num_days": 5}}
# """

#         try:
#             response = self.llm.invoke([HumanMessage(content=prompt)])
#             text = response.content.strip()
            
#             # Extract JSON
#             if '```json' in text:
#                 text = text.split('```json')[1].split('```')[0].strip()
#             elif '```' in text:
#                 text = text.split('```')[1].split('```')[0].strip()
            
#             import json
#             data = json.loads(text)
            
#             # Calculate missing fields
#             if data.get('departure_date') and data.get('return_date') and not data.get('num_days'):
#                 dep = datetime.strptime(data['departure_date'], '%Y-%m-%d')
#                 ret = datetime.strptime(data['return_date'], '%Y-%m-%d')
#                 data['num_days'] = (ret - dep).days
            
#             if data.get('departure_date') and data.get('num_days') and not data.get('return_date'):
#                 dep = datetime.strptime(data['departure_date'], '%Y-%m-%d')
#                 ret = dep + timedelta(days=data['num_days'])
#                 data['return_date'] = ret.strftime('%Y-%m-%d')
            
#             return data
#         except Exception as e:
#             print(f"   ⚠️ Extraction error: {e}")
#             return {}
    
#     def generate_itinerary(self, trip_details: dict = None, user_profile: UserProfile = None):
#         """Generate complete optimized day-by-day itinerary"""
        
#         print("\n" + "="*80)
#         print("🌍 GENERATING COMPLETE TRAVEL ITINERARY")
#         print("="*80)
        
#         # Use provided details or defaults
#         if not trip_details:
#             trip_details = {}
        
#         origin = trip_details.get('origin_city') or 'Mumbai'
#         destination = trip_details.get('destination_city') or 'Tokyo'
#         departure_date = trip_details.get('departure_date') or '2026-03-20'
#         num_days = trip_details.get('num_days') or 7
#         budget = trip_details.get('budget_inr') or 150000
#         interests = trip_details.get('interests')
#         dietary = trip_details.get('dietary_restrictions')
        
#         # Ensure interests and dietary are lists (handle None, null, or non-list values)
#         if not interests or not isinstance(interests, list):
#             interests = ['cultural', 'adventure']
#         if not dietary or not isinstance(dietary, list):
#             dietary = []
        
#         # Create or use user profile
#         if not user_profile:
#             user_profile = create_sample_profile()
#             # Update profile with trip details
#             if budget:
#                 user_profile.travel_preferences.budget_total = budget
#                 user_profile.travel_preferences.budget_per_day = budget / num_days
#             if destination:
#                 user_profile.destinations = [destination]
#             if departure_date:
#                 return_date_calc = (datetime.strptime(departure_date, '%Y-%m-%d') + timedelta(days=num_days)).strftime('%Y-%m-%d')
#                 user_profile.dates = TripDates(start=departure_date, end=return_date_calc)
#             if interests:
#                 user_profile.travel_preferences.activity_interests = interests
#             if dietary:
#                 user_profile.travel_preferences.dietary_restrictions = dietary
        
#         origin_code = self.get_airport_code(origin)
#         dest_code = self.get_airport_code(destination)
        
#         print(f"\n📍 Route: {origin} ({origin_code}) → {destination} ({dest_code})")
#         print(f"📅 Dates: {departure_date} ({num_days} days)")
#         print(f"💰 Budget: INR {budget:,}")
#         print(f"🎯 Interests: {', '.join(interests)}")
#         if dietary:
#             print(f"🥗 Dietary: {', '.join(dietary)}")
        
#         # Calculate return date
#         dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
#         return_date = (dep_date + timedelta(days=num_days)).strftime('%Y-%m-%d')
        
#         # [1/6] Analyze trends
#         print(f"\n{'='*80}")
#         print("[1/6] 🔍 ANALYZING SEASONAL TRENDS")
#         print("="*80)
        
#         try:
#             trends = self.trend_analyzer.get_seasonal_suggestions(destination, departure_date)
#             if trends:
#                 print(f"✅ Found {len(trends)} seasonal attractions")
#                 for trend in trends[:3]:
#                     print(f"   • {trend['name']} ({trend['season']})")
#             else:
#                 print("   No specific seasonal trends found")
#         except Exception as e:
#             print(f"   ⚠️ Trend analysis unavailable: {str(e)[:50]}")
#             trends = []
        
#         # [2/6] Search flights
#         print(f"\n{'='*80}")
#         print("[2/6] ✈️  SEARCHING FLIGHTS")
#         print("="*80)
#         print(f"   Outbound: {origin_code} → {dest_code} on {departure_date}")
        
#         flights = self.flight_agent.search_flights(
#             origin=origin_code,
#             destination=dest_code,
#             departure_date=departure_date,
#             max_results=10
#         )
        
#         if flights:
#             print(f"✅ Found {len(flights)} flights")
#             for i, f in enumerate(flights[:3], 1):
#                 hrs = f.duration_minutes // 60
#                 mins = f.duration_minutes % 60
#                 print(f"   {i}. {f.carrier} {f.flight_id}: INR {f.price:,.0f} ({hrs}h {mins}m)")
#         else:
#             print("   ⚠️ No flights found (will use mock data)")
#             flights = []
        
#         # [3/6] Search accommodations
#         print(f"\n{'='*80}")
#         print("[3/6] 🏨 SEARCHING ACCOMMODATIONS")
#         print("="*80)
#         print(f"   Location: {destination}")
#         print(f"   Check-in: {departure_date}, Check-out: {return_date}")
        
#         hotels = self.hotel_agent.search_accommodations(
#             destination=destination,
#             check_in=departure_date,
#             check_out=return_date,
#             max_results=10
#         )
        
#         if hotels:
#             print(f"✅ Found {len(hotels)} accommodations")
#             for i, h in enumerate(hotels[:3], 1):
#                 print(f"   {i}. {h.name}: INR {h.price_per_night:,.0f}/night ({h.type})")
#         else:
#             print("   ⚠️ No accommodations found (will use mock data)")
#             hotels = []
        
#         # [4/6] Search restaurants
#         print(f"\n{'='*80}")
#         print("[4/6] 🍽️  SEARCHING RESTAURANTS")
#         print("="*80)
#         print(f"   Location: {destination}")
#         if dietary:
#             print(f"   Dietary: {', '.join(dietary)}")
        
#         restaurants = self.restaurant_agent.search_restaurants(
#             location=destination,
#             dietary_restrictions=dietary if dietary else None,
#             max_results=20
#         )
        
#         if restaurants:
#             print(f"✅ Found {len(restaurants)} restaurants")
#             restaurants = self.restaurant_agent.rank_restaurants(restaurants)
#             for i, r in enumerate(restaurants[:3], 1):
#                 print(f"   {i}. {r.name}: {r.cuisine_type}")
#         else:
#             print("   ⚠️ No restaurants found (will use mock data)")
#             restaurants = []
        
#         # [5/6] Search activities
#         print(f"\n{'='*80}")
#         print("[5/6] 🎭 SEARCHING ACTIVITIES")
#         print("="*80)
#         print(f"   Location: {destination}")
#         print(f"   Interests: {', '.join(interests)}")
        
#         activities = self.activity_agent.search_activities(
#             location=destination,
#             interests=interests if interests else None,
#             max_results=25
#         )
        
#         if activities:
#             print(f"✅ Found {len(activities)} activities")
#             for i, a in enumerate(activities[:3], 1):
#                 print(f"   {i}. {a.name}: {a.description[:50]}...")
#         else:
#             print("   ⚠️ No activities found (will use mock data)")
#             activities = []
        
#         # [6/6] Optimize itinerary
#         print(f"\n{'='*80}")
#         print("[6/6] 🧮 OPTIMIZING ITINERARY (OR-Tools CP-SAT)")
#         print("="*80)
        
#         optimizer = ItineraryOptimizer(user_profile)
        
#         optimized = optimizer.optimize_itinerary(
#             flights=flights,
#             accommodations=hotels,
#             restaurants=restaurants,
#             activities=activities,
#             num_days=num_days
#         )
        
#         if 'error' in optimized:
#             print(f"   ❌ Optimization error: {optimized['error']}")
#             return
        
#         print(f"✅ Optimization complete!")
#         print(f"   Total cost: {optimized.get('currency', 'INR')} {optimized.get('total_cost', 0):,.2f}")
#         print(f"   Budget remaining: INR {budget - optimized.get('total_cost', 0):,.2f}")
        
#         # Display day-by-day itinerary
#         self.display_itinerary(optimized, trip_details)
        
#         return optimized
    
#     def display_itinerary(self, itinerary: dict, trip_details: dict):
#         """Display formatted day-by-day itinerary"""
        
#         print("\n" + "="*80)
#         print("📋 YOUR PERSONALIZED DAY-BY-DAY ITINERARY")
#         print("="*80)
        
#         destination = trip_details.get('destination_city', 'Destination')
        
#         print(f"\n🌍 Destination: {destination}")
#         print(f"💰 Total Cost: {itinerary.get('currency', 'INR')} {itinerary.get('total_cost', 0):,.2f}")
#         print(f"📅 Duration: {itinerary.get('num_days', 0)} days")
        
#         # Day-by-day breakdown
#         for day_num in range(itinerary.get('num_days', 0)):
#             if day_num not in itinerary.get('itinerary', {}):
#                 continue
            
#             items = itinerary['itinerary'][day_num]
            
#             print(f"\n{'─'*80}")
#             print(f"📅 DAY {day_num + 1}")
#             print(f"{'─'*80}")
            
#             if not items:
#                 print("   🌴 Rest day / Free time")
#                 continue
            
#             day_cost = 0
            
#             for item in items:
#                 # Get item details
#                 name = getattr(item, 'name', 'Unknown')
#                 item_type = getattr(item, 'item_type', 'Unknown')
                
#                 # Time
#                 time_str = "All day"
#                 if hasattr(item, 'time_str'):
#                     time_str = item.time_str
#                 elif hasattr(item, 'departure_time'):
#                     time_str = item.departure_time
#                 elif hasattr(item, 'start_time'):
#                     time_str = item.start_time
                
#                 # Duration
#                 duration_str = ""
#                 if hasattr(item, 'duration_minutes') and item.duration_minutes:
#                     hrs = item.duration_minutes // 60
#                     mins = item.duration_minutes % 60
#                     duration_str = f" ({hrs}h {mins}m)"
#                 elif hasattr(item, 'duration_hours') and item.duration_hours:
#                     duration_str = f" ({item.duration_hours}h)"
                
#                 # Cost
#                 cost = 0
#                 if hasattr(item, 'cost'):
#                     cost = item.cost
#                 elif hasattr(item, 'price'):
#                     cost = item.price
#                 elif hasattr(item, 'price_per_night'):
#                     cost = item.price_per_night
                
#                 day_cost += cost
                
#                 # Icon based on type
#                 icon = "📍"
#                 if 'flight' in item_type.lower():
#                     icon = "✈️"
#                 elif 'hotel' in item_type.lower() or 'accommodation' in item_type.lower():
#                     icon = "🏨"
#                 elif 'restaurant' in item_type.lower():
#                     icon = "🍽️"
#                 elif 'activity' in item_type.lower():
#                     icon = "🎭"
                
#                 print(f"\n   {icon} [{time_str}] {name}{duration_str}")
#                 print(f"      Type: {item_type}")
#                 if cost > 0:
#                     print(f"      Cost: INR {cost:,.2f}")
                
#                 # Additional info
#                 if hasattr(item, 'carrier'):
#                     print(f"      Carrier: {item.carrier}")
#                 if hasattr(item, 'cuisine_type'):
#                     print(f"      Cuisine: {item.cuisine_type}")
#                 if hasattr(item, 'rating') and item.rating:
#                     print(f"      Rating: {'⭐' * int(item.rating)}")
            
#             if day_cost > 0:
#                 print(f"\n   💵 Day {day_num + 1} Total: INR {day_cost:,.2f}")
        
#         print("\n" + "="*80)
#         print("✅ ITINERARY GENERATION COMPLETE!")
#         print("="*80)
    
#     def ask(self, query: str) -> str:
#         """Handle natural language queries"""
        
#         print("\n🧠 Understanding your request...")
        
#         # Check if it's a trip planning request
#         if any(word in query.lower() for word in ['plan', 'trip', 'itinerary', 'travel', 'visit']):
#             trip_details = self.extract_trip_details(query)
            
#             if trip_details.get('destination_city'):
#                 self.generate_itinerary(trip_details)
#                 return "Itinerary generated above ↑"
#             else:
#                 return "❓ I need at least a destination city. Example: 'Plan a trip to Paris from Bangalore'"
        
#         return "❓ I specialize in planning complete trip itineraries. Try: 'Plan a trip from Bangalore to Paris for 5 days'"
    
#     def interactive(self):
#         """Interactive mode"""
        
#         if not self.llm:
#             print("❌ Agent not initialized. Check GOOGLE_API_KEY in .env")
#             return
        
#         print("\n" + "="*80)
#         print("🌍 TRAVEL ITINERARY ORCHESTRATOR")
#         print("="*80)
#         print("\n💡 I create complete day-by-day travel itineraries!")
#         print("\n📝 Commands:")
#         print("   • 'generate' - Create sample 7-day Tokyo itinerary")
#         print("   • 'quit' - Exit")
#         print("\n📋 Examples:")
#         print("   • Plan a trip from Bangalore to Paris from March 1 to March 7")
#         print("   • I want to visit Tokyo for 5 days starting Feb 9 from Mumbai")
#         print("   • Create a 4-day Singapore trip from Delhi with budget 80000 INR")
#         print("="*80)
        
#         while True:
#             user_input = input("\nYou: ").strip()
            
#             if not user_input:
#                 continue
            
#             if user_input.lower() == "quit":
#                 print("\n👋 Safe travels!")
#                 break
            
#             if user_input.lower() == "generate":
#                 self.generate_itinerary()
#                 continue
            
#             self.conversation_history.append((user_input, ""))
#             response = self.ask(user_input)
#             print(f"\n{response}")


# if __name__ == "__main__":
#     orchestrator = TravelItineraryOrchestrator()
#     if orchestrator.llm:
#         orchestrator.interactive()
#     else:
#         print("\n❌ Setup required:")
#         print("   1. Create .env file")
#         print("   2. Add: GOOGLE_API_KEY=your_key")
#         print("   3. Get key from: https://makersuite.google.com/app/apikey")

"""
Complete Travel Itinerary Orchestrator
Generates day-by-day travel plans with flights, hotels, restaurants, and activities
Uses direct tool calls (no parsing errors) + OR-Tools optimizer
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

# Import existing agents and utilities
from flight_agent import FlightAgent
from accommodation_agent import AccommodationAgent
from restaurant_agent import RestaurantAgent
from activity_agent import ActivityAgent
from optimizer import ItineraryOptimizer
from trend_analyzer import TrendAnalyzer
from user_profile import create_sample_profile, UserProfile, TripDates
from currency_converter import CurrencyConverter, convert_to_inr

load_dotenv()


class TravelItineraryOrchestrator:
    """Complete orchestrator that generates optimized day-by-day itineraries"""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("❌ GOOGLE_API_KEY not found in .env")
            self.llm = None
            return
        
        print("🤖 Initializing Travel Itinerary Orchestrator...")
        
        # Initialize LLM for query understanding
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2,
            google_api_key=api_key
        )
        
        # Initialize all service agents
        self.flight_agent = FlightAgent(use_real_api=True)
        self.hotel_agent = AccommodationAgent()
        self.restaurant_agent = RestaurantAgent()
        self.activity_agent = ActivityAgent()
        self.trend_analyzer = TrendAnalyzer()
        self.currency_converter = CurrencyConverter()
        
        print(f"   💱 Currency converter ready ({len(self.currency_converter.rates)} currencies)")
        
        # Airport code mapping
        self.airport_codes = {
            'bangalore': 'BLR', 'mumbai': 'BOM', 'delhi': 'DEL',
            'tokyo': 'NRT', 'paris': 'CDG', 'london': 'LHR',
            'singapore': 'SIN', 'dubai': 'DXB', 'new york': 'JFK',
            'rome': 'FCO', 'barcelona': 'BCN', 'amsterdam': 'AMS',
            'blr': 'BLR', 'bom': 'BOM', 'del': 'DEL',
            'nrt': 'NRT', 'cdg': 'CDG', 'lhr': 'LHR'
        }
        
        self.conversation_history = []
        print("✅ Orchestrator ready!")
    
    def parse_date(self, date_str: str) -> str:
        """Convert various date formats to YYYY-MM-DD"""
        if not date_str:
            return None
            
        # Already in correct format
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            return date_str
        
        # Handle DD-MM-YYYY
        if '-' in date_str:
            parts = date_str.split('-')
            if len(parts[0]) == 2:  # DD-MM-YYYY
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
        
        # Handle natural language dates
        try:
            from dateutil import parser
            parsed = parser.parse(date_str)
            return parsed.strftime("%Y-%m-%d")
        except:
            return date_str
    
    def get_airport_code(self, city: str) -> str:
        """Get airport code from city name"""
        if not city:
            return None
        city_lower = city.lower().strip()
        return self.airport_codes.get(city_lower, city.upper()[:3])
    
    def extract_trip_details(self, query: str) -> dict:
        """Extract trip details from natural language query"""
        
        context = ""
        if self.conversation_history:
            context = "Previous conversation:\n"
            for q, _ in self.conversation_history[-2:]:
                context += f"User: {q}\n"
        
        prompt = f"""{context}

Current query: {query}

Extract trip planning information. Respond ONLY with valid JSON:

{{
    "origin_city": "city name or null",
    "destination_city": "city name or null",
    "departure_date": "YYYY-MM-DD or null",
    "return_date": "YYYY-MM-DD or null",
    "num_days": number or null,
    "budget_inr": number or null,
    "interests": ["interest1", "interest2"] or null,
    "dietary_restrictions": ["restriction1"] or null
}}

Examples:
"Plan a trip from Bangalore to Paris from March 1 to March 7"
→ {{"origin_city": "Bangalore", "destination_city": "Paris", "departure_date": "2026-03-01", "return_date": "2026-03-07", "num_days": 7}}

"I want to visit Tokyo for 5 days starting Feb 9 from Mumbai"
→ {{"origin_city": "Mumbai", "destination_city": "Tokyo", "departure_date": "2026-02-09", "num_days": 5}}
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            text = response.content.strip()
            
            # Extract JSON
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            import json
            data = json.loads(text)
            
            # Calculate missing fields
            if data.get('departure_date') and data.get('return_date') and not data.get('num_days'):
                dep = datetime.strptime(data['departure_date'], '%Y-%m-%d')
                ret = datetime.strptime(data['return_date'], '%Y-%m-%d')
                data['num_days'] = (ret - dep).days
            
            if data.get('departure_date') and data.get('num_days') and not data.get('return_date'):
                dep = datetime.strptime(data['departure_date'], '%Y-%m-%d')
                ret = dep + timedelta(days=data['num_days'])
                data['return_date'] = ret.strftime('%Y-%m-%d')
            
            return data
        except Exception as e:
            print(f"   ⚠️ Extraction error: {e}")
            return {}
    
    def generate_itinerary(self, trip_details: dict = None, user_profile: UserProfile = None):
        """Generate complete optimized day-by-day itinerary"""
        
        print("\n" + "="*80)
        print("🌍 GENERATING COMPLETE TRAVEL ITINERARY")
        print("="*80)
        
        # Use provided details or defaults
        if not trip_details:
            trip_details = {}
        
        origin = trip_details.get('origin_city') or 'Mumbai'
        destination = trip_details.get('destination_city') or 'Tokyo'
        departure_date = trip_details.get('departure_date') or '2026-03-20'
        num_days = trip_details.get('num_days') or 7
        budget = trip_details.get('budget_inr') or 150000
        interests = trip_details.get('interests')
        dietary = trip_details.get('dietary_restrictions')
        
        # Ensure interests and dietary are lists (handle None, null, or non-list values)
        if not interests or not isinstance(interests, list):
            interests = ['cultural', 'adventure']
        if not dietary or not isinstance(dietary, list):
            dietary = []
        
        # Create or use user profile
        if not user_profile:
            user_profile = create_sample_profile()
            # Update profile with trip details
            if budget:
                user_profile.travel_preferences.budget_total = budget
                user_profile.travel_preferences.budget_per_day = budget / num_days
            if destination:
                user_profile.destinations = [destination]
            if departure_date:
                return_date_calc = (datetime.strptime(departure_date, '%Y-%m-%d') + timedelta(days=num_days)).strftime('%Y-%m-%d')
                user_profile.dates = TripDates(start=departure_date, end=return_date_calc)
            if interests:
                user_profile.travel_preferences.activity_interests = interests
            if dietary:
                user_profile.travel_preferences.dietary_restrictions = dietary
        
        origin_code = self.get_airport_code(origin)
        dest_code = self.get_airport_code(destination)
        
        print(f"\n📍 Route: {origin} ({origin_code}) → {destination} ({dest_code})")
        print(f"📅 Dates: {departure_date} ({num_days} days)")
        print(f"💰 Budget: INR {budget:,}")
        print(f"🎯 Interests: {', '.join(interests)}")
        if dietary:
            print(f"🥗 Dietary: {', '.join(dietary)}")
        
        # Calculate return date
        dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
        return_date = (dep_date + timedelta(days=num_days)).strftime('%Y-%m-%d')
        
        # [1/6] Analyze trends
        print(f"\n{'='*80}")
        print("[1/6] 🔍 ANALYZING SEASONAL TRENDS")
        print("="*80)
        
        try:
            trends = self.trend_analyzer.get_seasonal_suggestions(destination, departure_date)
            if trends:
                print(f"✅ Found {len(trends)} seasonal attractions")
                for trend in trends[:3]:
                    print(f"   • {trend['name']} ({trend['season']})")
            else:
                print("   No specific seasonal trends found")
        except Exception as e:
            print(f"   ⚠️ Trend analysis unavailable: {str(e)[:50]}")
            trends = []
        
        # [2/6] Search flights
        print(f"\n{'='*80}")
        print("[2/6] ✈️  SEARCHING FLIGHTS")
        print("="*80)
        print(f"   Outbound: {origin_code} → {dest_code} on {departure_date}")
        
        flights = self.flight_agent.search_flights(
            origin=origin_code,
            destination=dest_code,
            departure_date=departure_date,
            max_results=10
        )
        
        if flights:
            print(f"✅ Found {len(flights)} flights")
            for i, f in enumerate(flights[:3], 1):
                hrs = f.duration_minutes // 60
                mins = f.duration_minutes % 60
                original_price = f"{f.currency} {f.price:,.0f}"
                inr_price = self.currency_converter.convert(f.price, f.currency, 'INR')
                print(f"   {i}. {f.carrier} {f.flight_id}: {original_price} (≈ INR {inr_price:,.0f}) ({hrs}h {mins}m)")
        else:
            print("   ⚠️ No flights found (will use mock data)")
            flights = []
        
        # [3/6] Search accommodations
        print(f"\n{'='*80}")
        print("[3/6] 🏨 SEARCHING ACCOMMODATIONS")
        print("="*80)
        print(f"   Location: {destination}")
        print(f"   Check-in: {departure_date}, Check-out: {return_date}")
        
        hotels = self.hotel_agent.search_accommodations(
            destination=destination,
            check_in=departure_date,
            check_out=return_date,
            max_results=10
        )
        
        if hotels:
            print(f"✅ Found {len(hotels)} accommodations")
            for i, h in enumerate(hotels[:3], 1):
                original_price = f"{h.currency} {h.price_per_night:,.0f}"
                inr_price = self.currency_converter.convert(h.price_per_night, h.currency, 'INR')
                print(f"   {i}. {h.name}: {original_price}/night (≈ INR {inr_price:,.0f}) [{h.type}]")
        else:
            print("   ⚠️ No accommodations found (will use mock data)")
            hotels = []
        
        # [4/6] Search restaurants
        print(f"\n{'='*80}")
        print("[4/6] 🍽️  SEARCHING RESTAURANTS")
        print("="*80)
        print(f"   Location: {destination}")
        if dietary:
            print(f"   Dietary: {', '.join(dietary)}")
        
        restaurants = self.restaurant_agent.search_restaurants(
            location=destination,
            dietary_restrictions=dietary if dietary else None,
            max_results=20
        )
        
        if restaurants:
            print(f"✅ Found {len(restaurants)} restaurants")
            restaurants = self.restaurant_agent.rank_restaurants(restaurants)
            for i, r in enumerate(restaurants[:3], 1):
                print(f"   {i}. {r.name}: {r.cuisine_type}")
        else:
            print("   ⚠️ No restaurants found (will use mock data)")
            restaurants = []
        
        # [5/6] Search activities
        print(f"\n{'='*80}")
        print("[5/6] 🎭 SEARCHING ACTIVITIES")
        print("="*80)
        print(f"   Location: {destination}")
        print(f"   Interests: {', '.join(interests)}")
        
        activities = self.activity_agent.search_activities(
            location=destination,
            interests=interests if interests else None,
            max_results=25
        )
        
        if activities:
            print(f"✅ Found {len(activities)} activities")
            for i, a in enumerate(activities[:3], 1):
                print(f"   {i}. {a.name}: {a.description[:50]}...")
        else:
            print("   ⚠️ No activities found (will use mock data)")
            activities = []
        
        # [6/6] Optimize itinerary
        print(f"\n{'='*80}")
        print("[6/6] 🧮 OPTIMIZING ITINERARY")
        print("="*80)
        
        # Convert all prices to base currency (INR) for optimization
        print("   💱 Converting all prices to INR...")
        base_currency = 'INR'
        
        # Convert flights
        flights_converted = []
        for flight in flights:
            converted_price = self.currency_converter.convert(
                flight.price, 
                flight.currency, 
                base_currency
            )
            # Create new flight object with converted price
            flight.price = converted_price
            flight.currency = base_currency
            flights_converted.append(flight)
        
        # Convert hotels
        hotels_converted = []
        for hotel in hotels:
            converted_price = self.currency_converter.convert(
                hotel.price_per_night,
                hotel.currency,
                base_currency
            )
            hotel.price_per_night = converted_price
            hotel.currency = base_currency
            hotels_converted.append(hotel)
        
        # Convert restaurants
        restaurants_converted = []
        for restaurant in restaurants:
            converted_price = self.currency_converter.convert(
                restaurant.average_meal_cost,
                restaurant.currency,
                base_currency
            )
            restaurant.average_meal_cost = converted_price
            restaurant.currency = base_currency
            restaurants_converted.append(restaurant)
        
        # Convert activities
        activities_converted = []
        for activity in activities:
            if hasattr(activity, 'cost') and hasattr(activity, 'currency'):
                converted_price = self.currency_converter.convert(
                    activity.price,
                    activity.currency,
                    base_currency
                )
                activity.price = converted_price
                activity.currency = base_currency
            activities_converted.append(activity)
        
        print(f"   ✅ All prices converted to {base_currency}")
        
        # Run optimizer with converted prices
        print("   🔧 Running OR-Tools CP-SAT optimizer...")
        
        optimizer = ItineraryOptimizer(user_profile)
        
        optimized = optimizer.optimize_itinerary(
            flights=flights_converted,
            accommodations=hotels_converted,
            restaurants=restaurants_converted,
            activities=activities_converted,
            num_days=num_days
        )
        
        if 'error' in optimized:
            print(f"   ❌ Optimization error: {optimized['error']}")
            return
        
        print(f"✅ Optimization complete!")
        print(f"   Total cost: {optimized.get('currency', 'INR')} {optimized.get('total_cost', 0):,.2f}")
        print(f"   Budget remaining: INR {budget - optimized.get('total_cost', 0):,.2f}")
        
        # Display day-by-day itinerary
        self.display_itinerary(optimized, trip_details)
        
        return optimized
    
    def display_itinerary(self, itinerary: dict, trip_details: dict):
        """Display formatted day-by-day itinerary"""
        
        print("\n" + "="*80)
        print("📋 YOUR PERSONALIZED DAY-BY-DAY ITINERARY")
        print("="*80)
        
        destination = trip_details.get('destination_city', 'Destination')
        
        print(f"\n🌍 Destination: {destination}")
        print(f"💰 Total Cost: {itinerary.get('currency', 'INR')} {itinerary.get('total_cost', 0):,.2f}")
        print(f"📅 Duration: {itinerary.get('num_days', 0)} days")
        
        # Day-by-day breakdown
        for day_num in range(itinerary.get('num_days', 0)):
            if day_num not in itinerary.get('itinerary', {}):
                continue
            
            items = itinerary['itinerary'][day_num]
            
            print(f"\n{'─'*80}")
            print(f"📅 DAY {day_num + 1}")
            print(f"{'─'*80}")
            
            if not items:
                print("   🌴 Rest day / Free time")
                continue
            
            day_cost = 0
            
            for item in items:
                # Get item details
                name = getattr(item, 'name', 'Unknown')
                item_type = getattr(item, 'item_type', 'Unknown')
                
                # Time
                time_str = "All day"
                if hasattr(item, 'time_str'):
                    time_str = item.time_str
                elif hasattr(item, 'departure_time'):
                    time_str = item.departure_time
                elif hasattr(item, 'start_time'):
                    time_str = item.start_time
                
                # Duration
                duration_str = ""
                if hasattr(item, 'duration_minutes') and item.duration_minutes:
                    hrs = item.duration_minutes // 60
                    mins = item.duration_minutes % 60
                    duration_str = f" ({hrs}h {mins}m)"
                elif hasattr(item, 'duration_hours') and item.duration_hours:
                    duration_str = f" ({item.duration_hours}h)"
                
                # Cost
                cost = 0
                if hasattr(item, 'cost'):
                    cost = item.cost
                elif hasattr(item, 'price'):
                    cost = item.price
                elif hasattr(item, 'price_per_night'):
                    cost = item.price_per_night
                
                day_cost += cost
                
                # Icon based on type
                icon = "📍"
                if 'flight' in item_type.lower():
                    icon = "✈️"
                elif 'hotel' in item_type.lower() or 'accommodation' in item_type.lower():
                    icon = "🏨"
                elif 'restaurant' in item_type.lower():
                    icon = "🍽️"
                elif 'activity' in item_type.lower():
                    icon = "🎭"
                
                print(f"\n   {icon} [{time_str}] {name}{duration_str}")
                print(f"      Type: {item_type}")
                if cost > 0:
                    print(f"      Cost: INR {cost:,.2f}")
                
                # Additional info
                if hasattr(item, 'carrier'):
                    print(f"      Carrier: {item.carrier}")
                if hasattr(item, 'cuisine_type'):
                    print(f"      Cuisine: {item.cuisine_type}")
                if hasattr(item, 'rating') and item.rating:
                    print(f"      Rating: {'⭐' * int(item.rating)}")
            
            if day_cost > 0:
                print(f"\n   💵 Day {day_num + 1} Total: INR {day_cost:,.2f}")
        
        print("\n" + "="*80)
        print("✅ ITINERARY GENERATION COMPLETE!")
        print("="*80)
    
    def ask(self, query: str) -> str:
        """Handle natural language queries"""
        
        print("\n🧠 Understanding your request...")
        
        # Check if it's a trip planning request
        if any(word in query.lower() for word in ['plan', 'trip', 'itinerary', 'travel', 'visit']):
            trip_details = self.extract_trip_details(query)
            
            if trip_details.get('destination_city'):
                self.generate_itinerary(trip_details)
                return "Itinerary generated above ↑"
            else:
                return "❓ I need at least a destination city. Example: 'Plan a trip to Paris from Bangalore'"
        
        return "❓ I specialize in planning complete trip itineraries. Try: 'Plan a trip from Bangalore to Paris for 5 days'"
    
    def interactive(self):
        """Interactive mode"""
        
        if not self.llm:
            print("❌ Agent not initialized. Check GOOGLE_API_KEY in .env")
            return
        
        print("\n" + "="*80)
        print("🌍 TRAVEL ITINERARY ORCHESTRATOR")
        print("="*80)
        print("\n💡 I create complete day-by-day travel itineraries!")
        print("\n📝 Commands:")
        print("   • 'generate' - Create sample 7-day Tokyo itinerary")
        print("   • 'quit' - Exit")
        print("\n📋 Examples:")
        print("   • Plan a trip from Bangalore to Paris from March 1 to March 7")
        print("   • I want to visit Tokyo for 5 days starting Feb 9 from Mumbai")
        print("   • Create a 4-day Singapore trip from Delhi with budget 80000 INR")
        print("="*80)
        
        while True:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                print("\n👋 Safe travels!")
                break
            
            if user_input.lower() == "generate":
                self.generate_itinerary()
                continue
            
            self.conversation_history.append((user_input, ""))
            response = self.ask(user_input)
            print(f"\n{response}")


if __name__ == "__main__":
    orchestrator = TravelItineraryOrchestrator()
    if orchestrator.llm:
        orchestrator.interactive()
    else:
        print("\n❌ Setup required:")
        print("   1. Create .env file")
        print("   2. Add: GOOGLE_API_KEY=your_key")
        print("   3. Get key from: https://makersuite.google.com/app/apikey")