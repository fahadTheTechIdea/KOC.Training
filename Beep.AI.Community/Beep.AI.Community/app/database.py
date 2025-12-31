"""
Database initialization and utilities
"""
from app import db
from app.models.user import User, UserProfile, APIKey, UserActivity
from app.models.dataset import Dataset, DatasetVersion, DatasetDownload
from app.models.notebook import Notebook, NotebookFork, NotebookUpvote
from app.models.competition import Competition, CompetitionParticipant
from app.models.submission import Submission
from app.models.discussion import Discussion, DiscussionReply, DiscussionUpvote
from app.models.model_registry import ModelRegistry, ModelVersion, ModelDownload
from app.models.activity import Activity


def init_db():
    """Initialize database tables"""
    db.create_all()
    print("Database initialized successfully")


def reset_db():
    """Reset database (drop and recreate all tables)"""
    db.drop_all()
    db.create_all()
    print("Database reset successfully")
