"""
Yahoo Finance Data Service for HOT SHARK Bot
Free unlimited data source alternative
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import logging
from sqlalchemy.orm import Session
import requests
from bs4 import BeautifulSoup

from app.config import Config
from app.models.market_data import MarketData

logger = logging.getLogger(__name__)

class YahooFinanceService:
    """
    Yahoo Finance data service - unlimited free data
    No API limits, real-time data available
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.session = requests.Session()
        
        # Symbol mapping for Yahoo Finance
        self.symbol_mapping = {
            'EURUSD': 'EURUSD=X',
            'GBPUSD': 'GBPUSD=X',
            'USDJPY': 'USDJPY=X',
            'GBPJPY': 'GBPJPY=X',
            'XAUUSD': 'GC=F',  # Gold futures
            'BTCUSD': 'BTC-USD',
            'ETHUSD': 'ETH-USD',
            'US30': '^DJI',    # Dow Jones
            'US100': '^IXIC'   # NASDAQ
        }
        
        # Alternative symbols for better coverage
        self.alt_symbols = {
            'XAUUSD': ['GLD', 'GOLD'],  # Gold ETFs
            'US30': ['^DJI', 'DIA'],
            'US100': ['^IXIC', 'QQQ']
        }
        
    def _get_yahoo_symbol(self, symbol: str) -> str:
        """Get Yahoo Finance symbol"""
        return self.symbol_mapping.get(symbol, symbol)
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current price from Yahoo Finance"""
        try:
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            
            # Use yfinance for real-time data
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            if not info:
                logger.warning(f"No info available for {symbol}")
                return None
            
            # Get current price
            current_price = info.get('regularMarketPrice') or info.get('previousClose')
            
            if not current_price:
                # Try alternative method
                hist = ticker.history(period='1d', interval='1m')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    logger.error(f"No price data available for {symbol}")
                    return None
            
            # Calculate bid/ask spread (approximate)
            spread_pct = 0.0001 if 'USD' in symbol else 0.001
            spread = current_price * spread_pct
            
            return {
                'symbol': symbol,
                'price': float(current_price),
                'bid': float(current_price - spread/2),
                'ask': float(current_price + spread/2),
                'last': float(current_price),
                'spread': float(spread),
                'timestamp': datetime.now(),
                'source': 'Yahoo Finance',
                'volume': info.get('regularMarketVolume', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_intraday_data(self, symbol: str, interval: str = '5m') -> Optional[pd.DataFrame]:
        """
        Get intraday data from Yahoo Finance
        
        Args:
            symbol: Trading symbol
            interval: '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h'
        """
        try:
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            
            # Map interval to Yahoo Finance format
            interval_map = {
                '1min': '1m',
                '5min': '5m',
                '15min': '15m',
                '30min': '30m',
                '60min': '1h'
            }
            yf_interval = interval_map.get(interval, interval)
            
            # Get data for last 7 days with specified interval
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period='7d', interval=yf_interval)
            
            if hist.empty:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            # Convert to standard format
            df = pd.DataFrame()
            df['timestamp'] = hist.index
            df['open'] = hist['Open'].values
            df['high'] = hist['High'].values
            df['low'] = hist['Low'].values
            df['close'] = hist['Close'].values
            df['volume'] = hist['Volume'].values
            
            # Reset index and sort by timestamp
            df = df.reset_index(drop=True)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Remove any NaN values
            df = df.dropna()
            
            logger.info(f"Retrieved {len(df)} data points for {symbol} from Yahoo Finance")
            return df
            
        except Exception as e:
            logger.error(f"Error getting intraday data for {symbol}: {e}")
            return None
    
    def get_daily_data(self, symbol: str, days: int = 100) -> Optional[pd.DataFrame]:
        """Get daily data from Yahoo Finance"""
        try:
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period=f'{days}d', interval='1d')
            
            if hist.empty:
                return None
            
            df = pd.DataFrame()
            df['timestamp'] = hist.index
            df['open'] = hist['Open'].values
            df['high'] = hist['High'].values
            df['low'] = hist['Low'].values
            df['close'] = hist['Close'].values
            df['volume'] = hist['Volume'].values
            
            df = df.reset_index(drop=True)
            df = df.sort_values('timestamp').reset_index(drop=True)
            df = df.dropna()
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting daily data for {symbol}: {e}")
            return None
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return list(self.symbol_mapping.keys())
    
    def test_connection(self) -> bool:
        """Test Yahoo Finance connection"""
        try:
            # Test with a simple symbol
            ticker = yf.Ticker('EURUSD=X')
            info = ticker.info
            return bool(info)
            
        except Exception as e:
            logger.error(f"Yahoo Finance connection test failed: {e}")
            return False
    
    def get_api_usage_info(self) -> Dict:
        """Get API usage information"""
        return {
            'provider': 'Yahoo Finance',
            'free_tier_limit': 'Unlimited',
            'rate_limit': 'None (reasonable use)',
            'supported_assets': ['Forex', 'Crypto', 'Stocks', 'Indices', 'Commodities'],
            'data_quality': 'High',
            'historical_data': '10+ years',
            'real_time': 'Yes (15-20 min delay for some markets)',
            'cost': 'Completely Free'
        }
    
    def get_market_hours(self, symbol: str) -> Dict:
        """Get market hours for symbol"""
        try:
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'market': info.get('market', 'Unknown'),
                'exchange': info.get('exchange', 'Unknown'),
                'timezone': info.get('timeZoneFullName', 'UTC'),
                'is_open': info.get('marketState') == 'REGULAR',
                'next_open': info.get('preMarketTime'),
                'next_close': info.get('postMarketTime')
            }
            
        except Exception as e:
            logger.error(f"Error getting market hours for {symbol}: {e}")
            return {}
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get current prices for multiple symbols efficiently"""
        try:
            yahoo_symbols = [self._get_yahoo_symbol(s) for s in symbols]
            
            # Use yfinance download for multiple symbols
            data = yf.download(yahoo_symbols, period='1d', interval='1m', group_by='ticker')
            
            results = {}
            for i, symbol in enumerate(symbols):
                try:
                    yahoo_symbol = yahoo_symbols[i]
                    
                    if len(symbols) == 1:
                        symbol_data = data
                    else:
                        symbol_data = data[yahoo_symbol]
                    
                    if not symbol_data.empty:
                        latest_price = symbol_data['Close'].iloc[-1]
                        latest_volume = symbol_data['Volume'].iloc[-1] if 'Volume' in symbol_data else 0
                        
                        spread_pct = 0.0001 if 'USD' in symbol else 0.001
                        spread = latest_price * spread_pct
                        
                        results[symbol] = {
                            'symbol': symbol,
                            'price': float(latest_price),
                            'bid': float(latest_price - spread/2),
                            'ask': float(latest_price + spread/2),
                            'volume': float(latest_volume),
                            'timestamp': datetime.now(),
                            'source': 'Yahoo Finance'
                        }
                        
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting multiple prices: {e}")
            return {}
    
    def save_to_database(self, symbol: str, df: pd.DataFrame, timeframe: str):
        """Save market data to database"""
        try:
            for _, row in df.iterrows():
                market_data = MarketData(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=row['timestamp'],
                    open_price=row['open'],
                    high_price=row['high'],
                    low_price=row['low'],
                    close_price=row['close'],
                    volume=row['volume'],
                    source='Yahoo Finance'
                )
                
                # Check if data already exists
                existing = self.db.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timeframe == timeframe,
                    MarketData.timestamp == row['timestamp']
                ).first()
                
                if not existing:
                    self.db.add(market_data)
            
            self.db.commit()
            logger.info(f"Saved {len(df)} data points for {symbol} to database")
            
        except Exception as e:
            logger.error(f"Error saving data to database: {e}")
            self.db.rollback()
    
    def get_economic_calendar(self) -> List[Dict]:
        """Get basic economic calendar events"""
        try:
            # This is a simplified version - you could integrate with a proper economic calendar API
            events = [
                {
                    'time': '09:30',
                    'currency': 'USD',
                    'event': 'Market Open',
                    'impact': 'High',
                    'description': 'US Market Opening'
                },
                {
                    'time': '14:30',
                    'currency': 'EUR',
                    'event': 'London Close',
                    'impact': 'Medium',
                    'description': 'European Market Close'
                }
            ]
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting economic calendar: {e}")
            return []

