"""
Main bot application for HOT SHARK Bot
"""
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from app.config import Config
from app.handlers.start import StartHandler
from app.handlers.callback import CallbackHandler
from app.handlers.admin import AdminHandler
from app.handlers.reports import ReportsHandler
from app.handlers.catalog import CatalogHandler
from app.handlers.preferences import toggle_recommendations, manage_paused_pairs, toggle_pair, toggle_news, manage_news_preferences, toggle_impact
from app.models.database import create_tables
from app.services.scheduler_service import SchedulerService
from app.services.market_monitor_service import MarketMonitorService
from app.handlers.trade_interaction import entered_trade_callback, update_trade_callback

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class HotSharkBot:
    def __init__(self):
        self.application = None
        self.scheduler = None
        self.market_monitor = None
        self.setup_bot()
    
    def setup_bot(self):
        """Setup the bot application"""
        # Create database tables
        create_tables()
        
        # Create application
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Setup scheduler
        self.scheduler = SchedulerService(self.application.bot)
        
        # Setup market monitor
        self.market_monitor = MarketMonitorService(self.application.bot)
        
        # Add handlers
        self.add_handlers()
    
    def add_handlers(self):
        """Add command and callback handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", StartHandler.start))
        self.application.add_handler(CommandHandler("admin", AdminHandler.admin_panel))
        self.application.add_handler(CommandHandler("report", ReportsHandler.send_report_command))
        self.application.add_handler(CommandHandler("catalog", CatalogHandler.handle_catalog_command))
        
        # Admin command handlers
        self.application.add_handler(CommandHandler("add_subscription", AdminHandler.add_user_subscription))
        self.application.add_handler(CommandHandler("remove_subscription", AdminHandler.remove_user_subscription))
        self.application.add_handler(CommandHandler("send_rec", self.send_recommendation_command))
        self.application.add_handler(CommandHandler("send_news", self.send_news_command))
        self.application.add_handler(CommandHandler("update_trade", self.update_trade_command))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(
            CallbackHandler.handle_callback,
            pattern="^(login|logout|change_language|reports|settings).*"
        ))
        
        # Catalog callback handlers
        self.application.add_handler(CallbackQueryHandler(
            CatalogHandler.show_catalog_menu,
            pattern="^catalog_menu$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            CatalogHandler.show_market_schedule,
            pattern="^catalog_market_schedule$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            CatalogHandler.show_liquidity_schedule,
            pattern="^catalog_liquidity_schedule$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            CatalogHandler.show_news_calendar,
            pattern="^catalog_news_calendar$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            CatalogHandler.show_trading_pairs,
            pattern="^catalog_trading_pairs$"
        ))
        
        # Trade interaction handlers
        self.application.add_handler(CallbackQueryHandler(entered_trade_callback, pattern=r"^entered_\d+$"))
        self.application.add_handler(CallbackQueryHandler(update_trade_callback, pattern=r"^update_\d+$"))
        
        # Preferences handlers
        self.application.add_handler(CallbackQueryHandler(toggle_recommendations, pattern="^toggle_recommendations$"))
        self.application.add_handler(CallbackQueryHandler(manage_paused_pairs, pattern="^manage_paused_pairs$"))
        self.application.add_handler(CallbackQueryHandler(toggle_pair, pattern="^toggle_pair_.*$"))
        self.application.add_handler(CallbackQueryHandler(toggle_news, pattern="^toggle_news$"))
        self.application.add_handler(CallbackQueryHandler(manage_news_preferences, pattern="^manage_news_preferences$"))
        self.application.add_handler(CallbackQueryHandler(toggle_impact, pattern="^toggle_impact_.*$"))
        
        # Admin handlers
        self.application.add_handler(CallbackQueryHandler(
            AdminHandler.handle_admin_callback,
            pattern="^admin_.*"
        ))

    async def send_recommendation_command(self, update, context):
        """Handle /send_rec command"""
        if not AdminHandler.is_admin(update.effective_user.id):
            await update.message.reply_text("غير مخول لتنفيذ هذا الأمر.")
            return
        
        if len(context.args) < 8:
            await update.message.reply_text(
                "الاستخدام: /send_rec [pair] [type] [entry] [tp] [sl] [pips] [success_rate] [duration] [rr] [lot] [premium] [strategy] [live]\n"
                "مثال: /send_rec XAUUSD BUY 1950,1948 1960,1965 1945 15 85 short 1:2 0.01 premium ICT_BOS live"
            )
            return
        
        try:
            from app.handlers.recommendation import RecommendationHandler
            
            # Parse arguments
            asset_pair = context.args[0]
            trade_type = context.args[1].upper()
            entry_points = [float(x) for x in context.args[2].split(",")]
            tp_levels = [float(x) for x in context.args[3].split(",")]
            sl = float(context.args[4])
            pips = int(context.args[5])
            success_rate = float(context.args[6]) if context.args[6] != 'None' else None
            trade_duration = context.args[7]
            rr_ratio = context.args[8]
            lot_size_per_100 = float(context.args[9])
            is_premium = context.args[10].lower() == 'premium' if len(context.args) > 10 else False
            strategy = context.args[11] if len(context.args) > 11 and context.args[11] != 'None' else None
            is_live = context.args[12].lower() == 'live' if len(context.args) > 12 else True
            
            # Send recommendation
            await RecommendationHandler.send_recommendation_to_all(
                bot=self.application.bot,
                asset_pair=asset_pair,
                trade_type=trade_type,
                entry_points=entry_points,
                tp_levels=tp_levels,
                sl=sl,
                pips=pips,
                success_rate=success_rate,
                trade_duration=trade_duration,
                rr_ratio=rr_ratio,
                lot_size_per_100=lot_size_per_100,
                is_premium=is_premium,
                strategy=strategy,
                is_live=is_live
            )
            
            await update.message.reply_text("✅ تم إرسال التوصية لجميع المشتركين!")
            
        except Exception as e:
            await update.message.reply_text(f"خطأ في إرسال التوصية: {str(e)}")

    async def send_news_command(self, update, context):
        """Handle /send_news command"""
        if not AdminHandler.is_admin(update.effective_user.id):
            await update.message.reply_text("غير مخول لتنفيذ هذا الأمر.")
            return
        
        if len(context.args) < 3:
            await update.message.reply_text(
                'الاستخدام: /send_news "العنوان" "YYYY-MM-DD HH:MM" [العملة] [التأثير] ["الوصف"] [حرج]\n'
                'مثال: /send_news "بيانات التضخم الأمريكي" "2024-01-15 14:30" USD high "بيانات مهمة" critical'
            )
            return
        
        try:
            from datetime import datetime
            from app.services.news_service import NewsService
            from app.models.user import User
            from app.models.database import SessionLocal
            
            # Parse arguments
            title = context.args[0].strip('"')
            time_str = context.args[1].strip('"')
            news_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            currency = context.args[2] if len(context.args) > 2 and context.args[2] != 'None' else None
            impact = context.args[3] if len(context.args) > 3 else "medium"
            description = context.args[4].strip('"') if len(context.args) > 4 and context.args[4] != 'None' else None
            is_critical = context.args[5].lower() == 'critical' if len(context.args) > 5 else False
            
            # Create news
            news = NewsService.create_news(
                title=title,
                time=news_time,
                currency=currency,
                impact=impact,
                description=description,
                is_critical=is_critical
            )
            
            # Send to all subscribed users
            db = SessionLocal()
            try:
                users = db.query(User).filter(User.is_subscribed == True).all()
                
                for user in users:
                    try:
                        message = NewsService.format_news_alert(news, user.lang_code)
                        await self.application.bot.send_message(
                            chat_id=user.id,
                            text=message,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        print(f"Error sending news to user {user.id}: {e}")
            finally:
                db.close()
            
            await update.message.reply_text("✅ تم إرسال الخبر لجميع المشتركين!")
            
        except Exception as e:
            await update.message.reply_text(f"خطأ في إرسال الخبر: {str(e)}")

    async def update_trade_command(self, update, context):
        """Handle /update_trade command"""
        if not AdminHandler.is_admin(update.effective_user.id):
            await update.message.reply_text("غير مخول لتنفيذ هذا الأمر.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("الاستخدام: /update_trade [recommendation_id] [status]")
            return
        
        try:
            from app.handlers.recommendation import RecommendationHandler
            
            recommendation_id = int(context.args[0])
            status = context.args[1]
            
            if status not in ["tp_hit", "sl_hit", "pending", "active"]:
                await update.message.reply_text("الحالة غير صحيحة. استخدم: tp_hit, sl_hit, pending, active")
                return
            
            # Update recommendation
            await RecommendationHandler.update_recommendation_status(
                bot=self.application.bot,
                recommendation_id=recommendation_id,
                status=status
            )
            
            await update.message.reply_text(f"✅ تم تحديث حالة الصفقة {recommendation_id} إلى {status}")
            
        except Exception as e:
            await update.message.reply_text(f"خطأ في تحديث الصفقة: {str(e)}")
    
    async def setup_webhook(self):
        """Setup webhook for the bot"""
        if Config.TELEGRAM_WEBHOOK_URL and Config.TELEGRAM_BOT_TOKEN != "your_bot_token_here":
            try:
                await self.application.bot.set_webhook(
                    url=f"{Config.TELEGRAM_WEBHOOK_URL}/webhook/{Config.TELEGRAM_BOT_TOKEN}"
                )
                logger.info(f"Webhook set to: {Config.TELEGRAM_WEBHOOK_URL}")
            except Exception as e:
                logger.warning(f"Failed to set webhook: {e}")
        else:
            logger.info("Webhook not configured (running in development mode)")
    
    def start_scheduler(self):
        """Start the scheduler"""
        if self.scheduler:
            self.scheduler.start()
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.stop()
    
    async def start_market_monitor(self):
        """Start 24/7 market monitoring"""
        if self.market_monitor:
            await self.market_monitor.start_monitoring()
    
    async def stop_market_monitor(self):
        """Stop market monitoring"""
        if self.market_monitor:
            await self.market_monitor.stop_monitoring()
    
    def get_application(self):
        """Get the bot application"""
        return self.application

# Global bot instance
bot = HotSharkBot()