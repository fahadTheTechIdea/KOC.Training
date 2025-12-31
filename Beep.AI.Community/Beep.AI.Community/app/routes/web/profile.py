"""
Profile Routes - User profile pages
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.profile_service import ProfileService
from app.services.auth_service import AuthService
from app.utils.request_validators import error_handler
import logging

logger = logging.getLogger(__name__)

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@jwt_required(optional=True)
@error_handler
def view_own():
    """View own profile (redirects to username route)"""
    current_user = AuthService.get_current_user()
    if not current_user:
        flash('Please log in to view your profile', 'info')
        return redirect(url_for('main.login_page'))
    
    return redirect(url_for('profile.view', username=current_user.username))


@profile_bp.route('/profile/<username>')
@jwt_required(optional=True)
@error_handler
def view(username):
    """View user profile"""
    current_user = AuthService.get_current_user()
    user = ProfileService.get_user_profile(username)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('main.index'))
    
    can_edit = ProfileService.can_edit_profile(current_user, user)
    stats = ProfileService.get_user_stats(user.id)
    
    return render_template('profile/index.html',
                         user=user,
                         current_user=current_user,
                         can_edit=can_edit,
                         stats=stats)


@profile_bp.route('/profile/edit')
@jwt_required()
@error_handler
def edit_form():
    """Show profile edit form"""
    user_id = get_jwt_identity()
    user = ProfileService.get_user_by_id(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('profile/edit.html', user=user)


@profile_bp.route('/profile', methods=['POST'])
@jwt_required()
@error_handler
def update():
    """Update user profile"""
    user_id = get_jwt_identity()
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    profile, error = ProfileService.update_user_profile(user_id, data)
    if error:
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('profile.edit_form'))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'profile': profile.to_dict()
        })
    
    flash('Profile updated successfully', 'success')
    user = ProfileService.get_user_by_id(user_id)
    return redirect(url_for('profile.view', username=user.username))


# ==================== API Key Management ====================

@profile_bp.route('/profile/api-keys', methods=['POST'])
@jwt_required()
@error_handler
def generate_api_key():
    """Generate a new API key for the current user"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or 'key_name' not in data:
        return jsonify({'success': False, 'error': 'Key name is required'}), 400
    
    key_name = data['key_name'].strip()
    if not key_name:
        return jsonify({'success': False, 'error': 'Key name cannot be empty'}), 400
    
    api_key, error = ProfileService.generate_api_key(user_id, key_name)
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    # Return the API key once (only time it will be shown)
    return jsonify({
        'success': True,
        'message': 'API key generated successfully. Copy it now - you won\'t be able to see it again!',
        'api_key': {
            'id': api_key.id,
            'key_name': api_key.key_name,
            'api_key': api_key.api_key,  # Show full key only once
            'created_at': api_key.created_at.isoformat() if api_key.created_at else None,
            'is_active': api_key.is_active
        }
    })


@profile_bp.route('/profile/api-keys', methods=['GET'])
@jwt_required()
@error_handler
def list_api_keys():
    """List all API keys for the current user"""
    user_id = int(get_jwt_identity())
    api_keys = ProfileService.get_user_api_keys(user_id)
    
    # Mask API keys for security (only show first 8 characters)
    keys_data = []
    for key in api_keys:
        masked_key = key.api_key[:8] + '...' if len(key.api_key) > 8 else key.api_key
        keys_data.append({
            'id': key.id,
            'key_name': key.key_name,
            'api_key_masked': masked_key,
            'is_active': key.is_active,
            'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
            'created_at': key.created_at.isoformat() if key.created_at else None
        })
    
    return jsonify({
        'success': True,
        'api_keys': keys_data
    })


@profile_bp.route('/profile/api-keys/<int:api_key_id>', methods=['DELETE'])
@jwt_required()
@error_handler
def delete_api_key(api_key_id):
    """Delete an API key"""
    user_id = int(get_jwt_identity())
    
    success, error = ProfileService.delete_api_key(user_id, api_key_id)
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    return jsonify({
        'success': True,
        'message': 'API key deleted successfully'
    })


@profile_bp.route('/profile/api-keys/<int:api_key_id>/toggle-active', methods=['POST'])
@jwt_required()
@error_handler
def toggle_api_key_active(api_key_id):
    """Toggle API key active status"""
    user_id = int(get_jwt_identity())
    
    api_key, error = ProfileService.toggle_api_key_active(user_id, api_key_id)
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    return jsonify({
        'success': True,
        'message': f'API key {"activated" if api_key.is_active else "deactivated"} successfully',
        'is_active': api_key.is_active
    })
