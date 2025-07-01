"""
Main FastAPI application for HOT SHARK Bot
"""
import os
import logging
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from telegram import Update
from app.bot import bot
from app.services.data_collector_service import DataCollectorService
from app.models.database import Base, engine, SessionLocal
from app.services.scheduler_service import scheduler
from app.services.training_service import TrainingService
from app.services.auto_recommendation_service import AutoRecommendationService
from app.services.market_monitor_service import MarketMonitorService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="HOT SHARK Bot API",
    description="Telegram Trading Bot with Admin Panel",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for admin panel
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except:
    logger.warning("Static files directory not found")

# Configure Jinja2Templates
templates = Jinja2Templates(directory="app/templates")

# Include admin routes
from app.web.admin_routes import admin_router
app.include_router(admin_router)

# Global market monitor instance
market_monitor = None

async def collect_market_data_job():
    """Collect market data periodically"""
    db = SessionLocal()
    try:
        collector = DataCollectorService(db)
        # Collect data for supported pairs
        pairs = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
        for pair in pairs:
            try:
                await collector.collect_and_store_data(pair, "1min", "TwelveData")
            except Exception as e:
                logger.error(f"Error collecting data for {pair}: {e}")
    finally:
        db.close()

async def train_models_job():
    """Train ML models periodically"""
    db = SessionLocal()
    try:
        training_service = TrainingService(db)
        pairs = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
        for pair in pairs:
            try:
                await training_service.train_and_evaluate_model(pair, "1min")
            except Exception as e:
                logger.error(f"Error training model for {pair}: {e}")
    finally:
        db.close()

async def generate_and_send_recommendations_job():
    """Generate and send recommendations periodically"""
    db = SessionLocal()
    try:
        auto_rec_service = AutoRecommendationService(db, bot.get_application().bot)
        await auto_rec_service.monitor_and_generate_recommendations()
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    global market_monitor
    
    logger.info("Starting HOT SHARK Bot...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Setup webhook
    await bot.setup_webhook()
    
    # Start scheduler
    bot.start_scheduler()
    
    # Schedule periodic jobs
    scheduler.add_job(
        collect_market_data_job, 
        "interval", 
        minutes=5, 
        id="market_data_collection"
    )
    
    scheduler.add_job(
        train_models_job, 
        "interval", 
        hours=24, 
        id="model_training"
    )
    
    scheduler.add_job(
        generate_and_send_recommendations_job, 
        "interval", 
        minutes=15, 
        id="auto_recommendation_generation"
    )
    
    # Start 24/7 market monitoring
    market_monitor = MarketMonitorService(bot.get_application().bot)
    await market_monitor.start_monitoring()
    
    logger.info("Bot initialized successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global market_monitor
    
    logger.info("Shutting down HOT SHARK Bot...")
    
    # Stop market monitoring
    if market_monitor:
        await market_monitor.stop_monitoring()
    
    # Stop scheduler
    bot.stop_scheduler()
    scheduler.shutdown()
    
    logger.info("Bot shutdown complete!")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HOT SHARK Bot API is running! 🐋",
        "status": "active",
        "admin_panel": "/admin/",
        "features": [
            "24/7 Market Monitoring",
            "Automatic Recommendations",
            "ICT/SMC Analysis",
            "Multi-language Support",
            "Session Management",
            "Market Catalog"
        ]
    }

@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    """Telegram webhook endpoint"""
    try:
        # Verify token
        from app.config import Config
        if token != Config.TELEGRAM_BOT_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get update data
        update_data = await request.json()
        
        # Process update
        update = Update.de_json(update_data, bot.get_application().bot)
        await bot.get_application().process_update(update)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.services.session_manager_service import SessionManagerService
    
    return {
        "status": "healthy",
        "bot_status": "running",
        "active_sessions": SessionManagerService.get_active_sessions_count(),
        "market_monitor": "active" if market_monitor and market_monitor.is_running else "inactive",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/status")
async def bot_status():
    """Bot status endpoint"""
    from app.services.session_manager_service import SessionManagerService
    
    return {
        "bot_name": "HOT SHARK Bot",
        "version": "1.0.0",
        "active_users": SessionManagerService.get_active_sessions_count(),
        "supported_pairs": [
            "XAUUSD", "BTCUSD", "ETHUSD", "EURUSD", 
            "GBPJPY", "GBPUSD", "USDJPY", "US30", "US100"
        ],
        "features": {
            "market_monitoring": True,
            "auto_recommendations": True,
            "ict_smc_analysis": True,
            "session_management": True,
            "catalog_system": True,
            "multi_language": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )