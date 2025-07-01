"""
Notification Service for HOT SHARK Bot.
Handles sending real-time updates and notifications to users.
"""

from telegram import Bot
from app.models.database import SessionLocal
from app.models.user import User
from app.utils.localization import loc
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    async def send_instant_update(bot: Bot, user_id: int, message: str, parse_mode: str = 'Markdown') -> None:
        """Sends an instant update message to a specific user."""
        try:
            await bot.send_message(chat_id=user_id, text=message, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Error sending instant update to user {user_id}: {e}")

    @staticmethod
    async def broadcast_market_alert(bot: Bot, alert_type: str, details: str, lang: str) -> None:
        """Broadcasts a market alert to all subscribed users."""
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.is_subscribed == True).all()
            alert_message = loc.get_text(f"market_alert_{alert_type}", lang).format(details=details)
            for user in users:
                try:
                    await bot.send_message(chat_id=user.id, text=alert_message, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Error broadcasting market alert to user {user.id}: {e}")
        finally:
            db.close()

    @staticmethod
    async def send_zero_drawdown_alert(bot: Bot, recommendation_id: int, lang: str) -> None:
        """Sends a special alert for zero drawdown trades."""
        from app.services.recommendation_service import RecommendationService
        recommendation = RecommendationService.get_recommendation_by_id(recommendation_id)
        if recommendation:
            message = loc.get_text("zero_drawdown_alert", lang).format(
                asset_pair=recommendation.asset_pair,
                trade_type=recommendation.trade_type.upper()
            )
            db = SessionLocal()
            try:
                users = db.query(User).filter(User.is_subscribed == True).all()
                for user in users:
                    try:
                        await bot.send_message(chat_id=user.id, text=message, parse_mode='Markdown')
                    except Exception as e:
                        logger.error(f"Error sending zero drawdown alert to user {user.id}: {e}")
            finally:
                db.close()



