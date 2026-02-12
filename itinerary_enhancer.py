"""
Itinerary Enhancer - FIXED VERSION with Proper Flight Attribute Handling
Correctly reads flight data from both optimizer and return flights
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from local_transport_agent import LocalTransportAgent, TransportOption
from currency_converter import get_converter


@dataclass
class ItineraryItem:
    """Enhanced itinerary item with all details"""
    time: str
    type: str
    name: str
    duration_minutes: int
    cost: float
    currency: str
    cost_inr: float
    details: Dict[str, Any]
    
    def __repr__(self):
        return f"{self.type}: {self.name} ({self.duration_minutes}m, INR {self.cost_inr})"


@dataclass
class EnhancedDaySchedule:
    """Day schedule with transport included"""
    day_number: int
    items: List[ItineraryItem]
    total_cost: float
    total_duration_minutes: int


class ItineraryEnhancer:
    """Add transport options between locations in itinerary"""
    
    def __init__(self, budget_conscious: bool = True):
        self.transport_agent = LocalTransportAgent()
        self.budget_conscious = budget_conscious
        self.converter = get_converter()
    
    def enhance_itinerary(self, daily_schedules: List[Any]) -> List[EnhancedDaySchedule]:
        """Add transport between locations in the itinerary"""
        enhanced_days = []
        
        for day in daily_schedules:
            enhanced_day = self._enhance_single_day(day)
            enhanced_days.append(enhanced_day)
        
        return enhanced_days
    
    def _enhance_single_day(self, day_schedule: Any) -> EnhancedDaySchedule:
        """Add transport to a single day's schedule"""
        
        enhanced_items = []
        previous_location = None
        
        for item in day_schedule.items:
            # Check if we need transport to this location
            if previous_location and self._needs_transport(previous_location, item):
                transport = self._add_transport(previous_location, item)
                if transport:
                    enhanced_items.append(transport)
            
            # Add the actual item
            enhanced_item = self._convert_to_enhanced_item(item)
            enhanced_items.append(enhanced_item)
            
            # Update previous location (only for items with coordinates)
            if self._has_location(item):
                previous_location = item
        
        # Calculate totals in INR
        total_cost = sum(item.cost_inr for item in enhanced_items)
        total_duration = sum(item.duration_minutes for item in enhanced_items)
        
        return EnhancedDaySchedule(
            day_number=day_schedule.day_number,
            items=enhanced_items,
            total_cost=round(total_cost, 2),
            total_duration_minutes=total_duration
        )
    
    def _get_item_type(self, item: Any) -> str:
        """Get item type - handles both 'type' and 'item_type' attributes"""
        if hasattr(item, 'type'):
            return item.type
        elif hasattr(item, 'item_type'):
            return item.item_type
        else:
            return 'unknown'
    
    def _needs_transport(self, from_item: Any, to_item: Any) -> bool:
        """Check if transport is needed between two items"""
        
        to_type = self._get_item_type(to_item)
        from_type = self._get_item_type(from_item)
        
        # No transport needed for accommodation (all day)
        if to_type in ['accommodation', 'flight', 'ground_transport']:
            return False
        
        # No transport from accommodation to first activity
        if from_type == 'accommodation':
            return False
        
        # Check if locations are different
        if not (self._has_location(from_item) and self._has_location(to_item)):
            return False
        
        # Calculate distance
        try:
            distance = self.transport_agent.calculate_distance(
                from_item.latitude, from_item.longitude,
                to_item.latitude, to_item.longitude
            )
        except Exception as e:
            return False
        
        # Need transport if distance > 0.3 km
        return distance > 0.3
    
    def _has_location(self, item: Any) -> bool:
        """Check if item has valid location coordinates"""
        try:
            return (hasattr(item, 'latitude') and hasattr(item, 'longitude') and
                    item.latitude != 0 and item.longitude != 0 and
                    item.latitude is not None and item.longitude is not None)
        except:
            return False
    
    def _add_transport(self, from_item: Any, to_item: Any) -> Optional[ItineraryItem]:
        """Add transport option between two items"""
        try:
            transport = self.transport_agent.suggest_transport(
                from_item, to_item, self.budget_conscious
            )
            
            cost_inr = self.converter.convert(transport.cost, transport.currency, 'INR')
            
            transport_item = ItineraryItem(
                time="",
                type="local_transport",
                name=transport.description,
                duration_minutes=transport.duration_minutes,
                cost=transport.cost,
                currency=transport.currency,
                cost_inr=cost_inr,
                details={
                    'mode': transport.mode,
                    'distance_km': transport.distance_km,
                    'from': transport.from_location,
                    'to': transport.to_location,
                    'comfort': transport.comfort_level
                }
            )
            
            return transport_item
            
        except Exception as e:
            return None
    
    def _convert_to_enhanced_item(self, item: Any) -> ItineraryItem:
        """Convert optimizer item to enhanced itinerary item"""
        
        # Get item type
        item_type = self._get_item_type(item)
        
        # Get duration
        duration = 0
        if hasattr(item, 'duration_minutes'):
            duration = item.duration_minutes
        elif hasattr(item, 'duration'):
            duration = item.duration
        
        # Get cost
        cost = 0
        if hasattr(item, 'price'):
            cost = item.price
        elif hasattr(item, 'cost'):
            cost = item.cost
        elif hasattr(item, 'average_cost'):
            cost = item.average_cost
        elif hasattr(item, 'price_per_night'):
            cost = item.price_per_night
        
        currency = getattr(item, 'currency', 'INR')
        
        # Convert cost to INR
        try:
            cost_inr = self.converter.convert(cost, currency, 'INR')
        except:
            cost_inr = cost  # Assume already in INR if conversion fails
        
        # Get time - SPECIAL HANDLING FOR FLIGHTS
        # time_str = ""
        # if item_type in ['flight', 'ground_transport']:
        #     departure_time = getattr(item, 'departure_time', '')
        #     if departure_time:
        #         if isinstance(departure_time, str) and 'T' in departure_time:
        #             try:
        #                 time_str = departure_time.split('T')[1][:5]  # "HH:MM"
        #             except:
        #                 time_str = ""
        #         else:
        #             time_str = str(departure_time)[:5] if departure_time else ""
        # else:
        #     if hasattr(item, 'time'):
        #         time_str = item.time
        #     elif hasattr(item, 'time_str'):
        #         time_str = item.time_str
        #     elif hasattr(item, 'start_time'):
        #         start = item.start_time
        #         if isinstance(start, int):
        #             hours = start // 60
        #             mins = start % 60
        #             time_str = f"{hours:02d}:{mins:02d}"
        #         else:
        #             time_str = str(start)

        # Get time - IMPROVED TIME EXTRACTION
        time_str = ""
        if item_type in ['flight', 'ground_transport']:
            # Try to get departure_time
            departure_time = getattr(item, 'departure_time', None)
            
            if departure_time:
                if isinstance(departure_time, str):
                    if 'T' in departure_time:
                        # ISO format: "2026-03-01T10:30:00"
                        try:
                            time_str = departure_time.split('T')[1][:5]  # Extract "10:30"
                        except:
                            time_str = ""
                    elif ':' in departure_time and len(departure_time) <= 8:
                        # Already in time format like "10:30" or "10:30:00"
                        time_str = departure_time[:5]
                    else:
                        # Try to extract first 5 chars
                        time_str = str(departure_time)[:5] if len(departure_time) >= 5 else ""
                else:
                    # Not a string - convert and try
                    dep_str = str(departure_time)
                    if ':' in dep_str:
                        time_str = dep_str[:5]
            
            # If still no time, try alternate attributes
            if not time_str:
                # Try 'time' attribute
                if hasattr(item, 'time') and item.time:
                    time_str = str(item.time)[:5]
                # Try 'start_time' (might be in minutes)
                elif hasattr(item, 'start_time') and item.start_time is not None:
                    start = item.start_time
                    if isinstance(start, int):
                        hours = start // 60
                        mins = start % 60
                        time_str = f"{hours:02d}:{mins:02d}"
                    else:
                        time_str = str(start)[:5]
            
            # Debug output if time still not found (remove after fixing)
            if not time_str:
                print(f"\n      ⚠️ DEBUG: No time found for {item_type}")
                if hasattr(item, 'name'):
                    print(f"         Item: {getattr(item, 'name', 'Unknown')}")
                print(f"         departure_time value: {departure_time}")
                print(f"         departure_time type: {type(departure_time)}")
                # Check all time-related attributes
                time_attrs = ['time', 'start_time', 'departure', 'depart_time']
                for attr in time_attrs:
                    if hasattr(item, attr):
                        print(f"         {attr}: {getattr(item, attr)}")

        else:
            # Normal time extraction for other items (restaurants, activities, etc.)
            if hasattr(item, 'time') and item.time:
                time_str = str(item.time)
            elif hasattr(item, 'time_str') and item.time_str:
                time_str = str(item.time_str)
            elif hasattr(item, 'start_time') and item.start_time is not None:
                start = item.start_time
                if isinstance(start, int):
                    hours = start // 60
                    mins = start % 60
                    time_str = f"{hours:02d}:{mins:02d}"
                else:
                    time_str = str(start)

        
        # ===================================================================
        # FLIGHT HANDLING - FIXED TO READ ATTRIBUTES CORRECTLY
        # ===================================================================
        if item_type == 'flight':
            # Try to get carrier - check multiple possible attribute names
            carrier = None
            if hasattr(item, 'carrier'):
                carrier = item.carrier
            elif hasattr(item, 'carrier_code'):
                carrier = item.carrier_code
            elif hasattr(item, 'airline'):
                carrier = item.airline
            
            # If carrier is still None, try getting from name
            if not carrier and hasattr(item, 'name'):
                # Name might be like "AI BLR-CDG"
                parts = str(item.name).split()
                if parts:
                    carrier = parts[0]
            
            # Final fallback
            if not carrier:
                carrier = 'Unknown'
            
            # Try to get origin
            origin = None
            if hasattr(item, 'origin'):
                origin = item.origin
            elif hasattr(item, 'origin_code'):
                origin = item.origin_code
            elif hasattr(item, 'departure_airport'):
                origin = item.departure_airport
            
            # Try to get destination
            destination = None
            if hasattr(item, 'destination'):
                destination = item.destination
            elif hasattr(item, 'destination_code'):
                destination = item.destination_code
            elif hasattr(item, 'arrival_airport'):
                destination = item.arrival_airport
            
            # If origin/destination still None, try parsing from name
            if (not origin or not destination) and hasattr(item, 'name'):
                # Name might be like "AI BLR-CDG" or "Air India BLR-DEL"
                name_str = str(item.name)
                if '-' in name_str:
                    # Extract the route part
                    for part in name_str.split():
                        if '-' in part and len(part) <= 10:  # Like "BLR-CDG"
                            route_parts = part.split('-')
                            if len(route_parts) == 2:
                                if not origin:
                                    origin = route_parts[0].strip()
                                if not destination:
                                    destination = route_parts[1].strip()
                            break
            
            # Final fallbacks
            if not origin:
                origin = '???'
            if not destination:
                destination = '???'
            
            # Check if return flight
            is_return = getattr(item, 'is_return', False)
            
            # Get flight number/ID
            flight_id = ''
            if hasattr(item, 'flight_id'):
                flight_id = item.flight_id
            elif hasattr(item, 'flight_number'):
                flight_id = item.flight_number
            
            # Get segments
            segments = getattr(item, 'segments', 1)
            
            # Get departure and arrival times
            departure = getattr(item, 'departure_time', '')
            arrival = getattr(item, 'arrival_time', '')
            
            # Build details dict
            details = {
                'carrier': carrier,
                'origin': origin,
                'destination': destination,
                'flight_number': flight_id,
                'departure': departure,
                'arrival': arrival,
                'is_return': is_return,
                'segments': segments
            }
            
            # Create descriptive name
            return_label = " (Return)" if is_return else ""
            name = f"{carrier} {origin}→{destination}{return_label}"
        
        # ===================================================================
        # GROUND TRANSPORT HANDLING
        # ===================================================================
        elif item_type == 'ground_transport':
            provider = getattr(item, 'provider', 'Unknown')
            origin = getattr(item, 'origin', '???')
            destination = getattr(item, 'destination', '???')
            is_return = getattr(item, 'is_return', False)
            
            details = {
                'provider': provider,
                'type': getattr(item, 'transport_type', 'Unknown'),
                'origin': origin,
                'destination': destination,
                'is_return': is_return
            }
            
            return_label = " (Return)" if is_return else ""
            name = f"{provider} {origin}→{destination}{return_label}"
        
        # ===================================================================
        # OTHER ITEM TYPES
        # ===================================================================
        else:
            name = getattr(item, 'name', 'Unknown')
            details = {}
            
            if item_type == 'restaurant':
                details = {
                    'cuisine': getattr(item, 'cuisine', getattr(item, 'cuisine_type', 'Unknown')),
                    'rating': getattr(item, 'rating', 0),
                    'address': getattr(item, 'address', '')
                }
            elif item_type == 'activity':
                details = {
                    'category': getattr(item, 'category', 'Unknown'),
                    'rating': getattr(item, 'rating', 0),
                    'duration': duration,
                    'address': getattr(item, 'address', '')
                }
            elif item_type == 'accommodation':
                details = {
                    'type': getattr(item, 'accommodation_type', 'Hotel'),
                    'rating': getattr(item, 'rating', 0),
                    'amenities': getattr(item, 'amenities', [])
                }
        
        return ItineraryItem(
            time=time_str,
            type=item_type,
            name=name,
            duration_minutes=duration,
            cost=cost,
            currency=currency,
            cost_inr=cost_inr,
            details=details
        )


def display_enhanced_itinerary(enhanced_days: List[EnhancedDaySchedule],
                               total_budget: float = 0):
    """Display enhanced itinerary with all costs in INR"""
    
    print("\n" + "="*80)
    print("📋 YOUR ENHANCED ITINERARY WITH LOCAL TRANSPORT")
    print("="*80)
    
    total_cost = sum(day.total_cost for day in enhanced_days)
    
    print(f"💰 Total Cost: ₹{total_cost:,.2f}")
    print(f"📅 Duration: {len(enhanced_days)} days")
    if total_budget > 0:
        remaining = total_budget - total_cost
        if remaining >= 0:
            print(f"💵 Budget Remaining: ₹{remaining:,.2f}")
        else:
            print(f"⚠️  Over Budget: ₹{abs(remaining):,.2f}")
    
    for day in enhanced_days:
        print("\n" + "─"*80)
        print(f"📅 DAY {day.day_number}")
        print("─"*80)
        
        current_time = None
        
        for item in day.items:
            icons = {
                'accommodation': '🏨',
                'restaurant': '🍽️',
                'activity': '🎭',
                'local_transport': '🚗',
                'flight': '✈️',
                'ground_transport': '🚂'
            }
            
            icon = icons.get(item.type, '📍')
            
            # Calculate time display
            if item.type == 'accommodation':
                time_str = "[All day]"
            elif item.type == 'local_transport':
                if current_time:
                    time_str = f"[{current_time}]"
                    current_time = _add_minutes(current_time, item.duration_minutes)
                else:
                    time_str = "[Travel]"
            else:
                if item.time:
                    time_str = f"[{item.time}]"
                    current_time = item.time
                elif current_time:
                    time_str = f"[{current_time}]"
                else:
                    time_str = "[--:--]"
                
                if current_time and item.duration_minutes > 0 and item.type not in ['flight', 'ground_transport']:
                    current_time = _add_minutes(current_time, item.duration_minutes)
            
            # Format duration
            if item.duration_minutes > 0:
                hrs = item.duration_minutes // 60
                mins = item.duration_minutes % 60
                duration_str = f"({hrs}h {mins}m)" if hrs > 0 else f"({mins}m)"
            else:
                duration_str = ""
            
            # Display item
            print(f"   {icon} {time_str} {item.name} {duration_str}")
            
            # Show details based on type
            if item.type == 'local_transport':
                details = item.details
                if item.currency != 'INR':
                    print(f"      {details['mode'].capitalize()} • {details['distance_km']} km • ₹{item.cost_inr:.2f} (≈{item.currency} {item.cost:.2f})")
                else:
                    print(f"      {details['mode'].capitalize()} • {details['distance_km']} km • ₹{item.cost_inr:.2f}")
            
            elif item.type == 'flight':
                details = item.details
                print(f"      {details['carrier']} Flight {details.get('flight_number', '')}")
                print(f"      Route: {details['origin']} → {details['destination']}")
                if details.get('is_return'):
                    print(f"      🔄 Return Flight")
                if details.get('segments', 1) > 1:
                    print(f"      ⚠️  {details['segments']} stops")
                if item.currency != 'INR':
                    print(f"      Cost: ₹{item.cost_inr:,.2f} (≈{item.currency} {item.cost:,.2f})")
                else:
                    print(f"      Cost: ₹{item.cost_inr:,.2f}")
            
            elif item.type == 'ground_transport':
                details = item.details
                print(f"      {details['provider']} ({details['type']})")
                print(f"      Route: {details['origin']} → {details['destination']}")
                if details.get('is_return'):
                    print(f"      🔄 Return Journey")
                if item.currency != 'INR':
                    print(f"      Cost: ₹{item.cost_inr:,.2f} (≈{item.currency} {item.cost:,.2f})")
                else:
                    print(f"      Cost: ₹{item.cost_inr:,.2f}")
            
            else:
                if item.cost_inr > 0:
                    if item.currency != 'INR':
                        print(f"      Cost: ₹{item.cost_inr:,.2f} (≈{item.currency} {item.cost:.2f})")
                    else:
                        print(f"      Cost: ₹{item.cost_inr:,.2f}")
                
                if item.type == 'restaurant' and 'cuisine' in item.details:
                    print(f"      Cuisine: {item.details['cuisine']}")
                    if item.details.get('rating', 0) > 0:
                        print(f"      Rating: {item.details['rating']}⭐")
                elif item.type == 'activity' and 'category' in item.details:
                    print(f"      Category: {item.details['category']}")
                    if item.details.get('rating', 0) > 0:
                        print(f"      Rating: {item.details['rating']}⭐")
                elif item.type == 'accommodation':
                    if item.details.get('rating', 0) > 0:
                        print(f"      Rating: {item.details['rating']}⭐")
                    acc_type = item.details.get('type', 'Hotel')
                    print(f"      Type: {acc_type}")
        
        print(f"\n   💵 Day {day.day_number} Total: ₹{day.total_cost:,.2f}")
    
    print("\n" + "="*80)
    print(f"💰 GRAND TOTAL: ₹{total_cost:,.2f}")
    print("="*80)
    print("✅ Itinerary complete!")
    print("="*80)


def _add_minutes(time_str: str, minutes: int) -> str:
    """Add minutes to a time string (HH:MM)"""
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        new_time = time_obj + timedelta(minutes=minutes)
        return new_time.strftime("%H:%M")
    except:
        return time_str


if __name__ == "__main__":
    print("Testing Itinerary Enhancer...")
    print("\n✅ Enhancer initialized with proper flight attribute handling")
    print("To use: call enhance_itinerary(daily_schedules) after optimization")