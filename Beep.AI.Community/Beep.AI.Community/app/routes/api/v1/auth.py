"""
Authentication API endpoints
"""
from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from flask_jwt_extended import set_access_cookies
from app.services.auth_service import AuthService
from app.utils.validators import validate_email, validate_username, validate_password
from app import db

ns = Namespace('auth', description='Authentication operations')

register_model = ns.model('Register', {
    'username': fields.String(required=True, description='Username (3-20 chars, alphanumeric and _)'),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password (min 8 chars)')
})

login_model = ns.model('Login', {
    'username_or_email': fields.String(required=True, description='Username or email'),
    'password': fields.String(required=True, description='Password')
})

api_key_model = ns.model('CreateAPIKey', {
    'key_name': fields.String(required=True, description='Name for the API key')
})


@ns.route('/register')
class Register(Resource):
    @ns.expect(register_model)
    @ns.doc('register_user')
    def post(self):
        """Register a new user"""
        data = request.get_json()
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not username:
            return {'error': 'Username is required'}, 400
        
        if not validate_username(username):
            return {'error': 'Invalid username format. Use 3-20 characters, alphanumeric and underscores only'}, 400
        
        if not email:
            return {'error': 'Email is required'}, 400
        
        if not validate_email(email):
            return {'error': 'Invalid email format'}, 400
        
        if not password:
            return {'error': 'Password is required'}, 400
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return {'error': error_msg}, 400
        
        user, error = AuthService.register_user(username, email, password)
        if error:
            return {'error': error}, 400
        
        return {
            'message': 'User registered successfully',
            'user': user.to_dict()
        }, 201


@ns.route('/login')
class Login(Resource):
    @ns.expect(login_model)
    @ns.doc('login_user')
    def post(self):
        """Login user and get JWT token"""
        data = request.get_json()
        
        username_or_email = data.get('username_or_email', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return {'error': 'Username/email and password are required'}, 400
        
        result, error = AuthService.login_user(username_or_email, password)
        if error:
            return {'error': error}, 401
        
        # Set JWT token as httpOnly cookie
        # Flask-RESTX expects tuple (data, status), but we need to set cookies
        # So we create response and return it directly
        response = jsonify(result)
        if 'access_token' in result:
            set_access_cookies(response, result['access_token'])
        
        return response


@ns.route('/me')
class CurrentUser(Resource):
    @ns.doc('get_current_user', security='Bearer Auth')
    def get(self):
        """Get current authenticated user"""
        from flask_jwt_extended import jwt_required, get_jwt_identity
        from app.models.user import User
        
        @jwt_required()
        def _get_user():
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404
            return user.to_dict(), 200
        
        return _get_user()


@ns.route('/api-keys')
class APIKeys(Resource):
    @ns.doc('list_api_keys', security='Bearer Auth')
    def get(self):
        """List user's API keys"""
        from flask_jwt_extended import jwt_required, get_jwt_identity
        
        @jwt_required()
        def _list_keys():
            user_id = get_jwt_identity()
            keys = AuthService.get_user_api_keys(user_id)
            return {'api_keys': keys}, 200
        
        return _list_keys()
    
    @ns.expect(api_key_model)
    @ns.doc('create_api_key', security='Bearer Auth')
    def post(self):
        """Create new API key for MLStudio"""
        from flask_jwt_extended import jwt_required, get_jwt_identity
        
        @jwt_required()
        def _create_key():
            user_id = get_jwt_identity()
            data = request.get_json()
            key_name = data.get('key_name', 'MLStudio Key').strip()
            
            if not key_name:
                return {'error': 'Key name is required'}, 400
            
            key_obj, error = AuthService.create_api_key(user_id, key_name)
            if error:
                return {'error': error}, 400
            
            return {
                'message': 'API key created successfully',
                'api_key': key_obj.api_key,
                'key_info': key_obj.to_dict()
            }, 201
        
        return _create_key()


@ns.route('/api-keys/<int:key_id>')
class APIKeyDetail(Resource):
    @ns.doc('revoke_api_key', security='Bearer Auth')
    def delete(self, key_id):
        """Revoke an API key"""
        from flask_jwt_extended import jwt_required, get_jwt_identity
        
        @jwt_required()
        def _revoke_key():
            user_id = get_jwt_identity()
            success, error = AuthService.revoke_api_key(user_id, key_id)
            if error:
                return {'error': error}, 404
            
            return {'message': 'API key revoked successfully'}, 200
        
        return _revoke_key()
