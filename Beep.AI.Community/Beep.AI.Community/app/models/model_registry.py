"""
Model Registry Models
"""
from datetime import datetime
from app import db


class ModelRegistry(db.Model):
    """Model registry for sharing ML models"""
    __tablename__ = 'model_registry'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    model_type = db.Column(db.String(100))
    framework = db.Column(db.String(50))
    model_file_path = db.Column(db.String(500), nullable=False)
    metrics = db.Column(db.Text)
    input_schema = db.Column(db.Text)
    output_schema = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True, index=True)
    download_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = db.relationship('User', backref='models')
    versions = db.relationship('ModelVersion', backref='model', lazy=True, cascade='all, delete-orphan')
    downloads = db.relationship('ModelDownload', backref='model', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'owner': self.owner.username if self.owner else None,
            'model_type': self.model_type,
            'framework': self.framework,
            'metrics': json.loads(self.metrics) if self.metrics else None,
            'input_schema': json.loads(self.input_schema) if self.input_schema else None,
            'output_schema': json.loads(self.output_schema) if self.output_schema else None,
            'is_public': self.is_public,
            'download_count': self.download_count,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ModelRegistry {self.name}>'


class ModelVersion(db.Model):
    """Model version history"""
    __tablename__ = 'model_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model_registry.id'), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    model_file_path = db.Column(db.String(500), nullable=False)
    metrics = db.Column(db.Text)
    change_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'model_id': self.model_id,
            'version': self.version,
            'metrics': json.loads(self.metrics) if self.metrics else None,
            'change_description': self.change_description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ModelVersion {self.model_id} v{self.version}>'


class ModelDownload(db.Model):
    """Model download tracking"""
    __tablename__ = 'model_downloads'
    
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model_registry.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'user_id': self.user_id,
            'downloaded_at': self.downloaded_at.isoformat() if self.downloaded_at else None
        }
    
    def __repr__(self):
        return f'<ModelDownload {self.model_id}>'
