"""
Reports handler for HOT SHARK Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.handlers.base import BaseHandler
from app.services.report_service import ReportService
from app.utils.localization import loc

class ReportsHandler(BaseHandler):
    @staticmethod
    async def handle_report_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report request callback"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        lang = BaseHandler.get_user_language(user_id)
        
        # Check if user is subscribed
        if not BaseHandler.is_user_subscribed(user_id):
            text = loc.get_text("subscription_expired", lang)
            await query.edit_message_text(text)
            return
        
        data = query.data
        
        if data == "report_daily":
            await ReportsHandler.generate_daily_report(query, user_id, lang)
        elif data == "report_weekly":
            await ReportsHandler.generate_weekly_report(query, user_id, lang)
        elif data == "report_monthly":
            await ReportsHandler.generate_monthly_report(query, user_id, lang)
    
    @staticmethod
    async def generate_daily_report(query, user_id: int, lang: str):
        """Generate and send daily report"""
        try:
            # Generate report
            report = ReportService.generate_user_report(user_id, "daily")
            
            # Format message
            message = ReportService.format_report_message(report, lang)
            
            # Create back button
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔙 العودة" if lang == "ar" else "🔙 Back",
                        callback_data="reports"
                    )
                ]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            error_text = "حدث خطأ في إنشاء التقرير" if lang == "ar" else "Error generating report"
            await query.edit_message_text(f"{error_text}: {str(e)}")
    
    @staticmethod
    async def generate_weekly_report(query, user_id: int, lang: str):
        """Generate and send weekly report"""
        try:
            # Generate report
            report = ReportService.generate_user_report(user_id, "weekly")
            
            # Format message
            message = ReportService.format_report_message(report, lang)
            
            # Create back button
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔙 العودة" if lang == "ar" else "🔙 Back",
                        callback_data="reports"
                    )
                ]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            error_text = "حدث خطأ في إنشاء التقرير" if lang == "ar" else "Error generating report"
            await query.edit_message_text(f"{error_text}: {str(e)}")
    
    @staticmethod
    async def generate_monthly_report(query, user_id: int, lang: str):
        """Generate and send monthly report"""
        try:
            # Generate report
            report = ReportService.generate_user_report(user_id, "monthly")
            
            # Format message
            message = ReportService.format_report_message(report, lang)
            
            # Create back button
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔙 العودة" if lang == "ar" else "🔙 Back",
                        callback_data="reports"
                    )
                ]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            error_text = "حدث خطأ في إنشاء التقرير" if lang == "ar" else "Error generating report"
            await query.edit_message_text(f"{error_text}: {str(e)}")
    
    @staticmethod
    async def send_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command"""
        user_id = update.effective_user.id
        lang = BaseHandler.get_user_language(user_id)
        
        # Check if user is subscribed
        if not BaseHandler.is_user_subscribed(user_id):
            text = loc.get_text("subscription_expired", lang)
            await update.message.reply_text(text)
            return
        
        # Check if report type is specified
        if len(context.args) == 0:
            # Show report options
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
                ]
            ]
            
            text = "📊 اختر نوع التقرير:" if lang == "ar" else "📊 Choose report type:"
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Generate specific report type
            report_type = context.args[0].lower()
            
            if report_type not in ["daily", "weekly", "monthly"]:
                error_text = "نوع التقرير غير صحيح. استخدم: daily, weekly, monthly" if lang == "ar" else "Invalid report type. Use: daily, weekly, monthly"
                await update.message.reply_text(error_text)
                return
            
            try:
                # Generate report
                report = ReportService.generate_user_report(user_id, report_type)
                
                # Format and send message
                message = ReportService.format_report_message(report, lang)
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                error_text = "حدث خطأ في إنشاء التقرير" if lang == "ar" else "Error generating report"
                await update.message.reply_text(f"{error_text}: {str(e)}")

