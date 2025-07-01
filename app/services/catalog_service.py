"""
Catalog Service for HOT SHARK Bot
Provides market schedules, news calendar, and liquidity information
"""
from datetime import datetime, timedelta
import pytz
from typing import Dict, List
from app.utils.localization import get_text

class CatalogService:
    """Service for providing market information catalogs"""
    
    # Market sessions in GMT
    MARKET_SESSIONS = {
        'sydney': {'open': '21:00', 'close': '06:00', 'timezone': 'Australia/Sydney'},
        'tokyo': {'open': '23:00', 'close': '08:00', 'timezone': 'Asia/Tokyo'},
        'london': {'open': '07:00', 'close': '16:00', 'timezone': 'Europe/London'},
        'new_york': {'open': '12:00', 'close': '21:00', 'timezone': 'America/New_York'}
    }
    
    # High liquidity periods (GMT)
    HIGH_LIQUIDITY_PERIODS = [
        {'name': 'London Open', 'time': '07:00', 'duration': 2},
        {'name': 'London-NY Overlap', 'time': '12:00', 'duration': 4},
        {'name': 'NY Open', 'time': '12:00', 'duration': 2},
        {'name': 'Asian Session', 'time': '23:00', 'duration': 3}
    ]
    
    @classmethod
    def get_market_schedule(cls, lang_code: str = 'ar') -> str:
        """Get formatted market opening schedule"""
        now_gmt = datetime.now(pytz.UTC)
        palestine_tz = pytz.timezone('Asia/Gaza')
        now_palestine = now_gmt.astimezone(palestine_tz)
        
        schedule_text = f"📅 {get_text('market_schedule', lang_code)}\n\n"
        
        # Market sessions
        sessions = [
            ('🇦🇺 Sydney', '21:00 - 06:00 GMT', '12:00 AM - 9:00 AM Palestine'),
            ('🇯🇵 Tokyo', '23:00 - 08:00 GMT', '2:00 AM - 11:00 AM Palestine'),
            ('🇬🇧 London', '07:00 - 16:00 GMT', '10:00 AM - 7:00 PM Palestine'),
            ('🇺🇸 New York', '12:00 - 21:00 GMT', '3:00 PM - 12:00 AM Palestine')
        ]
        
        for session_name, gmt_time, palestine_time in sessions:
            schedule_text += f"{session_name}\n"
            schedule_text += f"⏰ GMT: {gmt_time}\n"
            schedule_text += f"🇵🇸 Palestine: {palestine_time}\n\n"
        
        # Current time
        schedule_text += f"🕐 {get_text('current_time', lang_code)}:\n"
        schedule_text += f"GMT: {now_gmt.strftime('%H:%M')}\n"
        schedule_text += f"Palestine: {now_palestine.strftime('%I:%M %p')}\n\n"
        
        # Next market opening
        next_opening = cls._get_next_market_opening()
        if next_opening:
            schedule_text += f"🔔 {get_text('next_market_opening', lang_code)}: {next_opening}\n"
        
        return schedule_text
    
    @classmethod
    def get_liquidity_schedule(cls, lang_code: str = 'ar') -> str:
        """Get high liquidity periods schedule"""
        schedule_text = f"💧 {get_text('high_liquidity_periods', lang_code)}\n\n"
        
        for period in cls.HIGH_LIQUIDITY_PERIODS:
            # Convert GMT to Palestine time
            gmt_time = datetime.strptime(period['time'], '%H:%M').time()
            palestine_time = cls._convert_gmt_to_palestine(gmt_time)
            
            schedule_text += f"🔥 {period['name']}\n"
            schedule_text += f"⏰ GMT: {period['time']} ({period['duration']}h)\n"
            schedule_text += f"🇵🇸 Palestine: {palestine_time.strftime('%I:%M %p')} ({period['duration']}h)\n\n"
        
        # Current liquidity status
        current_liquidity = cls._get_current_liquidity_status()
        schedule_text += f"📊 {get_text('current_liquidity', lang_code)}: {current_liquidity}\n"
        
        return schedule_text
    
    @classmethod
    def get_news_calendar(cls, lang_code: str = 'ar') -> str:
        """Get economic news calendar for today"""
        from app.models.news import News
        from app.models.database import SessionLocal
        
        db = SessionLocal()
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            # Get today's news
            today_news = db.query(News).filter(
                News.time >= today,
                News.time < tomorrow
            ).order_by(News.time).all()
            
            calendar_text = f"📰 {get_text('news_calendar', lang_code)} - {today.strftime('%Y-%m-%d')}\n\n"
            
            if not today_news:
                calendar_text += f"{get_text('no_news_today', lang_code)}\n"
                return calendar_text
            
            for news in today_news:
                # Convert to Palestine time
                palestine_time = news.time.astimezone(pytz.timezone('Asia/Gaza'))
                
                impact_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🔴'
                }.get(news.impact, '⚪')
                
                critical_emoji = '🚨' if news.is_critical else ''
                
                calendar_text += f"{impact_emoji} {critical_emoji} {news.title}\n"
                calendar_text += f"⏰ {palestine_time.strftime('%I:%M %p')} Palestine\n"
                calendar_text += f"💱 {news.currency or 'Multiple'}\n"
                
                if news.description:
                    calendar_text += f"📝 {news.description}\n"
                
                calendar_text += "\n"
            
            return calendar_text
            
        finally:
            db.close()
    
    @classmethod
    def get_trading_pairs_info(cls, lang_code: str = 'ar') -> str:
        """Get information about supported trading pairs"""
        pairs_info = f"📈 {get_text('supported_pairs', lang_code)}\n\n"
        
        pairs = [
            ('🥇 XAUUSD', 'Gold vs US Dollar', 'Precious Metal'),
            ('₿ BTCUSD', 'Bitcoin vs US Dollar', 'Cryptocurrency'),
            ('⟠ ETHUSD', 'Ethereum vs US Dollar', 'Cryptocurrency'),
            ('🇪🇺 EURUSD', 'Euro vs US Dollar', 'Major Pair'),
            ('🇬🇧 GBPJPY', 'British Pound vs Japanese Yen', 'Cross Pair'),
            ('🇬🇧 GBPUSD', 'British Pound vs US Dollar', 'Major Pair'),
            ('🇺🇸 USDJPY', 'US Dollar vs Japanese Yen', 'Major Pair'),
            ('📊 US30', 'Dow Jones Industrial Average', 'Index'),
            ('💻 US100', 'NASDAQ 100', 'Index')
        ]
        
        for symbol, description, category in pairs:
            pairs_info += f"{symbol}\n"
            pairs_info += f"📋 {description}\n"
            pairs_info += f"🏷️ {category}\n\n"
        
        return pairs_info
    
    @classmethod
    def _get_next_market_opening(cls) -> str:
        """Get next market opening time"""
        now_gmt = datetime.now(pytz.UTC)
        
        # Check each market session
        for market, times in cls.MARKET_SESSIONS.items():
            open_time = datetime.strptime(times['open'], '%H:%M').time()
            open_datetime = datetime.combine(now_gmt.date(), open_time)
            open_datetime = pytz.UTC.localize(open_datetime)
            
            # If opening time is in the future today
            if open_datetime > now_gmt:
                palestine_time = open_datetime.astimezone(pytz.timezone('Asia/Gaza'))
                return f"{market.title()} - {palestine_time.strftime('%I:%M %p')} Palestine"
        
        # If no opening today, check tomorrow
        tomorrow = now_gmt.date() + timedelta(days=1)
        for market, times in cls.MARKET_SESSIONS.items():
            open_time = datetime.strptime(times['open'], '%H:%M').time()
            open_datetime = datetime.combine(tomorrow, open_time)
            open_datetime = pytz.UTC.localize(open_datetime)
            palestine_time = open_datetime.astimezone(pytz.timezone('Asia/Gaza'))
            return f"{market.title()} (Tomorrow) - {palestine_time.strftime('%I:%M %p')} Palestine"
        
        return "Unknown"
    
    @classmethod
    def _convert_gmt_to_palestine(cls, gmt_time) -> datetime.time:
        """Convert GMT time to Palestine time"""
        # Palestine is GMT+2 (GMT+3 during DST)
        gmt_datetime = datetime.combine(datetime.now().date(), gmt_time)
        gmt_datetime = pytz.UTC.localize(gmt_datetime)
        palestine_datetime = gmt_datetime.astimezone(pytz.timezone('Asia/Gaza'))
        return palestine_datetime.time()
    
    @classmethod
    def _get_current_liquidity_status(cls) -> str:
        """Get current market liquidity status"""
        now_gmt = datetime.now(pytz.UTC).time()
        
        for period in cls.HIGH_LIQUIDITY_PERIODS:
            start_time = datetime.strptime(period['time'], '%H:%M').time()
            end_time = (datetime.combine(datetime.now().date(), start_time) + 
                       timedelta(hours=period['duration'])).time()
            
            if start_time <= now_gmt <= end_time:
                return f"🔥 High ({period['name']})"
        
        return "🟡 Normal"

