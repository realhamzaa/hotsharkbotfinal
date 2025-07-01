"""
News model for HOT SHARK Bot
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.database import Base

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    time = Column(DateTime, nullable=False)
    currency = Column(String(10), nullable=True)
    impact = Column(String(20), nullable=True)  # low, medium, high
    description = Column(Text, nullable=True)
    is_critical = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<News(id={self.id}, title={self.title[:50]}...)>"

