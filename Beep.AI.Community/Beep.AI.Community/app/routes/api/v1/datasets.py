"""
Datasets API endpoints
"""
from flask_restx import Namespace, Resource, fields
from flask import request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.services.dataset_service import DatasetService
from app.models.dataset import Dataset
from pathlib import Path
import json

ns = Namespace('datasets', description='Dataset operations')

dataset_model = ns.model('Dataset', {
    'id': fields.Integer(description='Dataset ID'),
    'title': fields.String(description='Dataset title'),
    'description': fields.String(description='Dataset description'),
    'owner': fields.String(description='Owner username'),
    'file_name': fields.String(description='File name'),
    'file_size': fields.Integer(description='File size in bytes'),
    'file_format': fields.String(description='File format'),
    'category': fields.String(description='Category'),
    'is_public': fields.Boolean(description='Is public'),
    'download_count': fields.Integer(description='Download count'),
    'view_count': fields.Integer(description='View count'),
    'created_at': fields.String(description='Creation date')
})

upload_model = ns.model('UploadDataset', {
    'title': fields.String(required=True, description='Dataset title'),
    'description': fields.String(description='Dataset description'),
    'tags': fields.List(fields.String, description='Tags'),
    'category': fields.String(description='Category'),
    'license': fields.String(description='License'),
    'is_public': fields.Boolean(description='Is public', default=True)
})


@ns.route('')
class DatasetsList(Resource):
    @ns.doc('list_datasets')
    @ns.param('category', 'Filter by category')
    @ns.param('search', 'Search term')
    @ns.param('page', 'Page number', type=int, default=1)
    @ns.param('per_page', 'Items per page', type=int, default=20)
    @ns.marshal_list_with(dataset_model)
    def get(self):
        """List datasets"""
        service = DatasetService()
        
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        category = request.args.get('category')
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        datasets, total = service.list_datasets(
            user_id=user_id,
            category=category,
            search=search,
            is_public=True,
            page=page,
            per_page=per_page
        )
        
        return {
            'datasets': [d.to_dict() for d in datasets],
            'total': total,
            'page': page,
            'per_page': per_page
        }
    
    @ns.expect(upload_model)
    @ns.doc('upload_dataset', security='Bearer Auth')
    @jwt_required()
    def post(self):
        """Upload new dataset"""
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400
        
        file = request.files['file']
        data = request.form
        
        service = DatasetService()
        
        tags = []
        if data.get('tags'):
            try:
                tags = json.loads(data.get('tags'))
            except:
                tags = [t.strip() for t in data.get('tags', '').split(',') if t.strip()]
        
        dataset, error = service.upload_dataset(
            file=file,
            owner_id=user_id,
            title=data.get('title', file.filename),
            description=data.get('description', ''),
            tags=tags,
            category=data.get('category'),
            license=data.get('license', 'MIT'),
            is_public=data.get('is_public', 'true').lower() == 'true'
        )
        
        if error:
            return {'error': error}, 400
        
        return dataset.to_dict(), 201


@ns.route('/<int:dataset_id>')
class DatasetDetail(Resource):
    @ns.doc('get_dataset')
    @ns.marshal_with(dataset_model)
    def get(self, dataset_id):
        """Get dataset details"""
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        service = DatasetService()
        dataset = service.get_dataset(dataset_id, user_id)
        
        if not dataset:
            return {'error': 'Dataset not found'}, 404
        
        return dataset.to_dict()
    
    @ns.doc('delete_dataset', security='Bearer Auth')
    @jwt_required()
    def delete(self, dataset_id):
        """Delete dataset"""
        user_id = get_jwt_identity()
        
        service = DatasetService()
        success, error = service.delete_dataset(dataset_id, user_id)
        
        if error:
            return {'error': error}, 404 if 'not found' in error.lower() else 403
        
        return {'message': 'Dataset deleted successfully'}, 200


@ns.route('/<int:dataset_id>/preview')
class DatasetPreview(Resource):
    @ns.doc('preview_dataset')
    @ns.param('rows', 'Number of rows to preview', type=int, default=20)
    def get(self, dataset_id):
        """Get dataset preview"""
        rows = request.args.get('rows', 20, type=int)
        
        service = DatasetService()
        preview = service.get_dataset_preview(dataset_id, rows)
        
        if 'error' in preview:
            return preview, 404
        
        return preview


@ns.route('/<int:dataset_id>/stats')
class DatasetStats(Resource):
    @ns.doc('get_dataset_stats')
    def get(self, dataset_id):
        """Get dataset statistics"""
        service = DatasetService()
        stats = service.get_dataset_stats(dataset_id)
        
        if 'error' in stats:
            return stats, 404
        
        return stats


@ns.route('/<int:dataset_id>/download')
class DatasetDownload(Resource):
    @ns.doc('download_dataset')
    def get(self, dataset_id):
        """Download dataset"""
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        service = DatasetService()
        file_path, error = service.download_dataset(dataset_id, user_id)
        
        if error:
            return {'error': error}, 404 if 'not found' in error.lower() else 403
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=Path(file_path).name
        )


@ns.route('/<int:dataset_id>/upvote')
class DatasetUpvote(Resource):
    @ns.doc('upvote_dataset', security='Bearer Auth')
    @jwt_required()
    def post(self, dataset_id):
        """Upvote a dataset"""
        user_id = get_jwt_identity()
        
        service = DatasetService()
        success, error = service.upvote_dataset(dataset_id, user_id)
        
        if error:
            return {'error': error}, 404
        
        return {'message': 'Dataset upvoted'}, 200
