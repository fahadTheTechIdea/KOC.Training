"""
User Participation API endpoints
Provides user participation data for ML Studio integration
"""
from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from app.services.competition_service import CompetitionService
from app.services.auth_service import AuthService
from app.models.user import User
from app.models.activity import Activity
from app.utils.request_validators import error_handler
import logging

logger = logging.getLogger(__name__)

ns = Namespace('user-participation', description='User participation operations')

# Response models
competition_entry_model = ns.model('CompetitionEntry', {
    'id': fields.Integer(description='Competition ID'),
    'title': fields.String(description='Competition title'),
    'description': fields.String(description='Competition description'),
    'is_active': fields.Boolean(description='Is active'),
    'end_date': fields.String(description='End date'),
    'participant_count': fields.Integer(description='Participant count'),
    'submission_count': fields.Integer(description='Submission count')
})

ranking_entry_model = ns.model('RankingEntry', {
    'competition_id': fields.Integer(description='Competition ID'),
    'competition_title': fields.String(description='Competition title'),
    'rank': fields.Integer(description='User rank'),
    'score': fields.Float(description='User score'),
    'total_participants': fields.Integer(description='Total participants'),
    'is_active': fields.Boolean(description='Is active')
})

submission_entry_model = ns.model('SubmissionEntry', {
    'id': fields.Integer(description='Submission ID'),
    'competition_id': fields.Integer(description='Competition ID'),
    'competition_title': fields.String(description='Competition title'),
    'score': fields.Float(description='Score'),
    'status': fields.String(description='Status'),
    'submitted_at': fields.String(description='Submission date')
})

activity_entry_model = ns.model('ActivityEntry', {
    'id': fields.Integer(description='Activity ID'),
    'user_id': fields.Integer(description='User ID'),
    'activity_type': fields.String(description='Activity type'),
    'resource_type': fields.String(description='Resource type'),
    'resource_id': fields.Integer(description='Resource ID'),
    'activity_data': fields.Raw(description='Activity data'),
    'created_at': fields.String(description='Created date')
})

stats_model = ns.model('UserStats', {
    'total_competitions_joined': fields.Integer(description='Total competitions joined'),
    'active_competitions': fields.Integer(description='Active competitions count'),
    'total_submissions': fields.Integer(description='Total submissions'),
    'best_rank': fields.Integer(description='Best ranking achieved'),
    'competitions_with_rankings': fields.Integer(description='Competitions with rankings')
})


@ns.route('/users/<int:user_id>/competitions')
class UserCompetitions(Resource):
    @ns.doc('get_user_competitions', security='Bearer Auth')
    @ns.marshal_list_with(competition_entry_model)
    @error_handler
    def get(self, user_id):
        """Get competitions user has joined (supports JWT and API key auth)"""
        # Get current user (supports JWT, API key, or OAuth)
        current_user = AuthService.get_current_user()
        if not current_user:
            return {'error': 'Authentication required'}, 401
        
        # Verify user can only access their own data (or admin)
        if current_user.id != user_id and not current_user.is_admin:
            return {'error': 'Access denied'}, 403
        
        service = CompetitionService()
        competitions = service.get_user_competitions(user_id)
        
        return {
            'success': True,
            'data': [comp.to_dict() for comp in competitions]
        }


@ns.route('/users/<int:user_id>/submissions')
class UserSubmissions(Resource):
    @ns.doc('get_user_submissions', security='Bearer Auth')
    @ns.param('competition_id', 'Filter by competition ID')
    @ns.marshal_list_with(submission_entry_model)
    @error_handler
    def get(self, user_id):
        """Get all user submissions (supports JWT and API key auth)"""
        current_user = AuthService.get_current_user()
        if not current_user:
            return {'error': 'Authentication required'}, 401
        
        if current_user.id != user_id and not current_user.is_admin:
            return {'error': 'Access denied'}, 403
        
        competition_id = request.args.get('competition_id', type=int)
        service = CompetitionService()
        
        if competition_id:
            submissions = service.get_user_submissions(user_id, competition_id)
        else:
            submissions = service.get_user_submissions(user_id)
        
        # Enrich with competition title
        from app.models.competition import Competition
        result = []
        for sub in submissions:
            sub_dict = sub.to_dict()
            competition = Competition.query.get(sub.competition_id)
            if competition:
                sub_dict['competition_title'] = competition.title
            result.append(sub_dict)
        
        return {
            'success': True,
            'data': result
        }


@ns.route('/users/<int:user_id>/submissions/<int:competition_id>')
class UserCompetitionSubmissions(Resource):
    @ns.doc('get_user_competition_submissions', security='Bearer Auth')
    @ns.marshal_list_with(submission_entry_model)
    @error_handler
    def get(self, user_id, competition_id):
        """Get user submissions for a specific competition (supports JWT and API key auth)"""
        current_user = AuthService.get_current_user()
        if not current_user:
            return {'error': 'Authentication required'}, 401
        
        if current_user.id != user_id and not current_user.is_admin:
            return {'error': 'Access denied'}, 403
        
        service = CompetitionService()
        submissions = service.get_user_submissions(user_id, competition_id)
        
        # Enrich with competition title
        from app.models.competition import Competition
        result = []
        for sub in submissions:
            sub_dict = sub.to_dict()
            competition = Competition.query.get(sub.competition_id)
            if competition:
                sub_dict['competition_title'] = competition.title
            result.append(sub_dict)
        
        return {
            'success': True,
            'data': result
        }


@ns.route('/users/<int:user_id>/rankings')
class UserRankings(Resource):
    @ns.doc('get_user_rankings', security='Bearer Auth')
    @ns.marshal_list_with(ranking_entry_model)
    @error_handler
    def get(self, user_id):
        """Get user rankings across competitions (supports JWT and API key auth)"""
        current_user = AuthService.get_current_user()
        if not current_user:
            return {'error': 'Authentication required'}, 401
        
        if current_user.id != user_id and not current_user.is_admin:
            return {'error': 'Access denied'}, 403
        
        service = CompetitionService()
        rankings = service.get_user_rankings(user_id)
        
        return {
            'success': True,
            'data': rankings
        }


@ns.route('/users/<int:user_id>/activity')
class UserActivity(Resource):
    @ns.doc('get_user_activity', security='Bearer Auth')
    @ns.param('limit', 'Maximum number of activities', type=int, default=10)
    @ns.marshal_list_with(activity_entry_model)
    @error_handler
    def get(self, user_id):
        """Get recent user activity (supports JWT and API key auth)"""
        current_user = AuthService.get_current_user()
        if not current_user:
            return {'error': 'Authentication required'}, 401
        
        if current_user.id != user_id and not current_user.is_admin:
            return {'error': 'Access denied'}, 403
        
        limit = request.args.get('limit', 10, type=int)
        if limit > 50:
            limit = 50  # Cap at 50
        
        activities = Activity.query.filter_by(user_id=user_id)\
            .order_by(Activity.created_at.desc())\
            .limit(limit).all()
        
        # Format activities for display
        result = []
        for activity in activities:
            activity_dict = activity.to_dict()
            # Generate description if not present
            if not activity_dict.get('description'):
                activity_type = activity.activity_type.replace('_', ' ').title()
                resource_type = activity.resource_type.replace('_', ' ').title() if activity.resource_type else ''
                activity_dict['description'] = f"{activity_type} - {resource_type}"
            result.append(activity_dict)
        
        return {
            'success': True,
            'data': result
        }


@ns.route('/users/<int:user_id>/competitions/stats')
class UserStats(Resource):
    @ns.doc('get_user_stats', security='Bearer Auth')
    @ns.marshal_with(stats_model)
    @error_handler
    def get(self, user_id):
        """Get user participation statistics (supports JWT and API key auth)"""
        current_user = AuthService.get_current_user()
        if not current_user:
            return {'error': 'Authentication required'}, 401
        
        if current_user.id != user_id and not current_user.is_admin:
            return {'error': 'Access denied'}, 403
        
        service = CompetitionService()
        stats = service.get_user_statistics(user_id)
        
        return {
            'success': True,
            'data': stats
        }
