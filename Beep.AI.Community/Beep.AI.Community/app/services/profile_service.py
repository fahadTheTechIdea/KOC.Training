"""
Profile Service - User profile management
"""
from typing import Optional, Dict, List, Tuple
from app import db
from app.models.user import User, UserProfile, APIKey
import logging

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles"""
    
    @staticmethod
    def get_user_profile(username: str) -> Optional[User]:
        """Get user profile by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def can_edit_profile(current_user: Optional[User], target_user: User) -> bool:
        """
        Check if current user can edit target user's profile
        
        Args:
            current_user: Currently authenticated user (None if not authenticated)
            target_user: User whose profile is being accessed
            
        Returns:
            True if current_user can edit target_user's profile
        """
        if not current_user:
            return False
        # User can edit their own profile, or admins can edit any profile
        return current_user.id == target_user.id or current_user.is_admin_role()
    
    @staticmethod
    def update_user_profile(user_id: int, data: Dict) -> Tuple[Optional[UserProfile], Optional[str]]:
        """
        Update user profile
        
        Args:
            user_id: User ID
            data: Dictionary with profile fields to update
            
        Returns:
            Tuple of (updated_profile, error_message)
        """
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        # Get or create profile
        profile = user.profile
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
        
        # Update profile fields
        if 'display_name' in data:
            profile.display_name = data['display_name']
        if 'bio' in data:
            profile.bio = data['bio']
        if 'avatar_url' in data:
            profile.avatar_url = data['avatar_url']
        if 'location' in data:
            profile.location = data['location']
        if 'organization' in data:
            profile.organization = data['organization']
        if 'website' in data:
            profile.website = data['website']
        if 'skills' in data:
            profile.skills = data['skills']
        
        try:
            db.session.commit()
            return profile, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {e}", exc_info=True)
            return None, str(e)
    
    @staticmethod
    def get_user_stats(user_id: int) -> Dict:
        """
        Get user statistics (competitions, submissions, etc.)
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user statistics
        """
        from app.models.submission import Submission
        from app.models.competition import CompetitionParticipant
        from app.models.dataset import Dataset
        from app.models.notebook import Notebook
        
        stats = {
            'datasets': Dataset.query.filter_by(owner_id=user_id).count(),
            'notebooks': Notebook.query.filter_by(owner_id=user_id).count(),
            'submissions': Submission.query.filter_by(user_id=user_id).count(),
            'competitions_joined': CompetitionParticipant.query.filter_by(user_id=user_id).distinct().count()
        }
        
        return stats
    
    @staticmethod
    def generate_api_key(user_id: int, key_name: str) -> Tuple[Optional[APIKey], Optional[str]]:
        """
        Generate a new API key for a user
        
        Args:
            user_id: User ID
            key_name: Name/label for the API key
            
        Returns:
            Tuple of (api_key_object, error_message)
        """
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        if not key_name or not key_name.strip():
            return None, "Key name is required"
        
        # Generate unique API key
        api_key_value = APIKey.generate_key()
        
        # Ensure uniqueness (very unlikely collision, but check anyway)
        while APIKey.query.filter_by(api_key=api_key_value).first():
            api_key_value = APIKey.generate_key()
        
        api_key = APIKey(
            user_id=user_id,
            key_name=key_name.strip(),
            api_key=api_key_value,
            is_active=True
        )
        
        try:
            db.session.add(api_key)
            db.session.commit()
            return api_key, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error generating API key: {e}", exc_info=True)
            return None, str(e)
    
    @staticmethod
    def get_user_api_keys(user_id: int) -> List[APIKey]:
        """
        Get all API keys for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of APIKey objects
        """
        return APIKey.query.filter_by(user_id=user_id).order_by(APIKey.created_at.desc()).all()
    
    @staticmethod
    def get_api_key_by_id(user_id: int, api_key_id: int, allow_admin: bool = False) -> Optional[APIKey]:
        """
        Get a specific API key by ID (for validation)
        
        Args:
            user_id: User ID (must own the key, unless allow_admin=True and user is admin)
            api_key_id: API key ID
            allow_admin: If True, allow admin users to access any key
            
        Returns:
            APIKey object or None
        """
        api_key = APIKey.query.get(api_key_id)
        if not api_key:
            return None
        
        # Check ownership or admin access
        if api_key.user_id == user_id:
            return api_key
        
        if allow_admin:
            user = User.query.get(user_id)
            if user and user.is_admin_role():
                return api_key
        
        return None
    
    @staticmethod
    def delete_api_key(user_id: int, api_key_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete an API key
        
        Args:
            user_id: User ID (must own the key or be admin)
            api_key_id: API key ID to delete
            
        Returns:
            Tuple of (success, error_message)
        """
        api_key = ProfileService.get_api_key_by_id(user_id, api_key_id, allow_admin=True)
        if not api_key:
            return False, "API key not found or access denied"
        
        try:
            db.session.delete(api_key)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting API key: {e}", exc_info=True)
            return False, str(e)
    
    @staticmethod
    def toggle_api_key_active(user_id: int, api_key_id: int) -> Tuple[Optional[APIKey], Optional[str]]:
        """
        Toggle API key active status
        
        Args:
            user_id: User ID (must own the key or be admin)
            api_key_id: API key ID to toggle
            
        Returns:
            Tuple of (updated_api_key, error_message)
        """
        api_key = ProfileService.get_api_key_by_id(user_id, api_key_id, allow_admin=True)
        if not api_key:
            return None, "API key not found or access denied"
        
        try:
            api_key.is_active = not api_key.is_active
            db.session.commit()
            return api_key, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error toggling API key active status: {e}", exc_info=True)
            return None, str(e)
