"""
User Session Management Service for HOT SHARK Bot.
Ensures only one active login session per user.
"""

from sqlalchemy.orm import Session
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

class UserSessionService:
    def __init__(self, db: Session):
        self.db = db

    def set_user_active_session(self, user_id: int, session_id: str) -> bool:
        """Sets the active session ID for a user. Returns True if successful, False otherwise."""
        user = self.db.query(User).filter(User.telegram_id == user_id).first()
        if user:
            user.active_session_id = session_id
            self.db.add(user)
            self.db.commit()
            logger.info(f"User {user_id} active session set to {session_id}")
            return True
        logger.warning(f"User {user_id} not found when setting active session.")
        return False

    def is_active_session(self, user_id: int, session_id: str) -> bool:
        """Checks if the given session ID is the active session for the user."""
        user = self.db.query(User).filter(User.telegram_id == user_id).first()
        if user and user.active_session_id == session_id:
            return True
        logger.info(f"Session {session_id} is not active for user {user_id}. Active: {user.active_session_id if user else 'N/A'}")
        return False

    def clear_user_session(self, user_id: int) -> bool:
        """Clears the active session ID for a user. Returns True if successful, False otherwise."""
        user = self.db.query(User).filter(User.telegram_id == user_id).first()
        if user:
            user.active_session_id = None
            self.db.add(user)
            self.db.commit()
            logger.info(f"User {user_id} active session cleared.")
            return True
        logger.warning(f"User {user_id} not found when clearing active session.")
        return False


