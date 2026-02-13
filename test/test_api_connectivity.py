#!/usr/bin/env python3
"""
Quick API Connectivity Test
Tests all configured APIs and shows their status
"""

import os
import sys
from dotenv import load_dotenv
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def test_ticketmaster():
    """Test Ticketmaster API"""
    print("\n🎫 Testing Ticketmaster API...")
    
    api_key = os.getenv('TICKETMASTER_API_KEY')
    if not api_key:
        print("  ❌ No API key found in .env file")
        return False
    
    try:
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        params = {
            'apikey': api_key,
            'city': 'Tokyo',
            'size': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if '_embedded' in data and 'events' in data['_embedded']:
                event_count = data['page']['totalElements']
                print(f"  ✅ Connected! Found {event_count} events in Tokyo")
                print(f"  Sample event: {data['_embedded']['events'][0]['name']}")
                return True
            else:
                print("  ✅ API connected (no events found for Tokyo, but API works)")
                return True
        elif response.status_code == 401:
            print("  ❌ Authentication failed - check your API key")
            return False
        else:
            print(f"  ❌ Error: Status code {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("  ❌ Request timeout - check your internet connection")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

def test_openweather():
    """Test OpenWeatherMap API"""
    print("\n🌤️  Testing OpenWeatherMap API...")
    
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        print("  ❌ No API key found in .env file")
        return False
    
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': 'Tokyo',
            'appid': api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            weather = data['weather'][0]['description']
            print(f"  ✅ Connected! Tokyo weather: {temp}°C, {weather}")
            return True
        elif response.status_code == 401:
            print("  ❌ Authentication failed - check your API key")
            return False
        else:
            print(f"  ❌ Error: Status code {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("  ❌ Request timeout - check your internet connection")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

def test_serpapi():
    """Test SerpAPI"""
    print("\n📊 Testing SerpAPI (Google Trends)...")
    
    api_key = os.getenv('SERPAPI_API_KEY')
    if not api_key:
        print("  ⚠️  No API key found (optional)")
        return None
    
    try:
        url = "https://serpapi.com/search.json"
        params = {
            'engine': 'google',
            'q': 'test',
            'api_key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print("  ✅ Connected!")
            return True
        elif response.status_code == 401:
            print("  ❌ Authentication failed - check your API key")
            return False
        else:
            print(f"  ❌ Error: Status code {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("  ❌ Request timeout")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

def test_predicthq():
    """Test PredictHQ API"""
    print("\n📅 Testing PredictHQ API...")
    
    token = os.getenv('PREDICTHQ_ACCESS_TOKEN')
    if not token:
        print("  ⚠️  No API token found (optional)")
        return None
    
    try:
        url = "https://api.predicthq.com/v1/events/"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        params = {
            'q': 'Tokyo',
            'limit': 1
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"  ✅ Connected! Found {count} events")
            return True
        elif response.status_code == 401:
            print("  ❌ Authentication failed - check your token")
            return False
        else:
            print(f"  ❌ Error: Status code {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("  ❌ Request timeout")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

def main():
    """Main test function"""
    print_header("🧪 API CONNECTIVITY TEST")
    print(f"\nTesting APIs at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("\n❌ ERROR: .env file not found!")
        print("   Please create .env file from .env.template")
        print("   See API_SETUP_GUIDE.md for instructions")
        return
    
    results = {
        'required': {},
        'optional': {}
    }
    
    # Test required APIs
    print_header("Required APIs (Core Functionality)")
    results['required']['ticketmaster'] = test_ticketmaster()
    results['required']['openweather'] = test_openweather()
    
    # Test optional APIs
    print_header("Optional APIs (Enhanced Features)")
    results['optional']['serpapi'] = test_serpapi()
    results['optional']['predicthq'] = test_predicthq()
    
    # Summary
    print_header("📋 SUMMARY")
    
    required_working = sum(1 for v in results['required'].values() if v is True)
    required_total = len(results['required'])
    
    optional_working = sum(1 for v in results['optional'].values() if v is True)
    optional_configured = sum(1 for v in results['optional'].values() if v is not None)
    
    print(f"\n✅ Required APIs: {required_working}/{required_total} working")
    print(f"⭐ Optional APIs: {optional_working} working, {optional_configured} configured")
    
    # Status message
    if required_working == required_total:
        print("\n" + "🎉"*25)
        print("✅ ALL REQUIRED APIs ARE WORKING!")
        print("🎉"*25)
        print("\n📊 Your Trend Analyzer Features:")
        print("   ✅ Real-time events from Ticketmaster")
        print("   ✅ Weather-based activity suggestions")
        
        if results['optional']['serpapi']:
            print("   ✅ Trending destinations from Google")
        
        if results['optional']['predicthq']:
            print("   ✅ Advanced event intelligence")
        
        print("\n🚀 Next Steps:")
        print("   1. Run: python3 trend_analyzer.py")
        print("      → See real trend data in action!")
        print("")
        print("   2. Run: python3 main.py")
        print("      → Generate complete travel itinerary")
        print("")
        print("   3. Your itinerary will include:")
        print("      • Real events happening at your destination")
        print("      • Weather-appropriate activities")
        print("      • Seasonal attractions")
        
        if optional_working < 2:
            print("\n💡 Optional Enhancement:")
            if not results['optional']['predicthq']:
                print("   → Add PredictHQ for major event impact analysis")
                print("     (Sign up at https://www.predicthq.com/)")
        
    elif required_working > 0:
        print("\n⚠️  Some required APIs are not working.")
        print("   The application will use fallback data for missing APIs.")
        print("\n💡 Recommendations:")
        if not results['required']['ticketmaster']:
            print("   • Set up Ticketmaster API for real events data")
            print("     Get key from: https://developer.ticketmaster.com/")
        if not results['required']['openweather']:
            print("   • Set up OpenWeather API for weather-based suggestions")
            print("     Get key from: https://openweathermap.org/api")
    else:
        print("\n❌ No APIs are configured.")
        print("   The application will use fallback mock data.")
        print("   See API_SETUP_GUIDE.md to set up API keys.")
        print("\n💡 Recommendations:")
        print("   • Set up Ticketmaster API for real events data")
        print("     Get key from: https://developer.ticketmaster.com/")
        print("   • Set up OpenWeather API for weather-based suggestions")
        print("     Get key from: https://openweathermap.org/api")
    
    print("\n" + "="*70)
    print("✅ Test complete! Ready to generate amazing itineraries!")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)