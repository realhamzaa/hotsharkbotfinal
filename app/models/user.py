"""
User model for HOT SHARK Bot
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)  # Telegram User ID
    username = Column(String(255), nullable=True)
    lang_code = Column(String(10), default="ar")
    is_admin = Column(Boolean, default=False)
    is_subscribed = Column(Boolean, default=False)
    subscription_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    active_session_id = Column(String(255), nullable=True, unique=True) # For single session login
    receive_recommendations = Column(Boolean, default=True)
    paused_pairs = Column(Text, nullable=True) # Stores JSON string of paused pairs
    receive_news = Column(Boolean, default=True)
    news_preferences = Column(Text, nullable=True) # Stores JSON string of news preferences
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    user_trades = relationship("UserTrade", back_populates="user")
    reports = relationship("Report", back_populates="user")
    settings = relationship("Setting", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

