"""
KOC A.I. Digital Campus - Flask Application Factory
Knowledge Reservoir Platform
"""
import os
import logging
from pathlib import Path
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL', 'memory://')
)


def create_app(config_name=None):
    """Create and configure Flask application"""
    # Get project root directory (one level up from app package)
    project_root = Path(__file__).parent.parent
    template_dir = str(project_root / 'templates')
    static_dir = str(project_root / 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    if config_name == 'production':
        # Validate DATABASE_URL is set in production
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable must be set in production")
        app.config.from_object('app.config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('app.config.TestingConfig')
    else:
        app.config.from_object('app.config.DevelopmentConfig')
    
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    jwt.init_app(app)
    limiter.init_app(app)
    
    # Register context processor for branding (available in all templates)
    @app.context_processor
    def inject_branding():
        """Inject branding configuration into all templates"""
        from app.services.branding_service import BrandingService
        return {'branding': BrandingService.get_branding_config()}
    
    # Register context processor for authentication (available in all templates)
    @app.context_processor
    def inject_auth():
        """Inject current user into all templates"""
        from app.services.auth_service import AuthService
        current_user = AuthService.get_current_user()
        return {'current_user': current_user}
    
    from app.routes.web.main import main_bp
    from app.routes.api.v1 import api_v1_bp
    from app.routes.web.themes import themes_bp
    from app.routes.setup import setup_bp
    from app.routes.web.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_v1_bp)
    app.register_blueprint(themes_bp)
    app.register_blueprint(setup_bp, url_prefix='/setup')
    app.register_blueprint(admin_bp)
    
    try:
        from app.routes.web.datasets import datasets_bp
        app.register_blueprint(datasets_bp, url_prefix='/data')
    except ImportError:
        pass
    
    try:
        from app.routes.web.projects import projects_bp
        app.register_blueprint(projects_bp, url_prefix='/projects')
    except ImportError:
        pass
    
    try:
        from app.routes.web.competitions import competitions_bp
        app.register_blueprint(competitions_bp, url_prefix='/competitions')
    except ImportError:
        pass
    
    try:
        from app.routes.web.leaderboards import leaderboards_bp
        app.register_blueprint(leaderboards_bp, url_prefix='/leaderboards')
    except ImportError:
        pass
    
    try:
        from app.routes.web.discussions import discussions_bp
        app.register_blueprint(discussions_bp, url_prefix='/discussions')
    except ImportError:
        pass
    
    try:
        from app.routes.web.industries import industries_bp
        app.register_blueprint(industries_bp, url_prefix='/industries')
    except ImportError:
        pass
    
    try:
        from app.routes.web.profile import profile_bp
        app.register_blueprint(profile_bp)
    except ImportError:
        pass
    
    # Register custom exception handlers
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all exceptions"""
        # Import here to avoid circular imports
        from app.exceptions import (
            AuthenticationError,
            IdentityServerError,
            TokenValidationError,
            DatabaseError,
            DatabaseConnectionError,
            DatabaseConfigurationError,
            SetupError,
            SetupValidationError
        )
        
        # Handle custom exceptions
        if isinstance(e, (SetupValidationError, AuthenticationError)):
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        
        if isinstance(e, (DatabaseConnectionError, DatabaseConfigurationError)):
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        
        if isinstance(e, IdentityServerError):
            return jsonify({
                'success': False,
                'message': str(e)
            }), 502  # Bad Gateway for external service errors
        
        if isinstance(e, SetupError):
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
        
        # Log unexpected exceptions
        app.logger.error(f"Unhandled exception: {e}", exc_info=True)
        
        # Generic error response
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    
    # Register CLI commands
    @app.cli.command('seed-demo-data')
    def seed_demo_data_command():
        """Seed demo data for the platform"""
        from scripts.seed_demo_data import seed_all
        seed_all(reset=False, users_only=False)
    
    @app.cli.command('seed-demo-data-reset')
    def seed_demo_data_reset_command():
        """Clear and reseed demo data"""
        from scripts.seed_demo_data import seed_all
        seed_all(reset=True, users_only=False)
    
    @app.cli.command('seed-demo-users')
    def seed_demo_users_command():
        """Seed only demo users"""
        from scripts.seed_demo_data import seed_all
        seed_all(reset=False, users_only=True)
    
    # Make app discoverable for Flask CLI
    # Set FLASK_APP=app or use: flask --app app:create_app <command>
    
    return app
