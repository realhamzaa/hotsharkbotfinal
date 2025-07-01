"""
Recommendation handler for HOT SHARK Bot
"""
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ContextTypes
from app.handlers.base import BaseHandler
from app.services.recommendation_service import RecommendationService
from app.models.user import User
from app.models.database import SessionLocal

class RecommendationHandler(BaseHandler):
    @staticmethod
    async def send_recommendation_to_all(
        bot: Bot,
        asset_pair: str,
        trade_type: str,
        entry_points: list,
        tp_levels: list,
        sl: float,
        pips: int,
        success_rate: float = None,
        trade_duration: str = "short",
        rr_ratio: str = "1:2",
        lot_size_per_100: float = 0.01,
        is_premium: bool = False,
        strategy: str = None,
        is_live: bool = True
    ):
        """Send recommendation to all subscribed users"""
        
        # Create recommendation
        recommendation = RecommendationService.create_recommendation(
            asset_pair=asset_pair,
            trade_type=trade_type,
            entry_points=entry_points,
            tp_levels=tp_levels,
            sl=sl,
            pips=pips,
            success_rate=success_rate,
            trade_duration=trade_duration,
            rr_ratio=rr_ratio,
            lot_size_per_100=lot_size_per_100,
            is_premium=is_premium,
            strategy=strategy,
            is_live=is_live
        )
        
        # Create keyboard
        keyboard = RecommendationService.create_recommendation_keyboard(recommendation.id)
        
        # Get all subscribed users
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.is_subscribed == True).all()
            
            for user in users:
                try:
                    await bot.send_message(
                        chat_id=user.id,
                        text=recommendation.message_text,
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"Error sending recommendation to user {user.id}: {e}")
        finally:
            db.close()
    
    @staticmethod
    async def update_recommendation_status(
        bot: Bot,
        recommendation_id: int,
        status: str
    ):
        """Update recommendation status and notify users"""
        
        # Update recommendation
        success = RecommendationService.update_recommendation_status(recommendation_id, status)
        
        if success:
            # Get updated recommendation
            db = SessionLocal()
            try:
                from app.models.recommendation import Recommendation
                recommendation = db.query(Recommendation).filter(
                    Recommendation.id == recommendation_id
                ).first()
                
                if recommendation:
                    # Get users who entered this trade
                    from app.models.user_trade import UserTrade
                    user_trades = db.query(UserTrade).filter(
                        UserTrade.recommendation_id == recommendation_id
                    ).all()
                    
                    for trade in user_trades:
                        try:
                            # Update user trade result
                            if status == "tp_hit":
                                trade.result = "profit"
                                trade.profit_loss = recommendation.pips
                            elif status == "sl_hit":
                                trade.result = "loss"
                                trade.profit_loss = -recommendation.pips
                            
                            trade.exit_time = datetime.now()
                            
                            # Send update to user
                            status_message = "✅ تم تحقيق الهدف!" if status == "tp_hit" else "❌ تم ضرب وقف الخسارة"
                            
                            await bot.send_message(
                                chat_id=trade.user_id,
                                text=f"🔄 تحديث الصفقة: {recommendation.asset_pair}\n\n{status_message}",
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            print(f"Error updating user {trade.user_id}: {e}")
                    
                    db.commit()
            finally:
                db.close()
    
    @staticmethod
    async def send_market_analysis(bot: Bot, analysis_text: str):
        """Send market analysis to all subscribed users"""
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.is_subscribed == True).all()
            
            for user in users:
                try:
                    await bot.send_message(
                        chat_id=user.id,
                        text=f"📊 **تحليل السوق**\n\n{analysis_text}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"Error sending analysis to user {user.id}: {e}")
        finally:
            db.close()

