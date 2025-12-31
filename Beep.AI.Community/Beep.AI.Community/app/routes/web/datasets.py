"""
Dataset web routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.dataset_service import DatasetService
from app.services.branding_service import BrandingService
from app.utils.formatters import format_file_size, format_tags
from pathlib import Path
import json

datasets_bp = Blueprint('datasets', __name__)


@datasets_bp.route('/')
def browse():
    """Browse datasets"""
    branding = BrandingService.get_branding_config()
    
    service = DatasetService()
    category = request.args.get('category')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    user_id = None
    
    # No industry filter - show all datasets
    datasets, total = service.list_datasets(
        user_id=user_id,
        category=category,
        search=search,
        page=page,
        per_page=20
    )
    
    return render_template(
        'datasets/browse.html',
        datasets=datasets,
        total=total,
        page=page,
        category=category,
        search=search,
        branding=branding
    )


@datasets_bp.route('/<int:dataset_id>')
def detail(dataset_id):
    """Dataset detail page"""
    branding = BrandingService.get_branding_config()
    
    service = DatasetService()
    dataset = service.get_dataset(dataset_id)
    
    if not dataset:
        flash('Dataset not found', 'error')
        return redirect(url_for('datasets.browse'))
    
    preview = service.get_dataset_preview(dataset_id, rows=20)
    stats = service.get_dataset_stats(dataset_id)
    
    return render_template(
        'datasets/detail.html',
        dataset=dataset,
        preview=preview,
        stats=stats,
        branding=branding
    )


@datasets_bp.route('/download/<int:dataset_id>')
def download(dataset_id):
    """Download dataset"""
    service = DatasetService()
    file_path, error = service.download_dataset(dataset_id)
    
    if error:
        flash(error, 'error')
        return redirect(url_for('datasets.browse'))
    
    return send_file(
        str(file_path),
        as_attachment=True,
        download_name=Path(file_path).name
    )


@datasets_bp.route('/upload', methods=['GET', 'POST'])
@jwt_required()
def upload():
    """Upload dataset"""
    branding = BrandingService.get_branding_config()
    
    if request.method == 'GET':
        return render_template('datasets/upload.html', branding=branding)
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return render_template('datasets/upload.html', branding=branding)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return render_template('datasets/upload.html', branding=branding)
    
    user_id = get_jwt_identity()
    service = DatasetService()
    branding = BrandingService.get_branding_config()
    current_industry = branding.industry if branding else 'general'
    
    tags = []
    if request.form.get('tags'):
        tags = [t.strip() for t in request.form.get('tags', '').split(',') if t.strip()]
    
    dataset, error = service.upload_dataset(
        file=file,
        owner_id=user_id,
        title=request.form.get('title', file.filename),
        description=request.form.get('description', ''),
        tags=tags,
        category=request.form.get('category'),
        industry=current_industry,
        license=request.form.get('license', 'MIT'),
        is_public=request.form.get('is_public', 'true').lower() == 'true'
    )
    
    if error:
        flash(f'Upload failed: {error}', 'error')
        return render_template('datasets/upload.html', branding=branding)
    
    flash('Dataset uploaded successfully!', 'success')
    return redirect(url_for('datasets.detail', dataset_id=dataset.id))
