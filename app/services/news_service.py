"""
News service for HOT SHARK Bot
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.news import News
from app.utils.localization import loc
from app.utils.timezone_utils import get_palestine_time, get_gmt_time

class NewsService:
    @staticmethod
    def create_news(
        title: str,
        time: datetime,
        currency: str = None,
        impact: str = "medium",
        description: str = None,
        is_critical: bool = False
    ) -> News:
        """Create a new news entry."""
        db = SessionLocal()
        try:
            news = News(
                title=title,
                time=time,
                currency=currency,
                impact=impact,
                description=description,
                is_critical=is_critical
            )
            db.add(news)
            db.commit()
            db.refresh(news)
            return news
        finally:
            db.close()

    @staticmethod
    def get_upcoming_news(minutes_ahead: int = 60) -> list[News]:
        """Get upcoming news within a specified time frame."""
        db = SessionLocal()
        try:
            now = datetime.now()
            future_time = now + timedelta(minutes=minutes_ahead)
            return db.query(News).filter(News.time > now, News.time <= future_time).all()
        finally:
            db.close()

    @staticmethod
    def format_news_alert(news: News, lang: str) -> str:
        """Format news alert message for Telegram."""
        palestine_time = news.time.astimezone(get_palestine_time().tzinfo).strftime("%I:%M %p")
        gmt_time = news.time.astimezone(get_gmt_time().tzinfo).strftime("%H:%M")

        impact_emoji = "🔴" if news.impact == "high" else "🟠" if news.impact == "medium" else "⚪"
        critical_emoji = "🚨" if news.is_critical else ""

        message = loc.get_text("news_alert_message", lang).format(
            title=news.title,
            time_palestine=palestine_time,
            time_gmt=gmt_time,
            currency=news.currency if news.currency else loc.get_text("not_specified", lang),
            impact=loc.get_text(f"impact_{news.impact}", lang),
            impact_emoji=impact_emoji,
            critical_emoji=critical_emoji
        )
        if news.description:
            description_label = "الوصف" if lang == "ar" else "Description"
            message += f"\n\n{description_label}: {news.description}"
        return message

    @staticmethod
    def get_news_by_id(news_id: int) -> News:
        """Get news by ID."""
        db = SessionLocal()
        try:
            return db.query(News).filter(News.id == news_id).first()
        finally:
            db.close()

    @staticmethod
    def update_news_status(news_id: int, status: str) -> bool:
        """Update news status (e.g., sent)."""
        db = SessionLocal()
        try:
            news = db.query(News).filter(News.id == news_id).first()
            if news:
                news.status = status
                db.add(news)
                db.commit()
                db.refresh(news)
                return True
            return False
        finally:
            db.close()

    @staticmethod
    def get_all_news() -> list[News]:
        """Get all news entries."""
        db = SessionLocal()
        try:
            return db.query(News).order_by(News.time.desc()).all()
        finally:
            db.close()

    @staticmethod
    def delete_news(news_id: int) -> bool:
        """Delete a news entry."""
        db = SessionLocal()
        try:
            news = db.query(News).filter(News.id == news_id).first()
            if news:
                db.delete(news)
                db.commit()
                return True
            return False
        finally:
            db.close()


