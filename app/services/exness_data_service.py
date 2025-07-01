"""
Exness Data Service for HOT SHARK Bot.
Handles fetching real-time and historical market data from Exness via MetaTrader 5.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from sqlalchemy.orm import Session
from app.models.market_data import MarketData
from app.config import Config

logger = logging.getLogger(__name__)

class ExnessDataService:
    """Service for collecting market data from Exness via MetaTrader 5"""
    
    def __init__(self, db: Session):
        self.db = db
        self.mt5_initialized = False
        self.exness_login = getattr(Config, 'EXNESS_LOGIN', None)
        self.exness_password = getattr(Config, 'EXNESS_PASSWORD', None)
        self.exness_server = getattr(Config, 'EXNESS_SERVER', 'Exness-MT5Trial')
        
        # Exness symbol mapping
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
    
    async def initialize_mt5(self) -> bool:
        """Initialize MetaTrader 5 connection"""
        try:
            if not mt5.initialize():
                logger.error("Failed to initialize MetaTrader 5")
                return False
            
            # Login to Exness account if credentials provided
            if self.exness_login and self.exness_password:
                authorized = mt5.login(
                    login=int(self.exness_login),
                    password=self.exness_password,
                    server=self.exness_server
                )
                
                if not authorized:
                    logger.error(f"Failed to login to Exness account: {mt5.last_error()}")
                    return False
                
                logger.info(f"Successfully connected to Exness server: {self.exness_server}")
            
            self.mt5_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False
    
    def shutdown_mt5(self):
        """Shutdown MetaTrader 5 connection"""
        if self.mt5_initialized:
            mt5.shutdown()
            self.mt5_initialized = False
            logger.info("MetaTrader 5 connection closed")
    
    def get_exness_symbol(self, symbol: str) -> str:
        """Convert standard symbol to Exness format"""
        return self.symbol_mapping.get(symbol, symbol)
    
    async def get_tick_data(self, symbol: str, count: int = 1000) -> List[Dict[str, Any]]:
        """Get latest tick data from Exness"""
        if not self.mt5_initialized:
            await self.initialize_mt5()
        
        exness_symbol = self.get_exness_symbol(symbol)
        
        try:
            # Get latest ticks
            ticks = mt5.copy_ticks_from_pos(exness_symbol, 0, count)
            
            if ticks is None or len(ticks) == 0:
                logger.warning(f"No tick data received for {exness_symbol}")
                return []
            
            tick_data = []
            for tick in ticks:
                tick_data.append({
                    'symbol': symbol,
                    'timestamp': datetime.fromtimestamp(tick.time),
                    'bid': float(tick.bid),
                    'ask': float(tick.ask),
                    'last': float(tick.last),
                    'volume': int(tick.volume),
                    'flags': int(tick.flags)
                })
            
            logger.info(f"Retrieved {len(tick_data)} ticks for {symbol} from Exness")
            return tick_data
            
        except Exception as e:
            logger.error(f"Error getting tick data for {symbol}: {e}")
            return []
    
    async def get_ohlcv_data(self, symbol: str, timeframe: str = "M1", count: int = 1000) -> List[Dict[str, Any]]:
        """Get OHLCV data from Exness"""
        if not self.mt5_initialized:
            await self.initialize_mt5()
        
        exness_symbol = self.get_exness_symbol(symbol)
        
        # Convert timeframe to MT5 format
        timeframe_mapping = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        
        mt5_timeframe = timeframe_mapping.get(timeframe, mt5.TIMEFRAME_M1)
        
        try:
            # Get rates data
            rates = mt5.copy_rates_from_pos(exness_symbol, mt5_timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No OHLCV data received for {exness_symbol}")
                return []
            
            ohlcv_data = []
            for rate in rates:
                ohlcv_data.append({
                    'symbol': symbol,
                    'timestamp': datetime.fromtimestamp(rate['time']),
                    'open': float(rate['open']),
                    'high': float(rate['high']),
                    'low': float(rate['low']),
                    'close': float(rate['close']),
                    'volume': int(rate['tick_volume']),
                    'spread': int(rate['spread']),
                    'timeframe': timeframe
                })
            
            logger.info(f"Retrieved {len(ohlcv_data)} OHLCV bars for {symbol} from Exness")
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Error getting OHLCV data for {symbol}: {e}")
            return []
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information from Exness"""
        if not self.mt5_initialized:
            await self.initialize_mt5()
        
        exness_symbol = self.get_exness_symbol(symbol)
        
        try:
            symbol_info = mt5.symbol_info(exness_symbol)
            
            if symbol_info is None:
                logger.warning(f"No symbol info for {exness_symbol}")
                return None
            
            return {
                'symbol': symbol,
                'description': symbol_info.description,
                'currency_base': symbol_info.currency_base,
                'currency_profit': symbol_info.currency_profit,
                'currency_margin': symbol_info.currency_margin,
                'digits': symbol_info.digits,
                'point': symbol_info.point,
                'spread': symbol_info.spread,
                'trade_mode': symbol_info.trade_mode,
                'min_lot': symbol_info.volume_min,
                'max_lot': symbol_info.volume_max,
                'lot_step': symbol_info.volume_step,
                'swap_long': symbol_info.swap_long,
                'swap_short': symbol_info.swap_short
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    async def collect_and_store_data(self, symbol: str, timeframe: str = "M1", count: int = 1000):
        """Collect and store market data from Exness"""
        try:
            # Get OHLCV data
            ohlcv_data = await self.get_ohlcv_data(symbol, timeframe, count)
            
            if not ohlcv_data:
                logger.warning(f"No data to store for {symbol}")
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
                    source="Exness"
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
                
                logger.info(f"Successfully stored {len(unique_data)} data points for {symbol} from Exness")
            
        except Exception as e:
            logger.error(f"Error collecting and storing data for {symbol}: {e}")
            self.db.rollback()
    
    async def get_current_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get current price for symbol from Exness"""
        if not self.mt5_initialized:
            await self.initialize_mt5()
        
        exness_symbol = self.get_exness_symbol(symbol)
        
        try:
            tick = mt5.symbol_info_tick(exness_symbol)
            
            if tick is None:
                logger.warning(f"No current price for {exness_symbol}")
                return None
            
            return {
                'symbol': symbol,
                'bid': float(tick.bid),
                'ask': float(tick.ask),
                'last': float(tick.last),
                'spread': float(tick.ask - tick.bid),
                'timestamp': datetime.fromtimestamp(tick.time)
            }
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    async def get_market_depth(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market depth (DOM) data from Exness"""
        if not self.mt5_initialized:
            await self.initialize_mt5()
        
        exness_symbol = self.get_exness_symbol(symbol)
        
        try:
            # Get market book (depth of market)
            book = mt5.market_book_get(exness_symbol)
            
            if book is None:
                logger.warning(f"No market depth for {exness_symbol}")
                return None
            
            bids = []
            asks = []
            
            for item in book:
                if item.type == mt5.BOOK_TYPE_BUY:
                    bids.append({
                        'price': float(item.price),
                        'volume': float(item.volume)
                    })
                elif item.type == mt5.BOOK_TYPE_SELL:
                    asks.append({
                        'price': float(item.price),
                        'volume': float(item.volume)
                    })
            
            return {
                'symbol': symbol,
                'bids': bids,
                'asks': asks,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting market depth for {symbol}: {e}")
            return None

# Example usage
async def main():
    """Test the Exness data service"""
    from app.models.database import SessionLocal
    
    db = SessionLocal()
    exness_service = ExnessDataService(db)
    
    try:
        # Initialize MT5
        if await exness_service.initialize_mt5():
            # Test getting current price
            price = await exness_service.get_current_price("XAUUSD")
            print(f"Current XAUUSD price: {price}")
            
            # Test getting OHLCV data
            ohlcv = await exness_service.get_ohlcv_data("XAUUSD", "M1", 10)
            print(f"OHLCV data points: {len(ohlcv)}")
            
            # Test collecting and storing data
            await exness_service.collect_and_store_data("XAUUSD", "M1", 100)
            
        else:
            print("Failed to initialize MT5 connection")
            
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        exness_service.shutdown_mt5()
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

