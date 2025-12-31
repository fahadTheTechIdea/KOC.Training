"""
Industry Scenarios API endpoints
"""
from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.services.industry_scenarios_service import IndustryScenariosService
from app.models.user import User
from app.utils.request_validators import (
    validate_json_request,
    sanitize_string_input,
    error_handler
)
import logging

logger = logging.getLogger(__name__)

ns = Namespace('industry-scenarios', description='Industry scenarios operations')

# Request/Response models
scenario_model = ns.model('IndustryScenario', {
    'id': fields.Integer(description='Scenario ID'),
    'industry': fields.String(description='Industry name'),
    'scenario_type': fields.String(description='Scenario type (use_case, dataset_idea, competition_idea)'),
    'title': fields.String(description='Scenario title'),
    'description': fields.String(description='Scenario description'),
    'details': fields.Raw(description='Additional details (JSON)'),
    'icon_name': fields.String(description='Icon filename'),
    'priority': fields.Integer(description='Priority (higher = more important)'),
    'is_active': fields.Boolean(description='Is active'),
    'created_at': fields.String(description='Creation date'),
    'updated_at': fields.String(description='Update date')
})

create_scenario_model = ns.model('CreateScenario', {
    'industry': fields.String(required=True, description='Industry name'),
    'scenario_type': fields.String(required=True, description='Scenario type'),
    'title': fields.String(required=True, description='Scenario title'),
    'description': fields.String(required=True, description='Scenario description'),
    'icon_name': fields.String(description='Icon filename'),
    'priority': fields.Integer(description='Priority', default=0),
    'details': fields.Raw(description='Additional details (JSON)')
})

update_scenario_model = ns.model('UpdateScenario', {
    'title': fields.String(description='Scenario title'),
    'description': fields.String(description='Scenario description'),
    'icon_name': fields.String(description='Icon filename'),
    'priority': fields.Integer(description='Priority'),
    'details': fields.Raw(description='Additional details (JSON)'),
    'is_active': fields.Boolean(description='Is active')
})


@ns.route('/industries/<industry>/scenarios')
class IndustryScenariosList(Resource):
    @ns.doc('get_industry_scenarios')
    @ns.param('scenario_type', 'Filter by scenario type (use_case, dataset_idea, competition_idea)')
    @ns.marshal_list_with(scenario_model)
    def get(self, industry):
        """Get all scenarios for an industry"""
        service = IndustryScenariosService()
        scenario_type = request.args.get('scenario_type')
        
        scenarios = service.get_scenarios_for_industry(industry, scenario_type=scenario_type)
        return scenarios


@ns.route('/industries/<industry>/use-cases')
class IndustryUseCases(Resource):
    @ns.doc('get_industry_use_cases')
    @ns.marshal_list_with(scenario_model)
    def get(self, industry):
        """Get use cases for an industry"""
        service = IndustryScenariosService()
        use_cases = service.get_use_cases(industry)
        return use_cases


@ns.route('/industries/<industry>/dataset-ideas')
class IndustryDatasetIdeas(Resource):
    @ns.doc('get_industry_dataset_ideas')
    @ns.marshal_list_with(scenario_model)
    def get(self, industry):
        """Get dataset ideas for an industry"""
        service = IndustryScenariosService()
        dataset_ideas = service.get_dataset_ideas(industry)
        return dataset_ideas


@ns.route('/industries/<industry>/competition-ideas')
class IndustryCompetitionIdeas(Resource):
    @ns.doc('get_industry_competition_ideas')
    @ns.marshal_list_with(scenario_model)
    def get(self, industry):
        """Get competition ideas for an industry"""
        service = IndustryScenariosService()
        competition_ideas = service.get_competition_ideas(industry)
        return competition_ideas


@ns.route('/scenarios')
class ScenariosList(Resource):
    @ns.expect(create_scenario_model)
    @ns.doc('create_scenario', security='Bearer Auth')
    @ns.marshal_with(scenario_model)
    @jwt_required()
    @error_handler
    @validate_json_request(required_fields=['industry', 'scenario_type', 'title', 'description'])
    @sanitize_string_input(['industry', 'scenario_type', 'title', 'description', 'icon_name'])
    def post(self):
        """Create a new scenario (admin only)"""
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return {'error': 'Admin access required'}, 403
        
        data = request.get_json()
        service = IndustryScenariosService()
        
        scenario, error = service.add_scenario(
            industry=data['industry'],
            scenario_type=data['scenario_type'],
            title=data['title'],
            description=data['description'],
            icon_name=data.get('icon_name'),
            priority=data.get('priority', 0),
            details=data.get('details')
        )
        
        if error:
            return {'error': error}, 400
        
        return scenario.to_dict(), 201


@ns.route('/scenarios/<int:scenario_id>')
class ScenarioDetail(Resource):
    @ns.doc('get_scenario')
    @ns.marshal_with(scenario_model)
    def get(self, scenario_id):
        """Get scenario details"""
        service = IndustryScenariosService()
        scenario = service.get_scenario(scenario_id)
        
        if not scenario:
            return {'error': 'Scenario not found'}, 404
        
        return scenario.to_dict()
    
    @ns.expect(update_scenario_model)
    @ns.doc('update_scenario', security='Bearer Auth')
    @ns.marshal_with(scenario_model)
    @jwt_required()
    @error_handler
    @validate_json_request()
    @sanitize_string_input(['title', 'description', 'icon_name'])
    def put(self, scenario_id):
        """Update scenario (admin only)"""
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return {'error': 'Admin access required'}, 403
        
        data = request.get_json()
        service = IndustryScenariosService()
        
        scenario, error = service.update_scenario(
            scenario_id=scenario_id,
            title=data.get('title'),
            description=data.get('description'),
            icon_name=data.get('icon_name'),
            priority=data.get('priority'),
            details=data.get('details'),
            is_active=data.get('is_active')
        )
        
        if error:
            return {'error': error}, 404
        
        return scenario.to_dict()
    
    @ns.doc('delete_scenario', security='Bearer Auth')
    @jwt_required()
    @error_handler
    def delete(self, scenario_id):
        """Delete scenario (admin only)"""
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return {'error': 'Admin access required'}, 403
        
        service = IndustryScenariosService()
        success, error = service.delete_scenario(scenario_id)
        
        if error:
            return {'error': error}, 404
        
        return {'message': 'Scenario deleted successfully'}, 200
