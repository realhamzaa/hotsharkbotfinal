"""
Auto Recommendation Service for HOT SHARK Bot.
Generates and sends automated trading recommendations using AI/ML models.
"""

import asyncio
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.recommendation import Recommendation
from app.models.market_data import MarketData
from app.services.ml_model_service import MLModelService
from app.services.data_processor_service import DataProcessorService
from app.services.ict_smc_analyzer_service import ICTSMCAnalyzerService
from app.utils.localization import get_text
import logging

logger = logging.getLogger(__name__)

class AutoRecommendationService:
    def __init__(self, db: Session, bot):
        self.db = db
        self.bot = bot
        self.ml_service = MLModelService()
        self.data_processor = DataProcessorService()
        self.ict_analyzer = ICTSMCAnalyzerService()
        
        # Supported trading pairs
        self.supported_pairs = [
            "XAUUSD",  # Gold
            "BTCUSD",  # Bitcoin
            "ETHUSD",  # Ethereum
            "EURUSD",  # Euro/USD
            "GBPJPY",  # GBP/JPY
            "GBPUSD",  # GBP/USD
            "USDJPY",  # USD/JPY
            "US30",    # Dow Jones
            "US100"    # Nasdaq
        ]

    def calculate_success_probability(self, analysis_data: Dict) -> float:
        """Calculate success probability based on multiple factors."""
        base_probability = 0.5
        
        # ICT/SMC factors
        if analysis_data.get('is_bullish_ob') or analysis_data.get('is_bearish_ob'):
            base_probability += 0.15
        
        if analysis_data.get('is_liquidity_zone'):
            base_probability += 0.10
            
        if analysis_data.get('is_bullish_fvg') or analysis_data.get('is_bearish_fvg'):
            base_probability += 0.08
        
        # Technical indicators alignment
        rsi = analysis_data.get('RSI', 50)
        if (rsi < 30 and analysis_data.get('signal_type') == 'BUY') or \
           (rsi > 70 and analysis_data.get('signal_type') == 'SELL'):
            base_probability += 0.12
        
        # MACD confirmation
        macd = analysis_data.get('MACD', 0)
        if (macd > 0 and analysis_data.get('signal_type') == 'BUY') or \
           (macd < 0 and analysis_data.get('signal_type') == 'SELL'):
            base_probability += 0.08
        
        # Cap at 95%
        return min(base_probability, 0.95)

    def determine_trade_type(self, timeframe: str, expected_duration_hours: int) -> str:
        """Determine if trade is scalp, short-term, or long-term."""
        if expected_duration_hours <= 1:
            return "سكالب"
        elif expected_duration_hours <= 24:
            return "قصيرة المدى"
        else:
            return "طويلة المدى"

    def calculate_lot_size(self, account_balance: float = 100) -> float:
        """Calculate suggested lot size for given account balance."""
        # Conservative approach: 1% risk per trade
        base_lot = 0.01
        return round((account_balance / 100) * base_lot, 2)

    def calculate_pips(self, entry_price: float, target_price: float, symbol: str) -> int:
        """Calculate pips between entry and target."""
        pip_value = 0.0001  # Default for most pairs
        
        if "JPY" in symbol:
            pip_value = 0.01
        elif symbol in ["XAUUSD", "BTCUSD", "ETHUSD"]:
            pip_value = 0.1
        elif symbol in ["US30", "US100"]:
            pip_value = 1.0
            
        return int(abs(target_price - entry_price) / pip_value)

    def format_recommendation_message(self, recommendation_data: Dict, lang: str = "ar") -> str:
        """Format the recommendation message with all required details."""
        symbol = recommendation_data['symbol']
        signal_type = recommendation_data['signal_type']
        entry_price = recommendation_data['entry_price']
        tp_levels = recommendation_data['tp_levels']
        sl_price = recommendation_data['sl_price']
        success_probability = recommendation_data['success_probability']
        trade_type = recommendation_data['trade_type']
        strategy = recommendation_data['strategy']
        lot_size = recommendation_data['lot_size']
        is_premium = recommendation_data.get('is_premium', False)
        
        # Timezone formatting
        palestine_tz = pytz.timezone('Asia/Gaza')
        utc_tz = pytz.timezone('UTC')
        now = datetime.now(utc_tz)
        palestine_time = now.astimezone(palestine_tz)
        
        palestine_time_str = palestine_time.strftime("%I:%M %p")
        utc_time_str = now.strftime("%H:%M")
        
        # Emojis based on signal type and premium status
        direction_emoji = "🟢" if signal_type == "BUY" else "🔴"
        premium_emoji = "💎" if is_premium else "⭐"
        
        # Calculate R:R ratio
        tp1_pips = self.calculate_pips(entry_price, tp_levels[0], symbol)
        sl_pips = self.calculate_pips(entry_price, sl_price, symbol)
        rr_ratio = round(tp1_pips / sl_pips, 1) if sl_pips > 0 else 1.0
        
        if lang == "ar":
            message = f"""
{premium_emoji} **توصية {symbol}** {direction_emoji}

📊 **التحليل:** {strategy}
🎯 **الاتجاه:** {signal_type}
📈 **نوع الصفقة:** {trade_type}
🎲 **نسبة النجاح:** {success_probability:.0%}
💰 **اللوت المقترح:** {lot_size} لكل 100$

🔹 **الدخول:** `{entry_price:.5f}`
🎯 **الهدف الأول:** `{tp_levels[0]:.5f}` ({tp1_pips} نقطة)
🎯 **الهدف الثاني:** `{tp_levels[1]:.5f}` ({self.calculate_pips(entry_price, tp_levels[1], symbol)} نقطة)
🛑 **وقف الخسارة:** `{sl_price:.5f}` ({sl_pips} نقطة)

📊 **نسبة المخاطرة:** R 1:{rr_ratio}

⏰ **التوقيت:**
🇵🇸 فلسطين: {palestine_time_str}
🌍 غرينتش: {utc_time_str}

💡 **ملاحظة:** تأكد من إدارة المخاطر وعدم المخاطرة بأكثر من 2% من رأس المال
"""
        else:
            message = f"""
{premium_emoji} **{symbol} Signal** {direction_emoji}

📊 **Analysis:** {strategy}
🎯 **Direction:** {signal_type}
📈 **Trade Type:** {trade_type}
🎲 **Success Rate:** {success_probability:.0%}
💰 **Suggested Lot:** {lot_size} per $100

🔹 **Entry:** `{entry_price:.5f}`
🎯 **Target 1:** `{tp_levels[0]:.5f}` ({tp1_pips} pips)
🎯 **Target 2:** `{tp_levels[1]:.5f}` ({self.calculate_pips(entry_price, tp_levels[1], symbol)} pips)
🛑 **Stop Loss:** `{sl_price:.5f}` ({sl_pips} pips)

📊 **Risk Ratio:** R 1:{rr_ratio}

⏰ **Timing:**
🇵🇸 Palestine: {palestine_time_str}
🌍 GMT: {utc_time_str}

💡 **Note:** Ensure proper risk management and don't risk more than 2% of capital
"""
        
        return message.strip()

    async def generate_recommendation(self, symbol: str) -> Optional[Dict]:
        """Generate a trading recommendation for a given symbol."""
        try:
            # Get latest market data
            latest_data = self.db.query(MarketData).filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp.desc()).first()
            
            if not latest_data:
                logger.warning(f"No market data found for {symbol}")
                return None
            
            # Convert to DataFrame for processing
            data_dict = {
                "symbol": [latest_data.symbol],
                "timestamp": [latest_data.timestamp],
                "open_price": [latest_data.open_price],
                "high_price": [latest_data.high_price],
                "low_price": [latest_data.low_price],
                "close_price": [latest_data.close_price],
                "volume": [latest_data.volume],
                "interval": [latest_data.interval],
                "source": [latest_data.source]
            }
            
            import pandas as pd
            df = pd.DataFrame(data_dict)
            
            # Process data and extract features
            processed_df = self.data_processor.extract_features(df)
            
            if processed_df.empty:
                logger.warning(f"Failed to process data for {symbol}")
                return None
            
            # Get AI prediction
            signal_prediction = self.ml_service.predict_signal(processed_df)
            
            if signal_prediction == "HOLD":
                return None  # Don't send HOLD signals
            
            # Get the processed row for analysis
            analysis_row = processed_df.iloc[-1].to_dict()
            analysis_row['signal_type'] = signal_prediction
            
            # Calculate success probability
            success_probability = self.calculate_success_probability(analysis_row)
            
            # Only send high-probability signals (>65%)
            if success_probability < 0.65:
                return None
            
            # Determine if this is a premium signal (>85% success rate)
            is_premium = success_probability >= 0.85
            
            # Calculate entry, TP, and SL levels
            current_price = latest_data.close_price
            
            if signal_prediction == "BUY":
                entry_price = current_price
                tp1 = current_price * 1.01  # 1% profit
                tp2 = current_price * 1.02  # 2% profit
                sl_price = current_price * 0.995  # 0.5% loss
            else:  # SELL
                entry_price = current_price
                tp1 = current_price * 0.99  # 1% profit
                tp2 = current_price * 0.98  # 2% profit
                sl_price = current_price * 1.005  # 0.5% loss
            
            # Determine trade type and strategy
            trade_type = self.determine_trade_type("1min", 2)  # Assuming 2-hour expected duration
            strategy = "ICT/SMC + AI Analysis"
            
            recommendation_data = {
                'symbol': symbol,
                'signal_type': signal_prediction,
                'entry_price': entry_price,
                'tp_levels': [tp1, tp2],
                'sl_price': sl_price,
                'success_probability': success_probability,
                'trade_type': trade_type,
                'strategy': strategy,
                'lot_size': self.calculate_lot_size(),
                'is_premium': is_premium,
                'analysis_data': analysis_row
            }
            
            return recommendation_data
            
        except Exception as e:
            logger.error(f"Error generating recommendation for {symbol}: {e}")
            return None

    async def send_recommendation_to_users(self, recommendation_data: Dict):
        """Send recommendation to all subscribed users."""
        try:
            # Get all active subscribers
            active_users = self.db.query(User).filter(
                User.is_subscribed == True,
                User.subscription_end_date > datetime.now()
            ).all()
            
            if not active_users:
                logger.info("No active subscribers to send recommendations to")
                return
            
            # Save recommendation to database
            recommendation = Recommendation(
                symbol=recommendation_data['symbol'],
                signal_type=recommendation_data['signal_type'],
                entry_price=recommendation_data['entry_price'],
                tp1_price=recommendation_data['tp_levels'][0],
                tp2_price=recommendation_data['tp_levels'][1],
                sl_price=recommendation_data['sl_price'],
                success_probability=recommendation_data['success_probability'],
                trade_type=recommendation_data['trade_type'],
                strategy=recommendation_data['strategy'],
                is_premium=recommendation_data['is_premium'],
                status="ACTIVE"
            )
            
            self.db.add(recommendation)
            self.db.commit()
            
            # Send to users
            for user in active_users:
                try:
                    message = self.format_recommendation_message(
                        recommendation_data, 
                        user.language
                    )
                    
                    # Create inline keyboard for user interaction
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    
                    keyboard = [
                        [InlineKeyboardButton("✅ دخلت الصفقة", callback_data=f"entered_{recommendation.id}")],
                        [InlineKeyboardButton("📊 تحديث الحالة", callback_data=f"update_{recommendation.id}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    
                    logger.info(f"Recommendation sent to user {user.telegram_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to send recommendation to user {user.telegram_id}: {e}")
            
            logger.info(f"Recommendation for {recommendation_data['symbol']} sent to {len(active_users)} users")
            
        except Exception as e:
            logger.error(f"Error sending recommendation to users: {e}")

    async def monitor_and_generate_recommendations(self):
        """Main method to monitor market and generate recommendations."""
        logger.info("Starting recommendation monitoring...")
        
        for symbol in self.supported_pairs:
            try:
                recommendation_data = await self.generate_recommendation(symbol)
                
                if recommendation_data:
                    logger.info(f"Generated recommendation for {symbol}: {recommendation_data['signal_type']}")
                    await self.send_recommendation_to_users(recommendation_data)
                    
                    # Add delay between recommendations to avoid spam
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        logger.info("Recommendation monitoring cycle completed")

# Example usage
async def main():
    from app.models.database import SessionLocal
    from app.bot import bot
    
    db = SessionLocal()
    try:
        auto_rec_service = AutoRecommendationService(db, bot)
        await auto_rec_service.monitor_and_generate_recommendations()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())

