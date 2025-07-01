"""
Market data model for HOT SHARK Bot.
Stores historical and real-time market data for analysis.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class MarketData(Base):
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)  # e.g., XAUUSD, BTCUSD
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    interval = Column(String, nullable=False) # e.g., 1m, 5m, 1h, 1d
    source = Column(String, nullable=False) # e.g., TwelveData, Polygon.io

    def __repr__(self):
        return f"<MarketData(symbol='{self.symbol}', timestamp='{self.timestamp}', close_price={self.close_price})>"

class IndicatorData(Base):
    __tablename__ = 'indicator_data'

    id = Column(Integer, primary_key=True, index=True)
    market_data_id = Column(Integer, nullable=False) # Foreign key to MarketData
    indicator_name = Column(String, nullable=False) # e.g., RSI, MACD, MovingAverage
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<IndicatorData(indicator='{self.indicator_name}', value={self.value})>"

class Signal(Base):
    __tablename__ = 'signals'

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    signal_type = Column(String, nullable=False) # e.g., BUY, SELL, HOLD
    strategy_name = Column(String, nullable=False) # e.g., ICT_SMC_Breakout, TrendFollowing
    confidence = Column(Float, nullable=True) # Confidence score of the signal
    is_automated = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Signal(symbol='{self.symbol}', type='{self.signal_type}', strategy='{self.strategy_name}')>"


