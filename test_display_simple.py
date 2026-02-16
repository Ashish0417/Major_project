"""Direct test of display and distribution functions"""
from dataclasses import dataclass

# Mock object
@dataclass
class MockItem:
    name: str
    item_type: str
    cost: float = 0
    rating: float = 0
    duration_minutes: int = 0
    departure_time: str = ""
    carrier: str = ""

# Create test itinerary
itinerary = {
    'total_cost': 54768.40,
    'currency': 'INR',
    'num_days': 3,
    'itinerary': {
        0: [
            MockItem("IndiGo Flight BLR-CDG", "flight", 24885.82, 4.5, 399, "2026-03-01T08:00:00", "6E"),
            MockItem("Hôtel Montpensier", "accommodation", 3289.41, 4.2),
            MockItem("Café Moderne", "restaurant", 800, 4.0),
            MockItem("Grande Arche", "activity", 898.65, 4.0, 135)
        ],
        1: [
            MockItem("Hôtel Montpensier", "accommodation", 3289.41, 4.2),
            MockItem("Le Jules Verne", "restaurant", 2500, 4.5),
            MockItem("Louvre Museum", "activity", 1200, 4.8, 180),
            MockItem("Musée d'Orsay", "activity", 1000, 4.7, 120)
        ],
        2: [
            MockItem("Hôtel Montpensier", "accommodation", 3289.41, 4.2),
            MockItem("L'Astrance", "restaurant", 1800, 4.6),
            MockItem("Notre-Dame", "activity", 1500, 5.0, 90),
            MockItem("Air India Flight CDG-BLR", "flight", 25694.52, 4.5, 480, "2026-03-03T17:03:00", "AI"),
        ]
    },
    'optimizer_metadata': {
        'optimizer': 'langgraph',
        'score': 70.0,
        'combinations_evaluated': 15,
    }
}

trip_details = {
    'origin_city': 'Bangalore',
    'destination_city': 'Paris',
}

# Display helper functions (copied from llm_orchestrator)
def _get_item_icon(item_type: str, name: str) -> str:
    """Get appropriate emoji icon for item type"""
    item_type = item_type.lower()
    
    if 'flight' in item_type or 'return' in name.lower():
        return "✈️"
    elif 'train' in item_type or 'railway' in item_type:
        return "🚂"
    elif 'bus' in item_type:
        return "🚌"
    elif 'taxi' in item_type or 'uber' in item_type.lower() or 'ola' in item_type.lower():
        return "🚕"
    elif 'car' in item_type or 'transport' in item_type or 'ground' in item_type:
        return "🚗"
    elif 'hotel' in item_type or 'accommodation' in item_type:
        return "🏨"
    elif 'restaurant' in item_type or 'dining' in item_type:
        return "🍽️"
    elif 'activity' in item_type or 'attraction' in item_type:
        return "🎭"
    else:
        return "📍"

def _get_item_time(item) -> str:
    """Extract proper time string from item"""
    if hasattr(item, 'departure_time') and item.departure_time:
        time_val = item.departure_time
        if isinstance(time_val, str):
            if 'T' in time_val:
                time_part = time_val.split('T')[1][:5]
                return f"[{time_part}]"
            return f"[{time_val}]"
        return "[Time]"
    elif hasattr(item, 'start_time') and item.start_time and item.start_time > 0:
        hours = int(item.start_time // 60)
        mins = int(item.start_time % 60)
        return f"[{hours:02d}:{mins:02d}]"
    elif hasattr(item, 'time_str') and item.time_str:
        return f"[{item.time_str}]"
    else:
        return "[All day]"

def _get_item_duration(item) -> str:
    """Extract duration string from item"""
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

def _get_item_cost(item) -> float:
    """Extract cost from item"""
    if hasattr(item, 'cost') and item.cost:
        return item.cost
    elif hasattr(item, 'price') and item.price:
        return item.price
    elif hasattr(item, 'price_per_night') and item.price_per_night:
        return item.price_per_night
    return 0

# Display the itinerary
print("\n" + "="*80)
print("📋 YOUR PERSONALIZED DAY-BY-DAY ITINERARY")
print("="*80)

destination = trip_details.get('destination_city', 'Destination')
origin = trip_details.get('origin_city', 'Origin')

print(f"\n🌍 Destination: {destination}")
print(f"📤 From: {origin}")
print(f"💰 Total Cost: {itinerary.get('currency', 'INR')} {itinerary.get('total_cost', 0):,.2f}")
print(f"📅 Duration: {itinerary.get('num_days', 0)} days")

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
        name = getattr(item, 'name', 'Unknown')
        item_type = getattr(item, 'item_type', 'Unknown').lower()
        
        icon = _get_item_icon(item_type, name)
        time_str = _get_item_time(item)
        duration_str = _get_item_duration(item)
        cost = _get_item_cost(item)
        
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
            if hasattr(item, 'carrier') and item.carrier:
                print(f"      ✈️ {item.carrier}")
            if hasattr(item, 'duration_minutes') and item.duration_minutes > 0:
                hrs = item.duration_minutes // 60
                mins = item.duration_minutes % 60
                print(f"      ⏱️ Duration: {hrs}h {mins}m")
        elif item_type in ['restaurant']:
            if hasattr(item, 'cuisine_type') and item.cuisine_type:
                print(f"      🍜 {item.cuisine_type} cuisine")
        elif item_type in ['accommodation', 'hotel']:
            if hasattr(item, 'amenities') and item.amenities:
                amenities_str = ', '.join(item.amenities[:2])
                print(f"      🏠 {amenities_str}")
    
    if day_cost > 0:
        print(f"\n   {'─'*76}")
        print(f"   💰 Day {day_num + 1} Total: INR {day_cost:,.2f}")

print("\n" + "="*80)
print("✅ ITINERARY GENERATION COMPLETE!")
print("="*80)
