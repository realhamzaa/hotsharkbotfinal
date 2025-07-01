"""
Timezone utilities for HOT SHARK Bot
"""
import pytz
from datetime import datetime
from app.config import Config

def get_israel_time() -> datetime:
    """Get current time in Israel timezone"""
    israel_tz = pytz.timezone("Asia/Jerusalem")
    return datetime.now(israel_tz)

def get_palestine_time() -> datetime:
    """Get current time in Palestine timezone (same as Israel)"""
    palestine_tz = pytz.timezone("Asia/Gaza")
    return datetime.now(palestine_tz)

def get_gmt_time() -> datetime:
    """Get current time in GMT timezone"""
    gmt_tz = pytz.timezone("GMT")
    return datetime.now(gmt_tz)

def format_dual_time() -> str:
    """Format dual timezone display for recommendations"""
    israel_time = get_israel_time()
    gmt_time = get_gmt_time()
    
    israel_formatted = israel_time.strftime("%I:%M %p")
    gmt_formatted = gmt_time.strftime("%H:%M")
    
    return f"🇮🇱 {israel_formatted} (إسرائيل)\n🌍 {gmt_formatted} (غرينتش)"

def is_market_open() -> bool:
    """Check if forex market is open"""
    gmt_time = get_gmt_time()
    weekday = gmt_time.weekday()  # 0 = Monday, 6 = Sunday
    hour = gmt_time.hour
    
    # Forex market is closed on weekends (Saturday and Sunday)
    if weekday == 5:  # Saturday
        return hour >= 22  # Opens at 22:00 GMT on Saturday
    elif weekday == 6:  # Sunday
        return True  # Open all day Sunday
    elif weekday == 4:  # Friday
        return hour < 22  # Closes at 22:00 GMT on Friday
    else:  # Monday to Thursday
        return True  # Open 24 hours

def get_next_market_session() -> str:
    """Get the next major market session"""
    gmt_time = get_gmt_time()
    hour = gmt_time.hour
    
    if 0 <= hour < 8:
        return "Asian Session (Tokyo)"
    elif 8 <= hour < 16:
        return "European Session (London)"
    elif 16 <= hour < 24:
        return "American Session (New York)"
    else:
        return "Market Closed"

