"""
Discussion Service - Community discussions and Q&A
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import or_, desc, func
from app import db
from app.models.discussion import Discussion, DiscussionUpvote
from app.models.activity import Activity
import logging

logger = logging.getLogger(__name__)


class DiscussionService:
    """Service for discussion operations"""
    
    # ==================== Discussion Management ====================
    
    def create_discussion(
        self,
        author_id: int,
        title: str,
        content: str,
        topic_type: Optional[str] = None,
        topic_id: Optional[int] = None
    ) -> Tuple[Optional[Discussion], Optional[str]]:
        """
        Create a new discussion/question
        
        Args:
            author_id: Author user ID
            title: Discussion title
            content: Discussion content
            topic_type: Type of topic (e.g., 'competition', 'dataset', 'project')
            topic_id: ID of the related topic
            
        Returns:
            Tuple of (discussion_object, error_message)
        """
        try:
            discussion = Discussion(
                title=title,
                content=content,
                author_id=author_id,
                topic_type=topic_type,
                topic_id=topic_id
            )
            
            db.session.add(discussion)
            db.session.commit()
            
            # Record activity
            self._record_activity(author_id, 'discussion_created', discussion.id)
            
            logger.info(f"Discussion created: {title} by user {author_id}")
            return discussion, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating discussion: {e}")
            return None, str(e)
    
    def update_discussion(
        self,
        discussion_id: int,
        author_id: int,
        updates: Dict
    ) -> Tuple[Optional[Discussion], Optional[str]]:
        """
        Update discussion
        
        Args:
            discussion_id: Discussion ID
            author_id: Author user ID (for authorization)
            updates: Dictionary of fields to update
            
        Returns:
            Tuple of (updated_discussion, error_message)
        """
        try:
            discussion = Discussion.query.get(discussion_id)
            if not discussion:
                return None, "Discussion not found"
            
            if discussion.author_id != author_id:
                return None, "Not authorized to update this discussion"
            
            # Update allowed fields
            allowed_fields = ['title', 'content']
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(discussion, field, value)
            
            discussion.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Discussion updated: {discussion_id}")
            return discussion, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating discussion: {e}")
            return None, str(e)
    
    def delete_discussion(
        self,
        discussion_id: int,
        author_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete discussion
        
        Args:
            discussion_id: Discussion ID
            author_id: Author user ID (for authorization)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            discussion = Discussion.query.get(discussion_id)
            if not discussion:
                return False, "Discussion not found"
            
            # Check authorization (author or admin)
            from app.models.user import User
            user = User.query.get(author_id)
            if discussion.author_id != author_id and (not user or not user.is_admin):
                return False, "Not authorized to delete this discussion"
            
            db.session.delete(discussion)
            db.session.commit()
            
            logger.info(f"Discussion deleted: {discussion_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting discussion: {e}")
            return False, str(e)
    
    def get_discussion(
        self,
        discussion_id: int
    ) -> Optional[Discussion]:
        """
        Get discussion with replies
        
        Args:
            discussion_id: Discussion ID
            
        Returns:
            Discussion object or None
        """
        return Discussion.query.get(discussion_id)
    
    def list_discussions(
        self,
        topic_type: Optional[str] = None,
        topic_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[Discussion], int]:
        """
        List discussions with filtering
        
        Args:
            topic_type: Filter by topic type
            topic_id: Filter by topic ID
            page: Page number
            per_page: Items per page
            search: Search term
            
        Returns:
            Tuple of (discussions_list, total_count)
        """
        query = Discussion.query.filter(Discussion.parent_id.is_(None))  # Only top-level discussions
        
        if topic_type:
            query = query.filter(Discussion.topic_type == topic_type)
        
        if topic_id:
            query = query.filter(Discussion.topic_id == topic_id)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Discussion.title.ilike(search_term),
                    Discussion.content.ilike(search_term)
                )
            )
        
        # Order by pinned first, then by upvotes, then by creation date
        query = query.order_by(
            desc(Discussion.is_pinned),
            desc(Discussion.upvote_count),
            desc(Discussion.created_at)
        )
        
        total = query.count()
        discussions = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        ).items
        
        return discussions, total
    
    # ==================== Replies ====================
    
    def reply_to_discussion(
        self,
        discussion_id: int,
        author_id: int,
        content: str
    ) -> Tuple[Optional[Discussion], Optional[str]]:
        """
        Add reply to discussion
        
        Args:
            discussion_id: Parent discussion ID
            author_id: Reply author ID
            content: Reply content
            
        Returns:
            Tuple of (reply_object, error_message)
        """
        try:
            parent = Discussion.query.get(discussion_id)
            if not parent:
                return None, "Discussion not found"
            
            reply = Discussion(
                title=f"Re: {parent.title}",
                content=content,
                author_id=author_id,
                parent_id=discussion_id,
                topic_type=parent.topic_type,
                topic_id=parent.topic_id
            )
            
            db.session.add(reply)
            
            # Update reply count
            parent.reply_count = Discussion.query.filter_by(parent_id=discussion_id).count() + 1
            
            db.session.commit()
            
            # Record activity
            self._record_activity(author_id, 'discussion_reply', parent.id, reply.id)
            
            logger.info(f"Reply added to discussion {discussion_id} by user {author_id}")
            return reply, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding reply: {e}")
            return None, str(e)
    
    def mark_as_solved(
        self,
        discussion_id: int,
        author_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Mark discussion as solved
        
        Args:
            discussion_id: Discussion ID
            author_id: User ID (must be author)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            discussion = Discussion.query.get(discussion_id)
            if not discussion:
                return False, "Discussion not found"
            
            if discussion.author_id != author_id:
                return False, "Only the author can mark as solved"
            
            discussion.is_solved = True
            db.session.commit()
            
            logger.info(f"Discussion {discussion_id} marked as solved")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking as solved: {e}")
            return False, str(e)
    
    def pin_discussion(
        self,
        discussion_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Pin discussion (moderator/admin only)
        
        Args:
            discussion_id: Discussion ID
            user_id: User ID (must be admin/moderator)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            from app.models.user import User
            user = User.query.get(user_id)
            if not user or not user.is_admin:
                return False, "Only administrators can pin discussions"
            
            discussion = Discussion.query.get(discussion_id)
            if not discussion:
                return False, "Discussion not found"
            
            discussion.is_pinned = True
            db.session.commit()
            
            logger.info(f"Discussion {discussion_id} pinned by user {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error pinning discussion: {e}")
            return False, str(e)
    
    def unpin_discussion(
        self,
        discussion_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Unpin discussion (moderator/admin only)"""
        try:
            from app.models.user import User
            user = User.query.get(user_id)
            if not user or not user.is_admin:
                return False, "Only administrators can unpin discussions"
            
            discussion = Discussion.query.get(discussion_id)
            if not discussion:
                return False, "Discussion not found"
            
            discussion.is_pinned = False
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    # ==================== Upvotes ====================
    
    def upvote_discussion(
        self,
        discussion_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Upvote discussion
        
        Args:
            discussion_id: Discussion ID
            user_id: User ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            discussion = Discussion.query.get(discussion_id)
            if not discussion:
                return False, "Discussion not found"
            
            # Check if already upvoted
            existing = DiscussionUpvote.query.filter_by(
                discussion_id=discussion_id,
                user_id=user_id
            ).first()
            
            if existing:
                return False, "Already upvoted"
            
            upvote = DiscussionUpvote(
                discussion_id=discussion_id,
                user_id=user_id
            )
            
            db.session.add(upvote)
            
            # Update upvote count
            discussion.upvote_count += 1
            
            db.session.commit()
            
            logger.info(f"Discussion {discussion_id} upvoted by user {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error upvoting discussion: {e}")
            return False, str(e)
    
    def remove_upvote(
        self,
        discussion_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Remove upvote from discussion
        
        Args:
            discussion_id: Discussion ID
            user_id: User ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            upvote = DiscussionUpvote.query.filter_by(
                discussion_id=discussion_id,
                user_id=user_id
            ).first()
            
            if not upvote:
                return False, "Upvote not found"
            
            db.session.delete(upvote)
            
            # Update upvote count
            discussion = Discussion.query.get(discussion_id)
            if discussion:
                discussion.upvote_count = max(0, discussion.upvote_count - 1)
            
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing upvote: {e}")
            return False, str(e)
    
    def has_upvoted(
        self,
        discussion_id: int,
        user_id: int
    ) -> bool:
        """Check if user has upvoted discussion"""
        upvote = DiscussionUpvote.query.filter_by(
            discussion_id=discussion_id,
            user_id=user_id
        ).first()
        return upvote is not None
    
    # ==================== Search ====================
    
    def search_discussions(
        self,
        query: str,
        topic_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Discussion], int]:
        """
        Search discussions
        
        Args:
            query: Search query
            topic_type: Optional topic type filter
            page: Page number
            per_page: Items per page
            
        Returns:
            Tuple of (discussions_list, total_count)
        """
        return self.list_discussions(
            topic_type=topic_type,
            page=page,
            per_page=per_page,
            search=query
        )
    
    # ==================== Helper Methods ====================
    
    def _record_activity(
        self,
        user_id: int,
        activity_type: str,
        resource_id: int,
        related_id: Optional[int] = None
    ):
        """Record user activity"""
        try:
            import json
            activity_data = {}
            if related_id:
                activity_data['related_id'] = related_id
            
            activity = Activity(
                user_id=user_id,
                activity_type=activity_type,
                resource_type='discussion',
                resource_id=resource_id,
                activity_data=json.dumps(activity_data) if activity_data else None
            )
            db.session.add(activity)
            db.session.commit()
        except Exception as e:
            logger.warning(f"Failed to record activity: {e}")
