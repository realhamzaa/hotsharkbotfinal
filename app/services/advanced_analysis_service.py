"""
Advanced Analysis Service for HOT SHARK Bot.
Implements CVD, VWAP, Volume Dots, and Stop Run analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session
from app.models.market_data import MarketData
from app.services.multi_source_data_service import MultiSourceDataService

logger = logging.getLogger(__name__)

@dataclass
class CVDSignal:
    """Cumulative Volume Delta signal"""
    timestamp: datetime
    cvd_value: float
    trend: str  # 'bullish', 'bearish', 'neutral'
    divergence: bool
    strength: float  # 0-100

@dataclass
class VWAPSignal:
    """VWAP signal"""
    timestamp: datetime
    vwap_value: float
    price_position: str  # 'above', 'below', 'at'
    trend: str  # 'bullish', 'bearish', 'neutral'
    distance_percentage: float

@dataclass
class VolumeDotsSignal:
    """Volume Dots signal"""
    timestamp: datetime
    price_level: float
    volume_intensity: float  # 0-100
    significance: str  # 'high', 'medium', 'low'
    type: str  # 'accumulation', 'distribution', 'neutral'

@dataclass
class StopRunSignal:
    """Stop Run signal"""
    timestamp: datetime
    price_level: float
    direction: str  # 'upward', 'downward'
    liquidity_grabbed: float
    probability: float  # 0-100
    next_target: Optional[float]

class AdvancedAnalysisService:
    """Service for advanced market analysis using CVD, VWAP, Volume Dots, and Stop Runs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_service = MultiSourceDataService(db)
        
    async def calculate_cvd(self, symbol: str, timeframe: str = "M1", periods: int = 100) -> List[CVDSignal]:
        """Calculate Cumulative Volume Delta"""
        try:
            # Get tick data from Exness
            tick_data = await self.exness_service.get_tick_data(symbol, periods * 10)
            
            if not tick_data:
                logger.warning(f"No tick data for CVD calculation: {symbol}")
                return []
            
            # Convert to DataFrame
            df = pd.DataFrame(tick_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate volume delta for each tick
            df['mid_price'] = (df['bid'] + df['ask']) / 2
            df['price_change'] = df['mid_price'].diff()
            
            # Estimate buy/sell volume based on price movement and tick direction
            df['volume_delta'] = np.where(
                df['price_change'] > 0, 
                df['volume'],  # Buying pressure
                np.where(
                    df['price_change'] < 0,
                    -df['volume'],  # Selling pressure
                    0  # No change
                )
            )
            
            # Calculate cumulative volume delta
            df['cvd'] = df['volume_delta'].cumsum()
            
            # Resample to desired timeframe
            df.set_index('timestamp', inplace=True)
            
            timeframe_map = {
                'M1': '1T', 'M5': '5T', 'M15': '15T', 
                'M30': '30T', 'H1': '1H', 'H4': '4H', 'D1': '1D'
            }
            
            resampled = df.resample(timeframe_map.get(timeframe, '1T')).agg({
                'cvd': 'last',
                'mid_price': 'last',
                'volume': 'sum'
            }).dropna()
            
            # Generate CVD signals
            signals = []
            for i in range(1, len(resampled)):
                current_cvd = resampled.iloc[i]['cvd']
                prev_cvd = resampled.iloc[i-1]['cvd']
                current_price = resampled.iloc[i]['mid_price']
                prev_price = resampled.iloc[i-1]['mid_price']
                
                # Determine trend
                cvd_trend = 'bullish' if current_cvd > prev_cvd else 'bearish' if current_cvd < prev_cvd else 'neutral'
                
                # Check for divergence
                price_direction = 'up' if current_price > prev_price else 'down' if current_price < prev_price else 'flat'
                cvd_direction = 'up' if current_cvd > prev_cvd else 'down' if current_cvd < prev_cvd else 'flat'
                
                divergence = (price_direction == 'up' and cvd_direction == 'down') or \
                           (price_direction == 'down' and cvd_direction == 'up')
                
                # Calculate strength (0-100)
                cvd_change = abs(current_cvd - prev_cvd)
                max_cvd_change = resampled['cvd'].diff().abs().max()
                strength = min(100, (cvd_change / max_cvd_change * 100)) if max_cvd_change > 0 else 0
                
                signal = CVDSignal(
                    timestamp=resampled.index[i],
                    cvd_value=current_cvd,
                    trend=cvd_trend,
                    divergence=divergence,
                    strength=strength
                )
                signals.append(signal)
            
            logger.info(f"Generated {len(signals)} CVD signals for {symbol}")
            return signals[-periods:] if len(signals) > periods else signals
            
        except Exception as e:
            logger.error(f"Error calculating CVD for {symbol}: {e}")
            return []
    
    async def calculate_vwap(self, symbol: str, timeframe: str = "M1", periods: int = 100) -> List[VWAPSignal]:
        """Calculate Volume Weighted Average Price"""
        try:
            # Get OHLCV data from Exness
            ohlcv_data = await self.exness_service.get_ohlcv_data(symbol, timeframe, periods)
            
            if not ohlcv_data:
                logger.warning(f"No OHLCV data for VWAP calculation: {symbol}")
                return []
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate typical price
            df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
            
            # Calculate VWAP
            df['price_volume'] = df['typical_price'] * df['volume']
            df['cumulative_pv'] = df['price_volume'].cumsum()
            df['cumulative_volume'] = df['volume'].cumsum()
            df['vwap'] = df['cumulative_pv'] / df['cumulative_volume']
            
            # Generate VWAP signals
            signals = []
            for i, row in df.iterrows():
                current_price = row['close']
                vwap_value = row['vwap']
                
                # Determine price position relative to VWAP
                if current_price > vwap_value * 1.001:  # 0.1% threshold
                    position = 'above'
                    trend = 'bullish'
                elif current_price < vwap_value * 0.999:  # 0.1% threshold
                    position = 'below'
                    trend = 'bearish'
                else:
                    position = 'at'
                    trend = 'neutral'
                
                # Calculate distance percentage
                distance_percentage = ((current_price - vwap_value) / vwap_value) * 100
                
                signal = VWAPSignal(
                    timestamp=row['timestamp'],
                    vwap_value=vwap_value,
                    price_position=position,
                    trend=trend,
                    distance_percentage=distance_percentage
                )
                signals.append(signal)
            
            logger.info(f"Generated {len(signals)} VWAP signals for {symbol}")
            return signals
            
        except Exception as e:
            logger.error(f"Error calculating VWAP for {symbol}: {e}")
            return []
    
    async def analyze_volume_dots(self, symbol: str, timeframe: str = "M1", periods: int = 100) -> List[VolumeDotsSignal]:
        """Analyze Volume Dots (high volume price levels)"""
        try:
            # Get OHLCV data from Exness
            ohlcv_data = await self.exness_service.get_ohlcv_data(symbol, timeframe, periods)
            
            if not ohlcv_data:
                logger.warning(f"No OHLCV data for Volume Dots analysis: {symbol}")
                return []
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate volume statistics
            volume_mean = df['volume'].mean()
            volume_std = df['volume'].std()
            volume_threshold_high = volume_mean + (2 * volume_std)
            volume_threshold_medium = volume_mean + volume_std
            
            # Identify significant volume levels
            signals = []
            for i, row in df.iterrows():
                volume = row['volume']
                
                if volume >= volume_threshold_high:
                    significance = 'high'
                    intensity = min(100, ((volume - volume_mean) / volume_std) * 20)
                elif volume >= volume_threshold_medium:
                    significance = 'medium'
                    intensity = min(100, ((volume - volume_mean) / volume_std) * 15)
                else:
                    continue  # Skip low volume periods
                
                # Determine type based on price action
                price_range = row['high'] - row['low']
                close_position = (row['close'] - row['low']) / price_range if price_range > 0 else 0.5
                
                if close_position > 0.7:
                    volume_type = 'accumulation'
                elif close_position < 0.3:
                    volume_type = 'distribution'
                else:
                    volume_type = 'neutral'
                
                # Use typical price as the significant level
                price_level = (row['high'] + row['low'] + row['close']) / 3
                
                signal = VolumeDotsSignal(
                    timestamp=row['timestamp'],
                    price_level=price_level,
                    volume_intensity=intensity,
                    significance=significance,
                    type=volume_type
                )
                signals.append(signal)
            
            logger.info(f"Generated {len(signals)} Volume Dots signals for {symbol}")
            return signals
            
        except Exception as e:
            logger.error(f"Error analyzing Volume Dots for {symbol}: {e}")
            return []
    
    async def detect_stop_runs(self, symbol: str, timeframe: str = "M1", periods: int = 100) -> List[StopRunSignal]:
        """Detect Stop Runs (liquidity grabs)"""
        try:
            # Get OHLCV data from Exness
            ohlcv_data = await self.exness_service.get_ohlcv_data(symbol, timeframe, periods)
            
            if not ohlcv_data:
                logger.warning(f"No OHLCV data for Stop Run detection: {symbol}")
                return []
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate swing highs and lows
            window = 5  # Look for swings in 5-period windows
            df['swing_high'] = df['high'].rolling(window=window, center=True).max() == df['high']
            df['swing_low'] = df['low'].rolling(window=window, center=True).min() == df['low']
            
            # Identify potential stop run levels
            swing_highs = df[df['swing_high']]['high'].tolist()
            swing_lows = df[df['swing_low']]['low'].tolist()
            
            signals = []
            
            # Check for stop runs above swing highs
            for i in range(window, len(df)):
                current_high = df.iloc[i]['high']
                current_low = df.iloc[i]['low']
                current_close = df.iloc[i]['close']
                current_volume = df.iloc[i]['volume']
                timestamp = df.iloc[i]['timestamp']
                
                # Check for upward stop run (above recent swing high)
                recent_swing_highs = [h for h in swing_highs if h < current_high]
                if recent_swing_highs:
                    nearest_high = max(recent_swing_highs)
                    if current_high > nearest_high and current_close < nearest_high:
                        # Potential stop run detected
                        liquidity_grabbed = current_volume
                        probability = min(100, (current_high - nearest_high) / nearest_high * 1000)
                        
                        # Calculate next potential target
                        higher_levels = [h for h in swing_highs if h > current_high]
                        next_target = min(higher_levels) if higher_levels else None
                        
                        signal = StopRunSignal(
                            timestamp=timestamp,
                            price_level=current_high,
                            direction='upward',
                            liquidity_grabbed=liquidity_grabbed,
                            probability=probability,
                            next_target=next_target
                        )
                        signals.append(signal)
                
                # Check for downward stop run (below recent swing low)
                recent_swing_lows = [l for l in swing_lows if l > current_low]
                if recent_swing_lows:
                    nearest_low = min(recent_swing_lows)
                    if current_low < nearest_low and current_close > nearest_low:
                        # Potential stop run detected
                        liquidity_grabbed = current_volume
                        probability = min(100, (nearest_low - current_low) / nearest_low * 1000)
                        
                        # Calculate next potential target
                        lower_levels = [l for l in swing_lows if l < current_low]
                        next_target = max(lower_levels) if lower_levels else None
                        
                        signal = StopRunSignal(
                            timestamp=timestamp,
                            price_level=current_low,
                            direction='downward',
                            liquidity_grabbed=liquidity_grabbed,
                            probability=probability,
                            next_target=next_target
                        )
                        signals.append(signal)
            
            logger.info(f"Generated {len(signals)} Stop Run signals for {symbol}")
            return signals
            
        except Exception as e:
            logger.error(f"Error detecting Stop Runs for {symbol}: {e}")
            return []
    
    async def get_comprehensive_analysis(self, symbol: str, timeframe: str = "M1", periods: int = 100) -> Dict[str, Any]:
        """Get comprehensive analysis combining all indicators"""
        try:
            # Run all analyses in parallel
            cvd_signals = await self.calculate_cvd(symbol, timeframe, periods)
            vwap_signals = await self.calculate_vwap(symbol, timeframe, periods)
            volume_dots_signals = await self.analyze_volume_dots(symbol, timeframe, periods)
            stop_run_signals = await self.detect_stop_runs(symbol, timeframe, periods)
            
            # Get current market data
            current_price = await self.exness_service.get_current_price(symbol)
            
            # Combine analysis results
            analysis = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now(),
                'current_price': current_price,
                'cvd_analysis': {
                    'signals': cvd_signals,
                    'latest_trend': cvd_signals[-1].trend if cvd_signals else 'neutral',
                    'divergence_detected': any(s.divergence for s in cvd_signals[-5:]) if cvd_signals else False,
                    'average_strength': np.mean([s.strength for s in cvd_signals[-10:]]) if cvd_signals else 0
                },
                'vwap_analysis': {
                    'signals': vwap_signals,
                    'current_position': vwap_signals[-1].price_position if vwap_signals else 'unknown',
                    'current_trend': vwap_signals[-1].trend if vwap_signals else 'neutral',
                    'distance_from_vwap': vwap_signals[-1].distance_percentage if vwap_signals else 0
                },
                'volume_dots_analysis': {
                    'signals': volume_dots_signals,
                    'high_volume_levels': [s.price_level for s in volume_dots_signals if s.significance == 'high'],
                    'accumulation_levels': [s.price_level for s in volume_dots_signals if s.type == 'accumulation'],
                    'distribution_levels': [s.price_level for s in volume_dots_signals if s.type == 'distribution']
                },
                'stop_run_analysis': {
                    'signals': stop_run_signals,
                    'recent_stop_runs': stop_run_signals[-5:] if stop_run_signals else [],
                    'upward_targets': [s.next_target for s in stop_run_signals if s.direction == 'upward' and s.next_target],
                    'downward_targets': [s.next_target for s in stop_run_signals if s.direction == 'downward' and s.next_target]
                }
            }
            
            # Generate overall market sentiment
            sentiment_score = 0
            sentiment_factors = []
            
            # CVD sentiment
            if cvd_signals:
                latest_cvd = cvd_signals[-1]
                if latest_cvd.trend == 'bullish':
                    sentiment_score += latest_cvd.strength / 100 * 25
                    sentiment_factors.append(f"CVD bullish ({latest_cvd.strength:.1f}%)")
                elif latest_cvd.trend == 'bearish':
                    sentiment_score -= latest_cvd.strength / 100 * 25
                    sentiment_factors.append(f"CVD bearish ({latest_cvd.strength:.1f}%)")
            
            # VWAP sentiment
            if vwap_signals:
                latest_vwap = vwap_signals[-1]
                if latest_vwap.trend == 'bullish':
                    sentiment_score += 25
                    sentiment_factors.append(f"Price above VWAP ({latest_vwap.distance_percentage:.2f}%)")
                elif latest_vwap.trend == 'bearish':
                    sentiment_score -= 25
                    sentiment_factors.append(f"Price below VWAP ({latest_vwap.distance_percentage:.2f}%)")
            
            # Volume sentiment
            if volume_dots_signals:
                recent_accumulation = len([s for s in volume_dots_signals[-10:] if s.type == 'accumulation'])
                recent_distribution = len([s for s in volume_dots_signals[-10:] if s.type == 'distribution'])
                
                if recent_accumulation > recent_distribution:
                    sentiment_score += 25
                    sentiment_factors.append(f"Volume accumulation detected")
                elif recent_distribution > recent_accumulation:
                    sentiment_score -= 25
                    sentiment_factors.append(f"Volume distribution detected")
            
            # Stop run sentiment
            if stop_run_signals:
                recent_upward_runs = len([s for s in stop_run_signals[-5:] if s.direction == 'upward'])
                recent_downward_runs = len([s for s in stop_run_signals[-5:] if s.direction == 'downward'])
                
                if recent_upward_runs > recent_downward_runs:
                    sentiment_score += 25
                    sentiment_factors.append(f"Upward liquidity grabs")
                elif recent_downward_runs > recent_upward_runs:
                    sentiment_score -= 25
                    sentiment_factors.append(f"Downward liquidity grabs")
            
            # Determine overall sentiment
            if sentiment_score > 50:
                overall_sentiment = 'strongly_bullish'
            elif sentiment_score > 25:
                overall_sentiment = 'bullish'
            elif sentiment_score > -25:
                overall_sentiment = 'neutral'
            elif sentiment_score > -50:
                overall_sentiment = 'bearish'
            else:
                overall_sentiment = 'strongly_bearish'
            
            analysis['overall_sentiment'] = {
                'sentiment': overall_sentiment,
                'score': sentiment_score,
                'factors': sentiment_factors,
                'confidence': min(100, abs(sentiment_score))
            }
            
            logger.info(f"Comprehensive analysis completed for {symbol}: {overall_sentiment} ({sentiment_score:.1f})")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now()
            }

# Example usage
async def main():
    """Test the advanced analysis service"""
    from app.models.database import SessionLocal
    
    db = SessionLocal()
    analysis_service = AdvancedAnalysisService(db)
    
    try:
        # Test comprehensive analysis
        result = await analysis_service.get_comprehensive_analysis("XAUUSD", "M5", 50)
        print(f"Analysis result: {result['overall_sentiment']}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

