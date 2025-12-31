"""
Health check endpoint
"""
from flask_restx import Namespace, Resource

ns = Namespace('health', description='Health check')


@ns.route('')
class Health(Resource):
    def get(self):
        """Health check endpoint"""
        return {'status': 'ok', 'service': 'Beep.AI.Community'}, 200
