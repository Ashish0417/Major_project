import os
import joblib
from sentence_transformers import SentenceTransformer

class FeedbackPredictor:
    """Service to predict optimization weights from user feedback text"""
    
    def __init__(self, model_dir="saved_feedback_model"):
        self.model_dir = model_dir
        self.model_path = os.path.join(self.model_dir, "best_feedback_model.pkl")
        self.embedder_name = "all-MiniLM-L6-v2"
        self.model = None
        self.embedder = None
        # We try loading right away, but it's safe if it fails (lazy retry later)
        self._load_models()

    def _load_models(self):
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.embedder = SentenceTransformer(self.embedder_name)
                print(f"✅ Loaded NLP feedback model from {self.model_path}")
            else:
                print(f"⚠️  Predictor model not found at {self.model_path}. Will wait for training to finish.")
        except Exception as e:
            print(f"⚠️  Error loading NLP predictor models: {e}")

    def predict_weights_delta(self, feedback_text: str) -> dict:
        """
        Predicts the 4 constraint deltas from unstructured feedback text.
        Returns a dictionary containing predicted deltas, or empty dict if failure.
        """
        if not self.model or not self.embedder:
            self._load_models() # Try loading again in case training finishing recently
            if not self.model or not self.embedder:
                return {}

        try:
            vec = self.embedder.encode(
                [feedback_text],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            out = self.model.predict(vec)[0]

            return {
                "cost": round(float(out[0]), 3),
                "time": round(float(out[1]), 3),
                "pref": round(float(out[2]), 3),
                "pop": round(float(out[3]), 3)
            }
        except Exception as e:
            print(f"⚠️  NLP Inference error: {e}")
            return {}

# Provide a global instance map to avoid reloading transformers constantly
predictor = FeedbackPredictor()
