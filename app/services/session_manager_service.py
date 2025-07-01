"""
Session Manager Service for HOT SHARK Bot
Ensures only one active session per user
"""
import time
from typing import Dict, Optional
from app.models.database import SessionLocal
from app.models.user import User

class SessionManagerService:
    """Manages user sessions to ensure only one active session per user"""
    
    # In-memory session storage (for production, use Redis)
    active_sessions: Dict[int, Dict] = {}
    
    @classmethod
    def create_session(cls, user_id: int, session_data: Dict) -> bool:
        """
        Create a new session for user
        Returns True if session created, False if user already has active session
        """
        current_time = time.time()
        
        # Check if user already has an active session
        if user_id in cls.active_sessions:
            existing_session = cls.active_sessions[user_id]
            # Check if session is still valid (within 24 hours)
            if current_time - existing_session.get('created_at', 0) < 86400:  # 24 hours
                return False  # User already has active session
            else:
                # Session expired, remove it
                del cls.active_sessions[user_id]
        
        # Create new session
        cls.active_sessions[user_id] = {
            'created_at': current_time,
            'last_activity': current_time,
            'data': session_data
        }
        
        # Update user login status in database
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.is_logged_in = True
                user.last_login = current_time
                db.commit()
        finally:
            db.close()
        
        return True
    
    @classmethod
    def update_activity(cls, user_id: int) -> bool:
        """Update last activity time for user session"""
        if user_id in cls.active_sessions:
            cls.active_sessions[user_id]['last_activity'] = time.time()
            return True
        return False
    
    @classmethod
    def end_session(cls, user_id: int) -> bool:
        """End user session"""
        if user_id in cls.active_sessions:
            del cls.active_sessions[user_id]
            
            # Update user login status in database
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.is_logged_in = False
                    db.commit()
            finally:
                db.close()
            
            return True
        return False
    
    @classmethod
    def is_session_active(cls, user_id: int) -> bool:
        """Check if user has active session"""
        if user_id not in cls.active_sessions:
            return False
        
        current_time = time.time()
        session = cls.active_sessions[user_id]
        
        # Check if session expired (24 hours of inactivity)
        if current_time - session.get('last_activity', 0) > 86400:
            cls.end_session(user_id)
            return False
        
        return True
    
    @classmethod
    def get_session_info(cls, user_id: int) -> Optional[Dict]:
        """Get session information for user"""
        if cls.is_session_active(user_id):
            return cls.active_sessions[user_id]
        return None
    
    @classmethod
    def cleanup_expired_sessions(cls):
        """Clean up expired sessions (run periodically)"""
        current_time = time.time()
        expired_users = []
        
        for user_id, session in cls.active_sessions.items():
            if current_time - session.get('last_activity', 0) > 86400:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            cls.end_session(user_id)
    
    @classmethod
    def force_logout_user(cls, user_id: int) -> bool:
        """Force logout user (admin function)"""
        return cls.end_session(user_id)
    
    @classmethod
    def get_active_sessions_count(cls) -> int:
        """Get count of active sessions"""
        # Clean up expired sessions first
        cls.cleanup_expired_sessions()
        return len(cls.active_sessions)
    
    @classmethod
    def get_all_active_users(cls) -> list:
        """Get list of all users with active sessions"""
        cls.cleanup_expired_sessions()
        return list(cls.active_sessions.keys())

