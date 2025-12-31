"""
Users API endpoints - placeholder
"""
from flask_restx import Namespace, Resource

ns = Namespace('users', description='User operations')

@ns.route('')
class Users(Resource):
    def get(self):
        return {'message': 'User API - Coming in Phase 5'}, 200
