"""
Competitions API endpoints
"""
from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from app.services.competition_service import CompetitionService
from app.services.auth_service import AuthService
from app.models.competition import Competition
from app.utils.request_validators import (
    validate_json_request,
    sanitize_string_input,
    error_handler
)
import logging

logger = logging.getLogger(__name__)

ns = Namespace('competitions', description='Competition/Challenge operations')

# Request/Response models
competition_model = ns.model('Competition', {
    'id': fields.Integer(description='Competition ID'),
    'title': fields.String(description='Competition title'),
    'description': fields.String(description='Competition description'),
    'organizer_id': fields.Integer(description='Organizer user ID'),
    'organizer': fields.String(description='Organizer username'),
    'dataset_id': fields.Integer(description='Dataset ID'),
    'evaluation_metric': fields.String(description='Evaluation metric'),
    'start_date': fields.String(description='Start date'),
    'end_date': fields.String(description='End date'),
    'max_submissions_per_day': fields.Integer(description='Max submissions per day'),
    'max_total_submissions': fields.Integer(description='Max total submissions'),
    'prize_description': fields.String(description='Prize description'),
    'is_active': fields.Boolean(description='Is active'),
    'leaderboard_type': fields.String(description='Leaderboard type'),
    'participant_count': fields.Integer(description='Participant count'),
    'submission_count': fields.Integer(description='Submission count'),
    'created_at': fields.String(description='Creation date')
})

create_competition_model = ns.model('CreateCompetition', {
    'title': fields.String(required=True, description='Competition title'),
    'description': fields.String(required=True, description='Competition description'),
    'dataset_id': fields.Integer(description='Dataset ID'),
    'start_date': fields.String(description='Start date (ISO format)'),
    'end_date': fields.String(required=True, description='End date (ISO format)'),
    'evaluation_metric': fields.String(description='Evaluation metric'),
    'max_submissions_per_day': fields.Integer(description='Max submissions per day', default=5),
    'max_total_submissions': fields.Integer(description='Max total submissions', default=100),
    'prize_description': fields.String(description='Prize description'),
    'leaderboard_type': fields.String(description='Leaderboard type', default='public')
})

update_competition_model = ns.model('UpdateCompetition', {
    'title': fields.String(description='Competition title'),
    'description': fields.String(description='Competition description'),
    'dataset_id': fields.Integer(description='Dataset ID'),
    'start_date': fields.String(description='Start date (ISO format)'),
    'end_date': fields.String(description='End date (ISO format)'),
    'evaluation_metric': fields.String(description='Evaluation metric'),
    'max_submissions_per_day': fields.Integer(description='Max submissions per day'),
    'max_total_submissions': fields.Integer(description='Max total submissions'),
    'prize_description': fields.String(description='Prize description'),
    'leaderboard_type': fields.String(description='Leaderboard type'),
    'is_active': fields.Boolean(description='Is active')
})

leaderboard_entry_model = ns.model('LeaderboardEntry', {
    'rank': fields.Integer(description='Rank'),
    'submission_id': fields.Integer(description='Submission ID'),
    'user_id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
    'score': fields.Float(description='Score'),
    'submitted_at': fields.String(description='Submission date')
})


@ns.route('')
class CompetitionsList(Resource):
    @ns.doc('list_competitions')
    @ns.param('is_active', 'Filter by active status')
    @ns.param('search', 'Search term')
    @ns.param('page', 'Page number', type=int, default=1)
    @ns.param('per_page', 'Items per page', type=int, default=20)
    @ns.marshal_list_with(competition_model)
    def get(self):
        """List competitions"""
        service = CompetitionService()
        
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        is_active = request.args.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() in ('true', '1', 'yes')
        
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        competitions, total = service.list_competitions(
            user_id=user_id,
            is_active=is_active,
            page=page,
            per_page=per_page,
            search=search
        )
        
        # Add participation status to response
        result_list = []
        for competition in competitions:
            comp_dict = competition.to_dict()
            if user_id:
                comp_dict['is_participant'] = service.is_participant(competition.id, user_id)
            result_list.append(comp_dict)
        
        return {
            'competitions': result_list,
            'total': total,
            'page': page,
            'per_page': per_page
        }
    
    @ns.expect(create_competition_model)
    @ns.doc('create_competition', security='Bearer Auth')
    @ns.marshal_with(competition_model)
    @jwt_required()
    @error_handler
    @validate_json_request(required_fields=['title', 'description', 'end_date'])
    @sanitize_string_input(['title', 'description', 'evaluation_metric', 'prize_description', 'leaderboard_type'])
    def post(self):
        """Create a new competition (admin/organizer only)"""
        user_id = get_jwt_identity()
        
        # Check if user is admin (basic check - can be enhanced)
        from app.models.user import User
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return {'error': 'Only administrators can create competitions'}, 403
        
        data = request.get_json()
        service = CompetitionService()
        
        # Parse dates
        start_date = None
        end_date = None
        
        if data.get('start_date'):
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        if data.get('end_date'):
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        
        competition, error = service.create_competition(
            organizer_id=user_id,
            title=data['title'],
            description=data['description'],
            dataset_id=data.get('dataset_id'),
            start_date=start_date,
            end_date=end_date,
            evaluation_metric=data.get('evaluation_metric'),
            max_submissions_per_day=data.get('max_submissions_per_day', 5),
            max_total_submissions=data.get('max_total_submissions', 100),
            prize_description=data.get('prize_description'),
            leaderboard_type=data.get('leaderboard_type', 'public')
        )
        
        if error:
            return {'error': error}, 400
        
        return competition.to_dict(), 201


@ns.route('/<int:competition_id>')
class CompetitionDetail(Resource):
    @ns.doc('get_competition')
    @ns.marshal_with(competition_model)
    def get(self, competition_id):
        """Get competition details"""
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        service = CompetitionService()
        competition = service.get_competition(competition_id, user_id)
        
        if not competition:
            return {'error': 'Competition not found'}, 404
        
        result = competition.to_dict()
        if user_id:
            result['is_participant'] = service.is_participant(competition_id, user_id)
        
        return result
    
    @ns.expect(update_competition_model)
    @ns.doc('update_competition', security='Bearer Auth')
    @ns.marshal_with(competition_model)
    @jwt_required()
    @error_handler
    @validate_json_request()
    @sanitize_string_input(['title', 'description', 'evaluation_metric', 'prize_description', 'leaderboard_type'])
    def put(self, competition_id):
        """Update competition (organizer only)"""
        user_id = get_jwt_identity()
        data = request.get_json()
        service = CompetitionService()
        
        # Parse dates if provided
        updates = {}
        for key, value in data.items():
            if key in ['start_date', 'end_date'] and value:
                updates[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                updates[key] = value
        
        competition, error = service.update_competition(
            competition_id=competition_id,
            organizer_id=user_id,
            updates=updates
        )
        
        if error:
            return {'error': error}, 404 if 'not found' in error.lower() else 403
        
        return competition.to_dict()
    
    @ns.doc('delete_competition', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def delete(self, competition_id):
        """Delete competition (organizer only)"""
        user_id = get_jwt_identity()
        service = CompetitionService()
        
        success, error = service.delete_competition(competition_id, user_id)
        
        if error:
            return {'error': error}, 404 if 'not found' in error.lower() else 403
        
        return {'message': 'Competition deleted successfully'}, 200


@ns.route('/<int:competition_id>/join')
class CompetitionJoin(Resource):
    @ns.doc('join_competition', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def post(self, competition_id):
        """Join a competition"""
        user_id = get_jwt_identity()
        service = CompetitionService()
        
        participant, error = service.join_competition(competition_id, user_id)
        
        if error:
            return {'error': error}, 400
        
        return {'message': 'Successfully joined competition', 'participant': participant.to_dict()}, 200


@ns.route('/<int:competition_id>/leave')
class CompetitionLeave(Resource):
    @ns.doc('leave_competition', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def post(self, competition_id):
        """Leave a competition"""
        user_id = get_jwt_identity()
        service = CompetitionService()
        
        success, error = service.leave_competition(competition_id, user_id)
        
        if error:
            return {'error': error}, 400
        
        return {'message': 'Successfully left competition'}, 200


@ns.route('/<int:competition_id>/leaderboard')
class CompetitionLeaderboard(Resource):
    @ns.doc('get_leaderboard')
    @ns.param('limit', 'Maximum entries to return', type=int, default=100)
    @ns.marshal_list_with(leaderboard_entry_model)
    def get(self, competition_id):
        """Get competition leaderboard"""
        limit = request.args.get('limit', 100, type=int)
        service = CompetitionService()
        
        leaderboard = service.get_leaderboard(competition_id, limit)
        
        return leaderboard


@ns.route('/<int:competition_id>/submit')
class CompetitionSubmit(Resource):
    @ns.doc('submit_to_competition', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def post(self, competition_id):
        """Submit entry to competition"""
        user_id = get_jwt_identity()
        
        if 'submission_file' not in request.files:
            return {'error': 'No file provided'}, 400
        
        submission_file = request.files['submission_file']
        model_id = request.form.get('model_id', type=int)
        
        service = CompetitionService()
        submission, error = service.submit_to_competition(
            competition_id=competition_id,
            user_id=user_id,
            submission_file=submission_file,
            model_id=model_id
        )
        
        if error:
            return {'error': error}, 400
        
        return submission.to_dict(), 201


@ns.route('/<int:competition_id>/submissions')
class CompetitionSubmissions(Resource):
    @ns.doc('get_user_submissions', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def get(self, competition_id):
        """Get user's submissions for a competition"""
        user_id = get_jwt_identity()
        service = CompetitionService()
        
        submissions = service.get_user_submissions(competition_id, user_id)
        
        return {
            'submissions': [s.to_dict() for s in submissions]
        }


@ns.route('/<int:competition_id>/stats')
class CompetitionStats(Resource):
    @ns.doc('get_competition_stats')
    def get(self, competition_id):
        """Get competition statistics"""
        service = CompetitionService()
        stats = service.get_competition_stats(competition_id)
        
        if not stats:
            return {'error': 'Competition not found'}, 404
        
        return stats


submit_model_request_model = ns.model('SubmitModelRequest', {
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
    'user_id': fields.Integer(description='User ID (required for API key auth)')
})


def get_authenticated_user_id_for_submission():
    """
    Get authenticated user ID from JWT or API key for model submission
    
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


@ns.route('/<int:competition_id>/training-data')
class CompetitionTrainingData(Resource):
    @ns.doc('download_training_data', security='Bearer Auth')
    @error_handler
    def get(self, competition_id):
        """Download training dataset for a competition (participants only)"""
        from flask import send_file, abort
        from pathlib import Path
        import os
        
        # Get authenticated user
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        # For API key auth, check if provided
        if not user_id:
            api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
            if api_key:
                from app.services.auth_service import AuthService
                if AuthService.validate_api_key_for_service(api_key):
                    # Service API key - allow access
                    user_id = request.args.get('user_id', type=int)
        
        service = CompetitionService()
        competition = service.get_competition(competition_id, user_id)
        
        if not competition:
            return {'error': 'Competition not found'}, 404
        
        # Check if user is participant (required for download)
        if user_id and not service.is_participant(competition_id, user_id):
            return {'error': 'You must join the competition to download training data'}, 403
        
        # Get training data path
        training_data_path = competition.training_data_path
        if not training_data_path:
            return {'error': 'Training data not available for this competition'}, 404
        
        # Resolve file path
        file_path = Path(training_data_path)
        if not file_path.is_absolute():
            # Relative path - assume it's in uploads/competitions/
            file_path = Path('uploads/competitions') / training_data_path
        
        if not file_path.exists():
            return {'error': 'Training data file not found'}, 404
        
        # Send file
        try:
            return send_file(
                str(file_path),
                as_attachment=True,
                download_name=file_path.name,
                mimetype='application/octet-stream'
            )
        except Exception as e:
            logger.error(f"Error sending training data file: {e}")
            return {'error': 'Failed to download training data'}, 500


@ns.route('/<int:competition_id>/submit-model')
class CompetitionSubmitModel(Resource):
    @ns.expect(submit_model_request_model)
    @ns.doc('submit_model_to_competition', security='Bearer Auth')
    @error_handler
    @validate_json_request(required_fields=['model_name'])
    @sanitize_string_input(['model_name', 'description', 'model_type', 'framework'])
    def post(self, competition_id):
        """Submit a model from MLStudio to competition"""
        # Get authenticated user
        user_id = get_authenticated_user_id_for_submission()
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
        service = CompetitionService()
        
        # Submit model to competition (this will register model and create submission)
        # Validation happens inside submit_model_to_competition
        submission, error = service.submit_model_to_competition(
            competition_id=competition_id,
            user_id=user_id,
            model_name=data['model_name'],
            model_file_data=data.get('model_file_data'),
            model_file_path=data.get('model_file_path'),
            model_type=data.get('model_type'),
            framework=data.get('framework'),
            metrics=data.get('metrics'),
            description=data.get('description'),
            input_schema=data.get('input_schema'),
            output_schema=data.get('output_schema'),
            mlstudio_source_id=data.get('mlstudio_source_id')
        )
        
        if error:
            # Return detailed error response for validation failures
            response = {
                'success': False,
                'error': error
            }
            
            # If it's a validation error, include additional details
            if 'validation failed' in error.lower():
                response['validation_failed'] = True
                response['message'] = error
            
            return response, 400
        
        # Success response
        return {
            'success': True,
            'submission': submission.to_dict(),
            'message': 'Model submitted successfully'
        }, 201
