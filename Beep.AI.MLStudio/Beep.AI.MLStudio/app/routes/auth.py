"""
Authentication Routes
Handles login, logout, registration, and OAuth callbacks
"""
from flask import Blueprint, request, jsonify, redirect, url_for, session, render_template
from app.services.auth_service import AuthService
from app.services.microsoft_sso_service import MicrosoftSSOService
from app.models.auth_config import AuthConfig
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Login page - renders login template"""
    # If already logged in, redirect to dashboard
    user = AuthService.get_current_user()
    if user:
        return redirect(url_for('dashboard.index'))
    
    # Get auth mode to show appropriate login options
    auth_mode = AuthService.get_auth_mode()
    
    # If Identity Server or Microsoft SSO, redirect to OAuth flow
    if auth_mode == 'identity_server':
        return redirect(url_for('auth.identity_server_login'))
    elif auth_mode == 'microsoft_sso':
        return redirect(url_for('auth.microsoft_login'))
    
    return render_template('auth/login.html', auth_mode=auth_mode)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint - supports local JWT, Identity Server, and Microsoft SSO"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    username_or_email = data.get('username') or data.get('email')
    password = data.get('password')
    access_token = data.get('access_token')  # For Identity Server
    code = data.get('code')  # For Microsoft SSO
    state = data.get('state')  # For Microsoft SSO
    
    auth_mode = AuthService.get_auth_mode()
    
    if auth_mode == 'local':
        # Local JWT authentication
        if not username_or_email or not password:
            return jsonify({'error': 'Username/email and password required'}), 400
        
        result, error = AuthService.login_user(username_or_email, password)
        if error:
            return jsonify({'error': error}), 401
        
        return jsonify(result), 200
    
    elif auth_mode == 'identity_server':
        # Identity Server OAuth authentication
        if not access_token:
            return jsonify({'error': 'Access token required'}), 400
        
        result, error = AuthService.login_with_identity_server(access_token)
        if error:
            return jsonify({'error': error}), 401
        
        return jsonify(result), 200
    
    elif auth_mode == 'microsoft_sso':
        # Microsoft SSO authentication
        if not code:
            return jsonify({'error': 'Authorization code required'}), 400
        
        result, error = AuthService.login_with_microsoft(code, state)
        if error:
            return jsonify({'error': error}), 401
        
        return jsonify(result), 200
    
    else:
        return jsonify({'error': 'Unknown authentication mode'}), 400


@auth_bp.route('/register', methods=['GET'])
def register_page():
    """Registration page - renders register template"""
    # If already logged in, redirect to dashboard
    user = AuthService.get_current_user()
    if user:
        return redirect(url_for('dashboard.index'))
    
    # Only available in local mode
    if AuthService.get_auth_mode() != 'local':
        from flask import flash
        flash('Registration is only available in local authentication mode', 'warning')
        return redirect(url_for('auth.login_page'))
    
    return render_template('auth/register.html')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user (local mode only)"""
    from flask import flash
    
    if AuthService.get_auth_mode() != 'local':
        if request.is_json:
            return jsonify({'error': 'Registration only available in local mode'}), 403
        flash('Registration is only available in local authentication mode', 'error')
        return redirect(url_for('auth.login_page'))
    
    # Handle JSON API request
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        display_name = data.get('display_name')
    else:
        # Handle form submission
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        display_name = request.form.get('display_name')
    
    if not username or not email or not password:
        if request.is_json:
            return jsonify({'error': 'Username, email, and password required'}), 400
        flash('Username, email, and password are required', 'error')
        return redirect(url_for('auth.register_page'))
    
    profile_data = {'display_name': display_name} if display_name else None
    user, error = AuthService.register_user(username, email, password, profile_data=profile_data)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('auth.register_page'))
    
    if request.is_json:
        return jsonify({'message': 'User registered successfully', 'user': user.to_dict()}), 201
    
    flash('Account created successfully! Please log in.', 'success')
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logout endpoint - handles both GET (from navbar link) and POST"""
    # Clear session
    session.clear()
    
    # For API requests, return JSON
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({'message': 'Logged out successfully'}), 200
    
    # For web requests, redirect to login page
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/identity-server/login', methods=['GET'])
def identity_server_login():
    """Initiate Identity Server OAuth flow"""
    if AuthService.get_auth_mode() != 'identity_server':
        return redirect(url_for('auth.login_page'))
    
    try:
        from app.services.identity_server_auth_service import IdentityServerAuthService
        service = IdentityServerAuthService()
        auth_url = service.get_authorization_url()
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error initiating Identity Server login: {e}")
        return redirect(url_for('auth.login_page', error='Failed to initiate Identity Server login'))


@auth_bp.route('/identity-server/callback', methods=['GET'])
def identity_server_callback():
    """Handle Identity Server OAuth callback"""
    if AuthService.get_auth_mode() != 'identity_server':
        return redirect(url_for('auth.login_page'))
    
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return redirect(url_for('auth.login_page', error=f'OAuth error: {error}'))
    
    if not code:
        return redirect(url_for('auth.login_page', error='Authorization code missing'))
    
    try:
        from app.services.identity_server_auth_service import IdentityServerAuthService
        service = IdentityServerAuthService()
        result, error_msg = service.handle_callback(code)
        
        if error_msg:
            return redirect(url_for('auth.login_page', error=error_msg))
        
        # Store token and redirect to dashboard
        if result and result.get('access_token'):
            session['access_token'] = result['access_token']
            return redirect(url_for('dashboard.index'))
        else:
            return redirect(url_for('auth.login_page', error='Failed to authenticate'))
    except Exception as e:
        logger.error(f"Error handling Identity Server callback: {e}")
        return redirect(url_for('auth.login_page', error='Authentication failed'))


@auth_bp.route('/microsoft/login', methods=['GET'])
def microsoft_login():
    """Initiate Microsoft Azure SSO flow"""
    if AuthService.get_auth_mode() != 'microsoft_sso':
        return redirect(url_for('auth.login_page'))
    
    try:
        service = MicrosoftSSOService()
        auth_url = service.get_auth_url()
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error initiating Microsoft login: {e}")
        return redirect(url_for('auth.login_page', error='Failed to initiate Microsoft login'))


@auth_bp.route('/microsoft/authorize', methods=['GET'])
def microsoft_authorize():
    """Get Microsoft Azure AD authorization URL"""
    if AuthService.get_auth_mode() != 'microsoft_sso':
        return jsonify({'error': 'Microsoft SSO not enabled'}), 403
    
    try:
        service = MicrosoftSSOService()
        state = request.args.get('state', '')
        redirect_uri = request.args.get('redirect_uri')
        
        auth_url = service.get_authorization_url(redirect_uri, state)
        return jsonify({'authorization_url': auth_url}), 200
    except Exception as e:
        logger.error(f"Error getting Microsoft authorization URL: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/microsoft/callback', methods=['GET'])
def microsoft_callback():
    """Handle Microsoft OAuth callback"""
    if AuthService.get_auth_mode() != 'microsoft_sso':
        return redirect(url_for('auth.login_page', error='Microsoft SSO not enabled'))
    
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return redirect(url_for('auth.login_page', error=f'OAuth error: {error}'))
    
    if not code:
        return redirect(url_for('auth.login_page', error='Authorization code missing'))
    
    result, error_msg = AuthService.login_with_microsoft(code, state)
    if error_msg:
        return redirect(url_for('auth.login_page', error=error_msg))
    
    # Store token and redirect to dashboard
    if result and result.get('access_token'):
        session['access_token'] = result['access_token']
        return redirect(url_for('dashboard.index'))
    else:
        return redirect(url_for('auth.login_page', error='Failed to authenticate'))


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current authenticated user"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_dict = user.to_dict()
    # Add profile if exists
    if hasattr(user, 'profile') and user.profile:
        user_dict['profile'] = user.profile.to_dict()
    
    return jsonify(user_dict), 200


@auth_bp.route('/api-keys', methods=['GET'])
def get_api_keys():
    """Get user's API keys"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    keys = AuthService.get_user_api_keys(user.id)
    return jsonify({'api_keys': keys}), 200


@auth_bp.route('/api-keys', methods=['POST'])
def create_api_key():
    """Create a new API key"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    key_name = data.get('key_name', 'Default API Key')
    
    key_obj, error = AuthService.create_api_key(user.id, key_name)
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({'api_key': key_obj.to_dict()}), 201


@auth_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
def revoke_api_key(key_id):
    """Revoke an API key"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    success, error = AuthService.revoke_api_key(user.id, key_id)
    if not success:
        return jsonify({'error': error}), 404
    
    return jsonify({'message': 'API key revoked'}), 200


@auth_bp.route('/api-key/generate', methods=['POST'])
def generate_api_key():
    """Generate a new API key (alias for create_api_key)"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json() or {}
    key_name = data.get('key_name', 'API Key')
    
    key_obj, error = AuthService.create_api_key(user.id, key_name)
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({'api_key': key_obj.api_key, 'key': key_obj.to_dict()}), 201


@auth_bp.route('/api-key/revoke/<int:key_id>', methods=['POST'])
def revoke_api_key_post(key_id):
    """Revoke an API key (POST method for compatibility)"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    success, error = AuthService.revoke_api_key(user.id, key_id)
    if not success:
        return jsonify({'error': error}), 404
    
    return jsonify({'message': 'API key revoked'}), 200


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password (local mode only)"""
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if AuthService.get_auth_mode() != 'local':
        return jsonify({'error': 'Password change only available in local mode'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password required'}), 400
    
    # Verify current password
    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Set new password
    user.set_password(new_password)
    
    try:
        from app import db
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        from app import db
        db.session.rollback()
        logger.error(f"Error changing password: {e}")
        return jsonify({'error': 'Failed to change password'}), 500
