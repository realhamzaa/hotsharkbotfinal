"""
ICT/SMC Analyzer Service for HOT SHARK Bot.
Identifies ICT/SMC concepts (e.g., Order Blocks, Liquidity, FVG) from market data.
Enhanced with CVD, VWAP, Volume Dots, and Stop Run analysis.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.services.advanced_analysis_service import AdvancedAnalysisService

logger = logging.getLogger(__name__)

class ICTSMCAnalyzerService:
    def __init__(self, db_session=None):
        self.advanced_analysis = AdvancedAnalysisService(db_session) if db_session else None

    def identify_order_blocks(self, df: pd.DataFrame, lookback_period: int = 5) -> pd.DataFrame:
        """Identifies potential bullish and bearish order blocks.
        Enhanced with volume analysis for better accuracy.
        """
        df["is_bullish_ob"] = False
        df["is_bearish_ob"] = False
        df["ob_strength"] = 0.0

        for i in range(lookback_period, len(df)):
            # Bullish Order Block: Last down candle before an impulsive move up
            if df["close_price"].iloc[i-1] < df["open_price"].iloc[i-1]: # Previous candle is bearish
                # Check for strong move up with volume confirmation
                future_close_avg = df["close_price"].iloc[i:i+lookback_period].mean()
                volume_avg = df["volume"].iloc[i:i+lookback_period].mean()
                prev_volume_avg = df["volume"].iloc[i-lookback_period:i].mean()
                
                if (future_close_avg > df["open_price"].iloc[i-1] * 1.005 and 
                    volume_avg > prev_volume_avg * 1.2): # Volume confirmation
                    df.loc[df.index[i-1], "is_bullish_ob"] = True
                    # Calculate strength based on price move and volume
                    price_strength = (future_close_avg - df["open_price"].iloc[i-1]) / df["open_price"].iloc[i-1]
                    volume_strength = volume_avg / prev_volume_avg if prev_volume_avg > 0 else 1
                    df.loc[df.index[i-1], "ob_strength"] = min(100, price_strength * volume_strength * 1000)
            
            # Bearish Order Block: Last up candle before an impulsive move down
            if df["close_price"].iloc[i-1] > df["open_price"].iloc[i-1]: # Previous candle is bullish
                # Check for strong move down with volume confirmation
                future_close_avg = df["close_price"].iloc[i:i+lookback_period].mean()
                volume_avg = df["volume"].iloc[i:i+lookback_period].mean()
                prev_volume_avg = df["volume"].iloc[i-lookback_period:i].mean()
                
                if (future_close_avg < df["open_price"].iloc[i-1] * 0.995 and 
                    volume_avg > prev_volume_avg * 1.2): # Volume confirmation
                    df.loc[df.index[i-1], "is_bearish_ob"] = True
                    # Calculate strength based on price move and volume
                    price_strength = (df["open_price"].iloc[i-1] - future_close_avg) / df["open_price"].iloc[i-1]
                    volume_strength = volume_avg / prev_volume_avg if prev_volume_avg > 0 else 1
                    df.loc[df.index[i-1], "ob_strength"] = min(100, price_strength * volume_strength * 1000)
        
        return df

    def identify_liquidity_zones(self, df: pd.DataFrame, range_percent: float = 0.001) -> pd.DataFrame:
        """Identifies potential liquidity zones with enhanced stop run detection.
        """
        df["is_liquidity_zone"] = False
        df["liquidity_type"] = ""
        df["liquidity_strength"] = 0.0
        
        # Identify swing highs/lows with volume analysis
        window = 5
        df["swing_high"] = df["high_price"].rolling(window=window, center=True).max()
        df["swing_low"] = df["low_price"].rolling(window=window, center=True).min()
        df["volume_at_swing"] = df["volume"].rolling(window=window, center=True).mean()

        # Enhanced liquidity zone identification
        for i in range(window, len(df) - window):
            current_high = df["high_price"].iloc[i]
            current_low = df["low_price"].iloc[i]
            current_volume = df["volume"].iloc[i]
            avg_volume = df["volume"].iloc[i-window:i+window].mean()
            
            # Check for swing high with volume
            if (current_high == df["swing_high"].iloc[i] and 
                current_volume > avg_volume * 1.5):
                df.loc[df.index[i], "is_liquidity_zone"] = True
                df.loc[df.index[i], "liquidity_type"] = "resistance"
                df.loc[df.index[i], "liquidity_strength"] = min(100, (current_volume / avg_volume) * 20)
            
            # Check for swing low with volume
            if (current_low == df["swing_low"].iloc[i] and 
                current_volume > avg_volume * 1.5):
                df.loc[df.index[i], "is_liquidity_zone"] = True
                df.loc[df.index[i], "liquidity_type"] = "support"
                df.loc[df.index[i], "liquidity_strength"] = min(100, (current_volume / avg_volume) * 20)
            
            # Check for equal highs/lows (potential stop run areas)
            tolerance = current_high * range_percent
            
            # Look for equal highs in recent data
            recent_highs = df["high_price"].iloc[max(0, i-20):i]
            equal_highs = recent_highs[(recent_highs >= current_high - tolerance) & 
                                     (recent_highs <= current_high + tolerance)]
            
            if len(equal_highs) >= 2:
                df.loc[df.index[i], "is_liquidity_zone"] = True
                df.loc[df.index[i], "liquidity_type"] = "equal_highs"
                df.loc[df.index[i], "liquidity_strength"] = min(100, len(equal_highs) * 25)
            
            # Look for equal lows in recent data
            recent_lows = df["low_price"].iloc[max(0, i-20):i]
            equal_lows = recent_lows[(recent_lows >= current_low - tolerance) & 
                                   (recent_lows <= current_low + tolerance)]
            
            if len(equal_lows) >= 2:
                df.loc[df.index[i], "is_liquidity_zone"] = True
                df.loc[df.index[i], "liquidity_type"] = "equal_lows"
                df.loc[df.index[i], "liquidity_strength"] = min(100, len(equal_lows) * 25)
        
        return df

    def identify_fair_value_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identifies Fair Value Gaps (FVG) with enhanced volume analysis.
        """
        df["is_fvg"] = False
        df["fvg_type"] = ""
        df["fvg_strength"] = 0.0
        df["fvg_top"] = 0.0
        df["fvg_bottom"] = 0.0

        for i in range(2, len(df)):
            # Bullish FVG: Gap between candle[i-2].low and candle[i].high, with candle[i-1] not filling it
            prev2_low = df["low_price"].iloc[i-2]
            current_high = df["high_price"].iloc[i]
            prev1_low = df["low_price"].iloc[i-1]
            prev1_high = df["high_price"].iloc[i-1]
            
            # Volume analysis for FVG strength
            volume_surge = df["volume"].iloc[i] > df["volume"].iloc[i-5:i].mean() * 1.5
            
            # Bullish FVG
            if (prev2_low > current_high and 
                prev1_low > current_high and 
                prev1_high > current_high):
                df.loc[df.index[i], "is_fvg"] = True
                df.loc[df.index[i], "fvg_type"] = "bullish"
                df.loc[df.index[i], "fvg_top"] = prev2_low
                df.loc[df.index[i], "fvg_bottom"] = current_high
                
                # Calculate strength based on gap size and volume
                gap_size = (prev2_low - current_high) / current_high
                strength = gap_size * 1000
                if volume_surge:
                    strength *= 1.5
                df.loc[df.index[i], "fvg_strength"] = min(100, strength)

            # Bearish FVG: Gap between candle[i-2].high and candle[i].low, with candle[i-1] not filling it
            prev2_high = df["high_price"].iloc[i-2]
            current_low = df["low_price"].iloc[i]
            
            if (prev2_high < current_low and 
                prev1_high < current_low and 
                prev1_low < current_low):
                df.loc[df.index[i], "is_fvg"] = True
                df.loc[df.index[i], "fvg_type"] = "bearish"
                df.loc[df.index[i], "fvg_top"] = current_low
                df.loc[df.index[i], "fvg_bottom"] = prev2_high
                
                # Calculate strength based on gap size and volume
                gap_size = (current_low - prev2_high) / prev2_high
                strength = gap_size * 1000
                if volume_surge:
                    strength *= 1.5
                df.loc[df.index[i], "fvg_strength"] = min(100, strength)

        return df

    def identify_break_of_structure(self, df: pd.DataFrame, lookback: int = 10) -> pd.DataFrame:
        """Identifies Break of Structure (BOS) with volume confirmation.
        """
        df["is_bos"] = False
        df["bos_type"] = ""
        df["bos_strength"] = 0.0

        # Calculate swing highs and lows
        df["swing_high"] = df["high_price"].rolling(window=lookback, center=True).max()
        df["swing_low"] = df["low_price"].rolling(window=lookback, center=True).min()

        for i in range(lookback * 2, len(df)):
            current_close = df["close_price"].iloc[i]
            current_volume = df["volume"].iloc[i]
            avg_volume = df["volume"].iloc[i-lookback:i].mean()
            
            # Look for recent swing high to break
            recent_swing_highs = df["swing_high"].iloc[i-lookback*2:i-lookback]
            recent_swing_highs = recent_swing_highs.dropna()
            
            if len(recent_swing_highs) > 0:
                highest_swing = recent_swing_highs.max()
                if (current_close > highest_swing and 
                    current_volume > avg_volume * 1.3):  # Volume confirmation
                    df.loc[df.index[i], "is_bos"] = True
                    df.loc[df.index[i], "bos_type"] = "bullish"
                    
                    # Calculate strength
                    price_strength = (current_close - highest_swing) / highest_swing
                    volume_strength = current_volume / avg_volume if avg_volume > 0 else 1
                    df.loc[df.index[i], "bos_strength"] = min(100, price_strength * volume_strength * 100)

            # Look for recent swing low to break
            recent_swing_lows = df["swing_low"].iloc[i-lookback*2:i-lookback]
            recent_swing_lows = recent_swing_lows.dropna()
            
            if len(recent_swing_lows) > 0:
                lowest_swing = recent_swing_lows.min()
                if (current_close < lowest_swing and 
                    current_volume > avg_volume * 1.3):  # Volume confirmation
                    df.loc[df.index[i], "is_bos"] = True
                    df.loc[df.index[i], "bos_type"] = "bearish"
                    
                    # Calculate strength
                    price_strength = (lowest_swing - current_close) / lowest_swing
                    volume_strength = current_volume / avg_volume if avg_volume > 0 else 1
                    df.loc[df.index[i], "bos_strength"] = min(100, price_strength * volume_strength * 100)

        return df

    async def comprehensive_ict_analysis(self, symbol: str, timeframe: str = "M5", periods: int = 100) -> Dict[str, Any]:
        """Perform comprehensive ICT/SMC analysis with advanced indicators.
        """
        try:
            if not self.advanced_analysis:
                logger.warning("Advanced analysis service not available")
                return {"error": "Advanced analysis service not initialized"}
            
            # Get market data
            ohlcv_data = await self.advanced_analysis.exness_service.get_ohlcv_data(symbol, timeframe, periods)
            
            if not ohlcv_data:
                return {"error": f"No market data available for {symbol}"}
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Rename columns for compatibility
            df = df.rename(columns={
                'open': 'open_price',
                'high': 'high_price', 
                'low': 'low_price',
                'close': 'close_price'
            })
            
            # Apply ICT/SMC analysis
            df = self.identify_order_blocks(df)
            df = self.identify_liquidity_zones(df)
            df = self.identify_fair_value_gaps(df)
            df = self.identify_break_of_structure(df)
            
            # Get advanced analysis
            advanced_analysis = await self.advanced_analysis.get_comprehensive_analysis(symbol, timeframe, periods)
            
            # Combine results
            ict_analysis = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now(),
                'order_blocks': {
                    'bullish': df[df['is_bullish_ob']].to_dict('records'),
                    'bearish': df[df['is_bearish_ob']].to_dict('records'),
                    'count': len(df[df['is_bullish_ob'] | df['is_bearish_ob']])
                },
                'liquidity_zones': {
                    'zones': df[df['is_liquidity_zone']].to_dict('records'),
                    'resistance_levels': df[df['liquidity_type'] == 'resistance']['high_price'].tolist(),
                    'support_levels': df[df['liquidity_type'] == 'support']['low_price'].tolist(),
                    'equal_highs': df[df['liquidity_type'] == 'equal_highs']['high_price'].tolist(),
                    'equal_lows': df[df['liquidity_type'] == 'equal_lows']['low_price'].tolist()
                },
                'fair_value_gaps': {
                    'gaps': df[df['is_fvg']].to_dict('records'),
                    'bullish_gaps': df[df['fvg_type'] == 'bullish'].to_dict('records'),
                    'bearish_gaps': df[df['fvg_type'] == 'bearish'].to_dict('records')
                },
                'break_of_structure': {
                    'breaks': df[df['is_bos']].to_dict('records'),
                    'bullish_breaks': len(df[df['bos_type'] == 'bullish']),
                    'bearish_breaks': len(df[df['bos_type'] == 'bearish'])
                },
                'advanced_indicators': advanced_analysis
            }
            
            # Generate trading signals based on combined analysis
            signals = self._generate_trading_signals(ict_analysis, df)
            ict_analysis['trading_signals'] = signals
            
            logger.info(f"Comprehensive ICT analysis completed for {symbol}")
            return ict_analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive ICT analysis for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol, "timestamp": datetime.now()}

    def _generate_trading_signals(self, analysis: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading signals based on ICT/SMC and advanced analysis.
        """
        signals = {
            'overall_bias': 'neutral',
            'confidence': 0,
            'entry_signals': [],
            'key_levels': {
                'resistance': [],
                'support': [],
                'targets': []
            },
            'risk_factors': []
        }
        
        try:
            # Get latest price
            latest_price = df['close_price'].iloc[-1]
            
            # Analyze advanced indicators
            advanced = analysis.get('advanced_indicators', {})
            overall_sentiment = advanced.get('overall_sentiment', {})
            
            # Base bias from advanced analysis
            sentiment = overall_sentiment.get('sentiment', 'neutral')
            confidence = overall_sentiment.get('confidence', 0)
            
            # Adjust bias based on ICT concepts
            ict_bias_score = 0
            
            # Order blocks influence
            recent_bullish_obs = [ob for ob in analysis['order_blocks']['bullish'] 
                                if len(analysis['order_blocks']['bullish']) > 0]
            recent_bearish_obs = [ob for ob in analysis['order_blocks']['bearish'] 
                                if len(analysis['order_blocks']['bearish']) > 0]
            
            if recent_bullish_obs:
                ict_bias_score += 20
            if recent_bearish_obs:
                ict_bias_score -= 20
            
            # Liquidity zones influence
            resistance_levels = analysis['liquidity_zones']['resistance_levels']
            support_levels = analysis['liquidity_zones']['support_levels']
            
            # Check if price is near key levels
            for level in resistance_levels[-3:]:  # Last 3 resistance levels
                if abs(latest_price - level) / latest_price < 0.002:  # Within 0.2%
                    signals['key_levels']['resistance'].append(level)
                    if latest_price < level:
                        ict_bias_score -= 10  # Bearish near resistance
            
            for level in support_levels[-3:]:  # Last 3 support levels
                if abs(latest_price - level) / latest_price < 0.002:  # Within 0.2%
                    signals['key_levels']['support'].append(level)
                    if latest_price > level:
                        ict_bias_score += 10  # Bullish near support
            
            # Fair Value Gaps influence
            unfilled_fvgs = [gap for gap in analysis['fair_value_gaps']['gaps'] 
                           if gap['fvg_strength'] > 30]  # Strong gaps only
            
            for gap in unfilled_fvgs[-3:]:  # Recent strong gaps
                if gap['fvg_type'] == 'bullish' and latest_price > gap['fvg_bottom']:
                    ict_bias_score += 15
                elif gap['fvg_type'] == 'bearish' and latest_price < gap['fvg_top']:
                    ict_bias_score -= 15
            
            # Break of Structure influence
            recent_bos = analysis['break_of_structure']['breaks'][-5:] if analysis['break_of_structure']['breaks'] else []
            
            for bos in recent_bos:
                if bos['bos_type'] == 'bullish' and bos['bos_strength'] > 50:
                    ict_bias_score += 25
                elif bos['bos_type'] == 'bearish' and bos['bos_strength'] > 50:
                    ict_bias_score -= 25
            
            # Combine sentiment with ICT bias
            total_score = confidence * (1 if 'bullish' in sentiment else -1 if 'bearish' in sentiment else 0) + ict_bias_score
            
            # Determine final bias
            if total_score > 50:
                signals['overall_bias'] = 'strongly_bullish'
            elif total_score > 25:
                signals['overall_bias'] = 'bullish'
            elif total_score > -25:
                signals['overall_bias'] = 'neutral'
            elif total_score > -50:
                signals['overall_bias'] = 'bearish'
            else:
                signals['overall_bias'] = 'strongly_bearish'
            
            signals['confidence'] = min(100, abs(total_score))
            
            # Generate specific entry signals
            if signals['overall_bias'] in ['bullish', 'strongly_bullish']:
                # Look for bullish entry opportunities
                if support_levels:
                    nearest_support = min(support_levels, key=lambda x: abs(x - latest_price))
                    if latest_price > nearest_support * 1.001:  # Above support
                        signals['entry_signals'].append({
                            'type': 'buy',
                            'reason': 'Price above key support with bullish bias',
                            'entry_zone': [nearest_support * 0.999, nearest_support * 1.002],
                            'confidence': signals['confidence']
                        })
                
                # Target resistance levels
                if resistance_levels:
                    signals['key_levels']['targets'] = sorted(resistance_levels)[:3]
            
            elif signals['overall_bias'] in ['bearish', 'strongly_bearish']:
                # Look for bearish entry opportunities
                if resistance_levels:
                    nearest_resistance = min(resistance_levels, key=lambda x: abs(x - latest_price))
                    if latest_price < nearest_resistance * 0.999:  # Below resistance
                        signals['entry_signals'].append({
                            'type': 'sell',
                            'reason': 'Price below key resistance with bearish bias',
                            'entry_zone': [nearest_resistance * 0.998, nearest_resistance * 1.001],
                            'confidence': signals['confidence']
                        })
                
                # Target support levels
                if support_levels:
                    signals['key_levels']['targets'] = sorted(support_levels, reverse=True)[:3]
            
            # Add risk factors
            if len(unfilled_fvgs) > 3:
                signals['risk_factors'].append('Multiple unfilled Fair Value Gaps present')
            
            if advanced.get('stop_run_analysis', {}).get('recent_stop_runs'):
                signals['risk_factors'].append('Recent stop runs detected - high volatility expected')
            
            cvd_analysis = advanced.get('cvd_analysis', {})
            if cvd_analysis.get('divergence_detected'):
                signals['risk_factors'].append('CVD divergence detected - potential reversal')
            
        except Exception as e:
            logger.error(f"Error generating trading signals: {e}")
            signals['error'] = str(e)
        
        return signals

    def identify_fair_value_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identifies Fair Value Gaps (FVG).
        FVG: A gap between the high of candle 1 and the low of candle 3.
        """
        df["is_bullish_fvg"] = False
        df["is_bearish_fvg"] = False

        if len(df) >= 3:
            for i in range(len(df) - 2):
                # Bullish FVG: Low of current candle (i) > High of previous candle (i-1)
                # And current candle (i) is bullish, next candle (i+1) is bullish
                if df["low_price"].iloc[i+1] > df["high_price"].iloc[i]:
                    df.loc[df.index[i+1], "is_bullish_fvg"] = True
                
                # Bearish FVG: High of current candle (i) < Low of previous candle (i-1)
                # And current candle (i) is bearish, next candle (i+1) is bearish
                if df["high_price"].iloc[i+1] < df["low_price"].iloc[i]:
                    df.loc[df.index[i+1], "is_bearish_fvg"] = True
        return df

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies all ICT/SMC analysis methods to the DataFrame."""
        df = self.identify_order_blocks(df.copy())
        df = self.identify_liquidity_zones(df.copy())
        df = self.identify_fair_value_gaps(df.copy())
        return df.fillna(0) # Fill any NaNs created by analysis

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

    df = pd.DataFrame(sample_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    analyzer = ICTSMCAnalyzerService()
    df_analyzed = analyzer.analyze(df.copy())

    print("\nData with ICT/SMC Features (first 15 rows):\n", df_analyzed.head(15))
    print("\nColumns in final DataFrame:", df_analyzed.columns.tolist())

    # Check for identified features
    print("\nBullish Order Blocks found:", df_analyzed["is_bullish_ob"].sum())
    print("Bearish Order Blocks found:", df_analyzed["is_bearish_ob"].sum())
    print("Liquidity Zones found:", df_analyzed["is_liquidity_zone"].sum())
    print("Bullish FVGs found:", df_analyzed["is_bullish_fvg"].sum())
    print("Bearish FVGs found:", df_analyzed["is_bearish_fvg"].sum())


