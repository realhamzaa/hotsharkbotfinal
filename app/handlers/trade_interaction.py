"""
Trade interaction handlers for HOT SHARK Bot.
Handles user actions related to entering trades and updating their status.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.recommendation import Recommendation
from app.models.user_trade import UserTrade
from app.utils.localization import loc
from app.services.recommendation_service import RecommendationService
from app.handlers.auth_middleware import check_single_session
from app.services.data_collector_service import DataCollectorService
import logging

logger = logging.getLogger(__name__)

@check_single_session
async def entered_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the \'entered trade\' callback from inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    recommendation_id = int(query.data.split("_")[1])
    user_id = query.from_user.id
    message_id = query.message.message_id # Get the message ID of the recommendation
    
    db: Session = SessionLocal()
    try:
        recommendation = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not recommendation:
            await query.edit_message_text(text=loc.get_text("recommendation_not_found", query.from_user.language))
            return
        
        # Check if user already entered this trade
        existing_user_trade = db.query(UserTrade).filter(
            UserTrade.user_id == user_id,
            UserTrade.recommendation_id == recommendation_id
        ).first()
        
        if existing_user_trade:
            await query.edit_message_text(text=loc.get_text("trade_already_entered", query.from_user.language))
            return
            
        user_trade = UserTrade(
            user_id=user_id,
            recommendation_id=recommendation_id,
            message_id=message_id, # Store the message ID
            entry_time=datetime.now(),
            result="pending"
        )
        db.add(user_trade)
        db.commit()
        db.refresh(user_trade)
        
        await query.edit_message_text(text=loc.get_text("trade_entered_success", query.from_user.language).format(symbol=recommendation.asset_pair))
        logger.info(f"User {user_id} entered trade for recommendation {recommendation_id}")
        
    except Exception as e:
        logger.error(f"Error handling entered_trade_callback for user {user_id}, rec {recommendation_id}: {e}")
        await query.edit_message_text(text=loc.get_text("error_occurred", query.from_user.language))
    finally:
        db.close()

@check_single_session
async def update_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the \'update trade\' callback from inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    recommendation_id = int(query.data.split("_")[1])
    user_id = query.from_user.id
    
    db: Session = SessionLocal()
    try:
        recommendation = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not recommendation:
            await query.edit_message_text(text=loc.get_text("recommendation_not_found", query.from_user.language))
            return
        
        # Fetch the user\'s trade for this recommendation
        user_trade = db.query(UserTrade).filter(
            UserTrade.user_id == user_id,
            UserTrade.recommendation_id == recommendation_id
        ).first()

        if not user_trade:
            await query.edit_message_text(text=loc.get_text("trade_not_entered_yet", query.from_user.language))
            return

        # Get latest market data for the asset pair
        data_collector = DataCollectorService()
        latest_data = await data_collector.get_latest_data(recommendation.asset_pair)
        
        current_price = None
        if latest_data and latest_data.get("close_price"):
            current_price = latest_data["close_price"]

        scenario = "لا تتوفر بيانات حالية للسوق." # Default scenario
        if current_price:
            entry_price = recommendation.entry_points[0]
            trade_type = recommendation.trade_type.upper()
            
            if trade_type == "BUY":
                if current_price > entry_price:
                    scenario = f"السعر الحالي: {current_price:.5f}. الصفقة في منطقة الربح. استمر في المراقبة أو أغلق جزءًا من الصفقة."
                elif current_price < entry_price:
                    scenario = f"السعر الحالي: {current_price:.5f}. الصفقة في منطقة الخسارة. راقب مستوى وقف الخسارة."
                else:
                    scenario = f"السعر الحالي: {current_price:.5f}. الصفقة عند نقطة الدخول. لا يوجد تغيير كبير."
            elif trade_type == "SELL":
                if current_price < entry_price:
                    scenario = f"السعر الحالي: {current_price:.5f}. الصفقة في منطقة الربح. استمر في المراقبة أو أغلق جزءًا من الصفقة."
                elif current_price > entry_price:
                    scenario = f"السعر الحالي: {current_price:.5f}. الصفقة في منطقة الخسارة. راقب مستوى وقف الخسارة."
                else:
                    scenario = f"السعر الحالي: {current_price:.5f}. الصفقة عند نقطة الدخول. لا يوجد تغيير كبير."

            # Check against TP/SL levels
            if recommendation.tp_levels and trade_type == "BUY" and current_price >= recommendation.tp_levels[0]:
                scenario += "\n✅ تم تحقيق الهدف الأول (TP1)!"
            elif recommendation.tp_levels and trade_type == "SELL" and current_price <= recommendation.tp_levels[0]:
                scenario += "\n✅ تم تحقيق الهدف الأول (TP1)!"
            
            if recommendation.sl and trade_type == "BUY" and current_price <= recommendation.sl:
                scenario += "\n❌ تم ضرب وقف الخسارة (SL)!"
            elif recommendation.sl and trade_type == "SELL" and current_price >= recommendation.sl:
                scenario += "\n❌ تم ضرب وقف الخسارة (SL)!"

        status_message = loc.get_text("trade_status_update", query.from_user.language).format(
            symbol=recommendation.asset_pair,
            status=user_trade.result if user_trade.result else "قيد المتابعة",
            entry_price=recommendation.entry_points[0],
            current_price=f"{current_price:.5f}" if current_price else "غير متوفر",
            scenario=scenario
        )
        
        await query.edit_message_text(text=status_message)
        logger.info(f"User {user_id} requested update for trade {recommendation_id}")
        
    except Exception as e:
        logger.error(f"Error handling update_trade_callback for user {user_id}, rec {recommendation_id}: {e}")
        await query.edit_message_text(text=loc.get_text("error_occurred", query.from_user.language))
    finally:
        db.close()


