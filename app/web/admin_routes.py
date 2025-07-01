"""
Admin web routes for HOT SHARK Bot
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.recommendation import Recommendation
from app.models.user_trade import UserTrade
from app.models.news import News
from app.models.report import Report
from app.services.recommendation_service import RecommendationService
from app.services.news_service import NewsService
from app.config import Config

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

# Simple authentication check
def verify_admin(request: Request):
    """Simple admin verification - in production, use proper authentication"""
    # For demo purposes, we'll use a simple session check
    # In production, implement proper JWT or session-based auth
    admin_token = request.cookies.get("admin_token")
    if admin_token != "admin_authenticated":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard"""
    try:
        verify_admin(request)
    except HTTPException:
        return RedirectResponse(url="/admin/login")
    
    # Get statistics
    total_users = db.query(User).count()
    subscribed_users = db.query(User).filter(User.is_subscribed == True).count()
    total_recommendations = db.query(Recommendation).count()
    active_recommendations = db.query(Recommendation).filter(
        Recommendation.status == "active"
    ).count()
    total_trades = db.query(UserTrade).count()
    
    # Get recent recommendations
    recent_recommendations = db.query(Recommendation).order_by(
        Recommendation.sent_at.desc()
    ).limit(5).all()
    
    # Get recent users
    recent_users = db.query(User).order_by(
        User.created_at.desc()
    ).limit(5).all()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "total_users": total_users,
        "subscribed_users": subscribed_users,
        "total_recommendations": total_recommendations,
        "active_recommendations": active_recommendations,
        "total_trades": total_trades,
        "recent_recommendations": recent_recommendations,
        "recent_users": recent_users,
        "subscription_rate": round((subscribed_users / total_users * 100) if total_users > 0 else 0, 1)
    })

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin/login.html", {"request": request})

@router.post("/login")
async def admin_login(request: Request, password: str = Form(...)):
    """Handle admin login"""
    # Simple password check - in production, use proper authentication
    if password == "admin123":  # Change this in production!
        response = RedirectResponse(url="/admin/", status_code=302)
        response.set_cookie("admin_token", "admin_authenticated", max_age=3600*24)  # 24 hours
        return response
    else:
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "كلمة مرور خاطئة"
        })

@router.get("/logout")
async def admin_logout():
    """Admin logout"""
    response = RedirectResponse(url="/admin/login")
    response.delete_cookie("admin_token")
    return response

@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request, db: Session = Depends(get_db)):
    """Users management page"""
    verify_admin(request)
    
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "users": users
    })

@router.post("/users/{user_id}/subscription")
async def add_user_subscription(
    user_id: int,
    days: int = Form(...),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Add subscription to user"""
    verify_admin(request)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create subscription
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)
    
    subscription = Subscription(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        created_by=Config.ADMIN_USER_ID
    )
    
    # Update user
    user.is_subscribed = True
    user.subscription_expiry = end_date
    
    db.add(subscription)
    db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=302)

@router.post("/users/{user_id}/remove_subscription")
async def remove_user_subscription(
    user_id: int,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Remove user subscription"""
    verify_admin(request)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user
    user.is_subscribed = False
    user.subscription_expiry = None
    
    # Deactivate current subscriptions
    db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.is_active == True
    ).update({"is_active": False})
    
    db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=302)

@router.get("/recommendations", response_class=HTMLResponse)
async def admin_recommendations(request: Request, db: Session = Depends(get_db)):
    """Recommendations management page"""
    verify_admin(request)
    
    recommendations = db.query(Recommendation).order_by(
        Recommendation.sent_at.desc()
    ).limit(50).all()
    
    return templates.TemplateResponse("admin/recommendations.html", {
        "request": request,
        "recommendations": recommendations,
        "supported_pairs": Config.SUPPORTED_PAIRS
    })

@router.post("/recommendations/send")
async def send_recommendation(
    request: Request,
    asset_pair: str = Form(...),
    trade_type: str = Form(...),
    entry_points: str = Form(...),
    tp_levels: str = Form(...),
    sl: float = Form(...),
    pips: int = Form(...),
    success_rate: float = Form(None),
    trade_duration: str = Form(...),
    rr_ratio: str = Form(...),
    lot_size_per_100: float = Form(...),
    is_premium: bool = Form(False),
    strategy: str = Form(None),
    is_live: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Send new recommendation"""
    verify_admin(request)
    
    try:
        # Parse entry points and TP levels
        entry_list = [float(x.strip()) for x in entry_points.split(',')]
        tp_list = [float(x.strip()) for x in tp_levels.split(',')]
        
        # Create recommendation
        recommendation = RecommendationService.create_recommendation(
            asset_pair=asset_pair,
            trade_type=trade_type.upper(),
            entry_points=entry_list,
            tp_levels=tp_list,
            sl=sl,
            pips=pips,
            success_rate=success_rate,
            trade_duration=trade_duration,
            rr_ratio=rr_ratio,
            lot_size_per_100=lot_size_per_100,
            is_premium=is_premium,
            strategy=strategy if strategy else None,
            is_live=is_live
        )
        
        # In a real implementation, you would send this to Telegram users here
        # For now, we'll just save it to the database
        
        return RedirectResponse(url="/admin/recommendations", status_code=302)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating recommendation: {str(e)}")

@router.get("/news", response_class=HTMLResponse)
async def admin_news(request: Request, db: Session = Depends(get_db)):
    """News management page"""
    verify_admin(request)
    
    news_items = db.query(News).order_by(News.time.desc()).limit(50).all()
    
    return templates.TemplateResponse("admin/news.html", {
        "request": request,
        "news_items": news_items
    })

@router.post("/news/send")
async def send_news(
    request: Request,
    title: str = Form(...),
    time: str = Form(...),
    currency: str = Form(None),
    impact: str = Form(...),
    description: str = Form(None),
    is_critical: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Send news alert"""
    verify_admin(request)
    
    try:
        # Parse datetime
        news_time = datetime.strptime(time, "%Y-%m-%dT%H:%M")
        
        # Create news
        news = NewsService.create_news(
            title=title,
            time=news_time,
            currency=currency if currency else None,
            impact=impact,
            description=description if description else None,
            is_critical=is_critical
        )
        
        # In a real implementation, you would send this to Telegram users here
        
        return RedirectResponse(url="/admin/news", status_code=302)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating news: {str(e)}")

@router.get("/reports", response_class=HTMLResponse)
async def admin_reports(request: Request, db: Session = Depends(get_db)):
    """Reports page"""
    verify_admin(request)
    
    reports = db.query(Report).order_by(Report.generated_at.desc()).limit(20).all()
    
    return templates.TemplateResponse("admin/reports.html", {
        "request": request,
        "reports": reports
    })

@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(request: Request):
    """Settings page"""
    verify_admin(request)
    
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "config": Config
    })

