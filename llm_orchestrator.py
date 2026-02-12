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
from ground_transport_agent import GroundTransportAgent, TransportOption
from optimizer import ItineraryOptimizer
from trend_analyzer import TrendAnalyzer
from user_profile import create_sample_profile, UserProfile, TripDates
from currency_converter import CurrencyConverter, convert_to_inr
# Add to imports at top of file
from itinerary_enhancer import ItineraryEnhancer, display_enhanced_itinerary

from datetime import datetime, timedelta
from dataclasses import dataclass
import random

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
        self.ground_transport_agent = GroundTransportAgent()
        self.hotel_agent = AccommodationAgent()
        self.restaurant_agent = RestaurantAgent()
        self.activity_agent = ActivityAgent()
        self.trend_analyzer = TrendAnalyzer()
        self.currency_converter = CurrencyConverter()
        
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
        
        # [2/6] Search flights AND ground transport
        print(f"\n{'='*80}")
        print("[2/6] ✈️🚕 SEARCHING FLIGHTS & GROUND TRANSPORT")
        print("="*80)
        print(f"   Route: {origin_code} → {dest_code}")
        print(f"   Outbound: {departure_date}")
        
        # Calculate distance to determine if ground transport is viable
        distance_km = self.ground_transport_agent.calculate_distance(origin, destination)
        
        # Search for flights
        print(f"\n   ✈️ Searching flights...")
        flights = self.flight_agent.search_flights(
            origin=origin_code,
            destination=dest_code,
            departure_date=departure_date,
            max_results=10
        )
        
        if flights:
            print(f"   ✅ Found {len(flights)} flights")
            cheapest_flight = min(flights, key=lambda f: self.currency_converter.convert(f.price, f.currency, 'INR'))
            cheapest_flight_inr = self.currency_converter.convert(cheapest_flight.price, cheapest_flight.currency, 'INR')
            print(f"   💰 Cheapest flight: INR {cheapest_flight_inr:,.0f}")
        else:
            print("   ⚠️ No flights found")
            flights = []
            cheapest_flight_inr = float('inf')
        
        # Search for ground transport (if distance is reasonable)
        ground_transport_options = []
        if distance_km <= 1000:  # Only search ground transport for <= 1000km
            print(f"\n   🚕 Searching ground transport (distance: {distance_km:.0f}km)...")
            ground_transport_options = self.ground_transport_agent.search_transport(
                origin=origin,
                destination=destination,
                transport_types=['taxi', 'train', 'bus'],
                max_results=6
            )
            
            if ground_transport_options:
                print(f"   ✅ Found {len(ground_transport_options)} ground transport options")
                cheapest_ground = min(ground_transport_options, key=lambda t: t.price)
                print(f"   💰 Cheapest ground: INR {cheapest_ground.price:,.0f} ({cheapest_ground.type})")
                
                # Compare with flight
                if flights:
                    comparison = self.ground_transport_agent.compare_with_flight(
                        cheapest_ground, 
                        cheapest_flight_inr
                    )
                    
                    print(f"\n   📊 COMPARISON:")
                    print(f"   {'─'*70}")
                    if comparison['recommendation'] == 'ground_transport':
                        print(f"   💡 RECOMMENDED: Ground Transport ({cheapest_ground.type})")
                        print(f"   ✅ Save INR {comparison['savings']:,.0f} ({comparison['savings_pct']:.0f}%)")
                        print(f"   ⏱️  Extra time: {comparison['time_diff_minutes'] // 60}h {comparison['time_diff_minutes'] % 60}m")
                        print(f"   📝 {comparison['reason']}")
                    else:
                        print(f"   💡 RECOMMENDED: Flight")
                        print(f"   ⏱️  Save time: {abs(comparison['time_diff_minutes']) // 60}h {abs(comparison['time_diff_minutes']) % 60}m")
                        print(f"   📝 {comparison['reason']}")
                    print(f"   {'─'*70}")
        else:
            print(f"\n   ℹ️  Distance too far ({distance_km:.0f}km) - skipping ground transport")
        
        # Show top options from each category
        print(f"\n   📋 TOP OPTIONS:")
        print(f"   {'─'*70}")
        
        if flights:
            print(f"   ✈️ FLIGHTS:")
            for i, f in enumerate(flights[:3], 1):
                hrs = f.duration_minutes // 60
                mins = f.duration_minutes % 60
                original_price = f"{f.currency} {f.price:,.0f}"
                inr_price = self.currency_converter.convert(f.price, f.currency, 'INR')
                print(f"      {i}. {f.carrier} {f.flight_id}: {original_price} (≈ INR {inr_price:,.0f}) ({hrs}h {mins}m)")
        
        if ground_transport_options:
            print(f"\n   🚕 GROUND TRANSPORT:")
            for i, t in enumerate(ground_transport_options[:3], 1):
                hrs = t.duration_minutes // 60
                mins = t.duration_minutes % 60
                print(f"      {i}. {t.type.title()} ({t.provider}): INR {t.price:,.0f} ({hrs}h {mins}m)")
        
        # Combine all transport options for comparison
        all_transport_options = flights + ground_transport_options
        
        if not all_transport_options:
            print("\n   ⚠️ No transport options found (will use mock data)")
        
        # Determine which transport type to use based on recommendation
        selected_transport = []
        
        if ground_transport_options and flights:
            # We have both options - use the recommendation
            cheapest_ground = min(ground_transport_options, key=lambda t: t.price)
            comparison = self.ground_transport_agent.compare_with_flight(
                cheapest_ground, 
                cheapest_flight_inr
            )
            
            if comparison['recommendation'] == 'ground_transport':
                # Use ground transport options only
                selected_transport = ground_transport_options
                print(f"\n   ✅ USING GROUND TRANSPORT for optimization (cheaper)")
            else:
                # Use flight options only
                selected_transport = flights
                print(f"\n   ✅ USING FLIGHTS for optimization (better time value)")
        
        elif ground_transport_options:
            # Only ground transport available
            selected_transport = ground_transport_options
            print(f"\n   ✅ USING GROUND TRANSPORT (only option)")
        
        elif flights:
            # Only flights available
            selected_transport = flights
            print(f"\n   ✅ USING FLIGHTS (only option)")
        
        else:
            selected_transport = []
            print(f"\n   ❌ No transport options available")
        
        
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
        
        # Convert transport options (only the selected type)
        transport_converted = []
        for transport in selected_transport:
            if hasattr(transport, 'price') and hasattr(transport, 'currency'):
                # Check if it's a flight or ground transport
                if hasattr(transport, 'carrier'):  # It's a flight
                    converted_price = self.currency_converter.convert(
                        transport.price, 
                        transport.currency, 
                        base_currency
                    )
                    transport.price = converted_price
                    transport.currency = base_currency
                else:  # It's ground transport (already in INR)
                    pass  # Already in INR
                
                transport_converted.append(transport)
        
        print(f"   ✅ Using {len(transport_converted)} {transport_converted[0].item_type if transport_converted else 'transport'} options")
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
        
        # Pass transport options (flights + ground) as 'flights' parameter
        optimized = optimizer.optimize_itinerary(
            flights=transport_converted,  # This now includes both flights and ground transport
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
        
        # Add return journey to last day
        result = self.add_return_journey(optimized, trip_details)
        # Display day-by-day itinerary
        self.display_itinerary_with_transport(result, trip_details)

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
                elif hasattr(item, 'start_time') and item.start_time > 0:
                    hours = item.start_time // 60
                    mins = item.start_time % 60
                    time_str = f"{hours:02d}:{mins:02d}"
                
                # Duration
                duration_str = ""
                if hasattr(item, 'duration'):
                    hrs = item.duration // 60
                    mins = item.duration % 60
                    if hrs > 0 or mins > 0:
                        duration_str = f" ({hrs}h {mins}m)"
                elif hasattr(item, 'duration_minutes') and item.duration_minutes:
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
                if item_type == 'flight':
                    icon = "✈️"
                elif item_type == 'ground_transport':
                    icon = "🚂"  # Default, will be refined below
                elif 'hotel' in item_type.lower() or 'accommodation' in item_type.lower():
                    icon = "🏨"
                elif 'restaurant' in item_type.lower():
                    icon = "🍽️"
                elif 'activity' in item_type.lower():
                    icon = "🎭"
                
                # Refine ground transport icon based on name/type
                if item_type == 'ground_transport' and hasattr(item, 'name'):
                    name_lower = item.name.lower()
                    if 'taxi' in name_lower or 'uber' in name_lower or 'ola' in name_lower:
                        icon = "🚕"
                    elif 'train' in name_lower or 'railway' in name_lower:
                        icon = "🚂"
                    elif 'bus' in name_lower:
                        icon = "🚌"
                    elif 'car' in name_lower:
                        icon = "🚗"
                
                print(f"\n   {icon} [{time_str}] {name}{duration_str}")
                print(f"      Type: {item_type}")
                
                # Show additional transport details if available
                if item_type in ['flight', 'ground_transport']:
                    # For ItineraryItem from optimizer, details are in name
                    # Name format: "Carrier ORIGIN-DEST" or "Type (Provider)"
                    pass  # Details already in name
                
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
                                date: str, origin_city: str = None, 
                                destination_city: str = None):
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
            def name(self):
                return f"{self.carrier} {self.origin}-{self.destination} (Return)"
            
            @property
            def duration(self):
                return self.duration_minutes
        
        flight = ReturnFlight(
            flight_id=f"RET{random.randint(1000, 9999)}",
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


    # def add_return_journey(self, itinerary, trip_details: dict):
    #     """
    #     Add return flight/transport to the last day of itinerary
    #     Automatically searches for return options from destination back to origin
    #     """
        
    #     print("\n" + "="*80)
    #     print("🔄 ADDING RETURN JOURNEY")
    #     print("="*80)
        
    #     # Extract trip details
    #     origin = trip_details.get('origin_city', 'Bangalore')
    #     destination = trip_details.get('destination_city', 'Paris')
    #     origin_code = trip_details.get('origin_code', 'BLR')
    #     destination_code = trip_details.get('destination_code', 'CDG')
    #     departure_date = trip_details.get('departure_date', '2026-03-01')
    #     num_days = trip_details.get('num_days', 7)
        
    #     # Calculate return date (last day)
    #     try:
    #         dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
    #         return_date = (dep_date + timedelta(days=num_days - 1)).strftime('%Y-%m-%d')
    #     except Exception as e:
    #         print(f"   ⚠️ Date parsing error, using last day")
    #         return_date = departure_date
        
    #     print(f"   🛬 Return route: {destination} ({destination_code}) → {origin} ({origin_code})")
    #     print(f"   📅 Return date: {return_date}")
        
    #     # Try to search for return flight
    #     return_flight = None
    #     try:
    #         print(f"   🔍 Searching return flights...")
    #         return_flights = self.flight_agent.search_flights(
    #             origin=destination_code,
    #             destination=origin_code,
    #             departure_date=return_date,
    #             adults=1,
    #             max_results=5
    #         )
            
    #         if return_flights and len(return_flights) > 0:
    #             # Select cheapest return flight
    #             return_flight = min(return_flights, key=lambda x: x.price)
    #             print(f"   ✅ Found {len(return_flights)} return flights")
    #             print(f"   ✓ Selected: {return_flight.carrier} flight")
    #             print(f"   💰 Cost: {return_flight.currency} {return_flight.price:,.2f}")
    #         else:
    #             print(f"   ℹ️ No return flights from API, generating mock")
    #             return_flight = self._create_mock_return_flight(
    #                 destination_code, origin_code, return_date, destination, origin
    #             )
        
    #     except Exception as e:
    #         print(f"   ⚠️ Return flight search error: {str(e)[:100]}")
    #         print(f"   ℹ️ Generating mock return flight")
    #         return_flight = self._create_mock_return_flight(
    #             destination_code, origin_code, return_date, destination, origin
    #         )
        
    #     if not return_flight:
    #         print(f"   ❌ Could not add return journey")
    #         return itinerary
        
    #     # Add return flight to itinerary
    #     added = False
    #     try:
    #         # Handle dict format with 'itinerary' key
    #         if isinstance(itinerary, dict) and 'itinerary' in itinerary:
    #             last_day_idx = num_days - 1  # 0-indexed
                
    #             # Ensure last day exists in itinerary
    #             if last_day_idx not in itinerary['itinerary']:
    #                 itinerary['itinerary'][last_day_idx] = []
                
    #             # Add return flight at start of last day (morning departure)
    #             itinerary['itinerary'][last_day_idx].insert(0, return_flight)
                
    #             # Update total cost
    #             if 'total_cost' in itinerary:
    #                 itinerary['total_cost'] += return_flight.price
                
    #             added = True
    #             print(f"   ✅ Return flight added to Day {num_days}")
            
    #         # Handle daily_schedules format
    #         elif hasattr(itinerary, 'daily_schedules') and itinerary.daily_schedules:
    #             last_day_schedule = itinerary.daily_schedules[-1]
                
    #             # Ensure items list exists
    #             if not hasattr(last_day_schedule, 'items'):
    #                 last_day_schedule.items = []
                
    #             # Add to beginning of last day
    #             last_day_schedule.items.insert(0, return_flight)
                
    #             added = True
    #             print(f"   ✅ Return flight added to Day {last_day_schedule.day_number}")
            
    #         else:
    #             print(f"   ⚠️ Unknown itinerary format")
    #             print(f"   Type: {type(itinerary)}")
    #             if isinstance(itinerary, dict):
    #                 print(f"   Keys: {list(itinerary.keys())}")
        
    #     except Exception as e:
    #         print(f"   ❌ Error adding return flight: {e}")
    #         import traceback
    #         traceback.print_exc()
        
    #     if added:
    #         print(f"   🎉 Return journey successfully added!")
        
    #     return itinerary


    # def _create_mock_return_flight(self, origin_code: str, destination_code: str, 
    #                             date: str, origin_city: str = None, 
    #                             destination_city: str = None):
    #     """
    #     Create a realistic mock return flight
        
    #     Args:
    #         origin_code: Airport code departing from (e.g., 'CDG')
    #         destination_code: Airport code arriving at (e.g., 'BLR')
    #         date: Departure date (YYYY-MM-DD)
    #         origin_city: Origin city name
    #         destination_city: Destination city name
    #     """
        
    #     # Airlines operating international routes
    #     carriers = [
    #         ('AI', 'Air India'),
    #         ('6E', 'IndiGo'),
    #         ('UK', 'Vistara'),
    #         ('EK', 'Emirates'),
    #         ('QR', 'Qatar Airways'),
    #         ('SQ', 'Singapore Airlines'),
    #         ('LH', 'Lufthansa'),
    #         ('BA', 'British Airways')
    #     ]
        
    #     carrier_code, carrier_name = random.choice(carriers)
        
    #     # Generate realistic departure/arrival times
    #     try:
    #         dep_dt = datetime.strptime(date, '%Y-%m-%d')
            
    #         # Morning/afternoon departure (6am - 4pm)
    #         dep_hour = random.randint(6, 16)
    #         dep_minute = random.choice([0, 15, 30, 45])
    #         dep_time = dep_dt.replace(hour=dep_hour, minute=dep_minute)
            
    #         # Flight duration varies by route (3-12 hours for international)
    #         duration_hours = random.randint(6, 12)
    #         duration_minutes = random.randint(0, 59)
    #         total_duration_mins = duration_hours * 60 + duration_minutes
            
    #         arr_time = dep_time + timedelta(minutes=total_duration_mins)
            
    #         dep_time_str = dep_time.isoformat()
    #         arr_time_str = arr_time.isoformat()
            
    #     except Exception as e:
    #         print(f"      ⚠️ Date error: {e}")
    #         dep_time_str = f"{date}T10:00:00"
    #         arr_time_str = f"{date}T18:00:00"
    #         total_duration_mins = 480
        
    #     # Realistic pricing (return flights often slightly cheaper than one-way)
    #     # International: 25k-50k INR
    #     # Domestic: 3k-10k INR
    #     is_international = origin_code != destination_code[:2]
        
    #     if is_international:
    #         base_price = random.uniform(28000, 48000)
    #     else:
    #         base_price = random.uniform(3000, 10000)
        
    #     price = round(base_price, 2)
        
    #     # Create return flight object matching FlightOption structure
    #     @dataclass
    #     class ReturnFlight:
    #         flight_id: str
    #         origin: str
    #         destination: str
    #         departure_time: str
    #         arrival_time: str
    #         duration_minutes: int
    #         price: float
    #         currency: str
    #         carrier: str
    #         segments: int
    #         class_type: str
    #         reliability_score: float
    #         available_seats: int
    #         item_type: str
    #         is_return: bool
            
    #         @property
    #         def name(self):
    #             """Display name for itinerary"""
    #             return f"{self.carrier} {self.origin}-{self.destination} (Return)"
            
    #         @property
    #         def duration(self):
    #             """Duration in minutes for compatibility"""
    #             return self.duration_minutes
        
    #     flight = ReturnFlight(
    #         flight_id=f"RET{random.randint(1000, 9999)}",
    #         origin=origin_code,
    #         destination=destination_code,
    #         departure_time=dep_time_str,
    #         arrival_time=arr_time_str,
    #         duration_minutes=total_duration_mins,
    #         price=price,
    #         currency='INR',
    #         carrier=carrier_code,
    #         segments=random.randint(1, 2),
    #         class_type='economy',
    #         reliability_score=random.uniform(0.85, 0.95),
    #         available_seats=random.randint(10, 50),
    #         item_type='flight',
    #         is_return=True
    #     )
        
    #     hrs = total_duration_mins // 60
    #     mins = total_duration_mins % 60
    #     print(f"   📝 Generated: {carrier_code} {origin_code}→{destination_code} | "
    #         f"{hrs}h {mins}m | INR {price:,.2f}")
        
    #     return flight


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
        
        print("\n🚗 Adding local transport between locations...")
        
        # Handle dict format from optimizer
        daily_schedules = None
        
        # Try to extract daily schedules
        if hasattr(itinerary, 'daily_schedules'):
            daily_schedules = itinerary.daily_schedules
        elif isinstance(itinerary, dict) and 'itinerary' in itinerary:
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
            
            total_budget = trip_details.get('budget', 0)
            if hasattr(self, 'user_profile') and hasattr(self.user_profile, 'budget'):
                total_budget = self.user_profile.budget
            
            display_enhanced_itinerary(enhanced, total_budget=total_budget)
            
        except Exception as e:
            print(f"   ⚠️ Transport error: {e}")
            self.display_itinerary(itinerary, trip_details)
    
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