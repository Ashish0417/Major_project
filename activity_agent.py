# """
# Activity & Experience Agent Module
# Handles activity and experience recommendations
# """

# import os
# from typing import List, Dict, Optional, Any
# from dataclasses import dataclass
# import random


# @dataclass
# class ActivityOption:
#     """Activity option data structure"""
#     activity_id: str
#     name: str
#     category: str  # museum, tour, outdoor, culinary, cultural, adventure
#     description: str
#     address: str
#     latitude: float
#     longitude: float
#     duration_minutes: int
#     price: float
#     currency: str
#     rating: float  # 0-5
#     review_count: int
#     popularity_score: float  # 0-1
#     opening_hours: Dict[str, str]
#     time_slots: List[str]  # Available time slots
#     booking_required: bool
#     suitable_for: List[str]  # families, solo, groups, couples
#     difficulty_level: str  # easy, moderate, hard
#     indoor_outdoor: str  # indoor, outdoor, both

#     def to_dict(self) -> Dict[str, Any]:
#         return self.__dict__


# class ActivityAgent:
#     """Activity & Experience Agent - handles activity searches"""

#     def __init__(self, api_key: Optional[str] = None, use_mock: bool = True):
#         self.api_key = api_key or os.getenv('VIATOR_API_KEY')
#         self.use_mock = use_mock

#     def search_activities(self,
#                          location: str,
#                          categories: Optional[List[str]] = None,
#                          interests: Optional[List[str]] = None,
#                          max_duration_minutes: Optional[int] = None,
#                          max_price: Optional[float] = None,
#                          min_rating: float = 3.5,
#                          max_results: int = 15) -> List[ActivityOption]:
#         """Search for activities and experiences"""
#         if self.use_mock:
#             return self._mock_activity_search(
#                 location, categories, interests, max_duration_minutes,
#                 max_price, min_rating, max_results
#             )

#         return self._mock_activity_search(
#             location, categories, interests, max_duration_minutes,
#             max_price, min_rating, max_results
#         )

#     def _mock_activity_search(self, location, categories, interests,
#                              max_duration_minutes, max_price, min_rating,
#                              max_results) -> List[ActivityOption]:
#         """Generate mock activity data"""

#         activity_data = {
#             'museums': [
#                 ('Tokyo National Museum', 'Largest art museum in Japan', 180, 1200),
#                 ('Mori Art Museum', 'Contemporary art museum', 120, 1800),
#                 ('teamLab Borderless', 'Digital art museum', 150, 2500),
#             ],
#             'culinary': [
#                 ('Sushi Making Workshop', 'Learn to make authentic sushi', 120, 3500),
#                 ('Tokyo Food Tour', 'Explore local food markets', 180, 4000),
#                 ('Ramen Cooking Class', 'Master the art of ramen', 150, 3000),
#             ],
#             'outdoor': [
#                 ('Mount Fuji Day Trip', 'Visit Japan\'s iconic mountain', 600, 5000),
#                 ('Tokyo Bay Cruise', 'Scenic bay cruise', 90, 2500),
#                 ('Imperial Palace Gardens Walk', 'Historical gardens tour', 120, 800),
#             ],
#             'cultural': [
#                 ('Tea Ceremony Experience', 'Traditional Japanese tea ceremony', 90, 2000),
#                 ('Kimono Wearing Experience', 'Dress in traditional kimono', 60, 2500),
#                 ('Samurai Museum Tour', 'Learn about samurai history', 90, 1500),
#             ],
#             'tour': [
#                 ('Tokyo City Highlights', 'Full-day city tour', 480, 6000),
#                 ('Night Tokyo Tour', 'Experience Tokyo nightlife', 180, 3500),
#                 ('Asakusa Walking Tour', 'Explore historic Asakusa', 150, 1200),
#             ]
#         }

#         if categories is None:
#             categories = list(activity_data.keys())

#         activities = []
#         activity_count = 0

#         for category in categories:
#             if category not in activity_data:
#                 continue

#             for name, desc, duration, base_price in activity_data[category]:
#                 if activity_count >= max_results:
#                     break

#                 # Apply price variation
#                 price = base_price * random.uniform(0.9, 1.1)

#                 if max_price and price > max_price:
#                     continue

#                 if max_duration_minutes and duration > max_duration_minutes:
#                     continue

#                 rating = random.uniform(max(min_rating, 4.0), 5.0)

#                 # Opening hours
#                 hours = {
#                     'monday': '09:00-17:00',
#                     'tuesday': '09:00-17:00',
#                     'wednesday': '09:00-17:00',
#                     'thursday': '09:00-17:00',
#                     'friday': '09:00-18:00',
#                     'saturday': '09:00-18:00',
#                     'sunday': '09:00-17:00'
#                 }

#                 # Time slots
#                 time_slots = ['09:00', '11:00', '13:00', '15:00']

#                 activity = ActivityOption(
#                     activity_id=f"ACT{activity_count+1}_{category.upper()[:3]}",
#                     name=name,
#                     category=category,
#                     description=desc,
#                     address=f"{random.randint(1,50)} District, {location}",
#                     latitude=35.6762 + random.uniform(-0.08, 0.08),
#                     longitude=139.6503 + random.uniform(-0.08, 0.08),
#                     duration_minutes=duration,
#                     price=round(price, 2),
#                     currency='INR',
#                     rating=round(rating, 1),
#                     review_count=random.randint(50, 2000),
#                     popularity_score=random.uniform(0.7, 1.0),
#                     opening_hours=hours,
#                     time_slots=time_slots,
#                     booking_required=random.choice([True, False]),
#                     suitable_for=random.sample(['families', 'solo', 'groups', 'couples'], k=2),
#                     difficulty_level=random.choice(['easy', 'moderate']),
#                     indoor_outdoor=random.choice(['indoor', 'outdoor', 'both'])
#                 )
#                 activities.append(activity)
#                 activity_count += 1

#         # Sort by popularity and rating
#         activities.sort(key=lambda x: (x.popularity_score, x.rating), reverse=True)

#         return activities[:max_results]

#     def filter_by_interests(self, activities: List[ActivityOption],
#                            interests: List[str]) -> List[ActivityOption]:
#         """Filter activities by user interests"""
#         if not interests:
#             return activities

#         # Map interests to categories
#         interest_mapping = {
#             'museums': ['museums', 'cultural'],
#             'art': ['museums', 'cultural'],
#             'culinary': ['culinary'],
#             'food': ['culinary'],
#             'hiking': ['outdoor'],
#             'outdoor': ['outdoor'],
#             'culture': ['cultural'],
#             'history': ['cultural', 'museums'],
#             'adventure': ['outdoor', 'tour']
#         }

#         relevant_categories = set()
#         for interest in interests:
#             if interest.lower() in interest_mapping:
#                 relevant_categories.update(interest_mapping[interest.lower()])

#         if not relevant_categories:
#             return activities

#         return [act for act in activities if act.category in relevant_categories]

#     def rank_activities(self, activities: List[ActivityOption],
#                        weight_price: float = 0.2,
#                        weight_rating: float = 0.3,
#                        weight_popularity: float = 0.3,
#                        weight_duration: float = 0.2) -> List[ActivityOption]:
#         """Rank activities based on multiple criteria"""
#         if not activities:
#             return []

#         max_price = max(act.price for act in activities)
#         max_duration = max(act.duration_minutes for act in activities)

#         scored = []
#         for activity in activities:
#             price_score = 1 - (activity.price / max_price) if max_price > 0 else 1
#             rating_score = activity.rating / 5.0
#             popularity_score = activity.popularity_score
#             # Shorter activities score higher for flexibility
#             duration_score = 1 - (activity.duration_minutes / max_duration) if max_duration > 0 else 1

#             total_score = (
#                 weight_price * price_score +
#                 weight_rating * rating_score +
#                 weight_popularity * popularity_score +
#                 weight_duration * duration_score
#             )

#             scored.append((total_score, activity))

#         scored.sort(key=lambda x: x[0], reverse=True)
#         return [activity for _, activity in scored]

#     def mark_must_do(self, activity: ActivityOption) -> None:
#         """Mark an activity as must-do"""
#         activity.popularity_score = min(1.0, activity.popularity_score + 0.1)


# if __name__ == "__main__":
#     agent = ActivityAgent(use_mock=True)

#     print("Searching activities in Tokyo...")
#     activities = agent.search_activities(
#         location="Tokyo",
#         categories=['museums', 'culinary', 'outdoor'],
#         max_results=8
#     )

#     print(f"\nFound {len(activities)} activities:")
#     for i, act in enumerate(activities, 1):
#         print(f"\n{i}. {act.name} ({act.category})")
#         print(f"   {act.description}")
#         print(f"   Duration: {act.duration_minutes} mins")
#         print(f"   Price: {act.currency} {act.price}")
#         print(f"   Rating: {act.rating}/5 ({act.review_count} reviews)")
#         print(f"   Popularity: {act.popularity_score:.2f}")

#     # Filter by interests
#     print("\n" + "="*50)
#     print("Filtering by interests: museums, culinary...")
#     filtered = agent.filter_by_interests(activities, ['museums', 'culinary'])
#     print(f"Filtered to {len(filtered)} activities")


"""
Activity & Experience Agent Module - FIXED VERSION
Addresses common integration issues:
1. Better coordinate handling for mock data
2. Improved error handling
3. More reliable fallback mechanisms
4. Better logging
"""

import os
import requests
import random
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class ActivityOption:
    """Activity option data structure"""
    activity_id: str
    name: str
    category: str  # museum, tour, outdoor, culinary, cultural, adventure
    description: str
    address: str
    latitude: float
    longitude: float
    duration_minutes: int
    price: float
    currency: str
    rating: float  # 0-5
    review_count: int
    popularity_score: float  # 0-1
    opening_hours: Dict[str, str]
    time_slots: List[str]  # Available time slots
    booking_required: bool
    suitable_for: List[str]  # families, solo, groups, couples
    difficulty_level: str  # easy, moderate, hard
    indoor_outdoor: str  # indoor, outdoor, both
    website: Optional[str] = None
    phone: Optional[str] = None
    source: str = "API"  # API or Mock

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


class ActivityAgent:
    """Activity & Experience Agent - uses REAL APIs for activity searches"""

    # City coordinates for better mock data
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
    }

    def __init__(self, google_api_key: Optional[str] = None):
        """
        Initialize with Google Places API key
        Falls back to Overpass API if Google fails
        """
        self.google_api_key = google_api_key or os.getenv('GOOGLE_PLACES_API_KEY')
        
        # Overpass API endpoints (multiple for redundancy)
        self.overpass_urls = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.openstreetmap.ru/api/interpreter",
        ]
        
        self.headers = {'User-Agent': 'TravelPlannerApp/1.0 (student project)'}
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
        # Nominatim for geocoding
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"

    def search_activities(self,
                         location: str,
                         categories: Optional[List[str]] = None,
                         interests: Optional[List[str]] = None,
                         max_duration_minutes: Optional[int] = None,
                         max_price: Optional[float] = None,
                         min_rating: float = 3.5,
                         max_results: int = 15) -> List[ActivityOption]:
        """
        Search for activities and experiences using real APIs
        
        Strategy:
        1. Try Google Places API (if key available)
        2. Fall back to Overpass API
        3. Fall back to mock data
        """
        print(f"\n🎯 Searching activities in {location}...")
        
        # Get coordinates for the location
        coords = self._get_coordinates(location)
        if not coords:
            print(f"   ⚠️ Could not geocode {location}, using default coordinates")
            # Use city defaults or reasonable defaults
            coords = self._get_default_coords(location)
        
        lat, lon = coords
        print(f"   ✓ Location: {location} ({lat:.4f}, {lon:.4f})")
        
        activities = []
        
        # Try Google Places API first
        if self.google_api_key:
            print(f"   🔍 Trying Google Places API...")
            try:
                activities = self._search_google_places(
                    lat, lon, location, categories, max_results
                )
            except Exception as e:
                print(f"   ⚠️  Google Places failed: {str(e)[:50]}")
        
        # If Google fails or no key, try Overpass
        if not activities:
            print(f"   🔍 Trying Overpass API...")
            try:
                activities = self._search_overpass(
                    lat, lon, location, categories, max_results
                )
            except Exception as e:
                print(f"   ⚠️  Overpass failed: {str(e)[:50]}")
        
        # If both fail, use mock data WITH PROPER COORDINATES
        if not activities:
            print(f"   ⚠️ All APIs failed, generating mock data")
            activities = self._generate_mock_activities(
                location, categories, max_results, coords=coords
            )
        
        # Filter by interests
        if interests:
            activities = self.filter_by_interests(activities, interests)
        
        # Filter by constraints
        if max_price:
            activities = [a for a in activities if a.price <= max_price]
        if max_duration_minutes:
            activities = [a for a in activities if a.duration_minutes <= max_duration_minutes]
        
        # Rank activities
        activities = self.rank_activities(activities)
        
        print(f"   ✅ Returning {len(activities)} activities")
        return activities[:max_results]

    def _get_coordinates(self, location: str) -> Optional[tuple]:
        """Get coordinates from location name using Nominatim"""
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
            print(f"   ⚠️ Geocoding error: {str(e)[:50]}")
            return None

    def _get_default_coords(self, location: str) -> tuple:
        """Get default coordinates for known cities or generate reasonable ones"""
        # Check if location matches known cities
        location_lower = location.lower()
        for city, coords in self.CITY_COORDINATES.items():
            if city in location_lower:
                return coords
        
        # Default to Tokyo coordinates as fallback
        return self.CITY_COORDINATES['tokyo']

    def _search_google_places(self, lat: float, lon: float, 
                             location: str, categories: Optional[List[str]],
                             max_results: int) -> List[ActivityOption]:
        """Search using Google Places API"""
        
        # Map categories to Google Places types
        category_mapping = {
            'museums': ['museum', 'art_gallery'],
            'cultural': ['museum', 'art_gallery', 'place_of_worship', 'tourist_attraction'],
            'outdoor': ['park', 'amusement_park', 'zoo', 'aquarium'],
            'culinary': ['restaurant', 'cafe', 'bakery'],
            'tour': ['tourist_attraction', 'point_of_interest'],
            'adventure': ['tourist_attraction', 'park']
        }
        
        # Determine which types to search
        if categories:
            types_to_search = set()
            for cat in categories:
                if cat in category_mapping:
                    types_to_search.update(category_mapping[cat])
        else:
            types_to_search = {'tourist_attraction', 'museum', 'park', 'art_gallery'}
        
        activities = []
        
        for place_type in types_to_search:
            if len(activities) >= max_results:
                break
            
            try:
                self._apply_rate_limit()
                
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    'location': f"{lat},{lon}",
                    'radius': 10000,  # 10km radius
                    'type': place_type,
                    'key': self.google_api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for place in data.get('results', [])[:5]:  # Top 5 per type
                        activity = self._parse_google_place(place, location)
                        if activity:
                            activities.append(activity)
                
            except Exception as e:
                print(f"   ⚠️ Google API error for {place_type}: {str(e)[:30]}")
                continue
        
        return activities[:max_results]

    def _parse_google_place(self, place: dict, location: str) -> Optional[ActivityOption]:
        """Parse Google Place result into ActivityOption"""
        try:
            name = place.get('name', 'Unknown Activity')
            
            # Determine category from types
            place_types = place.get('types', [])
            category = self._determine_category(place_types)
            
            # Get location
            loc = place.get('geometry', {}).get('location', {})
            lat = loc.get('lat', 0.0)
            lon = loc.get('lng', 0.0)
            
            # Rating and reviews
            rating = place.get('rating', 4.0)
            review_count = place.get('user_ratings_total', 100)
            
            # Estimate duration based on category
            duration = self._estimate_duration(category)
            
            # Estimate price based on price_level (0-4)
            price_level = place.get('price_level', 2)
            price = self._estimate_price(category, price_level)
            
            # Generate activity
            activity_id = f"ACT_{place.get('place_id', random.randint(1000, 9999))}"
            
            return ActivityOption(
                activity_id=activity_id,
                name=name,
                category=category,
                description=f"{category.capitalize()} in {location}",
                address=place.get('vicinity', location),
                latitude=lat,
                longitude=lon,
                duration_minutes=duration,
                price=price,
                currency='INR',
                rating=min(rating, 5.0),
                review_count=review_count,
                popularity_score=min(rating / 5.0, 1.0),
                opening_hours=self._parse_opening_hours(place.get('opening_hours', {})),
                time_slots=self._generate_time_slots(category),
                booking_required=category in ['tour', 'adventure', 'culinary'],
                suitable_for=self._determine_suitable_for(category),
                difficulty_level=self._determine_difficulty(category),
                indoor_outdoor=self._determine_indoor_outdoor(category),
                website=None,
                phone=None,
                source="Google Places API"
            )
        except Exception as e:
            print(f"   ⚠️ Parse error: {str(e)[:30]}")
            return None

    def _search_overpass(self, lat: float, lon: float,
                        location: str, categories: Optional[List[str]],
                        max_results: int) -> List[ActivityOption]:
        """Search using Overpass API (OpenStreetMap)"""
        
        # Map categories to OSM tags
        osm_mapping = {
            'museums': ['museum'],
            'cultural': ['museum', 'theatre', 'arts_centre'],
            'outdoor': ['park', 'viewpoint', 'attraction'],
            'tour': ['attraction', 'viewpoint'],
            'adventure': ['park', 'attraction']
        }
        
        # Determine tags to search
        tags_to_search = set()
        if categories:
            for cat in categories:
                if cat in osm_mapping:
                    tags_to_search.update(osm_mapping[cat])
        else:
            tags_to_search = {'museum', 'attraction', 'park', 'viewpoint'}
        
        # Try each Overpass server
        for server_index, overpass_url in enumerate(self.overpass_urls, 1):
            try:
                print(f"      Trying Overpass server {server_index}/{len(self.overpass_urls)}...")
                
                self._apply_rate_limit()
                
                # Build query
                radius_km = 10
                lat1 = lat - (radius_km / 111.0)
                lon1 = lon - (radius_km / 111.0)
                lat2 = lat + (radius_km / 111.0)
                lon2 = lon + (radius_km / 111.0)
                
                query_parts = []
                for tag in tags_to_search:
                    query_parts.append(f'node["tourism"="{tag}"]({lat1},{lon1},{lat2},{lon2});')
                    query_parts.append(f'way["tourism"="{tag}"]({lat1},{lon1},{lat2},{lon2});')
                
                query = f"""[out:json][timeout:15];
(
  {'  '.join(query_parts)}
);
out center {max_results * 2};
"""
                
                response = requests.post(
                    overpass_url,
                    data=query,
                    headers=self.headers,
                    timeout=20
                )
                
                if response.status_code == 200:
                    data = response.json()
                    activities = self._parse_overpass_results(
                        data, location, categories
                    )
                    
                    if activities:
                        print(f"      ✅ Server {server_index} succeeded!")
                        return activities[:max_results]
                
            except Exception as e:
                print(f"      ⚠️ Server {server_index} error: {str(e)[:30]}")
                continue
        
        return []

    def _parse_overpass_results(self, data: dict, location: str,
                                categories: Optional[List[str]]) -> List[ActivityOption]:
        """Parse Overpass API results"""
        activities = []
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
                    coords = {'lat': element['center']['lat'], 'lon': element['center']['lon']}
                else:
                    continue
                
                name = tags.get('name')
                tourism_type = tags.get('tourism', 'attraction')
                
                # Determine category
                category = self._osm_to_category(tourism_type)
                
                # Skip if not in requested categories
                if categories and category not in categories:
                    continue
                
                # Duration and price estimation
                duration = self._estimate_duration(category)
                price = self._estimate_price(category, price_level=1)
                
                activity = ActivityOption(
                    activity_id=f"ACT_OSM_{element.get('id', i)}",
                    name=name,
                    category=category,
                    description=tags.get('description', f"{category.capitalize()} in {location}"),
                    address=self._get_address_from_tags(tags, location),
                    latitude=coords['lat'],
                    longitude=coords['lon'],
                    duration_minutes=duration,
                    price=price,
                    currency='INR',
                    rating=random.uniform(4.0, 4.8),
                    review_count=random.randint(50, 500),
                    popularity_score=random.uniform(0.7, 0.9),
                    opening_hours=self._parse_osm_opening_hours(tags),
                    time_slots=self._generate_time_slots(category),
                    booking_required=category in ['tour', 'adventure', 'culinary'],
                    suitable_for=self._determine_suitable_for(category),
                    difficulty_level=self._determine_difficulty(category),
                    indoor_outdoor=self._determine_indoor_outdoor(category),
                    website=tags.get('website'),
                    phone=tags.get('phone'),
                    source="OpenStreetMap"
                )
                
                activities.append(activity)
                
            except Exception as e:
                continue
        
        return activities

    def _generate_mock_activities(self, location: str,
                                  categories: Optional[List[str]],
                                  max_results: int,
                                  coords: Optional[tuple] = None) -> List[ActivityOption]:
        """
        Generate mock activity data as fallback
        FIXED: Now uses proper coordinates instead of (0, 0)
        """
        print(f"      Generating {max_results} mock activities...")
        
        # Use provided coords or get defaults
        if coords:
            base_lat, base_lon = coords
        else:
            base_lat, base_lon = self._get_default_coords(location)
        
        activity_templates = {
            'museums': [
                ('National Museum', 'Largest art and history museum', 180, 1200),
                ('Modern Art Gallery', 'Contemporary art exhibitions', 120, 800),
                ('Science Museum', 'Interactive science exhibits', 150, 1000),
            ],
            'cultural': [
                ('Cultural Center', 'Traditional cultural experiences', 120, 1500),
                ('Heritage Site Tour', 'Historical monuments tour', 180, 2000),
                ('Local Craft Workshop', 'Learn traditional crafts', 90, 1200),
            ],
            'outdoor': [
                ('City Park Walk', 'Scenic park exploration', 90, 500),
                ('Botanical Gardens', 'Beautiful garden tour', 120, 800),
                ('Viewpoint Visit', 'Panoramic city views', 60, 300),
            ],
            'culinary': [
                ('Cooking Class', 'Learn local cuisine', 120, 2500),
                ('Food Tour', 'Explore local markets', 180, 3000),
                ('Street Food Walk', 'Taste authentic street food', 150, 1500),
            ],
            'tour': [
                ('City Highlights Tour', 'Full-day city exploration', 480, 4000),
                ('Walking Tour', 'Historic district walk', 150, 1000),
                ('Night Tour', 'Evening city experience', 180, 2500),
            ],
            'adventure': [
                ('Adventure Activity', 'Outdoor adventure', 240, 3500),
                ('Nature Trek', 'Scenic nature walk', 180, 2000),
                ('Water Sports', 'Lake/beach activities', 120, 2500),
            ]
        }
        
        if not categories:
            categories = list(activity_templates.keys())
        
        activities = []
        count = 0
        
        for category in categories:
            if category not in activity_templates:
                continue
            
            for name, desc, duration, price in activity_templates[category]:
                if count >= max_results:
                    break
                
                # Add location specificity
                localized_name = f"{name} - {location}"
                
                # Generate coordinates near the city center
                # Add small random offset (±0.05 degrees ≈ ±5km)
                activity_lat = base_lat + random.uniform(-0.05, 0.05)
                activity_lon = base_lon + random.uniform(-0.05, 0.05)
                
                activity = ActivityOption(
                    activity_id=f"ACT_MOCK_{count+1}",
                    name=localized_name,
                    category=category,
                    description=desc,
                    address=f"Central District, {location}",
                    latitude=activity_lat,  # FIXED: Use proper coordinates
                    longitude=activity_lon,  # FIXED: Use proper coordinates
                    duration_minutes=duration,
                    price=price * random.uniform(0.9, 1.1),
                    currency='INR',
                    rating=random.uniform(4.0, 4.8),
                    review_count=random.randint(100, 1000),
                    popularity_score=random.uniform(0.7, 0.95),
                    opening_hours={'daily': '09:00-18:00'},
                    time_slots=['09:00', '11:00', '14:00', '16:00'],
                    booking_required=category in ['culinary', 'tour', 'adventure'],
                    suitable_for=self._determine_suitable_for(category),
                    difficulty_level=self._determine_difficulty(category),
                    indoor_outdoor=self._determine_indoor_outdoor(category),
                    source="Mock Data"
                )
                
                activities.append(activity)
                count += 1
        
        return activities

    # Helper methods
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _determine_category(self, types: List[str]) -> str:
        """Determine activity category from Google Place types"""
        if 'museum' in types or 'art_gallery' in types:
            return 'museums'
        elif 'park' in types or 'zoo' in types or 'aquarium' in types:
            return 'outdoor'
        elif 'restaurant' in types or 'cafe' in types:
            return 'culinary'
        elif 'place_of_worship' in types:
            return 'cultural'
        else:
            return 'tour'

    def _osm_to_category(self, osm_type: str) -> str:
        """Map OSM tourism type to our category"""
        mapping = {
            'museum': 'museums',
            'gallery': 'museums',
            'attraction': 'tour',
            'viewpoint': 'outdoor',
            'park': 'outdoor',
            'theatre': 'cultural',
            'arts_centre': 'cultural'
        }
        return mapping.get(osm_type, 'tour')

    def _estimate_duration(self, category: str) -> int:
        """Estimate activity duration in minutes"""
        durations = {
            'museums': random.randint(90, 180),
            'cultural': random.randint(60, 120),
            'outdoor': random.randint(90, 180),
            'culinary': random.randint(120, 180),
            'tour': random.randint(120, 300),
            'adventure': random.randint(180, 360)
        }
        return durations.get(category, 120)

    def _estimate_price(self, category: str, price_level: int = 2) -> float:
        """Estimate activity price in INR"""
        base_prices = {
            'museums': 1000,
            'cultural': 1500,
            'outdoor': 800,
            'culinary': 2500,
            'tour': 3000,
            'adventure': 3500
        }
        
        base = base_prices.get(category, 1500)
        multiplier = 1.0 + (price_level * 0.3)  # 0-4 scale
        
        return round(base * multiplier * random.uniform(0.8, 1.2), 2)

    def _parse_opening_hours(self, hours_data: dict) -> Dict[str, str]:
        """Parse Google opening hours"""
        if hours_data.get('open_now'):
            return {'daily': '09:00-18:00'}
        return {'daily': '10:00-17:00'}

    def _parse_osm_opening_hours(self, tags: dict) -> Dict[str, str]:
        """Parse OSM opening hours"""
        if 'opening_hours' in tags:
            return {'daily': tags['opening_hours']}
        return {'daily': '09:00-17:00'}

    def _get_address_from_tags(self, tags: dict, location: str) -> str:
        """Extract address from OSM tags"""
        parts = []
        for key in ['addr:street', 'addr:city']:
            if key in tags:
                parts.append(tags[key])
        return ', '.join(parts) if parts else location

    def _generate_time_slots(self, category: str) -> List[str]:
        """Generate available time slots"""
        if category == 'culinary':
            return ['11:00', '13:00', '18:00', '20:00']
        elif category == 'tour':
            return ['09:00', '10:00', '14:00', '15:00']
        else:
            return ['09:00', '11:00', '13:00', '15:00']

    def _determine_suitable_for(self, category: str) -> List[str]:
        """Determine who the activity is suitable for"""
        if category == 'museums':
            return ['families', 'couples', 'solo']
        elif category == 'adventure':
            return ['groups', 'solo']
        elif category == 'culinary':
            return ['couples', 'groups', 'families']
        else:
            return ['families', 'couples']

    def _determine_difficulty(self, category: str) -> str:
        """Determine activity difficulty"""
        if category == 'adventure':
            return random.choice(['moderate', 'hard'])
        return 'easy'

    def _determine_indoor_outdoor(self, category: str) -> str:
        """Determine if activity is indoor/outdoor"""
        if category in ['museums', 'cultural', 'culinary']:
            return 'indoor'
        elif category in ['outdoor', 'adventure']:
            return 'outdoor'
        else:
            return 'both'

    # Existing methods from original implementation
    
    def filter_by_interests(self, activities: List[ActivityOption],
                           interests: List[str]) -> List[ActivityOption]:
        """Filter activities by user interests"""
        if not interests:
            return activities

        interest_mapping = {
            'museums': ['museums', 'cultural'],
            'art': ['museums', 'cultural'],
            'culinary': ['culinary'],
            'food': ['culinary'],
            'hiking': ['outdoor', 'adventure'],
            'outdoor': ['outdoor', 'adventure'],
            'culture': ['cultural', 'museums'],
            'history': ['cultural', 'museums'],
            'adventure': ['outdoor', 'tour', 'adventure']
        }

        relevant_categories = set()
        for interest in interests:
            if interest.lower() in interest_mapping:
                relevant_categories.update(interest_mapping[interest.lower()])

        if not relevant_categories:
            return activities

        return [act for act in activities if act.category in relevant_categories]

    def rank_activities(self, activities: List[ActivityOption],
                       weight_price: float = 0.2,
                       weight_rating: float = 0.3,
                       weight_popularity: float = 0.3,
                       weight_duration: float = 0.2) -> List[ActivityOption]:
        """Rank activities based on multiple criteria"""
        if not activities:
            return []

        max_price = max(act.price for act in activities) or 1
        max_duration = max(act.duration_minutes for act in activities) or 1

        scored = []
        for activity in activities:
            price_score = 1 - (activity.price / max_price)
            rating_score = activity.rating / 5.0
            popularity_score = activity.popularity_score
            duration_score = 1 - (activity.duration_minutes / max_duration)

            total_score = (
                weight_price * price_score +
                weight_rating * rating_score +
                weight_popularity * popularity_score +
                weight_duration * duration_score
            )

            scored.append((total_score, activity))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [activity for _, activity in scored]


if __name__ == "__main__":
    # Test with API key if available
    agent = ActivityAgent()

    print("="*80)
    print("TESTING FIXED ACTIVITY AGENT")
    print("="*80)
    
    print("\nTest 1: Museums in Tokyo")
    activities = agent.search_activities(
        location="Tokyo",
        categories=['museums', 'cultural'],
        max_results=5
    )

    print(f"\n✅ Found {len(activities)} activities:")
    for i, act in enumerate(activities, 1):
        print(f"\n{i}. {act.name} ({act.category})")
        print(f"   Source: {act.source}")
        print(f"   Location: ({act.latitude:.4f}, {act.longitude:.4f})")
        print(f"   Address: {act.address}")
        print(f"   Duration: {act.duration_minutes} mins | Price: {act.currency} {act.price}")
        print(f"   Rating: {act.rating}/5 ({act.review_count} reviews)")
        print(f"   Popularity: {act.popularity_score:.2f}")