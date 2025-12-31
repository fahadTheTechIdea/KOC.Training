"""
Notebooks/Projects API endpoints
"""
from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.services.project_service import ProjectService
from app.models.notebook import Notebook
import json

ns = Namespace('notebooks', description='Notebook/Project operations')

# Request/Response models
project_model = ns.model('Project', {
    'id': fields.Integer(description='Project ID'),
    'title': fields.String(description='Project title'),
    'description': fields.String(description='Project description'),
    'owner': fields.String(description='Owner username'),
    'language': fields.String(description='Programming language'),
    'kernel_type': fields.String(description='Kernel type'),
    'category': fields.String(description='Category'),
    'is_public': fields.Boolean(description='Is public'),
    'fork_count': fields.Integer(description='Fork count'),
    'upvote_count': fields.Integer(description='Upvote count'),
    'view_count': fields.Integer(description='View count'),
    'created_at': fields.String(description='Creation date')
})

publish_model = ns.model('PublishProject', {
    'title': fields.String(required=True, description='Project title'),
    'description': fields.String(description='Project description'),
    'project_id': fields.Integer(description='MLStudio project ID'),
    'code_content': fields.String(description='Code content'),
    'output_content': fields.String(description='Output/results'),
    'language': fields.String(description='Programming language', default='python'),
    'kernel_type': fields.String(description='Kernel type', default='notebook'),
    'tags': fields.List(fields.String, description='Tags'),
    'category': fields.String(description='Category'),
    'is_public': fields.Boolean(description='Is public', default=True)
})


@ns.route('')
class NotebooksList(Resource):
    @ns.doc('list_projects')
    @ns.param('category', 'Filter by category')
    @ns.param('language', 'Filter by language')
    @ns.param('search', 'Search term')
    @ns.param('page', 'Page number', type=int, default=1)
    @ns.param('per_page', 'Items per page', type=int, default=20)
    @ns.marshal_list_with(project_model)
    def get(self):
        """List public projects"""
        service = ProjectService()
        
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        category = request.args.get('category')
        language = request.args.get('language')
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        projects, total = service.list_projects(
            user_id=user_id,
            category=category,
            language=language,
            search=search,
            is_public=True,
            page=page,
            per_page=per_page
        )
        
        return {
            'projects': [p.to_dict() for p in projects],
            'total': total,
            'page': page,
            'per_page': per_page
        }
    
    @ns.expect(publish_model)
    @ns.doc('publish_project', security='Bearer Auth')
    @jwt_required()
    def post(self):
        """Publish project from MLStudio"""
        user_id = get_jwt_identity()
        data = request.get_json()
        
        service = ProjectService()
        
        tags = data.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        
        project, error = service.publish_project(
            owner_id=user_id,
            title=data.get('title'),
            description=data.get('description', ''),
            project_id=data.get('project_id'),
            code_content=data.get('code_content', ''),
            output_content=data.get('output_content', ''),
            language=data.get('language', 'python'),
            kernel_type=data.get('kernel_type', 'notebook'),
            tags=tags,
            category=data.get('category'),
            is_public=data.get('is_public', True)
        )
        
        if error:
            return {'error': error}, 400
        
        return project.to_dict(), 201


@ns.route('/<int:notebook_id>')
class NotebookDetail(Resource):
    @ns.doc('get_project')
    @ns.marshal_with(project_model)
    def get(self, notebook_id):
        """Get project details"""
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        service = ProjectService()
        project = service.get_project(notebook_id, user_id)
        
        if not project:
            return {'error': 'Project not found'}, 404
        
        return project.to_dict()
    
    @ns.doc('delete_project', security='Bearer Auth')
    @jwt_required()
    def delete(self, notebook_id):
        """Delete project"""
        user_id = get_jwt_identity()
        
        service = ProjectService()
        success, error = service.delete_project(notebook_id, user_id)
        
        if error:
            return {'error': error}, 404 if 'not found' in error.lower() else 403
        
        return {'message': 'Project deleted successfully'}, 200


@ns.route('/<int:notebook_id>/fork')
class NotebookFork(Resource):
    @ns.doc('fork_project', security='Bearer Auth')
    @jwt_required()
    def post(self, notebook_id):
        """Fork a project"""
        user_id = get_jwt_identity()
        
        service = ProjectService()
        fork, error = service.fork_project(notebook_id, user_id)
        
        if error:
            return {'error': error}, 404 if 'not found' in error.lower() else 400
        
        return fork.to_dict(), 201


@ns.route('/<int:notebook_id>/upvote')
class NotebookUpvote(Resource):
    @ns.doc('upvote_project', security='Bearer Auth')
    @jwt_required()
    def post(self, notebook_id):
        """Upvote a project"""
        user_id = get_jwt_identity()
        
        service = ProjectService()
        success, error = service.upvote_project(notebook_id, user_id)
        
        if error:
            return {'error': error}, 404 if 'not found' in error.lower() else 400
        
        return {'message': 'Project upvoted'}, 200


@ns.route('/<int:notebook_id>/code')
class NotebookCode(Resource):
    @ns.doc('get_project_code')
    def get(self, notebook_id):
        """Get project code content"""
        service = ProjectService()
        project = service.get_project(notebook_id)
        
        if not project:
            return {'error': 'Project not found'}, 404
        
        return {
            'code': project.code_content,
            'output': project.output_content,
            'language': project.language
        }


@ns.route('/<int:notebook_id>/export')
class NotebookExport(Resource):
    @ns.doc('export_project')
    def get(self, notebook_id):
        """Export project to Jupyter notebook format"""
        service = ProjectService()
        notebook_json = service.export_to_notebook_format(notebook_id)
        
        if 'error' in notebook_json:
            return notebook_json, 404
        
        return jsonify(notebook_json)
