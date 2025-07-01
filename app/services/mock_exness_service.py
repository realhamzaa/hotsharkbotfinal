"""
Mock Exness Data Service for HOT SHARK Bot.
Simulates Exness data for testing without MetaTrader 5.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import random

from sqlalchemy.orm import Session
from app.models.market_data import MarketData
from app.config import Config

logger = logging.getLogger(__name__)

class MockExnessDataService:
    """Mock service for simulating Exness market data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.mt5_initialized = True  # Always initialized in mock
        
        # Mock symbol mapping
        self.symbol_mapping = {
            'XAUUSD': 'XAUUSD',
            'EURUSD': 'EURUSD',
            'GBPUSD': 'GBPUSD', 
            'USDJPY': 'USDJPY',
            'GBPJPY': 'GBPJPY',
            'BTCUSD': 'BTCUSD',
            'ETHUSD': 'ETHUSD',
            'US30': 'US30',
            'US100': 'US100'
        }
        
        # Base prices for simulation
        self.base_prices = {
            'XAUUSD': 2650.0,
            'EURUSD': 1.0850,
            'GBPUSD': 1.2750,
            'USDJPY': 149.50,
            'GBPJPY': 190.75,
            'BTCUSD': 95000.0,
            'ETHUSD': 3400.0,
            'US30': 44500.0,
            'US100': 19800.0
        }
    
    async def initialize_mt5(self) -> bool:
        """Mock MT5 initialization"""
        logger.info("Mock MT5 initialized successfully")
        return True
    
    def shutdown_mt5(self):
        """Mock MT5 shutdown"""
        logger.info("Mock MT5 connection closed")
    
    def get_exness_symbol(self, symbol: str) -> str:
        """Convert standard symbol to Exness format"""
        return self.symbol_mapping.get(symbol, symbol)
    
    def _generate_realistic_price_movement(self, base_price: float, volatility: float = 0.001) -> float:
        """Generate realistic price movement"""
        # Use random walk with mean reversion
        change_percent = np.random.normal(0, volatility)
        return base_price * (1 + change_percent)
    
    async def get_tick_data(self, symbol: str, count: int = 1000) -> List[Dict[str, Any]]:
        """Generate mock tick data"""
        try:
            base_price = self.base_prices.get(symbol, 100.0)
            tick_data = []
            
            current_time = datetime.now()
            current_price = base_price
            
            for i in range(count):
                # Generate realistic tick data
                timestamp = current_time - timedelta(seconds=count - i)
                
                # Simulate bid/ask spread
                spread = base_price * 0.0001  # 1 pip spread
                bid = current_price - spread / 2
                ask = current_price + spread / 2
                
                # Generate volume (higher during market hours)
                hour = timestamp.hour
                if 8 <= hour <= 17:  # Market hours
                    volume = random.randint(50, 500)
                else:
                    volume = random.randint(10, 100)
                
                tick_data.append({
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'bid': round(bid, 5),
                    'ask': round(ask, 5),
                    'last': round(current_price, 5),
                    'volume': volume,
                    'flags': 1
                })
                
                # Update price for next tick
                current_price = self._generate_realistic_price_movement(current_price, 0.0005)
            
            logger.info(f"Generated {len(tick_data)} mock ticks for {symbol}")
            return tick_data
            
        except Exception as e:
            logger.error(f"Error generating mock tick data for {symbol}: {e}")
            return []
    
    async def get_ohlcv_data(self, symbol: str, timeframe: str = "M1", count: int = 1000) -> List[Dict[str, Any]]:
        """Generate mock OHLCV data"""
        try:
            base_price = self.base_prices.get(symbol, 100.0)
            ohlcv_data = []
            
            # Determine timeframe in minutes
            timeframe_minutes = {
                "M1": 1, "M5": 5, "M15": 15, "M30": 30,
                "H1": 60, "H4": 240, "D1": 1440
            }.get(timeframe, 1)
            
            current_time = datetime.now()
            current_price = base_price
            
            for i in range(count):
                # Generate timestamp
                timestamp = current_time - timedelta(minutes=timeframe_minutes * (count - i))
                
                # Generate OHLCV data
                open_price = current_price
                
                # Generate realistic price movement for the period
                volatility = 0.002 * timeframe_minutes  # Higher volatility for longer timeframes
                high_price = open_price * (1 + abs(np.random.normal(0, volatility)))
                low_price = open_price * (1 - abs(np.random.normal(0, volatility)))
                close_price = self._generate_realistic_price_movement(open_price, volatility)
                
                # Ensure OHLC logic
                high_price = max(high_price, open_price, close_price)
                low_price = min(low_price, open_price, close_price)
                
                # Generate volume (higher for longer timeframes)
                base_volume = 1000 * timeframe_minutes
                volume = random.randint(int(base_volume * 0.5), int(base_volume * 2))
                
                # Generate spread
                spread = int(base_price * 0.0001 * 10)  # In points
                
                ohlcv_data.append({
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'open': round(open_price, 5),
                    'high': round(high_price, 5),
                    'low': round(low_price, 5),
                    'close': round(close_price, 5),
                    'volume': volume,
                    'spread': spread,
                    'timeframe': timeframe
                })
                
                # Update current price for next candle
                current_price = close_price
            
            logger.info(f"Generated {len(ohlcv_data)} mock OHLCV bars for {symbol}")
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Error generating mock OHLCV data for {symbol}: {e}")
            return []
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate mock symbol information"""
        try:
            base_price = self.base_prices.get(symbol, 100.0)
            
            # Determine digits based on symbol type
            if 'JPY' in symbol:
                digits = 3
                point = 0.001
            elif symbol in ['XAUUSD', 'BTCUSD', 'ETHUSD', 'US30', 'US100']:
                digits = 2
                point = 0.01
            else:
                digits = 5
                point = 0.00001
            
            return {
                'symbol': symbol,
                'description': f"Mock {symbol}",
                'currency_base': symbol[:3] if len(symbol) >= 6 else 'USD',
                'currency_profit': symbol[3:] if len(symbol) >= 6 else 'USD',
                'currency_margin': 'USD',
                'digits': digits,
                'point': point,
                'spread': int(base_price * 0.0001 / point),
                'trade_mode': 1,
                'min_lot': 0.01,
                'max_lot': 100.0,
                'lot_step': 0.01,
                'swap_long': -2.5,
                'swap_short': -1.5
            }
            
        except Exception as e:
            logger.error(f"Error getting mock symbol info for {symbol}: {e}")
            return None
    
    async def collect_and_store_data(self, symbol: str, timeframe: str = "M1", count: int = 1000):
        """Collect and store mock market data"""
        try:
            # Get OHLCV data
            ohlcv_data = await self.get_ohlcv_data(symbol, timeframe, count)
            
            if not ohlcv_data:
                logger.warning(f"No mock data to store for {symbol}")
                return
            
            # Convert to MarketData objects
            data_to_store = []
            for data_point in ohlcv_data:
                market_data = MarketData(
                    symbol=symbol,
                    timestamp=data_point['timestamp'],
                    open_price=data_point['open'],
                    high_price=data_point['high'],
                    low_price=data_point['low'],
                    close_price=data_point['close'],
                    volume=data_point['volume'],
                    interval=timeframe,
                    source="MockExness"
                )
                data_to_store.append(market_data)
            
            # Store in database
            if data_to_store:
                # Remove duplicates based on symbol and timestamp
                existing_timestamps = set()
                unique_data = []
                
                for data in data_to_store:
                    timestamp_key = f"{data.symbol}_{data.timestamp}"
                    if timestamp_key not in existing_timestamps:
                        existing_timestamps.add(timestamp_key)
                        unique_data.append(data)
                
                self.db.add_all(unique_data)
                self.db.commit()
                
                logger.info(f"Successfully stored {len(unique_data)} mock data points for {symbol}")
            
        except Exception as e:
            logger.error(f"Error collecting and storing mock data for {symbol}: {e}")
            self.db.rollback()
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get mock current price for symbol"""
        try:
            base_price = self.base_prices.get(symbol, 100.0)
            current_price = self._generate_realistic_price_movement(base_price, 0.001)
            
            spread = base_price * 0.0001
            bid = current_price - spread / 2
            ask = current_price + spread / 2
            
            return {
                'symbol': symbol,
                'price': round(current_price, 5),
                'bid': round(bid, 5),
                'ask': round(ask, 5),
                'last': round(current_price, 5),
                'spread': round(ask - bid, 5),
                'timestamp': datetime.now(),
                'source': 'Mock Exness'
            }
            
        except Exception as e:
            logger.error(f"Error getting mock current price for {symbol}: {e}")
            return None
    
    async def get_market_depth(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate mock market depth data"""
        try:
            base_price = self.base_prices.get(symbol, 100.0)
            current_price = self._generate_realistic_price_movement(base_price, 0.001)
            
            # Generate mock order book
            bids = []
            asks = []
            
            spread = base_price * 0.0001
            
            # Generate 5 levels of bids and asks
            for i in range(5):
                bid_price = current_price - spread * (i + 1)
                ask_price = current_price + spread * (i + 1)
                
                bid_volume = random.uniform(0.1, 10.0)
                ask_volume = random.uniform(0.1, 10.0)
                
                bids.append({
                    'price': round(bid_price, 5),
                    'volume': round(bid_volume, 2)
                })
                
                asks.append({
                    'price': round(ask_price, 5),
                    'volume': round(ask_volume, 2)
                })
            
            return {
                'symbol': symbol,
                'bids': bids,
                'asks': asks,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting mock market depth for {symbol}: {e}")
            return None

# Example usage
async def main():
    """Test the mock Exness data service"""
    from app.models.database import SessionLocal
    
    db = SessionLocal()
    mock_service = MockExnessDataService(db)
    
    try:
        # Test getting current price
        price = await mock_service.get_current_price("XAUUSD")
        print(f"Mock XAUUSD price: {price}")
        
        # Test getting OHLCV data
        ohlcv = await mock_service.get_ohlcv_data("XAUUSD", "M1", 10)
        print(f"Mock OHLCV data points: {len(ohlcv)}")
        
        # Test collecting and storing data
        await mock_service.collect_and_store_data("XAUUSD", "M1", 50)
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


    
    def test_connection(self) -> bool:
        """Test mock connection (always returns True)"""
        return True
    
    def get_intraday_data(self, symbol: str, interval: str = '5min') -> Optional[pd.DataFrame]:
        """Generate mock intraday data"""
        try:
            base_price = self.base_prices.get(symbol, 100.0)
            
            # Generate 100 data points
            data_points = []
            current_time = datetime.now()
            
            for i in range(100):
                timestamp = current_time - timedelta(minutes=5 * (100 - i))
                
                # Generate OHLCV data
                open_price = self._generate_realistic_price_movement(base_price, 0.002)
                high_price = open_price + random.uniform(0, base_price * 0.001)
                low_price = open_price - random.uniform(0, base_price * 0.001)
                close_price = random.uniform(low_price, high_price)
                volume = random.randint(100, 1000)
                
                data_points.append({
                    'timestamp': timestamp,
                    'open': round(open_price, 5),
                    'high': round(high_price, 5),
                    'low': round(low_price, 5),
                    'close': round(close_price, 5),
                    'volume': volume
                })
            
            df = pd.DataFrame(data_points)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"Generated {len(df)} mock intraday data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error generating mock intraday data for {symbol}: {e}")
            return None
    
    def get_daily_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Generate mock daily data"""
        try:
            base_price = self.base_prices.get(symbol, 100.0)
            
            # Generate 30 days of data
            data_points = []
            current_date = datetime.now().date()
            
            for i in range(30):
                date = current_date - timedelta(days=30 - i)
                timestamp = datetime.combine(date, datetime.min.time())
                
                # Generate OHLCV data
                open_price = self._generate_realistic_price_movement(base_price, 0.01)
                high_price = open_price + random.uniform(0, base_price * 0.02)
                low_price = open_price - random.uniform(0, base_price * 0.02)
                close_price = random.uniform(low_price, high_price)
                volume = random.randint(10000, 100000)
                
                data_points.append({
                    'timestamp': timestamp,
                    'open': round(open_price, 5),
                    'high': round(high_price, 5),
                    'low': round(low_price, 5),
                    'close': round(close_price, 5),
                    'volume': volume
                })
            
            df = pd.DataFrame(data_points)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error generating mock daily data for {symbol}: {e}")
            return None
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return list(self.symbol_mapping.keys())

