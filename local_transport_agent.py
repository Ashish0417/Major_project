"""
Local Transport Agent Module
Calculates distances and suggests transport modes between locations
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import random


@dataclass
class TransportOption:
    """Local transport option between two locations"""
    transport_id: str
    mode: str  # taxi, auto, metro, bus, walk
    from_location: str
    to_location: str
    distance_km: float
    duration_minutes: int
    cost: float
    currency: str
    description: str
    comfort_level: str  # high, medium, low
    item_type: str = "local_transport"
    
    def to_dict(self):
        return self.__dict__


class LocalTransportAgent:
    """Calculate distances and suggest local transport modes"""
    
    # Transport modes with cost per km and average speed
    TRANSPORT_MODES = {
        'walk': {
            'cost_per_km': 0,
            'speed_kmph': 4,
            'comfort': 'low',
            'max_distance': 2.0,  # Don't suggest walking > 2km
            'icon': '🚶'
        },
        'auto': {
            'cost_per_km': 15,
            'base_fare': 25,
            'speed_kmph': 25,
            'comfort': 'medium',
            'max_distance': 10.0,
            'icon': '🛺'
        },
        'taxi': {
            'cost_per_km': 20,
            'base_fare': 50,
            'speed_kmph': 30,
            'comfort': 'high',
            'max_distance': 50.0,
            'icon': '🚕'
        },
        'metro': {
            'cost_per_km': 5,
            'base_fare': 10,
            'speed_kmph': 40,
            'comfort': 'medium',
            'max_distance': 30.0,
            'icon': '🚇'
        },
        'bus': {
            'cost_per_km': 3,
            'base_fare': 10,
            'speed_kmph': 20,
            'comfort': 'low',
            'max_distance': 25.0,
            'icon': '🚌'
        }
    }
    
    def __init__(self):
        """Initialize transport agent"""
        pass
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        Returns distance in kilometers
        """
        # Radius of Earth in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        distance = R * c
        return round(distance, 2)
    
    def suggest_transport(self, from_item: any, to_item: any,
                         budget_conscious: bool = True) -> TransportOption:
        """
        Suggest best transport mode between two locations
        
        Args:
            from_item: Item with latitude, longitude, name
            to_item: Item with latitude, longitude, name
            budget_conscious: If True, prefer cheaper options
        """
        # Calculate distance
        distance = self.calculate_distance(
            from_item.latitude, from_item.longitude,
            to_item.latitude, to_item.longitude
        )
        
        # Get from/to names
        from_name = getattr(from_item, 'name', 'Location')
        to_name = getattr(to_item, 'name', 'Location')
        
        # Choose best transport mode based on distance and preferences
        best_mode = self._choose_best_mode(distance, budget_conscious)
        
        # Calculate cost and duration
        mode_info = self.TRANSPORT_MODES[best_mode]
        
        cost = mode_info.get('base_fare', 0) + (distance * mode_info['cost_per_km'])
        duration = int((distance / mode_info['speed_kmph']) * 60)  # Convert to minutes
        
        # Add some variation to make it realistic
        cost = cost * random.uniform(0.95, 1.05)
        duration = int(duration * random.uniform(0.9, 1.1))
        
        # Create description
        description = f"{mode_info['icon']} {best_mode.capitalize()} from {from_name} to {to_name}"
        
        transport = TransportOption(
            transport_id=f"TRANS_{random.randint(1000, 9999)}",
            mode=best_mode,
            from_location=from_name,
            to_location=to_name,
            distance_km=distance,
            duration_minutes=max(duration, 5),  # Minimum 5 minutes
            cost=round(cost, 2),
            currency='INR',
            description=description,
            comfort_level=mode_info['comfort']
        )
        
        return transport
    
    def _choose_best_mode(self, distance: float, budget_conscious: bool) -> str:
        """Choose best transport mode based on distance and budget"""
        
        # Walking distance
        if distance <= 0.5:
            return 'walk'
        
        # Short distance (0.5 - 2 km)
        if distance <= 2.0:
            if budget_conscious:
                return 'walk'
            else:
                return 'auto'
        
        # Medium distance (2 - 5 km)
        if distance <= 5.0:
            if budget_conscious:
                return 'auto'
            else:
                return 'taxi'
        
        # Medium-long distance (5 - 10 km)
        if distance <= 10.0:
            if budget_conscious:
                return 'metro' if random.random() > 0.5 else 'bus'
            else:
                return 'taxi'
        
        # Long distance (10+ km)
        if distance <= 25.0:
            if budget_conscious:
                return 'metro'
            else:
                return 'taxi'
        
        # Very long distance
        return 'taxi'
    
    def get_all_transport_modes(self, distance: float) -> List[TransportOption]:
        """Get all viable transport options for a given distance"""
        options = []
        
        for mode, info in self.TRANSPORT_MODES.items():
            # Skip if distance exceeds max for this mode
            if distance > info['max_distance']:
                continue
            
            cost = info.get('base_fare', 0) + (distance * info['cost_per_km'])
            duration = int((distance / info['speed_kmph']) * 60)
            
            option = {
                'mode': mode,
                'distance_km': distance,
                'duration_minutes': duration,
                'cost': round(cost, 2),
                'comfort': info['comfort'],
                'icon': info['icon']
            }
            options.append(option)
        
        return options


if __name__ == "__main__":
    # Test the transport agent
    print("="*70)
    print("TESTING LOCAL TRANSPORT AGENT")
    print("="*70)
    
    agent = LocalTransportAgent()
    
    # Test distance calculation
    # Coordinates for testing (Mumbai examples)
    gateway_of_india = (18.9220, 72.8347)
    marine_drive = (18.9432, 72.8236)
    
    distance = agent.calculate_distance(
        gateway_of_india[0], gateway_of_india[1],
        marine_drive[0], marine_drive[1]
    )
    
    print(f"\n📍 Distance between Gateway of India and Marine Drive:")
    print(f"   {distance} km")
    
    # Test transport suggestions
    print(f"\n🚗 Transport options for {distance} km:")
    options = agent.get_all_transport_modes(distance)
    
    print(f"\n{'Mode':<10} {'Duration':<12} {'Cost':<12} {'Comfort':<10}")
    print("-"*70)
    for opt in options:
        print(f"{opt['icon']} {opt['mode']:<7} {opt['duration_minutes']} mins      INR {opt['cost']:<8.2f} {opt['comfort']}")
    
    # Test with mock objects
    print("\n" + "="*70)
    print("TESTING WITH MOCK LOCATIONS")
    print("="*70)
    
    class MockLocation:
        def __init__(self, name, lat, lon):
            self.name = name
            self.latitude = lat
            self.longitude = lon
    
    hotel = MockLocation("Grand Hotel", 18.9220, 72.8347)
    restaurant = MockLocation("Sea View Restaurant", 18.9432, 72.8236)
    
    transport = agent.suggest_transport(hotel, restaurant, budget_conscious=True)
    
    print(f"\n✅ Suggested transport:")
    print(f"   {transport.description}")
    print(f"   Distance: {transport.distance_km} km")
    print(f"   Duration: {transport.duration_minutes} minutes")
    print(f"   Cost: {transport.currency} {transport.cost}")
    print(f"   Comfort: {transport.comfort_level}")