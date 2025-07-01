"""
Alpha Vantage Data Service for HOT SHARK Bot
Safe alternative to Exness for price data
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import logging
from sqlalchemy.orm import Session

from app.config import Config
from app.models.market_data import MarketData

logger = logging.getLogger(__name__)

class AlphaVantageService:
    """
    Alpha Vantage data service - safe alternative to Exness
    Free tier: 25 API calls per day
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.api_key = getattr(Config, 'ALPHA_VANTAGE_API_KEY', 'demo')
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12  # 5 calls per minute = 12 seconds between calls
        self.last_call_time = 0
        
        # Symbol mapping for Alpha Vantage
        self.symbol_mapping = {
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD', 
            'USDJPY': 'USD/JPY',
            'GBPJPY': 'GBP/JPY',
            'XAUUSD': 'XAU/USD',
            'BTCUSD': 'BTC/USD',
            'ETHUSD': 'ETH/USD'
        }
        
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
            
        self.last_call_time = time.time()
    
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make API request with rate limiting"""
        try:
            self._rate_limit()
            
            params['apikey'] = self.api_key
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
                
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note: {data['Note']}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def get_forex_intraday(self, symbol: str, interval: str = '5min') -> Optional[pd.DataFrame]:
        """
        Get intraday forex data
        
        Args:
            symbol: Currency pair (e.g., 'EURUSD')
            interval: Time interval ('1min', '5min', '15min', '30min', '60min')
        """
        try:
            # Map symbol to Alpha Vantage format
            av_symbol = self.symbol_mapping.get(symbol, symbol)
            from_currency, to_currency = av_symbol.split('/')
            
            params = {
                'function': 'FX_INTRADAY',
                'from_symbol': from_currency,
                'to_symbol': to_currency,
                'interval': interval,
                'outputsize': 'compact'  # Last 100 data points
            }
            
            data = self._make_request(params)
            if not data:
                return None
                
            # Parse time series data
            time_series_key = f'Time Series FX ({interval})'
            if time_series_key not in data:
                logger.error(f"No time series data found for {symbol}")
                return None
                
            time_series = data[time_series_key]
            
            # Convert to DataFrame
            df_data = []
            for timestamp, values in time_series.items():
                df_data.append({
                    'timestamp': pd.to_datetime(timestamp),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': 1000  # Alpha Vantage doesn't provide forex volume
                })
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"Retrieved {len(df)} data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting forex intraday data for {symbol}: {e}")
            return None
    
    def get_forex_daily(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get daily forex data"""
        try:
            av_symbol = self.symbol_mapping.get(symbol, symbol)
            from_currency, to_currency = av_symbol.split('/')
            
            params = {
                'function': 'FX_DAILY',
                'from_symbol': from_currency,
                'to_symbol': to_currency,
                'outputsize': 'compact'
            }
            
            data = self._make_request(params)
            if not data:
                return None
                
            time_series = data.get('Time Series FX (Daily)', {})
            
            df_data = []
            for date, values in time_series.items():
                df_data.append({
                    'timestamp': pd.to_datetime(date),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': 1000
                })
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting forex daily data for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current exchange rate"""
        try:
            av_symbol = self.symbol_mapping.get(symbol, symbol)
            from_currency, to_currency = av_symbol.split('/')
            
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': from_currency,
                'to_currency': to_currency
            }
            
            data = self._make_request(params)
            if not data:
                return None
                
            exchange_rate = data.get('Realtime Currency Exchange Rate', {})
            
            if not exchange_rate:
                logger.error(f"No exchange rate data found for {symbol}")
                return None
            
            current_price = float(exchange_rate['5. Exchange Rate'])
            
            return {
                'symbol': symbol,
                'price': current_price,
                'bid': current_price * 0.9999,  # Approximate bid
                'ask': current_price * 1.0001,  # Approximate ask
                'timestamp': datetime.now(),
                'source': 'Alpha Vantage'
            }
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_crypto_intraday(self, symbol: str, interval: str = '5min') -> Optional[pd.DataFrame]:
        """Get cryptocurrency intraday data"""
        try:
            # Extract crypto symbol (e.g., BTC from BTCUSD)
            crypto_symbol = symbol.replace('USD', '')
            
            params = {
                'function': 'CRYPTO_INTRADAY',
                'symbol': crypto_symbol,
                'market': 'USD',
                'interval': interval,
                'outputsize': 'compact'
            }
            
            data = self._make_request(params)
            if not data:
                return None
                
            time_series_key = f'Time Series Crypto ({interval})'
            if time_series_key not in data:
                logger.error(f"No crypto time series data found for {symbol}")
                return None
                
            time_series = data[time_series_key]
            
            df_data = []
            for timestamp, values in time_series.items():
                df_data.append({
                    'timestamp': pd.to_datetime(timestamp),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': float(values['5. volume'])
                })
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting crypto intraday data for {symbol}: {e}")
            return None
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return list(self.symbol_mapping.keys())
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Test with a simple currency exchange rate call
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': 'EUR',
                'to_currency': 'USD'
            }
            
            data = self._make_request(params)
            return data is not None and 'Realtime Currency Exchange Rate' in data
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_api_usage_info(self) -> Dict:
        """Get API usage information"""
        return {
            'provider': 'Alpha Vantage',
            'free_tier_limit': '25 calls per day',
            'rate_limit': '5 calls per minute',
            'supported_assets': ['Forex', 'Crypto', 'Stocks'],
            'data_quality': 'High',
            'historical_data': '20+ years',
            'real_time': 'Yes (with delay)',
            'cost': 'Free tier available'
        }
    
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
                    source='Alpha Vantage'
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

