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
            'preferences': {},
            'feedback': {}
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

    def store_itinerary(self, user_id: str, itinerary_data: Dict[str, Any]) -> bool:
        """Store complete detailed itinerary with all daily activities and costs."""
        try:
            itinerary_entry = {
                'user_id': user_id,
                'destination': itinerary_data.get('destination'),
                'origin': itinerary_data.get('origin'),
                'departure_date': itinerary_data.get('departure_date'),
                'return_date': itinerary_data.get('return_date'),
                'num_days': itinerary_data.get('num_days'),
                'total_budget_inr': itinerary_data.get('total_budget_inr'),
                'total_cost_inr': itinerary_data.get('total_cost_inr'),
                'optimization_score': itinerary_data.get('optimization_score'),
                'combinations_evaluated': itinerary_data.get('combinations_evaluated'),
                'daily_schedules': itinerary_data.get('daily_schedules', []),
                'created_at': datetime.now().isoformat(),
                'query': itinerary_data.get('query', ''),
                'interests': itinerary_data.get('interests', []),
                'dietary_restrictions': itinerary_data.get('dietary_restrictions', [])
            }

            if self.use_mongodb:
                itineraries = self.db['itineraries']
                result = itineraries.insert_one(itinerary_entry)
                print(f"Stored itinerary for user {user_id} (ID: {result.inserted_id})")
            else:
                if 'itineraries' not in self.memory_storage:
                    self.memory_storage['itineraries'] = {}
                if user_id not in self.memory_storage['itineraries']:
                    self.memory_storage['itineraries'][user_id] = []
                self.memory_storage['itineraries'][user_id].append(itinerary_entry)
                print(f"Stored itinerary for user {user_id} in memory")

            return True
        except Exception as e:
            print(f"Error storing itinerary: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_itineraries(self, user_id: str) -> List[Dict]:
        """Get all itineraries for a user."""
        try:
            if self.use_mongodb:
                itineraries = self.db['itineraries']
                return list(itineraries.find({'user_id': user_id}))
            else:
                if 'itineraries' in self.memory_storage:
                    return self.memory_storage['itineraries'].get(user_id, [])
                return []
        except Exception as e:
            print(f"Error retrieving itineraries: {e}")
            return []

    def store_itinerary_output(self, user_id: str, itinerary_text: str, trip_info: Dict[str, Any] = None) -> bool:
        """Store complete itinerary output as raw text (day-by-day format)."""
        try:
            itinerary_entry = {
                'user_id': user_id,
                'output_text': itinerary_text,
                'trip_info': trip_info or {},
                'created_at': datetime.now().isoformat(),
                'text_length': len(itinerary_text)
            }

            if self.use_mongodb:
                output_coll = self.db['itinerary_outputs']
                result = output_coll.insert_one(itinerary_entry)
                print(f"Stored itinerary output for user {user_id} ({len(itinerary_text)} bytes)")
            else:
                if 'itinerary_outputs' not in self.memory_storage:
                    self.memory_storage['itinerary_outputs'] = {}
                if user_id not in self.memory_storage['itinerary_outputs']:
                    self.memory_storage['itinerary_outputs'][user_id] = []
                self.memory_storage['itinerary_outputs'][user_id].append(itinerary_entry)
                print(f"Stored itinerary output for user {user_id} in memory")

            return True
        except Exception as e:
            print(f"Error storing itinerary output: {e}")
            return False

    def get_itinerary_outputs(self, user_id: str) -> List[Dict]:
        """Get all stored itinerary outputs for a user."""
        try:
            if self.use_mongodb:
                output_coll = self.db['itinerary_outputs']
                return list(output_coll.find({'user_id': user_id}))
            else:
                if 'itinerary_outputs' in self.memory_storage:
                    return self.memory_storage['itinerary_outputs'].get(user_id, [])
                return []
        except Exception as e:
            print(f"Error retrieving itinerary outputs: {e}")
            return []

    def get_latest_itinerary(self, user_id: str) -> Optional[Dict]:
        """Get the most recent itinerary for a user."""
        try:
            if self.use_mongodb:
                itineraries = self.db['itineraries']
                return itineraries.find_one(
                    {'user_id': user_id},
                    sort=[('created_at', -1)]
                )
            else:
                itineraries = self.get_itineraries(user_id)
                if itineraries:
                    return sorted(itineraries, key=lambda x: x['created_at'], reverse=True)[0]
                return None
        except Exception as e:
            print(f"Error retrieving latest itinerary: {e}")
            return None

    def store_conversation(self, user_id: str, query: str, response: str, trip_data: Dict[str, Any] = None) -> bool:
        """Store user question and AI response for conversation history."""
        try:
            conversation_entry = {
                'user_id': user_id,
                'query': query,
                'response': response,
                'trip_data': trip_data or {},
                'created_at': datetime.now().isoformat()
            }

            if self.use_mongodb:
                conv = self.db['conversations']
                conv.insert_one(conversation_entry)
            else:
                # Store in memory with a simple list
                if 'conversations' not in self.memory_storage:
                    self.memory_storage['conversations'] = {}
                if user_id not in self.memory_storage['conversations']:
                    self.memory_storage['conversations'][user_id] = []
                self.memory_storage['conversations'][user_id].append(conversation_entry)

            print(f"Stored conversation for user {user_id}")
            return True
        except Exception as e:
            print(f"Error storing conversation: {e}")
            return False

    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """Get conversation history for a user."""
        try:
            if self.use_mongodb:
                conv = self.db['conversations']
                return list(conv.find({'user_id': user_id}))
            else:
                if 'conversations' in self.memory_storage:
                    return self.memory_storage['conversations'].get(user_id, [])
                return []
        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return []

    def store_feedback(self, user_id: str, query: str, rating: int, comment: str = "", response_text: str = "", trip_info: Dict[str, Any] = None) -> bool:
        """Store thumbs-up / thumbs-down feedback per user query with full context."""
        try:
            feedback_entry = {
                'user_id': user_id,
                'query': query,
                'response': response_text[:500] if response_text else "",  # Store first 500 chars
                'rating': rating,
                'rating_emoji': '👍' if rating == 1 else '👎',
                'comment': comment,
                'trip_info': trip_info or {},
                'created_at': datetime.now().isoformat()
            }

            if self.use_mongodb:
                fdb = self.db['feedback']
                result = fdb.insert_one(feedback_entry)
                print(f"Stored feedback for user {user_id}: {feedback_entry['rating_emoji']} (ID: {result.inserted_id})")
            else:
                if user_id not in self.memory_storage['feedback']:
                    self.memory_storage['feedback'][user_id] = []
                self.memory_storage['feedback'][user_id].append(feedback_entry)
                print(f"Stored feedback for user {user_id}: {feedback_entry['rating_emoji']}")

            return True
        except Exception as e:
            print(f"Error storing feedback: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_feedback(self, user_id: str) -> List[Dict]:
        """Retrieve user feedback history."""
        try:
            if self.use_mongodb:
                fdb = self.db['feedback']
                return list(fdb.find({'user_id': user_id}))
            else:
                return self.memory_storage['feedback'].get(user_id, [])
        except Exception as e:
            print(f"Error retrieving feedback: {e}")
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

    def get_user_context(self, user_id: str) -> Optional[str]:
        """Build an in-context history summary for RAG prompt augmentation."""
        profile = self.get_user_profile(user_id)
        history = self.get_trip_history(user_id)

        if not profile and not history:
            return None

        def _clean_for_json(obj):
            """Remove _id and other non-serializable fields for JSON."""
            if isinstance(obj, list):
                return [_clean_for_json(item) for item in obj]
            elif isinstance(obj, dict):
                cleaned = {}
                for k, v in obj.items():
                    if k == '_id':  # Skip MongoDB _id field
                        continue
                    if isinstance(v, (dict, list)):
                        cleaned[k] = _clean_for_json(v)
                    else:
                        try:
                            json.dumps(v)  # Test if serializable
                            cleaned[k] = v
                        except (TypeError, ValueError):
                            cleaned[k] = str(v)  # Convert non-serializable to string
                return cleaned
            else:
                return obj

        ctx_parts = []
        if profile:
            cleaned_profile = _clean_for_json(profile)
            ctx_parts.append("**User Profile**:\n" + json.dumps(cleaned_profile, indent=2))

        if history:
            cleaned_history = _clean_for_json(history)
            ctx_parts.append("**Trip History**:\n" + json.dumps(cleaned_history, indent=2))

        return "\n\n".join(ctx_parts)

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
