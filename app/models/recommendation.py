"""
Recommendation model for HOT SHARK Bot
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_pair = Column(String(20), nullable=False)
    trade_type = Column(String(10), nullable=False)  # BUY or SELL
    entry_points = Column(Text, nullable=False)  # JSON string for multiple entry points
    tp = Column(Text, nullable=False)  # JSON string for multiple TP levels
    sl = Column(String(50), nullable=False)
    pips = Column(Integer, nullable=False)
    success_rate = Column(Float, nullable=True)
    trade_duration = Column(String(20), nullable=False)  # scalp, short, long
    rr_ratio = Column(String(20), nullable=False)
    lot_size_per_100 = Column(Float, nullable=False)
    message_text = Column(Text, nullable=False)
    is_premium = Column(Boolean, default=False)  # Diamond quality trades
    strategy = Column(Text, nullable=True)  # ICT/SMC strategy used
    is_live = Column(Boolean, default=True)  # Live or pending trade
    status = Column(String(20), default="active")  # active, tp_hit, sl_hit, pending
    sent_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user_trades = relationship("UserTrade", back_populates="recommendation")
    
    def __repr__(self):
        return f"<Recommendation(id={self.id}, pair={self.asset_pair}, type={self.trade_type})>"

