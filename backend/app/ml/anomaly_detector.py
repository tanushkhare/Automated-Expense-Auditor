import os
import joblib
import numpy as np
from backend.app.ml.features import ExpenseFeatureExtractor

class IsolationForestDetector:
    """
    Optional ML anomaly detector wrapper using Isolation Forest.
    Fails gracefully if the model artifact does not exist.
    """
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "models", "isolation_forest.joblib")
        self.model_path = model_path
        self.model = None
        self.extractor = ExpenseFeatureExtractor()
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
            except Exception as e:
                print(f"Warning: Failed to load Isolation Forest model from {self.model_path}: {e}")
                self.model = None
        else:
            self.model = None

    def is_available(self) -> bool:
        return self.model is not None

    def score(self, expense) -> float:
        if not self.is_available():
            return 0.0
        try:
            features = self.extractor.extract_features(expense)
            X = np.array(features).reshape(1, -1)
            raw_score = self.model.decision_function(X)[0]
            risk_score = float(1.0 / (1.0 + np.exp(raw_score)))
            return risk_score
        except Exception as e:
            print(f"Error during Isolation Forest scoring: {e}")
            return 0.0
