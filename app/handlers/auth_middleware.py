"""
Authentication middleware for HOT SHARK Bot handlers.
Ensures only one active login session per user.
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from app.models.database import SessionLocal
from app.services.user_session_service import UserSessionService
from app.utils.localization import loc
import logging

logger = logging.getLogger(__name__)

def check_single_session(handler_func):
    """Decorator to enforce single active session per user."""
    @wraps(handler_func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # For commands, the session ID can be the chat ID or a unique identifier for the bot instance
        # For simplicity, we'll use the chat ID as the session ID for now.
        # In a more complex setup, you might generate a unique session ID per bot instance/device.
        session_id = str(update.effective_chat.id) # Using chat ID as session ID for now
        
        db = SessionLocal()
        try:
            session_service = UserSessionService(db)
            
            # If it's a new user or /start command, the session will be set by the start handler.
            # For other commands/callbacks, we check if the current session is active.
            if not session_service.is_active_session(user_id, session_id):
                logger.warning(f"Unauthorized access attempt by user {user_id} from session {session_id}. Session not active.")
                await update.effective_message.reply_text(loc.get_text("session_expired_or_logged_in_elsewhere", update.effective_user.language))
                return # Stop further processing
            
            # If session is active, proceed with the handler
            return await handler_func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in check_single_session for user {user_id}: {e}")
            await update.effective_message.reply_text(loc.get_text("error_occurred", update.effective_user.language))
        finally:
            db.close()
            
    return wrapper


