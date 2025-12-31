"""
Admin Routes
Handles admin operations: user management, statistics, global server management
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from app.services.auth_service import AuthService
from app.services.admin_service import AdminService
from app.services.community_server_service import CommunityServerService
from app.models.auth_config import AuthConfig
from app import db
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_admin():
    """Helper to check admin access"""
    user = AuthService.get_current_user()
    if not user:
        return None, jsonify({'error': 'Not authenticated'}), 401
    if not user.is_admin:
        return None, jsonify({'error': 'Admin access required'}), 403
    return user, None, None


@admin_bp.route('/users/page', methods=['GET'])
def users_page():
    """Render admin user management page"""
    user = AuthService.get_current_user()
    if not user:
        return redirect(url_for('auth.login_page'))
    if not user.is_admin:
        return redirect(url_for('dashboard.index'))
    
    stats = AdminService.get_system_statistics()
    return render_template('admin/users.html', stats=stats)


@admin_bp.route('/auth/config/page', methods=['GET'])
def auth_config_page():
    """Render authentication configuration page"""
    user = AuthService.get_current_user()
    if not user:
        return redirect(url_for('auth.login_page'))
    if not user.is_admin:
        return redirect(url_for('dashboard.index'))
    
    config = AuthConfig.get_config()
    return render_template('admin/auth_config.html', config=config)


@admin_bp.route('/community-servers/page', methods=['GET'])
def community_servers_page():
    """Render community servers management page"""
    user = AuthService.get_current_user()
    if not user:
        return redirect(url_for('auth.login_page'))
    if not user.is_admin:
        return redirect(url_for('dashboard.index'))
    
    servers = CommunityServerService.get_global_servers()
    return render_template('admin/community_servers.html', servers=servers)


@admin_bp.route('/users', methods=['GET'])
def list_users():
    """List all users with filters and pagination"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {
        'is_active': request.args.get('is_active')
    }
    if filters['is_active'] is not None:
        filters['is_active'] = filters['is_active'].lower() == 'true'
    
    filters['is_admin'] = request.args.get('is_admin')
    if filters['is_admin'] is not None:
        filters['is_admin'] = filters['is_admin'].lower() == 'true'
    
    filters['search'] = request.args.get('search')
    
    result = AdminService.get_all_users(filters=filters, page=page, per_page=per_page)
    return jsonify(result), 200


@admin_bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    new_user, error = AdminService.create_user(data)
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({'user': new_user.to_dict()}), 201


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user details"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    target_user = AdminService.get_all_users(filters={'search': str(user_id)}, page=1, per_page=1)
    if not target_user['users']:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(target_user['users'][0]), 200


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    success, error = AdminService.update_user(user_id, data)
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'User updated successfully'}), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    success, error = AdminService.delete_user(user_id)
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'User deleted successfully'}), 200


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
def toggle_user_active(user_id):
    """Toggle user active status"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    success, error = AdminService.toggle_user_active(user_id)
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'User active status toggled'}), 200


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
def toggle_admin_role(user_id):
    """Toggle admin role"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    data = request.get_json()
    is_admin = data.get('is_admin', True) if data else True
    
    success, error = AdminService.assign_admin_role(user_id, is_admin)
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'Admin role updated'}), 200


@admin_bp.route('/users/<int:user_id>/activity', methods=['GET'])
def get_user_activity(user_id):
    """Get user activity log"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    days = request.args.get('days', 30, type=int)
    activities = AdminService.get_user_activity_log(user_id, days=days)
    
    return jsonify({'activities': activities}), 200


@admin_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    stats = AdminService.get_system_statistics()
    return jsonify(stats), 200


@admin_bp.route('/community-servers', methods=['GET'])
def list_global_servers():
    """List all global community servers"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    servers = CommunityServerService.get_global_servers()
    return jsonify({'servers': [s.to_dict() for s in servers]}), 200


@admin_bp.route('/community-servers', methods=['POST'])
def create_global_server():
    """Create a global community server"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    server, error = CommunityServerService.create_global_server(data, created_by=user.id)
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({'server': server.to_dict()}), 201


@admin_bp.route('/community-servers/<int:server_id>', methods=['PUT'])
def update_global_server(server_id):
    """Update a global community server"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    success, error = CommunityServerService.update_global_server(server_id, data)
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'Server updated successfully'}), 200


@admin_bp.route('/community-servers/<int:server_id>', methods=['DELETE'])
def delete_global_server(server_id):
    """Delete a global community server"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    success, error = CommunityServerService.delete_global_server(server_id)
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'Server deleted successfully'}), 200


@admin_bp.route('/auth/config', methods=['GET'])
def get_auth_config():
    """Get authentication configuration"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    config = AuthConfig.get_config()
    return jsonify(config.to_dict(include_secrets=False)), 200


@admin_bp.route('/auth/config', methods=['PUT'])
def update_auth_config():
    """Update authentication configuration"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    config = AuthConfig.get_config()
    
    if 'auth_mode' in data:
        config.auth_mode = data['auth_mode']
    
    if 'identity_server_url' in data:
        config.identity_server_url = data['identity_server_url']
    
    if 'identity_server_client_id' in data:
        config.identity_server_client_id = data['identity_server_client_id']
    
    if 'identity_server_client_secret' in data:
        config.set_identity_server_client_secret(data['identity_server_client_secret'])
    
    if 'microsoft_tenant_id' in data:
        config.microsoft_tenant_id = data['microsoft_tenant_id']
    
    if 'microsoft_client_id' in data:
        config.microsoft_client_id = data['microsoft_client_id']
    
    if 'microsoft_client_secret' in data:
        config.set_microsoft_client_secret(data['microsoft_client_secret'])
    
    if 'microsoft_redirect_uri' in data:
        config.microsoft_redirect_uri = data['microsoft_redirect_uri']
    
    if 'jwt_secret_key' in data:
        config.set_jwt_secret_key(data['jwt_secret_key'])
    
    if 'jwt_token_expires' in data:
        config.jwt_token_expires = data['jwt_token_expires']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Auth config updated successfully', 'config': config.to_dict(include_secrets=False)}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating auth config: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/auth/test-identity-server', methods=['POST'])
def test_identity_server():
    """Test Identity Server connection"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    config = AuthConfig.get_config()
    if not config.identity_server_url:
        return jsonify({'error': 'Identity Server URL not configured'}), 400
    
    from app.clients.identity_server_client import IdentityServerClient
    client = IdentityServerClient()
    success, error = client.health_check()
    
    if success:
        return jsonify({'message': 'Connection successful'}), 200
    else:
        return jsonify({'error': error}), 400


@admin_bp.route('/auth/test-microsoft-sso', methods=['POST'])
def test_microsoft_sso():
    """Test Microsoft SSO connection"""
    user, error_response, status = require_admin()
    if error_response:
        return error_response, status
    
    config = AuthConfig.get_config()
    if not config.microsoft_tenant_id or not config.microsoft_client_id:
        return jsonify({'error': 'Microsoft SSO not fully configured'}), 400
    
    # Just validate configuration, can't test without OAuth flow
    return jsonify({'message': 'Configuration valid (test requires OAuth flow)'}), 200
