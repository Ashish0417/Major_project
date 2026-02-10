# """
# Itinerary Enhancer - Adds Local Transport Between Locations
# Takes an optimized itinerary and inserts transport options
# """

# from typing import List, Dict, Any, Optional
# from dataclasses import dataclass
# from datetime import datetime, timedelta
# from local_transport_agent import LocalTransportAgent, TransportOption


# @dataclass
# class ItineraryItem:
#     """Enhanced itinerary item with all details"""
#     time: str
#     type: str  # accommodation, restaurant, activity, local_transport
#     name: str
#     duration_minutes: int
#     cost: float
#     currency: str
#     details: Dict[str, Any]
    
#     def __repr__(self):
#         return f"{self.type}: {self.name} ({self.duration_minutes}m, {self.currency} {self.cost})"


# @dataclass
# class EnhancedDaySchedule:
#     """Day schedule with transport included"""
#     day_number: int
#     items: List[ItineraryItem]
#     total_cost: float
#     total_duration_minutes: int


# class ItineraryEnhancer:
#     """Add transport options between locations in itinerary"""
    
#     def __init__(self, budget_conscious: bool = True):
#         """
#         Initialize enhancer
        
#         Args:
#             budget_conscious: If True, prefer cheaper transport options
#         """
#         self.transport_agent = LocalTransportAgent()
#         self.budget_conscious = budget_conscious
    
#     def enhance_itinerary(self, daily_schedules: List[Any]) -> List[EnhancedDaySchedule]:
#         """
#         Add transport between locations in the itinerary
        
#         Args:
#             daily_schedules: List of DaySchedule objects from optimizer
            
#         Returns:
#             List of EnhancedDaySchedule with transport inserted
#         """
#         enhanced_days = []
        
#         for day in daily_schedules:
#             enhanced_day = self._enhance_single_day(day)
#             enhanced_days.append(enhanced_day)
        
#         return enhanced_days
    
#     def _enhance_single_day(self, day_schedule: Any) -> EnhancedDaySchedule:
#         """Add transport to a single day's schedule"""
        
#         enhanced_items = []
#         previous_location = None
        
#         for item in day_schedule.items:
#             # Check if we need transport to this location
#             if previous_location and self._needs_transport(previous_location, item):
#                 transport = self._add_transport(previous_location, item)
#                 if transport:
#                     enhanced_items.append(transport)
            
#             # Add the actual item
#             enhanced_item = self._convert_to_enhanced_item(item)
#             enhanced_items.append(enhanced_item)
            
#             # Update previous location (only for items with coordinates)
#             if self._has_location(item):
#                 previous_location = item
        
#         # Calculate totals
#         total_cost = sum(item.cost for item in enhanced_items)
#         total_duration = sum(item.duration_minutes for item in enhanced_items)
        
#         return EnhancedDaySchedule(
#             day_number=day_schedule.day_number,
#             items=enhanced_items,
#             total_cost=round(total_cost, 2),
#             total_duration_minutes=total_duration
#         )
    
#     def _needs_transport(self, from_item: Any, to_item: Any) -> bool:
#         """Check if transport is needed between two items"""
        
#         # No transport needed for accommodation (all day)
#         if to_item.type in ['accommodation', 'flight', 'ground_transport']:
#             return False
        
#         # No transport from accommodation to first activity (assume walking to lobby)
#         if from_item.type == 'accommodation':
#             return False
        
#         # Check if locations are different
#         if not (self._has_location(from_item) and self._has_location(to_item)):
#             return False
        
#         # Calculate distance
#         distance = self.transport_agent.calculate_distance(
#             from_item.latitude, from_item.longitude,
#             to_item.latitude, to_item.longitude
#         )
        
#         # Need transport if distance > 0.3 km (300 meters)
#         return distance > 0.3
    
#     def _has_location(self, item: Any) -> bool:
#         """Check if item has valid location coordinates"""
#         return (hasattr(item, 'latitude') and hasattr(item, 'longitude') and
#                 item.latitude != 0 and item.longitude != 0)
    
#     def _add_transport(self, from_item: Any, to_item: Any) -> Optional[ItineraryItem]:
#         """Add transport option between two items"""
#         try:
#             transport = self.transport_agent.suggest_transport(
#                 from_item, to_item, self.budget_conscious
#             )
            
#             # Convert to ItineraryItem
#             transport_item = ItineraryItem(
#                 time="",  # Will be calculated when displaying
#                 type="local_transport",
#                 name=transport.description,
#                 duration_minutes=transport.duration_minutes,
#                 cost=transport.cost,
#                 currency=transport.currency,
#                 details={
#                     'mode': transport.mode,
#                     'distance_km': transport.distance_km,
#                     'from': transport.from_location,
#                     'to': transport.to_location,
#                     'comfort': transport.comfort_level
#                 }
#             )
            
#             return transport_item
            
#         except Exception as e:
#             print(f"   ⚠️ Could not add transport: {e}")
#             return None
    
#     def _convert_to_enhanced_item(self, item: Any) -> ItineraryItem:
#         """Convert optimizer item to enhanced itinerary item"""
        
#         # Get basic info
#         item_type = item.type
#         name = item.name
#         duration = getattr(item, 'duration_minutes', 0)
#         cost = getattr(item, 'price', getattr(item, 'cost', getattr(item, 'average_cost', 0)))
#         currency = getattr(item, 'currency', 'INR')
        
#         # Build details dict
#         details = {}
        
#         if item_type == 'restaurant':
#             details = {
#                 'cuisine': getattr(item, 'cuisine', 'Unknown'),
#                 'rating': getattr(item, 'rating', 0),
#                 'address': getattr(item, 'address', '')
#             }
#         elif item_type == 'activity':
#             details = {
#                 'category': getattr(item, 'category', 'Unknown'),
#                 'rating': getattr(item, 'rating', 0),
#                 'duration': duration,
#                 'address': getattr(item, 'address', '')
#             }
#         elif item_type == 'accommodation':
#             details = {
#                 'type': getattr(item, 'accommodation_type', 'Hotel'),
#                 'rating': getattr(item, 'rating', 0),
#                 'amenities': getattr(item, 'amenities', [])
#             }
#         elif item_type == 'flight':
#             details = {
#                 'carrier': getattr(item, 'carrier', 'Unknown'),
#                 'flight_number': getattr(item, 'flight_id', ''),
#                 'departure': getattr(item, 'departure_time', ''),
#                 'arrival': getattr(item, 'arrival_time', '')
#             }
        
#         return ItineraryItem(
#             time=getattr(item, 'time', ''),
#             type=item_type,
#             name=name,
#             duration_minutes=duration,
#             cost=cost,
#             currency=currency,
#             details=details
#         )


# def display_enhanced_itinerary(enhanced_days: List[EnhancedDaySchedule],
#                                total_budget: float = 0):
#     """
#     Display enhanced itinerary with transport included
    
#     Args:
#         enhanced_days: List of EnhancedDaySchedule
#         total_budget: Total trip budget
#     """
    
#     print("\n" + "="*80)
#     print("📋 YOUR ENHANCED ITINERARY WITH LOCAL TRANSPORT")
#     print("="*80)
    
#     total_cost = sum(day.total_cost for day in enhanced_days)
    
#     print(f"💰 Total Cost: INR {total_cost:,.2f}")
#     print(f"📅 Duration: {len(enhanced_days)} days")
#     if total_budget > 0:
#         remaining = total_budget - total_cost
#         print(f"💵 Budget Remaining: INR {remaining:,.2f}")
    
#     for day in enhanced_days:
#         print("\n" + "─"*80)
#         print(f"📅 DAY {day.day_number}")
#         print("─"*80)
        
#         current_time = None
        
#         for item in day.items:
#             # Icons for different types
#             icons = {
#                 'accommodation': '🏨',
#                 'restaurant': '🍽️',
#                 'activity': '🎭',
#                 'local_transport': '🚗',
#                 'flight': '✈️',
#                 'ground_transport': '🚂'
#             }
            
#             icon = icons.get(item.type, '📍')
            
#             # Calculate time for this item
#             if item.type == 'accommodation':
#                 time_str = "[All day]"
#             elif item.type == 'local_transport':
#                 # Show travel time
#                 if current_time:
#                     time_str = f"[{current_time}]"
#                     # Update current time after transport
#                     current_time = _add_minutes(current_time, item.duration_minutes)
#                 else:
#                     time_str = "[Travel]"
#             else:
#                 if hasattr(item, 'time') and item.time:
#                     time_str = f"[{item.time}]"
#                     current_time = item.time
#                 elif current_time:
#                     time_str = f"[{current_time}]"
#                 else:
#                     time_str = "[--:--]"
                
#                 # Update current time after activity
#                 if current_time and item.duration_minutes > 0:
#                     current_time = _add_minutes(current_time, item.duration_minutes)
            
#             # Format duration
#             if item.duration_minutes > 0:
#                 hrs = item.duration_minutes // 60
#                 mins = item.duration_minutes % 60
#                 if hrs > 0:
#                     duration_str = f"({hrs}h {mins}m)"
#                 else:
#                     duration_str = f"({mins}m)"
#             else:
#                 duration_str = ""
            
#             # Display item
#             print(f"   {icon} {time_str} {item.name} {duration_str}")
            
#             # Show transport details
#             if item.type == 'local_transport':
#                 details = item.details
#                 print(f"      {details['mode'].capitalize()} • {details['distance_km']} km • INR {item.cost:.2f}")
#             else:
#                 # Show cost for non-transport items
#                 print(f"      Type: {item.type}")
#                 print(f"      Cost: INR {item.cost:,.2f}")
                
#                 # Show additional details
#                 if item.type == 'restaurant' and 'cuisine' in item.details:
#                     print(f"      Cuisine: {item.details['cuisine']}")
#                 elif item.type == 'activity' and 'category' in item.details:
#                     print(f"      Category: {item.details['category']}")
        
#         print(f"\n   💵 Day {day.day_number} Total: INR {day.total_cost:,.2f}")
    
#     print("\n" + "="*80)
#     print("✅ Itinerary complete!")
#     print("="*80)


# def _add_minutes(time_str: str, minutes: int) -> str:
#     """Add minutes to a time string (HH:MM)"""
#     try:
#         time_obj = datetime.strptime(time_str, "%H:%M")
#         new_time = time_obj + timedelta(minutes=minutes)
#         return new_time.strftime("%H:%M")
#     except:
#         return time_str


# if __name__ == "__main__":
#     # Test the enhancer
#     print("Testing Itinerary Enhancer...")
    
#     # This would normally come from your optimizer
#     # For testing, we'll create mock data
    
#     print("\n✅ Enhancer initialized")
#     print("To use: call enhance_itinerary(daily_schedules) after optimization")

"""
Itinerary Enhancer - FIXED VERSION
Handles both 'type' and 'item_type' attributes
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from local_transport_agent import LocalTransportAgent, TransportOption


@dataclass
class ItineraryItem:
    """Enhanced itinerary item with all details"""
    time: str
    type: str  # accommodation, restaurant, activity, local_transport
    name: str
    duration_minutes: int
    cost: float
    currency: str
    details: Dict[str, Any]
    
    def __repr__(self):
        return f"{self.type}: {self.name} ({self.duration_minutes}m, {self.currency} {self.cost})"


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
        """
        Initialize enhancer
        
        Args:
            budget_conscious: If True, prefer cheaper transport options
        """
        self.transport_agent = LocalTransportAgent()
        self.budget_conscious = budget_conscious
    
    def enhance_itinerary(self, daily_schedules: List[Any]) -> List[EnhancedDaySchedule]:
        """
        Add transport between locations in the itinerary
        
        Args:
            daily_schedules: List of DaySchedule objects from optimizer
            
        Returns:
            List of EnhancedDaySchedule with transport inserted
        """
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
        
        # Calculate totals
        total_cost = sum(item.cost for item in enhanced_items)
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
        
        # Get item types
        to_type = self._get_item_type(to_item)
        from_type = self._get_item_type(from_item)
        
        # No transport needed for accommodation (all day)
        if to_type in ['accommodation', 'flight', 'ground_transport']:
            return False
        
        # No transport from accommodation to first activity (assume walking to lobby)
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
            print(f"   ⚠️ Could not calculate distance: {e}")
            return False
        
        # Need transport if distance > 0.3 km (300 meters)
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
            
            # Convert to ItineraryItem
            transport_item = ItineraryItem(
                time="",  # Will be calculated when displaying
                type="local_transport",
                name=transport.description,
                duration_minutes=transport.duration_minutes,
                cost=transport.cost,
                currency=transport.currency,
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
            print(f"   ⚠️ Could not add transport: {e}")
            return None
    
    def _convert_to_enhanced_item(self, item: Any) -> ItineraryItem:
        """Convert optimizer item to enhanced itinerary item"""
        
        # Get basic info
        item_type = self._get_item_type(item)
        name = getattr(item, 'name', 'Unknown')
        duration = getattr(item, 'duration_minutes', getattr(item, 'duration', 0))
        
        # Get cost (try multiple attribute names)
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
        
        # Get time
        time_str = ""
        if hasattr(item, 'time'):
            time_str = item.time
        elif hasattr(item, 'time_str'):
            time_str = item.time_str
        elif hasattr(item, 'start_time'):
            start = item.start_time
            if isinstance(start, int):
                hours = start // 60
                mins = start % 60
                time_str = f"{hours:02d}:{mins:02d}"
            else:
                time_str = str(start)
        
        # Build details dict
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
        elif item_type == 'flight':
            details = {
                'carrier': getattr(item, 'carrier', 'Unknown'),
                'flight_number': getattr(item, 'flight_id', ''),
                'departure': getattr(item, 'departure_time', ''),
                'arrival': getattr(item, 'arrival_time', '')
            }
        elif item_type == 'ground_transport':
            details = {
                'provider': getattr(item, 'provider', 'Unknown'),
                'type': getattr(item, 'transport_type', 'Unknown')
            }
        
        return ItineraryItem(
            time=time_str,
            type=item_type,
            name=name,
            duration_minutes=duration,
            cost=cost,
            currency=currency,
            details=details
        )


def display_enhanced_itinerary(enhanced_days: List[EnhancedDaySchedule],
                               total_budget: float = 0):
    """
    Display enhanced itinerary with transport included
    
    Args:
        enhanced_days: List of EnhancedDaySchedule
        total_budget: Total trip budget
    """
    
    print("\n" + "="*80)
    print("📋 YOUR ENHANCED ITINERARY WITH LOCAL TRANSPORT")
    print("="*80)
    
    total_cost = sum(day.total_cost for day in enhanced_days)
    
    print(f"💰 Total Cost: INR {total_cost:,.2f}")
    print(f"📅 Duration: {len(enhanced_days)} days")
    if total_budget > 0:
        remaining = total_budget - total_cost
        print(f"💵 Budget Remaining: INR {remaining:,.2f}")
    
    for day in enhanced_days:
        print("\n" + "─"*80)
        print(f"📅 DAY {day.day_number}")
        print("─"*80)
        
        current_time = None
        
        for item in day.items:
            # Icons for different types
            icons = {
                'accommodation': '🏨',
                'restaurant': '🍽️',
                'activity': '🎭',
                'local_transport': '🚗',
                'flight': '✈️',
                'ground_transport': '🚂'
            }
            
            icon = icons.get(item.type, '📍')
            
            # Calculate time for this item
            if item.type == 'accommodation':
                time_str = "[All day]"
            elif item.type == 'local_transport':
                # Show travel time
                if current_time:
                    time_str = f"[{current_time}]"
                    # Update current time after transport
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
                
                # Update current time after activity
                if current_time and item.duration_minutes > 0:
                    current_time = _add_minutes(current_time, item.duration_minutes)
            
            # Format duration
            if item.duration_minutes > 0:
                hrs = item.duration_minutes // 60
                mins = item.duration_minutes % 60
                if hrs > 0:
                    duration_str = f"({hrs}h {mins}m)"
                else:
                    duration_str = f"({mins}m)"
            else:
                duration_str = ""
            
            # Display item
            print(f"   {icon} {time_str} {item.name} {duration_str}")
            
            # Show transport details
            if item.type == 'local_transport':
                details = item.details
                print(f"      {details['mode'].capitalize()} • {details['distance_km']} km • INR {item.cost:.2f}")
            else:
                # Show cost for non-transport items
                if item.cost > 0:
                    print(f"      Cost: INR {item.cost:,.2f}")
                
                # Show additional details
                if item.type == 'restaurant' and 'cuisine' in item.details:
                    print(f"      Cuisine: {item.details['cuisine']}")
                elif item.type == 'activity' and 'category' in item.details:
                    print(f"      Category: {item.details['category']}")
        
        print(f"\n   💵 Day {day.day_number} Total: INR {day.total_cost:,.2f}")
    
    print("\n" + "="*80)
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
    # Test the enhancer
    print("Testing Itinerary Enhancer...")
    
    print("\n✅ Enhancer initialized")
    print("To use: call enhance_itinerary(daily_schedules) after optimization")