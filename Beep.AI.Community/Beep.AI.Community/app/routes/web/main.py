"""
Main web routes
"""
from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies
from pathlib import Path
import os
import json
import logging
import requests
from urllib.parse import urlencode
from app.services.branding_service import BrandingService
from app.services.dataset_service import DatasetService
from app.services.project_service import ProjectService
from app.services.competition_service import CompetitionService
from app.services.auth_service import AuthService
from app.utils.constants import (
    AUTH_MODE_IDENTITY_SERVER,
    ENV_IDENTITY_SERVER_URL,
    ENV_IDENTITY_SERVER_CLIENT_ID
)

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


def _is_setup_complete():
    """Check if setup is complete"""
    config_file = Path('instance') / 'setup_complete.json'
    if not config_file.exists():
        return False
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
            return data.get('setup_complete', False)
    except:
        return False


@main_bp.route('/')
def index():
    """Home page - shows landing page for non-authenticated users, dashboard for authenticated"""
    if not _is_setup_complete():
        return redirect(url_for('setup.index'))
    
    # Check if user is authenticated
    current_user = AuthService.get_current_user()
    
    # Show landing page for non-authenticated users or if explicitly requested
    show_landing = request.args.get('landing', 'false').lower() == 'true'
    if not current_user or show_landing:
        branding = BrandingService.get_branding_config()
        competition_service = CompetitionService()
        competitions, _ = competition_service.list_competitions(is_active=True, page=1, per_page=3)
        
        # Get leaderboard data for landing page
        from app.routes.web.leaderboards import get_global_leaderboard, get_competition_leaderboard
        top_performers = get_global_leaderboard(limit=5)
        recent_winners = []
        
        # Get recent winners from active competitions
        if competitions:
            for comp in competitions[:3]:  # Check top 3 active competitions
                comp_leaderboard = get_competition_leaderboard(comp.id, limit=1)
                if comp_leaderboard and len(comp_leaderboard) > 0:
                    winner = comp_leaderboard[0]
                    winner['competition_title'] = comp.title
                    winner['competition_id'] = comp.id
                    recent_winners.append(winner)
        
        return render_template('landing.html',
                             branding=branding,
                             competitions=competitions,
                             top_performers=top_performers,
                             recent_winners=recent_winners,
                             current_user=current_user)
    
    # Authenticated users see the dashboard
    branding = BrandingService.get_branding_config()
    current_industry = branding.industry if branding else 'general'
    
    # Fetch content - show all industries for better demo experience
    dataset_service = DatasetService()
    datasets, _ = dataset_service.list_datasets(page=1, per_page=3)  # No industry filter
    
    project_service = ProjectService()
    projects, _ = project_service.list_projects(page=1, per_page=2)  # No industry filter
    
    competition_service = CompetitionService()
    competitions, _ = competition_service.list_competitions(is_active=True, page=1, per_page=5)  # No industry filter, show more
    
    return render_template('index.html', 
                         branding=branding,
                         datasets=datasets,
                         projects=projects,
                         competitions=competitions)


@main_bp.route('/getting-started')
def getting_started():
    """Getting started guide"""
    branding = BrandingService.get_branding_config()
    return render_template('help/getting_started.html', branding=branding)


@main_bp.route('/help')
def help_index():
    """Help index"""
    branding = BrandingService.get_branding_config()
    return render_template('help/index.html', branding=branding)


@main_bp.route('/login')
def login_page():
    """
    Login page - adapts based on authentication mode:
    - Local mode: Shows login/register forms
    - Identity Server mode: Redirects to Identity Server account pages
    """
    current_user = AuthService.get_current_user()
    if current_user:
        return redirect(url_for('main.index'))
    
    auth_mode = AuthService.get_auth_mode()
    branding = BrandingService.get_branding_config()
    
    # If Identity Server mode, redirect to Identity Server account/login page
    if auth_mode == AUTH_MODE_IDENTITY_SERVER:
        identity_server_url = os.getenv(ENV_IDENTITY_SERVER_URL, '').rstrip('/')
        if not identity_server_url:
            # Fallback: Show error message if Identity Server URL not configured
            return render_template('auth/login.html', 
                                 branding=branding,
                                 auth_mode=auth_mode,
                                 error='Identity Server URL not configured')
        
        # Build callback URL for OAuth redirect
        callback_url = url_for('main.oauth_callback', _external=True)
        client_id = os.getenv(ENV_IDENTITY_SERVER_CLIENT_ID, '')
        
        if not client_id:
            # Fallback: Use direct account page if client_id not configured
            params = {'redirect_uri': callback_url}
            login_url = f"{identity_server_url}/Account/Login?{urlencode(params)}"
        else:
            # Use OAuth authorize endpoint (standard OAuth2/OIDC flow)
            login_url = f"{identity_server_url}/connect/authorize"
            params = {
                'client_id': client_id,
                'response_type': 'code',
                'redirect_uri': callback_url,
                'scope': 'openid profile email'
            }
            login_url = f"{login_url}?{urlencode(params)}"
        
        return redirect(login_url)
    
    # Local mode: Show login/register forms
    # Get error from query parameters if present (for OAuth callback errors)
    error = request.args.get('error')
    return render_template('auth/login.html', 
                         branding=branding,
                         auth_mode=auth_mode,
                         error=error)


@main_bp.route('/auth/callback')
def oauth_callback():
    """
    OAuth callback route for Identity Server authentication
    Handles the redirect from Identity Server after user authenticates
    """
    from app.services.identity_server_auth_service import IdentityServerAuthService
    
    auth_mode = AuthService.get_auth_mode()
    if auth_mode != AUTH_MODE_IDENTITY_SERVER:
        return redirect(url_for('main.login_page'))
    
    # Get authorization code from query parameters
    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    if error:
        # OAuth error occurred
        logger.warning(f"OAuth error: {error} - {error_description}")
        return redirect(url_for('main.login_page') + f'?error={error}')
    
    if not code:
        logger.warning("OAuth callback missing authorization code")
        return redirect(url_for('main.login_page') + '?error=missing_code')
    
    try:
        # Exchange authorization code for access token
        identity_server_url = os.getenv(ENV_IDENTITY_SERVER_URL, '').rstrip('/')
        client_id = os.getenv(ENV_IDENTITY_SERVER_CLIENT_ID, '')
        client_secret = os.getenv('IDENTITY_SERVER_CLIENT_SECRET', '')
        callback_url = url_for('main.oauth_callback', _external=True)
        
        if not identity_server_url or not client_id:
            logger.error("Identity Server URL or Client ID not configured")
            return redirect(url_for('main.login_page') + '?error=not_configured')
        
        # Exchange code for token via Identity Server token endpoint
        token_url = f"{identity_server_url}/connect/token"
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': callback_url,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        token_response = requests.post(token_url, data=token_data, timeout=10)
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
            return redirect(url_for('main.login_page') + '?error=token_exchange_failed')
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        if not access_token:
            logger.error("No access token in token response")
            return redirect(url_for('main.login_page') + '?error=no_access_token')
        
        # Use IdentityServerAuthService to validate token and get/create user
        auth_service = IdentityServerAuthService()
        login_result, error_msg = auth_service.login(access_token, client_id)
        
        if not login_result or error_msg:
            logger.error(f"Login failed: {error_msg}")
            return redirect(url_for('main.login_page') + f'?error={error_msg or "login_failed"}')
        
        # login_result contains: access_token (local JWT), oauth_token, user
        jwt_token = login_result.get('access_token')
        oauth_token = login_result.get('oauth_token', access_token)
        
        # Set JWT token as httpOnly cookie and redirect to home
        response = redirect(url_for('main.index'))
        if jwt_token:
            set_access_cookies(response, jwt_token)
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during OAuth callback: {e}", exc_info=True)
        return redirect(url_for('main.login_page') + '?error=network_error')
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        return redirect(url_for('main.login_page') + '?error=callback_error')


@main_bp.route('/auth/success')
def auth_success():
    """
    Success page for OAuth flow (legacy support)
    Now we set cookies directly in oauth_callback, but keep this for backward compatibility
    """
    jwt_token = request.args.get('jwt_token')
    
    if not jwt_token:
        return redirect(url_for('main.login_page') + '?error=missing_tokens')
    
    # Set cookie and redirect to home
    response = redirect(url_for('main.index'))
    set_access_cookies(response, jwt_token)
    return response


@main_bp.route('/logout')
def logout():
    """Logout user (clears JWT token and cookie)"""
    response = redirect(url_for('main.index'))
    unset_jwt_cookies(response)
    return response
