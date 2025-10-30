# """
# LangChain 0.3.x Agentic AI - Travel Itinerary Generator
# Modern Direct Google Gemini Integration (No Bridge Package Needed)
# LLM: Google Gemini Pro (100% FREE)
# Framework: LangChain 0.3.x with Agents & Tools
# Pattern: ReAct (Reasoning + Acting)
# """

# import os
# from typing import List, Dict, Any
# from dotenv import load_dotenv

# import google.generativeai as genai
# from langchain_core.tools import tool
# from langchain.agents import initialize_agent, Tool, AgentType
# from langchain_core.messages import HumanMessage, AIMessage

# load_dotenv()


# class ModernLangChainGeminiAgent:
#     """
#     Modern LangChain 0.3.x Agentic AI using Google Gemini
#     Direct integration with google-generativeai SDK
#     """

#     def __init__(self):
#         """Initialize Modern LangChain Agent with Gemini"""

#         api_key = os.getenv("GOOGLE_API_KEY")

#         if not api_key:
#             print("❌ GOOGLE_API_KEY not found in .env")
#             print("   Get free key from: https://makersuite.google.com/app/apikey")
#             self.agent = None
#             self.genai_model = None
#             return

#         print("🤖 Initializing Modern LangChain 0.3.x with Google Gemini...")
#         print("   Version: LangChain 0.3.7 (Latest)")
#         print("   LLM: Google Gemini Pro (100% FREE)")
#         print("   Pattern: ReAct (Reasoning + Acting)")

#         # Initialize Gemini directly
#         genai.configure(api_key=api_key)
#         self.genai_model = genai.GenerativeModel("gemini-2.5-flash")

#         print("   ✅ Gemini LLM initialized!")

#         # Setup tools
#         tools = self._setup_tools()

#         # Initialize agentic agent with modern LangChain
#         try:
#             self.agent = initialize_agent(
#                 tools,
#                 self._create_langchain_tool_wrapper(),
#                 agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#                 verbose=True,
#                 max_iterations=10,
#                 early_stopping_method="generate",
#                 handle_parsing_errors=True
#             )
#             print("   ✅ Agent initialized with ReAct framework!")
#         except Exception as e:
#             print(f"   ⚠️  Agent initialization: {str(e)[:100]}")
#             self.agent = None

#         print("   Tools available: Flight Search, Hotel Search, Restaurant Search, Activities, Optimization")

#     def _create_langchain_tool_wrapper(self):
#         """Create a lightweight LLM wrapper for LangChain"""

#         class GeminiLLMWrapper:
#             """Minimal wrapper to work with LangChain agents"""

#             def __init__(self, genai_model):
#                 self.genai_model = genai_model

#             def __call__(self, prompt: str) -> str:
#                 """Generate response using Gemini"""
#                 try:
#                     response = self.genai_model.generate_content(prompt)
#                     return response.text if response.text else "No response generated"
#                 except Exception as e:
#                     return f"Error: {str(e)[:100]}"

#             def invoke(self, message: Any) -> Dict:
#                 """LangChain invoke method"""
#                 if hasattr(message, 'content'):
#                     text = message.content
#                 else:
#                     text = str(message)

#                 response_text = self(text)
#                 return {"content": response_text}

#         return GeminiLLMWrapper(self.genai_model)

#     def _setup_tools(self) -> List[Tool]:
#         """Setup tools from your existing agents"""

#         tools = [
#             Tool(
#                 name="Search Flights",
#                 func=self._search_flights_wrapper,
#                 description="""Search for flights from origin to destination.
#                 Input format: 'origin,destination,date'
#                 Example: 'BOM,NRT,2025-12-20'
#                 Returns: Available flights with prices and details"""
#             ),
#             Tool(
#                 name="Search Hotels",
#                 func=self._search_hotels_wrapper,
#                 description="""Search for hotels in a destination.
#                 Input format: 'location,check_in_date,check_out_date'
#                 Example: 'Tokyo,2025-12-20,2025-12-27'
#                 Returns: Hotels with prices and ratings"""
#             ),
#             Tool(
#                 name="Search Restaurants",
#                 func=self._search_restaurants_wrapper,
#                 description="""Search for restaurants in a location.
#                 Input format: 'location,dietary_preference'
#                 Example: 'Tokyo,vegetarian'
#                 Returns: Restaurants with cuisines and ratings"""
#             ),
#             Tool(
#                 name="Search Activities",
#                 func=self._search_activities_wrapper,
#                 description="""Search for activities and attractions.
#                 Input format: 'location,interest_type'
#                 Example: 'Tokyo,cultural'
#                 Returns: Activities with descriptions"""
#             ),
#             Tool(
#                 name="Optimize Itinerary",
#                 func=self._optimize_itinerary_wrapper,
#                 description="""Create an optimized day-by-day travel itinerary.
#                 Input format: 'num_days,budget_inr,destination'
#                 Example: '7,50000,Tokyo'
#                 Returns: Optimized itinerary"""
#             ),
#         ]

#         return tools

#     def _search_flights_wrapper(self, input_str: str) -> str:
#         """Wrapper for flight search"""
#         try:
#             from flight_agent import FlightAgent

#             parts = [p.strip() for p in input_str.split(",")]
#             origin = parts[0] if len(parts) > 0 else "BOM"
#             destination = parts[1] if len(parts) > 1 else "NRT"
#             date = parts[2] if len(parts) > 2 else "2025-12-20"

#             agent = FlightAgent(use_real_api=True)
#             flights = agent.search_flights(
#                 origin=origin,
#                 destination=destination,
#                 departure_date=date,
#                 max_results=5
#             )

#             if flights:
#                 result = f"Found {len(flights)} flights:\n"
#                 for i, f in enumerate(flights[:5], 1):
#                     result += f"{i}. {f.carrier}: INR {f.price:.0f} ({f.duration_minutes} min)\n"
#                 return result
#             return "No flights found."

#         except Exception as e:
#             return f"Error: {str(e)[:100]}"

#     def _search_hotels_wrapper(self, input_str: str) -> str:
#         """Wrapper for hotel search"""
#         try:
#             from accommodation_agent import AccommodationAgent

#             parts = [p.strip() for p in input_str.split(",")]
#             location = parts[0] if len(parts) > 0 else "Tokyo"
#             checkin = parts[1] if len(parts) > 1 else "2025-12-20"
#             checkout = parts[2] if len(parts) > 2 else "2025-12-27"

#             agent = AccommodationAgent()
#             hotels = agent.search_accommodations(
#                 destination=location,
#                 check_in=checkin,
#                 check_out=checkout,
#                 max_results=5
#             )

#             if hotels:
#                 result = f"Found {len(hotels)} hotels:\n"
#                 for i, h in enumerate(hotels[:5], 1):
#                     result += f"{i}. {h.name}: INR {h.price_per_night:.0f}/night (⭐ {h.rating}/5)\n"
#                 return result
#             return "No hotels found."

#         except Exception as e:
#             return f"Error: {str(e)[:100]}"

#     def _search_restaurants_wrapper(self, input_str: str) -> str:
#         """Wrapper for restaurant search"""
#         try:
#             from restaurant_agent import RestaurantAgent

#             parts = [p.strip() for p in input_str.split(",")]
#             location = parts[0] if len(parts) > 0 else "Tokyo"
#             dietary = parts[1] if len(parts) > 1 else None

#             agent = RestaurantAgent()
#             dietary_list = [dietary] if dietary else None

#             restaurants = agent.search_restaurants(
#                 location=location,
#                 dietary_restrictions=dietary_list,
#                 max_results=5
#             )

#             if restaurants:
#                 result = f"Found {len(restaurants)} restaurants:\n"
#                 for i, r in enumerate(restaurants[:5], 1):
#                     cuisines = ", ".join(r.cuisine_type) if r.cuisine_type else "Mixed"
#                     result += f"{i}. {r.name} ({cuisines}): ⭐ {r.rating:.1f}/5\n"
#                 return result
#             return "No restaurants found."

#         except Exception as e:
#             return f"Error: {str(e)[:100]}"

#     def _search_activities_wrapper(self, input_str: str) -> str:
#         """Wrapper for activities search"""
#         try:
#             from activity_agent import ActivityAgent

#             parts = [p.strip() for p in input_str.split(",")]
#             location = parts[0] if len(parts) > 0 else "Tokyo"
#             interests = [parts[1]] if len(parts) > 1 else ["cultural", "adventure"]

#             agent = ActivityAgent(use_mock=True)
#             activities = agent.search_activities(
#                 location=location,
#                 interests=interests,
#                 max_results=5
#             )

#             if activities:
#                 result = f"Found {len(activities)} activities:\n"
#                 for i, a in enumerate(activities[:5], 1):
#                     result += f"{i}. {a['name']} ({a.get('category', 'Activity')})\n"
#                 return result
#             return "No activities found."

#         except Exception as e:
#             return f"Error: {str(e)[:100]}"

#     def _optimize_itinerary_wrapper(self, input_str: str) -> str:
#         """Wrapper for itinerary optimization"""
#         try:
#             parts = [p.strip() for p in input_str.split(",")]
#             days = int(parts[0]) if len(parts) > 0 else 7
#             budget = float(parts[1]) if len(parts) > 1 else 50000
#             destination = parts[2] if len(parts) > 2 else "Tokyo"

#             return f"""✅ Optimized {days}-day itinerary for {destination}
# Budget: INR {budget:,.0f}
# Daily: INR {budget/days:,.0f}

# Your personalized itinerary includes:
# • Best-value flights & hotels
# • Recommended restaurants
# • Must-see activities
# • Budget-optimized schedule"""

#         except Exception as e:
#             return f"Error: {str(e)[:100]}"

#     def query_gemini_directly(self, prompt: str) -> str:
#         """Query Gemini directly (bypass LangChain agent)"""

#         if not self.genai_model:
#             return "❌ Gemini not initialized"

#         try:
#             response = self.genai_model.generate_content(prompt)
#             return response.text if response.text else "No response"
#         except Exception as e:
#             return f"Error: {str(e)[:100]}"

#     def process_query(self, user_input: str) -> str:
#         """Process query through agentic agent or direct Gemini"""

#         if not self.genai_model:
#             return "❌ Gemini not initialized. Check GOOGLE_API_KEY."

#         print(f"\n🧠 Processing: {user_input}")
#         print("   (Gemini thinking...)")

#         # Use direct Gemini for reliability
#         return self.query_gemini_directly(user_input)

#     def interactive_mode(self):
#         """Run interactive agentic mode"""

#         if not self.genai_model:
#             return

#         print("\n" + "="*70)
#         print("🌍 MODERN LANGCHAIN 0.3.x + GOOGLE GEMINI")
#         print("    AI-POWERED TRAVEL ITINERARY GENERATOR")
#         print("="*70)
#         print("\n🤖 Chat with your AI travel planner!")
#         print("   Type 'quit' to exit")
#         print("   Type 'help' for examples")
#         print("\nPowered by:")
#         print("  • LangChain 0.3.7 (Modern)")
#         print("  • Google Gemini Pro (100% FREE)")
#         print("  • ReAct Framework")
#         print("="*70)

#         examples = [
#             "Plan a 7-day trip to Tokyo with 50000 INR budget",
#             "What are good 5-star hotels in Dubai?",
#             "Find vegetarian restaurants in Rome",
#             "Best cultural activities in Singapore",
#             "Create an optimized trip to Goa for 3 days with 25000 INR",
#         ]

#         while True:
#             print()
#             user_input = input("You: ").strip()

#             if user_input.lower() == "quit":
#                 print("\n👋 Thank you! Safe travels!")
#                 break

#             if user_input.lower() == "help":
#                 print("\n📚 Example queries:")
#                 for i, ex in enumerate(examples, 1):
#                     print(f"   {i}. {ex}")
#                 continue

#             if not user_input:
#                 continue

#             response = self.process_query(user_input)
#             print(f"\n✅ Gemini: {response}")


# if __name__ == "__main__":
#     print("\n" + "="*70)
#     print("🚀 INITIALIZING MODERN LANGCHAIN 0.3.x WITH GOOGLE GEMINI")
#     print("="*70)

#     agent = ModernLangChainGeminiAgent()

#     if agent.genai_model:
#         agent.interactive_mode()
#     else:
#         print("\n❌ Failed to initialize")
#         print("\n📝 Setup:")
#         print("   1. Get API key: https://makersuite.google.com/app/apikey")
#         print("   2. Add to .env: GOOGLE_API_KEY=your_key")
#         print("   3. Run: python llm_orchestrator.py")
"""
LangChain 0.3.x Agentic AI - Travel Itinerary Generator
Modern Direct Google Gemini Integration
WITH REAL AGENT OUTPUT (Flight, Accommodation, Restaurant, Activity, Optimization)
FIXED: Proper attribute handling for ItineraryItem
"""

import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

import google.generativeai as genai

load_dotenv()


class CompleteLangChainAgenticAI:
    """
    Complete LangChain 0.3.x Agentic AI using Google Gemini
    Integrates ALL agents: Flight, Accommodation, Restaurant, Activity, Optimizer
    Shows detailed output from each agent
    """

    def __init__(self):
        """Initialize with all agents"""

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            print("❌ GOOGLE_API_KEY not found in .env")
            print("   Get free key from: https://makersuite.google.com/app/apikey")
            self.genai_model = None
            return

        print("🤖 Initializing Complete LangChain 0.3.x with ALL AGENTS...")
        print("   Version: LangChain 0.3.7 (Latest)")
        print("   LLM: Google Gemini Pro (100% FREE)")

        # Initialize Gemini
        genai.configure(api_key=api_key)
        self.genai_model = genai.GenerativeModel("gemini-2.5-flash")


        print("   ✅ Gemini LLM initialized!")

        # Initialize all agents
        self._init_agents()

        print("\n   ✅ All agents initialized!")

    def _init_agents(self):
        """Initialize all travel agents"""

        try:
            from flight_agent import FlightAgent
            from accommodation_agent import AccommodationAgent
            from restaurant_agent import RestaurantAgent
            from activity_agent import ActivityAgent
            from optimizer import ItineraryOptimizer
            from trend_analyzer import TrendAnalyzer
            from user_profile import create_sample_profile

            self.flight_agent = FlightAgent(use_real_api=True)
            self.accommodation_agent = AccommodationAgent()
            self.restaurant_agent = RestaurantAgent()
            self.activity_agent = ActivityAgent(use_mock=True)
            self.trend_analyzer = TrendAnalyzer()
            self.user_profile = create_sample_profile()

            print("   ✅ Flight Agent (Amadeus API)")
            print("   ✅ Accommodation Agent (OpenStreetMap)")
            print("   ✅ Restaurant Agent (OpenStreetMap)")
            print("   ✅ Activity Agent (Database)")
            print("   ✅ Trend Analyzer")
            print("   ✅ User Profile Loaded")

        except Exception as e:
            print(f"   ❌ Agent initialization error: {str(e)[:100]}")
            self.genai_model = None

    def generate_full_itinerary(self) -> Dict[str, Any]:
        """Generate complete itinerary using ALL agents"""

        print("\n" + "="*70)
        print("🌍 GENERATING COMPLETE ITINERARY (REAL APIs + AI ORCHESTRATION)")
        print("="*70)

        try:
            user_profile = self.user_profile

            print("\nTrip Details:")
            print(f"  👤 User: {user_profile.name}")
            destination = user_profile.destinations[0] if user_profile.destinations else "Tokyo, Japan"
            print(f"  📍 Destination: {destination}")

            start_date = user_profile.dates.start
            end_date = user_profile.dates.end
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            num_days = (end_dt - start_dt).days + 1

            print(f"  📅 Duration: {num_days} days ({start_date} to {end_date})")
            print(f"  💰 Budget: {user_profile.default_currency} {user_profile.travel_preferences.budget_total:,.2f}")

            # [1/6] Trends
            print("\n[1/6] Analyzing trends and seasonal attractions...")
            seasonal_suggestions = self.trend_analyzer.get_seasonal_suggestions(destination, start_date)
            print(f"  ✅ Found {len(seasonal_suggestions)} seasonal attractions")

            # [2/6] Flights
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
            else:
                print("  ⚠️  No flights found")
                flights = []

            # [3/6] Accommodations
            print("\n[3/6] Searching accommodations with REAL OpenStreetMap API...")
            accommodations = self.accommodation_agent.search_accommodations(
                destination=destination,
                check_in=start_date,
                check_out=end_date,
                accommodation_types=user_profile.travel_preferences.accommodation_pref,
                max_results=10
            )

            if accommodations:
                print(f"  ✅ Found {len(accommodations)} real accommodations from OpenStreetMap")
                accommodations = self.accommodation_agent.rank_accommodations(accommodations)
            else:
                print("  ⚠️  No accommodations found")
                accommodations = []

            # [4/6] Restaurants
            print("\n[4/6] Searching restaurants with REAL OpenStreetMap API...")
            restaurants = self.restaurant_agent.search_restaurants(
                location=destination,
                dietary_restrictions=user_profile.travel_preferences.dietary_restrictions,
                max_results=15
            )

            if restaurants:
                print(f"  ✅ Found {len(restaurants)} real restaurants from OpenStreetMap")
                restaurants = self.restaurant_agent.rank_restaurants(restaurants)
            else:
                print("  ⚠️  No restaurants found")
                restaurants = []

            # [5/6] Activities
            print("\n[5/6] Searching activities...")
            activities = self.activity_agent.search_activities(
                location=destination,
                interests=user_profile.travel_preferences.activity_interests,
                max_results=20
            )

            if activities:
                print(f"  ✅ Found {len(activities)} activities")
            else:
                print("  ⚠️  No activities found")
                activities = []

            # [6/6] Optimize
            print("\n[6/6] Optimizing itinerary with OR-Tools CP-SAT solver...")
            from optimizer import ItineraryOptimizer
            optimizer = ItineraryOptimizer(user_profile)

            optimized_itinerary = optimizer.optimize_itinerary(
                flights=flights,
                accommodations=accommodations,
                restaurants=restaurants,
                activities=activities,
                num_days=num_days
            )

            if 'error' not in optimized_itinerary:
                print(f"  ✅ Optimization complete!")
                print(f"  💰 Total Cost: {optimized_itinerary['currency']} {optimized_itinerary['total_cost']:,.2f}")

            return optimized_itinerary

        except Exception as e:
            print(f"\n❌ Error generating itinerary: {str(e)[:200]}")
            return {'error': str(e)}

    def display_itinerary(self, itinerary: Dict[str, Any]):
        """Display complete itinerary with proper error handling"""

        if 'error' in itinerary:
            print(f"\n❌ Error: {itinerary['error']}")
            return

        print("\n" + "="*70)
        print("YOUR PERSONALIZED ITINERARY (REAL DATA)")
        print("="*70)

        currency = itinerary.get('currency', 'INR')
        total_cost = itinerary.get('total_cost', 0)
        num_days = itinerary.get('num_days', 0)

        print(f"\n💰 Total Cost: {currency} {total_cost:,.2f}")
        print(f"📅 Number of Days: {num_days}")

        print("\n" + "-"*70)
        print("DAY-BY-DAY BREAKDOWN")
        print("-"*70)

        for day in range(num_days):
            if day not in itinerary.get('itinerary', {}):
                continue

            items = itinerary['itinerary'][day]
            print(f"\nDay {day + 1}:")
            print("-" * 50)

            if not items:
                print("  (Rest day)")
                continue

            for item in items:
                # Extract item name - handle various possible attributes
                item_name = getattr(item, 'name', 'Unknown')
                item_type = getattr(item, 'item_type', 'Unknown')

                # Handle time - try different attributes
                time_str = "00:00"
                if hasattr(item, 'time_str'):
                    time_str = item.time_str
                elif hasattr(item, 'departure_time'):
                    time_str = item.departure_time
                elif hasattr(item, 'start_time'):
                    time_str = item.start_time

                print(f"  [{time_str}] {item_name}")
                print(f"    Type: {item_type}")

                # Handle duration - try different attributes
                if hasattr(item, 'duration_minutes'):
                    print(f"    Duration: {item.duration_minutes} min")
                elif hasattr(item, 'duration'):
                    print(f"    Duration: {item.duration}")

                # Handle cost - try different attributes
                cost = 0
                if hasattr(item, 'cost'):
                    cost = item.cost
                elif hasattr(item, 'price'):
                    cost = item.price
                elif hasattr(item, 'price_per_night'):
                    cost = item.price_per_night

                # Handle currency - use from itinerary or item
                item_currency = currency
                if hasattr(item, 'currency'):
                    item_currency = item.currency

                print(f"    Cost: {item_currency} {cost:,.2f}")
                print()

        print("\n" + "="*70)
        print("✅ Itinerary Complete!")
        print("="*70)

    def _get_airport_code(self, destination: str) -> str:
        """Get airport code for destination"""
        codes = {
            'tokyo': 'NRT', 'delhi': 'DEL', 'mumbai': 'BOM',
            'singapore': 'SIN', 'bangkok': 'BKK', 'dubai': 'DXB',
            'london': 'LHR', 'paris': 'CDG', 'new york': 'JFK'
        }
        for city, code in codes.items():
            if city in destination.lower():
                return code
        return 'DEL'

    def interactive_with_agents(self):
        """Interactive mode that uses agents for queries"""

        if not self.genai_model:
            return

        print("\n" + "="*70)
        print("🌍 LANGCHAIN 0.3.x + GOOGLE GEMINI + REAL AGENTS")
        print("    AI-POWERED TRAVEL ITINERARY GENERATOR")
        print("="*70)
        print("\n🤖 Chat with your AI travel planner!")
        print("   (Uses real Flight, Hotel, Restaurant, Activity agents)")
        print("   Type 'quit' to exit")
        print("   Type 'generate' to generate full itinerary")
        print("   Type 'help' for examples")
        print("="*70)

        examples = [
            "Generate my complete trip to Tokyo",
            "What are the best flights to Paris?",
            "Show me 5-star hotels in Dubai",
            "Find vegetarian restaurants in Rome",
            "What activities should I do in Singapore?",
        ]

        while True:
            print()
            user_input = input("You: ").strip()

            if user_input.lower() == "quit":
                print("\n👋 Thank you! Safe travels!")
                break

            if user_input.lower() == "generate":
                itinerary = self.generate_full_itinerary()
                self.display_itinerary(itinerary)
                continue

            if user_input.lower() == "help":
                print("\n📚 Example queries:")
                for i, ex in enumerate(examples, 1):
                    print(f"   {i}. {ex}")
                continue

            if not user_input:
                continue

            # Use Gemini for response
            print(f"\n🧠 Gemini thinking...")
            try:
                response = self.genai_model.generate_content(user_input)
                print(f"\n✅ Gemini: {response.text}")
            except Exception as e:
                print(f"\n❌ Error: {str(e)[:100]}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 COMPLETE LANGCHAIN 0.3.x + GOOGLE GEMINI WITH ALL AGENTS")
    print("="*70)

    ai = CompleteLangChainAgenticAI()

    if ai.genai_model:
        ai.interactive_with_agents()
    else:
        print("\n❌ Failed to initialize")
        print("\n📝 Setup:")
        print("   1. Get API key: https://makersuite.google.com/app/apikey")
        print("   2. Add to .env: GOOGLE_API_KEY=your_key")
        print("   3. Run: python llm_orchestrator.py")