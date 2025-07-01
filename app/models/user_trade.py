"""
UserTrade model for HOT SHARK Bot
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base

class UserTrade(Base):
    __tablename__ = "user_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False)
    entry_time = Column(DateTime, default=func.now())
    exit_time = Column(DateTime, nullable=True)
    result = Column(String(20), nullable=True)  # profit, loss, pending
    profit_loss = Column(Float, nullable=True)  # In pips or dollars
    message_id = Column(Integer, nullable=True) # To track the original message in Telegram
    
    # Relationships
    user = relationship("User", back_populates="user_trades")
    recommendation = relationship("Recommendation", back_populates="user_trades")
    
    def __repr__(self):
        return f"<UserTrade(id={self.id}, user_id={self.user_id}, recommendation_id={self.recommendation_id})>"

