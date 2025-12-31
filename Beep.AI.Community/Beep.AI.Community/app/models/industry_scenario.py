"""
Industry Scenario Model - Store scenarios (use cases, dataset ideas, competition ideas) per industry
"""
from app import db
from datetime import datetime
from sqlalchemy import Index
import json


class IndustryScenario(db.Model):
    """Model for industry scenarios (use cases, dataset ideas, competition ideas)"""
    __tablename__ = 'industry_scenarios'
    
    id = db.Column(db.Integer, primary_key=True)
    industry = db.Column(db.String(50), nullable=False, index=True)
    scenario_type = db.Column(db.String(20), nullable=False)  # 'use_case', 'dataset_idea', 'competition_idea'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    details = db.Column(db.JSON, nullable=True)  # Additional metadata (JSON field)
    icon_name = db.Column(db.String(255), nullable=True)
    priority = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index for faster queries
    __table_args__ = (
        Index('idx_industry_type', 'industry', 'scenario_type'),
        Index('idx_industry_priority', 'industry', 'priority'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'industry': self.industry,
            'scenario_type': self.scenario_type,
            'title': self.title,
            'description': self.description,
            'details': self.details or {},
            'icon_name': self.icon_name,
            'priority': self.priority,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<IndustryScenario {self.id}: {self.industry} - {self.scenario_type} - {self.title}>'
