"""
Database Models
"""
from app.models.user import User, UserProfile, APIKey, UserActivity
from app.models.dataset import Dataset, DatasetVersion, DatasetDownload
from app.models.notebook import Notebook, NotebookFork, NotebookUpvote
from app.models.competition import Competition, CompetitionParticipant
from app.models.submission import Submission
from app.models.discussion import Discussion, DiscussionReply, DiscussionUpvote
from app.models.model_registry import ModelRegistry, ModelVersion, ModelDownload
from app.models.activity import Activity
from app.models.industry_scenario import IndustryScenario

__all__ = [
    'User', 'UserProfile', 'APIKey', 'UserActivity',
    'Dataset', 'DatasetVersion', 'DatasetDownload',
    'Notebook', 'NotebookFork', 'NotebookUpvote',
    'Competition', 'CompetitionParticipant',
    'Submission',
    'Discussion', 'DiscussionReply', 'DiscussionUpvote',
    'ModelRegistry', 'ModelVersion', 'ModelDownload',
    'Activity',
    'IndustryScenario'
]
