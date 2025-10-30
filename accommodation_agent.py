# """
# Accommodation Agent Module
# Handles hotel and accommodation search
# """

# import os
# from typing import List, Dict, Optional, Any
# from dataclasses import dataclass
# import random


# @dataclass
# class AccommodationOption:
#     """Accommodation option data structure"""
#     accommodation_id: str
#     name: str
#     type: str  # hotel, apartment, hostel, guesthouse
#     address: str
#     latitude: float
#     longitude: float
#     price_per_night: float
#     currency: str
#     rating: float  # 0-5
#     review_count: int
#     amenities: List[str]
#     check_in_time: str
#     check_out_time: str
#     cancellation_policy: str
#     free_cancellation: bool
#     distance_to_center_km: float

#     def to_dict(self) -> Dict[str, Any]:
#         return self.__dict__


# class AccommodationAgent:
#     """Accommodation Agent - handles accommodation searches"""

#     def __init__(self, api_key: Optional[str] = None, use_mock: bool = True):
#         self.api_key = api_key or os.getenv('BOOKING_API_KEY')
#         self.use_mock = use_mock

#     def search_accommodations(self,
#                              destination: str,
#                              check_in: str,
#                              check_out: str,
#                              guests: int = 1,
#                              accommodation_types: Optional[List[str]] = None,
#                              max_price: Optional[float] = None,
#                              min_rating: float = 3.0,
#                              max_results: int = 10) -> List[AccommodationOption]:
#         """Search for accommodations"""
#         if self.use_mock:
#             return self._mock_accommodation_search(
#                 destination, check_in, check_out, accommodation_types,
#                 max_price, min_rating, max_results
#             )

#         # Real API implementation would go here
#         return self._mock_accommodation_search(
#             destination, check_in, check_out, accommodation_types,
#             max_price, min_rating, max_results
#         )

#     def _mock_accommodation_search(self, destination, check_in, check_out,
#                                    accommodation_types, max_price, min_rating,
#                                    max_results) -> List[AccommodationOption]:
#         """Generate mock accommodation data"""
#         if accommodation_types is None:
#             accommodation_types = ['hotel', 'apartment']

#         accommodations = []

#         # Sample hotel names
#         hotel_names = [
#             "Grand Palace Hotel", "Sakura Inn", "Modern Suites Tokyo",
#             "Traveler's Rest", "City View Apartments", "Budget Stay",
#             "Luxury Gardens Hotel", "Downtown Hostel", "Peaceful Retreat",
#             "Business Hub Hotel"
#         ]

#         amenities_pool = [
#             ['wifi', 'breakfast', 'parking', 'gym'],
#             ['wifi', 'kitchen', 'washing_machine'],
#             ['wifi', 'breakfast', 'pool', 'spa', 'restaurant'],
#             ['wifi', 'shared_kitchen', 'lounge'],
#             ['wifi', 'breakfast', 'airport_shuttle'],
#         ]

#         for i in range(max_results):
#             acc_type = random.choice(accommodation_types)

#             # Price ranges based on type
#             price_ranges = {
#                 'hotel': (3000, 10000),
#                 'apartment': (2500, 8000),
#                 'hostel': (800, 2500),
#                 'guesthouse': (1500, 4000)
#             }

#             min_p, max_p = price_ranges.get(acc_type, (2000, 6000))
#             price = random.uniform(min_p, max_p)

#             if max_price and price > max_price:
#                 price = max_price * random.uniform(0.7, 0.9)

#             rating = random.uniform(max(min_rating, 3.5), 5.0)

#             accommodation = AccommodationOption(
#                 accommodation_id=f"ACC{i+1}_{destination[:3].upper()}",
#                 name=random.choice(hotel_names),
#                 type=acc_type,
#                 address=f"{random.randint(1,100)} Street, {destination}",
#                 latitude=35.6762 + random.uniform(-0.1, 0.1),  # Tokyo coords
#                 longitude=139.6503 + random.uniform(-0.1, 0.1),
#                 price_per_night=round(price, 2),
#                 currency='INR',
#                 rating=round(rating, 1),
#                 review_count=random.randint(50, 1000),
#                 amenities=random.choice(amenities_pool),
#                 check_in_time="14:00",
#                 check_out_time="11:00",
#                 cancellation_policy="Free cancellation up to 24 hours before check-in",
#                 free_cancellation=random.choice([True, True, False]),
#                 distance_to_center_km=round(random.uniform(0.5, 10.0), 1)
#             )
#             accommodations.append(accommodation)

#         # Sort by rating
#         accommodations.sort(key=lambda x: x.rating, reverse=True)

#         return accommodations

#     def calculate_distance_to_activities(self, accommodation: AccommodationOption,
#                                         activities: List[Dict]) -> float:
#         """Calculate average distance from accommodation to activities"""
#         # Simplified distance calculation
#         # In real implementation, use proper distance APIs
#         import math

#         if not activities:
#             return 0.0

#         total_distance = 0.0
#         for activity in activities:
#             # Haversine formula (simplified)
#             lat_diff = abs(accommodation.latitude - activity.get('latitude', 0))
#             lon_diff = abs(accommodation.longitude - activity.get('longitude', 0))
#             distance = math.sqrt(lat_diff**2 + lon_diff**2) * 111  # Rough km conversion
#             total_distance += distance

#         return total_distance / len(activities)

#     def filter_by_amenities(self, accommodations: List[AccommodationOption],
#                            required_amenities: List[str]) -> List[AccommodationOption]:
#         """Filter accommodations by required amenities"""
#         if not required_amenities:
#             return accommodations

#         return [
#             acc for acc in accommodations
#             if all(amenity in acc.amenities for amenity in required_amenities)
#         ]

#     def rank_accommodations(self, accommodations: List[AccommodationOption],
#                            weight_price: float = 0.3,
#                            weight_rating: float = 0.4,
#                            weight_location: float = 0.3) -> List[AccommodationOption]:
#         """Rank accommodations based on multiple criteria"""
#         if not accommodations:
#             return []

#         max_price = max(acc.price_per_night for acc in accommodations)
#         max_distance = max(acc.distance_to_center_km for acc in accommodations)

#         scored = []
#         for acc in accommodations:
#             price_score = 1 - (acc.price_per_night / max_price)
#             rating_score = acc.rating / 5.0
#             location_score = 1 - (acc.distance_to_center_km / max_distance) if max_distance > 0 else 1

#             total_score = (
#                 weight_price * price_score +
#                 weight_rating * rating_score +
#                 weight_location * location_score
#             )

#             scored.append((total_score, acc))

#         scored.sort(key=lambda x: x[0], reverse=True)
#         return [acc for _, acc in scored]


# if __name__ == "__main__":
#     agent = AccommodationAgent(use_mock=True)

#     print("Searching accommodations in Tokyo...")
#     accommodations = agent.search_accommodations(
#         destination="Tokyo",
#         check_in="2026-03-20",
#         check_out="2026-03-27",
#         accommodation_types=['hotel', 'apartment'],
#         max_results=5
#     )

#     print(f"\nFound {len(accommodations)} accommodations:")
#     for i, acc in enumerate(accommodations, 1):
#         print(f"\n{i}. {acc.name} ({acc.type})")
#         print(f"   Rating: {acc.rating}/5 ({acc.review_count} reviews)")
#         print(f"   Price: {acc.currency} {acc.price_per_night}/night")
#         print(f"   Distance to center: {acc.distance_to_center_km} km")
#         print(f"   Amenities: {', '.join(acc.amenities)}")
"""
Accommodation Agent - CORRECTED Overpass Query Format
Uses CORRECT Overpass query syntax with bounding boxes
"""

import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import random
import math


@dataclass
class AccommodationOption:
    """Accommodation data"""
    accommodation_id: str
    name: str
    type: str
    address: str
    latitude: float
    longitude: float
    price_per_night: float
    currency: str
    rating: float
    review_count: int
    amenities: List[str]
    check_in_time: str
    check_out_time: str
    cancellation_policy: str
    free_cancellation: bool
    distance_to_center_km: float
    website: Optional[str] = None
    phone: Optional[str] = None
    source: str = "OpenStreetMap"


class AccommodationAgent:
    """CORRECTED Accommodation Agent - Proper Overpass Queries"""

    def __init__(self):
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.headers = {'User-Agent': 'TravelPlannerApp/1.0 (student project)'}

    def search_accommodations(self, destination: str, check_in: str, check_out: str,
                             guests: int = 1, accommodation_types: Optional[List[str]] = None,
                             max_price: Optional[float] = None, min_rating: float = 3.0,
                             radius_km: float = 10.0, max_results: int = 15) -> List[AccommodationOption]:
        """CORRECTED: Search accommodations with proper Overpass queries"""

        if accommodation_types is None:
            accommodation_types = ['hotel', 'apartment', 'guest_house']

        print(f"🔍 Searching accommodations in {destination}...")

        # Get location coordinates
        location_coords = self._get_location_coordinates(destination)
        if not location_coords:
            print(f"  ❌ Location not found")
            return []

        lat, lon = location_coords
        print(f"  ✓ Found location: {destination} ({lat:.4f}, {lon:.4f})")

        # Search using CORRECTED Overpass query
        accommodations = self._search_via_overpass(lat, lon, accommodation_types,
                                                  radius_km, max_results)

        # Filter by price
        if max_price and accommodations:
            accommodations = [a for a in accommodations if a.price_per_night <= max_price]

        # Filter by rating
        accommodations = [a for a in accommodations if a.rating >= min_rating]
        accommodations.sort(key=lambda x: x.rating, reverse=True)

        print(f"  ✓ Found {len(accommodations)} accommodations")
        return accommodations[:max_results]

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

    def _search_via_overpass(self, lat: float, lon: float, accommodation_types: List[str],
                            radius_km: float, max_results: int) -> List[AccommodationOption]:
        """CORRECTED: Search via Overpass with CORRECT query format"""
        try:
            # CORRECTED: Proper Overpass query with bounding box (south, west, north, east)
            lat1 = lat - (radius_km / 111.0)  # south
            lon1 = lon - (radius_km / 111.0)  # west
            lat2 = lat + (radius_km / 111.0)  # north
            lon2 = lon + (radius_km / 111.0)  # east

            # Build the CORRECT query for hotels and accommodations
            query = f"""[out:json][timeout:25];
(
  node["tourism"="hotel"]({lat1},{lon1},{lat2},{lon2});
  node["tourism"="apartment"]({lat1},{lon1},{lat2},{lon2});
  node["tourism"="guest_house"]({lat1},{lon1},{lat2},{lon2});
  node["tourism"="hostel"]({lat1},{lon1},{lat2},{lon2});
  way["tourism"="hotel"]({lat1},{lon1},{lat2},{lon2});
  way["tourism"="apartment"]({lat1},{lon1},{lat2},{lon2});
);
out body;
>;
out skel qt;
"""

            print(f"  🔍 Querying Overpass for hotels...")
            response = requests.post(self.overpass_url, data=query,
                                    headers=self.headers, timeout=60)

            if response.status_code != 200:
                print(f"  ❌ Overpass error {response.status_code}")
                return []

            data = response.json()
            accommodations = []

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
                name = tags.get('name', f'Hotel {i}')
                acc_type = tags.get('tourism', 'hotel')

                distance = self._calculate_distance(lat, lon, coords['lat'], coords['lon'])

                accommodation = AccommodationOption(
                    accommodation_id=f"ACC_{element.get('id', i)}",
                    name=name,
                    type=acc_type,
                    address=self._get_address(tags),
                    latitude=float(coords['lat']),
                    longitude=float(coords['lon']),
                    price_per_night=self._estimate_price(acc_type),
                    currency='INR',
                    rating=self._estimate_rating(tags),
                    review_count=random.randint(50, 1000),
                    amenities=self._parse_amenities(tags),
                    check_in_time="14:00",
                    check_out_time="11:00",
                    cancellation_policy="Free cancellation up to 24h",
                    free_cancellation=True,
                    distance_to_center_km=distance,
                    website=tags.get('website'),
                    phone=tags.get('phone'),
                    source="OpenStreetMap"
                )
                accommodations.append(accommodation)

            if accommodations:
                print(f"  ✓ Extracted {len(accommodations)} accommodations")

            return accommodations

        except Exception as e:
            print(f"  ❌ Overpass error: {e}")
            return []

    def _get_address(self, tags: dict) -> str:
        """Extract address"""
        parts = []
        for key in ['addr:street', 'addr:city', 'addr:postcode']:
            if key in tags:
                parts.append(str(tags[key]))
        return ', '.join(parts) if parts else 'Address available'

    def _estimate_price(self, acc_type: str) -> float:
        """Estimate price"""
        base = {'hotel': (3000, 12000), 'apartment': (2500, 10000),
                'hostel': (800, 3000), 'guest_house': (1500, 6000)}
        min_p, max_p = base.get(acc_type, (2000, 6000))
        return random.uniform(min_p, max_p)

    def _estimate_rating(self, tags: dict) -> float:
        """Estimate rating"""
        if 'rating' in tags:
            try:
                return float(tags['rating'])
            except:
                pass
        return random.uniform(3.5, 5.0)

    def _parse_amenities(self, tags: dict) -> List[str]:
        """Parse amenities"""
        amenities = []
        if tags.get('internet_access') in ['yes', 'wifi'] or tags.get('wifi') == 'yes':
            amenities.append('wifi')
        if tags.get('parking') == 'yes':
            amenities.append('parking')
        if tags.get('restaurant') == 'yes':
            amenities.append('restaurant')
        return amenities if amenities else ['wifi', 'parking']

    def _calculate_distance(self, lat1: float, lon1: float,
                           lat2: float, lon2: float) -> float:
        """Calculate distance in km"""
        lat_diff = abs(lat1 - lat2)
        lon_diff = abs(lon1 - lon2)
        distance = math.sqrt(lat_diff**2 + lon_diff**2) * 111
        return round(distance, 1)

    def rank_accommodations(self, accommodations: List[AccommodationOption]) -> List[AccommodationOption]:
        """Rank accommodations"""
        if not accommodations:
            return []

        max_price = max(a.price_per_night for a in accommodations)
        max_dist = max(a.distance_to_center_km for a in accommodations) or 1

        scored = []
        for acc in accommodations:
            price_score = 1 - (acc.price_per_night / max_price) if max_price > 0 else 0
            dist_score = 1 - (acc.distance_to_center_km / max_dist) if max_dist > 0 else 0
            rating_score = acc.rating / 5.0

            score = 0.3 * price_score + 0.3 * dist_score + 0.4 * rating_score
            scored.append((score, acc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored]