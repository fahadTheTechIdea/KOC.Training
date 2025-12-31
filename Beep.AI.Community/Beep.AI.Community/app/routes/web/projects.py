"""
Projects web routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.project_service import ProjectService
from app.services.branding_service import BrandingService
from app.utils.formatters import format_tags

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/')
def browse():
    """Browse projects"""
    branding = BrandingService.get_branding_config()
    
    service = ProjectService()
    category = request.args.get('category')
    language = request.args.get('language')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    user_id = None
    
    # No industry filter - show all projects
    projects, total = service.list_projects(
        user_id=user_id,
        category=category,
        language=language,
        search=search,
        page=page,
        per_page=20
    )
    
    return render_template(
        'projects/browse.html',
        projects=projects,
        total=total,
        page=page,
        category=category,
        language=language,
        search=search,
        branding=branding
    )


@projects_bp.route('/<int:project_id>')
def view(project_id):
    """View project"""
    branding = BrandingService.get_branding_config()
    
    service = ProjectService()
    project = service.get_project(project_id)
    
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('projects.browse'))
    
    return render_template(
        'projects/view.html',
        project=project,
        branding=branding
    )


@projects_bp.route('/<int:project_id>/fork', methods=['POST'])
@jwt_required()
def fork(project_id):
    """Fork a project"""
    user_id = get_jwt_identity()
    
    service = ProjectService()
    fork, error = service.fork_project(project_id, user_id)
    
    if error:
        flash(f'Cannot fork project: {error}', 'error')
        return redirect(url_for('projects.view', project_id=project_id))
    
    flash('Project forked successfully! You can now find it in your projects.', 'success')
    return redirect(url_for('projects.view', project_id=fork.id))


@projects_bp.route('/<int:project_id>/upvote', methods=['POST'])
@jwt_required()
def upvote(project_id):
    """Upvote a project"""
    user_id = get_jwt_identity()
    
    service = ProjectService()
    success, error = service.upvote_project(project_id, user_id)
    
    if error:
        flash(f'Cannot upvote: {error}', 'error')
    else:
        flash('Project upvoted!', 'success')
    
    return redirect(url_for('projects.view', project_id=project_id))
