import os
import json
from datetime import datetime
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from backend.app.core.database import SessionLocal
from backend.app.models.expense import Expense
from backend.app.ml.features import ExpenseFeatureExtractor

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "metadata.json")

MIN_REQUIRED_RECORDS = 20

def train_isolation_forest(db_session=None, n_estimators=100, contamination=0.05, random_state=42):
    session = db_session if db_session else SessionLocal()
    try:
        expenses = session.query(Expense).all()
        total_count = len(expenses)
        
        valid_expenses = [e for e in expenses if e.amount is not None]
        usable_count = len(valid_expenses)
        
        if usable_count < MIN_REQUIRED_RECORDS:
            print(f"Insufficient real training data: {usable_count} records found (Minimum required: {MIN_REQUIRED_RECORDS}).")
            return {
                "status": "NOT_TRAINED_INSUFFICIENT_DATA",
                "total_expenses": total_count,
                "usable_records": usable_count,
                "min_required": MIN_REQUIRED_RECORDS
            }
            
        extractor = ExpenseFeatureExtractor()
        X = extractor.transform_batch(valid_expenses)
        
        model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state
        )
        model.fit(X)
        
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        
        metadata = {
            "model_type": "IsolationForest",
            "training_timestamp": datetime.utcnow().isoformat(),
            "training_record_count": usable_count,
            "feature_count": X.shape[1],
            "n_estimators": n_estimators,
            "contamination": contamination,
            "random_state": random_state
        }
        with open(METADATA_PATH, "w") as f:
            json.dump(metadata, f, indent=2)
            
        return {
            "status": "TRAINED",
            "model_path": MODEL_PATH,
            "metadata": metadata,
            "total_expenses": total_count,
            "usable_records": usable_count
        }
    finally:
        if not db_session:
            session.close()

if __name__ == "__main__":
    result = train_isolation_forest()
    print(json.dumps(result, indent=2))
