"""
Data collection service for HOT SHARK Bot.
Handles fetching real-time and historical market data from various APIs.
"""

import os
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from app.models.market_data import MarketData
from app.config import Config

class DataCollectorService:
    def __init__(self, db: Session):
        self.db = db
        self.twelve_data_api_key = getattr(Config, 'TWELVE_DATA_API_KEY', None)
        self.polygon_api_key = getattr(Config, 'POLYGON_API_KEY', None)
        self.alpha_vantage_api_key = getattr(Config, 'ALPHA_VANTAGE_API_KEY', None)

    async def fetch_twelve_data(self, symbol: str, interval: str = "1min", outputsize: int = 100) -> List[Dict[str, Any]]:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={self.twelve_data_api_key}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            if data and "values" in data:
                return data["values"]
        return []

    async def fetch_polygon_data(self, symbol: str, multiplier: int = 1, timespan: str = "minute", from_date: str = None, to_date: str = None) -> List[Dict[str, Any]]:
        if not from_date: from_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if not to_date: to_date = datetime.now().strftime("%Y-%m-%d")
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date}?adjusted=true&sort=asc&limit=50000&apiKey={self.polygon_api_key}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            if data and "results" in data:
                return data["results"]
        return []

    async def fetch_alpha_vantage_data(self, symbol: str, interval: str = "1min", outputsize: str = "compact") -> Dict[str, Any]:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={self.alpha_vantage_api_key}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            if data and f"Time Series ({interval})" in data:
                return data[f"Time Series ({interval})"]
        return {}

    async def collect_and_store_data(self, symbol: str, interval: str = "1min", source: str = "TwelveData"):
        data_to_store = []
        if source == "TwelveData":
            raw_data = await self.fetch_twelve_data(symbol, interval)
            for entry in raw_data:
                data_to_store.append(MarketData(
                    symbol=symbol,
                    timestamp=datetime.strptime(entry["datetime"], "%Y-%m-%d %H:%M:%S"),
                    open_price=float(entry["open"]),
                    high_price=float(entry["high"]),
                    low_price=float(entry["low"]),
                    close_price=float(entry["close"]),
                    volume=float(entry["volume"]) if "volume" in entry else 0,
                    interval=interval,
                    source=source
                ))
        elif source == "Polygon.io":
            raw_data = await self.fetch_polygon_data(symbol, timespan=interval.replace("m", "minute").replace("h", "hour").replace("d", "day"))
            for entry in raw_data:
                data_to_store.append(MarketData(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(entry["t"] / 1000), # Convert milliseconds to seconds
                    open_price=float(entry["o"]),
                    high_price=float(entry["h"]),
                    low_price=float(entry["l"]),
                    close_price=float(entry["c"]),
                    volume=float(entry["v"]) if "v" in entry else 0,
                    interval=interval,
                    source=source
                ))
        elif source == "AlphaVantage":
            raw_data = await self.fetch_alpha_vantage_data(symbol, interval)
            for dt_str, values in raw_data.items():
                data_to_store.append(MarketData(
                    symbol=symbol,
                    timestamp=datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"),
                    open_price=float(values["1. open"]),
                    high_price=float(values["2. high"]),
                    low_price=float(values["3. low"]),
                    close_price=float(values["4. close"]),
                    volume=float(values["5. volume"]) if "5. volume" in values else 0,
                    interval=interval,
                    source=source
                ))

        if data_to_store:
            self.db.add_all(data_to_store)
            self.db.commit()
            print(f"Successfully collected and stored {len(data_to_store)} data points for {symbol} from {source}")
        else:
            print(f"No data collected for {symbol} from {source}")

# Example usage (for testing purposes, not part of the main app flow)
async def main():
    from app.models.database import SessionLocal
    db = SessionLocal()
    collector = DataCollectorService(db)
    try:
        # Ensure you have API keys set in your .env file or directly in app.config.settings
        # For example, TWELVE_DATA_API_KEY="YOUR_API_KEY"
        await collector.collect_and_store_data("EUR/USD", "1min", "TwelveData")
        await collector.collect_and_store_data("AAPL", "1day", "Polygon.io")
        await collector.collect_and_store_data("IBM", "5min", "AlphaVantage")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())


