"""
Discussions API endpoints
"""
from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.services.discussion_service import DiscussionService
from app.utils.request_validators import (
    validate_json_request,
    sanitize_string_input,
    error_handler
)
import logging

logger = logging.getLogger(__name__)

ns = Namespace('discussions', description='Discussion/Question operations')

# Request/Response models
discussion_model = ns.model('Discussion', {
    'id': fields.Integer(description='Discussion ID'),
    'title': fields.String(description='Discussion title'),
    'content': fields.String(description='Discussion content'),
    'author_id': fields.Integer(description='Author user ID'),
    'author': fields.String(description='Author username'),
    'topic_type': fields.String(description='Topic type'),
    'topic_id': fields.Integer(description='Topic ID'),
    'parent_id': fields.Integer(description='Parent discussion ID'),
    'upvote_count': fields.Integer(description='Upvote count'),
    'reply_count': fields.Integer(description='Reply count'),
    'is_pinned': fields.Boolean(description='Is pinned'),
    'is_solved': fields.Boolean(description='Is solved'),
    'created_at': fields.String(description='Creation date'),
    'updated_at': fields.String(description='Update date')
})

create_discussion_model = ns.model('CreateDiscussion', {
    'title': fields.String(required=True, description='Discussion title'),
    'content': fields.String(required=True, description='Discussion content'),
    'topic_type': fields.String(description='Topic type (competition, dataset, project)'),
    'topic_id': fields.Integer(description='Topic ID')
})

update_discussion_model = ns.model('UpdateDiscussion', {
    'title': fields.String(description='Discussion title'),
    'content': fields.String(description='Discussion content')
})

reply_model = ns.model('Reply', {
    'content': fields.String(required=True, description='Reply content')
})


@ns.route('')
class DiscussionsList(Resource):
    @ns.doc('list_discussions')
    @ns.param('topic_type', 'Filter by topic type')
    @ns.param('topic_id', 'Filter by topic ID', type=int)
    @ns.param('search', 'Search term')
    @ns.param('page', 'Page number', type=int, default=1)
    @ns.param('per_page', 'Items per page', type=int, default=20)
    @ns.marshal_list_with(discussion_model)
    def get(self):
        """List discussions"""
        service = DiscussionService()
        
        topic_type = request.args.get('topic_type')
        topic_id = request.args.get('topic_id', type=int)
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        discussions, total = service.list_discussions(
            topic_type=topic_type,
            topic_id=topic_id,
            page=page,
            per_page=per_page,
            search=search
        )
        
        # Add upvote status for authenticated users
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        result = []
        for discussion in discussions:
            disc_dict = discussion.to_dict()
            if user_id:
                disc_dict['has_upvoted'] = service.has_upvoted(discussion.id, user_id)
            else:
                disc_dict['has_upvoted'] = False
            result.append(disc_dict)
        
        return {
            'discussions': result,
            'total': total,
            'page': page,
            'per_page': per_page
        }
    
    @ns.expect(create_discussion_model)
    @ns.doc('create_discussion', security='Bearer Auth')
    @ns.marshal_with(discussion_model)
    @jwt_required()
    @error_handler
    @validate_json_request(required_fields=['title', 'content'])
    @sanitize_string_input(['title', 'content', 'topic_type'])
    def post(self):
        """Create a new discussion"""
        user_id = get_jwt_identity()
        data = request.get_json()
        service = DiscussionService()
        
        discussion, error = service.create_discussion(
            author_id=user_id,
            title=data['title'],
            content=data['content'],
            topic_type=data.get('topic_type'),
            topic_id=data.get('topic_id')
        )
        
        if error:
            return {'error': error}, 400
        
        return discussion.to_dict(), 201


@ns.route('/<int:discussion_id>')
class DiscussionDetail(Resource):
    @ns.doc('get_discussion')
    @ns.marshal_with(discussion_model)
    def get(self, discussion_id):
        """Get discussion details with replies"""
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        service = DiscussionService()
        discussion = service.get_discussion(discussion_id)
        
        if not discussion:
            return {'error': 'Discussion not found'}, 404
        
        result = discussion.to_dict()
        
        # Add replies
        if discussion.replies:
            result['replies'] = [reply.to_dict() for reply in discussion.replies]
        
        # Add upvote status if authenticated
        if user_id:
            result['has_upvoted'] = service.has_upvoted(discussion_id, user_id)
        
        return result
    
    @ns.expect(update_discussion_model)
    @ns.doc('update_discussion', security='Bearer Auth')
    @ns.marshal_with(discussion_model)
    @jwt_required()
    @error_handler
    @validate_json_request()
    @sanitize_string_input(['title', 'content'])
    def put(self, discussion_id):
        """Update discussion"""
        user_id = get_jwt_identity()
        data = request.get_json()
        service = DiscussionService()
        
        discussion, error = service.update_discussion(
            discussion_id=discussion_id,
            author_id=user_id,
            updates=data
        )
        
        if error:
            return {'error': error}, 404 if 'not found' in error.lower() else 403
        
        return discussion.to_dict()
    
    @ns.doc('delete_discussion', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def delete(self, discussion_id):
        """Delete discussion"""
        user_id = get_jwt_identity()
        service = DiscussionService()
        
        success, error = service.delete_discussion(discussion_id, user_id)
        
        if error:
            return {'error': error}, 404 if 'not found' in error.lower() else 403
        
        return {'message': 'Discussion deleted successfully'}, 200


@ns.route('/<int:discussion_id>/reply')
class DiscussionReply(Resource):
    @ns.expect(reply_model)
    @ns.doc('reply_to_discussion', security='Bearer Auth')
    @jwt_required()
    @error_handler
    @validate_json_request(required_fields=['content'])
    @sanitize_string_input(['content'])
    def post(self, discussion_id):
        """Add reply to discussion"""
        user_id = get_jwt_identity()
        data = request.get_json()
        service = DiscussionService()
        
        reply, error = service.reply_to_discussion(
            discussion_id=discussion_id,
            author_id=user_id,
            content=data['content']
        )
        
        if error:
            return {'error': error}, 400
        
        return reply.to_dict(), 201


@ns.route('/<int:discussion_id>/upvote')
class DiscussionUpvote(Resource):
    @ns.doc('upvote_discussion', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def post(self, discussion_id):
        """Upvote discussion"""
        user_id = get_jwt_identity()
        service = DiscussionService()
        
        success, error = service.upvote_discussion(discussion_id, user_id)
        
        if error:
            return {'error': error}, 400
        
        return {'message': 'Discussion upvoted'}, 200
    
    @ns.doc('remove_upvote', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def delete(self, discussion_id):
        """Remove upvote from discussion"""
        user_id = get_jwt_identity()
        service = DiscussionService()
        
        success, error = service.remove_upvote(discussion_id, user_id)
        
        if error:
            return {'error': error}, 400
        
        return {'message': 'Upvote removed'}, 200


@ns.route('/<int:discussion_id>/solve')
class DiscussionSolve(Resource):
    @ns.doc('mark_as_solved', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def post(self, discussion_id):
        """Mark discussion as solved"""
        user_id = get_jwt_identity()
        service = DiscussionService()
        
        success, error = service.mark_as_solved(discussion_id, user_id)
        
        if error:
            return {'error': error}, 400
        
        return {'message': 'Discussion marked as solved'}, 200


@ns.route('/<int:discussion_id>/pin')
class DiscussionPin(Resource):
    @ns.doc('pin_discussion', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def post(self, discussion_id):
        """Pin discussion (admin only)"""
        user_id = get_jwt_identity()
        service = DiscussionService()
        
        success, error = service.pin_discussion(discussion_id, user_id)
        
        if error:
            return {'error': error}, 403
        
        return {'message': 'Discussion pinned'}, 200
    
    @ns.doc('unpin_discussion', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def delete(self, discussion_id):
        """Unpin discussion (admin only)"""
        user_id = get_jwt_identity()
        service = DiscussionService()
        
        success, error = service.unpin_discussion(discussion_id, user_id)
        
        if error:
            return {'error': error}, 403
        
        return {'message': 'Discussion unpinned'}, 200


@ns.route('/search')
class DiscussionSearch(Resource):
    @ns.doc('search_discussions')
    @ns.param('q', 'Search query', required=True)
    @ns.param('topic_type', 'Filter by topic type')
    @ns.param('page', 'Page number', type=int, default=1)
    @ns.param('per_page', 'Items per page', type=int, default=20)
    @ns.marshal_list_with(discussion_model)
    def get(self):
        """Search discussions"""
        query = request.args.get('q', '')
        if not query:
            return {'error': 'Search query is required'}, 400
        
        service = DiscussionService()
        topic_type = request.args.get('topic_type')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        discussions, total = service.search_discussions(
            query=query,
            topic_type=topic_type,
            page=page,
            per_page=per_page
        )
        
        return {
            'discussions': [d.to_dict() for d in discussions],
            'total': total,
            'page': page,
            'per_page': per_page
        }
