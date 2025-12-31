"""
Competition Service - Competition/Challenge management
"""
import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, or_, desc, func
from sqlalchemy import and_, or_, desc, func
from werkzeug.utils import secure_filename
from app import db
from app.models.competition import Competition, CompetitionParticipant
from app.models.submission import Submission
from app.models.activity import Activity
from app.models.dataset import Dataset
from app.services.dataset_service import DatasetService
from app.services.dataset_split_service import DatasetSplitService
from app.services.scoring_service import ScoringService
from app.services.model_validator import ModelValidator
import logging

logger = logging.getLogger(__name__)


class CompetitionService:
    """Service for competition operations"""
    
    def __init__(self, upload_folder: str = 'uploads/submissions'):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.dataset_service = DatasetService()
        self.dataset_split_service = DatasetSplitService()
        self.scoring_service = ScoringService()
        self.model_validator = ModelValidator()
        
        # Competition data directory
        self.competition_data_dir = Path('uploads/competitions')
        self.competition_data_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== Competition Management ====================
    
    def create_competition(
        self,
        organizer_id: int,
        title: str,
        description: str,
        dataset_id: Optional[int] = None,
        industry: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        evaluation_metric: str = None,
        max_submissions_per_day: int = 5,
        max_total_submissions: int = 100,
        prize_description: str = None,
        leaderboard_type: str = 'public',
        task_type: str = None,
        target_columns: list = None,
        target_column: str = None,  # Legacy support
        prediction_format: str = None,
        evaluation_config: dict = None
    ) -> Tuple[Optional[Competition], Optional[str]]:
        """
        Create a new competition
        
        Args:
            organizer_id: ID of the user organizing the competition
            title: Competition title
            description: Competition description
            dataset_id: Optional dataset ID
            start_date: Competition start date
            end_date: Competition end date
            evaluation_metric: Evaluation metric name
            max_submissions_per_day: Maximum submissions per day per user
            max_total_submissions: Maximum total submissions per user
            prize_description: Prize description
            leaderboard_type: Leaderboard visibility (public/private)
            task_type: Type of ML task ('classification', 'regression', etc.)
            target_columns: List of target column names (for multi-output scenarios)
            target_column: Single target column (legacy, use target_columns)
            prediction_format: Expected prediction format
            evaluation_config: Task-specific evaluation configuration (dict)
            
        Returns:
            Tuple of (competition_object, error_message)
        """
        try:
            # Validate dates
            if start_date and end_date and start_date >= end_date:
                return None, "End date must be after start date"
            
            # Validate dataset if provided
            if dataset_id:
                dataset = Dataset.query.get(dataset_id)
                if not dataset:
                    return None, "Dataset not found"
            
            # Process target columns (support legacy target_column)
            target_columns_list = target_columns
            if not target_columns_list and target_column:
                target_columns_list = [target_column]
            
            # Set default task_type if not provided (infer from metric)
            if not task_type:
                if evaluation_metric and evaluation_metric.lower() in {'rmse', 'mae', 'mape', 'mse', 'r2', 'r2_score', 'r_squared'}:
                    task_type = 'regression'
                else:
                    task_type = 'classification'
            
            # Validate task configuration if provided
            if task_type and target_columns_list:
                valid_task_types = {
                    'classification', 'regression', 'multilabel_classification', 'multioutput_regression',
                    'time_series', 'object_detection', 'segmentation', 'text_classification', 'ner',
                    'ranking', 'recommendation'
                }
                if task_type not in valid_task_types:
                    return None, f"Invalid task_type. Must be one of: {', '.join(valid_task_types)}"
                
                # Validate target_columns count matches task_type
                if task_type in {'classification', 'regression', 'time_series', 'text_classification', 'ner'}:
                    if len(target_columns_list) > 1:
                        return None, f"Task type '{task_type}' requires a single target column"
                elif task_type in {'multilabel_classification', 'multioutput_regression'}:
                    if len(target_columns_list) < 2:
                        return None, f"Task type '{task_type}' requires multiple target columns"
            
            # Auto-set evaluation_metric based on task_type if not provided
            # This is optional - scoring service can auto-determine, but storing it is useful
            if not evaluation_metric and task_type:
                from app.services.scoring_service import ScoringService
                scoring_service = ScoringService()
                evaluation_metric = scoring_service._get_default_metric_for_task_type(task_type)
            
            # Process evaluation_config
            eval_config_json = None
            if evaluation_config:
                try:
                    eval_config_json = json.dumps(evaluation_config)
                except (TypeError, ValueError) as e:
                    return None, f"Invalid evaluation_config: {str(e)}"
            
            competition = Competition(
                title=title,
                description=description,
                organizer_id=organizer_id,
                dataset_id=dataset_id,
                industry=industry,
                start_date=start_date or datetime.utcnow(),
                end_date=end_date,
                evaluation_metric=evaluation_metric,
                max_submissions_per_day=max_submissions_per_day,
                max_total_submissions=max_total_submissions,
                prize_description=prize_description,
                leaderboard_type=leaderboard_type,
                is_active=True,
                task_type=task_type,
                target_columns=json.dumps(target_columns_list) if target_columns_list else None,
                target_column=target_columns_list[0] if target_columns_list else target_column,  # Legacy support
                prediction_format=prediction_format,
                evaluation_config=eval_config_json
            )
            
            db.session.add(competition)
            db.session.commit()
            
            # Record activity
            self._record_activity(organizer_id, 'competition_created', competition.id)
            
            logger.info(f"Competition created: {title} by user {organizer_id}")
            return competition, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating competition: {e}")
            return None, str(e)
    
    def update_competition(
        self,
        competition_id: int,
        organizer_id: int,
        updates: Dict
    ) -> Tuple[Optional[Competition], Optional[str]]:
        """
        Update competition details
        
        Args:
            competition_id: Competition ID
            organizer_id: ID of the organizer (for authorization)
            updates: Dictionary of fields to update
            
        Returns:
            Tuple of (updated_competition, error_message)
        """
        try:
            competition = Competition.query.get(competition_id)
            if not competition:
                return None, "Competition not found"
            
            # Allow admin users to update any competition
            from app.models.user import User
            organizer = User.query.get(organizer_id)
            if competition.organizer_id != organizer_id and not (organizer and organizer.is_admin_role()):
                return None, "Not authorized to update this competition"
            
            # Update allowed fields
            allowed_fields = [
                'title', 'description', 'dataset_id', 'start_date', 'end_date',
                'evaluation_metric', 'max_submissions_per_day', 'max_total_submissions',
                'prize_description', 'leaderboard_type', 'is_active'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(competition, field, value)
            
            competition.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Competition updated: {competition_id}")
            return competition, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating competition: {e}")
            return None, str(e)
    
    def delete_competition(
        self,
        competition_id: int,
        organizer_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a competition
        
        Args:
            competition_id: Competition ID
            organizer_id: ID of the organizer (for authorization)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            competition = Competition.query.get(competition_id)
            if not competition:
                return False, "Competition not found"
            
            # Allow admin users to delete any competition
            from app.models.user import User
            organizer = User.query.get(organizer_id)
            if competition.organizer_id != organizer_id and not (organizer and organizer.is_admin_role()):
                return False, "Not authorized to delete this competition"
            
            db.session.delete(competition)
            db.session.commit()
            
            logger.info(f"Competition deleted: {competition_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting competition: {e}")
            return False, str(e)
    
    def get_competition(
        self,
        competition_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Competition]:
        """
        Get competition details
        
        Args:
            competition_id: Competition ID
            user_id: Optional user ID to include participation status
            
        Returns:
            Competition object or None
        """
        competition = Competition.query.get(competition_id)
        if competition and user_id:
            # Add participation status (can be accessed via relationship)
            competition.is_participant = self.is_participant(competition_id, user_id)
        return competition
    
    def list_competitions(
        self,
        user_id: Optional[int] = None,
        industry: Optional[str] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[Competition], int]:
        """
        List competitions with filtering and pagination
        
        Args:
            user_id: Optional user ID to filter by participation
            industry: Filter by industry
            is_active: Filter by active status
            page: Page number
            per_page: Items per page
            search: Search term for title/description
            
        Returns:
            Tuple of (competitions_list, total_count)
        """
        query = Competition.query
        
        if is_active is not None:
            query = query.filter(Competition.is_active == is_active)
        
        if industry:
            query = query.filter(Competition.industry == industry)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Competition.title.ilike(search_term),
                    Competition.description.ilike(search_term)
                )
            )
        
        # Order by creation date (newest first)
        query = query.order_by(desc(Competition.created_at))
        
        total = query.count()
        competitions = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        ).items
        
        # Add participation status if user_id provided
        if user_id:
            for competition in competitions:
                competition.is_participant = self.is_participant(competition.id, user_id)
        
        return competitions, total
    
    # ==================== Participation ====================
    
    def join_competition(
        self,
        competition_id: int,
        user_id: int
    ) -> Tuple[Optional[CompetitionParticipant], Optional[str]]:
        """
        Join a competition
        
        Args:
            competition_id: Competition ID
            user_id: User ID
            
        Returns:
            Tuple of (participant_object, error_message)
        """
        try:
            competition = Competition.query.get(competition_id)
            if not competition:
                return None, "Competition not found"
            
            if not competition.is_active:
                return None, "Competition is not active"
            
            # Check if already a participant
            existing = CompetitionParticipant.query.filter_by(
                competition_id=competition_id,
                user_id=user_id
            ).first()
            
            if existing:
                return existing, None  # Already joined
            
            participant = CompetitionParticipant(
                competition_id=competition_id,
                user_id=user_id
            )
            
            db.session.add(participant)
            db.session.flush()  # Flush to get the participant ID
            
            # Update participant count
            competition.participant_count = CompetitionParticipant.query.filter_by(
                competition_id=competition_id
            ).count()
            
            db.session.commit()
            
            # Record activity
            self._record_activity(user_id, 'competition_joined', competition_id)
            
            logger.info(f"User {user_id} joined competition {competition_id}")
            return participant, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error joining competition: {e}")
            return None, str(e)
    
    def leave_competition(
        self,
        competition_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Leave a competition
        
        Args:
            competition_id: Competition ID
            user_id: User ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            participant = CompetitionParticipant.query.filter_by(
                competition_id=competition_id,
                user_id=user_id
            ).first()
            
            if not participant:
                return False, "Not a participant in this competition"
            
            db.session.delete(participant)
            
            # Update participant count
            competition = Competition.query.get(competition_id)
            if competition:
                competition.participant_count = CompetitionParticipant.query.filter_by(
                    competition_id=competition_id
                ).count()
            
            db.session.commit()
            
            logger.info(f"User {user_id} left competition {competition_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error leaving competition: {e}")
            return False, str(e)
    
    def is_participant(
        self,
        competition_id: int,
        user_id: int
    ) -> bool:
        """
        Check if user is a participant
        
        Args:
            competition_id: Competition ID
            user_id: User ID
            
        Returns:
            True if participant, False otherwise
        """
        participant = CompetitionParticipant.query.filter_by(
            competition_id=competition_id,
            user_id=user_id
        ).first()
        return participant is not None
    
    def get_user_submissions(
        self,
        user_id: int,
        competition_id: Optional[int] = None
    ) -> List[Submission]:
        """
        Get user's submissions (optionally filtered by competition)
        
        Args:
            user_id: User ID
            competition_id: Optional competition ID to filter by
            
        Returns:
            List of submission objects
        """
        query = Submission.query.filter_by(user_id=user_id)
        
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        submissions = query.order_by(desc(Submission.submitted_at)).all()
        
        return submissions
    
    # ==================== Submissions ====================
    
    def submit_to_competition(
        self,
        competition_id: int,
        user_id: int,
        submission_file=None,
        model_id: Optional[int] = None
    ) -> Tuple[Optional[Submission], Optional[str]]:
        """
        Submit entry to competition
        
        Args:
            competition_id: Competition ID
            user_id: User ID
            submission_file: File object to upload
            model_id: Optional model ID reference
            
        Returns:
            Tuple of (submission_object, error_message)
        """
        try:
            competition = Competition.query.get(competition_id)
            if not competition:
                return None, "Competition not found"
            
            if not competition.is_active:
                return None, "Competition is not active"
            
            # Check if user is a participant
            if not self.is_participant(competition_id, user_id):
                return None, "You must join the competition before submitting"
            
            # Validate submission limits
            validation_error = self.validate_submission(competition_id, user_id)
            if validation_error:
                return None, validation_error
            
            # Determine submission file path
            submission_file_path = None
            
            if model_id:
                # Use model from ModelRegistry
                from app.models.model_registry import ModelRegistry
                model = ModelRegistry.query.get(model_id)
                if not model:
                    return None, "Model not found"
                if model.owner_id != user_id:
                    return None, "You do not have permission to use this model"
                submission_file_path = model.model_file_path
            elif submission_file:
                # Save uploaded file
                filename = secure_filename(submission_file.filename)
                file_path = self.upload_folder / f"{competition_id}_{user_id}_{filename}"
                submission_file.save(str(file_path))
                submission_file_path = str(file_path)
            else:
                return None, "Either submission_file or model_id must be provided"
            
            # Model validation is optional/disabled - skip validation step
            # Just ensure file exists (already checked above)
            
            # Create submission record
            submission = Submission(
                competition_id=competition_id,
                user_id=user_id,
                model_id=model_id,
                submission_file=submission_file_path,
                status='pending'
            )
            
            db.session.add(submission)
            db.session.flush()  # Flush to get the submission ID
            
            # Update submission count
            competition.submission_count = Submission.query.filter_by(
                competition_id=competition_id
            ).count()
            
            db.session.commit()
            
            # Trigger automatic evaluation if competition has scoring script
            if competition.scoring_script_path and competition.test_data_path:
                try:
                    from app.services.submission_evaluator import SubmissionEvaluator
                    evaluator = SubmissionEvaluator()
                    # Run evaluation asynchronously (could use background task in production)
                    eval_success, eval_error = evaluator.evaluate_submission(submission.id, competition_id)
                    if not eval_success:
                        logger.warning(f"Auto-evaluation failed for submission {submission.id}: {eval_error}")
                except Exception as e:
                    logger.error(f"Error triggering auto-evaluation: {e}", exc_info=True)
                    # Don't fail submission if evaluation fails to start
            
            # Record activity
            self._record_activity(user_id, 'submission_created', competition_id, submission.id)
            
            logger.info(f"Submission created: {submission.id} for competition {competition_id}")
            return submission, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting to competition: {e}")
            return None, str(e)
    
    def submit_model_to_competition(
        self,
        competition_id: int,
        user_id: int,
        model_name: str,
        model_file_data: Optional[str] = None,
        model_file_path: Optional[str] = None,
        model_type: Optional[str] = None,
        framework: Optional[str] = None,
        metrics: Optional[Dict] = None,
        description: Optional[str] = None,
        input_schema: Optional[Dict] = None,
        output_schema: Optional[Dict] = None,
        mlstudio_source_id: Optional[str] = None
    ) -> Tuple[Optional[Submission], Optional[str]]:
        """
        Submit a model from MLStudio to competition
        
        Args:
            competition_id: Competition ID
            user_id: User ID
            model_name: Name of the model
            model_file_data: Base64 encoded model file data
            model_file_path: Path to model file (if already exists)
            model_type: Type of model
            framework: Framework used
            metrics: Model metrics dictionary
            description: Model description
            input_schema: Input schema dictionary
            output_schema: Output schema dictionary
            mlstudio_source_id: Original MLStudio model ID
            
        Returns:
            Tuple of (submission_object, error_message)
        """
        try:
            competition = Competition.query.get(competition_id)
            if not competition:
                return None, "Competition not found"
            
            if not competition.is_active:
                return None, "Competition is not active"
            
            # Check if user is a participant
            if not self.is_participant(competition_id, user_id):
                return None, "You must join the competition before submitting"
            
            # Validate submission limits
            validation_error = self.validate_submission(competition_id, user_id)
            if validation_error:
                return None, validation_error
            
            # Prepare model file for validation (save base64 to temp file if needed)
            temp_model_file = None
            model_file_path_for_validation = model_file_path
            
            if model_file_data and not model_file_path:
                # Save base64 data to temporary file for validation
                import base64
                import tempfile
                try:
                    model_data = base64.b64decode(model_file_data)
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
                    temp_file.write(model_data)
                    temp_file.close()
                    temp_model_file = temp_file.name
                    model_file_path_for_validation = temp_model_file
                except Exception as e:
                    return None, f"Failed to decode model file data: {str(e)}"
            
            # Validate model can work with competition data before accepting submission
            # This saves time and provides immediate feedback
            if competition.test_data_path and Path(competition.test_data_path).exists() and model_file_path_for_validation:
                # Parse target columns
                target_columns_list = None
                if competition.target_columns:
                    try:
                        target_columns_list = json.loads(competition.target_columns)
                        if not isinstance(target_columns_list, list):
                            target_columns_list = [target_columns_list]
                    except (json.JSONDecodeError, TypeError):
                        # If JSON parsing fails, fall back to target_column
                        if competition.target_column:
                            target_columns_list = [competition.target_column]
                elif competition.target_column:
                    target_columns_list = [competition.target_column]
                
                if target_columns_list:
                    # Validate model with test data
                    is_valid, validation_error_msg, validation_details = self.model_validator.validate_model_with_test_data(
                        model_path=model_file_path_for_validation,
                        test_data_path=competition.test_data_path,
                        target_columns=target_columns_list,
                        task_type=competition.task_type or 'classification',
                        id_column=competition.id_column,
                        sample_size=100  # Use first 100 rows for fast validation
                    )
                    
                    if not is_valid:
                        # Format validation errors for response
                        error_messages = validation_details.get('errors', [])
                        if validation_error_msg:
                            error_messages.insert(0, validation_error_msg)
                        error_msg = "Model validation failed: " + "; ".join(error_messages[:3])  # Limit to first 3 errors
                        
                        # Clean up temp file if we created it
                        if temp_model_file and Path(temp_model_file).exists():
                            try:
                                Path(temp_model_file).unlink()
                            except:
                                pass
                        
                        return None, error_msg
            
            # Register or get model in ModelRegistry
            from app.services.model_registry_service import ModelRegistryService
            model_service = ModelRegistryService()
            
            # Check if model already exists (by mlstudio_source_id if provided)
            model_registry = None
            if mlstudio_source_id:
                model_registry = model_service.get_model_by_mlstudio_id(mlstudio_source_id)
            
            if not model_registry:
                # Register new model
                model_registry, error = model_service.register_model_from_mlstudio(
                    owner_id=user_id,
                    model_name=model_name,
                    model_file_data=model_file_data,
                    model_file_path=model_file_path,
                    model_type=model_type,
                    framework=framework,
                    metrics=metrics,
                    description=description,
                    input_schema=input_schema,
                    output_schema=output_schema,
                    mlstudio_source_id=mlstudio_source_id,
                    is_public=False  # Competition submissions are not public by default
                )
                
                if error:
                    # Clean up temp file on error
                    if 'temp_model_file' in locals() and temp_model_file and Path(temp_model_file).exists():
                        try:
                            Path(temp_model_file).unlink()
                        except:
                            pass
                    return None, f"Failed to register model: {error}"
            
            # Model has been validated and registered successfully
            # Create submission record
            submission = Submission(
                competition_id=competition_id,
                user_id=user_id,
                model_id=model_registry.id,
                submission_file=model_registry.model_file_path,  # Use model file path
                status='pending'
            )
            
            db.session.add(submission)
            db.session.flush()  # Flush to get the submission ID
            
            # Update submission count
            competition.submission_count = Submission.query.filter_by(
                competition_id=competition_id
            ).count()
            
            db.session.commit()
            
            # Trigger automatic evaluation using standardized scoring
            if competition.test_data_path and Path(competition.test_data_path).exists():
                try:
                    from app.services.submission_evaluator import SubmissionEvaluator
                    evaluator = SubmissionEvaluator()
                    # Run evaluation asynchronously (could use background task in production)
                    eval_success, eval_error = evaluator.evaluate_submission(submission.id, competition_id)
                    if not eval_success:
                        logger.warning(f"Auto-evaluation failed for submission {submission.id}: {eval_error}")
                except Exception as e:
                    logger.error(f"Error triggering auto-evaluation: {e}", exc_info=True)
                    # Don't fail submission if evaluation fails to start
            
            # Record activity
            self._record_activity(user_id, 'submission_created', competition_id, submission.id)
            
            logger.info(f"Model submission created: {submission.id} for competition {competition_id} (model: {model_registry.id})")
            return submission, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting model to competition: {e}", exc_info=True)
            
            # Clean up temp file on error
            if 'temp_model_file' in locals() and temp_model_file and Path(temp_model_file).exists():
                try:
                    Path(temp_model_file).unlink()
                except:
                    pass
            
            return None, str(e)
    
    def validate_submission(
        self,
        competition_id: int,
        user_id: int
    ) -> Optional[str]:
        """
        Validate submission limits
        
        Args:
            competition_id: Competition ID
            user_id: User ID
            
        Returns:
            Error message if validation fails, None otherwise
        """
        competition = Competition.query.get(competition_id)
        if not competition:
            return "Competition not found"
        
        # Check total submissions limit
        total_submissions = Submission.query.filter_by(
            competition_id=competition_id,
            user_id=user_id
        ).count()
        
        if total_submissions >= competition.max_total_submissions:
            return f"Maximum total submissions ({competition.max_total_submissions}) reached"
        
        # Check daily submissions limit
        today = datetime.utcnow().date()
        daily_submissions = Submission.query.filter(
            and_(
                Submission.competition_id == competition_id,
                Submission.user_id == user_id,
                func.date(Submission.submitted_at) == today
            )
        ).count()
        
        if daily_submissions >= competition.max_submissions_per_day:
            return f"Maximum daily submissions ({competition.max_submissions_per_day}) reached"
        
        return None
    
    def update_submission_score(
        self,
        submission_id: int,
        score: float,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update submission score after evaluation
        
        Args:
            submission_id: Submission ID
            score: Evaluation score
            metadata: Optional evaluation metadata
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            import json
            submission = Submission.query.get(submission_id)
            if not submission:
                return False, "Submission not found"
            
            submission.score = score
            submission.status = 'evaluated'
            submission.evaluated_at = datetime.utcnow()
            
            if metadata:
                submission.submission_metadata = json.dumps(metadata)
            
            db.session.commit()
            
            # Update leaderboard rankings
            self.update_leaderboard(submission.competition_id)
            
            logger.info(f"Submission {submission_id} score updated: {score}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating submission score: {e}")
            return False, str(e)
    
    # ==================== Leaderboard ====================
    
    def get_leaderboard(
        self,
        competition_id: int,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get competition leaderboard showing best score per user
        
        Args:
            competition_id: Competition ID
            limit: Maximum number of entries to return
            
        Returns:
            List of leaderboard entries with rank, user, score (best score per user only)
        """
        # Get all evaluated submissions
        all_submissions = Submission.query.filter(
            and_(
                Submission.competition_id == competition_id,
                Submission.status == 'evaluated',
                Submission.score.isnot(None)
            )
        ).order_by(desc(Submission.score)).all()
        
        # Group by user and get best score for each
        user_best_scores = {}
        for submission in all_submissions:
            user_id = submission.user_id
            if user_id not in user_best_scores:
                user_best_scores[user_id] = submission
            else:
                # Keep submission with higher score
                if submission.score > user_best_scores[user_id].score:
                    user_best_scores[user_id] = submission
        
        # Convert to list and sort by score descending
        best_submissions = sorted(
            user_best_scores.values(),
            key=lambda s: s.score,
            reverse=True
        )[:limit]
        
        # Build leaderboard with ranks (handling ties)
        leaderboard = []
        current_rank = 1
        previous_score = None
        
        for idx, submission in enumerate(best_submissions):
            # Handle ties - same rank for same score
            if previous_score is not None and submission.score != previous_score:
                current_rank = idx + 1
            
            leaderboard.append({
                'rank': current_rank,
                'submission_id': submission.id,
                'user_id': submission.user_id,
                'username': submission.user.username if submission.user else None,
                'score': submission.score,
                'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None
            })
            
            previous_score = submission.score
        
        return leaderboard
    
    def get_user_rank(
        self,
        competition_id: int,
        user_id: int
    ) -> Optional[Dict]:
        """
        Get user's rank in competition
        
        Args:
            competition_id: Competition ID
            user_id: User ID
            
        Returns:
            Dictionary with rank info or None
        """
        # Get best submission for user
        best_submission = Submission.query.filter(
            and_(
                Submission.competition_id == competition_id,
                Submission.user_id == user_id,
                Submission.status == 'evaluated',
                Submission.score.isnot(None)
            )
        ).order_by(desc(Submission.score)).first()
        
        if not best_submission:
            return None
        
        # Calculate rank
        higher_scoring_count = Submission.query.filter(
            and_(
                Submission.competition_id == competition_id,
                Submission.status == 'evaluated',
                Submission.score > best_submission.score
            )
        ).count()
        
        rank = higher_scoring_count + 1
        
        return {
            'rank': rank,
            'score': best_submission.score,
            'submission_id': best_submission.id
        }
    
    def update_leaderboard(
        self,
        competition_id: int
    ) -> bool:
        """
        Recalculate rankings for a competition based on best scores per user
        
        Args:
            competition_id: Competition ID
            
        Returns:
            True if successful
        """
        try:
            # Get all evaluated submissions
            all_submissions = Submission.query.filter(
                and_(
                    Submission.competition_id == competition_id,
                    Submission.status == 'evaluated',
                    Submission.score.isnot(None)
                )
            ).all()
            
            # Group by user and get best submission for each
            user_best_submissions = {}
            for submission in all_submissions:
                user_id = submission.user_id
                if user_id not in user_best_submissions:
                    user_best_submissions[user_id] = submission
                else:
                    if submission.score > user_best_submissions[user_id].score:
                        user_best_submissions[user_id] = submission
            
            # Sort best submissions by score descending
            best_submissions = sorted(
                user_best_submissions.values(),
                key=lambda s: s.score,
                reverse=True
            )
            
            # Assign ranks (handling ties)
            current_rank = 1
            previous_score = None
            
            for idx, submission in enumerate(best_submissions):
                if previous_score is not None and submission.score != previous_score:
                    current_rank = idx + 1
                
                submission.rank = current_rank
                previous_score = submission.score
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating leaderboard: {e}")
            return False
    
    # ==================== Statistics ====================
    
    def get_competition_stats(
        self,
        competition_id: int
    ) -> Dict:
        """
        Get competition statistics
        
        Args:
            competition_id: Competition ID
            
        Returns:
            Dictionary with statistics
        """
        competition = Competition.query.get(competition_id)
        if not competition:
            return {}
        
        stats = {
            'competition_id': competition_id,
            'participant_count': competition.participant_count,
            'submission_count': competition.submission_count,
            'evaluated_submissions': Submission.query.filter(
                and_(
                    Submission.competition_id == competition_id,
                    Submission.status == 'evaluated'
                )
            ).count(),
            'pending_submissions': Submission.query.filter(
                and_(
                    Submission.competition_id == competition_id,
                    Submission.status == 'pending'
                )
            ).count()
        }
        
        return stats
    
    def update_participant_count(
        self,
        competition_id: int
    ) -> bool:
        """Update participant count for competition"""
        try:
            count = CompetitionParticipant.query.filter_by(
                competition_id=competition_id
            ).count()
            
            competition = Competition.query.get(competition_id)
            if competition:
                competition.participant_count = count
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating participant count: {e}")
            return False
    
    def update_submission_count(
        self,
        competition_id: int
    ) -> bool:
        """Update submission count for competition"""
        try:
            count = Submission.query.filter_by(
                competition_id=competition_id
            ).count()
            
            competition = Competition.query.get(competition_id)
            if competition:
                competition.submission_count = count
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating submission count: {e}")
            return False
    
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
                resource_type='competition',
                resource_id=resource_id,
                activity_data=json.dumps(activity_data) if activity_data else None
            )
            db.session.add(activity)
            db.session.commit()
        except Exception as e:
            logger.warning(f"Failed to record activity: {e}")
            db.session.rollback()
    
    # ==================== User Participation Data ====================
    
    def get_user_competitions(self, user_id: int) -> List[Competition]:
        """
        Get all competitions a user has joined
        
        Args:
            user_id: User ID
            
        Returns:
            List of Competition objects
        """
        participants = CompetitionParticipant.query.filter_by(user_id=user_id).all()
        competition_ids = [p.competition_id for p in participants]
        
        if not competition_ids:
            return []
        
        competitions = Competition.query.filter(Competition.id.in_(competition_ids)).all()
        return competitions
    
    def get_user_rankings(self, user_id: int) -> List[Dict]:
        """
        Get user rankings across all competitions
        
        Args:
            user_id: User ID
            
        Returns:
            List of dictionaries with competition_id, competition_title, rank, score, total_participants
        """
        rankings = []
        
        # Get all competitions user has joined
        user_competitions = self.get_user_competitions(user_id)
        
        for competition in user_competitions:
            # Get leaderboard for this competition
            leaderboard = self.get_leaderboard(competition.id)
            
            # Find user's rank
            user_rank = None
            user_score = None
            for idx, entry in enumerate(leaderboard):
                if entry['user_id'] == user_id:
                    user_rank = entry['rank']
                    user_score = entry['score']
                    break
            
            if user_rank is not None:
                rankings.append({
                    'competition_id': competition.id,
                    'competition_title': competition.title,
                    'rank': user_rank,
                    'score': user_score,
                    'total_participants': len(leaderboard),
                    'is_active': competition.is_active
                })
        
        return rankings
    
    def get_user_statistics(self, user_id: int) -> Dict:
        """
        Get user participation statistics
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with statistics
        """
        user_competitions = self.get_user_competitions(user_id)
        
        # Count submissions
        total_submissions = Submission.query.filter_by(user_id=user_id).count()
        
        # Get best ranking
        rankings = self.get_user_rankings(user_id)
        best_rank = None
        if rankings:
            best_rank = min(r['rank'] for r in rankings if r['rank'] is not None)
        
        # Active competitions count
        active_competitions = [c for c in user_competitions if c.is_active]
        
        return {
            'total_competitions_joined': len(user_competitions),
            'active_competitions': len(active_competitions),
            'total_submissions': total_submissions,
            'best_rank': best_rank,
            'competitions_with_rankings': len(rankings)
        }
    
    # ==================== Dataset and Scoring Management ====================
    
    def _is_multi_target_task(self, task_type: str) -> bool:
        """Check if task type requires multiple target columns"""
        return task_type in {'multilabel_classification', 'multioutput_regression'}
    
    def upload_competition_dataset(
        self,
        competition_id: int,
        dataset_file,
        train_ratio: float = 0.8,
        task_type: str = None,
        target_column: str = None,
        target_columns: List[str] = None,
        id_column: str = None,
        organizer_id: int = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload and split dataset for competition
        
        Args:
            competition_id: Competition ID
            dataset_file: File object to upload
            train_ratio: Ratio for train/test split (default 0.8)
            task_type: Type of ML task (required)
            target_column: Single target column name (for single-target tasks)
            target_columns: List of target column names (for multi-target tasks)
            id_column: ID column name (required)
            organizer_id: Organizer user ID (for authorization check)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            competition = Competition.query.get(competition_id)
            if not competition:
                return False, "Competition not found"
            
            # Check authorization
            if organizer_id and competition.organizer_id != organizer_id:
                from app.models.user import User
                organizer = User.query.get(organizer_id)
                if not (organizer and organizer.is_admin_role()):
                    return False, "Not authorized to upload dataset for this competition"
            
            if not dataset_file or not dataset_file.filename:
                return False, "No file provided"
            
            # Validate required parameters
            if not task_type:
                return False, "Task type is required"
            if not id_column:
                return False, "ID column is required"
            
            # Determine if multi-target task
            is_multi_target = self._is_multi_target_task(task_type)
            
            # Validate target column(s) based on task type
            if is_multi_target:
                if not target_columns or len(target_columns) == 0:
                    return False, "At least one target column is required for multi-target tasks"
                # Remove duplicates
                target_columns = list(set(target_columns))
                # Validate no target column equals ID column
                if id_column in target_columns:
                    return False, "ID column cannot be the same as any target column"
            else:
                if not target_column:
                    return False, "Target column is required for single-target tasks"
                if id_column == target_column:
                    return False, "ID column cannot be the same as target column"
            
            # Preview columns to validate they exist
            columns, error = self.preview_dataset_columns(dataset_file)
            if error:
                return False, f"Error reading dataset: {error}"
            
            if columns is None or len(columns) == 0:
                return False, "Dataset file has no columns"
            
            # Validate columns exist in dataset
            if is_multi_target:
                for col in target_columns:
                    if col not in columns:
                        return False, f"Target column '{col}' not found in dataset. Available columns: {', '.join(columns)}"
            else:
                if target_column not in columns:
                    return False, f"Target column '{target_column}' not found in dataset. Available columns: {', '.join(columns)}"
            
            if id_column not in columns:
                return False, f"ID column '{id_column}' not found in dataset. Available columns: {', '.join(columns)}"
            
            # Reset file pointer after preview
            dataset_file.seek(0)
            
            # Create competition data directory
            comp_data_dir = self.competition_data_dir / str(competition_id)
            comp_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Save original file
            filename = secure_filename(dataset_file.filename)
            unique_id = str(uuid.uuid4())[:8]
            original_filename = f"original_{unique_id}_{filename}"
            original_path = comp_data_dir / original_filename
            dataset_file.save(str(original_path))
            
            # Split dataset (keeps all columns in both splits)
            train_path, test_path, error = self.dataset_split_service.split_dataset(
                source_file_path=str(original_path),
                train_ratio=train_ratio,
                output_dir=str(comp_data_dir)
            )
            
            if error:
                # Clean up original file
                try:
                    original_path.unlink()
                except:
                    pass
                return False, f"Failed to split dataset: {error}"
            
            # Update competition with task configuration
            competition.original_dataset_path = str(original_path)
            competition.training_data_path = train_path
            competition.test_data_path = test_path
            competition.train_test_split_ratio = train_ratio
            competition.task_type = task_type
            competition.id_column = id_column
            
            if is_multi_target:
                # Store target_columns as JSON array
                competition.target_columns = json.dumps(target_columns)
                # Store first target column for legacy support
                competition.target_column = target_columns[0] if target_columns else None
            else:
                # Store target_column and target_columns as JSON array with single element
                competition.target_column = target_column
                competition.target_columns = json.dumps([target_column])
            
            competition.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Dataset uploaded and split for competition {competition_id} (task_type: {task_type})")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading competition dataset: {e}", exc_info=True)
            return False, str(e)
    
    def preview_dataset_columns(self, dataset_file) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Preview column names from dataset file without splitting
        
        Args:
            dataset_file: File object to read
            
        Returns:
            Tuple of (column_names_list, error_message)
        """
        try:
            import pandas as pd
            from io import BytesIO
            
            # Get file extension
            filename = secure_filename(dataset_file.filename)
            file_ext = Path(filename).suffix.lower()
            
            # Read file into memory
            file_content = dataset_file.read()
            dataset_file.seek(0)  # Reset file pointer
            
            # Load based on file type
            if file_ext == '.csv':
                df = pd.read_csv(BytesIO(file_content), nrows=1)  # Read just header
            elif file_ext in {'.parquet', '.pq'}:
                df = pd.read_parquet(BytesIO(file_content))
                df = df.head(1)  # Just get columns
            elif file_ext == '.json':
                df = pd.read_json(BytesIO(file_content), lines=False, nrows=1)
            elif file_ext in {'.xlsx', '.xls'}:
                df = pd.read_excel(BytesIO(file_content), nrows=1)
            else:
                return None, f"Unsupported file format: {file_ext}. Supported: CSV, Parquet, JSON, Excel"
            
            # Return column names
            column_names = df.columns.tolist()
            logger.info(f"Previewed {len(column_names)} columns from dataset file")
            return column_names, None
            
        except Exception as e:
            logger.error(f"Error previewing dataset columns: {e}", exc_info=True)
            return None, str(e)
    
    def update_scoring_config(
        self,
        competition_id: int,
        evaluation_metric: str,
        target_column: str,
        organizer_id: int = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update scoring configuration for competition (standard scoring only)
        
        Args:
            competition_id: Competition ID
            evaluation_metric: Metric name (e.g., 'accuracy', 'rmse', 'f1')
            target_column: Column name in test data containing ground truth
            organizer_id: Organizer user ID (for authorization check)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            competition = Competition.query.get(competition_id)
            if not competition:
                return False, "Competition not found"
            
            # Check authorization
            if organizer_id and competition.organizer_id != organizer_id:
                from app.models.user import User
                organizer = User.query.get(organizer_id)
                if not (organizer and organizer.is_admin_role()):
                    return False, "Not authorized to update scoring config for this competition"
            
            if not evaluation_metric:
                return False, "evaluation_metric is required"
            if not target_column:
                return False, "target_column is required"
            
            # Validate that test data exists and target column exists in it
            if competition.test_data_path:
                try:
                    import pandas as pd
                    test_file = Path(competition.test_data_path)
                    if test_file.exists():
                        if test_file.suffix.lower() == '.csv':
                            test_df = pd.read_csv(competition.test_data_path, nrows=1)
                        elif test_file.suffix.lower() in {'.parquet', '.pq'}:
                            test_df = pd.read_parquet(competition.test_data_path)
                        else:
                            test_df = None
                        
                        if test_df is not None and target_column not in test_df.columns:
                            available_cols = ', '.join(test_df.columns.tolist())
                            return False, f"Target column '{target_column}' not found in test data. Available columns: {available_cols}"
                except Exception as e:
                    logger.warning(f"Could not validate target column: {e}")
                    # Don't fail, just warn
            
            # Update competition
            competition.evaluation_metric = evaluation_metric
            competition.target_column = target_column
            competition.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Scoring config updated for competition {competition_id}: metric={evaluation_metric}, target={target_column}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating scoring config: {e}", exc_info=True)
            return False, str(e)
    
    def update_task_configuration(
        self,
        competition_id: int,
        task_type: str,
        target_columns: list = None,
        prediction_format: str = None,
        evaluation_config: dict = None,
        organizer_id: int = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update task configuration for competition
        
        Args:
            competition_id: Competition ID
            task_type: Type of ML task ('classification', 'regression', 'multilabel_classification', etc.)
            target_columns: List of target column names (for multi-output scenarios)
            prediction_format: Expected prediction format ('classes', 'probabilities', 'bounding_boxes', etc.)
            evaluation_config: Task-specific evaluation configuration (dict, will be stored as JSON)
            organizer_id: Organizer user ID (for authorization check)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            competition = Competition.query.get(competition_id)
            if not competition:
                return False, "Competition not found"
            
            # Check authorization
            if organizer_id and competition.organizer_id != organizer_id:
                from app.models.user import User
                organizer = User.query.get(organizer_id)
                if not (organizer and organizer.is_admin_role()):
                    return False, "Not authorized to update task configuration for this competition"
            
            # Validate task_type
            valid_task_types = {
                'classification', 'regression', 'multilabel_classification', 'multioutput_regression',
                'time_series', 'object_detection', 'segmentation', 'text_classification', 'ner',
                'ranking', 'recommendation'
            }
            if task_type not in valid_task_types:
                return False, f"Invalid task_type. Must be one of: {', '.join(valid_task_types)}"
            
            # Validate target_columns based on task_type
            if target_columns:
                if task_type in {'classification', 'regression', 'time_series', 'text_classification', 'ner'}:
                    if len(target_columns) > 1:
                        return False, f"Task type '{task_type}' requires a single target column"
                elif task_type in {'multilabel_classification', 'multioutput_regression'}:
                    if len(target_columns) < 2:
                        return False, f"Task type '{task_type}' requires multiple target columns"
            
            # Validate evaluation_config JSON
            eval_config_json = None
            if evaluation_config:
                try:
                    eval_config_json = json.dumps(evaluation_config)
                except (TypeError, ValueError) as e:
                    return False, f"Invalid evaluation_config: {str(e)}"
            
            # Update competition
            competition.task_type = task_type
            if target_columns:
                competition.target_columns = json.dumps(target_columns)
                # Also update legacy target_column for backward compatibility (use first one)
                if target_columns:
                    competition.target_column = target_columns[0]
            competition.prediction_format = prediction_format
            competition.evaluation_config = eval_config_json
            competition.id_column = id_column
            
            # Auto-set evaluation_metric based on task_type if not already set
            if not competition.evaluation_metric and task_type:
                from app.services.scoring_service import ScoringService
                scoring_service = ScoringService()
                competition.evaluation_metric = scoring_service._get_default_metric_for_task_type(task_type)
            
            competition.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Task configuration updated for competition {competition_id}: task_type={task_type}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating task configuration: {e}", exc_info=True)
            return False, str(e)
    
    def update_schemas(
        self,
        competition_id: int,
        input_schema: str = None,
        output_schema: str = None,
        organizer_id: int = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update expected input/output schemas for competition
        
        Args:
            competition_id: Competition ID
            input_schema: JSON string of input schema
            output_schema: JSON string of output schema
            organizer_id: Organizer user ID (for authorization check)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            competition = Competition.query.get(competition_id)
            if not competition:
                return False, "Competition not found"
            
            # Check authorization
            if organizer_id and competition.organizer_id != organizer_id:
                from app.models.user import User
                organizer = User.query.get(organizer_id)
                if not (organizer and organizer.is_admin_role()):
                    return False, "Not authorized to update schemas for this competition"
            
            # Validate JSON schemas
            if input_schema:
                try:
                    json.loads(input_schema)
                except json.JSONDecodeError as e:
                    return False, f"Invalid input schema JSON: {str(e)}"
                competition.expected_input_schema = input_schema
            
            if output_schema:
                try:
                    json.loads(output_schema)
                except json.JSONDecodeError as e:
                    return False, f"Invalid output schema JSON: {str(e)}"
                competition.expected_output_schema = output_schema
            
            competition.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Schemas updated for competition {competition_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating schemas: {e}", exc_info=True)
            return False, str(e)
    
    def update_allowed_formats(
        self,
        competition_id: int,
        formats: str,
        organizer_id: int = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update allowed model formats for competition
        
        Args:
            competition_id: Competition ID
            formats: Comma-separated list of allowed formats (e.g., "pkl,h5,onnx,pt")
            organizer_id: Organizer user ID (for authorization check)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            competition = Competition.query.get(competition_id)
            if not competition:
                return False, "Competition not found"
            
            # Check authorization
            if organizer_id and competition.organizer_id != organizer_id:
                from app.models.user import User
                organizer = User.query.get(organizer_id)
                if not (organizer and organizer.is_admin_role()):
                    return False, "Not authorized to update formats for this competition"
            
            # Validate formats (basic check)
            if formats:
                format_list = [f.strip().lower() for f in formats.split(',')]
                # Could add validation against known formats here
                competition.allowed_model_formats = ','.join(format_list)
            else:
                competition.allowed_model_formats = None
            
            competition.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Allowed formats updated for competition {competition_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating allowed formats: {e}", exc_info=True)
            return False, str(e)
    
