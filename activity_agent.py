"""
Activity & Experience Agent Module
Handles activity and experience recommendations
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import random


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

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


class ActivityAgent:
    """Activity & Experience Agent - handles activity searches"""

    def __init__(self, api_key: Optional[str] = None, use_mock: bool = True):
        self.api_key = api_key or os.getenv('VIATOR_API_KEY')
        self.use_mock = use_mock

    def search_activities(self,
                         location: str,
                         categories: Optional[List[str]] = None,
                         interests: Optional[List[str]] = None,
                         max_duration_minutes: Optional[int] = None,
                         max_price: Optional[float] = None,
                         min_rating: float = 3.5,
                         max_results: int = 15) -> List[ActivityOption]:
        """Search for activities and experiences"""
        if self.use_mock:
            return self._mock_activity_search(
                location, categories, interests, max_duration_minutes,
                max_price, min_rating, max_results
            )

        return self._mock_activity_search(
            location, categories, interests, max_duration_minutes,
            max_price, min_rating, max_results
        )

    def _mock_activity_search(self, location, categories, interests,
                             max_duration_minutes, max_price, min_rating,
                             max_results) -> List[ActivityOption]:
        """Generate mock activity data"""

        activity_data = {
            'museums': [
                ('Tokyo National Museum', 'Largest art museum in Japan', 180, 1200),
                ('Mori Art Museum', 'Contemporary art museum', 120, 1800),
                ('teamLab Borderless', 'Digital art museum', 150, 2500),
            ],
            'culinary': [
                ('Sushi Making Workshop', 'Learn to make authentic sushi', 120, 3500),
                ('Tokyo Food Tour', 'Explore local food markets', 180, 4000),
                ('Ramen Cooking Class', 'Master the art of ramen', 150, 3000),
            ],
            'outdoor': [
                ('Mount Fuji Day Trip', 'Visit Japan\'s iconic mountain', 600, 5000),
                ('Tokyo Bay Cruise', 'Scenic bay cruise', 90, 2500),
                ('Imperial Palace Gardens Walk', 'Historical gardens tour', 120, 800),
            ],
            'cultural': [
                ('Tea Ceremony Experience', 'Traditional Japanese tea ceremony', 90, 2000),
                ('Kimono Wearing Experience', 'Dress in traditional kimono', 60, 2500),
                ('Samurai Museum Tour', 'Learn about samurai history', 90, 1500),
            ],
            'tour': [
                ('Tokyo City Highlights', 'Full-day city tour', 480, 6000),
                ('Night Tokyo Tour', 'Experience Tokyo nightlife', 180, 3500),
                ('Asakusa Walking Tour', 'Explore historic Asakusa', 150, 1200),
            ]
        }

        if categories is None:
            categories = list(activity_data.keys())

        activities = []
        activity_count = 0

        for category in categories:
            if category not in activity_data:
                continue

            for name, desc, duration, base_price in activity_data[category]:
                if activity_count >= max_results:
                    break

                # Apply price variation
                price = base_price * random.uniform(0.9, 1.1)

                if max_price and price > max_price:
                    continue

                if max_duration_minutes and duration > max_duration_minutes:
                    continue

                rating = random.uniform(max(min_rating, 4.0), 5.0)

                # Opening hours
                hours = {
                    'monday': '09:00-17:00',
                    'tuesday': '09:00-17:00',
                    'wednesday': '09:00-17:00',
                    'thursday': '09:00-17:00',
                    'friday': '09:00-18:00',
                    'saturday': '09:00-18:00',
                    'sunday': '09:00-17:00'
                }

                # Time slots
                time_slots = ['09:00', '11:00', '13:00', '15:00']

                activity = ActivityOption(
                    activity_id=f"ACT{activity_count+1}_{category.upper()[:3]}",
                    name=name,
                    category=category,
                    description=desc,
                    address=f"{random.randint(1,50)} District, {location}",
                    latitude=35.6762 + random.uniform(-0.08, 0.08),
                    longitude=139.6503 + random.uniform(-0.08, 0.08),
                    duration_minutes=duration,
                    price=round(price, 2),
                    currency='INR',
                    rating=round(rating, 1),
                    review_count=random.randint(50, 2000),
                    popularity_score=random.uniform(0.7, 1.0),
                    opening_hours=hours,
                    time_slots=time_slots,
                    booking_required=random.choice([True, False]),
                    suitable_for=random.sample(['families', 'solo', 'groups', 'couples'], k=2),
                    difficulty_level=random.choice(['easy', 'moderate']),
                    indoor_outdoor=random.choice(['indoor', 'outdoor', 'both'])
                )
                activities.append(activity)
                activity_count += 1

        # Sort by popularity and rating
        activities.sort(key=lambda x: (x.popularity_score, x.rating), reverse=True)

        return activities[:max_results]

    def filter_by_interests(self, activities: List[ActivityOption],
                           interests: List[str]) -> List[ActivityOption]:
        """Filter activities by user interests"""
        if not interests:
            return activities

        # Map interests to categories
        interest_mapping = {
            'museums': ['museums', 'cultural'],
            'art': ['museums', 'cultural'],
            'culinary': ['culinary'],
            'food': ['culinary'],
            'hiking': ['outdoor'],
            'outdoor': ['outdoor'],
            'culture': ['cultural'],
            'history': ['cultural', 'museums'],
            'adventure': ['outdoor', 'tour']
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

        max_price = max(act.price for act in activities)
        max_duration = max(act.duration_minutes for act in activities)

        scored = []
        for activity in activities:
            price_score = 1 - (activity.price / max_price) if max_price > 0 else 1
            rating_score = activity.rating / 5.0
            popularity_score = activity.popularity_score
            # Shorter activities score higher for flexibility
            duration_score = 1 - (activity.duration_minutes / max_duration) if max_duration > 0 else 1

            total_score = (
                weight_price * price_score +
                weight_rating * rating_score +
                weight_popularity * popularity_score +
                weight_duration * duration_score
            )

            scored.append((total_score, activity))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [activity for _, activity in scored]

    def mark_must_do(self, activity: ActivityOption) -> None:
        """Mark an activity as must-do"""
        activity.popularity_score = min(1.0, activity.popularity_score + 0.1)


if __name__ == "__main__":
    agent = ActivityAgent(use_mock=True)

    print("Searching activities in Tokyo...")
    activities = agent.search_activities(
        location="Tokyo",
        categories=['museums', 'culinary', 'outdoor'],
        max_results=8
    )

    print(f"\nFound {len(activities)} activities:")
    for i, act in enumerate(activities, 1):
        print(f"\n{i}. {act.name} ({act.category})")
        print(f"   {act.description}")
        print(f"   Duration: {act.duration_minutes} mins")
        print(f"   Price: {act.currency} {act.price}")
        print(f"   Rating: {act.rating}/5 ({act.review_count} reviews)")
        print(f"   Popularity: {act.popularity_score:.2f}")

    # Filter by interests
    print("\n" + "="*50)
    print("Filtering by interests: museums, culinary...")
    filtered = agent.filter_by_interests(activities, ['museums', 'culinary'])
    print(f"Filtered to {len(filtered)} activities")
