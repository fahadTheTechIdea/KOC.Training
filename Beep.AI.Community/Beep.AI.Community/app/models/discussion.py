"""
Discussion Models
"""
from datetime import datetime
from app import db


class Discussion(db.Model):
    """Discussion/Question model"""
    __tablename__ = 'discussions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    topic_type = db.Column(db.String(50), index=True)
    topic_id = db.Column(db.Integer, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('discussions.id'), nullable=True)
    upvote_count = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_solved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    author = db.relationship('User', backref='discussions')
    parent = db.relationship('Discussion', remote_side=[id], backref='replies')
    upvotes = db.relationship('DiscussionUpvote', backref='discussion', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'author': self.author.username if self.author else None,
            'topic_type': self.topic_type,
            'topic_id': self.topic_id,
            'parent_id': self.parent_id,
            'upvote_count': self.upvote_count,
            'reply_count': self.reply_count,
            'is_pinned': self.is_pinned,
            'is_solved': self.is_solved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Discussion {self.title}>'


class DiscussionReply(db.Model):
    """Discussion reply model"""
    __tablename__ = 'discussion_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussions.id'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    discussion = db.relationship('Discussion', backref='discussion_replies')
    author = db.relationship('User', backref='discussion_replies')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'discussion_id': self.discussion_id,
            'author_id': self.author_id,
            'author': self.author.username if self.author else None,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<DiscussionReply {self.id}>'


class DiscussionUpvote(db.Model):
    """Discussion upvote tracking"""
    __tablename__ = 'discussion_upvotes'
    
    id = db.Column(db.Integer, primary_key=True)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussions.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('discussion_id', 'user_id', name='unique_discussion_upvote'),)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'discussion_id': self.discussion_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<DiscussionUpvote {self.discussion_id} by {self.user_id}>'
