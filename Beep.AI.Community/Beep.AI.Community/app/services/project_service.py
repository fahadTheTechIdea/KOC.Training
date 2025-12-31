"""
Project/Notebook Service - Project sharing from MLStudio
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app import db
from app.models.notebook import Notebook, NotebookFork, NotebookUpvote
from app.models.activity import Activity
import logging

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project/notebook operations"""
    
    def __init__(self):
        pass
    
    def publish_project(
        self,
        owner_id: int,
        title: str,
        description: str = '',
        project_id: Optional[int] = None,
        code_content: str = '',
        output_content: str = '',
        language: str = 'python',
        kernel_type: str = 'notebook',
        tags: List[str] = None,
        category: str = None,
        industry: str = None,
        thumbnail_url: Optional[str] = None,
        is_public: bool = True
    ) -> Tuple[Optional[Notebook], Optional[str]]:
        """Publish a project from MLStudio"""
        try:
            notebook = Notebook(
                title=title,
                description=description,
                owner_id=owner_id,
                project_id=project_id,
                code_content=code_content,
                output_content=output_content,
                language=language,
                kernel_type=kernel_type,
                tags=json.dumps(tags) if tags else None,
                category=category,
                industry=industry,
                thumbnail_url=thumbnail_url,
                is_public=is_public
            )
            
            db.session.add(notebook)
            
            activity = Activity(
                user_id=owner_id,
                activity_type='project_publish',
                resource_type='notebook',
                resource_id=notebook.id,
                activity_data=json.dumps({'title': title, 'project_id': project_id})
            )
            db.session.add(activity)
            
            db.session.commit()
            
            logger.info(f"Project published: {notebook.id} by user {owner_id}")
            return notebook, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error publishing project: {e}")
            return None, str(e)
    
    def get_project(self, notebook_id: int, user_id: Optional[int] = None) -> Optional[Notebook]:
        """Get project by ID"""
        notebook = Notebook.query.get(notebook_id)
        
        if not notebook:
            return None
        
        if not notebook.is_public and notebook.owner_id != user_id:
            return None
        
        notebook.view_count += 1
        db.session.commit()
        
        return notebook
    
    def list_projects(
        self,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        industry: Optional[str] = None,
        search: Optional[str] = None,
        language: Optional[str] = None,
        is_public: Optional[bool] = True,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Notebook], int]:
        """List projects with filters"""
        query = Notebook.query
        
        if is_public is not None:
            if is_public:
                query = query.filter_by(is_public=True)
            elif user_id:
                query = query.filter((Notebook.is_public == True) | (Notebook.owner_id == user_id))
        
        if category:
            query = query.filter_by(category=category)
        
        if industry:
            query = query.filter_by(industry=industry)
        
        if language:
            query = query.filter_by(language=language)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Notebook.title.ilike(search_term)) |
                (Notebook.description.ilike(search_term)) |
                (Notebook.tags.ilike(search_term))
            )
        
        query = query.order_by(Notebook.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return pagination.items, pagination.total
    
    def fork_project(self, notebook_id: int, user_id: int) -> Tuple[Optional[Notebook], Optional[str]]:
        """Fork a project"""
        original = Notebook.query.get(notebook_id)
        if not original:
            return None, "Project not found"
        
        if not original.is_public:
            return None, "Cannot fork private project"
        
        try:
            fork = Notebook(
                title=f"{original.title} (Fork)",
                description=original.description,
                owner_id=user_id,
                project_id=original.project_id,
                code_content=original.code_content,
                output_content=original.output_content,
                language=original.language,
                kernel_type=original.kernel_type,
                tags=original.tags,
                category=original.category,
                industry=original.industry,
                thumbnail_url=original.thumbnail_url,
                is_public=True,
                fork_of_id=notebook_id
            )
            
            db.session.add(fork)
            original.fork_count += 1
            
            fork_record = NotebookFork(
                notebook_id=notebook_id,
                forked_by_id=user_id,
                forked_to_notebook_id=fork.id
            )
            db.session.add(fork_record)
            
            activity = Activity(
                user_id=user_id,
                activity_type='project_fork',
                resource_type='notebook',
                resource_id=notebook_id,
                activity_data=json.dumps({'forked_to': fork.id, 'original_title': original.title})
            )
            db.session.add(activity)
            
            db.session.commit()
            
            logger.info(f"Project forked: {notebook_id} -> {fork.id} by user {user_id}")
            return fork, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error forking project: {e}")
            return None, str(e)
    
    def upvote_project(self, notebook_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """Upvote a project"""
        notebook = Notebook.query.get(notebook_id)
        if not notebook:
            return False, "Project not found"
        
        existing = NotebookUpvote.query.filter_by(
            notebook_id=notebook_id,
            user_id=user_id
        ).first()
        
        if existing:
            return False, "Already upvoted"
        
        try:
            upvote = NotebookUpvote(
                notebook_id=notebook_id,
                user_id=user_id
            )
            db.session.add(upvote)
            
            notebook.upvote_count += 1
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    def delete_project(self, notebook_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """Delete project"""
        notebook = Notebook.query.get(notebook_id)
        if not notebook:
            return False, "Project not found"
        
        from app.models.user import User
        user = User.query.get(user_id)
        if notebook.owner_id != user_id and not (user and user.is_admin):
            return False, "Permission denied"
        
        try:
            db.session.delete(notebook)
            db.session.commit()
            
            logger.info(f"Project deleted: {notebook_id} by user {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting project: {e}")
            return False, str(e)
    
    def export_to_notebook_format(self, notebook_id: int) -> Dict:
        """Export project to Jupyter notebook format"""
        notebook = Notebook.query.get(notebook_id)
        if not notebook:
            return {'error': 'Project not found'}
        
        notebook_json = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [f"# {notebook.title}\n\n{notebook.description}"]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": notebook.language,
                    "name": f"python3"
                },
                "language_info": {
                    "name": notebook.language,
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        if notebook.code_content:
            try:
                code_lines = notebook.code_content.split('\n')
                notebook_json["cells"].append({
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": code_lines,
                    "outputs": []
                })
            except:
                pass
        
        return notebook_json
