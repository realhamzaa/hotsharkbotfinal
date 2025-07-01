"""
Training Service for HOT SHARK Bot.
Handles the periodic training and retraining of ML models using collected market data.
"""

import pandas as pd
from sqlalchemy.orm import Session
from app.models.market_data import MarketData, Signal
from app.services.data_processor_service import DataProcessorService
from app.services.ml_model_service import MLModelService
from datetime import datetime, timedelta

class TrainingService:
    def __init__(self, db: Session):
        self.db = db
        self.data_processor = DataProcessorService()
        self.ml_model_service = MLModelService(model_path="./models/trading_model.joblib")

    def get_training_data(self, symbol: str, interval: str, lookback_days: int = 30) -> pd.DataFrame:
        """Fetches historical market data for training."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        market_data_records = self.db.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.interval == interval,
            MarketData.timestamp >= start_date,
            MarketData.timestamp <= end_date
        ).order_by(MarketData.timestamp).all()

        if not market_data_records:
            print(f"No market data found for {symbol} ({interval}) in the last {lookback_days} days.")
            return pd.DataFrame()

        # Convert SQLAlchemy objects to dictionaries for DataFrame creation
        data_dicts = [{
            "symbol": d.symbol,
            "timestamp": d.timestamp,
            "open_price": d.open_price,
            "high_price": d.high_price,
            "low_price": d.low_price,
            "close_price": d.close_price,
            "volume": d.volume,
            "interval": d.interval,
            "source": d.source
        } for d in market_data_records]

        df = pd.DataFrame(data_dicts)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def generate_dummy_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generates dummy signals for training purposes.
        In a real scenario, these would be derived from historical successful trades or expert labels.
        For now, a simple rule-based dummy signal is used.
        """
        # Example: Simple rule - if close price increased significantly, it was a BUY, else SELL/HOLD
        df["price_change"] = df["close_price"].diff()
        df["signal_type"] = "HOLD"
        df.loc[df["price_change"] > df["price_change"].quantile(0.75), "signal_type"] = "BUY"
        df.loc[df["price_change"] < df["price_change"].quantile(0.25), "signal_type"] = "SELL"
        return df

    async def train_and_evaluate_model(self, symbol: str, interval: str, model_type: str = "RandomForest"):
        """Collects data, processes it, trains, and evaluates the ML model.
        This method will be called periodically for retraining.
        """
        print(f"Starting training process for {symbol} ({interval})...")
        df_raw = self.get_training_data(symbol, interval)
        if df_raw.empty:
            print(f"Skipping training for {symbol} ({interval}) due to insufficient data.")
            return

        # Process data and extract features (including ICT/SMC)
        df_processed = self.data_processor.extract_features(df_raw.copy())
        
        # Generate dummy signals for training (replace with real labels in production)
        df_processed = self.generate_dummy_signals(df_processed)

        # Prepare data for ML model
        try:
            X, y, _ = self.ml_model_service.prepare_data_for_training(df_processed, target_column="signal_type")
        except ValueError as e:
            print(f"Error preparing data for training: {e}")
            return

        # Split data for training and testing
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the model
        self.ml_model_service.train_model(X_train, y_train, model_type=model_type)

        # Evaluate the model
        metrics = self.ml_model_service.evaluate_model(X_test, y_test)
        print(f"Training and evaluation complete for {symbol} ({interval}). Metrics: {metrics}")

        # Self-learning/Retraining logic (simplified here)
        # In a real RL scenario, the model would learn from rewards/penalties of actual trades.
        # Here, we simulate retraining with new data, which is handled by the MLModelService.

# Example usage (for testing purposes)
async def main():
    from app.models.database import SessionLocal
    db = SessionLocal()
    try:
        training_service = TrainingService(db)
        await training_service.train_and_evaluate_model("EUR/USD", "1min")
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


