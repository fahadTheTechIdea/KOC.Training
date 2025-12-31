"""
Admin Routes - Admin-only functionality for managing application settings
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required
from pathlib import Path
import os
import uuid
from werkzeug.utils import secure_filename
from app.services.auth_service import AuthService
from app.services.branding_service import BrandingService
from app.utils.constants import HTTP_BAD_REQUEST
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_admin():
    """Helper function to check if current user is admin"""
    current_user = AuthService.get_current_user()
    if not current_user or not current_user.is_admin_role():
        return None
    return current_user


@admin_bp.route('/settings')
@jwt_required()
def settings():
    """Admin settings page - branding management"""
    current_user = require_admin()
    if not current_user:
        return redirect(url_for('main.index'))
    
    branding = BrandingService.get_branding_config()
    # Get available industries for reference
    industries = BrandingService.get_available_industries()
    
    return render_template('admin/settings.html', branding=branding, industries=industries)


@admin_bp.route('/settings/branding', methods=['POST'])
@jwt_required()
def update_branding():
    """Update branding configuration (admin only)"""
    current_user = require_admin()
    if not current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get current branding config
    current_branding = BrandingService.get_branding_config()
    industry = current_branding.industry if current_branding else 'general'
    
    # Handle both JSON (legacy) and multipart/form-data (file upload)
    if request.is_json:
        data = request.get_json()
        company_name = data.get('company_name', '').strip() or None
        icon_name = data.get('icon_name', '').strip() or None
        logo_path = data.get('logo_path')
    else:
        # Multipart/form-data (file upload)
        company_name = request.form.get('company_name', '').strip() or None
        icon_name = request.form.get('icon_name', '').strip() or None
        
        # Handle logo file upload
        logo_file = request.files.get('logo')
        logo_path = None
        
        if logo_file and logo_file.filename:
            # Validate file type
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp'}
            file_ext = Path(logo_file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                return jsonify({
                    'success': False,
                    'message': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
                }), HTTP_BAD_REQUEST
            
            # Validate file size (max 5MB)
            logo_file.seek(0, os.SEEK_END)
            file_size = logo_file.tell()
            logo_file.seek(0)
            if file_size > 5 * 1024 * 1024:  # 5MB
                return jsonify({
                    'success': False,
                    'message': 'File size exceeds 5MB limit'
                }), HTTP_BAD_REQUEST
            
            # Save uploaded file
            upload_dir = Path('static/assets/images/branding')
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename to avoid conflicts
            unique_id = str(uuid.uuid4())[:8]
            original_name = secure_filename(logo_file.filename)
            file_stem = Path(original_name).stem
            saved_filename = f"{file_stem}_{unique_id}{file_ext}"
            logo_path = upload_dir / saved_filename
            
            try:
                logo_file.save(str(logo_path))
                logo_path = str(logo_path)  # Convert to string for service
                logger.info(f"Logo file uploaded by admin: {logo_path}")
            except Exception as e:
                logger.error(f"Error saving logo file: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Failed to save logo file: {str(e)}'
                }), HTTP_BAD_REQUEST
    
    try:
        # Use existing branding values if not provided
        if not company_name and current_branding:
            company_name = current_branding.company_name
        
        # Update branding configuration
        config = BrandingService.setup_industry_branding(
            industry=industry,  # Keep current industry
            company_name=company_name,
            logo_path=logo_path if logo_path else None,
            icon_name=icon_name
        )
        
        logger.info(f"Branding updated by admin: {current_user.username}")
        return jsonify({
            'success': True,
            'message': 'Branding updated successfully',
            'branding': config.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating branding: {e}", exc_info=True)
        # Clean up uploaded file if branding update failed
        if logo_path and Path(logo_path).exists():
            try:
                Path(logo_path).unlink()
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup uploaded logo file: {cleanup_error}")
        return jsonify({
            'success': False,
            'message': f'Failed to update branding: {str(e)}'
        }), HTTP_BAD_REQUEST


# ==================== Competition Management ====================

@admin_bp.route('/competitions')
@jwt_required()
def competitions_list():
    """List all competitions (admin only)"""
    current_user = require_admin()
    if not current_user:
        return redirect(url_for('main.index'))
    
    from app.services.competition_service import CompetitionService
    from flask import request
    
    service = CompetitionService()
    
    # Get filter parameters
    is_active_param = request.args.get('is_active')
    is_active = None
    if is_active_param == 'true':
        is_active = True
    elif is_active_param == 'false':
        is_active = False
    
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    competitions, total = service.list_competitions(
        user_id=None,
        industry=None,  # Show all industries for admin
        is_active=is_active,
        page=page,
        per_page=per_page,
        search=search
    )
    
    return render_template(
        'admin/competitions/list.html',
        competitions=competitions,
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        is_active=is_active,
        is_active_param=is_active_param or ''
    )


@admin_bp.route('/competitions/<int:competition_id>')
@jwt_required()
def competitions_detail(competition_id):
    """View competition details (admin only)"""
    current_user = require_admin()
    if not current_user:
        return redirect(url_for('main.index'))
    
    from app.services.competition_service import CompetitionService
    service = CompetitionService()
    
    competition = service.get_competition(competition_id)
    if not competition:
        from flask import flash
        flash('Competition not found', 'error')
        return redirect(url_for('admin.competitions_list'))
    
    # Get stats
    stats = service.get_competition_stats(competition_id)
    
    # Get all submissions
    from app.models.submission import Submission
    from sqlalchemy import desc
    submissions = Submission.query.filter_by(competition_id=competition_id).order_by(desc(Submission.submitted_at)).all()
    
    # Get participants
    from app.models.competition import CompetitionParticipant
    participants = CompetitionParticipant.query.filter_by(competition_id=competition_id).all()
    
    return render_template(
        'admin/competitions/detail.html',
        competition=competition,
        stats=stats,
        submissions=submissions,
        participants=participants
    )


@admin_bp.route('/competitions/<int:competition_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def competitions_edit(competition_id):
    """Edit competition (admin only)"""
    current_user = require_admin()
    if not current_user:
        return redirect(url_for('main.index'))
    
    from app.services.competition_service import CompetitionService
    from app.services.dataset_service import DatasetService
    from datetime import datetime
    from flask import flash
    
    service = CompetitionService()
    competition = service.get_competition(competition_id)
    
    if not competition:
        flash('Competition not found', 'error')
        return redirect(url_for('admin.competitions_list'))
    
    if request.method == 'GET':
        # Get available datasets
        dataset_service = DatasetService()
        datasets, _ = dataset_service.list_datasets(user_id=None, is_public=True, page=1, per_page=100)
        
        # Parse target_columns JSON for template
        import json
        target_columns_list = None
        if competition.target_columns:
            try:
                target_columns_list = json.loads(competition.target_columns)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return render_template('admin/competitions/edit.html', 
                             competition=competition, 
                             datasets=datasets,
                             target_columns_list=target_columns_list)
    
    # POST - Update competition
    try:
        updates = {}
        
        if 'title' in request.form:
            updates['title'] = request.form['title']
        if 'description' in request.form:
            updates['description'] = request.form['description']
        # evaluation_metric is auto-determined from task_type, no need to update manually
        if 'prize_description' in request.form:
            updates['prize_description'] = request.form.get('prize_description')
        if 'leaderboard_type' in request.form:
            updates['leaderboard_type'] = request.form['leaderboard_type']
        if 'max_submissions_per_day' in request.form:
            updates['max_submissions_per_day'] = int(request.form['max_submissions_per_day'])
        if 'max_total_submissions' in request.form:
            updates['max_total_submissions'] = int(request.form['max_total_submissions'])
        
        # Handle task configuration if provided (from Task Configuration form)
        # This is handled via AJAX in the template, but can also be done here if needed
        
        dataset_id = request.form.get('dataset_id')
        if dataset_id:
            dataset_id = int(dataset_id)
            if dataset_id == 0:
                dataset_id = None
            updates['dataset_id'] = dataset_id
        
        if request.form.get('start_date'):
            updates['start_date'] = datetime.fromisoformat(request.form['start_date'].replace('Z', '+00:00'))
        if request.form.get('end_date'):
            updates['end_date'] = datetime.fromisoformat(request.form['end_date'].replace('Z', '+00:00'))
        
        if 'is_active' in request.form:
            updates['is_active'] = request.form['is_active'] == 'true'
        
        # Admin can edit any competition - pass admin user_id so service checks admin role
        competition_obj, error = service.update_competition(
            competition_id=competition_id,
            organizer_id=current_user.id,  # Pass admin user_id for authorization check
            updates=updates
        )
        
        if error:
            flash(f'Error updating competition: {error}', 'error')
            return redirect(url_for('admin.competitions_edit', competition_id=competition_id))
        
        flash('Competition updated successfully!', 'success')
        return redirect(url_for('admin.competitions_detail', competition_id=competition_id))
        
    except Exception as e:
        logger.error(f"Error updating competition: {e}", exc_info=True)
        flash(f'Error updating competition: {str(e)}', 'error')
        return redirect(url_for('admin.competitions_edit', competition_id=competition_id))


@admin_bp.route('/competitions/<int:competition_id>/delete', methods=['POST'])
@jwt_required()
def competitions_delete(competition_id):
    """Delete competition (admin only)"""
    current_user = require_admin()
    if not current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from app.services.competition_service import CompetitionService
    from flask import flash
    
    service = CompetitionService()
    # Admin can delete - use competition's organizer_id for the check (service will allow admin)
    competition = service.get_competition(competition_id)
    if not competition:
        flash('Competition not found', 'error')
        return redirect(url_for('admin.competitions_list'))
    
    success, error = service.delete_competition(competition_id, current_user.id)
    
    if error:
        flash(f'Error: {error}', 'error')
    else:
        flash('Competition deleted successfully', 'success')
    
    return redirect(url_for('admin.competitions_list'))


@admin_bp.route('/competitions/<int:competition_id>/toggle-active', methods=['POST'])
@jwt_required()
def competitions_toggle_active(competition_id):
    """Toggle competition active status (admin only)"""
    current_user = require_admin()
    if not current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from app.services.competition_service import CompetitionService
    
    service = CompetitionService()
    competition = service.get_competition(competition_id)
    
    if not competition:
        return jsonify({'success': False, 'message': 'Competition not found'}), 404
    
    competition.is_active = not competition.is_active
    from app import db
    db.session.commit()
    
    status = 'activated' if competition.is_active else 'deactivated'
    return jsonify({'success': True, 'message': f'Competition {status} successfully', 'is_active': competition.is_active})


@admin_bp.route('/competitions/<int:competition_id>/submissions')
@jwt_required()
def competitions_submissions(competition_id):
    """View all submissions for a competition (admin only)"""
    current_user = require_admin()
    if not current_user:
        return redirect(url_for('main.index'))
    
    from app.services.competition_service import CompetitionService
    from app.models.submission import Submission
    from sqlalchemy import desc
    
    service = CompetitionService()
    competition = service.get_competition(competition_id)
    
    if not competition:
        from flask import flash
        flash('Competition not found', 'error')
        return redirect(url_for('admin.competitions_list'))
    
    # Get all submissions
    submissions = Submission.query.filter_by(competition_id=competition_id).order_by(desc(Submission.submitted_at)).all()
    
    return render_template(
        'admin/competitions/submissions.html',
        competition=competition,
        submissions=submissions
    )


@admin_bp.route('/competitions/<int:competition_id>/submissions/<int:submission_id>/evaluate', methods=['POST'])
@jwt_required()
def competitions_evaluate_submission(competition_id, submission_id):
    """Manually evaluate/update submission score (admin only)"""
    current_user = require_admin()
    if not current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from app.services.competition_service import CompetitionService
    from flask import request
    
    service = CompetitionService()
    
    data = request.get_json()
    score = data.get('score')
    
    if score is None:
        return jsonify({'success': False, 'message': 'Score is required'}), 400
    
    try:
        score = float(score)
        success, error = service.update_submission_score(
            submission_id=submission_id,
            score=score,
            metadata=data.get('metadata')
        )
        
        if error:
            return jsonify({'success': False, 'message': error}), 400
        
        return jsonify({'success': True, 'message': 'Submission evaluated successfully'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid score format'}), 400


# ==================== Competition Dataset and Scoring Management ====================

@admin_bp.route('/competitions/<int:competition_id>/preview-dataset-columns', methods=['POST'])
@jwt_required()
def competitions_preview_dataset_columns(competition_id):
    """Preview columns from uploaded dataset file (before splitting)"""
    current_user = require_admin()
    if not current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from app.services.competition_service import CompetitionService
    from flask import request
    
    service = CompetitionService()
    competition = service.get_competition(competition_id)
    
    if not competition:
        return jsonify({'success': False, 'message': 'Competition not found'}), 404
    
    # Get file
    dataset_file = request.files.get('dataset_file')
    if not dataset_file or not dataset_file.filename:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    # Preview columns
    columns, error = service.preview_dataset_columns(dataset_file)
    
    if error:
        return jsonify({'success': False, 'message': error}), 400
    
    return jsonify({
        'success': True,
        'columns': columns,
        'count': len(columns) if columns else 0
    })

@admin_bp.route('/competitions/<int:competition_id>/upload-dataset', methods=['POST'])
@jwt_required()
def competitions_upload_dataset(competition_id):
    """Upload and split dataset for competition (admin only)"""
    current_user = require_admin()
    if not current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from app.services.competition_service import CompetitionService
    from flask import request
    
    service = CompetitionService()
    competition = service.get_competition(competition_id)
    
    if not competition:
        return jsonify({'success': False, 'message': 'Competition not found'}), 404
    
    # Get file, train_ratio, task_type, target_column(s), and id_column
    dataset_file = request.files.get('dataset_file')
    if not dataset_file or not dataset_file.filename:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    train_ratio = request.form.get('train_ratio', 0.8, type=float)
    if not (0.1 <= train_ratio <= 0.9):
        return jsonify({'success': False, 'message': 'Train ratio must be between 0.1 and 0.9'}), 400
    
    task_type = request.form.get('task_type')
    if not task_type:
        return jsonify({'success': False, 'message': 'Task type is required'}), 400
    
    id_column = request.form.get('id_column')
    if not id_column:
        return jsonify({'success': False, 'message': 'ID column is required'}), 400
    
    # Determine if multi-target task
    is_multi_target = service._is_multi_target_task(task_type)
    
    # Get target column(s) based on task type
    target_column = None
    target_columns = None
    
    if is_multi_target:
        target_columns_str = request.form.get('target_columns')
        if not target_columns_str:
            return jsonify({'success': False, 'message': 'Target columns are required for multi-target tasks'}), 400
        # Parse comma-separated string or handle as list
        target_columns = [col.strip() for col in target_columns_str.split(',') if col.strip()]
        if len(target_columns) == 0:
            return jsonify({'success': False, 'message': 'At least one target column is required'}), 400
    else:
        target_column = request.form.get('target_column')
        if not target_column:
            return jsonify({'success': False, 'message': 'Target column is required for single-target tasks'}), 400
    
    success, error = service.upload_competition_dataset(
        competition_id=competition_id,
        dataset_file=dataset_file,
        train_ratio=train_ratio,
        task_type=task_type,
        target_column=target_column,
        target_columns=target_columns,
        id_column=id_column,
        organizer_id=current_user.id
    )
    
    if error:
        return jsonify({'success': False, 'message': error}), 400
    
    # Refresh competition object to get updated paths
    competition = service.get_competition(competition_id)
    
    return jsonify({
        'success': True,
        'message': 'Dataset uploaded and split successfully',
        'training_data_path': competition.training_data_path,
        'test_data_path': competition.test_data_path
    })


@admin_bp.route('/competitions/<int:competition_id>/update-schemas', methods=['POST'])
@jwt_required()
def competitions_update_schemas(competition_id):
    """Update input/output schemas for competition (admin only)"""
    current_user = require_admin()
    if not current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from app.services.competition_service import CompetitionService
    from flask import request
    
    service = CompetitionService()
    
    data = request.get_json()
    input_schema = data.get('input_schema')
    output_schema = data.get('output_schema')
    
    success, error = service.update_schemas(
        competition_id=competition_id,
        input_schema=input_schema,
        output_schema=output_schema,
        organizer_id=current_user.id
    )
    
    if error:
        return jsonify({'success': False, 'message': error}), 400
    
    return jsonify({'success': True, 'message': 'Schemas updated successfully'})


@admin_bp.route('/competitions/<int:competition_id>/update-formats', methods=['POST'])
@jwt_required()
def competitions_update_formats(competition_id):
    """Update allowed model formats for competition (admin only)"""
    current_user = require_admin()
    if not current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from app.services.competition_service import CompetitionService
    from flask import request
    
    service = CompetitionService()
    
    data = request.get_json()
    formats = data.get('formats', '')
    
    success, error = service.update_allowed_formats(
        competition_id=competition_id,
        formats=formats,
        organizer_id=current_user.id
    )
    
    if error:
        return jsonify({'success': False, 'message': error}), 400
    
    return jsonify({'success': True, 'message': 'Allowed formats updated successfully'})


@admin_bp.route('/competitions/<int:competition_id>/update-scoring-config', methods=['POST'])
@jwt_required()
def competitions_update_scoring_config(competition_id):
    """Update scoring configuration for competition (admin only)"""
    current_user = require_admin()
    if not current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from app.services.competition_service import CompetitionService
    from flask import request
    
    service = CompetitionService()
    competition = service.get_competition(competition_id)
    
    if not competition:
        return jsonify({'success': False, 'message': 'Competition not found'}), 404
    
    data = request.get_json()
    evaluation_metric = data.get('evaluation_metric')
    target_column = data.get('target_column')
    
    if not evaluation_metric:
        return jsonify({'success': False, 'message': 'evaluation_metric is required'}), 400
    if not target_column:
        return jsonify({'success': False, 'message': 'target_column is required'}), 400
    
    success, error = service.update_scoring_config(
        competition_id=competition_id,
        evaluation_metric=evaluation_metric,
        target_column=target_column,
        organizer_id=current_user.id
    )
    
    if error:
        return jsonify({'success': False, 'message': error}), 400
    
    return jsonify({'success': True, 'message': 'Scoring configuration updated successfully'})


@admin_bp.route('/competitions/<int:competition_id>/update-task-config', methods=['POST'])
@jwt_required()
def competitions_update_task_config(competition_id):
    """Update task configuration for competition (admin only)"""
    current_user = require_admin()
    if not current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from app.services.competition_service import CompetitionService
    from flask import request
    
    service = CompetitionService()
    competition = service.get_competition(competition_id)
    
    if not competition:
        return jsonify({'success': False, 'message': 'Competition not found'}), 404
    
    data = request.get_json()
    task_type = data.get('task_type')
    target_columns = data.get('target_columns')  # List
    prediction_format = data.get('prediction_format')
    evaluation_config = data.get('evaluation_config')  # Dict
    id_column = data.get('id_column')  # NEW
    
    if not task_type:
        return jsonify({'success': False, 'message': 'task_type is required'}), 400
    
    success, error = service.update_task_configuration(
        competition_id=competition_id,
        task_type=task_type,
        target_columns=target_columns,
        prediction_format=prediction_format,
        evaluation_config=evaluation_config,
        id_column=id_column,
        organizer_id=current_user.id
    )
    
    if error:
        return jsonify({'success': False, 'message': error}), 400
    
    return jsonify({'success': True, 'message': 'Task configuration updated successfully'})
