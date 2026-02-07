# """
# Flight Agent Module - CORRECTED for Amadeus TEST API
# Uses test.api.amadeus.com instead of api.amadeus.com
# """

# import os
# import requests
# from typing import List, Dict, Optional, Any
# from datetime import datetime, timedelta
# from dataclasses import dataclass
# from dotenv import load_dotenv
# import re

# load_dotenv()


# @dataclass
# class FlightOption:
#     """Flight option data structure"""
#     flight_id: str
#     origin: str
#     destination: str
#     departure_time: str
#     arrival_time: str
#     duration_minutes: int
#     price: float
#     currency: str
#     carrier: str
#     segments: int
#     class_type: str
#     reliability_score: float = 0.9
#     available_seats: int = 10


# class FlightAgent:
#     """Flight Agent - CORRECTED for Amadeus TEST API"""

#     def __init__(self, use_real_api: bool = True):
#         """Initialize with CORRECTED TEST API endpoints"""
#         self.client_id = os.getenv('AMADEUS_CLIENT_ID')
#         self.client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
#         self.use_real_api = use_real_api
#         self.access_token = None
#         self.token_expires = None

#         # FIXED: Use TEST API endpoint!
#         self.auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
#         self.base_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"

#         print(f"🛫 Flight Agent initialized (TEST API)")
#         print(f"  Client ID: {self.client_id[:15]}..." if self.client_id else "  No Client ID")

#         if self.use_real_api and self.client_id and self.client_secret:
#             self._authenticate()
#         else:
#             print("⚠️  Using mock data (credentials not configured)")
#             self.use_real_api = False

#     def _authenticate(self) -> bool:
#         """CORRECTED: Authenticate using TEST API"""
#         try:
#             print(f"\n  🔐 Authenticating with TEST API...")
#             print(f"  URL: {self.auth_url}")

#             # EXACT FORMAT from user's example
#             payload = {
#                 "grant_type": "client_credentials",
#                 "client_id": self.client_id.strip(),
#                 "client_secret": self.client_secret.strip()
#             }

#             response = requests.post(self.auth_url, data=payload, timeout=10)

#             print(f"  Status: {response.status_code}")

#             if response.status_code != 200:
#                 print(f"  ❌ Error {response.status_code}")
#                 if response.text:
#                     print(f"  Response: {response.text[:200]}")
#                 return False

#             data = response.json()

#             if 'access_token' not in data:
#                 print(f"  ❌ No access token in response")
#                 print(f"  Response: {data}")
#                 return False

#             self.access_token = data['access_token']
#             expires_in = data.get('expires_in', 1800)
#             self.token_expires = datetime.now() + timedelta(seconds=expires_in)

#             print(f"  ✅ Authentication successful!")
#             print(f"  Token: {self.access_token[:20]}...")
#             print(f"  Valid for: {expires_in} seconds")
#             return True

#         except Exception as e:
#             print(f"  ❌ Authentication Error: {e}")
#             return False

#     def search_flights(self, origin: str, destination: str, departure_date: str,
#                       adults: int = 1, travel_class: str = "ECONOMY",
#                       max_results: int = 5) -> List[FlightOption]:
#         """Search flights using TEST API"""

#         if not self.use_real_api or not self.access_token:
#             print(f"  ⚠️  Real API not available. Using mock data.")
#             return self._mock_flight_search(origin, destination, departure_date,
#                                           travel_class, max_results)

#         return self._real_flight_search(origin, destination, departure_date,
#                                        adults, travel_class, max_results)

#     def _real_flight_search(self, origin, destination, departure_date,
#                            adults, travel_class, max_results) -> List[FlightOption]:
#         """CORRECTED: Real flight search using TEST API endpoint"""
#         try:
#             # EXACT FORMAT from user's example
#             headers = {
#                 "Authorization": f"Bearer {self.access_token}"
#             }

#             params = {
#                 "originLocationCode": origin.upper(),
#                 "destinationLocationCode": destination.upper(),
#                 "departureDate": departure_date,
#                 "adults": adults
#             }

#             print(f"\n  🔍 Searching flights (TEST API)...")
#             print(f"  URL: {self.base_url}")
#             print(f"  From: {origin} → To: {destination}")
#             print(f"  Date: {departure_date}")

#             response = requests.get(self.base_url, headers=headers, params=params, timeout=15)

#             print(f"  Status: {response.status_code}")

#             if response.status_code == 401:
#                 print(f"  ❌ Token expired - re-authenticating...")
#                 self._authenticate()
#                 return []

#             if response.status_code != 200:
#                 print(f"  ⚠️  API Error {response.status_code}")
#                 try:
#                     print(f"  Response: {response.json()}")
#                 except:
#                     print(f"  Response: {response.text[:200]}")
#                 return []

#             data = response.json()
#             flights = []

#             if 'data' in data and data['data']:
#                 print(f"  Found {len(data['data'])} flights in response")

#                 for i, offer in enumerate(data['data'][:max_results]):
#                     try:
#                         itinerary = offer['itineraries'][0]
#                         segment = itinerary['segments'][0]

#                         price = float(offer['price']['total'])
#                         currency = offer['price'].get('currency', 'USD')

#                         flight = FlightOption(
#                             flight_id=f"FL{i+1}",
#                             origin=origin.upper(),
#                             destination=destination.upper(),
#                             departure_time=segment['departure']['at'],
#                             arrival_time=segment['arrival']['at'],
#                             duration_minutes=self._parse_duration(itinerary['duration']),
#                             price=price,
#                             currency=currency,
#                             carrier=segment.get('carrierCode', 'XX'),
#                             segments=len(itinerary['segments']),
#                             class_type=travel_class.lower()
#                         )
#                         flights.append(flight)

#                         print(f"    ✓ Flight {i+1}: {flight.carrier} {flight.currency} {flight.price}")

#                     except Exception as e:
#                         print(f"    ⚠️  Error parsing flight: {e}")
#                         continue

#                 print(f"  ✅ Successfully parsed {len(flights)} flights")
#             else:
#                 print(f"  ⚠️  No flights found in response")
#                 print(f"  Raw response: {data}")

#             return flights

#         except Exception as e:
#             print(f"  ❌ Flight search error: {type(e).__name__}: {e}")
#             import traceback
#             traceback.print_exc()
#             return []

#     def _mock_flight_search(self, origin, destination, departure_date,
#                            travel_class, max_results) -> List[FlightOption]:
#         """Generate mock flights for fallback"""
#         import random

#         print(f"  📊 Generating {max_results} mock flights...")
#         flights = []
#         base_prices = {'economy': 30000, 'business': 80000, 'first': 150000}
#         base_price = base_prices.get(travel_class.lower(), 40000)

#         carriers = ['AI', 'BA', 'LH', 'EK', 'SQ', 'ANA', 'JAL', 'UA', '6E', 'S2']

#         for i in range(max_results):
#             dep_hour = random.randint(6, 22)
#             duration = random.randint(180, 600)  # Flight duration in minutes

#             dep_dt = datetime.strptime(departure_date, '%Y-%m-%d')
#             dep_dt = dep_dt.replace(hour=dep_hour, minute=random.randint(0, 59))
#             arr_dt = dep_dt + timedelta(minutes=duration)

#             price = base_price * random.uniform(0.8, 1.3)

#             flight = FlightOption(
#                 flight_id=f"MOCK{i+1}",
#                 origin=origin.upper(),
#                 destination=destination.upper(),
#                 departure_time=dep_dt.isoformat(),
#                 arrival_time=arr_dt.isoformat(),
#                 duration_minutes=duration,
#                 price=round(price, 2),
#                 currency='INR',
#                 carrier=random.choice(carriers),
#                 segments=random.randint(1, 2),
#                 class_type=travel_class.lower()
#             )
#             flights.append(flight)
#             print(f"    Mock {i+1}: {flight.carrier} INR {flight.price}")

#         flights.sort(key=lambda x: x.price)
#         return flights

#     def _parse_duration(self, duration_str: str) -> int:
#         """Parse ISO 8601 duration to minutes"""
#         try:
#             hours = re.search(r'(\d+)H', duration_str)
#             minutes = re.search(r'(\d+)M', duration_str)

#             total = 0
#             if hours:
#                 total += int(hours.group(1)) * 60
#             if minutes:
#                 total += int(minutes.group(1))

#             return total if total > 0 else 300
#         except:
#             return 300

#     def filter_by_preferences(self, flights, avoid_night=False,
#                              max_segments=2, max_price=None):
#         """Filter flights by preferences"""
#         filtered = flights.copy()

#         if avoid_night:
#             filtered = [f for f in filtered if not self._is_night_flight(f.departure_time)]

#         if max_segments:
#             filtered = [f for f in filtered if f.segments <= max_segments]

#         if max_price:
#             filtered = [f for f in filtered if f.price <= max_price]

#         return filtered

#     def _is_night_flight(self, departure_time):
#         """Check if flight is at night"""
#         try:
#             hour = int(departure_time.split('T')[1].split(':')[0])
#             return hour >= 22 or hour < 6
#         except:
#             return False

#     def rank_flights(self, flights):
#         """Rank flights by value"""
#         if not flights:
#             return []

#         max_price = max(f.price for f in flights)
#         max_duration = max(f.duration_minutes for f in flights)

#         scored = []
#         for flight in flights:
#             price_score = 1 - (flight.price / max_price) if max_price > 0 else 0
#             duration_score = 1 - (flight.duration_minutes / max_duration) if max_duration > 0 else 0
#             score = 0.4 * price_score + 0.3 * duration_score + 0.3 * flight.reliability_score
#             scored.append((score, flight))

#         scored.sort(key=lambda x: x[0], reverse=True)
#         return [f for _, f in scored]


# if __name__ == "__main__":
#     # Test with actual Amadeus TEST API
#     agent = FlightAgent(use_real_api=True)

#     print("\n" + "="*70)
#     print("TESTING AMADEUS TEST API")
#     print("="*70)

#     flights = agent.search_flights(
#         origin="BOM",
#         destination="DEL",
#         departure_date="2025-11-10",
#         adults=1,
#         max_results=3
#     )

#     if flights:
#         print(f"\n✅ SUCCESS! Found {len(flights)} flights:")
#         for i, f in enumerate(flights, 1):
#             print(f"  {i}. {f.carrier} - {f.currency} {f.price:.2f}")
#             print(f"     {f.departure_time} → {f.arrival_time}")
#             print(f"     Duration: {f.duration_minutes} minutes")
#     else:
#         print(f"\n❌ No flights found")

"""
Flight Agent Module - CORRECTED for Amadeus TEST API
Uses test.api.amadeus.com instead of api.amadeus.com
"""

import os
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from dotenv import load_dotenv
import re

load_dotenv()


@dataclass
class FlightOption:
    """Flight option data structure"""
    flight_id: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    price: float
    currency: str
    carrier: str
    segments: int
    class_type: str
    reliability_score: float = 0.9
    available_seats: int = 10


class FlightAgent:
    """Flight Agent - CORRECTED for Amadeus TEST API"""

    def __init__(self, use_real_api: bool = True):
        """Initialize with CORRECTED TEST API endpoints"""
        self.client_id = os.getenv('AMADEUS_CLIENT_ID')
        self.client_secret = os.getenv('AMADEUS_CLIENT_SECRET')
        self.use_real_api = use_real_api
        self.access_token = None
        self.token_expires = None

        # FIXED: Use TEST API endpoint!
        self.auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        self.base_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"

        print(f"🛫 Flight Agent initialized (TEST API)")
        print(f"  Client ID: {self.client_id[:15]}..." if self.client_id else "  No Client ID")

        if self.use_real_api and self.client_id and self.client_secret:
            self._authenticate()
        else:
            print("⚠️  Using mock data (credentials not configured)")
            self.use_real_api = False

    def _authenticate(self) -> bool:
        """CORRECTED: Authenticate using TEST API"""
        try:
            print(f"\n  🔐 Authenticating with TEST API...")
            print(f"  URL: {self.auth_url}")

            # EXACT FORMAT from user's example
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.client_id.strip(),
                "client_secret": self.client_secret.strip()
            }

            response = requests.post(self.auth_url, data=payload, timeout=10)

            print(f"  Status: {response.status_code}")

            if response.status_code != 200:
                print(f"  ❌ Error {response.status_code}")
                if response.text:
                    print(f"  Response: {response.text[:200]}")
                return False

            data = response.json()

            if 'access_token' not in data:
                print(f"  ❌ No access token in response")
                print(f"  Response: {data}")
                return False

            self.access_token = data['access_token']
            expires_in = data.get('expires_in', 1800)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in)

            print(f"  ✅ Authentication successful!")
            print(f"  Token: {self.access_token[:20]}...")
            print(f"  Valid for: {expires_in} seconds")
            return True

        except Exception as e:
            print(f"  ❌ Authentication Error: {e}")
            return False

    def search_flights(self, origin: str, destination: str, departure_date: str,
                      adults: int = 1, travel_class: str = "ECONOMY",
                      max_results: int = 5) -> List[FlightOption]:
        """Search flights using TEST API"""

        if not self.use_real_api or not self.access_token:
            print(f"  ⚠️  Real API not available. Using mock data.")
            return self._mock_flight_search(origin, destination, departure_date,
                                          travel_class, max_results)

        return self._real_flight_search(origin, destination, departure_date,
                                       adults, travel_class, max_results)

    def _real_flight_search(self, origin, destination, departure_date,
                           adults, travel_class, max_results) -> List[FlightOption]:
        """CORRECTED: Real flight search using TEST API endpoint"""
        try:
            # EXACT FORMAT from user's example
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }

            params = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": departure_date,
                "adults": adults
            }

            print(f"\n  🔍 Searching flights (TEST API)...")
            print(f"  URL: {self.base_url}")
            print(f"  From: {origin} → To: {destination}")
            print(f"  Date: {departure_date}")

            response = requests.get(self.base_url, headers=headers, params=params, timeout=15)

            print(f"  Status: {response.status_code}")

            if response.status_code == 401:
                print(f"  ❌ Token expired - re-authenticating...")
                self._authenticate()
                return []

            if response.status_code != 200:
                print(f"  ⚠️  API Error {response.status_code}")
                try:
                    print(f"  Response: {response.json()}")
                except:
                    print(f"  Response: {response.text[:200]}")
                return []

            data = response.json()
            flights = []

            if 'data' in data and data['data']:
                print(f"  Found {len(data['data'])} flights in response")

                for i, offer in enumerate(data['data'][:max_results]):
                    try:
                        itinerary = offer['itineraries'][0]
                        segment = itinerary['segments'][0]

                        price = float(offer['price']['total'])
                        currency = offer['price'].get('currency', 'USD')

                        flight = FlightOption(
                            flight_id=f"FL{i+1}",
                            origin=origin.upper(),
                            destination=destination.upper(),
                            departure_time=segment['departure']['at'],
                            arrival_time=segment['arrival']['at'],
                            duration_minutes=self._parse_duration(itinerary['duration']),
                            price=price,
                            currency=currency,
                            carrier=segment.get('carrierCode', 'XX'),
                            segments=len(itinerary['segments']),
                            class_type=travel_class.lower()
                        )
                        flights.append(flight)

                        print(f"    ✓ Flight {i+1}: {flight.carrier} {flight.currency} {flight.price}")

                    except Exception as e:
                        print(f"    ⚠️  Error parsing flight: {e}")
                        continue

                print(f"  ✅ Successfully parsed {len(flights)} flights")
            else:
                print(f"  ⚠️  No flights found in response")
                print(f"  Raw response: {data}")

            return flights

        except Exception as e:
            print(f"  ❌ Flight search error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _mock_flight_search(self, origin, destination, departure_date,
                           travel_class, max_results) -> List[FlightOption]:
        """Generate mock flights for fallback"""
        import random

        print(f"  📊 Generating {max_results} mock flights...")
        flights = []
        base_prices = {'economy': 30000, 'business': 80000, 'first': 150000}
        base_price = base_prices.get(travel_class.lower(), 40000)

        carriers = ['AI', 'BA', 'LH', 'EK', 'SQ', 'ANA', 'JAL', 'UA', '6E', 'S2']

        for i in range(max_results):
            dep_hour = random.randint(6, 22)
            duration = random.randint(180, 600)  # Flight duration in minutes

            dep_dt = datetime.strptime(departure_date, '%Y-%m-%d')
            dep_dt = dep_dt.replace(hour=dep_hour, minute=random.randint(0, 59))
            arr_dt = dep_dt + timedelta(minutes=duration)

            price = base_price * random.uniform(0.8, 1.3)

            flight = FlightOption(
                flight_id=f"MOCK{i+1}",
                origin=origin.upper(),
                destination=destination.upper(),
                departure_time=dep_dt.isoformat(),
                arrival_time=arr_dt.isoformat(),
                duration_minutes=duration,
                price=round(price, 2),
                currency='INR',
                carrier=random.choice(carriers),
                segments=random.randint(1, 2),
                class_type=travel_class.lower()
            )
            flights.append(flight)
            print(f"    Mock {i+1}: {flight.carrier} INR {flight.price}")

        flights.sort(key=lambda x: x.price)
        return flights

    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to minutes"""
        try:
            hours = re.search(r'(\d+)H', duration_str)
            minutes = re.search(r'(\d+)M', duration_str)

            total = 0
            if hours:
                total += int(hours.group(1)) * 60
            if minutes:
                total += int(minutes.group(1))

            return total if total > 0 else 300
        except:
            return 300

    def filter_by_preferences(self, flights, avoid_night=False,
                             max_segments=2, max_price=None):
        """Filter flights by preferences"""
        filtered = flights.copy()

        if avoid_night:
            filtered = [f for f in filtered if not self._is_night_flight(f.departure_time)]

        if max_segments:
            filtered = [f for f in filtered if f.segments <= max_segments]

        if max_price:
            filtered = [f for f in filtered if f.price <= max_price]

        return filtered

    def _is_night_flight(self, departure_time):
        """Check if flight is at night"""
        try:
            hour = int(departure_time.split('T')[1].split(':')[0])
            return hour >= 22 or hour < 6
        except:
            return False

    def rank_flights(self, flights):
        """Rank flights by value"""
        if not flights:
            return []

        max_price = max(f.price for f in flights)
        max_duration = max(f.duration_minutes for f in flights)

        scored = []
        for flight in flights:
            price_score = 1 - (flight.price / max_price) if max_price > 0 else 0
            duration_score = 1 - (flight.duration_minutes / max_duration) if max_duration > 0 else 0
            score = 0.4 * price_score + 0.3 * duration_score + 0.3 * flight.reliability_score
            scored.append((score, flight))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored]


if __name__ == "__main__":
    # Test with actual Amadeus TEST API
    agent = FlightAgent(use_real_api=True)

    print("\n" + "="*70)
    print("TESTING AMADEUS TEST API")
    print("="*70)

    flights = agent.search_flights(
        origin="BOM",
        destination="DEL",
        departure_date="2025-11-10",
        adults=1,
        max_results=3
    )

    if flights:
        print(f"\n✅ SUCCESS! Found {len(flights)} flights:")
        for i, f in enumerate(flights, 1):
            print(f"  {i}. {f.carrier} - {f.currency} {f.price:.2f}")
            print(f"     {f.departure_time} → {f.arrival_time}")
            print(f"     Duration: {f.duration_minutes} minutes")
    else:
        print(f"\n❌ No flights found")