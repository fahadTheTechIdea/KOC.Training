"""
User Service
Handles user profile management, model retrieval, and statistics
"""
from typing import Optional, Dict, List
from datetime import datetime
from app import db
from app.models.user import User, UserProfile
from app.models.project import MLProject
from app.models.experiment import Experiment
from werkzeug.security import generate_password_hash
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management and profile operations"""
    
    @staticmethod
    def create_user(username: str, email: str, password: str, profile_data: Optional[Dict] = None, is_admin: bool = False) -> tuple[User, Optional[str]]:
        """
        Create a new user with profile
        
        Args:
            username: Username
            email: Email address
            password: User password
            profile_data: Optional profile data (display_name, bio, etc.)
            is_admin: Whether user is admin
            
        Returns:
            Tuple of (user, error_message)
        """
        try:
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                return None, "Username already exists"
            
            if User.query.filter_by(email=email).first():
                return None, "Email already registered"
            
            # Create user
            user = User(
                username=username,
                email=email,
                is_admin=is_admin,
                is_active=True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get user.id
            
            # Create profile
            profile = UserProfile(
                user_id=user.id,
                display_name=profile_data.get('display_name', username) if profile_data else username,
                bio=profile_data.get('bio') if profile_data else None,
                avatar_url=profile_data.get('avatar_url') if profile_data else None,
                timezone=profile_data.get('timezone', 'UTC') if profile_data else 'UTC',
                language=profile_data.get('language', 'en') if profile_data else 'en'
            )
            if profile_data and 'preferences' in profile_data:
                profile.set_preferences(profile_data['preferences'])
            
            db.session.add(profile)
            db.session.commit()
            
            logger.info(f"User created: {username}")
            return user, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {e}")
            return None, str(e)
    
    @staticmethod
    def update_user(user_id: int, data: Dict) -> tuple[bool, Optional[str]]:
        """
        Update user information
        
        Args:
            user_id: User ID
            data: Update data (username, email, is_admin, is_active, etc.)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Update user fields
            if 'username' in data:
                # Check if username is already taken by another user
                existing = User.query.filter_by(username=data['username']).first()
                if existing and existing.id != user_id:
                    return False, "Username already taken"
                user.username = data['username']
            
            if 'email' in data:
                # Check if email is already taken by another user
                existing = User.query.filter_by(email=data['email']).first()
                if existing and existing.id != user_id:
                    return False, "Email already taken"
                user.email = data['email']
            
            if 'password' in data and data['password']:
                user.set_password(data['password'])
            
            if 'is_admin' in data:
                user.is_admin = data['is_admin']
            
            if 'is_active' in data:
                user.is_active = data['is_active']
            
            db.session.commit()
            logger.info(f"User updated: {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user: {e}")
            return False, str(e)
    
    @staticmethod
    def delete_user(user_id: int) -> tuple[bool, Optional[str]]:
        """
        Delete a user (cascade deletes profile, projects, experiments)
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Cascade delete will handle related records
            db.session.delete(user)
            db.session.commit()
            
            logger.info(f"User deleted: {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting user: {e}")
            return False, str(e)
    
    @staticmethod
    def get_user_profile(user_id: int) -> Optional[UserProfile]:
        """Get user profile"""
        return UserProfile.query.filter_by(user_id=user_id).first()
    
    @staticmethod
    def update_user_profile(user_id: int, profile_data: Dict) -> tuple[bool, Optional[str]]:
        """
        Update user profile
        
        Args:
            user_id: User ID
            profile_data: Profile data to update
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                # Create profile if it doesn't exist
                profile = UserProfile(user_id=user_id)
                db.session.add(profile)
            
            if 'display_name' in profile_data:
                profile.display_name = profile_data['display_name']
            
            if 'bio' in profile_data:
                profile.bio = profile_data['bio']
            
            if 'avatar_url' in profile_data:
                profile.avatar_url = profile_data['avatar_url']
            
            if 'timezone' in profile_data:
                profile.timezone = profile_data['timezone']
            
            if 'language' in profile_data:
                profile.language = profile_data['language']
            
            if 'preferences' in profile_data:
                profile.set_preferences(profile_data['preferences'])
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {e}")
            return False, str(e)
    
    @staticmethod
    def get_user_models(user_id: int, include_shared: bool = False) -> Dict:
        """
        Get user's models (projects and experiments)
        
        Args:
            user_id: User ID
            include_shared: Whether to include shared projects
            
        Returns:
            Dictionary with projects and experiments
        """
        # Get user's projects
        projects_query = MLProject.query.filter_by(user_id=user_id)
        if include_shared:
            # Also include projects shared with this user
            from sqlalchemy import or_
            projects_query = MLProject.query.filter(
                or_(
                    MLProject.user_id == user_id,
                    MLProject.is_shared == True
                )
            )
        
        projects = projects_query.all()
        
        # Get user's experiments
        experiments = Experiment.query.filter_by(user_id=user_id).all()
        
        return {
            'projects': [p.to_dict() for p in projects],
            'experiments': [e.to_dict() for e in experiments],
            'projects_count': len(projects),
            'experiments_count': len(experiments)
        }
    
    @staticmethod
    def get_user_statistics(user_id: int) -> Dict:
        """
        Get user statistics
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user statistics
        """
        user = User.query.get(user_id)
        if not user:
            return {}
        
        projects_count = MLProject.query.filter_by(user_id=user_id).count()
        experiments_count = Experiment.query.filter_by(user_id=user_id).count()
        
        # Count shared projects user has access to
        shared_projects_count = MLProject.query.filter(
            MLProject.is_shared == True,
            MLProject.user_id != user_id
        ).count()
        
        return {
            'user_id': user_id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'projects_count': projects_count,
            'experiments_count': experiments_count,
            'shared_projects_count': shared_projects_count,
            'total_projects': projects_count + shared_projects_count,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
            'login_count': user.login_count,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
