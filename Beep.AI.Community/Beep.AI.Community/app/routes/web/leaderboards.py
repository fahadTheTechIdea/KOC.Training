"""
Leaderboards Web Routes
"""
from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy import func, desc, and_, case
from app import db
from app.models.submission import Submission
from app.models.competition import Competition, CompetitionParticipant
from app.models.user import User
from app.services.competition_service import CompetitionService
from app.services.branding_service import BrandingService
import logging

logger = logging.getLogger(__name__)

leaderboards_bp = Blueprint('leaderboards', __name__)


@leaderboards_bp.route('')
def index():
    """Global leaderboard and per-competition leaderboards"""
    branding = BrandingService.get_branding_config()
    
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except:
        pass
    
    # Get selected competition ID from query params
    selected_competition_id = request.args.get('competition_id', type=int)
    
    # Get global leaderboard - aggregate scores across all competitions
    global_leaderboard = get_global_leaderboard(limit=50)
    
    # Get all competitions for dropdown
    competition_service = CompetitionService()
    competitions, _ = competition_service.list_competitions(
        user_id=user_id,
        page=1,
        per_page=100
    )
    
    # Get per-competition leaderboard if competition is selected
    competition_leaderboard = None
    selected_competition = None
    if selected_competition_id:
        selected_competition = competition_service.get_competition(selected_competition_id, user_id)
        if selected_competition:
            competition_leaderboard = get_competition_leaderboard(selected_competition_id, limit=20)
    
    return render_template(
        'leaderboards/index.html',
        global_leaderboard=global_leaderboard,
        competition_leaderboard=competition_leaderboard,
        competitions=competitions,
        selected_competition=selected_competition,
        selected_competition_id=selected_competition_id,
        user_id=user_id,
        branding=branding
    )


def get_global_leaderboard(limit=50):
    """
    Calculate global leaderboard across all competitions
    Returns list of users with their aggregated stats
    """
    # Get best submission per user per competition
    best_submissions = db.session.query(
        Submission.user_id,
        Submission.competition_id,
        func.max(Submission.score).label('best_score'),
        func.min(Submission.rank).label('best_rank')  # min rank = best placement (1 = first place)
    ).filter(
        Submission.status == 'evaluated',
        Submission.score.isnot(None)
    ).group_by(
        Submission.user_id,
        Submission.competition_id
    ).subquery()
    
    # Aggregate user stats
    user_stats = db.session.query(
        best_submissions.c.user_id,
        func.count(best_submissions.c.competition_id).label('competitions_joined'),
        func.sum(best_submissions.c.best_score).label('total_points'),
        func.avg(best_submissions.c.best_score).label('avg_score'),
        func.sum(case((best_submissions.c.best_rank == 1, 1), else_=0)).label('wins')
    ).group_by(
        best_submissions.c.user_id
    ).order_by(
        desc('total_points'),
        desc('wins'),
        desc('avg_score')
    ).limit(limit).all()
    
    # Get user details and build leaderboard
    leaderboard = []
    rank = 1
    for stat in user_stats:
        user = User.query.get(stat.user_id)
        if user:
            profile = user.profile if hasattr(user, 'profile') else None
            leaderboard.append({
                'rank': rank,
                'user_id': stat.user_id,
                'username': user.username,
                'display_name': profile.display_name if profile and profile.display_name else user.username,
                'total_points': round(stat.total_points or 0, 2),
                'avg_score': round(stat.avg_score or 0, 2),
                'competitions_joined': stat.competitions_joined or 0,
                'wins': stat.wins or 0
            })
            rank += 1
    
    return leaderboard


def get_competition_leaderboard(competition_id, limit=20):
    """
    Get leaderboard for a specific competition
    """
    submissions = db.session.query(
        Submission.user_id,
        Submission.score,
        Submission.rank,
        Submission.submitted_at
    ).filter(
        Submission.competition_id == competition_id,
        Submission.status == 'evaluated',
        Submission.score.isnot(None)
    ).order_by(
        Submission.rank.asc(),
        Submission.score.desc()
    ).limit(limit).all()
    
    leaderboard = []
    seen_users = set()
    rank = 1
    
    for submission in submissions:
        if submission.user_id in seen_users:
            continue  # Only show best submission per user
        
        seen_users.add(submission.user_id)
        user = User.query.get(submission.user_id)
        if user:
            profile = user.profile if hasattr(user, 'profile') else None
            leaderboard.append({
                'rank': rank,
                'user_id': submission.user_id,
                'username': user.username,
                'display_name': profile.display_name if profile and profile.display_name else user.username,
                'score': round(submission.score, 2) if submission.score else 0,
                'submitted_at': submission.submitted_at
            })
            rank += 1
    
    return leaderboard


@leaderboards_bp.route('/api/global')
def api_global():
    """API endpoint for global leaderboard"""
    limit = request.args.get('limit', 50, type=int)
    leaderboard = get_global_leaderboard(limit=limit)
    return jsonify({'leaderboard': leaderboard})


@leaderboards_bp.route('/api/competition/<int:competition_id>')
def api_competition(competition_id):
    """API endpoint for competition leaderboard"""
    limit = request.args.get('limit', 20, type=int)
    leaderboard = get_competition_leaderboard(competition_id, limit=limit)
    return jsonify({'leaderboard': leaderboard})

