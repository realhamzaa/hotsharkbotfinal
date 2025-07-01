#!/usr/bin/env python3
"""
Production server runner for HOT SHARK Bot
"""
import uvicorn
from main import app

if __name__ == "__main__":
    print("🐋 Starting HOT SHARK Bot Server...")
    print("=" * 50)
    print("📊 Admin Panel: http://localhost:8000/admin/")
    print("🔗 API Docs: http://localhost:8000/docs")
    print("❤️ Health Check: http://localhost:8000/health")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

