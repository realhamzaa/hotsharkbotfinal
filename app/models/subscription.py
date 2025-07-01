"""
Subscription model for HOT SHARK Bot
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    subscription_type = Column(String(50), default="premium")
    created_by = Column(Integer, nullable=True)  # Admin who created the subscription
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, type={self.subscription_type})>"

