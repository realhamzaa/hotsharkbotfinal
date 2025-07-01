"""
Catalog Handler for HOT SHARK Bot
Handles catalog-related commands and callbacks
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram import Update
from app.services.catalog_service import CatalogService
from app.utils.localization import get_text
from app.models.user import User
from app.models.database import SessionLocal

class CatalogHandler:
    """Handler for catalog-related functionality"""
    
    @staticmethod
    async def show_catalog_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show catalog main menu"""
        query = update.callback_query
        if query:
            await query.answer()
            user_id = query.from_user.id
        else:
            user_id = update.effective_user.id
        
        # Get user language
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            lang_code = user.lang_code if user else 'ar'
        finally:
            db.close()
        
        # Create catalog menu
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text('market_schedule', lang_code),
                    callback_data='catalog_market_schedule'
                )
            ],
            [
                InlineKeyboardButton(
                    get_text('liquidity_schedule', lang_code),
                    callback_data='catalog_liquidity_schedule'
                )
            ],
            [
                InlineKeyboardButton(
                    get_text('news_calendar', lang_code),
                    callback_data='catalog_news_calendar'
                )
            ],
            [
                InlineKeyboardButton(
                    get_text('trading_pairs', lang_code),
                    callback_data='catalog_trading_pairs'
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
        
        message_text = f"📚 {get_text('catalog_menu', lang_code)}\n\n"
        message_text += get_text('catalog_menu_description', lang_code)
        
        if query:
            await query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=message_text,
                reply_markup=reply_markup
            )
    
    @staticmethod
    async def show_market_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show market opening schedule"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Get user language
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            lang_code = user.lang_code if user else 'ar'
        finally:
            db.close()
        
        # Get market schedule
        schedule_text = CatalogService.get_market_schedule(lang_code)
        
        # Back button
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text('back', lang_code),
                    callback_data='catalog_menu'
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=schedule_text,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def show_liquidity_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show high liquidity periods schedule"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Get user language
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            lang_code = user.lang_code if user else 'ar'
        finally:
            db.close()
        
        # Get liquidity schedule
        schedule_text = CatalogService.get_liquidity_schedule(lang_code)
        
        # Back button
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text('back', lang_code),
                    callback_data='catalog_menu'
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=schedule_text,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def show_news_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show economic news calendar"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Get user language
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            lang_code = user.lang_code if user else 'ar'
        finally:
            db.close()
        
        # Get news calendar
        calendar_text = CatalogService.get_news_calendar(lang_code)
        
        # Back button
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text('back', lang_code),
                    callback_data='catalog_menu'
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=calendar_text,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def show_trading_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show supported trading pairs information"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Get user language
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            lang_code = user.lang_code if user else 'ar'
        finally:
            db.close()
        
        # Get trading pairs info
        pairs_text = CatalogService.get_trading_pairs_info(lang_code)
        
        # Back button
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text('back', lang_code),
                    callback_data='catalog_menu'
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=pairs_text,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_catalog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /catalog command"""
        await CatalogHandler.show_catalog_menu(update, context)

