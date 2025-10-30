# """
# Restaurant Agent Module
# Handles restaurant and dining recommendations
# """

# import os
# from typing import List, Dict, Optional, Any
# from dataclasses import dataclass
# import random


# @dataclass
# class RestaurantOption:
#     """Restaurant option data structure"""
#     restaurant_id: str
#     name: str
#     cuisine_type: List[str]
#     address: str
#     latitude: float
#     longitude: float
#     price_level: int  # 1-4 ($, $$, $$$, $$$$)
#     average_meal_cost: float
#     currency: str
#     rating: float  # 0-5
#     review_count: int
#     opening_hours: Dict[str, str]
#     dietary_options: List[str]  # vegetarian, vegan, gluten-free, halal
#     average_meal_time_minutes: int
#     reservations_available: bool
#     phone: Optional[str] = None
#     website: Optional[str] = None

#     def to_dict(self) -> Dict[str, Any]:
#         return self.__dict__


# class RestaurantAgent:
#     """Restaurant Agent - handles restaurant searches"""

#     def __init__(self, api_key: Optional[str] = None, use_mock: bool = True):
#         self.api_key = api_key or os.getenv('GOOGLE_PLACES_API_KEY')
#         self.use_mock = use_mock

#     def search_restaurants(self,
#                           location: str,
#                           cuisine_types: Optional[List[str]] = None,
#                           dietary_restrictions: Optional[List[str]] = None,
#                           max_price_level: int = 4,
#                           min_rating: float = 3.5,
#                           max_results: int = 10) -> List[RestaurantOption]:
#         """Search for restaurants"""
#         if self.use_mock:
#             return self._mock_restaurant_search(
#                 location, cuisine_types, dietary_restrictions,
#                 max_price_level, min_rating, max_results
#             )

#         return self._mock_restaurant_search(
#             location, cuisine_types, dietary_restrictions,
#             max_price_level, min_rating, max_results
#         )

#     def _mock_restaurant_search(self, location, cuisine_types, dietary_restrictions,
#                                max_price_level, min_rating, max_results) -> List[RestaurantOption]:
#         """Generate mock restaurant data"""

#         restaurant_names = [
#             "Sushi Zen", "Tokyo Ramen House", "Vegetarian Delight",
#             "Tempura Garden", "Modern Asian Fusion", "Green Leaf Cafe",
#             "Traditional Japanese Kitchen", "Noodle Paradise",
#             "Healthy Bites", "Sakura Restaurant"
#         ]

#         all_cuisines = ['Japanese', 'Asian', 'Vegetarian', 'Sushi', 'Ramen', 'Fusion']

#         if cuisine_types is None:
#             cuisine_types = all_cuisines

#         restaurants = []

#         for i in range(max_results):
#             # Random attributes
#             price_level = random.randint(1, max_price_level)
#             rating = random.uniform(max(min_rating, 3.5), 5.0)

#             # Average meal cost based on price level
#             base_costs = {1: 500, 2: 1000, 3: 2000, 4: 4000}
#             meal_cost = base_costs[price_level] * random.uniform(0.8, 1.2)

#             # Dietary options
#             dietary_opts = []
#             if dietary_restrictions:
#                 dietary_opts = dietary_restrictions.copy()
#             else:
#                 dietary_opts = random.sample(
#                     ['vegetarian', 'vegan', 'gluten-free'],
#                     k=random.randint(1, 2)
#                 )

#             # Opening hours (simplified)
#             hours = {
#                 'monday': '11:00-22:00',
#                 'tuesday': '11:00-22:00',
#                 'wednesday': '11:00-22:00',
#                 'thursday': '11:00-22:00',
#                 'friday': '11:00-23:00',
#                 'saturday': '11:00-23:00',
#                 'sunday': '11:00-21:00'
#             }

#             restaurant = RestaurantOption(
#                 restaurant_id=f"REST{i+1}_{location[:3].upper()}",
#                 name=random.choice(restaurant_names),
#                 cuisine_type=random.sample(cuisine_types, k=min(2, len(cuisine_types))),
#                 address=f"{random.randint(1,100)} District, {location}",
#                 latitude=35.6762 + random.uniform(-0.05, 0.05),
#                 longitude=139.6503 + random.uniform(-0.05, 0.05),
#                 price_level=price_level,
#                 average_meal_cost=round(meal_cost, 2),
#                 currency='INR',
#                 rating=round(rating, 1),
#                 review_count=random.randint(20, 500),
#                 opening_hours=hours,
#                 dietary_options=dietary_opts,
#                 average_meal_time_minutes=random.randint(45, 90),
#                 reservations_available=random.choice([True, False]),
#                 phone=f"+81-{random.randint(10,99)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
#                 website=f"https://www.{restaurant_names[i % len(restaurant_names)].lower().replace(' ', '')}.com"
#             )
#             restaurants.append(restaurant)

#         # Filter by dietary restrictions
#         if dietary_restrictions:
#             restaurants = [
#                 r for r in restaurants
#                 if any(diet in r.dietary_options for diet in dietary_restrictions)
#             ]

#         # Sort by rating
#         restaurants.sort(key=lambda x: x.rating, reverse=True)

#         return restaurants[:max_results]

#     def filter_by_opening_hours(self, restaurants: List[RestaurantOption],
#                                day: str, time: str) -> List[RestaurantOption]:
#         """Filter restaurants open at specific day/time"""
#         # Simplified check
#         return [r for r in restaurants if day.lower() in r.opening_hours]

#     def rank_restaurants(self, restaurants: List[RestaurantOption],
#                         weight_price: float = 0.3,
#                         weight_rating: float = 0.5,
#                         weight_reviews: float = 0.2) -> List[RestaurantOption]:
#         """Rank restaurants based on multiple criteria"""
#         if not restaurants:
#             return []

#         max_cost = max(r.average_meal_cost for r in restaurants)
#         max_reviews = max(r.review_count for r in restaurants)

#         scored = []
#         for restaurant in restaurants:
#             price_score = 1 - (restaurant.average_meal_cost / max_cost)
#             rating_score = restaurant.rating / 5.0
#             review_score = restaurant.review_count / max_reviews if max_reviews > 0 else 0

#             total_score = (
#                 weight_price * price_score +
#                 weight_rating * rating_score +
#                 weight_reviews * review_score
#             )

#             scored.append((total_score, restaurant))

#         scored.sort(key=lambda x: x[0], reverse=True)
#         return [restaurant for _, restaurant in scored]


# if __name__ == "__main__":
#     agent = RestaurantAgent(use_mock=True)

#     print("Searching vegetarian restaurants in Tokyo...")
#     restaurants = agent.search_restaurants(
#         location="Tokyo",
#         dietary_restrictions=['vegetarian'],
#         max_price_level=3,
#         max_results=5
#     )

#     print(f"\nFound {len(restaurants)} restaurants:")
#     for i, rest in enumerate(restaurants, 1):
#         print(f"\n{i}. {rest.name}")
#         print(f"   Cuisine: {', '.join(rest.cuisine_type)}")
#         print(f"   Rating: {rest.rating}/5 ({rest.review_count} reviews)")
#         print(f"   Price: {rest.currency} {rest.average_meal_cost} (Level {rest.price_level})")
#         print(f"   Dietary: {', '.join(rest.dietary_options)}")
#         print(f"   Reservations: {'Yes' if rest.reservations_available else 'No'}")
"""
Restaurant Agent - CORRECTED Overpass Query Format
Uses CORRECT Overpass query syntax with bounding boxes and cuisine filtering
"""

import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import random
import math


@dataclass
class RestaurantOption:
    """Restaurant data"""
    restaurant_id: str
    name: str
    cuisine_type: List[str]
    address: str
    latitude: float
    longitude: float
    price_level: int
    average_meal_cost: float
    currency: str
    rating: float
    review_count: int
    opening_hours: Dict[str, str]
    dietary_options: List[str]
    average_meal_time_minutes: int
    reservations_available: bool
    phone: Optional[str] = None
    website: Optional[str] = None
    source: str = "OpenStreetMap"


class RestaurantAgent:
    """CORRECTED Restaurant Agent - Proper Overpass Queries"""

    def __init__(self):
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.headers = {'User-Agent': 'TravelPlannerApp/1.0 (student project)'}

    def search_restaurants(self, location: str, cuisine_types: Optional[List[str]] = None,
                          dietary_restrictions: Optional[List[str]] = None,
                          max_price_level: int = 4, min_rating: float = 3.5,
                          radius_km: float = 5.0, max_results: int = 15) -> List[RestaurantOption]:
        """CORRECTED: Search restaurants with proper Overpass queries"""

        print(f"🔍 Searching restaurants in {location}...")

        # Get location coordinates
        location_coords = self._get_location_coordinates(location)
        if not location_coords:
            print(f"  ❌ Location not found")
            return []

        lat, lon = location_coords
        print(f"  ✓ Found location: {location} ({lat:.4f}, {lon:.4f})")

        # Search using CORRECTED Overpass query
        restaurants = self._search_via_overpass(lat, lon, radius_km, max_results)

        # Filter by dietary
        if dietary_restrictions:
            restaurants = [r for r in restaurants
                         if any(d in r.dietary_options for d in dietary_restrictions)]

        restaurants.sort(key=lambda x: x.rating, reverse=True)
        restaurants = [r for r in restaurants if r.rating >= min_rating]

        print(f"  ✓ Found {len(restaurants)} restaurants")
        return restaurants[:max_results]

    def _get_location_coordinates(self, location: str) -> Optional[tuple]:
        """Get location coordinates"""
        try:
            params = {'q': location, 'format': 'json', 'limit': 1}
            response = requests.get(self.nominatim_url, params=params,
                                   headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data:
                return (float(data[0]['lat']), float(data[0]['lon']))
            return None
        except Exception as e:
            print(f"  ❌ Location error: {e}")
            return None

    def _search_via_overpass(self, lat: float, lon: float,
                            radius_km: float, max_results: int) -> List[RestaurantOption]:
        """CORRECTED: Search via Overpass with CORRECT query format"""
        try:
            # CORRECTED: Proper bounding box (south, west, north, east)
            lat1 = lat - (radius_km / 111.0)  # south
            lon1 = lon - (radius_km / 111.0)  # west
            lat2 = lat + (radius_km / 111.0)  # north
            lon2 = lon + (radius_km / 111.0)  # east

            # Build the CORRECT query for restaurants with amenity tag
            query = f"""[out:json][timeout:25];
(
  node["amenity"="restaurant"]({lat1},{lon1},{lat2},{lon2});
  way["amenity"="restaurant"]({lat1},{lon1},{lat2},{lon2});
);
out body;
>;
out skel qt;
"""

            print(f"  🔍 Querying Overpass for restaurants...")
            response = requests.post(self.overpass_url, data=query,
                                    headers=self.headers, timeout=60)

            if response.status_code != 200:
                print(f"  ❌ Overpass error {response.status_code}")
                return []

            data = response.json()
            restaurants = []

            elements = data.get('elements', [])
            print(f"  Found {len(elements)} raw elements")

            for i, element in enumerate(elements[:max_results]):
                if 'tags' not in element or 'name' not in element['tags']:
                    continue

                # Get coordinates
                if 'lat' in element and 'lon' in element:
                    coords = {'lat': element['lat'], 'lon': element['lon']}
                else:
                    continue

                tags = element['tags']
                name = tags.get('name', f'Restaurant {i}')

                restaurant = RestaurantOption(
                    restaurant_id=f"REST_{element.get('id', i)}",
                    name=name,
                    cuisine_type=self._parse_cuisines(tags.get('cuisine', '')),
                    address=self._get_address(tags),
                    latitude=float(coords['lat']),
                    longitude=float(coords['lon']),
                    price_level=self._estimate_price_level(tags),
                    average_meal_cost=self._estimate_meal_cost(tags),
                    currency='INR',
                    rating=self._estimate_rating(tags),
                    review_count=random.randint(20, 500),
                    opening_hours=self._parse_hours(tags),
                    dietary_options=self._parse_dietary(tags),
                    average_meal_time_minutes=60,
                    reservations_available=True,
                    phone=tags.get('phone'),
                    website=tags.get('website'),
                    source="OpenStreetMap"
                )
                restaurants.append(restaurant)

            if restaurants:
                print(f"  ✓ Extracted {len(restaurants)} restaurants")

            return restaurants

        except Exception as e:
            print(f"  ❌ Overpass error: {e}")
            return []

    def _parse_cuisines(self, cuisine_str: str) -> List[str]:
        """Parse cuisine types"""
        if not cuisine_str:
            return ['Mixed']
        cuisines = [c.strip().title() for c in cuisine_str.split(';')]
        return cuisines[:3] if cuisines else ['Mixed']

    def _get_address(self, tags: dict) -> str:
        """Extract address"""
        parts = []
        for key in ['addr:street', 'addr:city', 'addr:postcode']:
            if key in tags:
                parts.append(str(tags[key]))
        return ', '.join(parts) if parts else 'Address available'

    def _estimate_price_level(self, tags: dict) -> int:
        """Estimate price level"""
        if 'price_level' in tags:
            try:
                return min(4, int(tags['price_level']))
            except:
                pass
        return random.randint(1, 3)

    def _estimate_meal_cost(self, tags: dict) -> float:
        """Estimate meal cost"""
        level = self._estimate_price_level(tags)
        costs = {1: 300, 2: 700, 3: 1500, 4: 3000}
        return costs.get(level, 500) * random.uniform(0.8, 1.2)

    def _estimate_rating(self, tags: dict) -> float:
        """Estimate rating"""
        if 'rating' in tags:
            try:
                return float(tags['rating'])
            except:
                pass
        return random.uniform(3.5, 5.0)

    def _parse_hours(self, tags: dict) -> Dict[str, str]:
        """Parse opening hours"""
        if 'opening_hours' in tags:
            return {'hours': tags['opening_hours']}
        return {'default': '11:00-22:00'}

    def _parse_dietary(self, tags: dict) -> List[str]:
        """Parse dietary options"""
        options = []
        if tags.get('diet:vegetarian') == 'yes':
            options.append('vegetarian')
        if tags.get('diet:vegan') == 'yes':
            options.append('vegan')
        return options if options else ['vegetarian', 'mixed']

    def rank_restaurants(self, restaurants: List[RestaurantOption]) -> List[RestaurantOption]:
        """Rank restaurants"""
        if not restaurants:
            return []

        restaurants.sort(key=lambda x: x.rating, reverse=True)
        return restaurants