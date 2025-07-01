"""
Report model for HOT SHARK Bot
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_profit_loss = Column(Float, nullable=True)
    performance_ratio = Column(Float, nullable=True)
    report_data = Column(JSON, nullable=True)  # Detailed report data
    generated_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reports")
    
    def __repr__(self):
        return f"<Report(id={self.id}, user_id={self.user_id}, type={self.report_type})>"

