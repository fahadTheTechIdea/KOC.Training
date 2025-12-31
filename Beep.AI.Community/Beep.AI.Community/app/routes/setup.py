"""
Setup Wizard Routes
Refactored to use services and utilities for better separation of concerns
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import uuid
from app import db
from app.services.auth_service import AuthService
from app.models.user import ROLE_ADMIN
from app.services.branding_service import BrandingService
from app.services.setup_service import SetupService
from app.utils.database_provider import DatabaseProviderHelper
from app.utils.request_validators import (
    validate_json_request,
    sanitize_string_input,
    validate_email_field,
    validate_username_field,
    validate_password_field,
    error_handler
)
from app.exceptions.setup_exceptions import (
    SetupValidationError,
    SetupConfigurationError,
    SetupCompleteError
)
from app.exceptions.database_exceptions import (
    UnsupportedDatabaseProviderError,
    DatabaseConnectionError,
    DatabaseConfigurationError
)
from app.exceptions.auth_exceptions import IdentityServerError
from app.utils.constants import (
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    MSG_ADMIN_CREATED,
    MSG_SETUP_COMPLETE
)
import logging

logger = logging.getLogger(__name__)

setup_bp = Blueprint('setup', __name__)
setup_service = SetupService()


@setup_bp.route('/')
def index():
    """Setup wizard entry point"""
    if setup_service.is_setup_complete():
        return redirect(url_for('main.index'))
    
    return render_template('setup.html')


@setup_bp.route('/api/check-status')
def check_status():
    """Check setup status"""
    status = setup_service.get_setup_status()
    return jsonify(status)


@setup_bp.route('/api/step1-admin', methods=['POST'])
@error_handler
@validate_json_request(required_fields=['username', 'email', 'password'])
@sanitize_string_input(['username', 'email'])
@validate_username_field('username')
@validate_email_field('email')
@validate_password_field('password')
def step1_admin():
    """Step 1: Create admin user"""
    data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password', '')
    
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'}), HTTP_BAD_REQUEST
    
    user, error = AuthService.register_user(username, email, password, role=ROLE_ADMIN)
    if error:
        return jsonify({'success': False, 'message': error}), HTTP_BAD_REQUEST
    
    # Set both role and is_admin for backward compatibility
    user.role = ROLE_ADMIN
    user.is_admin = True
    db.session.commit()
    
    logger.info(f"Admin user created: {username}")
    return jsonify({'success': True, 'message': MSG_ADMIN_CREATED})


@setup_bp.route('/api/step2-database', methods=['POST'])
@error_handler
@validate_json_request(required_fields=['provider'])
@sanitize_string_input(['provider', 'connection_string'])
def step2_database():
    """Step 2: Configure database"""
    data = request.get_json()
    
    provider = data.get('provider', 'sqlite').lower()
    connection_string = data.get('connection_string', '').strip() if data.get('connection_string') else None
    
    try:
        success, message = setup_service.configure_database(provider, connection_string)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), HTTP_BAD_REQUEST
    except (UnsupportedDatabaseProviderError, DatabaseConfigurationError, DatabaseConnectionError) as e:
        return jsonify({'success': False, 'message': str(e)}), HTTP_BAD_REQUEST


@setup_bp.route('/api/step2-database/test', methods=['POST'])
@error_handler
@validate_json_request(required_fields=['provider', 'connection_string'])
@sanitize_string_input(['provider', 'connection_string'])
def step2_database_test():
    """Test database connection"""
    data = request.get_json()
    
    provider = data.get('provider', 'sqlite').lower()
    connection_string = data.get('connection_string', '').strip()
    
    success, error = setup_service.test_database_connection(provider, connection_string)
    if success:
        return jsonify({'success': True, 'message': 'Connection successful'})
    else:
        return jsonify({'success': False, 'message': error or 'Connection failed'}), HTTP_BAD_REQUEST


@setup_bp.route('/api/database-providers')
def get_database_providers():
    """Get available database providers"""
    providers = DatabaseProviderHelper.get_supported_providers()
    result = {}
    for key, value in providers.items():
        result[key] = {
            'name': value['name'],
            'description': value['description'],
            'example': value['connection_string_example']
        }
    return jsonify({'providers': result})


@setup_bp.route('/api/step3-auth', methods=['POST'])
@error_handler
@validate_json_request(required_fields=['auth_mode'])
@sanitize_string_input(['auth_mode', 'identity_server_url', 'client_id', 'client_secret', 'redirect_uris'])
def step3_auth():
    """Step 3: Configure authentication mode"""
    data = request.get_json()
    
    auth_mode = data.get('auth_mode', 'local').lower()
    identity_url = data.get('identity_server_url')
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    redirect_uris = data.get('redirect_uris')
    
    try:
        success, message = setup_service.configure_authentication(
            auth_mode=auth_mode,
            identity_server_url=identity_url,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uris=redirect_uris
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), HTTP_BAD_REQUEST
            
    except (SetupValidationError, IdentityServerError) as e:
        return jsonify({'success': False, 'message': str(e)}), HTTP_BAD_REQUEST


@setup_bp.route('/api/step3-auth/test', methods=['POST'])
@error_handler
@validate_json_request(required_fields=['identity_server_url', 'client_id'])
@sanitize_string_input(['identity_server_url', 'client_id', 'client_secret'])
def step3_auth_test():
    """Test Identity Server connection"""
    data = request.get_json()
    
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
        return jsonify({'success': False, 'message': message}), HTTP_BAD_REQUEST


@setup_bp.route('/api/step5-branding', methods=['POST'])
@error_handler
def step5_branding():
    """Step 5: Configure branding with file upload support"""
    # Handle both JSON (legacy) and multipart/form-data (file upload)
    if request.is_json:
        # Legacy JSON support (for backward compatibility)
        data = request.get_json()
        industry = data.get('industry', 'general')
        company_name = data.get('company_name', '').strip() or None
        logo_path = data.get('logo_path')
        icon_name = data.get('icon_name', '').strip() or None
    else:
        # Multipart/form-data (file upload)
        industry = request.form.get('industry', 'general')
        company_name = request.form.get('company_name', '').strip() or None
        icon_name = request.form.get('icon_name', '').strip() or None
        
        # Handle logo file upload
        logo_file = request.files.get('logo')
        logo_path = None
        
        if logo_file and logo_file.filename:
            # Validate file type
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp'}
            file_ext = Path(logo_file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                return jsonify({
                    'success': False,
                    'message': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
                }), HTTP_BAD_REQUEST
            
            # Validate file size (max 5MB)
            logo_file.seek(0, os.SEEK_END)
            file_size = logo_file.tell()
            logo_file.seek(0)
            if file_size > 5 * 1024 * 1024:  # 5MB
                return jsonify({
                    'success': False,
                    'message': 'File size exceeds 5MB limit'
                }), HTTP_BAD_REQUEST
            
            # Save uploaded file
            upload_dir = Path('static/assets/images/branding')
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename to avoid conflicts
            unique_id = str(uuid.uuid4())[:8]
            original_name = secure_filename(logo_file.filename)
            file_stem = Path(original_name).stem
            saved_filename = f"{file_stem}_{unique_id}{file_ext}"
            logo_path = upload_dir / saved_filename
            
            try:
                logo_file.save(str(logo_path))
                logo_path = str(logo_path)  # Convert to string for service
                logger.info(f"Logo file uploaded: {logo_path}")
            except Exception as e:
                logger.error(f"Error saving logo file: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Failed to save logo file: {str(e)}'
                }), HTTP_BAD_REQUEST
    
    # Validate required fields
    if not industry:
        return jsonify({
            'success': False,
            'message': 'Industry is required'
        }), HTTP_BAD_REQUEST
    
    try:
        config = BrandingService.setup_industry_branding(
            industry=industry,
            company_name=company_name,
            logo_path=logo_path if logo_path else None,
            icon_name=icon_name
        )
        
        logger.info(f"Branding configured: industry={industry}, icon={icon_name}, logo={logo_path is not None}")
        return jsonify({
            'success': True,
            'message': 'Branding configured successfully',
            'branding': config.to_dict()
        })
    except Exception as e:
        logger.error(f"Error configuring branding: {e}", exc_info=True)
        # Clean up uploaded file if branding configuration failed
        if logo_path and Path(logo_path).exists():
            try:
                Path(logo_path).unlink()
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup uploaded logo file: {cleanup_error}")
        return jsonify({
            'success': False,
            'message': f'Failed to configure branding: {str(e)}'
        }), HTTP_BAD_REQUEST


@setup_bp.route('/api/step6-complete', methods=['POST'])
@error_handler
def step6_complete():
    """Step 6: Complete setup - Create database schema"""
    try:
        # Reload environment variables
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        # Update app config with new database URL
        db_url = os.getenv('DATABASE_URL', 'sqlite:///community.db')
        current_app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        
        # Create all database tables
        db.create_all()
        
        # Mark setup as complete using service
        success, message = setup_service.complete_setup()
        
        if success:
            logger.info("Setup completed successfully")
            return jsonify({
                'success': True,
                'message': MSG_SETUP_COMPLETE,
                'redirect': url_for('main.index')
            })
        else:
            raise SetupCompleteError(message)
            
    except SetupCompleteError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), HTTP_INTERNAL_SERVER_ERROR
    except Exception as e:
        logger.error(f"Unexpected error completing setup: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Failed to complete setup: {str(e)}'
        }), HTTP_INTERNAL_SERVER_ERROR


@setup_bp.route('/api/industries')
def get_industries():
    """Get available industry presets"""
    industries = BrandingService.get_available_industries()
    return jsonify({'industries': industries})


@setup_bp.route('/api/industries/<industry>/icons')
def get_industry_icons(industry):
    """Get available icons for a specific industry"""
    icons = BrandingService.get_available_icons_for_industry(industry)
    return jsonify({'icons': icons})
