"""
Discussions Web Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from app.services.discussion_service import DiscussionService
from app.services.branding_service import BrandingService

discussions_bp = Blueprint('discussions', __name__)


@discussions_bp.route('')
def browse():
    """Browse discussions"""
    branding = BrandingService.get_branding_config()
    service = DiscussionService()
    
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except:
        pass
    
    topic_type = request.args.get('topic_type')
    topic_id = request.args.get('topic_id', type=int)
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    discussions, total = service.list_discussions(
        topic_type=topic_type,
        topic_id=topic_id,
        page=page,
        per_page=per_page,
        search=search
    )
    
    # Add upvote status for authenticated users
    if user_id:
        for discussion in discussions:
            discussion.has_upvoted = service.has_upvoted(discussion.id, user_id)
    
    return render_template(
        'discussions/browse.html',
        discussions=discussions,
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        topic_type=topic_type,
        topic_id=topic_id,
        user_id=user_id,
        branding=branding
    )


@discussions_bp.route('/<int:discussion_id>')
def detail(discussion_id):
    """Discussion detail page"""
    branding = BrandingService.get_branding_config()
    service = DiscussionService()
    
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except:
        pass
    
    discussion = service.get_discussion(discussion_id)
    
    if not discussion:
        flash('Discussion not found', 'error')
        return redirect(url_for('discussions.browse'))
    
    # Get replies (ordered by creation date)
    replies = []
    if hasattr(discussion, 'replies') and discussion.replies:
        replies = sorted(discussion.replies, key=lambda r: r.created_at if r.created_at else datetime.min)
    
    # Add upvote status
    has_upvoted = False
    if user_id:
        has_upvoted = service.has_upvoted(discussion_id, user_id)
    
    return render_template(
        'discussions/detail.html',
        discussion=discussion,
        replies=replies,
        has_upvoted=has_upvoted,
        user_id=user_id,
        branding=branding
    )


@discussions_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create():
    """Create discussion"""
    branding = BrandingService.get_branding_config()
    user_id = get_jwt_identity()
    
    if request.method == 'GET':
        topic_type = request.args.get('topic_type')
        topic_id = request.args.get('topic_id', type=int)
        
        return render_template(
            'discussions/create.html',
            topic_type=topic_type,
            topic_id=topic_id,
            branding=branding
        )
    
    # POST - Create discussion
    service = DiscussionService()
    
    discussion, error = service.create_discussion(
        author_id=user_id,
        title=request.form['title'],
        content=request.form['content'],
        topic_type=request.form.get('topic_type'),
        topic_id=request.form.get('topic_id', type=int) if request.form.get('topic_id') else None
    )
    
    if error:
        flash(f'Error creating discussion: {error}', 'error')
        return redirect(url_for('discussions.create'))
    
    flash('Discussion created successfully!', 'success')
    return redirect(url_for('discussions.detail', discussion_id=discussion.id))


@discussions_bp.route('/<int:discussion_id>/reply', methods=['POST'])
@jwt_required()
def reply(discussion_id):
    """Reply to discussion"""
    user_id = get_jwt_identity()
    service = DiscussionService()
    
    reply, error = service.reply_to_discussion(
        discussion_id=discussion_id,
        author_id=user_id,
        content=request.form['content']
    )
    
    if error:
        flash(f'Error: {error}', 'error')
    else:
        flash('Reply added successfully!', 'success')
    
    return redirect(url_for('discussions.detail', discussion_id=discussion_id))


@discussions_bp.route('/<int:discussion_id>/upvote', methods=['POST'])
@jwt_required()
def upvote(discussion_id):
    """Upvote discussion"""
    user_id = get_jwt_identity()
    service = DiscussionService()
    
    success, error = service.upvote_discussion(discussion_id, user_id)
    
    if error:
        flash(f'Error: {error}', 'error')
    else:
        flash('Discussion upvoted!', 'success')
    
    return redirect(url_for('discussions.detail', discussion_id=discussion_id))


@discussions_bp.route('/<int:discussion_id>/solve', methods=['POST'])
@jwt_required()
def solve(discussion_id):
    """Mark discussion as solved"""
    user_id = get_jwt_identity()
    service = DiscussionService()
    
    success, error = service.mark_as_solved(discussion_id, user_id)
    
    if error:
        flash(f'Error: {error}', 'error')
    else:
        flash('Discussion marked as solved!', 'success')
    
    return redirect(url_for('discussions.detail', discussion_id=discussion_id))
