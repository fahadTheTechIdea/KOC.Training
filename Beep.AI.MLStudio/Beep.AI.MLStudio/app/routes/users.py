"""
User Routes
Handles user profile management and model access
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.models.auth_config import AuthConfig
import logging

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__, url_prefix='/users')


@users_bp.route('/profile/page', methods=['GET'])
def profile_page():
    """Render user profile page"""
    user = AuthService.get_current_user()
    if not user:
        return redirect(url_for('auth.login_page'))
    
    profile = UserService.get_user_profile(user.id)
    stats = UserService.get_user_statistics(user.id)
    api_keys = AuthService.get_user_api_keys(user.id)
    auth_config = AuthConfig.get_config()
    auth_mode = auth_config.auth_mode if auth_config else 'local'
    
    return render_template('users/profile.html', 
                           profile=profile, 
                           stats=stats, 
                           api_keys=api_keys,
                           auth_mode=auth_mode)


@users_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get current user profile"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    profile = UserService.get_user_profile(user.id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    return jsonify(profile.to_dict()), 200


@users_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update current user profile"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    success, error = UserService.update_user_profile(user.id, data)
    if not success:
        return jsonify({'error': error}), 400
    
    profile = UserService.get_user_profile(user.id)
    return jsonify(profile.to_dict()), 200


@users_bp.route('/models', methods=['GET'])
def get_models():
    """Get user's models (projects and experiments)"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    include_shared = request.args.get('shared', 'false').lower() == 'true'
    models = UserService.get_user_models(user.id, include_shared=include_shared)
    
    return jsonify(models), 200


@users_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get user statistics"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    stats = UserService.get_user_statistics(user.id)
    return jsonify(stats), 200
