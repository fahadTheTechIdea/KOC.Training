"""
Competitions Web Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from app.services.competition_service import CompetitionService
from app.services.auth_service import AuthService
from app.services.dataset_service import DatasetService
from app.services.branding_service import BrandingService
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

competitions_bp = Blueprint('competitions', __name__)


@competitions_bp.route('')
def browse():
    """Browse competitions"""
    branding = BrandingService.get_branding_config()
    service = CompetitionService()
    
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except:
        pass
    
    is_active_param = request.args.get('is_active')
    is_active = None
    if is_active_param == 'true':
        is_active = True
    elif is_active_param == 'false':
        is_active = False
    
    # No industry filter - show all competitions
    industry_filter = request.args.get('industry')
    if industry_filter == 'all' or not industry_filter:
        industry_filter = None  # Show all industries
    
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    competitions, total = service.list_competitions(
        user_id=user_id,
        industry=industry_filter,
        is_active=is_active,
        page=page,
        per_page=per_page,
        search=search
    )
    
    # Add participation status for authenticated users
    if user_id:
        for competition in competitions:
            competition.is_participant = service.is_participant(competition.id, user_id)
    
    # Get available industries for filter dropdown
    available_industries = list(BrandingService.INDUSTRY_THEMES.keys())
    
    return render_template(
        'competitions/browse.html',
        competitions=competitions,
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        is_active=is_active,
        is_active_param=request.args.get('is_active', ''),
        industry_filter=industry_filter or 'all',
        available_industries=available_industries,
        industry_themes=BrandingService.INDUSTRY_THEMES,
        user_id=user_id,
        branding=branding
    )


@competitions_bp.route('/<int:competition_id>')
def detail(competition_id):
    """Competition detail page"""
    branding = BrandingService.get_branding_config()
    service = CompetitionService()
    
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except:
        pass
    
    competition = service.get_competition(competition_id, user_id)
    
    if not competition:
        flash('Competition not found', 'error')
        return redirect(url_for('competitions.browse'))
    
    # Add participation status
    is_participant = False
    if user_id:
        is_participant = service.is_participant(competition_id, user_id)
    
    # Get leaderboard (top 10 for preview)
    leaderboard = service.get_leaderboard(competition_id, limit=10)
    
    # Get user's submissions if authenticated
    user_submissions = []
    if user_id:
        user_submissions = service.get_user_submissions(competition_id, user_id)
    
    # Get stats
    stats = service.get_competition_stats(competition_id)
    
    return render_template(
        'competitions/detail.html',
        competition=competition,
        leaderboard=leaderboard,
        user_submissions=user_submissions,
        stats=stats,
        is_participant=is_participant,
        user_id=user_id,
        branding=branding
    )


@competitions_bp.route('/<int:competition_id>/leaderboard')
def leaderboard(competition_id):
    """Full leaderboard page"""
    branding = BrandingService.get_branding_config()
    service = CompetitionService()
    
    competition = service.get_competition(competition_id)
    
    if not competition:
        flash('Competition not found', 'error')
        return redirect(url_for('competitions.browse'))
    
    limit = request.args.get('limit', 100, type=int)
    full_leaderboard = service.get_leaderboard(competition_id, limit)
    
    return render_template(
        'competitions/leaderboard.html',
        competition=competition,
        leaderboard=full_leaderboard,
        branding=branding
    )


@competitions_bp.route('/<int:competition_id>/download-training-data')
@jwt_required()
def download_training_data(competition_id):
    """Download training dataset for a competition (participants only)"""
    from flask import send_file
    from pathlib import Path
    
    user_id = get_jwt_identity()
    service = CompetitionService()
    
    # Check if user is participant
    if not service.is_participant(competition_id, user_id):
        flash('You must join the competition to download training data', 'error')
        return redirect(url_for('competitions.detail', competition_id=competition_id))
    
    competition = service.get_competition(competition_id)
    if not competition or not competition.training_data_path:
        flash('Training data not available for this competition', 'error')
        return redirect(url_for('competitions.detail', competition_id=competition_id))
    
    # Resolve file path and send
    file_path = Path(competition.training_data_path)
    if not file_path.is_absolute():
        file_path = Path('uploads/competitions') / competition.training_data_path
    
    if not file_path.exists():
        flash('Training data file not found', 'error')
        return redirect(url_for('competitions.detail', competition_id=competition_id))
    
    return send_file(
        str(file_path),
        as_attachment=True,
        download_name=file_path.name
    )


@competitions_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create():
    """Create competition (admin/organizer only)"""
    branding = BrandingService.get_branding_config()
    user_id = get_jwt_identity()
    
    # Check if user is admin
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        flash('Only administrators can create competitions', 'error')
        return redirect(url_for('competitions.browse'))
    
    if request.method == 'GET':
        # Get available datasets for selection
        dataset_service = DatasetService()
        datasets, _ = dataset_service.list_datasets(user_id=user_id, is_public=True, page=1, per_page=100)
        
        return render_template('competitions/create.html', datasets=datasets, branding=branding)
    
    # POST - Create competition
    service = CompetitionService()
    
    try:
        # Parse dates
        start_date = None
        end_date = None
        
        if request.form.get('start_date'):
            start_date = datetime.fromisoformat(request.form['start_date'].replace('Z', '+00:00'))
        if request.form.get('end_date'):
            end_date = datetime.fromisoformat(request.form['end_date'].replace('Z', '+00:00'))
        
        dataset_id = request.form.get('dataset_id')
        if dataset_id:
            dataset_id = int(dataset_id)
            if dataset_id == 0:
                dataset_id = None
        
        current_industry = branding.industry if branding else 'general'
        competition, error = service.create_competition(
            organizer_id=user_id,
            title=request.form['title'],
            description=request.form['description'],
            dataset_id=dataset_id,
            industry=current_industry,
            start_date=start_date,
            end_date=end_date,
            evaluation_metric=request.form.get('evaluation_metric'),
            max_submissions_per_day=int(request.form.get('max_submissions_per_day', 5)),
            max_total_submissions=int(request.form.get('max_total_submissions', 100)),
            prize_description=request.form.get('prize_description'),
            leaderboard_type=request.form.get('leaderboard_type', 'public')
        )
        
        if error:
            flash(f'Error creating competition: {error}', 'error')
            return redirect(url_for('competitions.create'))
        
        flash('Competition created successfully!', 'success')
        return redirect(url_for('competitions.detail', competition_id=competition.id))
        
    except Exception as e:
        logger.error(f"Error creating competition: {e}")
        flash(f'Error creating competition: {str(e)}', 'error')
        return redirect(url_for('competitions.create'))


@competitions_bp.route('/<int:competition_id>/join', methods=['POST'])
@jwt_required()
def join(competition_id):
    """Join competition"""
    user_id = get_jwt_identity()
    service = CompetitionService()
    
    participant, error = service.join_competition(competition_id, user_id)
    
    if error:
        flash(f'Error: {error}', 'error')
    else:
        flash('Successfully joined competition!', 'success')
    
    return redirect(url_for('competitions.detail', competition_id=competition_id))


@competitions_bp.route('/<int:competition_id>/leave', methods=['POST'])
@jwt_required()
def leave(competition_id):
    """Leave competition"""
    user_id = get_jwt_identity()
    service = CompetitionService()
    
    success, error = service.leave_competition(competition_id, user_id)
    
    if error:
        flash(f'Error: {error}', 'error')
    else:
        flash('Left competition successfully', 'success')
    
    return redirect(url_for('competitions.detail', competition_id=competition_id))


@competitions_bp.route('/<int:competition_id>/submit', methods=['POST'])
@jwt_required()
def submit(competition_id):
    """Submit model to competition - validates model and creates submission"""
    import base64
    import tempfile
    from pathlib import Path
    
    user_id = get_jwt_identity()
    # Convert string ID to int
    user_id = int(user_id) if user_id else None
    
    service = CompetitionService()
    
    # Check if user is participant
    if not service.is_participant(competition_id, user_id):
        flash('You must join the competition before submitting', 'error')
        return redirect(url_for('competitions.detail', competition_id=competition_id))
    
    # Get form data - only model file needed
    model_file = request.files.get('model_file')
    
    # Validate required fields
    if not model_file:
        flash('Model file is required', 'error')
        return redirect(url_for('competitions.detail', competition_id=competition_id))
    
    # Auto-generate model name: userid_competitionid_generatedid
    import uuid
    generated_id = uuid.uuid4().hex[:8]  # Short unique ID
    model_name = f"{user_id}_{competition_id}_{generated_id}"
    
    # Save uploaded file temporarily and convert to base64
    temp_file = None
    try:
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(model_file.filename).suffix)
        model_file.save(temp_file.name)
        temp_file.close()
        
        # Read and encode as base64
        with open(temp_file.name, 'rb') as f:
            model_file_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Submit model using the submit_model_to_competition method
        # This will validate the model and create submission if valid
        # Framework will be auto-detected, no description needed
        submission, error = service.submit_model_to_competition(
            competition_id=competition_id,
            user_id=user_id,
            model_name=model_name,
            model_file_data=model_file_data,
            model_file_path=None,  # We're using base64 data
            model_type=None,  # Will be auto-detected
            framework=None,  # Auto-detect (no user selection)
            metrics=None,
            description=None,  # No description from user
            input_schema=None,
            output_schema=None,
            mlstudio_source_id=None
        )
        
        if error:
            # Parse validation errors for display
            error_message = error
            if 'validation failed' in error.lower():
                flash(f'Model validation failed: {error_message}', 'error')
            else:
                flash(f'Error submitting model: {error_message}', 'error')
        else:
            flash('Model submitted successfully! It is being evaluated.', 'success')
    
    except Exception as e:
        logger.error(f"Error submitting model: {e}", exc_info=True)
        flash(f'Error submitting model: {str(e)}', 'error')
    
    finally:
        # Clean up temp file
        if temp_file and Path(temp_file.name).exists():
            try:
                Path(temp_file.name).unlink()
            except:
                pass
    
    return redirect(url_for('competitions.detail', competition_id=competition_id))
