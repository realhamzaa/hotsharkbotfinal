"""
Session Handler for HOT SHARK Bot
Handles login/logout with single session enforcement
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.services.session_manager_service import SessionManagerService
from app.handlers.base import BaseHandler
from app.utils.localization import get_text
from app.models.database import SessionLocal
from app.models.user import User

class SessionHandler:
    """Handler for session management"""
    
    @staticmethod
    async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle login request"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        username = query.from_user.username
        
        # Get user language
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                # Create new user
                user = User(
                    id=user_id,
                    username=username,
                    lang_code='ar'
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            lang_code = user.lang_code
            
            # Check if user already has active session
            if SessionManagerService.is_session_active(user_id):
                message = get_text('session_already_active', lang_code)
                keyboard = [
                    [
                        InlineKeyboardButton(
                            get_text('force_login', lang_code),
                            callback_data='force_login'
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            get_text('back', lang_code),
                            callback_data='main_menu'
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    text=message,
                    reply_markup=reply_markup
                )
                return
            
            # Create new session
            session_data = {
                'username': username,
                'login_time': query.message.date.timestamp()
            }
            
            success = SessionManagerService.create_session(user_id, session_data)
            
            if success:
                message = get_text('login_success', lang_code)
                # Update user status
                user.is_logged_in = True
                db.commit()
            else:
                message = get_text('login_failed', lang_code)
            
            # Return to main menu
            keyboard = BaseHandler.create_main_keyboard(lang_code)
            
            await query.edit_message_text(
                text=message,
                reply_markup=keyboard
            )
            
        finally:
            db.close()
    
    @staticmethod
    async def handle_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle logout request"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Get user language
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            lang_code = user.lang_code if user else 'ar'
            
            # End session
            success = SessionManagerService.end_session(user_id)
            
            if success and user:
                message = get_text('logout_success', lang_code)
                user.is_logged_in = False
                db.commit()
            else:
                message = get_text('logout_failed', lang_code)
            
            # Return to main menu
            keyboard = BaseHandler.create_main_keyboard(lang_code)
            
            await query.edit_message_text(
                text=message,
                reply_markup=keyboard
            )
            
        finally:
            db.close()
    
    @staticmethod
    async def handle_force_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle force login (terminate existing session)"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        username = query.from_user.username
        
        # Get user language
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            lang_code = user.lang_code if user else 'ar'
            
            # Force end existing session
            SessionManagerService.end_session(user_id)
            
            # Create new session
            session_data = {
                'username': username,
                'login_time': query.message.date.timestamp(),
                'forced': True
            }
            
            success = SessionManagerService.create_session(user_id, session_data)
            
            if success and user:
                message = get_text('force_login_success', lang_code)
                user.is_logged_in = True
                db.commit()
            else:
                message = get_text('login_failed', lang_code)
            
            # Return to main menu
            keyboard = BaseHandler.create_main_keyboard(lang_code)
            
            await query.edit_message_text(
                text=message,
                reply_markup=keyboard
            )
            
        finally:
            db.close()
    
    @staticmethod
    async def check_session_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Middleware to check session validity"""
        user_id = update.effective_user.id
        
        # Update activity if session exists
        if SessionManagerService.is_session_active(user_id):
            SessionManagerService.update_activity(user_id)
            return True
        
        return False
    
    @staticmethod
    def get_session_info(user_id: int) -> dict:
        """Get session information for user"""
        return SessionManagerService.get_session_info(user_id)
    
    @staticmethod
    def get_active_sessions_count() -> int:
        """Get count of active sessions"""
        return SessionManagerService.get_active_sessions_count()
    
    @staticmethod
    def get_all_active_users() -> list:
        """Get list of all users with active sessions"""
        return SessionManagerService.get_all_active_users()

