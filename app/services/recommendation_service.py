"""
Recommendation service for HOT SHARK Bot
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.recommendation import Recommendation
from app.models.user import User
from app.models.user_trade import UserTrade
from app.utils.localization import loc
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.utils.timezone_utils import get_palestine_time, get_gmt_time

class RecommendationService:
    @staticmethod
    def create_recommendation(
        asset_pair: str,
        trade_type: str,
        entry_points: list,
        tp_levels: list,
        sl: float,
        pips: int,
        success_rate: float = None,
        trade_duration: str = "short",
        rr_ratio: str = "1:2",
        lot_size_per_100: float = 0.01,
        is_premium: bool = False,
        strategy: str = None,
        is_live: bool = True
    ) -> Recommendation:
        """Create a new recommendation and format its message."""
        db = SessionLocal()
        try:
            palestine_time = get_palestine_time().strftime("%I:%M %p") # 12-hour format with AM/PM
            gmt_time = get_gmt_time().strftime("%H:%M") # 24-hour format

            # Format entry points, TP levels
            entry_str = ", ".join([str(ep) for ep in entry_points])
            tp_str = ", ".join([str(tp) for tp in tp_levels])

            # Calculate pips for TP/SL (assuming TP1 and SL are primary for pips calculation)
            # This is a simplified calculation, actual pips depend on entry and exact TP/SL
            tp_pips = abs(tp_levels[0] - entry_points[0]) if tp_levels else 0
            sl_pips = abs(sl - entry_points[0]) if sl else 0

            # Determine emoji for trade type
            trade_emoji = "📈" if trade_type.upper() == "BUY" else "📉"

            # Diamond emoji for premium/zero drawdown
            diamond_emoji = "💎" if is_premium else ""

            # Construct the message
            message_text = (
                f"{diamond_emoji} **{asset_pair} {trade_type.upper()}** {trade_emoji}\n\n"
                f"**نقطة الدخول:** {entry_str}\n"
                f"**الأهداف (TP):** {tp_str} ({tp_pips:.0f} نقطة)\n"
                f"**وقف الخسارة (SL):** {sl} ({sl_pips:.0f} نقطة)\n"
                f"**النقاط المتوقعة:** {pips}\n"
                f"**المدة المتوقعة:** {trade_duration}\n"
                f"**نسبة المخاطرة/المكافأة (R:R):** {rr_ratio}\n"
                f"**اللوت المقترح لكل 100 دولار:** {lot_size_per_100}\n"
                f"**الاستراتيجية:** {strategy if strategy else 'غير محدد'}\n"
                f"**وقت الإرسال:** فلسطين {palestine_time} | غرينتش {gmt_time}\n"
            )

            if success_rate is not None:
                message_text += f"**نسبة النجاح المتوقعة:** {success_rate:.2f}%\n"

            recommendation = Recommendation(
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
                is_live=is_live,
                message_text=message_text
            )
            
            db.add(recommendation)
            db.commit()
            db.refresh(recommendation)
            return recommendation
            
        finally:
            db.close()

