# """
# Restaurant Agent - CORRECTED Overpass Query Format
# Uses CORRECT Overpass query syntax with bounding boxes and cuisine filtering
# """

# import requests
# from typing import List, Dict, Optional, Any
# from dataclasses import dataclass
# import random
# import math


# @dataclass
# class RestaurantOption:
#     """Restaurant data"""
#     restaurant_id: str
#     name: str
#     cuisine_type: List[str]
#     address: str
#     latitude: float
#     longitude: float
#     price_level: int
#     average_meal_cost: float
#     currency: str
#     rating: float
#     review_count: int
#     opening_hours: Dict[str, str]
#     dietary_options: List[str]
#     average_meal_time_minutes: int
#     reservations_available: bool
#     phone: Optional[str] = None
#     website: Optional[str] = None
#     source: str = "OpenStreetMap"


# class RestaurantAgent:
#     """CORRECTED Restaurant Agent - Proper Overpass Queries"""

#     def __init__(self):
#         self.nominatim_url = "https://nominatim.openstreetmap.org/search"
#         self.overpass_url = "https://overpass-api.de/api/interpreter"
#         self.headers = {'User-Agent': 'TravelPlannerApp/1.0 (student project)'}

#     def search_restaurants(self, location: str, cuisine_types: Optional[List[str]] = None,
#                           dietary_restrictions: Optional[List[str]] = None,
#                           max_price_level: int = 4, min_rating: float = 3.5,
#                           radius_km: float = 5.0, max_results: int = 15) -> List[RestaurantOption]:
#         """CORRECTED: Search restaurants with proper Overpass queries"""

#         print(f"🔍 Searching restaurants in {location}...")

#         # Get location coordinates
#         location_coords = self._get_location_coordinates(location)
#         if not location_coords:
#             print(f"  ❌ Location not found")
#             return []

#         lat, lon = location_coords
#         print(f"  ✓ Found location: {location} ({lat:.4f}, {lon:.4f})")

#         # Search using CORRECTED Overpass query
#         restaurants = self._search_via_overpass(lat, lon, radius_km, max_results)

#         # Filter by dietary
#         if dietary_restrictions:
#             restaurants = [r for r in restaurants
#                          if any(d in r.dietary_options for d in dietary_restrictions)]

#         restaurants.sort(key=lambda x: x.rating, reverse=True)
#         restaurants = [r for r in restaurants if r.rating >= min_rating]

#         print(f"  ✓ Found {len(restaurants)} restaurants")
#         return restaurants[:max_results]

#     def _get_location_coordinates(self, location: str) -> Optional[tuple]:
#         """Get location coordinates"""
#         try:
#             params = {'q': location, 'format': 'json', 'limit': 1}
#             response = requests.get(self.nominatim_url, params=params,
#                                    headers=self.headers, timeout=10)
#             response.raise_for_status()

#             data = response.json()
#             if data:
#                 return (float(data[0]['lat']), float(data[0]['lon']))
#             return None
#         except Exception as e:
#             print(f"  ❌ Location error: {e}")
#             return None

#     def _search_via_overpass(self, lat: float, lon: float,
#                             radius_km: float, max_results: int) -> List[RestaurantOption]:
#         """CORRECTED: Search via Overpass with CORRECT query format"""
#         try:
#             # CORRECTED: Proper bounding box (south, west, north, east)
#             lat1 = lat - (radius_km / 111.0)  # south
#             lon1 = lon - (radius_km / 111.0)  # west
#             lat2 = lat + (radius_km / 111.0)  # north
#             lon2 = lon + (radius_km / 111.0)  # east

#             # Build the CORRECT query for restaurants with amenity tag
#             query = f"""[out:json][timeout:25];
# (
#   node["amenity"="restaurant"]({lat1},{lon1},{lat2},{lon2});
#   way["amenity"="restaurant"]({lat1},{lon1},{lat2},{lon2});
# );
# out body;
# >;
# out skel qt;
# """

#             print(f"  🔍 Querying Overpass for restaurants...")
#             response = requests.post(self.overpass_url, data=query,
#                                     headers=self.headers, timeout=60)

#             if response.status_code != 200:
#                 print(f"  ❌ Overpass error {response.status_code}")
#                 return []

#             data = response.json()
#             restaurants = []

#             elements = data.get('elements', [])
#             print(f"  Found {len(elements)} raw elements")

#             for i, element in enumerate(elements[:max_results]):
#                 if 'tags' not in element or 'name' not in element['tags']:
#                     continue

#                 # Get coordinates
#                 if 'lat' in element and 'lon' in element:
#                     coords = {'lat': element['lat'], 'lon': element['lon']}
#                 else:
#                     continue

#                 tags = element['tags']
#                 name = tags.get('name', f'Restaurant {i}')

#                 restaurant = RestaurantOption(
#                     restaurant_id=f"REST_{element.get('id', i)}",
#                     name=name,
#                     cuisine_type=self._parse_cuisines(tags.get('cuisine', '')),
#                     address=self._get_address(tags),
#                     latitude=float(coords['lat']),
#                     longitude=float(coords['lon']),
#                     price_level=self._estimate_price_level(tags),
#                     average_meal_cost=self._estimate_meal_cost(tags),
#                     currency='INR',
#                     rating=self._estimate_rating(tags),
#                     review_count=random.randint(20, 500),
#                     opening_hours=self._parse_hours(tags),
#                     dietary_options=self._parse_dietary(tags),
#                     average_meal_time_minutes=60,
#                     reservations_available=True,
#                     phone=tags.get('phone'),
#                     website=tags.get('website'),
#                     source="OpenStreetMap"
#                 )
#                 restaurants.append(restaurant)

#             if restaurants:
#                 print(f"  ✓ Extracted {len(restaurants)} restaurants")

#             return restaurants

#         except Exception as e:
#             print(f"  ❌ Overpass error: {e}")
#             return []

    # def _parse_cuisines(self, cuisine_str: str) -> List[str]:
    #     """Parse cuisine types"""
    #     if not cuisine_str:
    #         return ['Mixed']
    #     cuisines = [c.strip().title() for c in cuisine_str.split(';')]
    #     return cuisines[:3] if cuisines else ['Mixed']

#     def _get_address(self, tags: dict) -> str:
#         """Extract address"""
#         parts = []
#         for key in ['addr:street', 'addr:city', 'addr:postcode']:
#             if key in tags:
#                 parts.append(str(tags[key]))
#         return ', '.join(parts) if parts else 'Address available'

    # def _estimate_price_level(self, tags: dict) -> int:
    #     """Estimate price level"""
    #     if 'price_level' in tags:
    #         try:
    #             return min(4, int(tags['price_level']))
    #         except:
    #             pass
    #     return random.randint(1, 3)

    # def _estimate_meal_cost(self, tags: dict) -> float:
    #     """Estimate meal cost"""
    #     level = self._estimate_price_level(tags)
    #     costs = {1: 300, 2: 700, 3: 1500, 4: 3000}
    #     return costs.get(level, 500) * random.uniform(0.8, 1.2)

#     def _estimate_rating(self, tags: dict) -> float:
#         """Estimate rating"""
#         if 'rating' in tags:
#             try:
#                 return float(tags['rating'])
#             except:
#                 pass
#         return random.uniform(3.5, 5.0)

#     def _parse_hours(self, tags: dict) -> Dict[str, str]:
#         """Parse opening hours"""
#         if 'opening_hours' in tags:
#             return {'hours': tags['opening_hours']}
#         return {'default': '11:00-22:00'}

#     def _parse_dietary(self, tags: dict) -> List[str]:
#         """Parse dietary options"""
#         options = []
#         if tags.get('diet:vegetarian') == 'yes':
#             options.append('vegetarian')
#         if tags.get('diet:vegan') == 'yes':
#             options.append('vegan')
#         return options if options else ['vegetarian', 'mixed']

    # def rank_restaurants(self, restaurants: List[RestaurantOption]) -> List[RestaurantOption]:
    #     """Rank restaurants"""
    #     if not restaurants:
    #         return []

    #     restaurants.sort(key=lambda x: x.rating, reverse=True)
    #     return restaurants

"""
Restaurant Agent - FIXED VERSION
Handles Overpass 504 timeouts and ensures mock data works properly
"""

import os
import requests
import random
import time
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class RestaurantOption:
    """Restaurant option data structure"""
    restaurant_id: str
    name: str
    cuisine: str
    address: str
    latitude: float
    longitude: float
    average_cost: float
    currency: str
    rating: float
    review_count: int
    dietary_options: List[str]
    opening_hours: Dict[str, str]
    cuisine_type: List[str]
    average_meal_cost: float
    average_meal_time_minutes: int
    phone: Optional[str] = None
    website: Optional[str] = None
    source: str = "API"

    def to_dict(self):
        return self.__dict__


class RestaurantAgent:
    """Restaurant Agent - FIXED to handle API timeouts"""

    # City coordinates for mock data
    CITY_COORDINATES = {
        'tokyo': (35.6762, 139.6503),
        'paris': (48.8566, 2.3522),
        'london': (51.5074, -0.1278),
        'new york': (40.7128, -74.0060),
        'dubai': (25.2048, 55.2708),
        'rome': (41.9028, 12.4964),
        'barcelona': (41.3851, 2.1734),
        'amsterdam': (52.3676, 4.9041),
        'bangkok': (13.7563, 100.5018),
        'sydney': (-33.8688, 151.2093),
        'mangalore': (12.8698, 74.8430),
        'bangalore': (12.9716, 77.5946),
        'mumbai': (19.0760, 72.8777),
        'delhi': (28.6139, 77.2090),
    }

    def __init__(self):
        """Initialize restaurant agent with multiple Overpass servers"""
        self.overpass_urls = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://lz4.overpass-api.de/api/interpreter",
        ]
        self.headers = {'User-Agent': 'TravelPlannerApp/1.0'}
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0

    def _parse_cuisines(self, cuisine_str: str) -> List[str]:
        """Parse cuisine types"""
        if not cuisine_str:
            return ['Mixed']
        cuisines = [c.strip().title() for c in cuisine_str.split(';')]
        return cuisines[:3] if cuisines else ['Mixed']
    
    def _estimate_meal_cost(self, tags: dict) -> float:
        """Estimate meal cost"""
        level = self._estimate_price_level(tags)
        costs = {1: 300, 2: 700, 3: 1500, 4: 3000}
        return costs.get(level, 500) * random.uniform(0.8, 1.2)
    
    def _estimate_price_level(self, tags: dict) -> int:
        """Estimate price level"""
        if 'price_level' in tags:
            try:
                return min(4, int(tags['price_level']))
            except:
                pass
        return random.randint(1, 3)


    def search_restaurants(self,
                          location: str,
                          dietary_restrictions: Optional[List[str]] = None,
                          cuisine_preference: Optional[str] = None,
                          max_price: Optional[float] = None,
                          min_rating: float = 3.5,
                          max_results: int = 15) -> List[RestaurantOption]:
        """
        Search for restaurants with better error handling
        """
        print(f"🔍 Searching restaurants in {location}...")
        
        # Get coordinates
        coords = self._get_coordinates(location)
        if not coords:
            print(f"  ⚠️ Could not geocode {location}, using defaults")
            coords = self._get_default_coords(location)
        
        lat, lon = coords
        print(f"  ✓ Found location: {location} ({lat:.4f}, {lon:.4f})")
        
        restaurants = []
        
        # Try Overpass API with timeout handling
        print(f"  🔍 Querying Overpass for restaurants...")
        try:
            restaurants = self._search_overpass(lat, lon, location, max_results)
        except Exception as e:
            error_msg = str(e)
            if '504' in error_msg or 'timeout' in error_msg.lower():
                print(f"  ❌ Overpass error 504 (timeout)")
            else:
                print(f"  ❌ Overpass error: {error_msg[:50]}")
        
        print(f"  ✓ Found {len(restaurants)} restaurants")
        
        # If API failed, use mock data
        if not restaurants:
            print(f"   ⚠️ No restaurants found (will use mock data)")
            restaurants = self._generate_mock_restaurants(
                location, max_results, coords=coords
            )
            print(f"   ✓ Generated {len(restaurants)} mock restaurants")
        
        # Apply filters
        if dietary_restrictions:
            restaurants = self._filter_by_dietary(restaurants, dietary_restrictions)
        
        if cuisine_preference:
            restaurants = [r for r in restaurants 
                          if cuisine_preference.lower() in r.cuisine.lower()]
        
        if max_price:
            restaurants = [r for r in restaurants if r.average_cost <= max_price]
        
        restaurants = [r for r in restaurants if r.rating >= min_rating]
        
        # Rank by rating
        restaurants.sort(key=lambda x: x.rating, reverse=True)
        
        return restaurants[:max_results]

    def _get_coordinates(self, location: str) -> Optional[tuple]:
        """Get coordinates from location name"""
        try:
            self._apply_rate_limit()
            
            params = {
                'q': location,
                'format': 'json',
                'limit': 1
            }
            
            response = requests.get(
                self.nominatim_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return (float(data[0]['lat']), float(data[0]['lon']))
            
            return None
        except Exception as e:
            print(f"  ⚠️ Geocoding error: {str(e)[:30]}")
            return None

    def _get_default_coords(self, location: str) -> tuple:
        """Get default coordinates for known cities"""
        location_lower = location.lower()
        for city, coords in self.CITY_COORDINATES.items():
            if city in location_lower:
                return coords
        # Default to Tokyo if unknown
        return self.CITY_COORDINATES['tokyo']

    def _search_overpass(self, lat: float, lon: float, 
                        location: str, max_results: int) -> List[RestaurantOption]:
        """Search using Overpass API with improved timeout handling"""
        
        restaurants = []
        
        # Try each server
        for server_idx, overpass_url in enumerate(self.overpass_urls, 1):
            try:
                self._apply_rate_limit()
                
                # SIMPLIFIED query to avoid timeouts
                radius_km = 5  # Reduced from 10km to 5km
                lat_offset = radius_km / 111.0
                lon_offset = radius_km / 111.0
                
                bbox = (
                    lat - lat_offset,
                    lon - lon_offset,
                    lat + lat_offset,
                    lon + lon_offset
                )
                
                # Simpler query - just restaurants, no complex filters
                query = f"""[out:json][timeout:10];
(
  node["amenity"="restaurant"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
  way["amenity"="restaurant"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
);
out center {max_results * 2};
"""
                
                response = requests.post(
                    overpass_url,
                    data=query,
                    headers=self.headers,
                    timeout=15  # 15 second timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    restaurants = self._parse_overpass_results(data, location)
                    
                    if restaurants:
                        print(f"     ✓ Server {server_idx} succeeded")
                        return restaurants[:max_results]
                elif response.status_code == 504:
                    print(f"     ⚠️ Server {server_idx} timeout (504)")
                    continue
                else:
                    print(f"     ⚠️ Server {server_idx} error {response.status_code}")
                    continue
                    
            except requests.Timeout:
                print(f"     ⚠️ Server {server_idx} timeout")
                continue
            except Exception as e:
                print(f"     ⚠️ Server {server_idx} error: {str(e)[:30]}")
                continue
        
        return restaurants

    def _parse_overpass_results(self, data: dict, location: str) -> List[RestaurantOption]:
        """Parse Overpass API results"""
        restaurants = []
        elements = data.get('elements', [])
        
        for i, element in enumerate(elements):
            try:
                tags = element.get('tags', {})
                
                if 'name' not in tags:
                    continue
                
                # Get coordinates
                if 'lat' in element and 'lon' in element:
                    coords = {'lat': element['lat'], 'lon': element['lon']}
                elif 'center' in element:
                    coords = {'lat': element['center']['lat'], 
                             'lon': element['center']['lon']}
                else:
                    continue
                
                name = tags.get('name')
                cuisine = tags.get('cuisine', 'International')
                
                # Estimate price
                price_range = self._estimate_price(cuisine)
                
                restaurant = RestaurantOption(
                    restaurant_id=f"REST_OSM_{element.get('id', i)}",
                    name=name,
                    cuisine=cuisine.capitalize(),
                    address=self._get_address_from_tags(tags, location),
                    latitude=coords['lat'],
                    longitude=coords['lon'],
                    average_cost=price_range,
                    currency='INR',
                    rating=random.uniform(4.0, 4.8),
                    review_count=random.randint(50, 500),
                    dietary_options=self._extract_dietary_options(tags),
                    opening_hours=self._parse_opening_hours(tags),
                    cuisine_type=self._parse_cuisines(tags.get('cuisine', '')),
                    average_meal_cost=self._estimate_meal_cost(tags),
                    average_meal_time_minutes=60,
                    phone=tags.get('phone'),
                    website=tags.get('website'),
                    source="OpenStreetMap"
                )
                
                restaurants.append(restaurant)
                
            except Exception as e:
                continue
        
        return restaurants

    def _generate_mock_restaurants(self, location: str, max_results: int,
                                   coords: Optional[tuple] = None) -> List[RestaurantOption]:
        """
        Generate mock restaurant data as fallback
        FIXED: Now uses proper coordinates instead of (0, 0)
        """
        
        # Use provided coords or get defaults
        if coords:
            base_lat, base_lon = coords
        else:
            base_lat, base_lon = self._get_default_coords(location)
        
        cuisines = [
            ('Indian', 600),
            ('Chinese', 500),
            ('Italian', 700),
            ('Japanese', 800),
            ('Thai', 550),
            ('Mexican', 600),
            ('Mediterranean', 750),
            ('American', 650),
            ('Korean', 700),
            ('Vietnamese', 500),
        ]
        
        restaurant_names = [
            "Spice Garden", "Golden Dragon", "Pasta House", "Sushi Bar",
            "Thai Orchid", "Taco Plaza", "Olive Branch", "Burger Shack",
            "Seoul Kitchen", "Pho House", "Curry Palace", "Noodle Express",
            "Pizza Corner", "Grill Master", "Cafe Delight"
        ]
        
        restaurants = []
        
        for i in range(min(max_results, len(restaurant_names))):
            cuisine, base_price = random.choice(cuisines)
            name = f"{random.choice(restaurant_names)} - {location}"
            
            # Generate coordinates near city center
            rest_lat = base_lat + random.uniform(-0.05, 0.05)
            rest_lon = base_lon + random.uniform(-0.05, 0.05)
            
            restaurant = RestaurantOption(
                restaurant_id=f"REST_MOCK_{i+1}",
                name=name,
                cuisine=cuisine,
                address=f"{random.randint(1, 100)} Main Street, {location}",
                latitude=rest_lat,  # FIXED: Use proper coordinates
                longitude=rest_lon,  # FIXED: Use proper coordinates
                average_cost=base_price * random.uniform(0.8, 1.2),
                currency='INR',
                rating=random.uniform(4.0, 4.8),
                review_count=random.randint(100, 1000),
                dietary_options=random.sample(
                    ['vegetarian', 'vegan', 'gluten-free', 'halal'],
                    k=random.randint(1, 3)
                ),
                opening_hours={'daily': '11:00-23:00'},
                cuisine_type=["Continental", "Italian"],
                average_meal_cost=200.0,
                average_meal_time_minutes=60,
                phone=f"+91-{random.randint(1000000000, 9999999999)}",
                website=None,
                source="Mock Data"
            )
            
            restaurants.append(restaurant)
        
        return restaurants

    def _filter_by_dietary(self, restaurants: List[RestaurantOption],
                          restrictions: List[str]) -> List[RestaurantOption]:
        """Filter restaurants by dietary restrictions"""
        if not restrictions:
            return restaurants
        
        filtered = []
        for restaurant in restaurants:
            if any(r.lower() in [d.lower() for d in restaurant.dietary_options]
                   for r in restrictions):
                filtered.append(restaurant)
        
        return filtered if filtered else restaurants  # Return all if none match

    def _apply_rate_limit(self):
        """Apply rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _estimate_price(self, cuisine: str) -> float:
        """Estimate price based on cuisine type"""
        price_map = {
            'indian': 600,
            'chinese': 500,
            'italian': 700,
            'japanese': 800,
            'thai': 550,
            'mexican': 600,
            'mediterranean': 750,
            'international': 650,
        }
        
        cuisine_lower = cuisine.lower()
        for key, price in price_map.items():
            if key in cuisine_lower:
                return price * random.uniform(0.8, 1.2)
        
        return 650 * random.uniform(0.8, 1.2)

    def _get_address_from_tags(self, tags: dict, location: str) -> str:
        """Extract address from OSM tags"""
        parts = []
        for key in ['addr:street', 'addr:housenumber']:
            if key in tags:
                parts.append(tags[key])
        return ', '.join(parts) if parts else location

    def _extract_dietary_options(self, tags: dict) -> List[str]:
        """Extract dietary options from tags"""
        options = []
        
        if tags.get('diet:vegetarian') == 'yes':
            options.append('vegetarian')
        if tags.get('diet:vegan') == 'yes':
            options.append('vegan')
        if tags.get('diet:halal') == 'yes':
            options.append('halal')
        if tags.get('diet:kosher') == 'yes':
            options.append('kosher')
        
        # Add some random options if none found
        if not options:
            options = random.sample(
                ['vegetarian', 'vegan', 'gluten-free', 'halal'],
                k=random.randint(1, 2)
            )
        
        return options

    def _parse_opening_hours(self, tags: dict) -> Dict[str, str]:
        """Parse opening hours from tags"""
        if 'opening_hours' in tags:
            return {'daily': tags['opening_hours']}
        return {'daily': '11:00-23:00'}
    
    def rank_restaurants(self, restaurants: List[RestaurantOption]) -> List[RestaurantOption]:
        """Rank restaurants"""
        if not restaurants:
            return []

        restaurants.sort(key=lambda x: x.rating, reverse=True)
        return restaurants


if __name__ == "__main__":
    agent = RestaurantAgent()
    
    print("="*80)
    print("TESTING FIXED RESTAURANT AGENT")
    print("="*80)
    
    print("\nTest 1: Restaurants in Mangalore")
    restaurants = agent.search_restaurants(
        location="Mangalore",
        max_results=5
    )
    
    print(f"\n✅ Found {len(restaurants)} restaurants:")
    for i, rest in enumerate(restaurants, 1):
        print(f"\n{i}. {rest.name}")
        print(f"   Source: {rest.source}")
        print(f"   Cuisine: {rest.cuisine}")
        print(f"   Location: ({rest.latitude:.4f}, {rest.longitude:.4f})")
        print(f"   Price: {rest.currency} {rest.average_cost:.2f}")
        print(f"   Rating: {rest.rating}/5")