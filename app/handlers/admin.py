"""
Admin handler for HOT SHARK Bot
"""
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.handlers.base import BaseHandler
from app.handlers.recommendation import RecommendationHandler
from app.services.news_service import NewsService
from app.models.user import User
from app.models.subscription import Subscription
from app.models.database import SessionLocal
from app.utils.localization import loc

class AdminHandler(BaseHandler):
    @staticmethod
    async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel"""
        user_id = update.effective_user.id
        
        if not BaseHandler.is_admin(user_id):
            await update.message.reply_text("غير مخول للوصول إلى لوحة الإدارة.")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("📊 إرسال توصية", callback_data="admin_send_recommendation"),
                InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_manage_users")
            ],
            [
                InlineKeyboardButton("📰 إرسال خبر", callback_data="admin_send_news"),
                InlineKeyboardButton("📈 تحديث صفقة", callback_data="admin_update_trade")
            ],
            [
                InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats"),
                InlineKeyboardButton("⚙️ إعدادات", callback_data="admin_settings")
            ]
        ]
        
        await update.message.reply_text(
            "👨‍💼 **لوحة الإدارة**\n\nاختر العملية المطلوبة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    @staticmethod
    async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin callback queries"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if not BaseHandler.is_admin(user_id):
            await query.edit_message_text("غير مخول للوصول إلى هذه الميزة.")
            return
        
        data = query.data
        
        if data == "admin_send_recommendation":
            await AdminHandler.show_recommendation_form(query)
        elif data == "admin_manage_users":
            await AdminHandler.show_user_management(query)
        elif data == "admin_send_news":
            await AdminHandler.show_news_form(query)
        elif data == "admin_update_trade":
            await AdminHandler.show_trade_update_form(query)
        elif data == "admin_stats":
            await AdminHandler.show_statistics(query)
        elif data == "admin_settings":
            await AdminHandler.show_settings(query)
    
    @staticmethod
    async def show_recommendation_form(query):
        """Show recommendation creation form"""
        text = """
📊 **إرسال توصية جديدة**

لإرسال توصية، استخدم الأمر التالي:

`/send_rec XAUUSD BUY 1950,1948 1960,1965 1945 15 85 short 1:2 0.01 premium ICT_BOS live`

**المعاملات:**
• زوج العملة (مثل XAUUSD)
• نوع الصفقة (BUY/SELL)
• نقاط الدخول (مفصولة بفاصلة)
• أهداف الربح (مفصولة بفاصلة)
• وقف الخسارة
• عدد النقاط
• نسبة النجاح (اختياري)
• مدة الصفقة (scalp/short/long)
• نسبة R:R
• حجم اللوت لكل 100$
• نوع الصفقة (premium/normal)
• الاستراتيجية (اختياري)
• نوع التنفيذ (live/pending)
"""
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def show_user_management(query):
        """Show user management interface"""
        db = SessionLocal()
        try:
            # Get user statistics
            total_users = db.query(User).count()
            subscribed_users = db.query(User).filter(User.is_subscribed == True).count()
            
            text = f"""
👥 **إدارة المستخدمين**

📊 **الإحصائيات:**
• إجمالي المستخدمين: {total_users}
• المشتركين النشطين: {subscribed_users}

**الأوامر المتاحة:**
• `/add_subscription [user_id] [days]` - إضافة اشتراك
• `/remove_subscription [user_id]` - إلغاء اشتراك
• `/user_info [user_id]` - معلومات المستخدم
• `/list_users` - قائمة المستخدمين
"""
            
            await query.edit_message_text(text, parse_mode='Markdown')
        finally:
            db.close()
    
    @staticmethod
    async def show_news_form(query):
        """Show news creation form"""
        text = """
📰 **إرسال خبر جديد**

لإرسال خبر، استخدم الأمر التالي:

`/send_news "عنوان الخبر" "2024-01-15 14:30" USD high "وصف الخبر" critical`

**المعاملات:**
• عنوان الخبر (بين علامتي اقتباس)
• وقت الخبر (YYYY-MM-DD HH:MM)
• العملة المتأثرة (اختياري)
• مستوى التأثير (low/medium/high)
• وصف الخبر (اختياري، بين علامتي اقتباس)
• هل الخبر حرج؟ (critical أو عادي)
"""
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def show_trade_update_form(query):
        """Show trade update form"""
        text = """
📈 **تحديث حالة الصفقة**

لتحديث حالة صفقة، استخدم الأمر التالي:

`/update_trade [recommendation_id] [status]`

**الحالات المتاحة:**
• `tp_hit` - تم تحقيق الهدف
• `sl_hit` - تم ضرب وقف الخسارة
• `pending` - معلقة
• `active` - نشطة

**مثال:**
`/update_trade 123 tp_hit`
"""
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def show_statistics(query):
        """Show bot statistics"""
        db = SessionLocal()
        try:
            # Get various statistics
            total_users = db.query(User).count()
            subscribed_users = db.query(User).filter(User.is_subscribed == True).count()
            
            from app.models.recommendation import Recommendation
            total_recommendations = db.query(Recommendation).count()
            active_recommendations = db.query(Recommendation).filter(
                Recommendation.status == "active"
            ).count()
            
            from app.models.user_trade import UserTrade
            total_trades = db.query(UserTrade).count()
            
            text = f"""
📊 **إحصائيات البوت**

👥 **المستخدمين:**
• إجمالي المستخدمين: {total_users}
• المشتركين النشطين: {subscribed_users}
• معدل الاشتراك: {(subscribed_users/total_users*100):.1f}%

📈 **التوصيات:**
• إجمالي التوصيات: {total_recommendations}
• التوصيات النشطة: {active_recommendations}

💼 **الصفقات:**
• إجمالي الصفقات المدخلة: {total_trades}
"""
            
            await query.edit_message_text(text, parse_mode='Markdown')
        finally:
            db.close()
    
    @staticmethod
    async def show_settings(query):
        """Show bot settings"""
        text = """
⚙️ **إعدادات البوت**

**الأوامر المتاحة:**
• `/set_timezone [timezone]` - تعيين المنطقة الزمنية
• `/toggle_notifications` - تفعيل/إلغاء الإشعارات
• `/backup_db` - نسخ احتياطي لقاعدة البيانات
• `/restart_bot` - إعادة تشغيل البوت

**المناطق الزمنية المدعومة:**
• Asia/Jerusalem (إسرائيل)
• GMT (غرينتش)
• America/New_York (نيويورك)
• Europe/London (لندن)
"""
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def add_user_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add subscription to user"""
        if not BaseHandler.is_admin(update.effective_user.id):
            await update.message.reply_text("غير مخول لتنفيذ هذا الأمر.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("الاستخدام: /add_subscription [user_id] [days]")
            return
        
        try:
            user_id = int(context.args[0])
            days = int(context.args[1])
            
            db = SessionLocal()
            try:
                # Get or create user
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    await update.message.reply_text(f"المستخدم {user_id} غير موجود.")
                    return
                
                # Create subscription
                start_date = datetime.now()
                end_date = start_date + timedelta(days=days)
                
                subscription = Subscription(
                    user_id=user_id,
                    start_date=start_date,
                    end_date=end_date,
                    created_by=update.effective_user.id
                )
                
                # Update user
                user.is_subscribed = True
                user.subscription_expiry = end_date
                
                db.add(subscription)
                db.commit()
                
                await update.message.reply_text(
                    f"✅ تم إضافة اشتراك للمستخدم {user_id} لمدة {days} يوم.\n"
                    f"ينتهي في: {end_date.strftime('%Y-%m-%d %H:%M')}"
                )
            finally:
                db.close()
                
        except ValueError:
            await update.message.reply_text("خطأ في المعاملات. تأكد من أن user_id و days أرقام صحيحة.")
        except Exception as e:
            await update.message.reply_text(f"خطأ: {str(e)}")
    
    @staticmethod
    async def remove_user_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove user subscription"""
        if not BaseHandler.is_admin(update.effective_user.id):
            await update.message.reply_text("غير مخول لتنفيذ هذا الأمر.")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("الاستخدام: /remove_subscription [user_id]")
            return
        
        try:
            user_id = int(context.args[0])
            
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    await update.message.reply_text(f"المستخدم {user_id} غير موجود.")
                    return
                
                # Update user
                user.is_subscribed = False
                user.subscription_expiry = None
                
                # Deactivate current subscriptions
                db.query(Subscription).filter(
                    Subscription.user_id == user_id,
                    Subscription.is_active == True
                ).update({"is_active": False})
                
                db.commit()
                
                await update.message.reply_text(f"✅ تم إلغاء اشتراك المستخدم {user_id}")
            finally:
                db.close()
                
        except ValueError:
            await update.message.reply_text("خطأ في user_id. تأكد من أنه رقم صحيح.")
        except Exception as e:
            await update.message.reply_text(f"خطأ: {str(e)}")

