"""
Notebook/Project Models
"""
from datetime import datetime
from app import db


class Notebook(db.Model):
    """Notebook/Project model for sharing ML projects"""
    __tablename__ = 'notebooks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    project_id = db.Column(db.Integer)
    language = db.Column(db.String(50), default='python')
    kernel_type = db.Column(db.String(50))
    code_content = db.Column(db.Text)
    output_content = db.Column(db.Text)
    thumbnail_url = db.Column(db.String(500))
    tags = db.Column(db.Text)
    category = db.Column(db.String(100), index=True)
    industry = db.Column(db.String(100), index=True, nullable=True)
    is_public = db.Column(db.Boolean, default=True, index=True)
    fork_count = db.Column(db.Integer, default=0)
    upvote_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    fork_of_id = db.Column(db.Integer, db.ForeignKey('notebooks.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = db.relationship('User', backref='notebooks')
    forks = db.relationship('Notebook', backref=db.backref('original', remote_side=[id]))
    upvotes = db.relationship('NotebookUpvote', backref='notebook', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'owner_id': self.owner_id,
            'owner': self.owner.username if self.owner else None,
            'project_id': self.project_id,
            'language': self.language,
            'kernel_type': self.kernel_type,
            'thumbnail_url': self.thumbnail_url,
            'tags': json.loads(self.tags) if self.tags and self.tags.startswith('[') else (self.tags.split(',') if self.tags else []),
            'category': self.category,
            'industry': self.industry,
            'is_public': self.is_public,
            'fork_count': self.fork_count,
            'upvote_count': self.upvote_count,
            'view_count': self.view_count,
            'comment_count': self.comment_count,
            'fork_of_id': self.fork_of_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Notebook {self.title}>'


class NotebookFork(db.Model):
    """Notebook fork tracking"""
    __tablename__ = 'notebook_forks'
    
    id = db.Column(db.Integer, primary_key=True)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebooks.id'), nullable=False)
    forked_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    forked_to_notebook_id = db.Column(db.Integer, db.ForeignKey('notebooks.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'notebook_id': self.notebook_id,
            'forked_by_id': self.forked_by_id,
            'forked_to_notebook_id': self.forked_to_notebook_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<NotebookFork {self.notebook_id}>'


class NotebookUpvote(db.Model):
    """Notebook upvote tracking"""
    __tablename__ = 'notebook_upvotes'
    
    id = db.Column(db.Integer, primary_key=True)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebooks.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('notebook_id', 'user_id', name='unique_notebook_upvote'),)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'notebook_id': self.notebook_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<NotebookUpvote {self.notebook_id} by {self.user_id}>'
