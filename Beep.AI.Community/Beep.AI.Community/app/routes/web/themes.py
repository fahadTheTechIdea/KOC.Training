"""
Theme routes for dynamic theming
"""
import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.theme_service import ThemeService
from app.services.branding_service import BrandingService

logger = logging.getLogger(__name__)
themes_bp = Blueprint('themes', __name__)


@themes_bp.route('/api/themes')
def list_themes():
    """Get all available themes"""
    themes = ThemeService.get_all_themes()
    return jsonify({
        'themes': {k: {'name': v['name']} for k, v in themes.items()},
        'current_theme': 'default'
    })


@themes_bp.route('/api/themes/<theme_name>')
def get_theme(theme_name):
    """Get theme configuration"""
    theme = ThemeService.get_theme(theme_name)
    if not theme:
        return jsonify({'error': 'Theme not found'}), 404
    
    css = ThemeService.generate_theme_css(theme_name)
    
    return jsonify({
        'theme': theme,
        'css': css
    })


@themes_bp.route('/api/themes/<theme_name>/css')
def get_theme_css(theme_name):
    """Get theme CSS"""
    css = ThemeService.generate_theme_css(theme_name)
    return css, 200, {'Content-Type': 'text/css'}


@themes_bp.route('/api/user/theme', methods=['POST'])
@jwt_required()
def set_user_theme():
    """Set user's preferred theme"""
    user_id = get_jwt_identity()
    data = request.get_json()
    theme_name = data.get('theme', 'default')
    
    if theme_name not in ThemeService.get_all_themes():
        return jsonify({'error': 'Invalid theme'}), 400
    
    ThemeService.save_user_theme(user_id, theme_name)
    return jsonify({'message': 'Theme saved', 'theme': theme_name})


@themes_bp.route('/api/user/theme')
@jwt_required()
def get_user_theme():
    """Get user's preferred theme"""
    user_id = get_jwt_identity()
    theme_name = ThemeService.get_user_theme(user_id)
    theme = ThemeService.get_theme(theme_name)
    
    return jsonify({
        'theme_name': theme_name,
        'theme': theme,
        'css': ThemeService.generate_theme_css(theme_name)
    })


@themes_bp.route('/api/themes/update-branding', methods=['POST'])
@jwt_required()
def update_branding_theme():
    """
    Update branding configuration theme_name and sync to Identity Server if configured
    This endpoint updates the application-level branding config when users switch themes
    """
    data = request.get_json()
    theme_name = data.get('theme_name') if data else None
    
    if not theme_name:
        return jsonify({'error': 'theme_name is required'}), 400
    
    # Validate theme name
    available_themes = ThemeService.get_all_themes()
    if theme_name not in available_themes:
        return jsonify({'error': f'Invalid theme name: {theme_name}'}), 400
    
    try:
        # Get current branding config
        config = BrandingService.get_branding_config()
        
        # Update theme_name
        config.theme_name = theme_name
        config.synchronize_properties()
        
        # Save branding config
        BrandingService.save_branding_config(config)
        
        # Sync to Identity Server if configured
        BrandingService.sync_branding_to_identity_server(config)
        
        logger.info(f"Branding theme updated to: {theme_name}")
        
        return jsonify({
            'success': True,
            'message': 'Branding theme updated successfully',
            'theme_name': theme_name
        })
    except Exception as e:
        logger.error(f"Error updating branding theme: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to update branding theme: {str(e)}'
        }), 500
