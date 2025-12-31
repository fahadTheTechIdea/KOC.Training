"""
Dataset Service - Data sharing and management
"""
import os
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app import db
from app.models.dataset import Dataset, DatasetVersion, DatasetDownload
from app.models.activity import Activity
from app.utils.validators import allowed_file, get_file_size, get_file_format
from app.utils.formatters import format_file_size, format_tags
import logging

logger = logging.getLogger(__name__)


class DatasetService:
    """Service for dataset operations"""
    
    def __init__(self, upload_folder: str = 'uploads/datasets'):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)
    
    def upload_dataset(
        self,
        file,
        owner_id: int,
        title: str,
        description: str = '',
        tags: List[str] = None,
        category: str = None,
        industry: str = None,
        license: str = 'MIT',
        is_public: bool = True
    ) -> Tuple[Optional[Dataset], Optional[str]]:
        """Upload a new dataset"""
        try:
            if not file or not file.filename:
                return None, "No file provided"
            
            if not allowed_file(file.filename, 'dataset'):
                return None, f"File type not allowed. Allowed types: CSV, JSON, Excel, Parquet"
            
            from app.utils.validators import secure_filename_custom
            filename = secure_filename_custom(file.filename)
            file_path = self.upload_folder / filename
            
            file.save(str(file_path))
            
            file_size = get_file_size(str(file_path))
            file_format = get_file_format(filename)
            
            dataset = Dataset(
                title=title,
                description=description,
                owner_id=owner_id,
                file_path=str(file_path),
                file_name=filename,
                file_size=file_size,
                file_format=file_format,
                tags=json.dumps(tags) if tags else None,
                category=category,
                industry=industry,
                license=license,
                is_public=is_public
            )
            
            db.session.add(dataset)
            
            activity = Activity(
                user_id=owner_id,
                activity_type='dataset_upload',
                resource_type='dataset',
                resource_id=dataset.id,
                activity_data=json.dumps({'title': title, 'file_name': filename})
            )
            db.session.add(activity)
            
            db.session.commit()
            
            logger.info(f"Dataset uploaded: {dataset.id} by user {owner_id}")
            return dataset, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading dataset: {e}")
            return None, str(e)
    
    def get_dataset(self, dataset_id: int, user_id: Optional[int] = None) -> Optional[Dataset]:
        """Get dataset by ID"""
        dataset = Dataset.query.get(dataset_id)
        
        if not dataset:
            return None
        
        if not dataset.is_public and dataset.owner_id != user_id:
            return None
        
        dataset.view_count += 1
        db.session.commit()
        
        return dataset
    
    def list_datasets(
        self,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        industry: Optional[str] = None,
        search: Optional[str] = None,
        is_public: Optional[bool] = True,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Dataset], int]:
        """List datasets with filters"""
        query = Dataset.query
        
        if is_public is not None:
            if is_public:
                query = query.filter_by(is_public=True)
            elif user_id:
                query = query.filter((Dataset.is_public == True) | (Dataset.owner_id == user_id))
        
        if category:
            query = query.filter_by(category=category)
        
        if industry:
            query = query.filter_by(industry=industry)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Dataset.title.ilike(search_term)) |
                (Dataset.description.ilike(search_term)) |
                (Dataset.tags.ilike(search_term))
            )
        
        query = query.order_by(Dataset.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return pagination.items, pagination.total
    
    def get_dataset_preview(self, dataset_id: int, rows: int = 20) -> Dict:
        """Get dataset preview (first N rows)"""
        dataset = Dataset.query.get(dataset_id)
        if not dataset or not Path(dataset.file_path).exists():
            return {'error': 'Dataset not found'}
        
        try:
            file_path = Path(dataset.file_path)
            
            if dataset.file_format == 'csv':
                df = pd.read_csv(file_path, nrows=rows)
            elif dataset.file_format == 'json':
                df = pd.read_json(file_path)
                if len(df) > rows:
                    df = df.head(rows)
            elif dataset.file_format in ['xlsx', 'xls']:
                df = pd.read_excel(file_path, nrows=rows)
            elif dataset.file_format == 'parquet':
                df = pd.read_parquet(file_path)
                if len(df) > rows:
                    df = df.head(rows)
            else:
                return {'error': 'Unsupported file format for preview'}
            
            return {
                'columns': list(df.columns),
                'rows': df.head(rows).to_dict('records'),
                'shape': df.shape,
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return {'error': str(e)}
    
    def get_dataset_stats(self, dataset_id: int) -> Dict:
        """Get dataset statistics"""
        dataset = Dataset.query.get(dataset_id)
        if not dataset or not Path(dataset.file_path).exists():
            return {'error': 'Dataset not found'}
        
        try:
            file_path = Path(dataset.file_path)
            
            if dataset.file_format == 'csv':
                df = pd.read_csv(file_path)
            elif dataset.file_format == 'json':
                df = pd.read_json(file_path)
            elif dataset.file_format in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            elif dataset.file_format == 'parquet':
                df = pd.read_parquet(file_path)
            else:
                return {'error': 'Unsupported file format'}
            
            stats = {
                'shape': df.shape,
                'columns': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'null_counts': df.isnull().sum().to_dict(),
                'memory_usage': df.memory_usage(deep=True).sum()
            }
            
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                stats['numeric_stats'] = df[numeric_cols].describe().to_dict()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            return {'error': str(e)}
    
    def download_dataset(self, dataset_id: int, user_id: Optional[int] = None) -> Tuple[Optional[Path], Optional[str]]:
        """Track dataset download and return file path"""
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return None, "Dataset not found"
        
        if not dataset.is_public and dataset.owner_id != user_id:
            return None, "Access denied"
        
        file_path = Path(dataset.file_path)
        if not file_path.exists():
            return None, "File not found"
        
        download = DatasetDownload(
            dataset_id=dataset_id,
            user_id=user_id
        )
        db.session.add(download)
        
        dataset.download_count += 1
        db.session.commit()
        
        return file_path, None
    
    def delete_dataset(self, dataset_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """Delete dataset"""
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return False, "Dataset not found"
        
        from app.models.user import User
        user = User.query.get(user_id)
        if dataset.owner_id != user_id and not (user and user.is_admin):
            return False, "Permission denied"
        
        try:
            file_path = Path(dataset.file_path)
            if file_path.exists():
                file_path.unlink()
            
            db.session.delete(dataset)
            db.session.commit()
            
            logger.info(f"Dataset deleted: {dataset_id} by user {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting dataset: {e}")
            return False, str(e)
    
    def upvote_dataset(self, dataset_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """Upvote a dataset"""
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return False, "Dataset not found"
        
        dataset.upvote_count += 1
        db.session.commit()
        
        return True, None
