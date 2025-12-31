"""
Competition/Challenge Models
"""
from datetime import datetime
from app import db


class Competition(db.Model):
    """Competition/Challenge model"""
    __tablename__ = 'competitions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=True)
    industry = db.Column(db.String(100), index=True, nullable=True)
    evaluation_metric = db.Column(db.String(100))
    start_date = db.Column(db.DateTime, nullable=False, index=True)
    end_date = db.Column(db.DateTime, nullable=False, index=True)
    max_submissions_per_day = db.Column(db.Integer, default=5)
    max_total_submissions = db.Column(db.Integer, default=100)
    prize_description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    leaderboard_type = db.Column(db.String(50), default='public')
    participant_count = db.Column(db.Integer, default=0)
    submission_count = db.Column(db.Integer, default=0)
    # Competition data files
    training_data_path = db.Column(db.String(500), nullable=True)
    test_data_path = db.Column(db.String(500), nullable=True)
    scoring_script_path = db.Column(db.String(500), nullable=True)
    original_dataset_path = db.Column(db.String(500), nullable=True)
    train_test_split_ratio = db.Column(db.Float, default=0.8)
    # Model requirements
    expected_input_schema = db.Column(db.Text, nullable=True)  # JSON schema
    expected_output_schema = db.Column(db.Text, nullable=True)  # JSON schema
    allowed_model_formats = db.Column(db.String(200), default='pkl,h5,onnx,pt')  # Comma-separated
    # Scoring configuration
    target_column = db.Column(db.String(100), nullable=True)  # Column name containing ground truth labels (legacy, use target_columns)
    # Task configuration
    task_type = db.Column(db.String(50), nullable=True)  # Type of ML task: 'classification', 'regression', 'multilabel_classification', etc.
    target_columns = db.Column(db.Text, nullable=True)  # JSON array of target column names (for multi-output scenarios)
    prediction_format = db.Column(db.String(50), nullable=True)  # Expected prediction format: 'classes', 'probabilities', 'bounding_boxes', etc.
    evaluation_config = db.Column(db.Text, nullable=True)  # JSON configuration for task-specific evaluation parameters
    id_column = db.Column(db.String(100), nullable=True)  # ID column to exclude from features
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organizer = db.relationship('User', backref='organized_competitions')
    dataset = db.relationship('Dataset', backref='competitions')
    participants = db.relationship('CompetitionParticipant', backref='competition', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='competition', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'organizer_id': self.organizer_id,
            'organizer': self.organizer.username if self.organizer else None,
            'dataset_id': self.dataset_id,
            'industry': self.industry,
            'evaluation_metric': self.evaluation_metric,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'max_submissions_per_day': self.max_submissions_per_day,
            'max_total_submissions': self.max_total_submissions,
            'prize_description': self.prize_description,
            'is_active': self.is_active,
            'leaderboard_type': self.leaderboard_type,
            'participant_count': self.participant_count,
            'submission_count': self.submission_count,
            'training_data_path': self.training_data_path,
            'test_data_path': self.test_data_path,
            'scoring_script_path': self.scoring_script_path,
            'original_dataset_path': self.original_dataset_path,
            'train_test_split_ratio': self.train_test_split_ratio,
            'expected_input_schema': self.expected_input_schema,
            'expected_output_schema': self.expected_output_schema,
            'allowed_model_formats': self.allowed_model_formats,
            'target_column': self.target_column,
            'task_type': self.task_type if self.task_type else None,
            'target_columns': self.target_columns if self.target_columns else None,
            'prediction_format': self.prediction_format if self.prediction_format else None,
            'evaluation_config': self.evaluation_config if self.evaluation_config else None,
            'id_column': self.id_column if self.id_column else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Competition {self.title}>'


class CompetitionParticipant(db.Model):
    """Competition participant tracking"""
    __tablename__ = 'competition_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('competition_id', 'user_id', name='unique_participant'),)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'competition_id': self.competition_id,
            'user_id': self.user_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }
    
    def __repr__(self):
        return f'<CompetitionParticipant {self.competition_id} - {self.user_id}>'
