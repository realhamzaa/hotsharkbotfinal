"""
Base handler for HOT SHARK Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.user import User
from app.utils.localization import loc
from app.config import Config
from app.handlers.auth_middleware import check_single_session

class BaseHandler:
    @staticmethod
    def get_db() -> Session:
        """Get database session"""
        return SessionLocal()
    
    @staticmethod
    @check_single_session
    def get_or_create_user(user_id: int, username: str = None) -> User:
        """Get or create user in database"""
        db = BaseHandler.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                user = User(
                    id=user_id,
                    username=username,
                    is_admin=(user_id == Config.ADMIN_USER_ID)
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            return user
        finally:
            db.close()
    
    @staticmethod
    @check_single_session
    def get_user_language(user_id: int) -> str:
        """Get user\'s preferred language"""
        db = BaseHandler.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user.lang_code if user else Config.DEFAULT_LANGUAGE
        finally:
            db.close()
    
    @staticmethod
    def create_main_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
        """Create main keyboard based on user language"""
        keyboard = [
            [
                InlineKeyboardButton(
                    loc.get_keyboard_text("login", lang),
                    callback_data="login"
                ),
                InlineKeyboardButton(
                    loc.get_keyboard_text("logout", lang),
                    callback_data="logout"
                )
            ],
            [
                InlineKeyboardButton(
                    loc.get_keyboard_text("reports", lang),
                    callback_data="reports"
                ),
                InlineKeyboardButton(
                    loc.get_keyboard_text("settings", lang),
                    callback_data="settings"
                )
            ],
            [
                InlineKeyboardButton(
                    loc.get_keyboard_text("catalog", lang),
                    callback_data="catalog_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    loc.get_keyboard_text("language", lang),
                    callback_data="change_language"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_admin_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
        """Create admin keyboard"""
        keyboard = [
            [
                InlineKeyboardButton(
                    loc.get_keyboard_text("admin", lang),
                    callback_data="admin_panel"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    @check_single_session
    def is_user_subscribed(user_id: int) -> bool:
        """Check if user has active subscription"""
        db = BaseHandler.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Check if subscription is active and not expired
            from datetime import datetime
            if user.is_subscribed and user.subscription_expiry:
                return user.subscription_expiry > datetime.now()
            
            return user.is_subscribed
        finally:
            db.close()
    
    @staticmethod
    @check_single_session
    def is_admin(user_id: int) -> bool:
        """Check if user is admin"""
        db = BaseHandler.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user.is_admin if user else False
        finally:
            db.close()
