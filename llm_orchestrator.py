"""
Complete Travel Itinerary Orchestrator
Generates day-by-day travel plans with flights, hotels, restaurants, and activities
Supports both OR-Tools and LangGraph optimizers (configurable via feature flag)

NEW: LangGraph optimizer for parallel exploration with dynamic constraints
- No hardcoded budget ratios
- Intelligent backtracking
- User-priority-based evaluation
- Flexible constraint handling
"""

import os
from typing import Optional, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

# Import existing agents and utilities
from flight_agent import FlightAgent
from accommodation_agent import AccommodationAgent
from restaurant_agent import RestaurantAgent
from activity_agent import ActivityAgent
from ground_transport_agent import GroundTransportAgent, TransportOption
from optimizer import ItineraryOptimizer
from trend_analyzer import TrendAnalyzer
from user_profile import create_sample_profile, UserProfile, TripDates
from currency_converter import CurrencyConverter, convert_to_inr
from itinerary_enhancer import ItineraryEnhancer, display_enhanced_itinerary
from history_manager import HistoryManager

# Import new LangGraph optimizer (optional)
try:
    from langgraph_optimizer import (
        LangGraphItineraryOptimizer,
        BudgetConstraint,
        UserPreferences,
        OptionCandidate
    )
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print(" LangGraph not available - using OR-Tools only")

from datetime import datetime, timedelta
from dataclasses import dataclass, field
import random
import logging
import time
import tracemalloc
import psutil
import os as os_module
import copy

load_dotenv()
logger = logging.getLogger(__name__)


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Track timing and memory usage across generation steps"""
    step_name: str
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    start_memory_mb: float = 0.0
    end_memory_mb: float = 0.0
    
    def __post_init__(self):
        process = psutil.Process()
        self.start_memory_mb = process.memory_info().rss / 1024 / 1024
    
    def finish(self):
        """Mark step as finished and capture end metrics"""
        self.end_time = time.time()
        process = psutil.Process()
        self.end_memory_mb = process.memory_info().rss / 1024 / 1024
    
    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def memory_delta_mb(self) -> float:
        return self.end_memory_mb - self.start_memory_mb
    
    def __str__(self) -> str:
        duration = f"{self.duration_seconds:.2f}s"
        mem_usage = f"{self.memory_delta_mb:+.1f} MB"
        return f"{self.step_name:30s} | {duration:>8s} | {mem_usage:>10s}"


class PerformanceMonitor:
    """Monitor and report on itinerary generation performance"""
    
    def __init__(self):
        self.metrics: dict = {}
        self.total_start_time = time.time()
        process = psutil.Process()
        self.total_start_memory = process.memory_info().rss / 1024 / 1024
    
    def start_step(self, step_name: str) -> PerformanceMetrics:
        """Start timing a step"""
        metric = PerformanceMetrics(step_name)
        self.metrics[step_name] = metric
        return metric
    
    def finish_step(self, step_name: str):
        """Finish timing a step"""
        if step_name in self.metrics:
            self.metrics[step_name].finish()
    
    @property
    def total_duration(self) -> float:
        return time.time() - self.total_start_time
    
    @property
    def total_memory_used(self) -> float:
        """Total memory used from start to peak"""
        process = psutil.Process()
        current_memory = process.memory_info().rss / 1024 / 1024
        return current_memory - self.total_start_memory
    
    def report(self):
        """Display performance report"""
        print("\n" + "="*80)
        print("⏱️  PERFORMANCE METRICS")
        print("="*80)
        print(f"{'Step':<30} | {'Time':>8} | {'Memory Delta':>10}")
        print("-" * 80)
        
        total_duration = 0
        for step_name in sorted(self.metrics.keys()):
            metric = self.metrics[step_name]
            print(metric)
            total_duration += metric.duration_seconds
        
        print("-" * 80)
        print(f"{'TOTAL':<30} | {total_duration:>7.2f}s | {self.total_memory_used:>9.1f} MB")
        print(f"{'Process Memory (Current)':<30} | {'':>8} | {psutil.Process().memory_info().rss / 1024 / 1024:>9.1f} MB")
        print("="*80)


class TravelItineraryOrchestrator:
    """
    Complete orchestrator that generates optimized day-by-day itineraries
    
    Features:
    - Dual optimizer support: OR-Tools (existing) + LangGraph (new)
    - Feature flag to switch between optimizers
    - No breaking changes - backward compatible
    - Dynamic constraint evaluation (LangGraph) vs fixed ratios (OR-Tools)
    """
    
    # ✅ FEATURE FLAG: Set to True to use LangGraph optimizer
    # Set to False to use existing OR-Tools optimizer
    USE_LANGGRAPH = True
    DELTA = 5   # how many extra options to fetch per expansion step
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("GOOGLE_API_KEY not found in .env")
            self.llm = None
            return
        
        print("Initializing Travel Itinerary Orchestrator...")
        
        # Show which optimizer will be used
        optimizer_name = "LangGraph (parallel + dynamic)" if self.USE_LANGGRAPH else "OR-Tools CP-SAT"
        print(f" Optimizer: {optimizer_name}")
        
        if self.USE_LANGGRAPH and not LANGGRAPH_AVAILABLE:
            print("  LangGraph not installed, falling back to OR-Tools")
            self.USE_LANGGRAPH = False
        
        # Initialize LLM for query understanding
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2,
            google_api_key=api_key
        )
        
        # Initialize all service agents
        self.flight_agent = FlightAgent(use_real_api=True)
        self.ground_transport_agent = GroundTransportAgent()
        self.hotel_agent = AccommodationAgent()
        self.restaurant_agent = RestaurantAgent()
        self.activity_agent = ActivityAgent()
        self.trend_analyzer = TrendAnalyzer()
        self.currency_converter = CurrencyConverter()
        self.history_manager = HistoryManager(
            use_mongodb=os.getenv("USE_MONGODB", "false").lower() in ("1", "true", "yes"),
            mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017")
        )
        
        print(f"   💱 Currency converter ready ({len(self.currency_converter.rates)} currencies)")
        print(f"   🚕 Ground transport agent ready")
        
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
    
    def parse_date(self, date_str: str) -> Optional[str]:
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
    
    def get_user_context(self, user_id: str) -> Optional[str]:
        """Retrieve user profile + trip history text for RAG augmentation."""
        context = self.history_manager.get_user_context(user_id)
        if not context:
            return None

        # Trim to safe prompt length and provide summary
        max_chars = 3000
        if len(context) > max_chars:
            context = context[:max_chars] + "\n...(truncated historical context)"

        return context

    def get_airport_code(self, city: str) -> Optional[str]:
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
"Plan a trip from Bangalore to Paris from April 8 to April 15"
→ {{"origin_city": "Bangalore", "destination_city": "Paris", "departure_date": "2026-04-08", "return_date": "2026-04-15", "num_days": 7}}

"I want to visit Tokyo for 5 days starting April 10 from Mumbai"
→ {{"origin_city": "Mumbai", "destination_city": "Tokyo", "departure_date": "2026-04-10", "num_days": 5}}
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
        
    
    def generate_itinerary(self, trip_details: Optional[dict] = None, user_profile: Optional[UserProfile] = None):
        """Generate complete optimized day-by-day itinerary"""
        
        # Initialize performance monitoring
        perf_monitor = PerformanceMonitor()
        
        print("\n" + "="*80)
        print("🌍 GENERATING COMPLETE TRAVEL ITINERARY")
        print("="*80)
        
        # Use provided details or defaults
        if not trip_details:
            trip_details = {}
        
        origin = trip_details.get('origin_city') or 'Mumbai'
        destination = trip_details.get('destination_city') or 'Tokyo'
        # Default to 7 days from today if no date provided
        default_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        departure_date = trip_details.get('departure_date') or default_date
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
        
        perf_monitor.start_step("Trend Analysis")
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
        finally:
            perf_monitor.finish_step("Trend Analysis")
        
        # # [2/6] Search flights AND ground transport
        # print(f"\n{'='*80}")
        # print("[2/6] ✈️🚕 SEARCHING FLIGHTS & GROUND TRANSPORT")
        # print("="*80)
        # print(f"   Route: {origin_code} → {dest_code}")
        # print(f"   Outbound: {departure_date}")
        
        # # Calculate distance to determine if ground transport is viable
        # distance_km = self.ground_transport_agent.calculate_distance(origin, destination)
        
        # # Search for flights
        # print(f"\n   ✈️ Searching flights...")
        # flights = self.flight_agent.search_flights(
        #     origin=origin_code,
        #     destination=dest_code,
        #     departure_date=departure_date,
        #     max_results=10
        # )
        
        # if flights:
        #     print(f"   ✅ Found {len(flights)} flights")
        #     cheapest_flight = min(flights, key=lambda f: self.currency_converter.convert(f.price, f.currency, 'INR'))
        #     cheapest_flight_inr = self.currency_converter.convert(cheapest_flight.price, cheapest_flight.currency, 'INR')
        #     print(f"   💰 Cheapest flight: INR {cheapest_flight_inr:,.0f}")
        # else:
        #     print("   ⚠️ No flights found")
        #     flights = []
        #     cheapest_flight_inr = float('inf')
        
        # # Search for ground transport (if distance is reasonable)
        # ground_transport_options = []
        # if distance_km <= 1000:  # Only search ground transport for <= 1000km
        #     print(f"\n   🚕 Searching ground transport (distance: {distance_km:.0f}km)...")
        #     ground_transport_options = self.ground_transport_agent.search_transport(
        #         origin=origin,
        #         destination=destination,
        #         transport_types=['taxi', 'train', 'bus'],
        #         max_results=6
        #     )
            
        #     if ground_transport_options:
        #         print(f"   ✅ Found {len(ground_transport_options)} ground transport options")
        #         cheapest_ground = min(ground_transport_options, key=lambda t: t.price)
        #         print(f"   💰 Cheapest ground: INR {cheapest_ground.price:,.0f} ({cheapest_ground.type})")
                
        #         # Compare with flight
        #         if flights:
        #             comparison = self.ground_transport_agent.compare_with_flight(
        #                 cheapest_ground, 
        #                 cheapest_flight_inr
        #             )
                    
        #             print(f"\n   📊 COMPARISON:")
        #             print(f"   {'─'*70}")
        #             if comparison['recommendation'] == 'ground_transport':
        #                 print(f"   💡 RECOMMENDED: Ground Transport ({cheapest_ground.type})")
        #                 print(f"   ✅ Save INR {comparison['savings']:,.0f} ({comparison['savings_pct']:.0f}%)")
        #                 print(f"   ⏱️  Extra time: {comparison['time_diff_minutes'] // 60}h {comparison['time_diff_minutes'] % 60}m")
        #                 print(f"   📝 {comparison['reason']}")
        #             else:
        #                 print(f"   💡 RECOMMENDED: Flight")
        #                 print(f"   ⏱️  Save time: {abs(comparison['time_diff_minutes']) // 60}h {abs(comparison['time_diff_minutes']) % 60}m")
        #                 print(f"   📝 {comparison['reason']}")
        #             print(f"   {'─'*70}")
        # else:
        #     print(f"\n   ℹ️  Distance too far ({distance_km:.0f}km) - skipping ground transport")
        
        # # Show top options from each category
        # print(f"\n   📋 TOP OPTIONS:")
        # print(f"   {'─'*70}")
        
        # if flights:
        #     print(f"   ✈️ FLIGHTS:")
        #     for i, f in enumerate(flights[:3], 1):
        #         hrs = f.duration_minutes // 60
        #         mins = f.duration_minutes % 60
        #         original_price = f"{f.currency} {f.price:,.0f}"
        #         inr_price = self.currency_converter.convert(f.price, f.currency, 'INR')
        #         print(f"      {i}. {f.carrier} {f.flight_id}: {original_price} (≈ INR {inr_price:,.0f}) ({hrs}h {mins}m)")
        
        # if ground_transport_options:
        #     print(f"\n   🚕 GROUND TRANSPORT:")
        #     for i, t in enumerate(ground_transport_options[:3], 1):
        #         hrs = t.duration_minutes // 60
        #         mins = t.duration_minutes % 60
        #         print(f"      {i}. {t.type.title()} ({t.provider}): INR {t.price:,.0f} ({hrs}h {mins}m)")
        

        # # Pass ALL options to LangGraph — it will pick the cheapest combination
        # # that fits within the total budget. No pre-selection here.
        # # selected_transport = flights + ground_transport_options

        # # if not selected_transport:
        # #     print("\n   ⚠️ No transport options found (will use mock data)")
        # # else:
        # #     n_flights = len(flights)
        # #     n_ground  = len(ground_transport_options)
        # #     print(f"\n   ✅ Passing ALL {len(selected_transport)} transport options "
        # #           f"to LangGraph for dynamic budget-aware selection")
        # #     if n_flights:
        # #         cheapest_f = min(
        # #             self.currency_converter.convert(f.price, f.currency, 'INR')
        # #             for f in flights
        # #         )
        # #         print(f"      ✈️  {n_flights} flights  — cheapest INR {cheapest_f:,.0f}")
        # #     if n_ground:
        # #         cheapest_g = min(t.price for t in ground_transport_options)
        # #         print(f"      🚕  {n_ground} ground   — cheapest INR {cheapest_g:,.0f}")
        # #     print(f"      💡 LangGraph will choose based on total budget INR {budget:,.0f}")
        # # ── Outbound: all options together ────────────────────────────────
        # selected_transport = flights + ground_transport_options

        # # ── Return: search reverse route ──────────────────────────────────
        # dep_date_obj  = datetime.strptime(departure_date, '%Y-%m-%d')
        # return_date   = (dep_date_obj + timedelta(days=num_days - 1)).strftime('%Y-%m-%d')

        # print(f"\n   🔄 Searching RETURN transport ({dest_code} → {origin_code}) "
        #       f"on {return_date}...")

        # return_flights = self.flight_agent.search_flights(
        #     origin=dest_code,
        #     destination=origin_code,
        #     departure_date=return_date,
        #     max_results=10
        # )

        # return_ground = []
        # if distance_km <= 1000:
        #     return_ground = self.ground_transport_agent.search_transport(
        #         origin=destination,
        #         destination=origin,
        #         transport_types=['taxi', 'train', 'bus'],
        #         max_results=6
        #     )

        # # Convert return flight prices to INR
        # for f in return_flights:
        #     f.price    = self.currency_converter.convert(f.price, f.currency, 'INR')
        #     f.currency = 'INR'
        #     f.is_return = True   # flag for display + day placement

        # for t in return_ground:
        #     t.is_return = True

        # return_transport_options = return_flights + return_ground

        # if return_transport_options:
        #     cheapest_ret = min(return_transport_options,
        #                        key=lambda t: getattr(t, 'price', 0))
        #     print(f"   ✅ Found {len(return_transport_options)} return options — "
        #           f"cheapest INR {cheapest_ret.price:,.0f}")
        # else:
        #     print("   ⚠️ No return options found — will use mock")

        # # Store on trip_details so other methods can access
        # trip_details['_return_transport_options'] = return_transport_options

        # if not selected_transport:
        #     print("\n   ⚠️ No outbound transport found (will use mock data)")
        # else:
        #     cheapest_out = min(
        #         self.currency_converter.convert(
        #             getattr(t, 'price', 0), getattr(t, 'currency', 'INR'), 'INR'
        #         )
        #         for t in selected_transport
        #     )
        #     cheapest_ret_cost = (
        #         min(getattr(t, 'price', 0) for t in return_transport_options)
        #         if return_transport_options else 0
        #     )
        #     print(f"\n   💡 LangGraph will optimise outbound + return + stay within "
        #           f"total budget INR {budget:,.0f}")
        #     print(f"      Cheapest outbound: INR {cheapest_out:,.0f}")
        #     print(f"      Cheapest return:   INR {cheapest_ret_cost:,.0f}")
        #     print(f"      Remaining for hotel/food/activities: "
        #           f"INR {budget - cheapest_out - cheapest_ret_cost:,.0f}")

        
        
        # # [3/6] Search accommodations
        # print(f"\n{'='*80}")
        # print("[3/6] 🏨 SEARCHING ACCOMMODATIONS")
        # print("="*80)
        # print(f"   Location: {destination}")
        # print(f"   Check-in: {departure_date}, Check-out: {return_date}")
        
        # hotels = self.hotel_agent.search_accommodations(
        #     destination=destination,
        #     check_in=departure_date,
        #     check_out=return_date,
        #     max_results=10
        # )
        
        # if hotels:
        #     print(f"✅ Found {len(hotels)} accommodations")
        #     for i, h in enumerate(hotels[:3], 1):
        #         original_price = f"{h.currency} {h.price_per_night:,.0f}"
        #         inr_price = self.currency_converter.convert(h.price_per_night, h.currency, 'INR')
        #         print(f"   {i}. {h.name}: {original_price}/night (≈ INR {inr_price:,.0f}) [{h.type}]")
        # else:
        #     print("   ⚠️ No accommodations found (will use mock data)")
        #     hotels = []
        
        # # [4/6] Search restaurants
        # print(f"\n{'='*80}")
        # print("[4/6] 🍽️  SEARCHING RESTAURANTS")
        # print("="*80)
        # print(f"   Location: {destination}")
        # if dietary:
        #     print(f"   Dietary: {', '.join(dietary)}")
        
        # restaurants = self.restaurant_agent.search_restaurants(
        #     location=destination,
        #     dietary_restrictions=dietary if dietary else None,
        #     max_results=20
        # )
        
        # if restaurants:
        #     print(f"✅ Found {len(restaurants)} restaurants")
        #     restaurants = self.restaurant_agent.rank_restaurants(restaurants)
        #     for i, r in enumerate(restaurants[:3], 1):
        #         print(f"   {i}. {r.name}: {r.cuisine_type}")
        # else:
        #     print("   ⚠️ No restaurants found (will use mock data)")
        #     restaurants = []
        
        # # [5/6] Search activities
        # print(f"\n{'='*80}")
        # print("[5/6] 🎭 SEARCHING ACTIVITIES")
        # print("="*80)
        # print(f"   Location: {destination}")
        # print(f"   Interests: {', '.join(interests)}")
        
        # activities = self.activity_agent.search_activities(
        #     location=destination,
        #     interests=interests if interests else None,
        #     max_results=25
        # )
        
        # if activities:
        #     print(f"✅ Found {len(activities)} activities")
        #     for i, a in enumerate(activities[:3], 1):
        #         print(f"   {i}. {a.name}: {a.description[:50]}...")
        # else:
        #     print("   ⚠️ No activities found (will use mock data)")
        #     activities = []
        
        # # [6/6] Optimize itinerary
        # print(f"\n{'='*80}")
        # print("[6/6] 🧮 OPTIMIZING ITINERARY")
        # print("="*80)
        
        # # Convert all prices to base currency (INR) for optimization
        # print("   💱 Converting all prices to INR...")
        # base_currency = 'INR'
        
        # # Convert transport options (only the selected type)
        # transport_converted = []
        # for transport in selected_transport:
        #     if hasattr(transport, 'price') and hasattr(transport, 'currency'):
        #         # Check if it's a flight or ground transport
        #         if hasattr(transport, 'carrier'):  # It's a flight
        #             converted_price = self.currency_converter.convert(
        #                 transport.price, 
        #                 transport.currency, 
        #                 base_currency
        #             )
        #             transport.price = converted_price
        #             transport.currency = base_currency
        #         else:  # It's ground transport (already in INR)
        #             pass  # Already in INR
                
        #         transport_converted.append(transport)
        
        # print(f"   ✅ Using {len(transport_converted)} {transport_converted[0].item_type if transport_converted else 'transport'} options")
        # # Convert hotels
        # hotels_converted = []
        # for hotel in hotels:
        #     converted_price = self.currency_converter.convert(
        #         hotel.price_per_night,
        #         hotel.currency,
        #         base_currency
        #     )
        #     hotel.price_per_night = converted_price
        #     hotel.currency = base_currency
        #     hotels_converted.append(hotel)
        
        # # Convert restaurants
        # restaurants_converted = []
        # for restaurant in restaurants:
        #     converted_price = self.currency_converter.convert(
        #         restaurant.average_meal_cost,
        #         restaurant.currency,
        #         base_currency
        #     )
        #     restaurant.average_meal_cost = converted_price
        #     restaurant.currency = base_currency
        #     restaurants_converted.append(restaurant)
        
        # # Convert activities
        # activities_converted = []
        # for activity in activities:
        #     if hasattr(activity, 'cost') and hasattr(activity, 'currency'):
        #         converted_price = self.currency_converter.convert(
        #             activity.price,
        #             activity.currency,
        #             base_currency
        #         )
        #         activity.price = converted_price
        #         activity.currency = base_currency
        #     activities_converted.append(activity)
        
        # print(f"   ✅ All prices converted to {base_currency}")
        
        # # ======================================================================
        # # FEATURE FLAG: Choose optimizer (OR-Tools vs LangGraph)
        # # ======================================================================
        
        # if self.USE_LANGGRAPH and LANGGRAPH_AVAILABLE:
        #     # NEW: Use LangGraph optimizer with dynamic constraints
        #     optimized = self._optimize_with_langgraph(
        #         transport_converted, hotels_converted, restaurants_converted,
        #         activities_converted, num_days, budget, user_profile, trip_details
        #     )
        # else:
        #     # EXISTING: Use OR-Tools optimizer with hardcoded ratios
        #     optimized = self._optimize_with_ortools(
        #         transport_converted, hotels_converted, restaurants_converted,
        #         activities_converted, num_days, user_profile
        #     )

        # In generate_itinerary(), replace steps [2/6]..[6/6] with:

        print(f"\n{'='*80}")
        print("[2-6/6] 🔍 SEARCH + OPTIMIZE (Comparing Two Expansion Strategies)")
        print("="*80)

        # ── STRATEGY 1: One-by-one expansion ───────────────────────────────────
        print(f"\n📊 STRATEGY 1: One-by-One Expansion (cycle through agents)")
        print("-" * 80)
        perf_monitor.start_step("OneByOne Expansion")
        result_onebyones = self._fetch_with_expansion(
            origin_code=origin_code,
            dest_code=dest_code,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            interests=interests,
            dietary=dietary,
            budget=budget,
            num_days=num_days,
            user_profile=user_profile,
            trip_details=trip_details,
            initial_counts={"flight": 10, "hotel": 10, "restaurant": 20, "activity": 25},
            max_rounds=3,
            perf_monitor=None,  # Don't track sub-steps separately
        )
        perf_monitor.finish_step("OneByOne Expansion")

        # ── STRATEGY 2: Parallel expansion ─────────────────────────────────────
        print(f"\n📊 STRATEGY 2: Parallel Expansion (expand all agents together)")
        print("-" * 80)
        perf_monitor.start_step("Parallel Expansion")
        result_parallel = self._fetch_with_parallel_expansion(
            origin_code=origin_code,
            dest_code=dest_code,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            interests=interests,
            dietary=dietary,
            budget=budget,
            num_days=num_days,
            user_profile=user_profile,
            trip_details=trip_details,
            initial_counts={"flight": 10, "hotel": 10, "restaurant": 20, "activity": 25},
            max_rounds=3,
            perf_monitor=None,
        )
        perf_monitor.finish_step("Parallel Expansion")

        # ── COMPARISON ─────────────────────────────────────────────────────────
        print(f"\n{'='*80}")
        print("📊 STRATEGY COMPARISON")
        print("="*80)
        
        strategy_1_valid = (
            result_onebyones is not None 
            and "error" not in result_onebyones 
            and result_onebyones.get("total_cost", float("inf")) <= budget
        )
        strategy_2_valid = (
            result_parallel is not None 
            and "error" not in result_parallel 
            and result_parallel.get("total_cost", float("inf")) <= budget
        )
        
        cost_1 = result_onebyones.get('total_cost', float('inf')) if result_onebyones else float('inf')
        cost_2 = result_parallel.get('total_cost', float('inf')) if result_parallel else float('inf')
        
        print(f"{'Strategy':<25} | {'Valid':<8} | {'Cost (INR)':<15} | {'vs Budget':<12}")
        print("-" * 80)
        
        status_1 = "✅ Yes" if strategy_1_valid else "❌ No"
        margin_1 = f"{((cost_1 / budget - 1) * 100):+.1f}%" if cost_1 < float('inf') else "N/A"
        print(f"{'One-by-One':<25} | {status_1:<8} | {cost_1:>13,.0f} | {margin_1:>12}")
        
        status_2 = "✅ Yes" if strategy_2_valid else "❌ No"
        margin_2 = f"{((cost_2 / budget - 1) * 100):+.1f}%" if cost_2 < float('inf') else "N/A"
        print(f"{'Parallel':<25} | {status_2:<8} | {cost_2:>13,.0f} | {margin_2:>12}")
        
        print("-" * 80)
        
        # ── STRATEGY 3: Sequential generation ──────────────────────────────────
        print(f"\n📊 STRATEGY 3: Sequential Generation (one-by-one evaluation)")
        print("-" * 80)
        perf_monitor.start_step("Sequential Generation")
        result_sequential = self._fetch_with_sequential_generation(
            origin_code=origin_code,
            dest_code=dest_code,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            interests=interests,
            dietary=dietary,
            budget=budget,
            num_days=num_days,
            user_profile=user_profile,
            trip_details=trip_details,
            initial_step_size=1,  # Unused (method calculates min unique required)
            perf_monitor=None,
        )
        perf_monitor.finish_step("Sequential Generation")

        # ── COMPARISON (3-way) ─────────────────────────────────────────────────
        print(f"\n{'='*80}")
        print("📊 THREE-STRATEGY COMPARISON")
        print("="*80)
        
        strategy_1_valid = (
            result_onebyones is not None 
            and "error" not in result_onebyones 
            and result_onebyones.get("total_cost", float("inf")) <= budget
        )
        strategy_2_valid = (
            result_parallel is not None 
            and "error" not in result_parallel 
            and result_parallel.get("total_cost", float("inf")) <= budget
        )
        strategy_3_valid = (
            result_sequential is not None 
            and "error" not in result_sequential 
            and result_sequential.get("total_cost", float("inf")) <= budget
        )
        
        cost_1 = result_onebyones.get('total_cost', float('inf')) if result_onebyones else float('inf')
        cost_2 = result_parallel.get('total_cost', float('inf')) if result_parallel else float('inf')
        cost_3 = result_sequential.get('total_cost', float('inf')) if result_sequential else float('inf')
        
        print(f"{'Strategy':<25} | {'Valid':<8} | {'Cost (INR)':<15} | {'vs Budget':<12}")
        print("-" * 80)
        
        status_1 = "✅ Yes" if strategy_1_valid else "❌ No"
        margin_1 = f"{((cost_1 / budget - 1) * 100):+.1f}%" if cost_1 < float('inf') else "N/A"
        print(f"{'One-by-One Agents':<25} | {status_1:<8} | {cost_1:>13,.0f} | {margin_1:>12}")
        
        status_2 = "✅ Yes" if strategy_2_valid else "❌ No"
        margin_2 = f"{((cost_2 / budget - 1) * 100):+.1f}%" if cost_2 < float('inf') else "N/A"
        print(f"{'Parallel Expansion':<25} | {status_2:<8} | {cost_2:>13,.0f} | {margin_2:>12}")
        
        status_3 = "✅ Yes" if strategy_3_valid else "❌ No"
        margin_3 = f"{((cost_3 / budget - 1) * 100):+.1f}%" if cost_3 < float('inf') else "N/A"
        print(f"{'Sequential (Memory-Opt)':<25} | {status_3:<8} | {cost_3:>13,.0f} | {margin_3:>12}")
        
        print("-" * 80)
        
        # Find best valid result
        valid_strategies = {
            'One-by-One': (result_onebyones, cost_1) if strategy_1_valid else None,
            'Parallel': (result_parallel, cost_2) if strategy_2_valid else None,
            'Sequential': (result_sequential, cost_3) if strategy_3_valid else None,
        }
        valid_strategies = {k: v for k, v in valid_strategies.items() if v is not None}
        
        if valid_strategies:
            # Get cheapest valid strategy
            winner_name = min(valid_strategies.keys(), key=lambda k: valid_strategies[k][1])
            optimized, winner_cost = valid_strategies[winner_name]
            
            if len(valid_strategies) > 1:
                # Show savings vs other strategies
                other_costs = [v[1] for k, v in valid_strategies.items() if k != winner_name]
                avg_other = sum(other_costs) / len(other_costs)
                savings = avg_other - winner_cost
                print(f"🏆 WINNER: {winner_name} strategy (saves INR {savings:,.0f} on average)")
            else:
                print(f"🏆 WINNER: {winner_name} strategy (feasible)")
        else:
            # All strategies over budget - use best effort (closest to budget)
            costs_dict = {
                'One-by-One': cost_1,
                'Parallel': cost_2,
                'Sequential': cost_3,
            }
            best_effort_name = min(costs_dict.keys(), key=lambda k: costs_dict[k])
            if best_effort_name == 'One-by-One':
                optimized = result_onebyones
            elif best_effort_name == 'Parallel':
                optimized = result_parallel
            else:
                optimized = result_sequential
            
            overage = costs_dict[best_effort_name] - budget
            print(f"⚠️  All strategies over budget. Best effort: {best_effort_name} (+INR {overage:,.0f})")

        print("=" * 80)

        if optimized is None or "error" in optimized:
            print("❌ Could not generate itinerary.")
            perf_monitor.report()
            return
        
        if 'error' in optimized:
            print(f"   ❌ Optimization error: {optimized['error']}")
            perf_monitor.report()
            return
        
        print(f"✅ Optimization complete!")
        print(f"   Total cost: {optimized.get('currency', 'INR')} {optimized.get('total_cost', 0):,.2f}")
        print(f"   Budget remaining: INR {budget - optimized.get('total_cost', 0):,.2f}")
        
        # Add return journey to last day
        # result = self.add_return_journey(optimized, trip_details)
        result = optimized  # LangGraph already includes return journey in optimization
        
        # Display day-by-day itinerary
        perf_monitor.start_step("Display Itinerary")
        self.display_itinerary(result, trip_details)
        perf_monitor.finish_step("Display Itinerary")
        
        # Show performance metrics
        perf_monitor.report()

        return optimized
    
    # orchestrator.py — add this method to TravelItineraryOrchestrator

    def _fetch_with_expansion(
        self,
        origin_code: str,
        dest_code: str,
        destination: str,
        departure_date: str,
        return_date: str,
        interests: Optional[list],
        dietary: Optional[list],
        budget: float,
        num_days: int,
        user_profile,
        trip_details: dict,
        initial_counts: Optional[dict] = None,
        max_rounds: int = 3,
        perf_monitor: Optional['PerformanceMonitor'] = None,
    ) -> Optional[dict]:
        """
        Sub-method 1 from the notes:
        1. Fetch P1..P4 options from all agents (initial_counts per agent).
        2. Try to optimise — if a feasible plan is found, return it.
        3. If not, expand ONE agent's search space by δ, recheck.
        4. Cycle through all agents before declaring a full round done.
        5. If still nothing after max_rounds, return None.

        initial_counts: {"flight": P1, "hotel": P2, "restaurant": P3, "activity": P4, ...}
        """
         
    # ── PRE-CHECK: estimate minimum possible cost ──────────────────────────
        def _estimate_min_cost(destination, departure_date, return_date, num_days):
            """Quick sanity check before expensive expansion loop."""
            # Rough minimums (INR) — adjust to your data
            MIN_TRANSPORT = 400        # cheapest bus/train one-way
            MIN_HOTEL_PER_NIGHT = 800  # budget guesthouse
            MIN_FOOD_PER_DAY = 300     # two basic meals
            MIN_ACTIVITY_PER_DAY = 0   # free attractions exist
            
            min_total = (
                MIN_TRANSPORT * 2                          # outbound + return
                + MIN_HOTEL_PER_NIGHT * (num_days - 1)    # nights
                + MIN_FOOD_PER_DAY * num_days
                + MIN_ACTIVITY_PER_DAY * num_days
            )
            return min_total

        min_possible = _estimate_min_cost(destination, departure_date, return_date, num_days)
        if min_possible > budget:
            print(f"   ❌ Budget INR {budget:,.0f} is below estimated minimum "
                f"INR {min_possible:,.0f} for this trip. "
                f"Please increase your budget.")
            return {"error": "budget_too_low", "min_required": min_possible}
        
        if initial_counts is None:
            initial_counts = {"flight": 10, "hotel": 10, "restaurant": 20, "activity": 25, "ground_transport": 6}
        else:
            # Ensure all required keys exist (add defaults if missing)
            defaults = {"flight": 10, "hotel": 10, "restaurant": 20, "activity": 25, "ground_transport": 6}
            for key, value in defaults.items():
                if key not in initial_counts:
                    initial_counts[key] = value

        # ── agent order defines the expansion sequence ────────────────────
        # NOW INCLUDES ground_transport!
        agent_order = ["flight", "ground_transport", "hotel", "restaurant", "activity"]

        # current max-results per agent (grows by DELTA on each expansion)
        limits = dict(initial_counts)

        # ✅ Initialize cache for reuse across rounds (FIX 4: avoid re-fetching all agents)
        cached = {}

        # ── ROUND 0: Try with initial counts BEFORE expanding ──────────────
        print(f"\n   🔄 Round 0 (initial search): trying with limits={limits}")
        
        flights = self.flight_agent.search_flights(
            origin=origin_code,
            destination=dest_code,
            departure_date=departure_date,
            max_results=limits["flight"],
        )

        hotels = self.hotel_agent.search_accommodations(
            destination=destination,
            check_in=departure_date,
            check_out=return_date,
            max_results=limits["hotel"],
        )

        restaurants = self.restaurant_agent.search_restaurants(
            location=destination,
            dietary_restrictions=dietary or None,
            max_results=limits["restaurant"],
        )

        activities = self.activity_agent.search_activities(
            location=destination,
            interests=interests or None,
            max_results=limits["activity"],
        )

        # ── Currency conversion ────────────────────────────────────────────
        base = "INR"
        for f in flights:
            f.price = self.currency_converter.convert(f.price, f.currency, base)
            f.currency = base
        for h in hotels:
            h.price_per_night = self.currency_converter.convert(h.price_per_night, h.currency, base)
            h.currency = base
        for r in restaurants:
            r.average_meal_cost = self.currency_converter.convert(r.average_meal_cost, r.currency, base)
            r.currency = base
        for a in activities:
            if hasattr(a, "price"):
                a.price = self.currency_converter.convert(a.price, a.currency, base)
                a.currency = base

        # Ground transport
        distance_km = self.ground_transport_agent.calculate_distance(
            trip_details.get("origin_city", ""), destination)
        ground = []
        if distance_km <= 1000:
            ground = self.ground_transport_agent.search_transport(
                origin=trip_details.get("origin_city", ""),
                destination=destination,
                transport_types=["taxi", "train", "bus"],
                max_results=limits["ground_transport"],
            )
        # transport_all = flights + ground
        transport_all = sorted(
            flights + ground,
            key=lambda t: getattr(t, 'price', float('inf'))
        )

        # ✅ Cache Round 0 results for reuse in expansion rounds
        cached["flight"] = flights
        cached["hotel"] = hotels
        cached["restaurant"] = restaurants
        cached["activity"] = activities
        cached["ground_transport"] = ground

        # ── Try to optimize with initial counts ────────────────────────────
        result = self._optimize_with_langgraph(
            transport_all, hotels, restaurants, activities,
            num_days, budget, user_profile, trip_details,
        ) if self.USE_LANGGRAPH and LANGGRAPH_AVAILABLE else \
            self._optimize_with_ortools(
                transport_all, hotels, restaurants, activities,
                num_days, user_profile,
            )

        is_feasible = (
            "error" not in result
            and result.get("total_cost", float("inf")) <= budget
        )

        if is_feasible:
            print(f"   ✅ Round 0: feasible plan found with initial search!")
            return result

        print(f"   ❌ Round 0 not feasible (cost={result.get('total_cost', '?'):.0f} > budget={budget:.0f})")
        print(f"   🔄 Starting expansion rounds...\n")

        # ── ROUNDS 1+: Expand agent by agent ───────────────────────────────
        # ✅ FIX 4: Use cache, only re-fetch the expanding agent
        best_plan_overall = result  # Track best plan even if not feasible
        best_cost_overall = result.get('total_cost', float('inf'))
        
        if perf_monitor:
            perf_monitor.start_step("Expansion Rounds")
        
        for round_num in range(max_rounds):
            for agent_idx, expanding_agent in enumerate(agent_order):

                print(f"   🔄 Round {round_num+1}, expanding '{expanding_agent}' "
                    f"(limits={limits})")

                # ── 1. CACHE-AWARE FETCH: Only re-fetch the expanding agent ────
                # All other agents use cached results from previous round
                
                # Re-fetch flight (might have more options now)
                if expanding_agent == "flight":
                    flights = self.flight_agent.search_flights(
                        origin=origin_code,
                        destination=dest_code,
                        departure_date=departure_date,
                        max_results=limits["flight"],
                    )
                    base = "INR"
                    for f in flights:
                        f.price = self.currency_converter.convert(f.price, f.currency, base)
                        f.currency = base
                    cached["flight"] = flights
                else:
                    flights = cached.get("flight", [])

                # Re-fetch hotel if expanding
                if expanding_agent == "hotel":
                    hotels = self.hotel_agent.search_accommodations(
                        destination=destination,
                        check_in=departure_date,
                        check_out=return_date,
                        max_results=limits["hotel"],
                    )
                    base = "INR"
                    for h in hotels:
                        h.price_per_night = self.currency_converter.convert(
                            h.price_per_night, h.currency, base)
                        h.currency = base
                    cached["hotel"] = hotels
                else:
                    hotels = cached.get("hotel", [])

                # Re-fetch restaurant if expanding
                if expanding_agent == "restaurant":
                    restaurants = self.restaurant_agent.search_restaurants(
                        location=destination,
                        dietary_restrictions=dietary or None,
                        max_results=limits["restaurant"],
                    )
                    base = "INR"
                    for r in restaurants:
                        r.average_meal_cost = self.currency_converter.convert(
                            r.average_meal_cost, r.currency, base)
                        r.currency = base
                    cached["restaurant"] = restaurants
                else:
                    restaurants = cached.get("restaurant", [])

                # Re-fetch activity if expanding
                if expanding_agent == "activity":
                    activities = self.activity_agent.search_activities(
                        location=destination,
                        interests=interests or None,
                        max_results=limits["activity"],
                    )
                    base = "INR"
                    for a in activities:
                        if hasattr(a, "price"):
                            a.price = self.currency_converter.convert(
                                a.price, a.currency, base)
                            a.currency = base
                    cached["activity"] = activities
                else:
                    activities = cached.get("activity", [])

                # Re-fetch ground_transport if expanding
                if expanding_agent == "ground_transport":
                    distance_km = self.ground_transport_agent.calculate_distance(
                        trip_details.get("origin_city", ""), destination)
                    ground = []
                    if distance_km <= 1000:
                        ground = self.ground_transport_agent.search_transport(
                            origin=trip_details.get("origin_city", ""),
                            destination=destination,
                            transport_types=["taxi", "train", "bus"],
                            max_results=limits["ground_transport"],
                        )
                    cached["ground_transport"] = ground
                else:
                    ground = cached.get("ground_transport", [])

                transport_all = sorted(
                    flights + ground,
                    key=lambda t: getattr(t, 'price', float('inf'))
                )

                # ── 2. Try to optimise with cached + freshly-fetched options ────
                result = self._optimize_with_langgraph(
                    transport_all, hotels, restaurants, activities,
                    num_days, budget, user_profile, trip_details,
                ) if self.USE_LANGGRAPH and LANGGRAPH_AVAILABLE else \
                    self._optimize_with_ortools(
                        transport_all, hotels, restaurants, activities,
                        num_days, user_profile,
                    )

                # ── 3. Feasibility check ───────────────────────────────────
                is_feasible = (
                    "error" not in result
                    and result.get("total_cost", float("inf")) <= budget
                )
                
                current_cost = result.get('total_cost', float('inf'))
                
                # Track best plan (even if not feasible)
                if current_cost < best_cost_overall:
                    best_plan_overall = result
                    best_cost_overall = current_cost
                    print(f"   💰 New best cost: {current_cost:.0f} INR")

                if is_feasible:
                    print(f"   ✅ Sub-method 1: feasible plan found "
                        f"(round {round_num+1}, agent '{expanding_agent}')")
                    if perf_monitor:
                        perf_monitor.finish_step("Expansion Rounds")
                    return result

                print(f"   ⚠️  Cost: {current_cost:.0f} > Budget: {budget:.0f}, "
                    f"expanding next agent…")

                # ── 4. Expand the current agent for next iteration ──
                limits[expanding_agent] += self.DELTA

            # after cycling all agents, bump every limit by δ before next round
            print(f"   ⚠️  Round {round_num+1} done — increasing all limits by {self.DELTA}")
            for key in limits:
                limits[key] += self.DELTA

        print("   ❌ Sub-method 1: no feasible plan after "
            f"{max_rounds} rounds")
        print(f"   💡 Best effort cost: INR {best_cost_overall:.0f} (budget: INR {budget:.0f})")
        print(f"   📊 Shortfall: INR {best_cost_overall - budget:.0f}")
        
        if perf_monitor:
            perf_monitor.finish_step("Expansion Rounds")
        
        # Return best effort if close enough (within 20% of budget)
        if best_cost_overall <= budget * 1.2:
            print(f"   ✓ Returning best effort (only {((best_cost_overall / budget - 1) * 100):.0f}% over)")
            return best_plan_overall
        
        # Budget is impossible - suggest realistic budget
        print(f"   💰 Suggested minimum budget: INR {best_cost_overall:.0f}")
        return None   # caller decides what to do

    def _fetch_with_parallel_expansion(
        self,
        origin_code: str,
        dest_code: str,
        destination: str,
        departure_date: str,
        return_date: str,
        interests: Optional[list],
        dietary: Optional[list],
        budget: float,
        num_days: int,
        user_profile,
        trip_details: dict,
        initial_counts: Optional[dict] = None,
        max_rounds: int = 3,
        perf_monitor: Optional['PerformanceMonitor'] = None,
    ) -> Optional[dict]:
        """
        Alternative strategy: Expand ALL agents together each round (not one-by-one).
        
        Strategy comparison:
        - One-by-one: Cycle through each agent, increasing one at a time
          (more granular, but more optimization calls)
        - Parallel: Increase all agents together each round
          (fewer optimization calls, potentially faster)
          
        Rounds structure:
        1. Round 0: Try with initial counts
        2. Rounds 1-N: Increase ALL agent limits by DELTA, then try optimization
        3. If feasible, return; else continue to next round
        """
        
        # ── PRE-CHECK: estimate minimum possible cost ──────────────────────────
        def _estimate_min_cost(destination, departure_date, return_date, num_days):
            """Quick sanity check before expensive expansion loop."""
            
            # Rough estimates:
            MIN_FLIGHT_COST = 3000   # INR
            MIN_HOTEL_PER_NIGHT = 800     # INR
            MIN_RESTAURANT_PER_MEAL = 300  # INR
            MIN_ACTIVITY_PER_DAY = 500    # INR
            
            min_total = (
                MIN_FLIGHT_COST * 2  # outbound + return
                + MIN_HOTEL_PER_NIGHT * num_days
                + MIN_RESTAURANT_PER_MEAL * 2 * num_days  # 2 meals per day
                + MIN_ACTIVITY_PER_DAY * num_days
            )
            return min_total

        min_possible = _estimate_min_cost(destination, departure_date, return_date, num_days)
        if min_possible > budget:
            print(f"   ❌ Budget INR {budget:,.0f} is below estimated minimum "
                f"INR {min_possible:,.0f} for this trip. "
                f"Please increase your budget.")
            return {"error": "budget_too_low", "min_required": min_possible}
        
        if initial_counts is None:
            initial_counts = {"flight": 10, "hotel": 10, "restaurant": 20, "activity": 25, "ground_transport": 6}
        else:
            # Ensure all required keys exist (add defaults if missing)
            defaults = {"flight": 10, "hotel": 10, "restaurant": 20, "activity": 25, "ground_transport": 6}
            for key, value in defaults.items():
                if key not in initial_counts:
                    initial_counts[key] = value

        # ── agent order ────────────────────────────────────────────────────────
        agent_order = ["flight", "ground_transport", "hotel", "restaurant", "activity"]

        # current max-results per agent (ALL grow together each round)
        limits = dict(initial_counts)

        # ✅ Cache for reuse across rounds
        cached = {}

        # ── ROUND 0: Try with initial counts ────────────────────────────────
        print(f"\n   🔄 Round 0 (parallel - initial): limits={limits}")
        
        flights = self.flight_agent.search_flights(
            origin=origin_code,
            destination=dest_code,
            departure_date=departure_date,
            max_results=limits["flight"],
        )

        hotels = self.hotel_agent.search_accommodations(
            destination=destination,
            check_in=departure_date,
            check_out=return_date,
            max_results=limits["hotel"],
        )

        restaurants = self.restaurant_agent.search_restaurants(
            location=destination,
            dietary_restrictions=dietary or None,
            max_results=limits["restaurant"],
        )

        activities = self.activity_agent.search_activities(
            location=destination,
            interests=interests or None,
            max_results=limits["activity"],
        )

        # ── Currency conversion ────────────────────────────────────────────────
        base = "INR"
        for f in flights:
            f.price = self.currency_converter.convert(f.price, f.currency, base)
            f.currency = base
        for h in hotels:
            h.price_per_night = self.currency_converter.convert(h.price_per_night, h.currency, base)
            h.currency = base
        for r in restaurants:
            r.average_meal_cost = self.currency_converter.convert(r.average_meal_cost, r.currency, base)
            r.currency = base
        for a in activities:
            if hasattr(a, "price"):
                a.price = self.currency_converter.convert(a.price, a.currency, base)
                a.currency = base

        # Ground transport
        distance_km = self.ground_transport_agent.calculate_distance(
            trip_details.get("origin_city", ""), destination)
        ground = []
        if distance_km <= 1000:
            ground = self.ground_transport_agent.search_transport(
                origin=trip_details.get("origin_city", ""),
                destination=destination,
                transport_types=["taxi", "train", "bus"],
                max_results=limits["ground_transport"],
            )
        
        transport_all = sorted(
            flights + ground,
            key=lambda t: getattr(t, 'price', float('inf'))
        )

        # ✅ Cache Round 0 results
        cached["flight"] = flights
        cached["hotel"] = hotels
        cached["restaurant"] = restaurants
        cached["activity"] = activities
        cached["ground_transport"] = ground

        # ── Try to optimize with initial counts
        result = self._optimize_with_langgraph(
            transport_all, hotels, restaurants, activities,
            num_days, budget, user_profile, trip_details,
        ) if self.USE_LANGGRAPH and LANGGRAPH_AVAILABLE else \
            self._optimize_with_ortools(
                transport_all, hotels, restaurants, activities,
                num_days, user_profile,
            )

        is_feasible = (
            "error" not in result
            and result.get("total_cost", float("inf")) <= budget
        )

        if is_feasible:
            print(f"   ✅ Parallel expansion: feasible plan found in Round 0")
            return result

        print(f"   ❌ Round 0 not feasible (cost={result.get('total_cost', '?'):.0f} > budget={budget:.0f})")
        print(f"   🔄 Starting parallel expansion rounds...\n")

        # ── ROUNDS 1+: Expand ALL agents together ───────────────────────────────
        best_plan_overall = result
        best_cost_overall = result.get('total_cost', float('inf'))
        
        if perf_monitor:
            perf_monitor.start_step("Parallel Expansion Rounds")
        
        for round_num in range(max_rounds):
            # ── INCREASE ALL LIMITS AT ONCE ────────────────────────────────────
            print(f"   🔄 Round {round_num+1} (parallel): increasing all agents by {self.DELTA}")
            for agent in agent_order:
                limits[agent] += self.DELTA
            
            print(f"   📊 New limits: {limits}")
            
            # ── RE-FETCH ALL AGENTS (not cached, all fresh) ───────────────────
            flights = self.flight_agent.search_flights(
                origin=origin_code,
                destination=dest_code,
                departure_date=departure_date,
                max_results=limits["flight"],
            )
            base = "INR"
            for f in flights:
                f.price = self.currency_converter.convert(f.price, f.currency, base)
                f.currency = base

            hotels = self.hotel_agent.search_accommodations(
                destination=destination,
                check_in=departure_date,
                check_out=return_date,
                max_results=limits["hotel"],
            )
            for h in hotels:
                h.price_per_night = self.currency_converter.convert(h.price_per_night, h.currency, base)
                h.currency = base

            restaurants = self.restaurant_agent.search_restaurants(
                location=destination,
                dietary_restrictions=dietary or None,
                max_results=limits["restaurant"],
            )
            for r in restaurants:
                r.average_meal_cost = self.currency_converter.convert(r.average_meal_cost, r.currency, base)
                r.currency = base

            activities = self.activity_agent.search_activities(
                location=destination,
                interests=interests or None,
                max_results=limits["activity"],
            )
            for a in activities:
                if hasattr(a, "price"):
                    a.price = self.currency_converter.convert(a.price, a.currency, base)
                    a.currency = base

            distance_km = self.ground_transport_agent.calculate_distance(
                trip_details.get("origin_city", ""), destination)
            ground = []
            if distance_km <= 1000:
                ground = self.ground_transport_agent.search_transport(
                    origin=trip_details.get("origin_city", ""),
                    destination=destination,
                    transport_types=["taxi", "train", "bus"],
                    max_results=limits["ground_transport"],
                )

            transport_all = sorted(
                flights + ground,
                key=lambda t: getattr(t, 'price', float('inf'))
            )

            # ── TRY TO OPTIMIZE ────────────────────────────────────────────────
            result = self._optimize_with_langgraph(
                transport_all, hotels, restaurants, activities,
                num_days, budget, user_profile, trip_details,
            ) if self.USE_LANGGRAPH and LANGGRAPH_AVAILABLE else \
                self._optimize_with_ortools(
                    transport_all, hotels, restaurants, activities,
                    num_days, user_profile,
                )

            is_feasible = (
                "error" not in result
                and result.get("total_cost", float("inf")) <= budget
            )
            
            current_cost = result.get('total_cost', float('inf'))
            
            # Track best plan
            if current_cost < best_cost_overall:
                best_plan_overall = result
                best_cost_overall = current_cost
                print(f"   💰 New best cost: {current_cost:.0f} INR")

            if is_feasible:
                print(f"   ✅ Parallel expansion: feasible plan found in Round {round_num+1}")
                if perf_monitor:
                    perf_monitor.finish_step("Parallel Expansion Rounds")
                return result

            print(f"   ⚠️  Cost: {current_cost:.0f} > Budget: {budget:.0f}, expanding all agents for next round…")

        if perf_monitor:
            perf_monitor.finish_step("Parallel Expansion Rounds")
        
        print("   ❌ Parallel expansion: no feasible plan after "
            f"{max_rounds} rounds")
        print(f"   💡 Best effort cost: INR {best_cost_overall:.0f} (budget: INR {budget:.0f})")
        print(f"   📊 Shortfall: INR {best_cost_overall - budget:.0f}")
        
        # Return best effort if close enough (within 20% of budget)
        if best_cost_overall <= budget * 1.2:
            print(f"   ✓ Returning best effort (only {((best_cost_overall / budget - 1) * 100):.0f}% over)")
            return best_plan_overall
        
        # Budget is impossible - suggest realistic budget
        print(f"   💰 Suggested minimum budget: INR {best_cost_overall:.0f}")
        return None

    def _fetch_with_sequential_generation(
        self,
        origin_code: str,
        dest_code: str,
        destination: str,
        departure_date: str,
        return_date: str,
        interests: Optional[list],
        dietary: Optional[list],
        budget: float,
        num_days: int,
        user_profile,
        trip_details: dict,
        initial_step_size: int = 1,
        perf_monitor: Optional['PerformanceMonitor'] = None,
    ) -> Optional[dict]:
        """
        Method 3: Sequential generation with early stopping (Memory-optimized).
        
        Strategy:
        - Don't pre-fetch all best options at once
        - Instead generate options one-by-one from each agent pool
        - Evaluate each combination immediately
        - Stop early when feasible plan found
        - Lower memory footprint vs other strategies
        
        Process:
        1. For restaurants & activities: Start with MINIMUM UNIQUE required (not just 1)
           - Restaurants: num_days * meals_per_day (e.g., 3 days x 2 meals = 6)
           - Activities: (num_days - 1) * activities_per_day + 1 (e.g., 2 days x 2 + 1 = 5)
        2. For flights & hotels: Use reasonable initial_step_size (3-5)
        3. Try optimization with current pool
        4. If feasible found, return immediately (EARLY STOPPING)
        5. Else, increment fetches and retry
        
        Advantage: First iteration tries realistic options counts, higher chance of success
        """
        
        # ── PRE-CHECK: estimate minimum possible cost ──────────────────────────
        def _estimate_min_cost(destination, departure_date, return_date, num_days):
            MIN_FLIGHT_COST = 3000
            MIN_HOTEL_PER_NIGHT = 800
            MIN_RESTAURANT_PER_MEAL = 300
            MIN_ACTIVITY_PER_DAY = 500
            
            min_total = (
                MIN_FLIGHT_COST * 2
                + MIN_HOTEL_PER_NIGHT * num_days
                + MIN_RESTAURANT_PER_MEAL * 2 * num_days
                + MIN_ACTIVITY_PER_DAY * num_days
            )
            return min_total

        min_possible = _estimate_min_cost(destination, departure_date, return_date, num_days)
        if min_possible > budget:
            print(f"   ❌ Budget INR {budget:,.0f} is below estimated minimum "
                f"INR {min_possible:,.0f} for this trip.")
            return {"error": "budget_too_low", "min_required": min_possible}
        
        def _sequential_init_counts(num_days, MEALS_PER_DAY=2, ACTIVITIES_PER_DAY=2):
            """
            Returns the (flight, hotel, restaurant, activity) starting counts
            for _fetch_with_sequential_generation.
        
            Restaurants and activities start at the minimum required for full coverage.
            Flights and hotels start at 1 (cheapest-first exploration).
            
            Activities are requested with a 2x multiplier because filtering by user interests
            typically removes 30-50% of results, so we request more upfront to ensure
            we have enough after filtering.
            """
            min_restaurants = num_days * MEALS_PER_DAY
            min_activities  = (num_days - 1) * ACTIVITIES_PER_DAY + 1
            # Request 2x activities upfront to account for interest filtering
            requested_activities = min_activities * 2
        
            return dict(
                flights=1,
                hotels=1,
                restaurants=min_restaurants,       # e.g. 6 for a 3-day trip
                activities=requested_activities,   # e.g. 10 for a 3-day trip (2x the minimum)
            )
        
        # ── Calculate minimum unique options required ───────────────────────────
        MEALS_PER_DAY = 2
        ACTIVITIES_PER_DAY = 2
        
        min_restaurants_needed = num_days * MEALS_PER_DAY
        # Activities: last day gets only 1, other days get ACTIVITIES_PER_DAY
        min_activities_needed = (num_days - 1) * ACTIVITIES_PER_DAY + 1
        
        print(f"   🔄 Sequential generation starting")
        print(f"      Minimum unique restaurants needed: {min_restaurants_needed}")
        print(f"      Minimum unique activities needed: {min_activities_needed}")
        
        # ── Consecutive fetch iterations ───────────────────────────────────────
        best_plan_overall = None
        best_cost_overall = float('inf')
        # Start with MINIMAL for flights & hotels, realistic minimum for restaurants & activities
        # current_restaurant_count = min_restaurants_needed
        # current_activity_count = min_activities_needed
        # current_flight_count = 1    # Start minimal: 1 flight option
        # current_hotel_count = 1     # Start minimal: 1 hotel option
        init = _sequential_init_counts(num_days, MEALS_PER_DAY, ACTIVITIES_PER_DAY)
        current_flight_count      = init['flights']
        current_hotel_count       = init['hotels']
        current_restaurant_count  = init['restaurants']
        current_activity_count    = init['activities']
        # Sanity-check: never request fewer than the coverage minimum
        current_restaurant_count  = max(current_restaurant_count, min_restaurants_needed)
        # Activities: keep the multiplied count from _sequential_init_counts (already accounts for filtering)
        # Don't force it down to min_activities_needed, that would undo the 2x multiplier

        base = "INR"
        
        for iteration in range(5):  # Max 5 iterations (increasing diversity each time)
            if current_restaurant_count > 25:  # Cap at 25 options
                break
            
            print(f"\n   📍 Iteration {iteration + 1}:")
            print(f"      Fetching: {current_flight_count} flights | {current_hotel_count} hotels | "
                  f"{current_restaurant_count} restaurants | {current_activity_count} activities")
            
            # ── Fetch from each agent with current counts ──────────────────────
            flights = self.flight_agent.search_flights(
                origin=origin_code,
                destination=dest_code,
                departure_date=departure_date,
                max_results=current_flight_count,
            )
            for f in flights:
                f.price = self.currency_converter.convert(f.price, f.currency, base)
                f.currency = base

            hotels = self.hotel_agent.search_accommodations(
                destination=destination,
                check_in=departure_date,
                check_out=return_date,
                max_results=current_hotel_count,
            )
            for h in hotels:
                h.price_per_night = self.currency_converter.convert(
                    h.price_per_night, h.currency, base)
                h.currency = base

            restaurants = self.restaurant_agent.search_restaurants(
                location=destination,
                dietary_restrictions=dietary or None,
                max_results=current_restaurant_count,
            )
            for r in restaurants:
                r.average_meal_cost = self.currency_converter.convert(
                    r.average_meal_cost, r.currency, base)
                r.currency = base

            activities = self.activity_agent.search_activities(
                location=destination,
                interests=interests or None,
                max_results=current_activity_count,
            )
            for a in activities:
                if hasattr(a, "price"):
                    a.price = self.currency_converter.convert(a.price, a.currency, base)
                    a.currency = base

            distance_km = self.ground_transport_agent.calculate_distance(
                trip_details.get("origin_city", ""), destination)
            ground = []
            current_step_size = max(
                current_flight_count,
                current_hotel_count,
                current_restaurant_count,
                current_activity_count,
                5
            )
            if distance_km <= 1000:
                ground = self.ground_transport_agent.search_transport(
                    origin=trip_details.get("origin_city", ""),
                    destination=destination,
                    transport_types=["taxi", "train", "bus"],
                    max_results=current_step_size,
                )

            transport_all = sorted(
                flights + ground,
                key=lambda t: getattr(t, 'price', float('inf'))
            )
            
            print(f"      ✈️  {len(flights)} flights | 🏨 {len(hotels)} hotels | "
                  f"🍽️  {len(restaurants)} restaurants | 🎭 {len(activities)} activities | "
                  f"🚗 {len(ground)} ground transport")

            # ── Try to optimize with current pool ───────────────────────────────
            result = self._optimize_with_langgraph(
                transport_all, hotels, restaurants, activities,
                num_days, budget, user_profile, trip_details,
            ) if self.USE_LANGGRAPH and LANGGRAPH_AVAILABLE else \
                self._optimize_with_ortools(
                    transport_all, hotels, restaurants, activities,
                    num_days, user_profile,
                )

            is_feasible = (
                "error" not in result
                and result.get("total_cost", float("inf")) <= budget
            )
            
            current_cost = result.get('total_cost', float('inf'))
            
            # Track best plan
            if current_cost < best_cost_overall:
                best_plan_overall = result
                best_cost_overall = current_cost
                print(f"      💰 New best: INR {current_cost:.0f}")

            if is_feasible:
                print(f"   ✅ Sequential generation: feasible plan found in iteration {iteration + 1}")
                return result

            print(f"      ⚠️  Cost: INR {current_cost:.0f} > Budget: INR {budget:.0f}, "
                  f"expanding pools...")
            
            # ── Increment for next iteration ────────────────────────────────────
            # Increase restaurant & activity by 2 each (to get more diversity)
            # Increase flight & hotel by 1 each (minor adjustment)
            current_restaurant_count += 3
            current_activity_count += 2
            current_flight_count += 1
            current_hotel_count += 1

        # ── End of iterations ──────────────────────────────────────────────────
        print(f"   ❌ Sequential generation: no feasible plan after {iteration + 1} iterations")
        print(f"   💡 Best effort cost: INR {best_cost_overall:.0f} (budget: INR {budget:.0f})")
        print(f"   📊 Shortfall: INR {best_cost_overall - budget:.0f}")
        
        # Return best effort if close enough (within 20% of budget)
        if best_cost_overall <= budget * 1.2:
            print(f"   ✓ Returning best effort (only {((best_cost_overall / budget - 1) * 100):.0f}% over)")
            return best_plan_overall
        
        # Budget is impossible
        print(f"   💰 Suggested minimum budget: INR {best_cost_overall:.0f}")
        return None

    # ============================================================================
    # OPTIMIZER SELECTION (Feature Flag)
    # ============================================================================
    
    def _optimize_with_langgraph(self, flights, accommodations, restaurants,
                                 activities, num_days, budget, user_profile,
                                 trip_details: dict) -> dict:
        """
        NEW: Use LangGraph optimizer with dynamic constraints
        
        Key differences from OR-Tools:
        - No hardcoded budget ratios
        - Parallel exploration of combinations
        - Intelligent backtracking
        - User-priority-based evaluation
        """
        
        print("   🔧 Running LangGraph optimizer (parallel + dynamic)...")
        
        try:
            # Extract and clean interests and dietary from trip_details
            interests = trip_details.get('interests')
            dietary = trip_details.get('dietary_restrictions')
            
            # Ensure interests and dietary are lists (handle None, null, or non-list values)
            if not interests or not isinstance(interests, list):
                interests = ['cultural', 'adventure']
            if not dietary or not isinstance(dietary, list):
                dietary = []
            
            # Define flexible budget constraints (no 30% hardcoded!)
            budget_constraint = {
                'total_budget': budget,

                # Soft floors only — prevent zero-cost placeholder picks
                'transport_min':      0,
                'transport_max':      budget,   # uncapped — let optimizer decide

                'accommodation_min':  0,
                'accommodation_max':  budget,

                'restaurant_min':     0,
                'restaurant_max':     budget,

                'activity_min':       0,
                'activity_max':       budget,
            }

            # Preferences — no budget ratio logic here either
            preferences = {
                'priority':               'budget',   # signals evaluator to maximise savings
                'preferred_pace':         trip_details.get('pace', 'balanced'),
                'hotel_min_rating':       3.0,
                'restaurant_min_rating':  3.0,
                'activity_min_rating':    3.0,
                'activity_interests':     interests,
                'dietary_restrictions':   dietary,
                'activities_per_day_min': 1,
                'activities_per_day_max': 4,
                'meals_per_day':          2,
            }
            # Retrieve return options stored by generate_itinerary
            return_transport_options = trip_details.get('_return_transport_options', [])

            # Convert return options to LangGraph format
            return_transport_candidates = self._convert_to_langgraph_format(
                return_transport_options, 'return_transport'
            )
            
            # Initialize LangGraph optimizer
            optimizer = LangGraphItineraryOptimizer(
                budget_constraint=budget_constraint,
                preferences=preferences,
                num_days=num_days
            )
            
            # Convert to LangGraph format
            transport_candidates = self._convert_to_langgraph_format(flights, 'transport')
            accommodation_candidates = self._convert_to_langgraph_format(accommodations, 'accommodation')
            restaurant_candidates = self._convert_to_langgraph_format(restaurants, 'restaurant')
            activity_candidates = self._convert_to_langgraph_format(activities, 'activity')
            
            # Run optimization
            lg_result = optimizer.optimize(
                transport_options=transport_candidates,
                return_transport_options=return_transport_candidates,   # NEW
                accommodation_options=accommodation_candidates,
                restaurant_options=restaurant_candidates,
                activity_options=activity_candidates,
                trip_start_date=trip_details.get('departure_date', '2026-03-01'),
                origin=trip_details.get('origin_city', 'Bangalore'),
                destination=trip_details.get('destination_city', 'Paris')
            )
            
            # Check if successful
            if lg_result['success']:
                print(f"   ✅ LangGraph found optimal plan!")
                print(f"      Score: {lg_result['best_score']:.1f}/100")
                print(f"      Combinations evaluated: {lg_result['evaluated_combinations']}")
                print(f"      Backtrack attempts: {lg_result['backtrack_attempts']}")
                
                # Convert result back to itinerary format
                return self._convert_langgraph_result(lg_result, flights, accommodations,
                                                      restaurants, activities, num_days)
            else:
                print(f"   ⚠️ LangGraph couldn't find plan, falling back to OR-Tools...")
                return self._optimize_with_ortools(flights, accommodations, restaurants,
                                                    activities, num_days, user_profile)
        
        except Exception as e:
            print(f"   ⚠️ LangGraph error: {str(e)[:100]}, falling back to OR-Tools...")
            logger.exception(f"LangGraph optimization failed: {e}")
            return self._optimize_with_ortools(flights, accommodations, restaurants,
                                                activities, num_days, user_profile)
    
    def _optimize_with_ortools(self, flights, accommodations, restaurants,
                               activities, num_days, user_profile) -> dict:
        """
        EXISTING: Use OR-Tools CP-SAT optimizer
        
        This is the original optimizer with hardcoded budget ratios
        Kept for backward compatibility
        """
        
        print("   🔧 Running OR-Tools CP-SAT optimizer...")
        
        optimizer = ItineraryOptimizer(user_profile)
        
        # Pass transport options (flights + ground) as 'flights' parameter
        optimized = optimizer.optimize_itinerary(
            flights=flights,  # This includes both flights and ground transport
            accommodations=accommodations,
            restaurants=restaurants,
            activities=activities,
            num_days=num_days
        )
        
        return optimized
    
    def _convert_to_langgraph_format(self, options: list, category: str) -> list:
        """Convert agent results to LangGraph optimizer format"""
        
        candidates = []
        for i, option in enumerate(options or []):
            # Detect option type and extract fields
            is_flight = hasattr(option, 'carrier')
            is_ground = hasattr(option, 'provider') and hasattr(option, 'type')
            is_accommodation = hasattr(option, 'type') and hasattr(option, 'latitude')
            is_restaurant = hasattr(option, 'cuisine_type')
            is_activity = hasattr(option, 'activity_type')
            
            # Determine category if not explicitly provided
            if category == 'transport':
                if is_flight:
                    sub_type = 'flight'
                elif is_ground:
                    sub_type = 'ground'
                else:
                    sub_type = 'transport'
            else:
                sub_type = category

            # ── build a meaningful name when the raw option has no .name attr ──
            raw_name = getattr(option, 'name', None)

            if not raw_name:
                if is_flight:
                    carrier  = getattr(option, 'carrier', '')
                    orig     = getattr(option, 'origin', '')
                    dest     = getattr(option, 'destination', '')
                    fid      = getattr(option, 'flight_id', '')
                    raw_name = (f"{carrier} {orig}→{dest}"
                                if (carrier and orig and dest)
                                else f"Flight {fid}" if fid
                                else "Flight")
                elif is_ground:
                    provider = getattr(option, 'provider', '')
                    orig     = getattr(option, 'origin', '')
                    dest     = getattr(option, 'destination', '')
                    gtype    = getattr(option, 'type', '')
                    raw_name = (f"{provider} {orig}→{dest}"
                                if provider
                                else f"{gtype} {orig}→{dest}"
                                if gtype
                                else "Ground transport")
                else:
                    raw_name = 'Unknown'

            # Carrier label used both in properties and (later) for display
            carrier_label = getattr(option, 'carrier',
                            getattr(option, 'provider', 'Unknown'))

            candidate = {
                'id': f"{category}_{i}",
                'category': category,
                'name': raw_name,                                    # ← real name now
                'cost': getattr(option, 'price',
                        getattr(option, 'price_per_night', 0)),
                'currency': getattr(option, 'currency', 'INR'),
                'rating': getattr(option, 'rating', 3.5),
                'duration_minutes': getattr(option, 'duration_minutes', 0),
                'properties': {
                    'type':         sub_type,
                    'is_ground':    is_ground,          # NEW — helps display layer
                    'provider':     carrier_label,                   # airline/provider code
                    'origin':       getattr(option, 'origin', ''),
                    'destination':  getattr(option, 'destination', ''),
                    'flight_id':    getattr(option, 'flight_id', ''),
                    'review_count': getattr(option, 'review_count', 0),
                    'cuisine':      getattr(option, 'cuisine_type', ''),
                }
            }
            candidates.append(candidate)
        
        return candidates
    

    def _convert_langgraph_result(self, lg_result: dict, flights, accommodations,
                              restaurants, activities, num_days) -> dict:
        """
        Convert LangGraph result back to itinerary display format.

        Day-slot targets
        ----------------
        • Transport  – Day 0 only (outbound), Day N-1 only (return, added later)
        • Hotel      – every day (same property throughout stay)
        • Restaurants – MEALS_PER_DAY per day, drawn from full restaurant list
        • Activities  – ACTIVITIES_PER_DAY per day, drawn from full activity list
        """

        # ── tuneable constants ──────────────────────────────────────────────────
        MEALS_PER_DAY      = 2   # number of restaurant slots per day
        ACTIVITIES_PER_DAY = 2   # number of activity slots per day
        # ────────────────────────────────────────────────────────────────────────

        best_plan = lg_result.get('best_plan', {})

        # ------------------------------------------------------------------
        # 1.  Initialise empty days
        # ------------------------------------------------------------------
        day_itinerary = {i: [] for i in range(num_days)}

        # ------------------------------------------------------------------
        # 2.  Transport  ──  Day 0 only
        # ------------------------------------------------------------------
        # if best_plan.get('transport'):
        #     day_itinerary[0].append(best_plan['transport'])
        # Outbound transport → Day 0
        if best_plan.get('transport'):
            day_itinerary[0].append(best_plan['transport'])

        # Return transport → last day
        if best_plan.get('return_transport'):
            ret = best_plan['return_transport']
            # Mark as return for display and overlap logic
            if hasattr(ret, 'properties') and isinstance(ret.properties, dict):
                ret.properties['is_return'] = True
            day_itinerary[num_days - 1].insert(0, ret)

        # Cost breakdown — include return transport
        transport_cost  = (best_plan['transport'].cost
                           if best_plan.get('transport') else 0)
        transport_cost += (best_plan['return_transport'].cost
                           if best_plan.get('return_transport') else 0)

        # ------------------------------------------------------------------
        # 3.  Accommodation  ──  every day (same hotel)
        # ------------------------------------------------------------------
        acc_list = best_plan.get('accommodations', [])
        if acc_list:
            for day in range(num_days):
                day_itinerary[day].append(acc_list[0])

        # ------------------------------------------------------------------
        # 4.  Build a rich restaurant pool from the FULL list
        #     (best_plan only has 1 restaurant – not enough for multi-day)
        # ------------------------------------------------------------------
        def _to_option_candidate(obj, category: str, idx: int):
            """
            Lightweight converter: raw agent object → OptionCandidate dict
            that _assign_item_times / display_itinerary can consume.
            Works with both RestaurantOption and ActivityOption.
            """
            from langgraph_optimizer import OptionCandidate   # local import

            # cost ──────────────────────────────────────────────────────────
            cost = (getattr(obj, 'cost', None)
                    or getattr(obj, 'price', None)
                    or getattr(obj, 'average_meal_cost', None)
                    or getattr(obj, 'average_cost', None)
                    or getattr(obj, 'price_per_night', None)
                    or 0)

            # name ─────────────────────────────────────────────────────────
            name = getattr(obj, 'name', f'{category}_{idx}')

            # rating ────────────────────────────────────────────────────────
            rating = getattr(obj, 'rating', 3.5) or 3.5

            # duration ──────────────────────────────────────────────────────
            duration = (getattr(obj, 'duration_minutes', None)
                        or getattr(obj, 'average_meal_time_minutes', None)
                        or 0)

            # cuisine / type details ────────────────────────────────────────
            cuisine = (getattr(obj, 'cuisine_type', None)
                    or getattr(obj, 'cuisine', ''))

            return OptionCandidate(
                id=f"{category}_{idx}",
                category=category,
                name=name,
                cost=cost,
                currency=getattr(obj, 'currency', 'INR'),
                rating=rating,
                duration_minutes=duration,
                properties={
                    'type':     category,
                    'cuisine':  cuisine,
                    'provider': getattr(obj, 'carrier',
                                getattr(obj, 'provider', '')),
                }
            )

        # Build pools ─────────────────────────────────────────────────────
        # ENSURE UNIQUE restaurants/activities per distribution (no repeats for same item on consecutive days)
        
        # Convert all restaurants to OptionCandidate format
        unique_restaurants = []
        if restaurants:
            for i, r in enumerate(restaurants):
                unique_restaurants.append(_to_option_candidate(r, 'restaurant', i))
        
        # Convert all activities to OptionCandidate format
        unique_activities = []
        if activities:
            for i, a in enumerate(activities):
                unique_activities.append(_to_option_candidate(a, 'activity', i))
        
        # Distribute restaurants using modulo (cycles through list without repeating same item consecutively)
        # rest_pool = []
        # for meal_slot in range(num_days * MEALS_PER_DAY):
        #     if unique_restaurants:
        #         selected = unique_restaurants[meal_slot % len(unique_restaurants)]
        #         rest_pool.append(selected)
        
        # # Distribute activities using modulo (cycles through list without repeating same item consecutively)
        # act_pool = []
        # for activity_slot in range((num_days - 1) * ACTIVITIES_PER_DAY + 1):
        #     if unique_activities:
        #         selected = unique_activities[activity_slot % len(unique_activities)]
        #         act_pool.append(selected)
        def _build_pools(unique_restaurants, unique_activities, num_days,
                 MEALS_PER_DAY=2, ACTIVITIES_PER_DAY=2):
            """
            Build per-slot pools for restaurants and activities.
        
            Each slot receives a DEEP COPY of the source item so that
            _assign_item_times() can write a unique scheduled_time into every copy
            without aliasing effects.
        
            A unique id is stamped on each copy:  original_id + "__slot{N}"
            """
        
            total_meal_slots     = num_days * MEALS_PER_DAY
            # last day gets only 1 activity slot
            total_activity_slots = (num_days - 1) * ACTIVITIES_PER_DAY + 1
        
            rest_pool = []
            for slot in range(total_meal_slots):
                if unique_restaurants:
                    src   = unique_restaurants[slot % len(unique_restaurants)]
                    clone = copy.deepcopy(src)
                    clone.id = f"{src.id}__slot{slot}"          # unique id per slot
                    rest_pool.append(clone)
        
            act_pool = []
            for slot in range(total_activity_slots):
                if unique_activities:
                    src   = unique_activities[slot % len(unique_activities)]
                    clone = copy.deepcopy(src)
                    clone.id = f"{src.id}__slot{slot}"
                    act_pool.append(clone)
        
            return rest_pool, act_pool
        
        rest_pool, act_pool = _build_pools(unique_restaurants, unique_activities, num_days,MEALS_PER_DAY, ACTIVITIES_PER_DAY)

        # ------------------------------------------------------------------
        # 5.  Distribute restaurants  ── MEALS_PER_DAY per day
        # ------------------------------------------------------------------
        rest_idx = 0
        for day in range(num_days):
            for _ in range(MEALS_PER_DAY):
                if rest_idx < len(rest_pool):
                    day_itinerary[day].append(rest_pool[rest_idx])
                    rest_idx += 1

        # ------------------------------------------------------------------
        # 6.  Distribute activities  ── ACTIVITIES_PER_DAY per day
        #     Skip the last day (return travel day) – set to 1 activity max
        # ------------------------------------------------------------------
        act_idx = 0
        for day in range(num_days):
            slots = 1 if day == num_days - 1 else ACTIVITIES_PER_DAY
            for _ in range(slots):
                if act_idx < len(act_pool):
                    day_itinerary[day].append(act_pool[act_idx])
                    act_idx += 1

        # ------------------------------------------------------------------
        # 7.  Assign realistic timestamps to every item
        # ------------------------------------------------------------------
        self._assign_item_times(day_itinerary, num_days)
        self._sort_and_fix_overlaps(day_itinerary, num_days)

        # ------------------------------------------------------------------
        # 8.  Calculate costs  ── count each item exactly once
        # ------------------------------------------------------------------
        transport_cost    = 0
        accommodation_cost = 0
        restaurant_cost   = 0
        activity_cost     = 0

        # Transport (day 0 only)
        if best_plan.get('transport'):
            transport_cost = best_plan['transport'].cost

        # Accommodation (count once, not once-per-day)
        for acc in best_plan.get('accommodations', []):
            accommodation_cost += acc.cost

        # Restaurants (unique items actually placed)
        for item in rest_pool[:rest_idx]:
            restaurant_cost += item.cost

        # Activities (unique items actually placed)
        for item in act_pool[:act_idx]:
            activity_cost += item.cost

        total_cost = (transport_cost + accommodation_cost
                    + restaurant_cost + activity_cost)

        print(f"   📊 LangGraph Plan Breakdown:")
        print(f"      Transport:     INR {transport_cost:,.2f}")
        print(f"      Accommodation: INR {accommodation_cost:,.2f}")
        print(f"      Restaurants:   INR {restaurant_cost:,.2f}  ({rest_idx} meals across {num_days} days)")
        print(f"      Activities:    INR {activity_cost:,.2f}  ({act_idx} activities across {num_days} days)")
        print(f"      Total:         INR {total_cost:,.2f}")

        return {
            'total_cost':    total_cost,
            'currency':      'INR',
            'num_days':      num_days,
            'itinerary':     day_itinerary,
            'optimizer_metadata': {
                'optimizer':               'langgraph',
                'score':                   lg_result.get('best_score', 0),
                'combinations_evaluated':  lg_result.get('evaluated_combinations', 0),
                'backtrack_attempts':      lg_result.get('backtrack_attempts', 0),
                'best_plan':               best_plan,
            }
        }

    
    def _assign_item_times(self, day_itinerary: dict, num_days: int) -> None:
        """
        Assign realistic scheduled times to every item in day_itinerary
        by writing into item.properties['scheduled_time'].

        Time assignment rules:
        • Flights / transport   →  06:00 on outbound days, 14:00 on return day
        • Accommodation         →  15:00 check-in (day 0), 'Stay' on later days
        • Restaurants           →  first = 08:00, second = 13:00, third = 19:30
        • Activities            →  09:00 / 10:30 / 14:00 / 16:00 (cycle)
        """
        ACTIVITY_SLOTS = ['09:00', '10:30', '14:00', '16:00']
        MEAL_SLOTS     = ['08:00', '13:00', '19:30']

        for day_num, items in day_itinerary.items():
            restaurant_count = 0
            activity_count   = 0

            for item in items:
                # ── already has a real departure_time?  leave it alone
                if hasattr(item, 'departure_time') and item.departure_time:
                    continue

                # ── detect category
                category = ''
                if hasattr(item, 'category'):
                    category = (item.category or '').lower()
                elif hasattr(item, 'item_type'):
                    category = (item.item_type or '').lower()

                # also sniff by attributes when category string is ambiguous
                is_flight     = hasattr(item, 'carrier') or 'flight' in category
                is_ground     = (hasattr(item, 'provider') and not hasattr(item, 'latitude')
                                and 'transport' in category)
                is_transport  = is_flight or is_ground or category == 'transport'
                is_hotel      = 'accommodation' in category or 'hotel' in (item.name or '').lower()
                is_restaurant = 'restaurant' in category
                is_activity   = 'activity' in category or 'attraction' in category

                # ── pick a time
                if is_transport:
                    # return day (last day index) ── afternoon departure
                    if day_num == num_days - 1:
                        scheduled = '14:00'
                    else:
                        scheduled = '06:00'

                elif is_hotel:
                    scheduled = '15:00' if day_num == 0 else 'Overnight'

                elif is_restaurant:
                    scheduled = MEAL_SLOTS[min(restaurant_count, len(MEAL_SLOTS) - 1)]
                    restaurant_count += 1

                elif is_activity:
                    scheduled = ACTIVITY_SLOTS[activity_count % len(ACTIVITY_SLOTS)]
                    activity_count += 1

                else:
                    scheduled = '10:00'

                # ── write into properties dict (OptionCandidate always has one)
                if hasattr(item, 'properties') and isinstance(item.properties, dict):
                    item.properties['scheduled_time'] = scheduled
                else:
                    # fallback: monkey-patch a tiny attribute
                    try:
                        object.__setattr__(item, '_scheduled_time', scheduled)
                    except Exception:
                        pass

    def _sort_and_fix_overlaps(self, day_itinerary: dict, num_days: int,
                           buffer_minutes: int = 15) -> None:
        """
        Per-day pass that:
        1. Splits items into tiers (transport / moveable / hotel)
        2. Sorts moveable items by scheduled_time ascending
        3. Detects overlaps and nudges later items forward
        4. REMOVES items that cannot start before their category cutoff
        5. Re-sorts the surviving items after nudging (final pass)
        6. Rebuilds day as  transports → moveable → hotel

        Parameters
        ----------
        day_itinerary   : {day_idx: [item, ...]}  — modified IN PLACE
        num_days        : total days (used for return-day detection)
        buffer_minutes  : minimum gap enforced between consecutive slots
        """

        # ── tunable cutoffs ────────────────────────────────────────────────────
        ACTIVITY_CUTOFF   = 21 * 60        # activities must start before 21:00
        RESTAURANT_CUTOFF = 22 * 60 + 30   # restaurants must start before 22:30
        DEFAULT_CUTOFF    = 22 * 60        # fallback for unknown types
        # ────────────────────────────────────────────────────────────────────────

        # ── small utilities ────────────────────────────────────────────────────

        def _to_mins(time_str: str):
            """'HH:MM' → int minutes since midnight, or None."""
            if not time_str or time_str in ('Overnight', 'All day', ''):
                return None
            try:
                parts = time_str.strip().split(':')
                return int(parts[0]) * 60 + int(parts[1])
            except Exception:
                return None

        def _to_str(mins: int) -> str:
            """int minutes (wraps at 24 h) → 'HH:MM'."""
            mins = mins % 1440
            return f"{mins // 60:02d}:{mins % 60:02d}"

        def _get_sched(item) -> str:
            if hasattr(item, 'properties') and isinstance(item.properties, dict):
                return item.properties.get('scheduled_time', '') or ''
            return str(getattr(item, '_scheduled_time', '') or '')

        def _set_sched(item, val: str):
            if hasattr(item, 'properties') and isinstance(item.properties, dict):
                item.properties['scheduled_time'] = val
            else:
                try:
                    object.__setattr__(item, '_scheduled_time', val)
                except Exception:
                    pass

        def _get_dur(item) -> int:
            if hasattr(item, 'properties') and isinstance(item.properties, dict):
                d = item.properties.get('duration_minutes')
                if d:
                    return int(d)
            d = getattr(item, 'duration_minutes', None) or getattr(item, 'duration', None)
            return int(d) if d else 0

        def _category(item) -> str:
            c = (getattr(item, 'category', '')
                or getattr(item, 'item_type', '')).lower()
            name_lower = (getattr(item, 'name', '') or '').lower()
            if 'accommodation' in c or 'hotel' in name_lower:
                return 'hotel'
            if 'flight' in c or 'transport' in c:
                return 'transport'
            if 'restaurant' in c:
                return 'restaurant'
            if 'activity' in c or 'attraction' in c:
                return 'activity'
            return 'other'

        def _cutoff(cat: str) -> int:
            if cat == 'activity':
                return ACTIVITY_CUTOFF
            if cat == 'restaurant':
                return RESTAURANT_CUTOFF
            return DEFAULT_CUTOFF

        # ── process each day ───────────────────────────────────────────────────

        for day_num, items in day_itinerary.items():
            if not items:
                continue

            # 1. Split into tiers ─────────────────────────────────────────────
            transports = []
            moveable   = []
            hotels     = []

            for it in items:
                cat = _category(it)
                if cat == 'hotel':
                    hotels.append(it)
                elif cat == 'transport':
                    transports.append(it)
                else:
                    moveable.append(it)

            # 2. Sort Tier-0 (transports) by departure time ───────────────────
            def _transport_key(it):
                dep = getattr(it, 'departure_time', None)
                if dep and isinstance(dep, str) and 'T' in dep:
                    return _to_mins(dep.split('T')[1][:5]) or 0
                return _to_mins(_get_sched(it)) or 0

            transports.sort(key=_transport_key)

            # 3. Sort Tier-1 (moveable) by current scheduled_time ascending ───
            def _moveable_key(it):
                m = _to_mins(_get_sched(it))
                return m if m is not None else 9999

            moveable.sort(key=_moveable_key)

            # 4. Compute earliest_free from transport anchors ─────────────────
            #    Restaurants / activities cannot happen while a flight is in air.
            earliest_free = 0
            for tr in transports:
                dep = getattr(tr, 'departure_time', None)
                if dep and isinstance(dep, str) and 'T' in dep:
                    start_str = dep.split('T')[1][:5]
                else:
                    start_str = _get_sched(tr)
                start_m = _to_mins(start_str) or 0
                dur     = _get_dur(tr)
                end_m   = start_m + (dur if dur else 60)
                earliest_free = max(earliest_free, end_m + buffer_minutes)

            # 5. Walk moveable items: push forward + drop items past cutoff ───
            cursor   = earliest_free
            kept     = []
            dropped  = 0

            for it in moveable:
                cat       = _category(it)
                sched_str = _get_sched(it)
                start_m   = _to_mins(sched_str)

                if start_m is None:
                    kept.append(it)
                    continue

                # Push forward if this item overlaps the previous one
                if start_m < cursor:
                    start_m = cursor

                # Drop if past the category's day-end cutoff ──────────────────
                if start_m >= _cutoff(cat):
                    dropped += 1
                    continue   # skip this item entirely

                # Item fits — commit the updated time and advance cursor ───────
                _set_sched(it, _to_str(start_m))
                dur    = _get_dur(it)
                end_m  = start_m + (dur if dur else 60)
                cursor = end_m + buffer_minutes
                kept.append(it)

            if dropped:
                print(f"   ⚠️  Day {day_num + 1}: removed {dropped} item(s) "
                    f"that could not fit within reasonable hours")

            # 6. Final sort of surviving items by their (possibly updated) time ─
            #    This ensures items that were nudged are displayed in order.
            def _final_key(it):
                m = _to_mins(_get_sched(it))
                return m if m is not None else 9999

            kept.sort(key=_final_key)

            # 7. Rebuild day: transports → moveable (sorted) → hotel ──────────
            day_itinerary[day_num] = transports + kept + hotels
    # def _sort_and_fix_overlaps(self, day_itinerary: dict, num_days: int,
    #                        buffer_minutes: int = 15) -> None:
    #     """
    #     Per-day pass that:
    #     1. Sorts items chronologically  (flights first, hotel last)
    #     2. Detects time overlaps and nudges later items forward

    #     Parameters
    #     ----------
    #     day_itinerary   : {day_index: [item, ...]}  – modified IN PLACE
    #     num_days        : total days in trip
    #     buffer_minutes  : minimum gap to enforce between consecutive activities
    #     """

    #     # ── helpers ────────────────────────────────────────────────────────────

    #     def _parse_mins(time_str: str):
    #         """'HH:MM' → int minutes, None for non-clock strings."""
    #         if not time_str or time_str in ('Overnight', 'All day', ''):
    #             return None
    #         try:
    #             h, m = time_str.strip().split(':')
    #             return int(h) * 60 + int(m)
    #         except Exception:
    #             return None

    #     def _to_str(mins: int) -> str:
    #         """int minutes → 'HH:MM' (wraps at midnight)."""
    #         mins = mins % 1440
    #         return f"{mins // 60:02d}:{mins % 60:02d}"

    #     def _get_sched(item) -> str:
    #         if hasattr(item, 'properties') and isinstance(item.properties, dict):
    #             return item.properties.get('scheduled_time', '') or ''
    #         return str(getattr(item, '_scheduled_time', '') or '')

    #     def _set_sched(item, val: str):
    #         if hasattr(item, 'properties') and isinstance(item.properties, dict):
    #             item.properties['scheduled_time'] = val
    #         else:
    #             try:
    #                 object.__setattr__(item, '_scheduled_time', val)
    #             except Exception:
    #                 pass

    #     def _get_dur(item) -> int:
    #         """Duration in minutes; 0 if unknown."""
    #         if hasattr(item, 'properties') and isinstance(item.properties, dict):
    #             d = item.properties.get('duration_minutes')
    #             if d:
    #                 return int(d)
    #         d = getattr(item, 'duration_minutes', None) or getattr(item, 'duration', None)
    #         return int(d) if d else 0

    #     def _category(item) -> str:
    #         c = (getattr(item, 'category', '')
    #             or getattr(item, 'item_type', '')).lower()
    #         name_lower = (getattr(item, 'name', '') or '').lower()
    #         if 'accommodation' in c or 'hotel' in name_lower:
    #             return 'hotel'
    #         if 'flight' in c or 'transport' in c:
    #             return 'transport'
    #         if 'restaurant' in c:
    #             return 'restaurant'
    #         if 'activity' in c or 'attraction' in c:
    #             return 'activity'
    #         return 'other'

    #     # ── per-day processing ─────────────────────────────────────────────────

    #     for day_num, items in day_itinerary.items():
    #         if not items:
    #             continue

    #         # ── 1. Split into tiers ───────────────────────────────────────────
    #         transports = []   # Tier 0: fixed anchors
    #         moveable   = []   # Tier 1: restaurants + activities (sortable)
    #         hotels     = []   # Tier 2: always last

    #         for it in items:
    #             cat = _category(it)
    #             if cat == 'hotel':
    #                 hotels.append(it)
    #             elif cat == 'transport':
    #                 transports.append(it)
    #             else:
    #                 moveable.append(it)

    #         # ── 2. Sort Tier-0 by departure_time (they are already fixed) ─────
    #         def _transport_sort_key(it):
    #             dep = getattr(it, 'departure_time', None)
    #             if dep and isinstance(dep, str) and 'T' in dep:
    #                 t = dep.split('T')[1][:5]          # 'HH:MM'
    #                 return _parse_mins(t) or 0
    #             return _parse_mins(_get_sched(it)) or 0

    #         transports.sort(key=_transport_sort_key)

    #         # ── 3. Sort Tier-1 by scheduled_time ─────────────────────────────
    #         def _moveable_sort_key(it):
    #             m = _parse_mins(_get_sched(it))
    #             return m if m is not None else 9999

    #         moveable.sort(key=_moveable_sort_key)

    #         # ── 4. Fix overlaps inside Tier-1  ────────────────────────────────
    #         #       Tier-0 items are anchors: if a moveable item starts while a
    #         #       transport is still running, push it past the flight's end.
    #         #
    #         #       Build the "earliest free minute" from transports first.

    #         earliest_free = 0
    #         for tr in transports:
    #             dep = getattr(tr, 'departure_time', None)
    #             if dep and isinstance(dep, str) and 'T' in dep:
    #                 start_str = dep.split('T')[1][:5]
    #             else:
    #                 start_str = _get_sched(tr)
    #             start_m = _parse_mins(start_str) or 0
    #             dur     = _get_dur(tr)
    #             end_m   = start_m + dur if dur else start_m + 60
    #             earliest_free = max(earliest_free, end_m + buffer_minutes)

    #         # Walk moveable items and push forward when needed
    #         cursor = earliest_free   # minutes-since-midnight of "next available slot"

    #         for it in moveable:
    #             sched_str = _get_sched(it)
    #             start_m   = _parse_mins(sched_str)

    #             if start_m is None:
    #                 # Item has no clock time; just skip overlap logic
    #                 continue

    #             # Push forward if this item would overlap the previous one
    #             if start_m < cursor:
    #                 start_m = cursor
    #                 _set_sched(it, _to_str(start_m))

    #             # Advance cursor past this item (default 60 min if no duration)
    #             dur    = _get_dur(it)
    #             end_m  = start_m + (dur if dur else 60)
    #             cursor = end_m + buffer_minutes

    #         # ── 5. Rebuild day in correct order ──────────────────────────────
    #         #       Tier 0 → Tier 1 → Tier 2
    #         day_itinerary[day_num] = transports + moveable + hotels
    
    def display_itinerary(self, itinerary: dict, trip_details: dict) -> str:
        """Display formatted day-by-day itinerary with proper emojis and timestamps.
        Returns the formatted output as a string for storage/display."""
        
        output_lines = []
        
        output_lines.append("\n" + "="*80)
        output_lines.append("📋 YOUR PERSONALIZED DAY-BY-DAY ITINERARY")
        output_lines.append("="*80)
        
        destination = trip_details.get('destination_city', 'Destination')
        origin = trip_details.get('origin_city', 'Origin')
        
        print(f"\n🌍 Destination: {destination}")
        print(f"📤 From: {origin}")
        print(f"💰 Total Cost: {itinerary.get('currency', 'INR')} {itinerary.get('total_cost', 0):,.2f}")
        print(f"📅 Duration: {itinerary.get('num_days', 0)} days")
        
        # Show optimizer metadata if available
        if 'optimizer_metadata' in itinerary:
            meta = itinerary['optimizer_metadata']
            if meta.get('optimizer') == 'langgraph':
                print(f"\n🤖 LangGraph Optimization:")
                print(f"   Score: {meta.get('score', 0):.1f}/100")
                print(f"   Combinations evaluated: {meta.get('combinations_evaluated', 0)}")
        
        # Day-by-day breakdown
        for day_num in range(itinerary.get('num_days', 0)):
            if day_num not in itinerary.get('itinerary', {}):
                continue
            
            items = itinerary['itinerary'][day_num]
            
            print(f"\n{'━'*80}")
            print(f"📅 DAY {day_num + 1}")
            print(f"{'━'*80}")
            
            if not items:
                print("   🌴 Rest day / Free time")
                continue
            
            day_cost = 0
            
            for item in items:
                # Get item details - handle both OptionCandidate and other objects
                # name = getattr(item, 'name', 'Unknown')
                # ── robust name extraction ────────────────────────────────────────
                name = getattr(item, 'name', None)

                # Fallback: build name from carrier + route for flight items
                if not name or name == 'Unknown':
                    item_type_check = (getattr(item, 'item_type', '')
                                    or getattr(item, 'category', '')).lower()
                    if 'flight' in item_type_check or 'transport' in item_type_check:
                        carrier = getattr(item, 'carrier', None)
                        if not carrier and hasattr(item, 'properties'):
                            carrier = item.properties.get('provider', '')
                        orig = getattr(item, 'origin', '')
                        dest = getattr(item, 'destination', '')
                        if not orig and hasattr(item, 'properties'):
                            orig = item.properties.get('origin', '')
                        if not dest and hasattr(item, 'properties'):
                            dest = item.properties.get('destination', '')
                        is_ret = getattr(item, 'is_return', False)
                        ret_label = ' (Return)' if is_ret else ''
                        name = (f"{carrier} {orig}→{dest}{ret_label}"
                                if carrier else f"Flight {orig}→{dest}{ret_label}")
                    else:
                        name = 'Unknown'
                
                # Try to get item_type from different attributes
                item_type = getattr(item, 'item_type', None)
                if not item_type:
                    item_type = getattr(item, 'category', 'unknown')
                item_type = item_type.lower() if item_type else 'unknown'
                
                # Determine icon based on type and name
                icon = self._get_item_icon(item_type, name)
                
                # Time - Extract proper timestamp
                time_str = self._get_item_time(item)
                
                # Duration
                duration_str = self._get_item_duration(item)
                
                # Cost
                cost = self._get_item_cost(item)
                if cost:
                    day_cost += cost
                
                # Display main line
                print(f"\n   {icon} {time_str} • {name}{duration_str}")
                
                # Display details
                if cost > 0:
                    print(f"      💵 INR {cost:,.2f}")
                
                # Rating if available
                if hasattr(item, 'rating') and item.rating and item.rating > 0:
                    stars = min(5, int(item.rating))
                    rating_str = '⭐' * stars
                    if item.rating % 1 > 0.4:
                        rating_str += '✨'  # Half star indicator
                    print(f"      {rating_str} {item.rating:.1f}/5")
                
                # Additional details based on type
                # if item_type in ['flight', 'transport']:
                #     if hasattr(item, 'carrier') and item.carrier:
                #         print(f"      ✈️ {item.carrier}")
                #     if hasattr(item, 'duration_minutes') and item.duration_minutes > 0:
                #         hrs = item.duration_minutes // 60
                #         mins = item.duration_minutes % 60
                #         print(f"      ⏱️ Duration: {hrs}h {mins}m")
                if item_type in ['flight', 'transport']:
                    # Carrier: check direct attribute first, then properties dict
                    carrier = getattr(item, 'carrier', None)
                    if not carrier and hasattr(item, 'properties') and isinstance(item.properties, dict):
                        carrier = item.properties.get('provider') or item.properties.get('carrier')
                    if carrier and carrier != 'Unknown':
                        # Show origin→destination if available
                        origin = getattr(item, 'origin', None)
                        destination = getattr(item, 'destination', None)
                        if not origin and hasattr(item, 'properties'):
                            origin = item.properties.get('origin', '')
                        if not destination and hasattr(item, 'properties'):
                            destination = item.properties.get('destination', '')
                        route = f" {origin}→{destination}" if (origin and destination) else ""
                        
                        # Use dynamic icon based on transport type
                        carrier_icon = self._get_item_icon(item_type, carrier)
                        
                        # Add transport type label
                        transport_type = ''
                        carrier_lower = carrier.lower()
                        if 'train' in carrier_lower or 'railway' in carrier_lower:
                            transport_type = ' (Train)'
                        elif 'bus' in carrier_lower or 'public' in carrier_lower:
                            transport_type = ' (Bus)'
                        elif 'taxi' in carrier_lower or 'cab' in carrier_lower or 'ola' in carrier_lower or 'uber' in carrier_lower:
                            transport_type = ' (Taxi)'
                        
                        print(f"      {carrier_icon} {carrier}{transport_type}{route}")
                    if hasattr(item, 'duration_minutes') and item.duration_minutes > 0:
                        hrs = item.duration_minutes // 60
                        mins = item.duration_minutes % 60
                        print(f"      ⏱️ Duration: {hrs}h {mins}m")
                elif item_type in ['restaurant']:
                    if hasattr(item, 'cuisine_type') and item.cuisine_type:
                        print(f"      🍜 {item.cuisine_type} cuisine")
                    # Also check properties for cuisine
                    elif hasattr(item, 'properties') and item.properties.get('cuisine'):
                        print(f"      🍜 {item.properties.get('cuisine')} cuisine")
                elif item_type in ['accommodation']:
                    if hasattr(item, 'amenities') and item.amenities:
                        amenities_str = ', '.join(item.amenities[:2])
                        print(f"      🏠 {amenities_str}")
            
            if day_cost > 0:
                print(f"\n   {'─'*76}")
                print(f"   💰 Day {day_num + 1} Total: INR {day_cost:,.2f}")
        
        print("\n" + "="*80)
        print("✅ ITINERARY GENERATION COMPLETE!")
        print("="*80)
    
    
    def display_itinerary_text(self, itinerary: dict, trip_details: dict):
        """Display formatted day-by-day itinerary as text (for console output capture)."""
        
        destination = trip_details.get('destination_city', 'Destination')
        origin = trip_details.get('origin_city', 'Origin')
        
        print("\n" + "="*80)
        print("📋 YOUR PERSONALIZED DAY-BY-DAY ITINERARY")
        print("="*80)
        
        print(f"\n🌍 Destination: {destination}")
        print(f"📤 From: {origin}")
        print(f"💰 Total Cost: {itinerary.get('currency', 'INR')} {itinerary.get('total_cost', 0):,.2f}")
        print(f"📅 Duration: {itinerary.get('num_days', 0)} days")
        
        # Show optimizer metadata if available
        if 'optimizer_metadata' in itinerary:
            meta = itinerary['optimizer_metadata']
            if meta.get('optimizer') == 'langgraph':
                print(f"\n🤖 LangGraph Optimization:")
                print(f"   Score: {meta.get('score', 0):.1f}/100")
                print(f"   Combinations evaluated: {meta.get('combinations_evaluated', 0)}")
        
        # Day-by-day breakdown
        for day_num in range(itinerary.get('num_days', 0)):
            if day_num not in itinerary.get('itinerary', {}):
                continue
            
            items = itinerary['itinerary'][day_num]
            
            print(f"\n{'━'*80}")
            print(f"📅 DAY {day_num + 1}")
            print(f"{'━'*80}")
            
            if not items:
                print("   🌴 Rest day / Free time")
                continue
            
            day_cost = 0
            
            for item in items:
                name = getattr(item, 'name', None)
                if not name or name == 'Unknown':
                    item_type_check = (getattr(item, 'item_type', '')
                                    or getattr(item, 'category', '')).lower()
                    if 'flight' in item_type_check or 'transport' in item_type_check:
                        carrier = getattr(item, 'carrier', None)
                        if not carrier and hasattr(item, 'properties'):
                            carrier = item.properties.get('provider', '')
                        orig = getattr(item, 'origin', '')
                        dest = getattr(item, 'destination', '')
                        if not orig and hasattr(item, 'properties'):
                            orig = item.properties.get('origin', '')
                        if not dest and hasattr(item, 'properties'):
                            dest = item.properties.get('destination', '')
                        is_ret = getattr(item, 'is_return', False)
                        ret_label = ' (Return)' if is_ret else ''
                        name = (f"{carrier} {orig}→{dest}{ret_label}" if carrier 
                                else f"Flight {orig}→{dest}{ret_label}")
                    else:
                        name = 'Unknown'
                
                item_type = getattr(item, 'item_type', None) or getattr(item, 'category', 'unknown')
                item_type = item_type.lower() if item_type else 'unknown'
                
                icon = self._get_item_icon(item_type, name)
                time_str = self._get_item_time(item)
                duration_str = self._get_item_duration(item)
                cost = self._get_item_cost(item)
                
                if cost:
                    day_cost += cost
                
                print(f"\n   {icon} {time_str} • {name}{duration_str}")
                
                if cost > 0:
                    print(f"      💵 INR {cost:,.2f}")
                
                if hasattr(item, 'rating') and item.rating and item.rating > 0:
                    stars = min(5, int(item.rating))
                    rating_str = '⭐' * stars
                    if item.rating % 1 > 0.4:
                        rating_str += '✨'
                    print(f"      {rating_str} {item.rating:.1f}/5")
                
                if item_type in ['flight', 'transport']:
                    carrier = getattr(item, 'carrier', None)
                    if not carrier and hasattr(item, 'properties') and isinstance(item.properties, dict):
                        carrier = item.properties.get('provider') or item.properties.get('carrier')
                    if carrier and carrier != 'Unknown':
                        origin_disp = getattr(item, 'origin', '')
                        dest_disp = getattr(item, 'destination', '')
                        if not origin_disp and hasattr(item, 'properties'):
                            origin_disp = item.properties.get('origin', '')
                        if not dest_disp and hasattr(item, 'properties'):
                            dest_disp = item.properties.get('destination', '')
                        route = f" {origin_disp}→{dest_disp}" if (origin_disp and dest_disp) else ""
                        carrier_icon = self._get_item_icon(item_type, carrier)
                        transport_type = ''
                        carrier_lower = carrier.lower()
                        if 'train' in carrier_lower or 'railway' in carrier_lower:
                            transport_type = ' (Train)'
                        elif 'bus' in carrier_lower or 'public' in carrier_lower:
                            transport_type = ' (Bus)'
                        elif 'taxi' in carrier_lower or 'cab' in carrier_lower or 'ola' in carrier_lower or 'uber' in carrier_lower:
                            transport_type = ' (Taxi)'
                        print(f"      {carrier_icon} {carrier}{transport_type}{route}")
                    if hasattr(item, 'duration_minutes') and item.duration_minutes > 0:
                        hrs = item.duration_minutes // 60
                        mins = item.duration_minutes % 60
                        print(f"      ⏱️ Duration: {hrs}h {mins}m")
                elif item_type in ['restaurant']:
                    if hasattr(item, 'cuisine_type') and item.cuisine_type:
                        print(f"      🍜 {item.cuisine_type} cuisine")
                    elif hasattr(item, 'properties') and item.properties.get('cuisine'):
                        print(f"      🍜 {item.properties.get('cuisine')} cuisine")
            
            if day_cost > 0:
                print(f"\n   {'─'*76}")
                print(f"   💰 Day {day_num + 1} Total: INR {day_cost:,.2f}")
        
        print("\n" + "="*80)
        print("✅ ITINERARY GENERATION COMPLETE!")
        print("="*80)
    
    def _get_item_icon(self, item_type: str, name: str) -> str:
        """Get appropriate emoji icon for item type"""
        item_type = item_type.lower()
        name_lower = name.lower()
        
        # Check for specific types
        if 'transport' in item_type or 'flight' in item_type or '→' in name_lower:
            # Ground transport detection FIRST
            if 'train' in name_lower or 'railway' in name_lower or 'rajdhani' in name_lower or 'express' in name_lower:
                return "🚆"
            elif 'bus' in name_lower or 'vrl' in name_lower or 'redbus' in name_lower or 'public transport' in name_lower:
                return "🚌"
            elif 'taxi' in name_lower or 'uber' in name_lower or 'ola' in name_lower or 'cab' in name_lower:
                return "🚕"
            elif 'car' in name_lower:
                return "🚗"
            elif 'flight' in item_type or 'flight' in name_lower or 'air' in name_lower:
                return "✈️"
            else:
                return "✈️"  # Default transport to flight
        elif 'accommodation' in item_type or 'hotel' in name_lower:
            return "🏨"
        elif 'restaurant' in item_type or 'dining' in item_type:
            return "🍽️"
        elif 'activity' in item_type or 'attraction' in item_type:
            return "🎭"
        else:
            # Fallback: check name for clues
            if 'hotel' in name_lower or 'hôtel' in name_lower or 'inn' in name_lower:
                return "🏨"
            elif 'restaurant' in name_lower or 'café' in name_lower or 'bistro' in name_lower:
                return "🍽️"
            elif 'flight' in name_lower or 'air' in name_lower:
                return "✈️"
            elif 'train' in name_lower or 'railway' in name_lower or 'express' in name_lower:
                return "🚆"
            elif 'bus' in name_lower or 'public transport' in name_lower:
                return "🚌"
            elif 'taxi' in name_lower or 'cab' in name_lower:
                return "🚕"
            elif 'museum' in name_lower or 'palace' in name_lower or 'cathedral' in name_lower or 'tower' in name_lower or 'park' in name_lower or 'beach' in name_lower or 'garden' in name_lower:
                return "🎭"
            else:
                return "📍"
    
    # def _get_item_time(self, item) -> str:
    #     """Extract proper time string from item"""
    #     # Try different time attributes
    #     if hasattr(item, 'departure_time') and item.departure_time:
    #         time_val = item.departure_time
    #         if isinstance(time_val, str):
    #             # Parse ISO format like "2026-03-03T17:03:00"
    #             if 'T' in time_val:
    #                 time_part = time_val.split('T')[1][:5]  # Get HH:MM
    #                 return f"[{time_part}]"
    #             return f"[{time_val}]"
    #         return "[Time]"
        
    #     # Check properties dict for departure_time (OptionCandidate)
    #     if hasattr(item, 'properties') and isinstance(item.properties, dict):
    #         if 'departure_time' in item.properties:
    #             time_val = item.properties['departure_time']
    #             if isinstance(time_val, str) and 'T' in time_val:
    #                 time_part = time_val.split('T')[1][:5]
    #                 return f"[{time_part}]"
        
    #     if hasattr(item, 'start_time') and item.start_time and item.start_time > 0:
    #         hours = int(item.start_time // 60)
    #         mins = int(item.start_time % 60)
    #         return f"[{hours:02d}:{mins:02d}]"
    #     elif hasattr(item, 'time_str') and item.time_str:
    #         return f"[{item.time_str}]"
    #     else:
    #         return "[All day]"

    def _get_item_time(self, item) -> str:
        """Extract proper time string from item, falling back to assigned slot."""

        # ── 1. Check properties dict for assigned scheduled_time (OptionCandidate)
        if hasattr(item, 'properties') and isinstance(item.properties, dict):
            st = item.properties.get('scheduled_time')
            if st:
                return f"[{st}]"

        # ── 2. Check monkey-patched fallback attribute
        if hasattr(item, '_scheduled_time') and item._scheduled_time:
            return f"[{item._scheduled_time}]"

        # ── 3. Real departure_time on flight / transport objects
        if hasattr(item, 'departure_time') and item.departure_time:
            time_val = item.departure_time
            if isinstance(time_val, str):
                if 'T' in time_val:          # "2026-03-03T17:03:00"
                    time_part = time_val.split('T')[1][:5]
                    return f"[{time_part}]"
                return f"[{time_val}]"
            return "[Time]"

        # ── 4. Check properties dict for departure_time
        if hasattr(item, 'properties') and isinstance(item.properties, dict):
            tv = item.properties.get('departure_time')
            if tv and isinstance(tv, str) and 'T' in tv:
                return f"[{tv.split('T')[1][:5]}]"

        # ── 5. Numeric start_time (minutes since midnight)
        if hasattr(item, 'start_time') and item.start_time and item.start_time > 0:
            hours = int(item.start_time // 60)
            mins  = int(item.start_time % 60)
            return f"[{hours:02d}:{mins:02d}]"

        # ── 6. Plain string time_str
        if hasattr(item, 'time_str') and item.time_str:
            return f"[{item.time_str}]"

        return "[All day]"   # genuine fallback only when nothing else matches
    
    def _get_item_duration(self, item) -> str:
        """Extract duration string from item"""
        # Check properties dict first (for OptionCandidate)
        if hasattr(item, 'properties') and isinstance(item.properties, dict):
            if 'duration_minutes' in item.properties:
                dur = item.properties['duration_minutes']
                if dur > 0:
                    hrs = dur // 60
                    mins = dur % 60
                    if hrs > 0:
                        return f" ({hrs}h {mins}m)" if mins > 0 else f" ({hrs}h)"
                    elif mins > 0:
                        return f" ({mins}m)"
        
        if hasattr(item, 'duration_minutes') and item.duration_minutes > 0:
            hrs = item.duration_minutes // 60
            mins = item.duration_minutes % 60
            if hrs > 0:
                return f" ({hrs}h {mins}m)" if mins > 0 else f" ({hrs}h)"
            elif mins > 0:
                return f" ({mins}m)"
        elif hasattr(item, 'duration') and item.duration > 0:
            hrs = item.duration // 60
            mins = item.duration % 60
            if hrs > 0:
                return f" ({hrs}h {mins}m)" if mins > 0 else f" ({hrs}h)"
            elif mins > 0:
                return f" ({mins}m)"
        elif hasattr(item, 'duration_hours') and item.duration_hours > 0:
            return f" ({item.duration_hours}h)"
        return ""
    
    def _get_item_cost(self, item) -> float:
        """Extract cost from item"""
        # Check properties dict first (for OptionCandidate)
        if hasattr(item, 'properties') and isinstance(item.properties, dict):
            if 'cost' in item.properties and item.properties['cost'] > 0:
                return item.properties['cost']
        
        if hasattr(item, 'cost') and item.cost:
            return item.cost
        elif hasattr(item, 'price') and item.price:
            return item.price
        elif hasattr(item, 'price_per_night') and item.price_per_night:
            return item.price_per_night
        return 0


    """
    FIX: Add City to Airport Code Mapping
    This allows return journey to work even without airport codes in trip_details
    """

    def add_return_journey(self, itinerary, trip_details: dict):
        """
        Add return flight/transport to the last day of itinerary
        NOW WITH CITY-TO-AIRPORT-CODE MAPPING
        """
        
        print("\n" + "="*80)
        print("🔄 ADDING RETURN JOURNEY")
        print("="*80)
        
        # City to airport code mapping
        CITY_TO_AIRPORT = {
            # Major Indian Cities
            'bangalore': 'BLR',
            'bengaluru': 'BLR',
            'mumbai': 'BOM',
            'delhi': 'DEL',
            'new delhi': 'DEL',
            'kolkata': 'CCU',
            'chennai': 'MAA',
            'hyderabad': 'HYD',
            'pune': 'PNQ',
            'ahmedabad': 'AMD',
            'jaipur': 'JAI',
            'kochi': 'COK',
            'cochin': 'COK',
            'goa': 'GOI',
            'thiruvananthapuram': 'TRV',
            'trivandrum': 'TRV',
            'lucknow': 'LKO',
            'chandigarh': 'IXC',
            'coimbatore': 'CJB',
            'mangalore': 'IXE',
            'mangaluru': 'IXE',
            'visakhapatnam': 'VTZ',
            'vizag': 'VTZ',
            'indore': 'IDR',
            'bhubaneswar': 'BBI',
            'nagpur': 'NAG',
            'vadodara': 'BDQ',
            'raipur': 'RPR',
            'surat': 'STV',
            'amritsar': 'ATQ',
            'varanasi': 'VNS',
            'patna': 'PAT',
            'ranchi': 'IXR',
            'guwahati': 'GAU',
            'imphal': 'IMF',
            'agartala': 'IXA',
            
            # International Cities
            'paris': 'CDG',
            'london': 'LHR',
            'new york': 'JFK',
            'dubai': 'DXB',
            'singapore': 'SIN',
            'bangkok': 'BKK',
            'kuala lumpur': 'KUL',
            'hong kong': 'HKG',
            'tokyo': 'NRT',
            'sydney': 'SYD',
            'melbourne': 'MEL',
            'los angeles': 'LAX',
            'san francisco': 'SFO',
            'toronto': 'YYZ',
            'vancouver': 'YVR',
            'amsterdam': 'AMS',
            'frankfurt': 'FRA',
            'zurich': 'ZRH',
            'rome': 'FCO',
            'barcelona': 'BCN',
            'madrid': 'MAD',
            'istanbul': 'IST',
            'doha': 'DOH',
            'abu dhabi': 'AUH',
            'muscat': 'MCT',
            'colombo': 'CMB',
            'kathmandu': 'KTM',
            'dhaka': 'DAC',
            'male': 'MLE',
            'phuket': 'HKT',
            'denpasar': 'DPS',
            'bali': 'DPS',
            'beijing': 'PEK',
            'shanghai': 'PVG',
            'seoul': 'ICN',
            'osaka': 'KIX',
        }
        
        # DEBUG: Show what trip_details contains
        print(f"   🔍 trip_details keys: {list(trip_details.keys())}")
        
        # Extract origin and destination cities
        origin = (trip_details.get('origin_city') or 
                trip_details.get('origin') or 
                trip_details.get('from_city'))
        
        destination = (trip_details.get('destination_city') or 
                    trip_details.get('destination') or 
                    trip_details.get('to_city'))
        
        # Try to get airport codes directly first
        origin_code = (trip_details.get('origin_code') or 
                    trip_details.get('from_code') or 
                    trip_details.get('origin_airport'))
        
        destination_code = (trip_details.get('destination_code') or 
                        trip_details.get('to_code') or 
                        trip_details.get('destination_airport'))
        
        # If no airport codes, convert from city names
        if not origin_code and origin:
            origin_lower = origin.lower().strip()
            origin_code = CITY_TO_AIRPORT.get(origin_lower)
            if origin_code:
                print(f"   ✓ Mapped '{origin}' → {origin_code}")
            else:
                print(f"   ⚠️ Unknown city: '{origin}' (add to mapping)")
        
        if not destination_code and destination:
            destination_lower = destination.lower().strip()
            destination_code = CITY_TO_AIRPORT.get(destination_lower)
            if destination_code:
                print(f"   ✓ Mapped '{destination}' → {destination_code}")
            else:
                print(f"   ⚠️ Unknown city: '{destination}' (add to mapping)")
        
        # Show what we extracted
        print(f"   📍 Origin: {origin} ({origin_code or 'Unknown'})")
        print(f"   📍 Destination: {destination} ({destination_code or 'Unknown'})")
        
        # Get other details
        departure_date = trip_details.get('departure_date', '2026-03-01')
        num_days = trip_details.get('num_days', 7)
        
        # Validate we have airport codes
        if not origin_code or not destination_code:
            print(f"\n   ❌ ERROR: Could not determine airport codes!")
            print(f"      Origin code: {origin_code}")
            print(f"      Destination code: {destination_code}")
            
            if not origin_code and origin:
                print(f"\n   💡 Please add '{origin.lower()}' to the CITY_TO_AIRPORT mapping")
            if not destination_code and destination:
                print(f"   💡 Please add '{destination.lower()}' to the CITY_TO_AIRPORT mapping")
            
            print(f"\n   ⚠️ Cannot add return journey without airport codes")
            return itinerary
        
        # Calculate return date (last day)
        from datetime import datetime, timedelta
        try:
            dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
            return_date = (dep_date + timedelta(days=num_days - 1)).strftime('%Y-%m-%d')
        except Exception as e:
            print(f"   ⚠️ Date parsing error: {e}")
            return_date = departure_date
        
        print(f"   🛬 Return route: {destination} ({destination_code}) → {origin} ({origin_code})")
        print(f"   📅 Return date: {return_date}")
        
        # Try to search for return flight
        return_flight = None
        try:
            print(f"   🔍 Searching return flights...")
            return_flights = self.flight_agent.search_flights(
                origin=destination_code,      # Flying FROM destination
                destination=origin_code,      # Flying TO origin
                departure_date=return_date,
                adults=1,
                max_results=5
            )
            
            if return_flights and len(return_flights) > 0:
                # Select cheapest return flight
                return_flight = min(return_flights, key=lambda x: x.price)
                print(f"   ✅ Found {len(return_flights)} return flights")
                print(f"   ✓ Selected: {return_flight.carrier} {destination_code}→{origin_code}")
                print(f"   💰 Cost: {return_flight.currency} {return_flight.price:,.2f}")
            else:
                print(f"   ℹ️ No return flights from API, generating mock")
                return_flight = self._create_mock_return_flight(
                    destination_code, origin_code, return_date, destination, origin
                )
        
        except Exception as e:
            print(f"   ⚠️ Return flight search error: {str(e)[:100]}")
            print(f"   ℹ️ Generating mock return flight")
            return_flight = self._create_mock_return_flight(
                destination_code, origin_code, return_date, destination, origin
            )
        
        if return_flight and return_flight.currency != 'INR':
            original_price    = return_flight.price
            original_currency = return_flight.currency
            return_flight.price    = self.currency_converter.convert(
                original_price, original_currency, 'INR'
            )
            return_flight.currency = 'INR'
            print(f"   💱 Converted: {original_currency} {original_price:,.2f} "
                  f"→ INR {return_flight.price:,.2f}")
            
        if not return_flight:
            print(f"   ❌ Could not add return journey")
            return itinerary
        
        # Add return flight to itinerary
        added = False
        try:
            # Handle dict format with 'itinerary' key
            if isinstance(itinerary, dict) and 'itinerary' in itinerary:
                last_day_idx = num_days - 1  # 0-indexed
                
                # Ensure last day exists in itinerary
                if last_day_idx not in itinerary['itinerary']:
                    itinerary['itinerary'][last_day_idx] = []
                
                # Add return flight at start of last day (morning departure)
                itinerary['itinerary'][last_day_idx].insert(0, return_flight)
                
                # Update total cost
                if 'total_cost' in itinerary:
                    itinerary['total_cost'] += return_flight.price
                
                added = True
                print(f"   ✅ Return flight added to Day {num_days}")
            
            # Handle daily_schedules format
            elif hasattr(itinerary, 'daily_schedules') and itinerary.daily_schedules:
                last_day_schedule = itinerary.daily_schedules[-1]
                
                # Ensure items list exists
                if not hasattr(last_day_schedule, 'items'):
                    last_day_schedule.items = []
                
                # Add to beginning of last day
                last_day_schedule.items.insert(0, return_flight)
                
                added = True
                print(f"   ✅ Return flight added to Day {last_day_schedule.day_number}")
            
            else:
                print(f"   ⚠️ Unknown itinerary format")
                print(f"   Type: {type(itinerary)}")
                if isinstance(itinerary, dict):
                    print(f"   Keys: {list(itinerary.keys())}")
        
        except Exception as e:
            print(f"   ❌ Error adding return flight: {e}")
            import traceback
            traceback.print_exc()
        
        if added:
            print(f"   🎉 Return journey successfully added!")
        
        return itinerary


    # Keep your existing _create_mock_return_flight method
    # (The one from the previous file works fine)


    def _create_mock_return_flight(self, origin_code: str, destination_code: str, 
                                date: str, origin_city: Optional[str] = None, 
                                destination_city: Optional[str] = None):
        """
        Create a realistic mock return flight
        
        Args:
            origin_code: Airport code departing from (e.g., 'BOM')
            destination_code: Airport code arriving at (e.g., 'BLR')
            date: Departure date (YYYY-MM-DD)
            origin_city: Origin city name
            destination_city: Destination city name
        """
        from datetime import datetime, timedelta
        from dataclasses import dataclass
        import random
        
        # Airlines operating in India
        carriers = [
            ('AI', 'Air India'),
            ('6E', 'IndiGo'),
            ('UK', 'Vistara'),
            ('SG', 'SpiceJet'),
            ('G8', 'Go First')
        ]
        
        carrier_code, carrier_name = random.choice(carriers)
        
        # Generate realistic departure/arrival times
        try:
            dep_dt = datetime.strptime(date, '%Y-%m-%d')
            
            # Morning/afternoon departure (6am - 4pm)
            dep_hour = random.randint(6, 16)
            dep_minute = random.choice([0, 15, 30, 45])
            dep_time = dep_dt.replace(hour=dep_hour, minute=dep_minute)
            
            # Flight duration (1-3 hours for domestic, 6-12 for international)
            is_domestic = (origin_code[:2] == destination_code[:2] == 'IN' or 
                        origin_code in ['BLR', 'BOM', 'DEL', 'MAA', 'CCU', 'HYD'] and 
                        destination_code in ['BLR', 'BOM', 'DEL', 'MAA', 'CCU', 'HYD'])
            
            if is_domestic:
                duration_hours = random.randint(1, 3)
                duration_minutes = random.randint(0, 59)
            else:
                duration_hours = random.randint(6, 12)
                duration_minutes = random.randint(0, 59)
            
            total_duration_mins = duration_hours * 60 + duration_minutes
            
            arr_time = dep_time + timedelta(minutes=total_duration_mins)
            
            dep_time_str = dep_time.isoformat()
            arr_time_str = arr_time.isoformat()
            
        except Exception as e:
            print(f"      ⚠️ Date error: {e}")
            dep_time_str = f"{date}T10:00:00"
            arr_time_str = f"{date}T13:00:00"
            total_duration_mins = 180
            is_domestic = True
        
        # Realistic pricing
        if is_domestic:
            base_price = random.uniform(3000, 8000)
        else:
            base_price = random.uniform(25000, 45000)
        
        price = round(base_price, 2)
        
        # Create return flight object
        @dataclass
        class ReturnFlight:
            flight_id: str
            name: str                    # ← plain field, not @property
            origin: str
            destination: str
            departure_time: str
            arrival_time: str
            duration_minutes: int
            price: float
            currency: str
            carrier: str
            segments: int
            class_type: str
            reliability_score: float
            available_seats: int
            item_type: str
            is_return: bool

            @property
            def duration(self):          # kept for compatibility
                return self.duration_minutes

        # Build the name string before construction
        flight_name = f"{carrier_code} {origin_code}→{destination_code} (Return)"

        flight = ReturnFlight(
            flight_id=f"RET{random.randint(1000, 9999)}",
            name=flight_name,            # ← passed directly as field
            origin=origin_code,
            destination=destination_code,
            departure_time=dep_time_str,
            arrival_time=arr_time_str,
            duration_minutes=total_duration_mins,
            price=price,
            currency='INR',
            carrier=carrier_code,
            segments=random.randint(1, 2),
            class_type='economy',
            reliability_score=random.uniform(0.85, 0.95),
            available_seats=random.randint(10, 50),
            item_type='flight',
            is_return=True
        )

        hrs = total_duration_mins // 60
        mins = total_duration_mins % 60
        print(f"   📝 Generated: {carrier_code} {origin_code}→{destination_code} | "
              f"{hrs}h {mins}m | INR {price:,.2f}")

        return flight

        # @dataclass
        # class ReturnFlight:
        #     flight_id: str
        #     origin: str
        #     destination: str
        #     departure_time: str
        #     arrival_time: str
        #     duration_minutes: int
        #     price: float
        #     currency: str
        #     carrier: str
        #     segments: int
        #     class_type: str
        #     reliability_score: float
        #     available_seats: int
        #     item_type: str
        #     is_return: bool
            
        #     @property
        #     def name(self):
        #         return f"{self.carrier} {self.origin}-{self.destination} (Return)"
            
        #     @property
        #     def duration(self):
        #         return self.duration_minutes
        
        # flight = ReturnFlight(
        #     flight_id=f"RET{random.randint(1000, 9999)}",
        #     origin=origin_code,
        #     destination=destination_code,
        #     departure_time=dep_time_str,
        #     arrival_time=arr_time_str,
        #     duration_minutes=total_duration_mins,
        #     price=price,
        #     currency='INR',
        #     carrier=carrier_code,
        #     segments=random.randint(1, 2),
        #     class_type='economy',
        #     reliability_score=random.uniform(0.85, 0.95),
        #     available_seats=random.randint(10, 50),
        #     item_type='flight',
        #     is_return=True
        # )
        
        # hrs = total_duration_mins // 60
        # mins = total_duration_mins % 60
        # print(f"   📝 Generated: {carrier_code} {origin_code}→{destination_code} | "
        #     f"{hrs}h {mins}m | INR {price:,.2f}")
        
        # return flight


    # ============================================================================
    # OPTIONAL: Ground Transport Return (for domestic trips)
    # ============================================================================

    def add_return_ground_transport(self, itinerary, trip_details: dict):
        """
        Add return ground transport (train/bus) instead of flight
        Use this for domestic trips where ground transport is more common
        """
        
        print("\n" + "="*80)
        print("🚂 ADDING RETURN GROUND TRANSPORT")
        print("="*80)
        
        origin = trip_details.get('origin_city', 'Bangalore')
        destination = trip_details.get('destination_city', 'Mumbai')
        departure_date = trip_details.get('departure_date', '2026-03-01')
        num_days = trip_details.get('num_days', 7)
        
        # Calculate return date
        try:
            dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
            return_date = (dep_date + timedelta(days=num_days - 1)).strftime('%Y-%m-%d')
        except:
            return_date = departure_date
        
        print(f"   🚂 Return route: {destination} → {origin}")
        print(f"   📅 Return date: {return_date}")
        
        # Create mock ground transport
        transport_types = [
            ('Train', 'Indian Railways', 1000, 8),
            ('Train', 'Rajdhani Express', 1500, 6),
            ('Bus', 'VRL Travels', 800, 10),
            ('Bus', 'RedBus Sleeper', 900, 9)
        ]
        
        transport_type, provider, base_cost, hours = random.choice(transport_types)
        
        @dataclass
        class ReturnTransport:
            transport_id: str
            origin: str
            destination: str
            departure_time: str
            duration_hours: float
            price: float
            currency: str
            provider: str
            transport_type: str
            item_type: str
            is_return: bool
            
            @property
            def name(self):
                return f"{self.provider} {self.origin}-{self.destination} (Return)"
            
            @property
            def duration_minutes(self):
                return int(self.duration_hours * 60)
            
            @property
            def duration(self):
                return int(self.duration_hours * 60)
        
        transport = ReturnTransport(
            transport_id=f"GT_RET_{random.randint(1000, 9999)}",
            origin=destination,
            destination=origin,
            departure_time=f"{return_date}T20:00:00",  # Evening departure
            duration_hours=hours,
            price=round(base_cost * random.uniform(0.9, 1.1), 2),
            currency='INR',
            provider=provider,
            transport_type=transport_type,
            item_type='ground_transport',
            is_return=True
        )
        
        print(f"   ✓ Generated: {provider} ({transport_type})")
        print(f"   💰 Cost: INR {transport.price:,.2f} | Duration: {hours}h")
        
        # Add to itinerary (same logic as flight)
        try:
            if isinstance(itinerary, dict) and 'itinerary' in itinerary:
                last_day_idx = num_days - 1
                
                if last_day_idx not in itinerary['itinerary']:
                    itinerary['itinerary'][last_day_idx] = []
                
                itinerary['itinerary'][last_day_idx].insert(0, transport)
                
                if 'total_cost' in itinerary:
                    itinerary['total_cost'] += transport.price
                
                print(f"   ✅ Return transport added to Day {num_days}")
            
            elif hasattr(itinerary, 'daily_schedules') and itinerary.daily_schedules:
                last_day_schedule = itinerary.daily_schedules[-1]
                if not hasattr(last_day_schedule, 'items'):
                    last_day_schedule.items = []
                last_day_schedule.items.insert(0, transport)
                print(f"   ✅ Return transport added!")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        return itinerary


    """"

    2. In your generate_itinerary() method, add this AFTER optimization:

    # Run optimizer
    result = optimizer.optimize_itinerary(...)
    
    # ADD RETURN JOURNEY
    result = self.add_return_journey(result, trip_details)
    
    # Display
    self.display_itinerary_with_transport(result, trip_details)

    3. For ground transport returns (trains/buses), use:
    result = self.add_return_ground_transport(result, trip_details)

    Done! Return journey will now appear on the last day.
    """

    def display_itinerary_with_transport(self, itinerary, trip_details: dict):
        """Display itinerary with transport - works with dict format"""
        
        print("\n🚗 Preparing itinerary display...")
        
        # Handle dict format from optimizer
        daily_schedules = None
        
        # Try to extract daily schedules
        if hasattr(itinerary, 'daily_schedules'):
            daily_schedules = itinerary.daily_schedules
        elif isinstance(itinerary, dict) and 'itinerary' in itinerary:
            # Check if itinerary is empty
            if not itinerary['itinerary'] or len(itinerary['itinerary']) == 0:
                print(f"\n   ℹ️ No detailed daily schedule available, using summary display")
                self.display_itinerary(itinerary, trip_details)
                return
            
            # Convert old dict format
            from dataclasses import dataclass
            from typing import List, Any
            
            @dataclass
            class DaySchedule:
                day_number: int
                items: List[Any]
            
            daily_schedules = []
            for day_num in range(itinerary.get('num_days', 7)):
                if day_num in itinerary['itinerary']:
                    daily_schedules.append(DaySchedule(
                        day_number=day_num + 1,
                        items=itinerary['itinerary'][day_num]
                    ))
            
            print(f"   ✓ Converted {len(daily_schedules)} days")
        
        if not daily_schedules:
            print(f"   Using standard display")
            self.display_itinerary(itinerary, trip_details)
            return
        
        # Enhance with transport
        try:
            from itinerary_enhancer import ItineraryEnhancer, display_enhanced_itinerary
            
            enhancer = ItineraryEnhancer(budget_conscious=True)
            enhanced = enhancer.enhance_itinerary(daily_schedules)
            
            total_budget = trip_details.get('budget_inr', 0)
            if hasattr(self, 'user_profile') and hasattr(self.user_profile, 'budget'):
                total_budget = self.user_profile.budget
            
            display_enhanced_itinerary(enhanced, total_budget=total_budget)
            
            # Store complete itinerary to MongoDB
            try:
                user_id = trip_details.get('user_id', 'anonymous')
                
                # Calculate total cost
                total_cost = sum(day.total_cost for day in enhanced)
                
                # Convert EnhancedDaySchedule objects to storable format
                daily_schedules_data = []
                for day in enhanced:
                    day_data = {
                        'day_number': day.day_number,
                        'total_cost': day.total_cost,
                        'total_duration_minutes': day.total_duration_minutes,
                        'items': [
                            {
                                'time': item.time,
                                'type': item.type,
                                'name': item.name,
                                'duration_minutes': item.duration_minutes,
                                'cost': item.cost,
                                'currency': item.currency,
                                'cost_inr': item.cost_inr,
                                'details': item.details
                            }
                            for item in day.items
                        ]
                    }
                    daily_schedules_data.append(day_data)
                
                # Get optimization score if available
                optimization_score = 0
                combinations_evaluated = 0
                if isinstance(itinerary, dict):
                    optimization_score = itinerary.get('score', 0)
                    combinations_evaluated = itinerary.get('combinations_evaluated', 0)
                
                # Prepare itinerary data for storage
                itinerary_data = {
                    'destination': trip_details.get('destination_city', ''),
                    'origin': trip_details.get('origin_city', ''),
                    'departure_date': trip_details.get('departure_date', ''),
                    'return_date': trip_details.get('return_date', ''),
                    'num_days': trip_details.get('num_days', 0),
                    'total_budget_inr': total_budget,
                    'total_cost_inr': total_cost,
                    'optimization_score': optimization_score,
                    'combinations_evaluated': combinations_evaluated,
                    'daily_schedules': daily_schedules_data,
                    'query': trip_details.get('query', ''),
                    'interests': trip_details.get('interests', []),
                    'dietary_restrictions': trip_details.get('dietary_restrictions', [])
                }
                
                # Store to MongoDB
                self.history_manager.store_itinerary(user_id, itinerary_data)
                print(f"\n✅ Complete itinerary stored to MongoDB for user {user_id}")
                
            except Exception as storage_error:
                print(f"\n⚠️ Could not store itinerary to MongoDB: {storage_error}")
            
        except Exception as e:
            print(f"   ⚠️ Transport error: {e}")
            self.display_itinerary(itinerary, trip_details)
    
    def ask(self, query: str, user_id: Optional[str] = None) -> str:
        """Handle natural language queries."""

        user_id = user_id or os.getenv('DEFAULT_USER_ID', 'anonymous')
        user_context = self.get_user_context(user_id)

        if user_context:
            print(f"🧾 Loaded context for user {user_id}:")
            print(user_context)

        print("\n🧠 Understanding your request...")

        # Check if it's a trip planning request
        if any(word in query.lower() for word in ['plan', 'trip', 'itinerary', 'travel', 'visit']):
            trip_details = self.extract_trip_details(query)
            trip_details['user_id'] = user_id  # Add user_id for storage
            trip_details['query'] = query  # Add original query

            if trip_details.get('destination_city'):
                result = self.generate_itinerary(trip_details)

                # Capture itinerary output as text for storage
                import io
                import sys
                
                captured_output = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = captured_output
                
                try:
                    # Display itinerary (output goes to capture)
                    self.display_itinerary_text(result, trip_details)
                finally:
                    sys.stdout = old_stdout
                
                itinerary_response = captured_output.getvalue()
                
                # Print to actual console
                print(itinerary_response)
                
                # Save trip history entry for RAG and store conversation
                if user_id != 'anonymous':
                    trip_data = {
                        'origin_city': trip_details.get('origin_city'),
                        'destination': trip_details.get('destination_city'),
                        'departure_date': trip_details.get('departure_date'),
                        'return_date': trip_details.get('return_date'),
                        'num_days': trip_details.get('num_days'),
                        'budget_inr': trip_details.get('budget_inr'),
                        'rating': None,
                        'generated_at': datetime.now().isoformat(),
                        'query': query,
                        'result_summary': 'Itinerary generated'
                    }
                    self.history_manager.store_trip_history(user_id, trip_data)
                    # Store the complete itinerary response
                    self.history_manager.store_conversation(user_id, query, itinerary_response, trip_data)
                    # Also store as raw itinerary output
                    self.history_manager.store_itinerary_output(user_id, itinerary_response, trip_data)

                return itinerary_response
            else:
                response = "❓ I need at least a destination city. Example: 'Plan a trip to Paris from Bangalore'"
                if user_id != 'anonymous':
                    self.history_manager.store_conversation(user_id, query, response)
                return response

        response = "❓ I specialize in planning complete trip itineraries. Try: 'Plan a trip from Bangalore to Paris for 5 days'"
        if user_id != 'anonymous':
            self.history_manager.store_conversation(user_id, query, response)
        return response

    def interactive(self):
        """Interactive mode"""
        
        if not self.llm:
            print("❌ Agent not initialized. Check GOOGLE_API_KEY in .env")
            return
        
        print("\n" + "="*80)
        print("🌍 TRAVEL ITINERARY ORCHESTRATOR")
        print("="*80)
        print("\n💡 I create complete day-by-day travel itineraries!")
        print("   ✈️ Searches flights AND ground transport (taxis, trains, buses)")
        print("   💰 Automatically chooses the cheapest option")
        print("   🎯 Compares cost vs time for best value")
        print("\n📝 Commands:")
        print("   • 'generate' - Create sample 7-day Tokyo itinerary")
        print("   • 'quit' - Exit")
        print("\n📋 Examples:")
        print("   • Plan a trip from Bangalore to Paris from March 1 to March 7")
        print("   • I want to visit Mumbai for 3 days from Bangalore")
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
