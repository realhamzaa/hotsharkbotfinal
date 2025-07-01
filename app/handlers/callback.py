"""
Callback query handler for HOT SHARK Bot
"""
from telegram import Update
from telegram.ext import ContextTypes
from app.handlers.base import BaseHandler
from app.handlers.session_handler import SessionHandler
from app.utils.localization import loc
from app.models.user import User

class CallbackHandler(BaseHandler):
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        lang = BaseHandler.get_user_language(user_id)
        data = query.data
        
        if data == "login":
            await SessionHandler.handle_login(update, context)
        elif data == "logout":
            await SessionHandler.handle_logout(update, context)
        elif data == "force_login":
            await SessionHandler.handle_force_login(update, context)
        elif data == "change_language":
            await CallbackHandler.handle_language_change(query, user_id)
        elif data == "reports":
            await CallbackHandler.handle_reports(query, lang)
        elif data == "settings":
            await CallbackHandler.handle_settings(query, lang)
        elif data == "main_menu":
            await CallbackHandler.handle_main_menu(query, user_id, lang)
        elif data == "admin_panel":
            await CallbackHandler.handle_admin_panel(query, user_id, lang)
        elif data.startswith("enter_trade_"):
            await CallbackHandler.handle_enter_trade(query, data, user_id, lang)
        elif data.startswith("update_trade_"):
            await CallbackHandler.handle_update_trade(query, data, user_id, lang)
    
    @staticmethod
    async def handle_main_menu(query, user_id: int, lang: str):
        """Handle main menu callback"""
        keyboard = BaseHandler.create_main_keyboard(lang)
        
        # Add admin keyboard if user is admin
        if BaseHandler.is_admin(user_id):
            admin_keyboard = BaseHandler.create_admin_keyboard(lang)
            keyboard.inline_keyboard.extend(admin_keyboard.inline_keyboard)
        
        welcome_text = loc.get_text("welcome", lang)
        await query.edit_message_text(welcome_text, reply_markup=keyboard)
    
    @staticmethod
    async def handle_language_change(query, user_id: int):
        """Handle language change callback"""
        db = BaseHandler.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # Toggle language
                new_lang = "en" if user.lang_code == "ar" else "ar"
                user.lang_code = new_lang
                db.commit()
                
                text = loc.get_text("language_changed", new_lang)
                keyboard = BaseHandler.create_main_keyboard(new_lang)
                
                # Add admin keyboard if user is admin
                if BaseHandler.is_admin(user_id):
                    admin_keyboard = BaseHandler.create_admin_keyboard(new_lang)
                    keyboard.inline_keyboard.extend(admin_keyboard.inline_keyboard)
                
                await query.edit_message_text(text, reply_markup=keyboard)
        finally:
            db.close()
    
    @staticmethod
    async def handle_reports(query, lang: str):
        """Handle reports callback"""
        # Create reports keyboard
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton(
                    loc.get_keyboard_text("daily_report", lang),
                    callback_data="report_daily"
                )
            ],
            [
                InlineKeyboardButton(
                    loc.get_keyboard_text("weekly_report", lang),
                    callback_data="report_weekly"
                )
            ],
            [
                InlineKeyboardButton(
                    loc.get_keyboard_text("monthly_report", lang),
                    callback_data="report_monthly"
                )
            ],
            [
                InlineKeyboardButton(
                    loc.get_text("back", lang),
                    callback_data="main_menu"
                )
            ]
        ]
        
        await query.edit_message_text(
            "📊 اختر نوع التقرير:" if lang == "ar" else "📊 Choose report type:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def handle_settings(query, lang: str):
        """Handle settings callback"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton(
                    loc.get_text("back", lang),
                    callback_data="main_menu"
                )
            ]
        ]
        
        text = "⚙️ الإعدادات قيد التطوير" if lang == "ar" else "⚙️ Settings under development"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    @staticmethod
    async def handle_admin_panel(query, user_id: int, lang: str):
        """Handle admin panel callback"""
        if not BaseHandler.is_admin(user_id):
            text = loc.get_text("not_authorized", lang)
            await query.edit_message_text(text)
            return
        
        text = loc.get_text("admin_panel", lang)
        await query.edit_message_text(text)
    
    @staticmethod
    async def handle_enter_trade(query, data: str, user_id: int, lang: str):
        """Handle enter trade callback"""
        # Extract recommendation ID from callback data
        recommendation_id = int(data.split("_")[-1])
        
        # Record user trade entry
        from app.models.user_trade import UserTrade
        db = BaseHandler.get_db()
        try:
            # Check if user already entered this trade
            existing_trade = db.query(UserTrade).filter(
                UserTrade.user_id == user_id,
                UserTrade.recommendation_id == recommendation_id
            ).first()
            
            if not existing_trade:
                trade = UserTrade(
                    user_id=user_id,
                    recommendation_id=recommendation_id
                )
                db.add(trade)
                db.commit()
            
            text = loc.get_text("trade_entered", lang)
            await query.edit_message_text(text)
        finally:
            db.close()
    
    @staticmethod
    async def handle_update_trade(query, data: str, user_id: int, lang: str):
        """Handle update trade callback"""
        # Extract recommendation ID from callback data
        recommendation_id = int(data.split("_")[-1])
        
        text = loc.get_text("trade_updated", lang)
        await query.edit_message_text(text)

