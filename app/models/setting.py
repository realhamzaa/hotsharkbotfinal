"""
Setting model for HOT SHARK Bot
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base

class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for global settings
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<Setting(id={self.id}, key={self.key}, user_id={self.user_id})>"

