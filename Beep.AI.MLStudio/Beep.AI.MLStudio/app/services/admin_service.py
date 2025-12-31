"""
Admin Service
Handles admin operations: user management, activity logs, system statistics
"""
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from app import db
from app.models.user import User, UserProfile
from app.models.project import MLProject
from app.models.experiment import Experiment
from app.services.user_service import UserService
import logging

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin operations"""
    
    @staticmethod
    def get_all_users(filters: Optional[Dict] = None, page: int = 1, per_page: int = 20) -> Dict:
        """
        Get all users with optional filters and pagination
        
        Args:
            filters: Optional filters (is_active, is_admin, search)
            page: Page number
            per_page: Items per page
            
        Returns:
            Dictionary with users and pagination info
        """
        query = User.query
        
        if filters:
            if filters.get('is_active') is not None:
                query = query.filter(User.is_active == filters['is_active'])
            
            if filters.get('is_admin') is not None:
                query = query.filter(User.is_admin == filters['is_admin'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    db.or_(
                        User.username.like(search_term),
                        User.email.like(search_term)
                    )
                )
        
        # Order by created_at descending
        query = query.order_by(User.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        users_data = []
        for user in pagination.items:
            user_dict = user.to_dict()
            # Add profile info
            profile = UserProfile.query.filter_by(user_id=user.id).first()
            if profile:
                user_dict['profile'] = profile.to_dict()
            users_data.append(user_dict)
        
        return {
            'users': users_data,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }
    
    @staticmethod
    def create_user(data: Dict) -> Tuple[Optional[User], Optional[str]]:
        """
        Create a new user (admin only)
        
        Args:
            data: User data (username, email, password, is_admin, profile_data)
            
        Returns:
            Tuple of (user, error_message)
        """
        return UserService.create_user(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            profile_data=data.get('profile_data'),
            is_admin=data.get('is_admin', False)
        )
    
    @staticmethod
    def update_user(user_id: int, data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Update user (admin only)
        
        Args:
            user_id: User ID
            data: Update data
            
        Returns:
            Tuple of (success, error_message)
        """
        return UserService.update_user(user_id, data)
    
    @staticmethod
    def delete_user(user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete user (admin only)
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (success, error_message)
        """
        return UserService.delete_user(user_id)
    
    @staticmethod
    def toggle_user_active(user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Toggle user active status
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            user.is_active = not user.is_active
            db.session.commit()
            
            logger.info(f"User {user_id} active status toggled to {user.is_active}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error toggling user active status: {e}")
            return False, str(e)
    
    @staticmethod
    def assign_admin_role(user_id: int, is_admin: bool) -> Tuple[bool, Optional[str]]:
        """
        Assign or remove admin role
        
        Args:
            user_id: User ID
            is_admin: Whether user should be admin
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            user.is_admin = is_admin
            db.session.commit()
            
            logger.info(f"User {user_id} admin role set to {is_admin}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning admin role: {e}")
            return False, str(e)
    
    @staticmethod
    def get_user_activity_log(user_id: int, days: int = 30) -> List[Dict]:
        """
        Get user activity log
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            List of activity entries
        """
        user = User.query.get(user_id)
        if not user:
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        activities = []
        
        # Recent projects
        recent_projects = MLProject.query.filter(
            MLProject.user_id == user_id,
            MLProject.created_at >= cutoff_date
        ).order_by(MLProject.created_at.desc()).limit(10).all()
        
        for project in recent_projects:
            activities.append({
                'type': 'project_created',
                'timestamp': project.created_at.isoformat() if project.created_at else None,
                'description': f"Created project: {project.name}",
                'entity_id': project.id,
                'entity_type': 'project'
            })
        
        # Recent experiments
        recent_experiments = Experiment.query.filter(
            Experiment.user_id == user_id,
            Experiment.created_at >= cutoff_date
        ).order_by(Experiment.created_at.desc()).limit(10).all()
        
        for experiment in recent_experiments:
            activities.append({
                'type': 'experiment_created',
                'timestamp': experiment.created_at.isoformat() if experiment.created_at else None,
                'description': f"Created experiment: {experiment.name}",
                'entity_id': experiment.id,
                'entity_type': 'experiment'
            })
        
        # Login activity
        if user.last_login_at and user.last_login_at >= cutoff_date:
            activities.append({
                'type': 'login',
                'timestamp': user.last_login_at.isoformat(),
                'description': f"Logged in (total logins: {user.login_count})",
                'entity_id': user_id,
                'entity_type': 'user'
            })
        
        # Sort by timestamp descending
        activities.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        return activities[:50]  # Return top 50 activities
    
    @staticmethod
    def get_system_statistics() -> Dict:
        """
        Get system-wide statistics
        
        Returns:
            Dictionary with system statistics
        """
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        
        total_projects = MLProject.query.count()
        active_projects = MLProject.query.filter_by(status='active').count()
        
        total_experiments = Experiment.query.count()
        completed_experiments = Experiment.query.filter_by(status='completed').count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = User.query.filter(User.created_at >= week_ago).count()
        recent_projects = MLProject.query.filter(MLProject.created_at >= week_ago).count()
        recent_experiments = Experiment.query.filter(Experiment.created_at >= week_ago).count()
        
        return {
            'users': {
                'total': total_users,
                'active': active_users,
                'admin': admin_users,
                'inactive': total_users - active_users
            },
            'projects': {
                'total': total_projects,
                'active': active_projects,
                'archived': total_projects - active_projects
            },
            'experiments': {
                'total': total_experiments,
                'completed': completed_experiments,
                'pending': Experiment.query.filter_by(status='pending').count(),
                'running': Experiment.query.filter_by(status='running').count(),
                'failed': Experiment.query.filter_by(status='failed').count()
            },
            'recent_activity': {
                'users_created': recent_users,
                'projects_created': recent_projects,
                'experiments_created': recent_experiments
            }
        }
