#!/usr/bin/env python3
"""
Test script for HOT SHARK Bot
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from app.config import Config
        print("✅ Config imported successfully")
        
        from app.models.database import create_tables, SessionLocal
        print("✅ Database models imported successfully")
        
        from app.bot import bot
        print("✅ Bot imported successfully")
        
        from app.handlers.start import StartHandler
        print("✅ Start handler imported successfully")
        
        from app.services.recommendation_service import RecommendationService
        print("✅ Recommendation service imported successfully")
        
        from app.services.news_service import NewsService
        print("✅ News service imported successfully")
        
        print("✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def test_database():
    """Test database connection and table creation"""
    print("\n🗄️ Testing database...")
    
    try:
        from app.models.database import create_tables, SessionLocal
        
        # Create tables
        create_tables()
        print("✅ Database tables created successfully")
        
        # Test database connection
        db = SessionLocal()
        try:
            # Simple query to test connection
            from sqlalchemy import text
            result = db.execute(text("SELECT 1")).fetchone()
            if result:
                print("✅ Database connection successful")
            db.close()
            return True
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            db.close()
            return False
            
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False

async def test_bot_setup():
    """Test bot initialization"""
    print("\n🤖 Testing bot setup...")
    
    try:
        from app.bot import bot
        
        # Check if bot application is created
        if bot.application:
            print("✅ Bot application created successfully")
        else:
            print("❌ Bot application not created")
            return False
            
        # Check if handlers are added
        handlers = bot.application.handlers
        if handlers:
            print(f"✅ Bot handlers added: {len(handlers)} handler groups")
        else:
            print("❌ No handlers found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Bot setup error: {e}")
        return False

async def test_services():
    """Test service classes"""
    print("\n🔧 Testing services...")
    
    try:
        from app.services.recommendation_service import RecommendationService
        from app.services.news_service import NewsService
        from app.services.report_service import ReportService
        
        print("✅ All services imported successfully")
        
        # Test market schedule
        schedule = NewsService.get_market_schedule()
        if schedule:
            print("✅ Market schedule service working")
        
        return True
        
    except Exception as e:
        print(f"❌ Services test error: {e}")
        return False

async def test_web_routes():
    """Test web routes"""
    print("\n🌐 Testing web routes...")
    
    try:
        from app.web.admin_routes import router
        
        # Check if routes are defined
        routes = router.routes
        if routes:
            print(f"✅ Admin routes defined: {len(routes)} routes")
            for route in routes:
                if hasattr(route, 'path'):
                    print(f"   - {route.path}")
        else:
            print("❌ No admin routes found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Web routes test error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🐋 HOT SHARK Bot - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("Bot Setup", test_bot_setup),
        ("Services", test_services),
        ("Web Routes", test_web_routes)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready to run.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

