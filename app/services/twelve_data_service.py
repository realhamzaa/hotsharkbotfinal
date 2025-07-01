"""
Twelve Data Service for HOT SHARK Bot
Free tier: 8 API calls per minute, 800 per day
High quality financial data
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import logging
from sqlalchemy.orm import Session

from app.config import Config
from app.models.market_data import MarketData

logger = logging.getLogger(__name__)

class TwelveDataService:
    """
    Twelve Data service - free tier with good limits
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://api.twelvedata.com"
        self.api_key = getattr(Config, 'TWELVE_DATA_API_KEY', 'demo')
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 7.5  # 8 requests per minute = 7.5 seconds between requests
        
        # Symbol mapping
        self.symbol_mapping = {
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD',
            'USDJPY': 'USD/JPY',
            'GBPJPY': 'GBP/JPY',
            'XAUUSD': 'XAU/USD',
            'BTCUSD': 'BTC/USD',
            'ETHUSD': 'ETH/USD',
            'US30': 'DJI',
            'US100': 'IXIC'
        }
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_twelve_symbol(self, symbol: str) -> str:
        """Get Twelve Data symbol"""
        return self.symbol_mapping.get(symbol, symbol)
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make rate-limited request to Twelve Data API"""
        try:
            self._rate_limit()
            
            params['apikey'] = self.api_key
            url = f"{self.base_url}/{endpoint}"
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API errors
                if 'error' in data:
                    logger.error(f"Twelve Data API error: {data['error']}")
                    return None
                
                return data
            else:
                logger.error(f"HTTP error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current price from Twelve Data"""
        try:
            twelve_symbol = self._get_twelve_symbol(symbol)
            
            # Get real-time quote
            params = {
                'symbol': twelve_symbol,
                'interval': '1min',
                'outputsize': 1
            }
            
            data = self._make_request('time_series', params)
            
            if not data or 'values' not in data:
                logger.warning(f"No price data for {symbol}")
                return None
            
            values = data['values']
            if not values:
                return None
            
            latest = values[0]
            current_price = float(latest['close'])
            
            # Calculate approximate spread
            spread_pct = 0.0001 if 'USD' in symbol else 0.001
            spread = current_price * spread_pct
            
            return {
                'symbol': symbol,
                'price': current_price,
                'bid': current_price - spread/2,
                'ask': current_price + spread/2,
                'last': current_price,
                'spread': spread,
                'timestamp': datetime.now(),
                'source': 'Twelve Data',
                'volume': float(latest.get('volume', 0))
            }
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_intraday_data(self, symbol: str, interval: str = '5min') -> Optional[pd.DataFrame]:
        """Get intraday data from Twelve Data"""
        try:
            twelve_symbol = self._get_twelve_symbol(symbol)
            
            # Map interval
            interval_map = {
                '1min': '1min',
                '5min': '5min',
                '15min': '15min',
                '30min': '30min',
                '60min': '1h'
            }
            td_interval = interval_map.get(interval, '5min')
            
            params = {
                'symbol': twelve_symbol,
                'interval': td_interval,
                'outputsize': 100
            }
            
            data = self._make_request('time_series', params)
            
            if not data or 'values' not in data:
                return None
            
            values = data['values']
            if not values:
                return None
            
            # Convert to DataFrame
            df_data = []
            for item in values:
                df_data.append({
                    'timestamp': datetime.strptime(item['datetime'], '%Y-%m-%d %H:%M:%S'),
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': float(item.get('volume', 0))
                })
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"Retrieved {len(df)} data points for {symbol} from Twelve Data")
            return df
            
        except Exception as e:
            logger.error(f"Error getting intraday data for {symbol}: {e}")
            return None
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return list(self.symbol_mapping.keys())
    
    def test_connection(self) -> bool:
        """Test Twelve Data connection"""
        try:
            params = {
                'symbol': 'EUR/USD',
                'interval': '1min',
                'outputsize': 1
            }
            
            data = self._make_request('time_series', params)
            return data is not None and 'values' in data
            
        except Exception as e:
            logger.error(f"Twelve Data connection test failed: {e}")
            return False
    
    def get_api_usage_info(self) -> Dict:
        """Get API usage information"""
        return {
            'provider': 'Twelve Data',
            'free_tier_limit': '800 calls/day, 8 calls/minute',
            'rate_limit': '8 requests per minute',
            'supported_assets': ['Forex', 'Crypto', 'Stocks', 'Indices'],
            'data_quality': 'High',
            'historical_data': '10+ years',
            'real_time': 'Yes',
            'cost': 'Free tier available'
        }
    
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get multiple quotes (limited by rate limit)"""
        results = {}
        
        for symbol in symbols:
            try:
                price_data = self.get_current_price(symbol)
                if price_data:
                    results[symbol] = price_data
            except Exception as e:
                logger.error(f"Error getting price for {symbol}: {e}")
                continue
        
        return results

