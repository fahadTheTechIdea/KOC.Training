"""
Submission Models
"""
from datetime import datetime
from app import db


class Submission(db.Model):
    """Competition submission model"""
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model_registry.id'), nullable=True)
    submission_file = db.Column(db.String(500))
    score = db.Column(db.Float, index=True)
    rank = db.Column(db.Integer, index=True)
    submission_metadata = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    evaluated_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='submissions')
    model = db.relationship('ModelRegistry', backref='submissions')
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'competition_id': self.competition_id,
            'user_id': self.user_id,
            'user': self.user.username if self.user else None,
            'model_id': self.model_id,
            'score': self.score,
            'rank': self.rank,
            'status': self.status,
            'submission_metadata': json.loads(self.submission_metadata) if self.submission_metadata else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'evaluated_at': self.evaluated_at.isoformat() if self.evaluated_at else None
        }
    
    def __repr__(self):
        return f'<Submission {self.id} - Score: {self.score}>'
