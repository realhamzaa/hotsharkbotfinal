"""
Scheduler service for HOT SHARK Bot
"""
import asyncio
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from app.config import Config
from app.services.news_service import NewsService
from app.services.report_service import ReportService
from app.models.user import User
from app.models.database import SessionLocal

class SchedulerService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.setup_jobs()
    
    def setup_jobs(self):
        """Setup scheduled jobs"""
        
        # Daily market opening notifications
        self.scheduler.add_job(
            self.send_market_opening_notification,
            CronTrigger(hour=22, minute=0),  # 22:00 GMT (Asian session start)
            id="asian_session_start"
        )
        
        self.scheduler.add_job(
            self.send_market_opening_notification,
            CronTrigger(hour=8, minute=0),   # 08:00 GMT (European session start)
            id="european_session_start"
        )
        
        self.scheduler.add_job(
            self.send_market_opening_notification,
            CronTrigger(hour=13, minute=0),  # 13:00 GMT (American session start)
            id="american_session_start"
        )
        
        # News reminders (check every 10 minutes for upcoming news)
        self.scheduler.add_job(
            self.check_upcoming_news,
            CronTrigger(minute="*/10"),
            id="news_reminder_check"
        )
        
        # Weekly reports (every Saturday at 12:00 GMT)
        self.scheduler.add_job(
            self.generate_weekly_reports,
            CronTrigger(day_of_week=5, hour=12, minute=0),  # Saturday
            id="weekly_reports"
        )
        
        # Daily market schedule notification
        self.scheduler.add_job(
            self.send_daily_market_schedule,
            CronTrigger(hour=6, minute=0),   # 06:00 GMT daily
            id="daily_market_schedule"
        )
    
    async def send_market_opening_notification(self):
        """Send market opening notification"""
        try:
            schedule = NewsService.get_market_schedule()
            
            if schedule["is_market_open"]:
                message = NewsService.format_market_schedule_message("ar")
                
                # Send to all subscribed users
                db = SessionLocal()
                try:
                    users = db.query(User).filter(User.is_subscribed == True).all()
                    
                    for user in users:
                        try:
                            await self.bot.send_message(
                                chat_id=user.id,
                                text=message,
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            print(f"Error sending market notification to user {user.id}: {e}")
                finally:
                    db.close()
        except Exception as e:
            print(f"Error in market opening notification: {e}")
    
    async def check_upcoming_news(self):
        """Check for upcoming news and send reminders"""
        try:
            # Get news in the next hour
            upcoming_news = NewsService.get_news_in_one_hour()
            
            for news in upcoming_news:
                # Send reminder
                message_ar = NewsService.format_news_reminder(news, "ar")
                message_en = NewsService.format_news_reminder(news, "en")
                
                # Send to all subscribed users
                db = SessionLocal()
                try:
                    users = db.query(User).filter(User.is_subscribed == True).all()
                    
                    for user in users:
                        try:
                            message = message_ar if user.lang_code == "ar" else message_en
                            await self.bot.send_message(
                                chat_id=user.id,
                                text=message,
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            print(f"Error sending news reminder to user {user.id}: {e}")
                    
                    # Mark as sent
                    NewsService.mark_news_as_sent(news.id)
                finally:
                    db.close()
        except Exception as e:
            print(f"Error checking upcoming news: {e}")
    
    async def generate_weekly_reports(self):
        """Generate and send weekly reports"""
        try:
            db = SessionLocal()
            try:
                users = db.query(User).filter(User.is_subscribed == True).all()
                
                for user in users:
                    try:
                        # Generate report
                        report = ReportService.generate_user_report(user.id, "weekly")
                        
                        # Format and send message
                        message = ReportService.format_report_message(report, user.lang_code)
                        
                        await self.bot.send_message(
                            chat_id=user.id,
                            text=message,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        print(f"Error generating weekly report for user {user.id}: {e}")
            finally:
                db.close()
        except Exception as e:
            print(f"Error in weekly reports generation: {e}")
    
    async def send_daily_market_schedule(self):
        """Send daily market schedule"""
        try:
            message = NewsService.format_market_schedule_message("ar")
            
            # Send to all subscribed users
            db = SessionLocal()
            try:
                users = db.query(User).filter(User.is_subscribed == True).all()
                
                for user in users:
                    try:
                        user_message = NewsService.format_market_schedule_message(user.lang_code)
                        await self.bot.send_message(
                            chat_id=user.id,
                            text=f"🌅 **جدول السوق اليومي**\n\n{user_message}",
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        print(f"Error sending daily schedule to user {user.id}: {e}")
            finally:
                db.close()
        except Exception as e:
            print(f"Error in daily market schedule: {e}")
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        print("Scheduler started successfully!")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("Scheduler stopped!")
    
    def add_custom_job(self, func, trigger, job_id: str, **kwargs):
        """Add a custom job to the scheduler"""
        self.scheduler.add_job(func, trigger, id=job_id, **kwargs)
    
    def remove_job(self, job_id: str):
        """Remove a job from the scheduler"""
        try:
            self.scheduler.remove_job(job_id)
        except Exception as e:
            print(f"Error removing job {job_id}: {e}")
    
    def list_jobs(self):
        """List all scheduled jobs"""
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            print(f"Job ID: {job.id}, Next run: {job.next_run_time}")
        return jobs

