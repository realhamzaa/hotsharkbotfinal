"""
User preferences handlers for HOT SHARK Bot.
Handles user settings for recommendations and news.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.user import User
from app.utils.localization import loc
from app.handlers.auth_middleware import check_single_session
import json
import logging

logger = logging.getLogger(__name__)

@check_single_session
async def toggle_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggles receiving recommendations for the user."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.receive_recommendations = not user.receive_recommendations
            db.add(user)
            db.commit()
            db.refresh(user)
            status = loc.get_text("enabled" if user.receive_recommendations else "disabled", user.lang_code)
            await query.edit_message_text(text=loc.get_text("recommendations_status", user.lang_code).format(status=status))
        else:
            await query.edit_message_text(text=loc.get_text("user_not_found", user.lang_code))
    except Exception as e:
        logger.error(f"Error toggling recommendations for user {user_id}: {e}")
        await query.edit_message_text(text=loc.get_text("error_occurred", user.lang_code))
    finally:
        db.close()

@check_single_session
async def manage_paused_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allows user to manage paused asset pairs for recommendations."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # For simplicity, let's just list some common pairs. In a real app, this would be dynamic.
            available_pairs = ["XAUUSD", "BTCUSD", "EURUSD", "GBPUSD"]
            paused_pairs = json.loads(user.paused_pairs) if user.paused_pairs else []
            
            keyboard = []
            for pair in available_pairs:
                status_emoji = "✅" if pair not in paused_pairs else "❌"
                keyboard.append([InlineKeyboardButton(f"{pair} {status_emoji}", callback_data=f"toggle_pair_{pair}")])
            keyboard.append([InlineKeyboardButton(loc.get_text("back", user.lang_code), callback_data="settings_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=loc.get_text("manage_pairs_menu", user.lang_code), reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=loc.get_text("user_not_found", user.lang_code))
    except Exception as e:
        logger.error(f"Error managing paused pairs for user {user_id}: {e}")
        await query.edit_message_text(text=loc.get_text("error_occurred", user.lang_code))
    finally:
        db.close()

@check_single_session
async def toggle_pair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggles pausing/unpausing a specific asset pair."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    pair_to_toggle = query.data.split("_")[1]
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            paused_pairs = json.loads(user.paused_pairs) if user.paused_pairs else []
            if pair_to_toggle in paused_pairs:
                paused_pairs.remove(pair_to_toggle)
                status = loc.get_text("unpaused", user.lang_code)
            else:
                paused_pairs.append(pair_to_toggle)
                status = loc.get_text("paused", user.lang_code)
            
            user.paused_pairs = json.dumps(paused_pairs)
            db.add(user)
            db.commit()
            db.refresh(user)
            
            await query.edit_message_text(text=loc.get_text("pair_status_updated", user.lang_code).format(pair=pair_to_toggle, status=status))
            # Re-show the manage pairs menu
            await manage_paused_pairs(update, context)
        else:
            await query.edit_message_text(text=loc.get_text("user_not_found", user.lang_code))
    except Exception as e:
        logger.error(f"Error toggling pair {pair_to_toggle} for user {user_id}: {e}")
        await query.edit_message_text(text=loc.get_text("error_occurred", user.lang_code))
    finally:
        db.close()

@check_single_session
async def toggle_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggles receiving news for the user."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.receive_news = not user.receive_news
            db.add(user)
            db.commit()
            db.refresh(user)
            status = loc.get_text("enabled" if user.receive_news else "disabled", user.lang_code)
            await query.edit_message_text(text=loc.get_text("news_status", user.lang_code).format(status=status))
        else:
            await query.edit_message_text(text=loc.get_text("user_not_found", user.lang_code))
    except Exception as e:
        logger.error(f"Error toggling news for user {user_id}: {e}")
        await query.edit_message_text(text=loc.get_text("error_occurred", user.lang_code))
    finally:
        db.close()

@check_single_session
async def manage_news_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allows user to manage news preferences (e.g., impact level)."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # For simplicity, let's just list impact levels. In a real app, this would be dynamic.
            available_impacts = ["low", "medium", "high"]
            news_prefs = json.loads(user.news_preferences) if user.news_preferences else {"impacts": ["low", "medium", "high"]}
            
            keyboard = []
            for impact in available_impacts:
                status_emoji = "✅" if impact in news_prefs.get("impacts", []) else "❌"
                keyboard.append([InlineKeyboardButton(f"{loc.get_text(impact, user.lang_code)} {status_emoji}", callback_data=f"toggle_impact_{impact}")])
            keyboard.append([InlineKeyboardButton(loc.get_text("back", user.lang_code), callback_data="settings_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=loc.get_text("manage_news_prefs_menu", user.lang_code), reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=loc.get_text("user_not_found", user.lang_code))
    except Exception as e:
        logger.error(f"Error managing news preferences for user {user_id}: {e}")
        await query.edit_message_text(text=loc.get_text("error_occurred", user.lang_code))
    finally:
        db.close()

@check_single_session
async def toggle_impact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggles a specific news impact level."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    impact_to_toggle = query.data.split("_")[1]
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            news_prefs = json.loads(user.news_preferences) if user.news_preferences else {"impacts": ["low", "medium", "high"]}
            current_impacts = news_prefs.get("impacts", [])
            
            if impact_to_toggle in current_impacts:
                current_impacts.remove(impact_to_toggle)
                status = loc.get_text("disabled", user.lang_code)
            else:
                current_impacts.append(impact_to_toggle)
                status = loc.get_text("enabled", user.lang_code)
            
            news_prefs["impacts"] = current_impacts
            user.news_preferences = json.dumps(news_prefs)
            db.add(user)
            db.commit()
            db.refresh(user)
            
            await query.edit_message_text(text=loc.get_text("impact_status_updated", user.lang_code).format(impact=loc.get_text(impact_to_toggle, user.lang_code), status=status))
            # Re-show the manage news preferences menu
            await manage_news_preferences(update, context)
        else:
            await query.edit_message_text(text=loc.get_text("user_not_found", user.lang_code))
    except Exception as e:
        logger.error(f"Error toggling impact {impact_to_toggle} for user {user_id}: {e}")
        await query.edit_message_text(text=loc.get_text("error_occurred", user.lang_code))
    finally:
        db.close()



