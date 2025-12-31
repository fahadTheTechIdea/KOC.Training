"""
API v1 Routes
"""
from flask import Blueprint
from flask_restx import Api

api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

api = Api(
    api_v1_bp,
    version='1.0',
    title='KOC A.I. Digital Campus API',
    description='REST API for KOC A.I. Digital Campus - Knowledge Reservoir Platform',
    doc='/docs'
)

try:
    from app.routes.api.v1 import auth, datasets, notebooks, health
    api.add_namespace(auth.ns, path='/auth')
    api.add_namespace(datasets.ns, path='/datasets')
    api.add_namespace(notebooks.ns, path='/notebooks')
    api.add_namespace(health.ns, path='/health')
except ImportError as e:
    print(f"Warning: Could not import some API modules: {e}")

try:
    from app.routes.api.v1 import competitions, models, discussions, users, industry_scenarios, user_participation
    api.add_namespace(competitions.ns, path='/competitions')
    api.add_namespace(models.ns, path='/models')
    api.add_namespace(discussions.ns, path='/discussions')
    api.add_namespace(users.ns, path='/users')
    api.add_namespace(industry_scenarios.ns, path='/industry-scenarios')
    api.add_namespace(user_participation.ns, path='/users')
except ImportError:
    pass
