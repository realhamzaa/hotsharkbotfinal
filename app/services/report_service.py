"""
Report service for HOT SHARK Bot
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import SessionLocal
from app.models.report import Report
from app.models.user_trade import UserTrade
from app.models.recommendation import Recommendation
from app.models.user import User

class ReportService:
    @staticmethod
    def generate_user_report(
        user_id: int,
        report_type: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Report:
        """Generate a report for a user"""
        
        if not start_date or not end_date:
            start_date, end_date = ReportService._get_date_range(report_type)
        
        # Get user trades in the period
        trades_data = ReportService._get_user_trades_data(user_id, start_date, end_date)
        
        # Calculate metrics
        total_profit_loss = sum(trade.get('profit_loss', 0) for trade in trades_data['trades'])
        total_trades = len(trades_data['trades'])
        winning_trades = len([t for t in trades_data['trades'] if t.get('result') == 'profit'])
        performance_ratio = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Prepare detailed report data
        report_data = {
            'trades': trades_data['trades'],
            'summary': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': performance_ratio,
                'total_profit_loss': total_profit_loss,
                'average_profit_loss': total_profit_loss / total_trades if total_trades > 0 else 0
            },
            'by_asset': trades_data['by_asset'],
            'by_trade_type': trades_data['by_trade_type']
        }
        
        # Create report
        db = SessionLocal()
        try:
            report = Report(
                user_id=user_id,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                total_profit_loss=total_profit_loss,
                performance_ratio=performance_ratio,
                report_data=report_data
            )
            
            db.add(report)
            db.commit()
            db.refresh(report)
            return report
        finally:
            db.close()
    
    @staticmethod
    def _get_date_range(report_type: str) -> tuple:
        """Get date range based on report type"""
        end_date = datetime.now()
        
        if report_type == "daily":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif report_type == "weekly":
            # Start of current week (Monday)
            days_since_monday = end_date.weekday()
            start_date = end_date - timedelta(days=days_since_monday)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif report_type == "monthly":
            # Start of current month
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to daily
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return start_date, end_date
    
    @staticmethod
    def _get_user_trades_data(user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get user trades data for the specified period"""
        db = SessionLocal()
        try:
            # Get user trades with recommendations
            trades = db.query(UserTrade, Recommendation).join(
                Recommendation, UserTrade.recommendation_id == Recommendation.id
            ).filter(
                UserTrade.user_id == user_id,
                UserTrade.entry_time >= start_date,
                UserTrade.entry_time <= end_date
            ).all()
            
            trades_list = []
            by_asset = {}
            by_trade_type = {"BUY": 0, "SELL": 0}
            
            for user_trade, recommendation in trades:
                trade_data = {
                    'id': user_trade.id,
                    'asset_pair': recommendation.asset_pair,
                    'trade_type': recommendation.trade_type,
                    'entry_time': user_trade.entry_time.isoformat(),
                    'exit_time': user_trade.exit_time.isoformat() if user_trade.exit_time else None,
                    'result': user_trade.result,
                    'profit_loss': user_trade.profit_loss or 0,
                    'pips': recommendation.pips,
                    'rr_ratio': recommendation.rr_ratio
                }
                
                trades_list.append(trade_data)
                
                # Group by asset
                asset = recommendation.asset_pair
                if asset not in by_asset:
                    by_asset[asset] = {'count': 0, 'profit_loss': 0}
                by_asset[asset]['count'] += 1
                by_asset[asset]['profit_loss'] += user_trade.profit_loss or 0
                
                # Group by trade type
                by_trade_type[recommendation.trade_type] += 1
            
            return {
                'trades': trades_list,
                'by_asset': by_asset,
                'by_trade_type': by_trade_type
            }
        finally:
            db.close()
    
    @staticmethod
    def format_report_message(report: Report, lang: str = "ar") -> str:
        """Format report message for display"""
        data = report.report_data
        summary = data.get('summary', {})
        
        # Format dates
        start_date_str = report.start_date.strftime("%Y-%m-%d")
        end_date_str = report.end_date.strftime("%Y-%m-%d")
        
        if lang == "ar":
            report_title = {
                "daily": "📊 التقرير اليومي",
                "weekly": "📊 التقرير الأسبوعي", 
                "monthly": "📊 التقرير الشهري"
            }.get(report.report_type, "📊 التقرير")
            
            message = f"""
{report_title}

📅 **الفترة:** {start_date_str} إلى {end_date_str}

📈 **ملخص الأداء:**
• إجمالي الصفقات: {summary.get('total_trades', 0)}
• الصفقات الرابحة: {summary.get('winning_trades', 0)}
• الصفقات الخاسرة: {summary.get('losing_trades', 0)}
• معدل النجاح: {summary.get('win_rate', 0):.1f}%
• إجمالي الربح/الخسارة: {summary.get('total_profit_loss', 0):.1f} نقطة
• متوسط الربح/الخسارة: {summary.get('average_profit_loss', 0):.1f} نقطة

💰 **الأداء حسب الأصول:**
"""
            
            # Add performance by asset
            by_asset = data.get('by_asset', {})
            for asset, asset_data in by_asset.items():
                message += f"• {asset}: {asset_data['count']} صفقات، {asset_data['profit_loss']:.1f} نقطة\n"
            
        else:  # English
            report_title = {
                "daily": "📊 Daily Report",
                "weekly": "📊 Weekly Report",
                "monthly": "📊 Monthly Report"
            }.get(report.report_type, "📊 Report")
            
            message = f"""
{report_title}

📅 **Period:** {start_date_str} to {end_date_str}

📈 **Performance Summary:**
• Total Trades: {summary.get('total_trades', 0)}
• Winning Trades: {summary.get('winning_trades', 0)}
• Losing Trades: {summary.get('losing_trades', 0)}
• Win Rate: {summary.get('win_rate', 0):.1f}%
• Total P&L: {summary.get('total_profit_loss', 0):.1f} pips
• Average P&L: {summary.get('average_profit_loss', 0):.1f} pips

💰 **Performance by Asset:**
"""
            
            # Add performance by asset
            by_asset = data.get('by_asset', {})
            for asset, asset_data in by_asset.items():
                message += f"• {asset}: {asset_data['count']} trades, {asset_data['profit_loss']:.1f} pips\n"
        
        return message.strip()
    
    @staticmethod
    def get_user_reports(user_id: int, limit: int = 10) -> List[Report]:
        """Get user's recent reports"""
        db = SessionLocal()
        try:
            return db.query(Report).filter(
                Report.user_id == user_id
            ).order_by(Report.generated_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def schedule_weekly_reports():
        """Generate weekly reports for all active users (to be called by scheduler)"""
        db = SessionLocal()
        try:
            # Get all subscribed users
            users = db.query(User).filter(User.is_subscribed == True).all()
            
            for user in users:
                try:
                    ReportService.generate_user_report(user.id, "weekly")
                except Exception as e:
                    print(f"Error generating weekly report for user {user.id}: {e}")
        finally:
            db.close()

