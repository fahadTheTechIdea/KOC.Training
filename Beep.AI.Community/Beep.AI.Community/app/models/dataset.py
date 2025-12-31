"""
Dataset Models
"""
from datetime import datetime
from app import db


class Dataset(db.Model):
    """Dataset model for data sharing"""
    __tablename__ = 'datasets'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger)
    file_format = db.Column(db.String(50))
    version = db.Column(db.Integer, default=1)
    tags = db.Column(db.Text)
    category = db.Column(db.String(100), index=True)
    industry = db.Column(db.String(100), index=True, nullable=True)
    license = db.Column(db.String(100))
    is_public = db.Column(db.Boolean, default=True, index=True)
    download_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)
    upvote_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = db.relationship('User', backref='datasets')
    versions = db.relationship('DatasetVersion', backref='dataset', lazy=True, cascade='all, delete-orphan')
    downloads = db.relationship('DatasetDownload', backref='dataset', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'owner_id': self.owner_id,
            'owner': self.owner.username if self.owner else None,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'version': self.version,
            'tags': json.loads(self.tags) if self.tags and self.tags.startswith('[') else (self.tags.split(',') if self.tags else []),
            'category': self.category,
            'industry': self.industry,
            'license': self.license,
            'is_public': self.is_public,
            'download_count': self.download_count,
            'view_count': self.view_count,
            'rating': self.rating,
            'upvote_count': self.upvote_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Dataset {self.title}>'


class DatasetVersion(db.Model):
    """Dataset version history"""
    __tablename__ = 'dataset_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    change_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'version': self.version,
            'file_size': self.file_size,
            'change_description': self.change_description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<DatasetVersion {self.dataset_id} v{self.version}>'


class DatasetDownload(db.Model):
    """Dataset download tracking"""
    __tablename__ = 'dataset_downloads'
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'user_id': self.user_id,
            'downloaded_at': self.downloaded_at.isoformat() if self.downloaded_at else None
        }
    
    def __repr__(self):
        return f'<DatasetDownload {self.dataset_id}>'
