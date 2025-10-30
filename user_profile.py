"""
User Profile Management Module
Handles user preference modeling and profile management
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid


@dataclass
class TravelPreferences:
    """Travel preferences dataclass"""
    budget_total: float
    budget_per_day: float
    comfort_level: str  # economy / premium / luxury
    transport_pref: List[str]  # flight, train, bus, car
    accommodation_pref: List[str]  # hotel, apartment, hostel
    dietary_restrictions: List[str]
    activity_interests: List[str]
    avoid: List[str]
    max_daily_travel_minutes: int = 90
    max_activities_per_day: int = 4


@dataclass
class TripDates:
    """Trip date information"""
    start: str  # YYYY-MM-DD
    end: str


@dataclass
class ContactInfo:
    """User contact information"""
    email: str
    phone: str


@dataclass
class HistoricalTrip:
    """Historical trip record"""
    trip_id: str
    rating: float
    tags: List[str]
    destination: Optional[str] = None
    date: Optional[str] = None


class UserProfile:
    """User Profile Management Class"""

    def __init__(self, user_id: Optional[str] = None):
        """Initialize user profile"""
        self.user_id = user_id or str(uuid.uuid4())
        self.name: str = ""
        self.contact: Optional[ContactInfo] = None
        self.destinations: List[str] = []
        self.dates: Optional[TripDates] = None
        self.default_currency: str = "USD"
        self.travel_preferences: Optional[TravelPreferences] = None
        self.historical_trips: List[HistoricalTrip] = []
        self.consent: Dict[str, bool] = {
            "store_history": True,
            "share_anonymized": False
        }

    def from_dict(self, data: Dict[str, Any]) -> 'UserProfile':
        """Create UserProfile from dictionary"""
        self.user_id = data.get('user_id', self.user_id)
        self.name = data.get('name', '')

        # Contact info
        if 'contact' in data:
            self.contact = ContactInfo(**data['contact'])

        # Destinations and dates
        self.destinations = data.get('destinations', [])
        if 'dates' in data:
            self.dates = TripDates(**data['dates'])

        self.default_currency = data.get('default_currency', 'USD')

        # Travel preferences
        if 'travel_preferences' in data:
            self.travel_preferences = TravelPreferences(**data['travel_preferences'])

        # Historical trips
        if 'historical_trips' in data:
            self.historical_trips = [
                HistoricalTrip(**trip) for trip in data['historical_trips']
            ]

        # Consent
        self.consent = data.get('consent', self.consent)

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert UserProfile to dictionary"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'contact': asdict(self.contact) if self.contact else None,
            'destinations': self.destinations,
            'dates': asdict(self.dates) if self.dates else None,
            'default_currency': self.default_currency,
            'travel_preferences': asdict(self.travel_preferences) if self.travel_preferences else None,
            'historical_trips': [asdict(trip) for trip in self.historical_trips],
            'consent': self.consent
        }

    def to_json(self, filepath: Optional[str] = None) -> str:
        """Export profile to JSON"""
        json_data = json.dumps(self.to_dict(), indent=2)

        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_data)

        return json_data

    @classmethod
    def from_json(cls, json_str: Optional[str] = None, filepath: Optional[str] = None) -> 'UserProfile':
        """Load profile from JSON"""
        if filepath:
            with open(filepath, 'r') as f:
                data = json.load(f)
        elif json_str:
            data = json.loads(json_str)
        else:
            raise ValueError("Either json_str or filepath must be provided")

        profile = cls()
        return profile.from_dict(data)

    def validate(self) -> tuple[bool, List[str]]:
        """Validate user profile"""
        errors = []

        if not self.name:
            errors.append("User name is required")

        if not self.destinations:
            errors.append("At least one destination is required")

        if not self.dates:
            errors.append("Travel dates are required")

        if not self.travel_preferences:
            errors.append("Travel preferences are required")
        else:
            # Validate preferences
            if self.travel_preferences.budget_total <= 0:
                errors.append("Budget total must be positive")

            if self.travel_preferences.comfort_level not in ['economy', 'premium', 'luxury']:
                errors.append("Comfort level must be economy, premium, or luxury")

        return len(errors) == 0, errors

    def add_historical_trip(self, trip_id: str, rating: float, tags: List[str], 
                           destination: Optional[str] = None):
        """Add a historical trip to profile"""
        trip = HistoricalTrip(
            trip_id=trip_id,
            rating=rating,
            tags=tags,
            destination=destination,
            date=datetime.now().strftime('%Y-%m-%d')
        )
        self.historical_trips.append(trip)

    def get_interest_vector(self) -> List[str]:
        """Get user interest vector for recommendation"""
        if not self.travel_preferences:
            return []

        interests = self.travel_preferences.activity_interests.copy()

        # Add historical preferences
        for trip in self.historical_trips:
            if trip.rating >= 4.0:  # Only high-rated trips
                interests.extend(trip.tags)

        # Return unique interests
        return list(set(interests))


def create_sample_profile() -> UserProfile:
    """Create a sample user profile for testing"""
    profile = UserProfile(user_id="221IT074")
    profile.name = "Uggumudi Sai Lasya Reddy"
    profile.contact = ContactInfo(
        email="user@example.com",
        phone="+91-XXXXXXXXXX"
    )
    profile.destinations = ["Tokyo, Japan"]
    profile.dates = TripDates(start="2026-03-20", end="2026-03-27")
    profile.default_currency = "INR"
    profile.travel_preferences = TravelPreferences(
        budget_total=50000,
        budget_per_day=8000,
        comfort_level="economy",
        transport_pref=["flight", "train"],
        accommodation_pref=["hotel", "apartment"],
        dietary_restrictions=["vegetarian"],
        activity_interests=["museums", "culinary", "hiking"],
        avoid=["red-eye flights", "late-night travel"],
        max_daily_travel_minutes=90,
        max_activities_per_day=4
    )
    profile.add_historical_trip("t-123", 4.5, ["art", "museum"])

    return profile


if __name__ == "__main__":
    # Test the module
    profile = create_sample_profile()
    print("Sample User Profile Created:")
    print(profile.to_json())

    # Validate
    is_valid, errors = profile.validate()
    print(f"\nProfile Valid: {is_valid}")
    if errors:
        print("Errors:", errors)
