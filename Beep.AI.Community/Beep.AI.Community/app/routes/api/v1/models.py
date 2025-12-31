"""
Models API endpoints - Model Registry operations
"""
from flask_restx import Namespace, Resource, fields
from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.services.model_registry_service import ModelRegistryService
from app.services.auth_service import AuthService
from app.utils.request_validators import (
    validate_json_request,
    sanitize_string_input,
    error_handler
)
import logging

logger = logging.getLogger(__name__)

ns = Namespace('models', description='Model registry operations')

# Request/Response models
model_registry_model = ns.model('ModelRegistry', {
    'id': fields.Integer(description='Model ID'),
    'name': fields.String(description='Model name'),
    'description': fields.String(description='Model description'),
    'owner_id': fields.Integer(description='Owner user ID'),
    'owner': fields.String(description='Owner username'),
    'model_type': fields.String(description='Model type'),
    'framework': fields.String(description='Framework'),
    'metrics': fields.Raw(description='Model metrics'),
    'input_schema': fields.Raw(description='Input schema'),
    'output_schema': fields.Raw(description='Output schema'),
    'is_public': fields.Boolean(description='Is public'),
    'download_count': fields.Integer(description='Download count'),
    'view_count': fields.Integer(description='View count'),
    'created_at': fields.String(description='Creation date')
})

register_model_model = ns.model('RegisterModel', {
    'model_name': fields.String(required=True, description='Model name'),
    'model_file_data': fields.String(description='Base64 encoded model file'),
    'model_file_path': fields.String(description='Path to model file (if already exists)'),
    'model_type': fields.String(description='Model type'),
    'framework': fields.String(description='Framework'),
    'metrics': fields.Raw(description='Model metrics dictionary'),
    'description': fields.String(description='Model description'),
    'input_schema': fields.Raw(description='Input schema dictionary'),
    'output_schema': fields.Raw(description='Output schema dictionary'),
    'mlstudio_source_id': fields.String(description='Original MLStudio model ID'),
    'is_public': fields.Boolean(description='Is public', default=True),
    'user_id': fields.Integer(description='User ID (required for API key auth)')
})


def get_authenticated_user_id():
    """
    Get authenticated user ID from JWT or API key
    
    For API key auth, user_id should be in request body
    """
    # Try JWT first
    try:
        verify_jwt_in_request(optional=True)
        user_id_str = get_jwt_identity()
        if user_id_str:
            try:
                return int(user_id_str)
            except (ValueError, TypeError):
                pass
    except RuntimeError:
        pass
    except Exception:
        pass
    
    # Try API key authentication
    api_key = request.headers.get('X-API-Key')
    if not api_key and request.headers.get('Authorization', '').startswith('Bearer '):
        api_key = request.headers.get('Authorization', '').split('Bearer ')[1]
    
    if api_key:
        if AuthService.validate_api_key_for_service(api_key):
            # Valid API key - get user_id from request body
            data = request.get_json() or {}
            user_id = data.get('user_id')
            if user_id:
                try:
                    return int(user_id)
                except (ValueError, TypeError):
                    pass
    
    return None


@ns.route('/register')
class RegisterModel(Resource):
    @ns.expect(register_model_model)
    @ns.doc('register_model', security='Bearer Auth')
    @ns.marshal_with(model_registry_model)
    @error_handler
    @validate_json_request(required_fields=['model_name'])
    @sanitize_string_input(['model_name', 'description', 'model_type', 'framework'])
    def post(self):
        """Register a model from MLStudio to Model Registry"""
        # Get authenticated user
        user_id = get_authenticated_user_id()
        if not user_id:
            # Try API key auth
            api_key = request.headers.get('X-API-Key')
            if not api_key and request.headers.get('Authorization', '').startswith('Bearer '):
                api_key = request.headers.get('Authorization', '').split('Bearer ')[1]
            
            if api_key and AuthService.validate_api_key_for_service(api_key):
                # Service API key - user_id must be in request
                data = request.get_json()
                user_id = data.get('user_id')
                if not user_id:
                    return {'error': 'user_id is required when using API key authentication'}, 400
            else:
                return {'error': 'Authentication required'}, 401
        
        data = request.get_json()
        service = ModelRegistryService()
        
        model, error = service.register_model_from_mlstudio(
            owner_id=user_id,
            model_name=data['model_name'],
            model_file_data=data.get('model_file_data'),
            model_file_path=data.get('model_file_path'),
            model_type=data.get('model_type'),
            framework=data.get('framework'),
            metrics=data.get('metrics'),
            description=data.get('description'),
            input_schema=data.get('input_schema'),
            output_schema=data.get('output_schema'),
            mlstudio_source_id=data.get('mlstudio_source_id'),
            is_public=data.get('is_public', True)
        )
        
        if error:
            return {'error': error}, 400
        
        return model.to_dict(), 201


@ns.route('/user/<int:user_id>')
class UserModels(Resource):
    @ns.doc('get_user_models')
    @ns.param('limit', 'Maximum number of models to return', type=int, default=100)
    @ns.param('is_public', 'Filter by public status', type=bool)
    @ns.marshal_list_with(model_registry_model)
    def get(self, user_id):
        """Get user's registered models"""
        # Allow public access or require authentication
        limit = request.args.get('limit', 100, type=int)
        is_public = request.args.get('is_public')
        if is_public is not None:
            is_public = is_public.lower() in ('true', '1', 'yes')
        
        service = ModelRegistryService()
        models = service.get_user_models(user_id, limit=limit, is_public=is_public)
        
        return [model.to_dict() for model in models]


@ns.route('/<int:model_id>')
class ModelDetail(Resource):
    @ns.doc('get_model')
    @ns.marshal_with(model_registry_model)
    def get(self, model_id):
        """Get model details"""
        service = ModelRegistryService()
        model = service.get_model_by_id(model_id)
        
        if not model:
            return {'error': 'Model not found'}, 404
        
        return model.to_dict()
