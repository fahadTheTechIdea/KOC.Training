"""
Setup Wizard Routes
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from app import db
from app.services.auth_service import AuthService
from app.services.setup_service import SetupService
from app.models.auth_config import AuthConfig
import logging

logger = logging.getLogger(__name__)

setup_bp = Blueprint('setup', __name__)
setup_service = SetupService()


@setup_bp.route('/')
def index():
    """Setup wizard entry point"""
    if setup_service.is_setup_complete():
        return redirect(url_for('dashboard.index'))
    
    return render_template('setup.html')


@setup_bp.route('/api/check-status')
def check_status():
    """Check setup status"""
    status = setup_service.get_setup_status()
    return jsonify(status)


@setup_bp.route('/api/step1-admin', methods=['POST'])
def step1_admin():
    """Step 1: Create admin user"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password', '')
    
    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
    
    # Create admin user
    from app.services.user_service import UserService
    user, error = UserService.create_user(
        username=username,
        email=email,
        password=password,
        profile_data={'display_name': username},
        is_admin=True
    )
    
    if error:
        return jsonify({'success': False, 'message': error}), 400
    
    logger.info(f"Admin user created: {username}")
    return jsonify({'success': True, 'message': 'Admin user created successfully'})


@setup_bp.route('/api/step2-auth', methods=['POST'])
def step2_auth():
    """Step 2: Configure authentication mode"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400
    
    auth_mode = data.get('auth_mode', 'local').lower()
    
    success, message = setup_service.configure_authentication(
        auth_mode=auth_mode,
        identity_server_url=data.get('identity_server_url'),
        client_id=data.get('client_id'),
        client_secret=data.get('client_secret'),
        microsoft_tenant_id=data.get('microsoft_tenant_id'),
        microsoft_client_id=data.get('microsoft_client_id'),
        microsoft_client_secret=data.get('microsoft_client_secret'),
        microsoft_redirect_uri=data.get('microsoft_redirect_uri'),
        jwt_secret_key=data.get('jwt_secret_key')
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400


@setup_bp.route('/api/step2-auth/test', methods=['POST'])
def step2_auth_test():
    """Test Identity Server connection"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400
    
    identity_url = data.get('identity_server_url', '').strip()
    client_id = data.get('client_id', '').strip()
    client_secret = data.get('client_secret', '').strip()
    
    success, message = setup_service.test_identity_server_connection(
        identity_url,
        client_id,
        client_secret
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400


@setup_bp.route('/api/step3-complete', methods=['POST'])
def step3_complete():
    """Step 3: Complete setup - Create database schema"""
    try:
        # Create all database tables
        db.create_all()
        
        # Mark setup as complete
        success, message = setup_service.complete_setup()
        
        if success:
            logger.info("Setup completed successfully")
            return jsonify({
                'success': True,
                'message': 'Setup completed successfully',
                'redirect': url_for('dashboard.index')
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error completing setup: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to complete setup: {str(e)}'
        }), 500
