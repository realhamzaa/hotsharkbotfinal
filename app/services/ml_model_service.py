"""
Machine Learning Model Service for HOT SHARK Bot.
Handles building, training, evaluating, saving, loading, and self-learning of ML models for trading signals.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib # For saving/loading scikit-learn models
import os

# For simplicity, we'll use scikit-learn for initial models.
# For more complex models (Neural Networks, Reinforcement Learning),
# TensorFlow/Keras or PyTorch would be used.
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

class MLModelService:
    def __init__(self, model_path: str = "./models/trading_model.joblib"):
        self.scaler = MinMaxScaler()
        self.model = None # This will hold the trained model
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Loads a pre-trained model if it exists."""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print(f"Model loaded from {self.model_path}")
        else:
            print("No pre-trained model found. A new model will be trained.")

    def _save_model(self):
        """Saves the trained model to disk."""
        if self.model:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            print(f"Model saved to {self.model_path}")

    def prepare_data_for_training(self, df: pd.DataFrame, target_column: str = 'signal_type') -> tuple[np.ndarray, np.ndarray, MinMaxScaler]:
        """Prepares data for ML model training: scaling and feature/target split.
        Assumes df contains features and a target column.
        """
        if target_column not in df.columns:
            raise ValueError(f"Target column \'{target_column}\' not found in DataFrame.")

        # Drop non-numeric or irrelevant columns for training
        features_df = df.drop(columns=[col for col in df.columns if col in ['symbol', 'timestamp', 'interval', 'source', target_column]], errors='ignore')
        
        # Handle any remaining NaN values after feature extraction (e.g., from initial rows of indicators)
        features_df = features_df.fillna(0)

        # Scale features
        # Fit scaler only on training data, transform all data
        if self.model is None: # Only fit scaler if no model is loaded (first training)
            scaled_features = self.scaler.fit_transform(features_df)
        else:
            scaled_features = self.scaler.transform(features_df)
        
        # Get target variable
        target = df[target_column].values

        return scaled_features, target, self.scaler

    def train_model(self, X_train: np.ndarray, y_train: np.ndarray, model_type: str = 'RandomForest'):
        """Trains a machine learning model.
        For initial implementation, using RandomForestClassifier.
        """
        if self.model is None or model_type != self.model.__class__.__name__:
            if model_type == 'RandomForest':
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif model_type == 'LogisticRegression':
                self.model = LogisticRegression(random_state=42, solver='liblinear')
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
        
        self.model.fit(X_train, y_train)
        self._save_model()
        print(f"Model ({model_type}) trained successfully.")

    def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Evaluates the trained model and returns performance metrics."""
        if self.model is None:
            raise ValueError("Model has not been trained yet.")
        
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        print(f"Model Accuracy: {accuracy:.4f}")
        print("Classification Report:")
        print(classification_report(y_test, y_pred))
        
        return {"accuracy": accuracy, "report": report}

    def predict_signal(self, new_data: pd.DataFrame) -> Any:
        """Predicts a trading signal for new, unseen data.
        new_data should have the same features as the training data.
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet.")
        
        # Ensure new_data has the same columns as the training features
        # and fill any missing ones with 0 or appropriate default
        processed_new_data = new_data.drop(columns=[col for col in new_data.columns if col in ['symbol', 'timestamp', 'interval', 'source']], errors='ignore')
        processed_new_data = processed_new_data.fillna(0) # Fill NaNs for prediction

        # Scale the new data using the *fitted* scaler
        scaled_new_data = self.scaler.transform(processed_new_data)
        
        prediction = self.model.predict(scaled_new_data)
        return prediction[0]

    def self_learn_and_retrain(self, new_data: pd.DataFrame, target_column: str = 'signal_type'):
        """Incorporates new data for continuous self-learning and retraining.
        This is a simplified approach. For true reinforcement learning, a more complex setup is needed.
        """
        print("Initiating self-learning and retraining process...")
        
        # Prepare new data for training
        X_new, y_new, _ = self.prepare_data_for_training(new_data, target_column)
        
        # Combine with existing data (if applicable, for simplicity we're just retraining on new data here)
        # In a real scenario, you'd load historical data, combine, and then retrain.
        
        # Retrain the model with the new data
        # This assumes the model type is already set from initial training
        if self.model:
            self.train_model(X_new, y_new, model_type=self.model.__class__.__name__)
            print("Model retrained with new data.")
        else:
            print("No model to retrain. Please train an initial model first.")

# Example usage (for testing purposes)
if __name__ == "__main__":
    # Create dummy data for demonstration
    data = {
        'open_price': np.random.rand(100) * 100,
        'high_price': np.random.rand(100) * 100 + 1,
        'low_price': np.random.rand(100) * 100 - 1,
        'close_price': np.random.rand(100) * 100,
        'volume': np.random.rand(100) * 1000,
        'SMA_10': np.random.rand(100) * 100,
        'RSI': np.random.rand(100) * 100,
        'MACD': np.random.rand(100) * 10,
        'is_bullish_ob': np.random.choice([True, False], 100),
        'is_bearish_ob': np.random.choice([True, False], 100),
        'is_liquidity_zone': np.random.choice([True, False], 100),
        'is_bullish_fvg': np.random.choice([True, False], 100),
        'is_bearish_fvg': np.random.choice([True, False], 100),
        'signal_type': np.random.choice(['BUY', 'SELL', 'HOLD'], 100) # Dummy target
    }
    df = pd.DataFrame(data)

    # Initialize ML service (will try to load existing model)
    ml_service = MLModelService(model_path="./test_model.joblib")

    # Prepare data
    X, y, scaler = ml_service.prepare_data_for_training(df)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model (if not loaded)
    if ml_service.model is None:
        ml_service.train_model(X_train, y_train, model_type='RandomForest')

    # Evaluate model
    metrics = ml_service.evaluate_model(X_test, y_test)
    print(f"Evaluation Metrics: {metrics}")

    # Predict new signal
    new_sample = pd.DataFrame({
        'open_price': [50],
        'high_price': [51],
        'low_price': [49],
        'close_price': [50.5],
        'volume': [500],
        'SMA_10': [50],
        'RSI': [60],
        'MACD': [2],
        'is_bullish_ob': [False],
        'is_bearish_ob': [True],
        'is_liquidity_zone': [False],
        'is_bullish_fvg': [False],
        'is_bearish_fvg': [False]
    })
    predicted_signal = ml_service.predict_signal(new_sample)
    print(f"Predicted Signal for new data: {predicted_signal}")

    # Simulate self-learning with new data
    new_data_for_learning = {
        'open_price': np.random.rand(10) * 100,
        'high_price': np.random.rand(10) * 100 + 1,
        'low_price': np.random.rand(10) * 100 - 1,
        'close_price': np.random.rand(10) * 100,
        'volume': np.random.rand(10) * 1000,
        'SMA_10': np.random.rand(10) * 100,
        'RSI': np.random.rand(10) * 100,
        'MACD': np.random.rand(10) * 10,
        'is_bullish_ob': np.random.choice([True, False], 10),
        'is_bearish_ob': np.random.choice([True, False], 10),
        'is_liquidity_zone': np.random.choice([True, False], 10),
        'is_bullish_fvg': np.random.choice([True, False], 10),
        'is_bearish_fvg': np.random.choice([True, False], 10),
        'signal_type': np.random.choice(['BUY', 'SELL', 'HOLD'], 10) # Dummy target
    }
    new_df = pd.DataFrame(new_data_for_learning)
    ml_service.self_learn_and_retrain(new_df)

    # Clean up test model file
    if os.path.exists("./test_model.joblib"):
        os.remove("./test_model.joblib")
        print("Cleaned up test_model.joblib")


