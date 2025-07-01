"""
Data processing service for HOT SHARK Bot.
Handles cleaning, transforming, and feature engineering for market data.
"""

import pandas as pd
from typing import List, Dict, Any
from app.services.ict_smc_analyzer_service import ICTSMCAnalyzerService

class DataProcessorService:
    def __init__(self):
        self.ict_smc_analyzer = ICTSMCAnalyzerService()

    def clean_data(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Cleans raw market data and converts it to a pandas DataFrame."""
        df = pd.DataFrame(data)
        # Convert timestamp to datetime objects
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Handle missing values (e.g., fill with previous values or 0)
        df = df.fillna(0) # Simple fill for now, can be more sophisticated
        
        # Ensure numeric types
        numeric_cols = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates common technical indicators and adds them to the DataFrame."""
        # Simple Moving Average (SMA)
        if 'close_price' in df.columns:
            df['SMA_10'] = df['close_price'].rolling(window=10).mean()
            df['SMA_20'] = df['close_price'].rolling(window=20).mean()

        # Relative Strength Index (RSI)
        if 'close_price' in df.columns:
            delta = df['close_price'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

        # Moving Average Convergence Divergence (MACD)
        if 'close_price' in df.columns:
            exp1 = df['close_price'].ewm(span=12, adjust=False).mean()
            exp2 = df['close_price'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']

        # Bollinger Bands
        if 'close_price' in df.columns:
            df['BB_Middle'] = df['close_price'].rolling(window=20).mean()
            df['BB_StdDev'] = df['close_price'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (df['BB_StdDev'] * 2)
            df['BB_Lower'] = df['BB_Middle'] - (df['BB_StdDev'] * 2)

        return df.fillna(0) # Fill NaN values created by rolling/ewm calculations

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extracts features suitable for ML models from the DataFrame.
        Includes technical indicators and ICT/SMC concepts.
        """
        # Add technical indicators
        df = self.calculate_technical_indicators(df.copy())

        # Add ICT/SMC concepts
        df = self.ict_smc_analyzer.analyze(df.copy())

        # Example: Lagged prices
        if 'close_price' in df.columns:
            df['close_price_lag1'] = df['close_price'].shift(1)
            df['close_price_lag5'] = df['close_price'].shift(5)

        # Price change
        if 'close_price' in df.columns and 'open_price' in df.columns:
            df['price_change'] = df['close_price'] - df['open_price']
            df['daily_range'] = df['high_price'] - df['low_price']

        # Interaction features (example)
        if 'RSI' in df.columns and 'MACD' in df.columns:
            df['RSI_MACD_interaction'] = df['RSI'] * df['MACD']

        return df.fillna(0)

# Example usage (for testing purposes)
if __name__ == "__main__":
    # Sample data (replace with actual data from your database)
    sample_data = [
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:00:00", "open_price": 1.1, "high_price": 1.101, "low_price": 1.099, "close_price": 1.1005, "volume": 100, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:01:00", "open_price": 1.1005, "high_price": 1.1015, "low_price": 1.1, "close_price": 1.101, "volume": 120, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:02:00", "open_price": 1.101, "high_price": 1.102, "low_price": 1.1005, "close_price": 1.1018, "volume": 150, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:03:00", "open_price": 1.1018, "high_price": 1.1019, "low_price": 1.101, "close_price": 1.1012, "volume": 130, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:04:00", "open_price": 1.1012, "high_price": 1.1015, "low_price": 1.1008, "close_price": 1.101, "volume": 110, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:05:00", "open_price": 1.101, "high_price": 1.1005, "low_price": 1.098, "close_price": 1.0985, "volume": 200, "interval": "1min", "source": "TwelveData"}, # Potential bearish OB
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:06:00", "open_price": 1.0985, "high_price": 1.097, "low_price": 1.095, "close_price": 1.0955, "volume": 250, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:07:00", "open_price": 1.0955, "high_price": 1.094, "low_price": 1.092, "close_price": 1.0925, "volume": 300, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:08:00", "open_price": 1.0925, "high_price": 1.093, "low_price": 1.091, "close_price": 1.092, "volume": 180, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:09:00", "open_price": 1.092, "high_price": 1.0935, "low_price": 1.0915, "close_price": 1.093, "volume": 160, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:10:00", "open_price": 1.093, "high_price": 1.095, "low_price": 1.0925, "close_price": 1.0945, "volume": 220, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:11:00", "open_price": 1.0945, "high_price": 1.096, "low_price": 1.094, "close_price": 1.0955, "volume": 240, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:12:00", "open_price": 1.0955, "high_price": 1.098, "low_price": 1.095, "close_price": 1.0975, "volume": 280, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:13:00", "open_price": 1.0975, "high_price": 1.100, "low_price": 1.097, "close_price": 1.0995, "volume": 320, "interval": "1min", "source": "TwelveData"},
        {"symbol": "EUR/USD", "timestamp": "2025-01-01 00:14:00", "open_price": 1.0995, "high_price": 1.102, "low_price": 1.099, "close_price": 1.1015, "volume": 350, "interval": "1min", "source": "TwelveData"}, # Potential bullish OB
    ]

    processor = DataProcessorService()
    
    # 1. Clean data
    cleaned_df = processor.clean_data(sample_data)
    print("\nCleaned Data (first 5 rows):\n", cleaned_df.head())

    # 2. Extract features (now includes indicators and ICT/SMC)
    df_with_features = processor.extract_features(cleaned_df.copy())
    print("\nData with Features (last 5 rows):\n", df_with_features.tail())

    print("\nColumns in final DataFrame:", df_with_features.columns.tolist())


