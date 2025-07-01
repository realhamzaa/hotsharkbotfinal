"""
Multi-Source Data Service for HOT SHARK Bot
Manages multiple data sources with automatic fallback
Now includes Yahoo Finance as primary unlimited source
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from sqlalchemy.orm import Session

from app.services.alpha_vantage_service import AlphaVantageService
from app.services.yahoo_finance_service import YahooFinanceService
from app.services.twelve_data_service import TwelveDataService
from app.services.free_market_data_service import FreeMarketDataService
from app.services.mock_exness_service import MockExnessDataService
from app.config import Config

logger = logging.getLogger(__name__)

class MultiSourceDataService:
    """
    Multi-source data service with Yahoo Finance as primary unlimited source
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize all data sources
        self.free_service = FreeMarketDataService(db)  # Primary - unlimited free
        self.twelve_data_service = TwelveDataService(db)
        self.yahoo_service = YahooFinanceService(db)
        self.alpha_vantage_service = AlphaVantageService(db)
        self.mock_service = MockExnessDataService(db)
        
        # Source priority (Free service first - completely unlimited)
        self.source_priority = [
            ('free_market_data', self.free_service),
            ('twelve_data', self.twelve_data_service),
            ('yahoo_finance', self.yahoo_service),
            ('alpha_vantage', self.alpha_vantage_service),
            ('mock_exness', self.mock_service)
        ]
        
        self.current_source = 'free_market_data'
        self.fallback_count = 0
        
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current price with automatic fallback"""
        for source_name, service in self.source_priority:
            try:
                logger.info(f"Trying to get current price for {symbol} from {source_name}")
                
                if source_name == 'yahoo_finance':
                    price_data = service.get_current_price(symbol)
                elif source_name == 'alpha_vantage':
                    price_data = service.get_current_price(symbol)
                else:  # mock_exness
                    price_data = service.get_current_price(symbol)
                
                if price_data:
                    self.current_source = source_name
                    logger.info(f"Successfully got price from {source_name}: {price_data['price']}")
                    return price_data
                    
            except Exception as e:
                logger.warning(f"Failed to get price from {source_name}: {e}")
                continue
        
        logger.error(f"All sources failed for {symbol}")
        return None
    
    def get_intraday_data(self, symbol: str, interval: str = '5min') -> Optional[pd.DataFrame]:
        """Get intraday data with automatic fallback"""
        for source_name, service in self.source_priority:
            try:
                logger.info(f"Trying to get intraday data for {symbol} from {source_name}")
                
                if hasattr(service, 'get_intraday_data'):
                    data = service.get_intraday_data(symbol, interval)
                    
                    if data is not None and not data.empty:
                        self.current_source = source_name
                        logger.info(f"Successfully got {len(data)} data points from {source_name}")
                        return data
                        
            except Exception as e:
                logger.warning(f"Failed to get intraday data from {source_name}: {e}")
                continue
        
        logger.error(f"All sources failed for intraday data: {symbol}")
        return None
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get multiple prices efficiently"""
        try:
            # Try Yahoo Finance first (supports batch requests)
            logger.info(f"Getting multiple prices for {symbols} from Yahoo Finance")
            results = self.yahoo_service.get_multiple_prices(symbols)
            
            if results:
                self.current_source = 'yahoo_finance'
                return results
            
            # Fallback to individual requests
            results = {}
            for symbol in symbols:
                price_data = self.get_current_price(symbol)
                if price_data:
                    results[symbol] = price_data
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting multiple prices: {e}")
            return {}
    
    def get_data_with_volume_analysis(self, symbol: str, interval: str = '5min') -> Optional[Dict]:
        """Get enhanced data with volume analysis"""
        try:
            # Get intraday data
            df = self.get_intraday_data(symbol, interval)
            if df is None or df.empty:
                return None
            
            # Calculate VWAP
            df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
            current_vwap = df['vwap'].iloc[-1]
            
            # Calculate CVD (simplified)
            df['price_change'] = df['close'].diff()
            df['cvd'] = np.where(df['price_change'] > 0, df['volume'], -df['volume']).cumsum()
            current_cvd = df['cvd'].iloc[-1]
            
            # Find volume dots (high volume points)
            volume_threshold = df['volume'].quantile(0.8)
            volume_dots = df[df['volume'] > volume_threshold][['timestamp', 'close', 'volume']].to_dict('records')
            
            # Get current price
            current_price_data = self.get_current_price(symbol)
            current_price = current_price_data['price'] if current_price_data else df['close'].iloc[-1]
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'current_vwap': current_vwap,
                'current_cvd': current_cvd,
                'volume_dots': volume_dots,
                'data_points': len(df),
                'source': self.current_source,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced data for {symbol}: {e}")
            return None
    
    def test_connection(self) -> Dict[str, bool]:
        """Test connection to all sources"""
        results = {}
        
        for source_name, service in self.source_priority:
            try:
                if hasattr(service, 'test_connection'):
                    results[source_name] = service.test_connection()
                else:
                    # Try a simple operation
                    test_result = service.get_current_price('EURUSD')
                    results[source_name] = test_result is not None
                    
            except Exception as e:
                logger.error(f"{source_name} connection test failed: {e}")
                results[source_name] = False
        
        return results
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about current data source"""
        source_info = {
            'current_source': self.current_source,
            'fallback_count': self.fallback_count
        }
        
        if self.current_source == 'free_market_data':
            source_info.update({
                'provider': 'Free Market Data',
                'cost': 'Completely Free',
                'rate_limit': 'Unlimited',
                'data_quality': 'Realistic Simulation',
                'real_time': 'Simulated Real-time',
                'supported_assets': 'All Major Assets',
                'api_key_required': 'No'
            })
        elif self.current_source == 'twelve_data':
            source_info.update({
                'provider': 'Twelve Data',
                'cost': 'Free (800 calls/day)',
                'rate_limit': '8 calls/minute',
                'data_quality': 'High',
                'real_time': 'Yes'
            })
        elif self.current_source == 'yahoo_finance':
            source_info.update({
                'provider': 'Yahoo Finance',
                'cost': 'Free',
                'rate_limit': 'Unlimited',
                'data_quality': 'High',
                'real_time': 'Yes (minimal delay)',
                'supported_assets': 'Forex, Crypto, Stocks, Indices'
            })
        elif self.current_source == 'alpha_vantage':
            source_info.update({
                'provider': 'Alpha Vantage',
                'cost': 'Free (25 calls/day)',
                'rate_limit': '5 calls/minute',
                'data_quality': 'High',
                'real_time': 'Yes'
            })
        else:  # mock_exness
            source_info.update({
                'provider': 'Mock Exness',
                'cost': 'Free',
                'rate_limit': 'Unlimited',
                'data_quality': 'Simulated',
                'real_time': 'Simulated'
            })
        
        return source_info
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        # Return the common symbols supported by all sources
        return ['EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'XAUUSD', 'BTCUSD', 'ETHUSD', 'US30', 'US100']
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        try:
            # Get market hours from Yahoo Finance
            market_info = {}
            symbols = ['EURUSD', 'XAUUSD', 'BTCUSD', 'US30']
            
            for symbol in symbols:
                try:
                    hours = self.yahoo_service.get_market_hours(symbol)
                    if hours:
                        market_info[symbol] = hours
                except Exception as e:
                    logger.warning(f"Could not get market hours for {symbol}: {e}")
            
            return {
                'timestamp': datetime.now(),
                'source': 'Yahoo Finance',
                'markets': market_info,
                'data_source_status': self.get_source_info()
            }
            
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return {}
    
    def get_economic_calendar(self) -> List[Dict]:
        """Get economic calendar events"""
        try:
            return self.yahoo_service.get_economic_calendar()
        except Exception as e:
            logger.error(f"Error getting economic calendar: {e}")
            return []
    
    def force_switch_source(self, source_name: str) -> bool:
        """Force switch to specific source"""
        valid_sources = [name for name, _ in self.source_priority]
        
        if source_name in valid_sources:
            self.current_source = source_name
            logger.info(f"Forced switch to {source_name}")
            return True
        else:
            logger.error(f"Invalid source: {source_name}. Valid sources: {valid_sources}")
            return False
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics for all sources"""
        stats = {
            'primary_source': 'free_market_data',
            'primary_source_status': 'Unlimited Free (No API Key)',
            'fallback_sources': ['twelve_data', 'yahoo_finance', 'alpha_vantage', 'mock_exness'],
            'total_fallbacks': self.fallback_count,
            'current_active_source': self.current_source,
            'last_updated': datetime.now()
        }
        
        # Add source-specific stats
        for source_name, service in self.source_priority:
            if hasattr(service, 'get_api_usage_info'):
                stats[f'{source_name}_info'] = service.get_api_usage_info()
        
        return stats

