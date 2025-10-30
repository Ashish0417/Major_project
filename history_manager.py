"""
History Manager Module
Handles user history storage and collaborative filtering
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class HistoryManager:
    """
    Manages user history and implements collaborative filtering
    Uses MongoDB for storage (mock implementation included)
    """

    def __init__(self, use_mongodb: bool = False, mongo_uri: str = "mongodb://localhost:27017"):
        """Initialize history manager"""
        self.use_mongodb = use_mongodb
        self.mongo_uri = mongo_uri
        self.db = None
        self.collection = None

        # In-memory storage (fallback)
        self.memory_storage = {
            'users': {},
            'trips': {},
            'preferences': {}
        }

        if self.use_mongodb:
            self._connect_mongodb()

    def _connect_mongodb(self):
        """Connect to MongoDB"""
        try:
            from pymongo import MongoClient
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client['travel_planner']
            self.collection = self.db['user_profiles']
            print("Connected to MongoDB")
        except ImportError:
            print("Warning: pymongo not installed. Using in-memory storage.")
            self.use_mongodb = False
        except Exception as e:
            print(f"MongoDB connection failed: {e}. Using in-memory storage.")
            self.use_mongodb = False

    def store_user_profile(self, user_profile: Any) -> bool:
        """Store or update user profile"""
        try:
            profile_dict = user_profile.to_dict()
            profile_dict['updated_at'] = datetime.now().isoformat()

            if self.use_mongodb:
                self.collection.update_one(
                    {'user_id': profile_dict['user_id']},
                    {'$set': profile_dict},
                    upsert=True
                )
            else:
                self.memory_storage['users'][profile_dict['user_id']] = profile_dict

            print(f"Stored profile for user {profile_dict['user_id']}")
            return True
        except Exception as e:
            print(f"Error storing profile: {e}")
            return False

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Retrieve user profile"""
        try:
            if self.use_mongodb:
                return self.collection.find_one({'user_id': user_id})
            else:
                return self.memory_storage['users'].get(user_id)
        except Exception as e:
            print(f"Error retrieving profile: {e}")
            return None

    def store_trip_history(self, user_id: str, trip_data: Dict[str, Any]) -> bool:
        """Store completed trip in history"""
        try:
            trip_data['user_id'] = user_id
            trip_data['stored_at'] = datetime.now().isoformat()

            if self.use_mongodb:
                trips_collection = self.db['trip_history']
                trips_collection.insert_one(trip_data)
            else:
                if user_id not in self.memory_storage['trips']:
                    self.memory_storage['trips'][user_id] = []
                self.memory_storage['trips'][user_id].append(trip_data)

            print(f"Stored trip history for user {user_id}")
            return True
        except Exception as e:
            print(f"Error storing trip: {e}")
            return False

    def get_trip_history(self, user_id: str) -> List[Dict]:
        """Get user's trip history"""
        try:
            if self.use_mongodb:
                trips_collection = self.db['trip_history']
                return list(trips_collection.find({'user_id': user_id}))
            else:
                return self.memory_storage['trips'].get(user_id, [])
        except Exception as e:
            print(f"Error retrieving trip history: {e}")
            return []

    def cluster_users(self, num_clusters: int = 5) -> Dict[str, List[str]]:
        """
        Cluster users based on preferences using K-Means
        Returns dict mapping cluster_id to list of user_ids
        """
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            import numpy as np

            # Get all users
            if self.use_mongodb:
                users = list(self.collection.find())
            else:
                users = list(self.memory_storage['users'].values())

            if len(users) < num_clusters:
                print("Not enough users for clustering")
                return {'cluster_0': [u['user_id'] for u in users]}

            # Extract features for clustering
            features = []
            user_ids = []

            for user in users:
                if 'travel_preferences' not in user:
                    continue

                prefs = user['travel_preferences']

                # Create feature vector
                feature_vector = [
                    prefs.get('budget_total', 0),
                    prefs.get('budget_per_day', 0),
                    1 if prefs.get('comfort_level') == 'economy' else 2 if prefs.get('comfort_level') == 'premium' else 3,
                    len(prefs.get('activity_interests', [])),
                    prefs.get('max_activities_per_day', 4)
                ]

                features.append(feature_vector)
                user_ids.append(user['user_id'])

            if not features:
                return {}

            # Normalize features
            scaler = StandardScaler()
            features_normalized = scaler.fit_transform(features)

            # Perform K-Means clustering
            kmeans = KMeans(n_clusters=min(num_clusters, len(features)), random_state=42)
            clusters = kmeans.fit_predict(features_normalized)

            # Group users by cluster
            cluster_map = {}
            for user_id, cluster_id in zip(user_ids, clusters):
                cluster_key = f'cluster_{cluster_id}'
                if cluster_key not in cluster_map:
                    cluster_map[cluster_key] = []
                cluster_map[cluster_key].append(user_id)

            print(f"Clustered {len(user_ids)} users into {len(cluster_map)} clusters")
            return cluster_map

        except ImportError:
            print("sklearn not available for clustering")
            return {}
        except Exception as e:
            print(f"Error clustering users: {e}")
            return {}

    def collaborative_filtering(self, user_id: str, top_n: int = 5) -> List[Dict]:
        """
        Recommend items based on similar users (collaborative filtering)
        Returns top N recommended destinations/activities
        """
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np

            # Get current user
            current_user = self.get_user_profile(user_id)
            if not current_user or 'travel_preferences' not in current_user:
                return []

            # Get all users
            if self.use_mongodb:
                all_users = list(self.collection.find({'user_id': {'$ne': user_id}}))
            else:
                all_users = [u for uid, u in self.memory_storage['users'].items() if uid != user_id]

            if not all_users:
                return []

            # Build user-item matrix (simplified)
            # Features: budget, comfort, interests
            current_interests = set(current_user.get('travel_preferences', {}).get('activity_interests', []))

            similarities = []
            for other_user in all_users:
                if 'travel_preferences' not in other_user:
                    continue

                other_interests = set(other_user['travel_preferences'].get('activity_interests', []))

                # Jaccard similarity for interests
                if current_interests or other_interests:
                    intersection = len(current_interests & other_interests)
                    union = len(current_interests | other_interests)
                    similarity = intersection / union if union > 0 else 0
                else:
                    similarity = 0

                similarities.append((similarity, other_user))

            # Sort by similarity
            similarities.sort(key=lambda x: x[0], reverse=True)

            # Get recommendations from most similar users
            recommendations = []
            for similarity, similar_user in similarities[:5]:
                # Get their trip history
                trips = self.get_trip_history(similar_user['user_id'])
                for trip in trips:
                    if trip.get('rating', 0) >= 4.0:  # Only highly rated trips
                        recommendations.append({
                            'destination': trip.get('destination'),
                            'activities': trip.get('activities', []),
                            'similarity_score': similarity,
                            'rating': trip.get('rating')
                        })

            # Return top N unique recommendations
            seen = set()
            unique_recs = []
            for rec in recommendations:
                if rec['destination'] not in seen:
                    seen.add(rec['destination'])
                    unique_recs.append(rec)
                if len(unique_recs) >= top_n:
                    break

            return unique_recs

        except ImportError:
            print("sklearn not available for collaborative filtering")
            return []
        except Exception as e:
            print(f"Error in collaborative filtering: {e}")
            return []

    def export_data(self, filepath: str) -> bool:
        """Export all data to JSON file"""
        try:
            if self.use_mongodb:
                # Export from MongoDB
                data = {
                    'users': list(self.collection.find({}, {'_id': 0})),
                    'trips': list(self.db['trip_history'].find({}, {'_id': 0}))
                }
            else:
                data = self.memory_storage

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            print(f"Data exported to {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False


if __name__ == "__main__":
    # Test the History Manager
    manager = HistoryManager(use_mongodb=False)

    print("History Manager Test")
    print("Using in-memory storage")

    # Test would require user profile objects
    print("\nModule loaded successfully!")
