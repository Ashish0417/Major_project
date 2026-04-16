"""
Accommodation Agent - CORRECTED Overpass Query Format
Uses CORRECT Overpass query syntax with bounding boxes
"""

import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import random
import math
import time  # For rate limiting


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
        
        # Multiple Overpass servers (fallback list)
        self.overpass_urls = [
            "https://overpass-api.de/api/interpreter",  # Primary
            "https://overpass.kumi.systems/api/interpreter",  # Backup 1
            "https://overpass.openstreetmap.ru/api/interpreter",  # Backup 2
        ]
        
        self.headers = {'User-Agent': 'TravelPlannerApp/1.0 (student project)'}
        self.current_overpass_index = 0

        # Rate limiting to avoid being blocked
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests

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
        """Search via Overpass with multiple server fallback and rate limiting"""
        
        # Try each Overpass server in sequence
        for server_index, overpass_url in enumerate(self.overpass_urls, 1):
            try:
                print(f"  🔍 Querying Overpass server {server_index}/{len(self.overpass_urls)}...")
                
                # Rate limiting: wait if needed
                self._apply_rate_limit()
                
                # CORRECTED: Proper Overpass query with bounding box (south, west, north, east)
                lat1 = lat - (radius_km / 111.0)  # south
                lon1 = lon - (radius_km / 111.0)  # west
                lat2 = lat + (radius_km / 111.0)  # north
                lon2 = lon + (radius_km / 111.0)  # east

                # Optimized query - reduced timeout, limited types
                query = f"""[out:json][timeout:15];
(
  node["tourism"="hotel"]({lat1},{lon1},{lat2},{lon2});
  way["tourism"="hotel"]({lat1},{lon1},{lat2},{lon2});
  node["tourism"="guest_house"]({lat1},{lon1},{lat2},{lon2});
  way["tourism"="guest_house"]({lat1},{lon1},{lat2},{lon2});
  node["tourism"="hostel"]({lat1},{lon1},{lat2},{lon2});
);
out center {max_results};
"""

                # Make request with timeout
                response = requests.post(
                    overpass_url, 
                    data=query,
                    headers=self.headers, 
                    timeout=20  # 20 second timeout
                )

                # Check response status
                if response.status_code == 200:
                    # Success! Parse and return results
                    data = response.json()
                    accommodations = self._parse_overpass_results(
                        data, lat, lon, max_results
                    )
                    
                    if accommodations:
                        print(f"  ✅ Server {server_index} succeeded!")
                        print(f"  ✓ Extracted {len(accommodations)} accommodations")
                        return accommodations
                    else:
                        print(f"  ⚠️  Server {server_index} returned 0 results, trying next...")
                        continue
                
                elif response.status_code == 429:
                    # Rate limited
                    print(f"  ⚠️  Server {server_index} rate limited (429), trying next...")
                    continue
                
                elif response.status_code == 504:
                    # Gateway timeout
                    print(f"  ⚠️  Server {server_index} timeout (504), trying next...")
                    continue
                
                else:
                    print(f"  ⚠️  Server {server_index} error {response.status_code}, trying next...")
                    continue

            except requests.exceptions.Timeout:
                print(f"  ⚠️  Server {server_index} timeout, trying next...")
                continue
            
            except requests.exceptions.ConnectionError:
                print(f"  ⚠️  Server {server_index} connection error, trying next...")
                continue
            
            except Exception as e:
                print(f"  ⚠️  Server {server_index} error: {str(e)[:50]}, trying next...")
                continue
        
        # All servers failed
        print(f"  ❌ All {len(self.overpass_urls)} Overpass servers failed")
        print(f"  🔄 Generating mock accommodations as fallback...")
        return self._generate_mock_accommodations(lat, lon, max_results)
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _parse_overpass_results(self, data: dict, center_lat: float, 
                                center_lon: float, max_results: int) -> List[AccommodationOption]:
        """Parse Overpass API response into AccommodationOption objects"""
        accommodations = []
        elements = data.get('elements', [])
        
        print(f"  Found {len(elements)} raw elements")

        for i, element in enumerate(elements[:max_results]):
            if 'tags' not in element or 'name' not in element['tags']:
                continue

            # Get coordinates
            if 'lat' in element and 'lon' in element:
                coords = {'lat': element['lat'], 'lon': element['lon']}
            elif 'center' in element:  # For ways
                coords = {'lat': element['center']['lat'], 'lon': element['center']['lon']}
            else:
                continue

            tags = element['tags']
            name = tags.get('name', f'Hotel {i}')
            acc_type = tags.get('tourism', 'hotel')

            distance = self._calculate_distance(
                center_lat, center_lon, 
                coords['lat'], coords['lon']
            )

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

        return accommodations
    
    def _generate_mock_accommodations(self, lat: float, lon: float, max_results: int) -> List[AccommodationOption]:
        """Generate mock accommodations when API fails"""
        import random
        
        hotel_names = [
            "Grand Palace Hotel", "City View Inn", "Budget Stay", 
            "Luxury Gardens Hotel", "Downtown Hostel", "Traveler's Rest",
            "Modern Suites", "Comfort Inn", "Heritage Hotel",
            "Riverside Resort", "Airport Hotel", "Business Hub"
        ]
        
        accommodation_types = ['hotel', 'guest_house', 'hostel']
        
        accommodations = []
        for i in range(min(max_results, len(hotel_names))):
            acc_type = random.choice(accommodation_types)
            
            # Price based on type
            if acc_type == 'hostel':
                base_price = random.randint(500, 1500)
            elif acc_type == 'guest_house':
                base_price = random.randint(1500, 3500)
            else:  # hotel
                base_price = random.randint(2500, 8000)
            
            accommodation = AccommodationOption(
                accommodation_id=f"MOCK_ACC_{i}",
                name=hotel_names[i],
                type=acc_type,
                address=f"Mock Address {i+1}",
                latitude=lat + random.uniform(-0.05, 0.05),
                longitude=lon + random.uniform(-0.05, 0.05),
                price_per_night=float(base_price),
                currency='INR',
                rating=random.uniform(3.5, 4.8),
                review_count=random.randint(50, 500),
                amenities=['WiFi', 'Breakfast', 'AC'],
                check_in_time="14:00",
                check_out_time="11:00",
                cancellation_policy="Free cancellation up to 24h",
                free_cancellation=True,
                distance_to_center_km=random.uniform(0.5, 5.0),
                website=None,
                phone=None,
                source="Mock Data"
            )
            accommodations.append(accommodation)
        
        print(f"  ✓ Generated {len(accommodations)} mock accommodations")
        return accommodations

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