"""
Market Monitor Service for HOT SHARK Bot
24/7 market monitoring and alert system
"""
import asyncio
import logging
from datetime import datetime, timedelta
import pytz
from typing import List, Dict
from app.models.database import SessionLocal
from app.models.user import User
from app.services.data_collector_service import DataCollectorService
from app.services.auto_recommendation_service import AutoRecommendationService
from app.services.catalog_service import CatalogService
from app.utils.localization import get_text

logger = logging.getLogger(__name__)

class MarketMonitorService:
    """24/7 Market monitoring and alert service"""
    
    def __init__(self, bot):
        self.bot = bot
        self.is_running = False
        self.monitoring_task = None
        self.last_liquidity_alert = {}
        self.last_market_opening_alert = {}
        
    async def start_monitoring(self):
        """Start 24/7 market monitoring"""
        if self.is_running:
            logger.warning("Market monitoring is already running")
            return
        
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Market monitoring started")
    
    async def stop_monitoring(self):
        """Stop market monitoring"""
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Market monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Check market openings
                await self._check_market_openings()
                
                # Check high liquidity periods
                await self._check_high_liquidity()
                
                # Generate automatic recommendations
                await self._generate_auto_recommendations()
                
                # Check for important news alerts
                await self._check_news_alerts()
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _check_market_openings(self):
        """Check for market opening times and send alerts"""
        now_gmt = datetime.now(pytz.UTC)
        
        # Market sessions to check
        markets = {
            'sydney': {'open': '21:00', 'name': '🇦🇺 Sydney'},
            'tokyo': {'open': '23:00', 'name': '🇯🇵 Tokyo'},
            'london': {'open': '07:00', 'name': '🇬🇧 London'},
            'new_york': {'open': '12:00', 'name': '🇺🇸 New York'}
        }
        
        for market_id, market_info in markets.items():
            # Check if it's market opening time (within 1 minute)
            open_time = datetime.strptime(market_info['open'], '%H:%M').time()
            market_open_datetime = datetime.combine(now_gmt.date(), open_time)
            market_open_datetime = pytz.UTC.localize(market_open_datetime)
            
            time_diff = abs((now_gmt - market_open_datetime).total_seconds())
            
            # If within 1 minute of opening and haven't alerted today
            if time_diff <= 60:
                today_key = f"{market_id}_{now_gmt.date()}"
                if today_key not in self.last_market_opening_alert:
                    await self._send_market_opening_alert(market_info['name'])
                    self.last_market_opening_alert[today_key] = now_gmt
    
    async def _check_high_liquidity(self):
        """Check for high liquidity periods and send alerts"""
        now_gmt = datetime.now(pytz.UTC)
        
        # High liquidity periods
        liquidity_periods = [
            {'name': 'London Open', 'time': '07:00', 'duration': 2},
            {'name': 'London-NY Overlap', 'time': '12:00', 'duration': 4},
            {'name': 'NY Open', 'time': '12:00', 'duration': 2},
            {'name': 'Asian Session', 'time': '23:00', 'duration': 3}
        ]
        
        for period in liquidity_periods:
            start_time = datetime.strptime(period['time'], '%H:%M').time()
            start_datetime = datetime.combine(now_gmt.date(), start_time)
            start_datetime = pytz.UTC.localize(start_datetime)
            
            time_diff = abs((now_gmt - start_datetime).total_seconds())
            
            # If within 1 minute of high liquidity period start
            if time_diff <= 60:
                today_key = f"{period['name']}_{now_gmt.date()}"
                if today_key not in self.last_liquidity_alert:
                    await self._send_liquidity_alert(period['name'])
                    self.last_liquidity_alert[today_key] = now_gmt
    
    async def _generate_auto_recommendations(self):
        """Generate automatic recommendations based on market analysis"""
        try:
            # Get supported trading pairs
            trading_pairs = ['XAUUSD', 'BTCUSD', 'ETHUSD', 'EURUSD', 'GBPJPY', 'GBPUSD', 'USDJPY', 'US30', 'US100']
            
            for pair in trading_pairs:
                # Check if we should generate a recommendation for this pair
                if await self._should_generate_recommendation(pair):
                    recommendation = await AutoRecommendationService.generate_recommendation(pair)
                    if recommendation:
                        await self._send_auto_recommendation(recommendation)
                        
        except Exception as e:
            logger.error(f"Error generating auto recommendations: {e}")
    
    async def _check_news_alerts(self):
        """Check for upcoming important news and send alerts"""
        from app.models.news import News
        
        db = SessionLocal()
        try:
            now = datetime.now()
            one_hour_later = now + timedelta(hours=1)
            
            # Get news in the next hour that haven't been alerted
            upcoming_news = db.query(News).filter(
                News.time >= now,
                News.time <= one_hour_later,
                News.impact.in_(['high', 'critical']),
                News.alerted == False
            ).all()
            
            for news in upcoming_news:
                await self._send_news_alert(news)
                news.alerted = True
                db.commit()
                
        finally:
            db.close()
    
    async def _should_generate_recommendation(self, pair: str) -> bool:
        """Check if we should generate a recommendation for this pair"""
        # Simple logic: generate recommendation every 4 hours for each pair
        # In production, this would be based on market conditions and ML models
        
        from app.models.recommendation import Recommendation
        
        db = SessionLocal()
        try:
            # Check last recommendation time for this pair
            last_rec = db.query(Recommendation).filter(
                Recommendation.asset_pair == pair
            ).order_by(Recommendation.created_at.desc()).first()
            
            if not last_rec:
                return True  # No previous recommendation
            
            # Check if 4 hours have passed
            time_diff = datetime.now() - last_rec.created_at
            return time_diff.total_seconds() > 14400  # 4 hours
            
        finally:
            db.close()
    
    async def _send_market_opening_alert(self, market_name: str):
        """Send market opening alert to all subscribed users"""
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.is_subscribed == True).all()
            
            for user in users:
                try:
                    palestine_time = datetime.now(pytz.timezone('Asia/Gaza'))
                    
                    message = f"🔔 {get_text('market_opening_alert', user.lang_code)}\n\n"
                    message += f"📈 {market_name} {get_text('market_opened', user.lang_code)}\n"
                    message += f"⏰ {palestine_time.strftime('%I:%M %p')} Palestine Time\n\n"
                    message += f"💡 {get_text('trading_opportunity', user.lang_code)}"
                    
                    await self.bot.send_message(
                        chat_id=user.id,
                        text=message
                    )
                    
                except Exception as e:
                    logger.error(f"Error sending market opening alert to user {user.id}: {e}")
                    
        finally:
            db.close()
    
    async def _send_liquidity_alert(self, period_name: str):
        """Send high liquidity alert to all subscribed users"""
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.is_subscribed == True).all()
            
            for user in users:
                try:
                    palestine_time = datetime.now(pytz.timezone('Asia/Gaza'))
                    
                    message = f"💧 {get_text('high_liquidity_alert', user.lang_code)}\n\n"
                    message += f"🔥 {period_name} {get_text('high_liquidity_started', user.lang_code)}\n"
                    message += f"⏰ {palestine_time.strftime('%I:%M %p')} Palestine Time\n\n"
                    message += f"⚡ {get_text('high_volatility_expected', user.lang_code)}\n"
                    message += f"📊 {get_text('watch_for_opportunities', user.lang_code)}"
                    
                    await self.bot.send_message(
                        chat_id=user.id,
                        text=message
                    )
                    
                except Exception as e:
                    logger.error(f"Error sending liquidity alert to user {user.id}: {e}")
                    
        finally:
            db.close()
    
    async def _send_auto_recommendation(self, recommendation: Dict):
        """Send automatically generated recommendation"""
        from app.handlers.recommendation import RecommendationHandler
        
        try:
            await RecommendationHandler.send_recommendation_to_all(
                bot=self.bot,
                asset_pair=recommendation['asset_pair'],
                trade_type=recommendation['trade_type'],
                entry_points=recommendation['entry_points'],
                tp_levels=recommendation['tp_levels'],
                sl=recommendation['sl'],
                pips=recommendation['pips'],
                success_rate=recommendation['success_rate'],
                trade_duration=recommendation['trade_duration'],
                rr_ratio=recommendation['rr_ratio'],
                lot_size_per_100=recommendation['lot_size_per_100'],
                is_premium=recommendation['is_premium'],
                strategy=recommendation['strategy'],
                is_live=True
            )
            
        except Exception as e:
            logger.error(f"Error sending auto recommendation: {e}")
    
    async def _send_news_alert(self, news):
        """Send news alert to all subscribed users"""
        from app.services.news_service import NewsService
        
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.is_subscribed == True).all()
            
            for user in users:
                try:
                    message = NewsService.format_news_alert(news, user.lang_code)
                    await self.bot.send_message(
                        chat_id=user.id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                except Exception as e:
                    logger.error(f"Error sending news alert to user {user.id}: {e}")
                    
        finally:
            db.close()

