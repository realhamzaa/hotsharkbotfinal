"""
Start command handler for HOT SHARK Bot
"""
from telegram import Update
from telegram.ext import ContextTypes
from app.handlers.base import BaseHandler
from app.utils.localization import loc
from app.services.user_session_service import UserSessionService
from app.models.database import SessionLocal
import uuid

class StartHandler(BaseHandler):
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Get or create user
        db_user = BaseHandler.get_or_create_user(user.id, user.username)
        lang = db_user.lang_code
        
        # Generate a unique session ID for the user
        session_id = str(update.effective_chat.id) # Using chat ID as session ID for now
        
        db = SessionLocal()
        try:
            session_service = UserSessionService(db)
            # Set the new session as active
            session_service.set_user_active_session(user.id, session_id)
            
            # Create welcome message
            welcome_text = loc.get_text("welcome", lang)
            
            # Create keyboard
            keyboard = BaseHandler.create_main_keyboard(lang)
            
            # Add admin keyboard if user is admin
            if BaseHandler.is_admin(user.id):
                admin_keyboard = BaseHandler.create_admin_keyboard(lang)
                keyboard.inline_keyboard.extend(admin_keyboard.inline_keyboard)
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=keyboard
            )
        finally:
            db.close()
