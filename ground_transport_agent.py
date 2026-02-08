"""
Ground Transport Agent Module
Handles taxis, cars, trains, and buses for inter-city travel
"""

from typing import List, Optional
from dataclasses import dataclass
import math


@dataclass
class TransportOption:
    """Ground transport option data structure"""
    transport_id: str
    type: str  # taxi, car, train, bus
    origin: str
    destination: str
    distance_km: float
    duration_minutes: int
    price: float
    currency: str
    provider: str  # Uber, Ola, Train, Bus company
    comfort_level: str  # economy, premium, luxury
    departure_time: str = "Flexible"
    arrival_time: str = "Flexible"
    item_type: str = "ground_transport"


class GroundTransportAgent:
    """
    Ground Transport Agent
    Provides taxi, car, train, and bus options for inter-city travel
    """
    
    def __init__(self):
        """Initialize ground transport agent"""
        
        # Major city coordinates (latitude, longitude)
        self.city_coords = {
            'bangalore': (12.9716, 77.5946),
            'mumbai': (19.0760, 72.8777),
            'delhi': (28.7041, 77.1025),
            'chennai': (13.0827, 80.2707),
            'kolkata': (22.5726, 88.3639),
            'hyderabad': (17.3850, 78.4867),
            'pune': (18.5204, 73.8567),
            'ahmedabad': (23.0225, 72.5714),
            'jaipur': (26.9124, 75.7873),
            'goa': (15.2993, 74.1240),
            
            # International cities
            'tokyo': (35.6762, 139.6503),
            'paris': (48.8566, 2.3522),
            'london': (51.5074, -0.1278),
            'singapore': (1.3521, 103.8198),
            'dubai': (25.2048, 55.2708),
            'bangkok': (13.7563, 100.5018),
            'kuala lumpur': (3.1390, 101.6869),
            'hong kong': (22.3193, 114.1694),
        }
        
        # Base rates per km (in INR)
        self.rates_per_km = {
            'taxi_economy': 15,      # Regular taxi
            'taxi_premium': 25,      # Premium taxi (Uber/Ola)
            'car_rental': 20,        # Self-drive car rental
            'train_sleeper': 1.5,    # Train sleeper class
            'train_ac': 3,           # Train AC class
            'bus_regular': 2,        # Regular bus
            'bus_luxury': 5,         # Luxury bus
        }
        
        # Average speeds (km/h)
        self.avg_speeds = {
            'taxi': 60,
            'car': 70,
            'train': 80,
            'bus': 50,
        }
        
        # Maximum practical distances (km)
        self.max_distances = {
            'taxi': 500,      # Taxis practical up to 500km
            'car': 800,       # Car rental up to 800km
            'train': 3000,    # Trains for long distance
            'bus': 1000,      # Buses up to 1000km
        }
    
    def calculate_distance(self, origin: str, destination: str) -> float:
        """
        Calculate distance between two cities using Haversine formula
        
        Returns:
            Distance in kilometers
        """
        origin_lower = origin.lower().strip()
        dest_lower = destination.lower().strip()
        
        # Get coordinates
        if origin_lower not in self.city_coords or dest_lower not in self.city_coords:
            # If coordinates not found, estimate based on typical distances
            print(f"   ⚠️ Coordinates not found, using estimated distance")
            return 500  # Default estimate
        
        lat1, lon1 = self.city_coords[origin_lower]
        lat2, lon2 = self.city_coords[dest_lower]
        
        # Haversine formula
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        distance = R * c
        return round(distance, 2)
    
    def search_transport(self,
                        origin: str,
                        destination: str,
                        transport_types: Optional[List[str]] = None,
                        max_price: Optional[float] = None,
                        max_results: int = 10) -> List[TransportOption]:
        """
        Search for ground transport options
        
        Args:
            origin: Origin city
            destination: Destination city
            transport_types: Types to search ['taxi', 'car', 'train', 'bus']
            max_price: Maximum price in INR
            max_results: Maximum number of results
            
        Returns:
            List of transport options
        """
        
        if transport_types is None:
            transport_types = ['taxi', 'train', 'bus']
        
        # Calculate distance
        distance_km = self.calculate_distance(origin, destination)
        
        print(f"   📏 Distance: {distance_km:.0f} km")
        
        options = []
        
        # Generate options for each transport type
        for transport_type in transport_types:
            # Check if distance is practical for this transport type
            if distance_km > self.max_distances.get(transport_type, float('inf')):
                print(f"   ⚠️ {transport_type.title()} not practical for {distance_km:.0f}km")
                continue
            
            if transport_type == 'taxi':
                options.extend(self._generate_taxi_options(
                    origin, destination, distance_km
                ))
            elif transport_type == 'car':
                options.extend(self._generate_car_options(
                    origin, destination, distance_km
                ))
            elif transport_type == 'train':
                options.extend(self._generate_train_options(
                    origin, destination, distance_km
                ))
            elif transport_type == 'bus':
                options.extend(self._generate_bus_options(
                    origin, destination, distance_km
                ))
        
        # Filter by price if specified
        if max_price:
            options = [opt for opt in options if opt.price <= max_price]
        
        # Sort by price
        options.sort(key=lambda x: x.price)
        
        return options[:max_results]
    
    def _generate_taxi_options(self, origin: str, dest: str, distance: float) -> List[TransportOption]:
        """Generate taxi options"""
        options = []
        
        # Economy taxi (Ola/Uber)
        duration = int((distance / self.avg_speeds['taxi']) * 60)
        price_economy = distance * self.rates_per_km['taxi_economy']
        
        options.append(TransportOption(
            transport_id=f"TAXI-ECO-{origin[:3].upper()}-{dest[:3].upper()}",
            type="taxi",
            origin=origin,
            destination=dest,
            distance_km=distance,
            duration_minutes=duration,
            price=price_economy,
            currency="INR",
            provider="Ola/Uber",
            comfort_level="economy",
            departure_time="Flexible",
            arrival_time="Flexible"
        ))
        
        # Premium taxi
        price_premium = distance * self.rates_per_km['taxi_premium']
        
        options.append(TransportOption(
            transport_id=f"TAXI-PREM-{origin[:3].upper()}-{dest[:3].upper()}",
            type="taxi",
            origin=origin,
            destination=dest,
            distance_km=distance,
            duration_minutes=duration,
            price=price_premium,
            currency="INR",
            provider="Uber Premier",
            comfort_level="premium",
            departure_time="Flexible",
            arrival_time="Flexible"
        ))
        
        return options
    
    def _generate_car_options(self, origin: str, dest: str, distance: float) -> List[TransportOption]:
        """Generate car rental options"""
        options = []
        
        duration = int((distance / self.avg_speeds['car']) * 60)
        price = distance * self.rates_per_km['car_rental']
        
        options.append(TransportOption(
            transport_id=f"CAR-{origin[:3].upper()}-{dest[:3].upper()}",
            type="car",
            origin=origin,
            destination=dest,
            distance_km=distance,
            duration_minutes=duration,
            price=price,
            currency="INR",
            provider="Zoomcar/Revv",
            comfort_level="premium",
            departure_time="Flexible",
            arrival_time="Flexible"
        ))
        
        return options
    
    def _generate_train_options(self, origin: str, dest: str, distance: float) -> List[TransportOption]:
        """Generate train options"""
        options = []
        
        duration = int((distance / self.avg_speeds['train']) * 60)
        
        # Sleeper class
        price_sleeper = distance * self.rates_per_km['train_sleeper']
        options.append(TransportOption(
            transport_id=f"TRAIN-SL-{origin[:3].upper()}-{dest[:3].upper()}",
            type="train",
            origin=origin,
            destination=dest,
            distance_km=distance,
            duration_minutes=duration,
            price=price_sleeper,
            currency="INR",
            provider="Indian Railways",
            comfort_level="economy",
            departure_time="08:00",
            arrival_time=f"{8 + duration//60:02d}:{duration%60:02d}"
        ))
        
        # AC class
        price_ac = distance * self.rates_per_km['train_ac']
        options.append(TransportOption(
            transport_id=f"TRAIN-AC-{origin[:3].upper()}-{dest[:3].upper()}",
            type="train",
            origin=origin,
            destination=dest,
            distance_km=distance,
            duration_minutes=duration,
            price=price_ac,
            currency="INR",
            provider="Indian Railways",
            comfort_level="premium",
            departure_time="14:00",
            arrival_time=f"{14 + duration//60:02d}:{duration%60:02d}"
        ))
        
        return options
    
    def _generate_bus_options(self, origin: str, dest: str, distance: float) -> List[TransportOption]:
        """Generate bus options"""
        options = []
        
        duration = int((distance / self.avg_speeds['bus']) * 60)
        
        # Regular bus
        price_regular = distance * self.rates_per_km['bus_regular']
        options.append(TransportOption(
            transport_id=f"BUS-REG-{origin[:3].upper()}-{dest[:3].upper()}",
            type="bus",
            origin=origin,
            destination=dest,
            distance_km=distance,
            duration_minutes=duration,
            price=price_regular,
            currency="INR",
            provider="State Transport",
            comfort_level="economy",
            departure_time="06:00",
            arrival_time=f"{6 + duration//60:02d}:{duration%60:02d}"
        ))
        
        # Luxury bus
        price_luxury = distance * self.rates_per_km['bus_luxury']
        options.append(TransportOption(
            transport_id=f"BUS-LUX-{origin[:3].upper()}-{dest[:3].upper()}",
            type="bus",
            origin=origin,
            destination=dest,
            distance_km=distance,
            duration_minutes=duration,
            price=price_luxury,
            currency="INR",
            provider="Volvo/Sleeper",
            comfort_level="premium",
            departure_time="22:00",
            arrival_time=f"{(22 + duration//60) % 24:02d}:{duration%60:02d}"
        ))
        
        return options
    
    def compare_with_flight(self, transport_option: TransportOption, 
                           flight_price: float) -> dict:
        """
        Compare ground transport with flight option
        
        Returns:
            Comparison dict with recommendation
        """
        savings = flight_price - transport_option.price
        savings_pct = (savings / flight_price * 100) if flight_price > 0 else 0
        
        # Calculate time difference (assume flight is 2 hours for short distances)
        flight_duration = 120  # 2 hours average
        time_diff = transport_option.duration_minutes - flight_duration
        
        recommendation = "ground_transport"
        reason = ""
        
        if savings > 5000 and time_diff < 300:  # Save >5000 INR and <5 hours extra
            recommendation = "ground_transport"
            reason = f"Save INR {savings:,.0f} ({savings_pct:.0f}%) with reasonable time"
        elif savings > 10000:  # Save >10000 INR
            recommendation = "ground_transport"
            reason = f"Significant savings: INR {savings:,.0f}"
        elif time_diff < 120:  # Less than 2 hours extra
            recommendation = "ground_transport"
            reason = "Similar duration, much cheaper"
        elif transport_option.distance_km < 300:  # Very short distance
            recommendation = "ground_transport"
            reason = "Short distance, ground transport more practical"
        else:
            recommendation = "flight"
            reason = "Time savings worth the extra cost"
        
        return {
            'recommendation': recommendation,
            'reason': reason,
            'savings': savings,
            'savings_pct': savings_pct,
            'time_diff_minutes': time_diff,
            'ground_transport': transport_option,
            'flight_price': flight_price
        }


if __name__ == "__main__":
    # Test the ground transport agent
    agent = GroundTransportAgent()
    
    print("="*70)
    print("GROUND TRANSPORT AGENT TEST")
    print("="*70)
    
    # Test 1: Short distance (Bangalore to Mumbai)
    print("\n📍 Test 1: Bangalore to Mumbai")
    print("-"*70)
    options = agent.search_transport(
        origin="Bangalore",
        destination="Mumbai",
        transport_types=['taxi', 'train', 'bus'],
        max_results=6
    )
    
    for i, opt in enumerate(options, 1):
        print(f"\n{i}. {opt.type.upper()} - {opt.provider}")
        print(f"   Distance: {opt.distance_km:.0f} km")
        print(f"   Duration: {opt.duration_minutes // 60}h {opt.duration_minutes % 60}m")
        print(f"   Price: {opt.currency} {opt.price:,.2f}")
        print(f"   Comfort: {opt.comfort_level}")
    
    # Test 2: Compare with flight
    print("\n" + "="*70)
    print("📊 COMPARISON WITH FLIGHT")
    print("="*70)
    
    flight_price = 8000  # INR
    best_ground = options[0]  # Cheapest option
    
    comparison = agent.compare_with_flight(best_ground, flight_price)
    
    print(f"\nFlight Price: INR {flight_price:,.0f}")
    print(f"Ground Transport: {best_ground.type.title()} - INR {best_ground.price:,.0f}")
    print(f"Savings: INR {comparison['savings']:,.0f} ({comparison['savings_pct']:.0f}%)")
    print(f"Time Difference: {comparison['time_diff_minutes'] // 60}h {comparison['time_diff_minutes'] % 60}m")
    print(f"\n💡 Recommendation: {comparison['recommendation'].upper()}")
    print(f"   Reason: {comparison['reason']}")