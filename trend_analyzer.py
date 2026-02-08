"""
Trend Analyzer Module
Provides trend-based tour suggestions using REAL APIs
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()


class TrendAnalyzer:
    """
    Analyzes trends and provides seasonal/popular recommendations using real APIs
    
    APIs Used:
    1. Ticketmaster API - for events and popular attractions
    2. OpenWeatherMap API - for weather-based suggestions
    3. SerpAPI (Google Trends) - for trending destinations
    4. Predicthq API - for events and trends (optional)
    """

    def __init__(self, use_realtime_data: bool = True):
        """Initialize trend analyzer with API credentials"""
        self.use_realtime_data = use_realtime_data
        
        # API Keys from environment
        self.ticketmaster_key = os.getenv('TICKETMASTER_API_KEY', '')
        self.openweather_key = os.getenv('OPENWEATHER_API_KEY', '')
        self.serpapi_key = os.getenv('SERPAPI_API_KEY', '')
        self.predicthq_token = os.getenv('PREDICTHQ_ACCESS_TOKEN', '')
        
        # API Endpoints
        self.ticketmaster_url = "https://app.ticketmaster.com/discovery/v2/events.json"
        self.openweather_url = "https://api.openweathermap.org/data/2.5/forecast"
        self.serpapi_url = "https://serpapi.com/search.json"
        self.predicthq_url = "https://api.predicthq.com/v1/events/"
        
        # Fallback seasonal data (used if APIs fail)
        self.seasonal_attractions_fallback = {
            'Japan': {
                'spring': ['Cherry Blossom Viewing', 'Hanami Festivals', 'Spring Gardens'],
                'summer': ['Summer Festivals', 'Beach Activities', 'Fireworks'],
                'autumn': ['Fall Foliage Tours', 'Autumn Festivals', 'Harvest Tours'],
                'winter': ['Snow Festivals', 'Hot Springs', 'Winter Illuminations']
            },
            'Germany': {
                'winter': ['Christmas Markets', 'Winter Sports', 'Holiday Lights'],
                'spring': ['Spring Festivals', 'Garden Tours'],
                'summer': ['Beer Gardens', 'Outdoor Concerts'],
                'autumn': ['Oktoberfest', 'Wine Festivals']
            }
        }
        
        # Check API availability
        self._check_api_status()

    def _check_api_status(self):
        """Check which APIs are available"""
        self.apis_available = {
            'ticketmaster': bool(self.ticketmaster_key),
            'openweather': bool(self.openweather_key),
            'serpapi': bool(self.serpapi_key),
            'predicthq': bool(self.predicthq_token)
        }
        
        if self.use_realtime_data:
            print("\n🔌 API Status Check:")
            for api, available in self.apis_available.items():
                status = "✅ Connected" if available else "❌ Not configured"
                print(f"  {api.title()}: {status}")
            
            if not any(self.apis_available.values()):
                print("\n⚠️  Warning: No API keys found. Using fallback mock data.")
                print("   Add API keys to .env file for real-time data.")

    def get_seasonal_suggestions(self, destination: str, travel_date: str) -> List[Dict[str, Any]]:
        """
        Get seasonal attraction suggestions using real event data
        
        Args:
            destination: Destination city/country
            travel_date: Travel date (YYYY-MM-DD)
            
        Returns:
            List of seasonal suggestions
        """
        try:
            date_obj = datetime.strptime(travel_date, '%Y-%m-%d')
            season = self._get_season(date_obj.month)
            suggestions = []
            
            # Try Ticketmaster API first
            if self.apis_available['ticketmaster']:
                ticketmaster_suggestions = self._get_ticketmaster_attractions(destination, travel_date)
                suggestions.extend(ticketmaster_suggestions)
            
            # Try PredictHQ API
            if self.apis_available['predicthq']:
                predicthq_suggestions = self._get_predicthq_events(destination, travel_date, 'seasonal')
                suggestions.extend(predicthq_suggestions)
            
            # Fallback to static data if no API results
            if not suggestions:
                country = self._find_country(destination)
                if country in self.seasonal_attractions_fallback:
                    attractions = self.seasonal_attractions_fallback[country].get(season, [])
                    for attraction in attractions:
                        suggestions.append({
                            'name': attraction,
                            'type': 'seasonal',
                            'season': season,
                            'relevance_score': 0.7,
                            'source': 'fallback'
                        })
            
            return suggestions[:10]  # Limit to top 10
            
        except Exception as e:
            print(f"⚠️  Error getting seasonal suggestions: {e}")
            return []

    def _get_ticketmaster_attractions(self, destination: str, date: str) -> List[Dict[str, Any]]:
        """Fetch attractions from Ticketmaster API"""
        if not self.ticketmaster_key:
            return []
        
        try:
            # Parse date for range
            start_date = datetime.strptime(date, '%Y-%m-%d')
            end_date = start_date + timedelta(days=30)
            
            params = {
                'apikey': self.ticketmaster_key,
                'city': destination.split(',')[0],  # Extract city name
                'startDateTime': start_date.strftime('%Y-%m-%dT00:00:00Z'),
                'endDateTime': end_date.strftime('%Y-%m-%dT23:59:59Z'),
                'size': 20,
                'sort': 'relevance,desc'
            }
            
            response = requests.get(self.ticketmaster_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                suggestions = []
                
                if '_embedded' in data and 'events' in data['_embedded']:
                    for event in data['_embedded']['events'][:10]:
                        suggestions.append({
                            'name': event.get('name', 'Unknown Event'),
                            'type': 'event',
                            'season': self._get_season(start_date.month),
                            'relevance_score': 0.9,
                            'source': 'ticketmaster',
                            'date': event.get('dates', {}).get('start', {}).get('localDate', ''),
                            'url': event.get('url', ''),
                            'category': event.get('classifications', [{}])[0].get('segment', {}).get('name', 'Entertainment')
                        })
                
                return suggestions
            else:
                print(f"⚠️  Ticketmaster API returned status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️  Ticketmaster API error: {e}")
            return []

    def _get_predicthq_events(self, destination: str, date: str, category: str = 'seasonal') -> List[Dict[str, Any]]:
        """Fetch events from PredictHQ API"""
        if not self.predicthq_token:
            return []
        
        try:
            start_date = datetime.strptime(date, '%Y-%m-%d')
            end_date = start_date + timedelta(days=30)
            
            headers = {
                'Authorization': f'Bearer {self.predicthq_token}',
                'Accept': 'application/json'
            }
            
            params = {
                'q': destination,
                'start.gte': start_date.strftime('%Y-%m-%d'),
                'start.lte': end_date.strftime('%Y-%m-%d'),
                'limit': 20,
                'sort': 'rank'
            }
            
            response = requests.get(self.predicthq_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                suggestions = []
                
                for event in data.get('results', [])[:10]:
                    suggestions.append({
                        'name': event.get('title', 'Unknown Event'),
                        'type': category,
                        'season': self._get_season(start_date.month),
                        'relevance_score': min(event.get('rank', 50) / 100, 1.0),
                        'source': 'predicthq',
                        'date': event.get('start', ''),
                        'category': event.get('category', 'Unknown')
                    })
                
                return suggestions
            else:
                print(f"⚠️  PredictHQ API returned status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️  PredictHQ API error: {e}")
            return []

    def get_popular_events(self, destination: str, travel_date: str) -> List[Dict[str, Any]]:
        """
        Get popular events happening during travel dates using real APIs
        
        Args:
            destination: Destination city
            travel_date: Travel start date (YYYY-MM-DD)
            
        Returns:
            List of popular events
        """
        try:
            events = []
            
            # Try Ticketmaster
            if self.apis_available['ticketmaster']:
                tm_events = self._get_ticketmaster_events(destination, travel_date)
                events.extend(tm_events)
            
            # Try PredictHQ
            if self.apis_available['predicthq']:
                phq_events = self._get_predicthq_events(destination, travel_date, 'popular')
                events.extend(phq_events)
            
            # Remove duplicates by name
            seen_names = set()
            unique_events = []
            for event in events:
                if event['name'] not in seen_names:
                    seen_names.add(event['name'])
                    unique_events.append(event)
            
            # Sort by relevance/popularity
            unique_events.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return unique_events[:10]
            
        except Exception as e:
            print(f"⚠️  Error getting popular events: {e}")
            return []

    def _get_ticketmaster_events(self, destination: str, date: str) -> List[Dict[str, Any]]:
        """Get events from Ticketmaster (same as attractions but formatted for events)"""
        attractions = self._get_ticketmaster_attractions(destination, date)
        
        # Convert to event format
        events = []
        for attr in attractions:
            events.append({
                'name': attr['name'],
                'type': 'event',
                'month': datetime.strptime(attr.get('date', date), '%Y-%m-%d').month if attr.get('date') else None,
                'popularity': attr['relevance_score'],
                'source': 'ticketmaster',
                'url': attr.get('url', ''),
                'category': attr.get('category', 'Entertainment')
            })
        
        return events

    def get_weather_based_suggestions(self, destination: str, travel_date: str) -> List[str]:
        """
        Get activity suggestions based on real weather forecast
        
        Args:
            destination: Destination city
            travel_date: Travel date (YYYY-MM-DD)
            
        Returns:
            List of weather-appropriate suggestions
        """
        try:
            if self.apis_available['openweather']:
                return self._get_openweather_suggestions(destination, travel_date)
            else:
                # Fallback to seasonal logic
                date_obj = datetime.strptime(travel_date, '%Y-%m-%d')
                return self._get_seasonal_weather_suggestions(date_obj.month)
                
        except Exception as e:
            print(f"⚠️  Error getting weather suggestions: {e}")
            date_obj = datetime.strptime(travel_date, '%Y-%m-%d')
            return self._get_seasonal_weather_suggestions(date_obj.month)

    def _get_openweather_suggestions(self, destination: str, date: str) -> List[str]:
        """Get weather-based suggestions from OpenWeatherMap API"""
        if not self.openweather_key:
            return []
        
        try:
            # First get coordinates for the city
            geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct"
            geo_params = {
                'q': destination.split(',')[0],
                'limit': 1,
                'appid': self.openweather_key
            }
            
            geo_response = requests.get(geocoding_url, params=geo_params, timeout=10)
            
            if geo_response.status_code == 200:
                geo_data = geo_response.json()
                if not geo_data:
                    return self._get_seasonal_weather_suggestions(datetime.strptime(date, '%Y-%m-%d').month)
                
                lat = geo_data[0]['lat']
                lon = geo_data[0]['lon']
                
                # Get weather forecast
                weather_params = {
                    'lat': lat,
                    'lon': lon,
                    'appid': self.openweather_key,
                    'units': 'metric'
                }
                
                weather_response = requests.get(self.openweather_url, params=weather_params, timeout=10)
                
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()
                    
                    # Analyze forecast
                    avg_temp = sum(item['main']['temp'] for item in weather_data['list'][:8]) / 8
                    rain_prob = sum(item.get('pop', 0) for item in weather_data['list'][:8]) / 8
                    
                    suggestions = []
                    
                    # Temperature-based suggestions
                    if avg_temp > 25:
                        suggestions.extend(['Outdoor Activities', 'Beach Trips', 'Water Sports', 'Outdoor Dining'])
                    elif avg_temp > 15:
                        suggestions.extend(['Garden Tours', 'Outdoor Festivals', 'Hiking', 'Cycling'])
                    elif avg_temp > 5:
                        suggestions.extend(['City Walking Tours', 'Outdoor Markets', 'Scenic Tours'])
                    else:
                        suggestions.extend(['Indoor Museums', 'Hot Springs', 'Winter Sports', 'Indoor Markets'])
                    
                    # Rain-based suggestions
                    if rain_prob > 0.5:
                        suggestions.extend(['Indoor Attractions', 'Shopping Malls', 'Art Galleries', 'Cooking Classes'])
                    
                    return list(set(suggestions))[:6]
            
            # Fallback
            return self._get_seasonal_weather_suggestions(datetime.strptime(date, '%Y-%m-%d').month)
                
        except Exception as e:
            print(f"⚠️  OpenWeather API error: {e}")
            return self._get_seasonal_weather_suggestions(datetime.strptime(date, '%Y-%m-%d').month)

    def _get_seasonal_weather_suggestions(self, month: int) -> List[str]:
        """Fallback weather suggestions based on season"""
        if month in [6, 7, 8]:  # Summer
            return ['Outdoor Activities', 'Beach Trips', 'Hiking', 'Outdoor Dining']
        elif month in [12, 1, 2]:  # Winter
            return ['Indoor Museums', 'Hot Springs', 'Winter Sports', 'Indoor Markets']
        elif month in [3, 4, 5]:  # Spring
            return ['Garden Tours', 'Outdoor Festivals', 'Picnics', 'Cycling']
        else:  # Fall
            return ['Scenic Tours', 'Hiking', 'Cultural Sites', 'Food Tours']

    def get_trending_destinations(self, region: str = 'Asia', top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Get currently trending destinations using SerpAPI (Google Trends)
        
        Args:
            region: Geographic region
            top_n: Number of results
            
        Returns:
            List of trending destinations
        """
        try:
            if self.apis_available['serpapi']:
                return self._get_serpapi_trends(region, top_n)
            else:
                # Fallback to static trending data
                return self._get_fallback_trending(region, top_n)
                
        except Exception as e:
            print(f"⚠️  Error getting trending destinations: {e}")
            return self._get_fallback_trending(region, top_n)

    def _get_serpapi_trends(self, region: str, top_n: int) -> List[Dict[str, Any]]:
        """Get trending destinations from SerpAPI (Google Trends)"""
        if not self.serpapi_key:
            return []
        
        try:
            params = {
                'engine': 'google_trends',
                'q': f'travel destinations {region}',
                'data_type': 'RELATED_QUERIES',
                'api_key': self.serpapi_key
            }
            
            response = requests.get(self.serpapi_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                trending = []
                
                # Parse trending queries
                if 'related_queries' in data:
                    queries = data['related_queries'].get('rising', [])[:top_n]
                    
                    for i, query in enumerate(queries):
                        trending.append({
                            'name': query.get('query', 'Unknown'),
                            'trend_score': 1.0 - (i * 0.1),  # Decreasing score
                            'reason': 'Trending on Google',
                            'source': 'serpapi'
                        })
                
                return trending
            else:
                print(f"⚠️  SerpAPI returned status {response.status_code}")
                return self._get_fallback_trending(region, top_n)
                
        except Exception as e:
            print(f"⚠️  SerpAPI error: {e}")
            return self._get_fallback_trending(region, top_n)

    def _get_fallback_trending(self, region: str, top_n: int) -> List[Dict[str, Any]]:
        """Fallback trending destinations"""
        trending_data = {
            'Asia': [
                {'name': 'Tokyo, Japan', 'trend_score': 0.95, 'reason': 'Cultural hotspot', 'source': 'fallback'},
                {'name': 'Seoul, South Korea', 'trend_score': 0.92, 'reason': 'K-culture boom', 'source': 'fallback'},
                {'name': 'Bangkok, Thailand', 'trend_score': 0.88, 'reason': 'Food paradise', 'source': 'fallback'},
                {'name': 'Singapore', 'trend_score': 0.85, 'reason': 'Modern city', 'source': 'fallback'},
                {'name': 'Bali, Indonesia', 'trend_score': 0.83, 'reason': 'Beach paradise', 'source': 'fallback'},
            ],
            'Europe': [
                {'name': 'Paris, France', 'trend_score': 0.94, 'reason': 'Art and culture', 'source': 'fallback'},
                {'name': 'Barcelona, Spain', 'trend_score': 0.91, 'reason': 'Architecture', 'source': 'fallback'},
                {'name': 'Amsterdam, Netherlands', 'trend_score': 0.88, 'reason': 'Canals and museums', 'source': 'fallback'},
            ]
        }
        
        return trending_data.get(region, [])[:top_n]

    def analyze_user_trends(self, user_interests: List[str]) -> Dict[str, Any]:
        """
        Analyze user interests against current trends
        
        Args:
            user_interests: List of user interest keywords
            
        Returns:
            Trend analysis results
        """
        trend_keywords = {
            'museums': ['cultural tourism', 'art exhibitions', 'history tours'],
            'culinary': ['food tourism', 'cooking classes', 'street food'],
            'hiking': ['adventure travel', 'eco-tourism', 'nature trails'],
            'history': ['heritage sites', 'historical tours', 'archaeology'],
            'art': ['art galleries', 'creative workshops', 'street art'],
            'beach': ['coastal tourism', 'water sports', 'island hopping'],
            'shopping': ['retail therapy', 'local markets', 'fashion districts']
        }
        
        matching_trends = []
        for interest in user_interests:
            if interest.lower() in trend_keywords:
                matching_trends.extend(trend_keywords[interest.lower()])
        
        return {
            'user_interests': user_interests,
            'matching_trends': list(set(matching_trends)),
            'trend_alignment_score': len(matching_trends) / len(user_interests) if user_interests else 0,
            'api_status': self.apis_available
        }

    def _get_season(self, month: int) -> str:
        """Determine season from month (Northern Hemisphere)"""
        if month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'autumn'
        else:
            return 'winter'

    def _find_country(self, destination: str) -> Optional[str]:
        """Find country from destination string"""
        destination_lower = destination.lower()
        
        country_keywords = {
            'Japan': ['japan', 'tokyo', 'kyoto', 'osaka', 'hiroshima'],
            'Germany': ['germany', 'berlin', 'munich', 'frankfurt'],
            'France': ['france', 'paris', 'lyon', 'marseille'],
            'Italy': ['italy', 'rome', 'venice', 'milan', 'florence'],
            'Spain': ['spain', 'madrid', 'barcelona', 'seville'],
            'Thailand': ['thailand', 'bangkok', 'phuket', 'chiang mai'],
        }
        
        for country, keywords in country_keywords.items():
            if any(keyword in destination_lower for keyword in keywords):
                return country
        
        return None


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_trend_analyzer():
    """Test the TrendAnalyzer with real APIs"""
    print("="*70)
    print("🧪 TREND ANALYZER API INTEGRATION TEST")
    print("="*70)
    
    analyzer = TrendAnalyzer(use_realtime_data=True)
    
    # Test 1: Seasonal Suggestions
    print("\n" + "="*70)
    print("TEST 1: Seasonal Suggestions")
    print("="*70)
    suggestions = analyzer.get_seasonal_suggestions('Tokyo, Japan', '2026-03-20')
    print(f"\nFound {len(suggestions)} seasonal suggestions:")
    for sugg in suggestions[:5]:
        print(f"  • {sugg['name']}")
        print(f"    Season: {sugg.get('season', 'N/A')} | Source: {sugg.get('source', 'N/A')}")
        if 'date' in sugg and sugg['date']:
            print(f"    Date: {sugg['date']}")
    
    # Test 2: Popular Events
    print("\n" + "="*70)
    print("TEST 2: Popular Events")
    print("="*70)
    events = analyzer.get_popular_events('Tokyo', '2026-04-15')
    print(f"\nFound {len(events)} popular events:")
    for event in events[:5]:
        print(f"  • {event['name']}")
        print(f"    Popularity: {event.get('popularity', 0):.2f} | Source: {event.get('source', 'N/A')}")
    
    # Test 3: Weather Suggestions
    print("\n" + "="*70)
    print("TEST 3: Weather-based Suggestions")
    print("="*70)
    weather_sugg = analyzer.get_weather_based_suggestions('Tokyo', '2026-03-20')
    print(f"\nWeather-appropriate activities:")
    for sugg in weather_sugg:
        print(f"  • {sugg}")
    
    # Test 4: Trending Destinations
    print("\n" + "="*70)
    print("TEST 4: Trending Destinations")
    print("="*70)
    trending = analyzer.get_trending_destinations('Asia', top_n=5)
    print(f"\nTop trending destinations in Asia:")
    for dest in trending:
        print(f"  • {dest['name']}")
        print(f"    Score: {dest['trend_score']:.2f} | Reason: {dest['reason']} | Source: {dest.get('source', 'N/A')}")
    
    # Test 5: User Trend Analysis
    print("\n" + "="*70)
    print("TEST 5: User Trend Analysis")
    print("="*70)
    user_interests = ['museums', 'culinary', 'hiking']
    analysis = analyzer.analyze_user_trends(user_interests)
    print(f"\nUser interests: {', '.join(analysis['user_interests'])}")
    print(f"Matching trends: {', '.join(analysis['matching_trends'][:5])}")
    print(f"Alignment score: {analysis['trend_alignment_score']:.2%}")
    
    print("\n" + "="*70)
    print("✅ Testing Complete!")
    print("="*70)


if __name__ == "__main__":
    test_trend_analyzer()
