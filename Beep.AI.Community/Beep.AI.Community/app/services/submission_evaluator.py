"""
Submission Evaluator - Evaluate competition submissions using validation and scoring services
"""
import os
import json
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
from app import db
from app.models.submission import Submission
from app.models.competition import Competition
from app.services.competition_service import CompetitionService
from app.services.model_validator import ModelValidator
from app.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)


class SubmissionEvaluator:
    """Service for evaluating competition submissions"""
    
    def __init__(self):
        self.competition_service = CompetitionService()
        self.model_validator = ModelValidator()
        self.scoring_service = ScoringService()
    
    def evaluate_submission(
        self,
        submission_id: int,
        competition_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate a submission using model validation and scoring script
        
        Args:
            submission_id: Submission ID
            competition_id: Competition ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            submission = Submission.query.get(submission_id)
            if not submission:
                return False, "Submission not found"
            
            competition = Competition.query.get(competition_id)
            if not competition:
                return False, "Competition not found"
            
            # Check if already evaluated
            if submission.status == 'evaluated':
                logger.info(f"Submission {submission_id} already evaluated")
                return True, None
            
            # Check if competition has required files
            if not competition.test_data_path or not Path(competition.test_data_path).exists():
                return False, "Competition test data not available"
            
            # Metric will be auto-determined from task_type if not set
            
            # Parse target columns (support both legacy target_column and new target_columns JSON)
            target_columns_list = None
            if competition.target_columns:
                try:
                    target_columns_list = json.loads(competition.target_columns)
                    if not isinstance(target_columns_list, list):
                        target_columns_list = [target_columns_list]
                except (json.JSONDecodeError, TypeError):
                    return False, "Invalid target_columns JSON format"
            
            # Fallback to legacy target_column if target_columns not set
            if not target_columns_list and competition.target_column:
                target_columns_list = [competition.target_column]
            
            if not target_columns_list:
                return False, "Competition target columns not configured (target_column or target_columns required)"
            
            # Parse evaluation_config if provided
            eval_config = None
            if competition.evaluation_config:
                try:
                    eval_config = json.loads(competition.evaluation_config)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Invalid evaluation_config JSON, ignoring: {competition.evaluation_config}")
                    eval_config = None
            
            # Get model file path
            model_path = None
            if submission.model_id and submission.model:
                model_path = submission.model.model_file_path
            elif submission.submission_file:
                model_path = submission.submission_file
            
            if not model_path or not Path(model_path).exists():
                return False, "Model file not found"
            
            # Skip model validation (simplified - just check file exists)
            # Optionally log a warning if validation fields are set but we're skipping
            validation_details = {}
            if competition.allowed_model_formats or competition.expected_input_schema:
                logger.warning(f"Model validation fields set but validation is disabled for competition {competition_id}")
            
            # Step 2: Score model using standard scoring
            submission.status = 'scoring'
            db.session.commit()
            
            # Auto-determine metric if not set (scoring service will handle this)
            metric = competition.evaluation_metric  # May be None, scoring service will auto-determine
            
            logger.info(f"Using standard scoring for submission {submission_id} (task_type: {competition.task_type or 'auto'}, metric: {metric or 'auto-determined'})")
            score, scoring_error, execution_details = self.scoring_service.execute_standard_scoring(
                model_path=model_path,
                test_data_path=competition.test_data_path,
                target_column=competition.target_column,  # Legacy support
                target_columns=target_columns_list,
                metric=metric,  # May be None, will be auto-determined
                task_type=competition.task_type,
                prediction_format=competition.prediction_format,
                evaluation_config=eval_config,
                id_column=competition.id_column
            )
            
            if scoring_error or score is None:
                submission.status = 'error'
                metadata = {
                    'validation_details': validation_details,
                    'scoring_error': scoring_error,
                    'execution_details': execution_details
                }
                submission.submission_metadata = json.dumps(metadata)
                db.session.commit()
                return False, f"Scoring failed: {scoring_error}"
            
            # Step 3: Update submission with score
            metadata = {
                'validation_details': validation_details,
                'execution_details': execution_details
            }
            
            success, error = self.competition_service.update_submission_score(
                submission_id=submission_id,
                score=float(score),
                metadata=metadata
            )
            
            if success:
                logger.info(f"Submission {submission_id} evaluated successfully: score={score}")
                return True, None
            else:
                submission.status = 'error'
                db.session.commit()
                return False, error
                
        except Exception as e:
            logger.error(f"Error evaluating submission: {e}", exc_info=True)
            if 'submission' in locals():
                submission.status = 'error'
                db.session.commit()
            return False, str(e)
    
    
    def poll_evaluation_status(
        self,
        evaluation_job_id: str
    ) -> Dict:
        """
        Poll evaluation status for an async evaluation job
        
        Args:
            evaluation_job_id: Evaluation job ID from Beep.AI.Server
            
        Returns:
            Dictionary with status information
        """
        # TODO: Implement actual polling from Beep.AI.Server
        # For now, return placeholder status
        
        return {
            'job_id': evaluation_job_id,
            'status': 'completed',
            'progress': 100,
            'message': 'Placeholder: Integration with Beep.AI.Server pending'
        }
    
    def handle_evaluation_result(
        self,
        evaluation_job_id: str,
        result: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Handle evaluation result from Beep.AI.Server
        
        Args:
            evaluation_job_id: Evaluation job ID
            result: Evaluation result dictionary
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # TODO: Extract submission_id from evaluation_job_id
            # For now, this is a placeholder
            
            # Example: result should contain {'submission_id': X, 'score': Y, 'metadata': {...}}
            submission_id = result.get('submission_id')
            if not submission_id:
                return False, "Submission ID not found in result"
            
            score = result.get('score')
            metadata = result.get('metadata', {})
            
            # Update submission
            success, error = self.competition_service.update_submission_score(
                submission_id=submission_id,
                score=score,
                metadata=metadata
            )
            
            if success:
                logger.info(f"Evaluation result processed for submission {submission_id}")
                return True, None
            else:
                return False, error
                
        except Exception as e:
            logger.error(f"Error handling evaluation result: {e}", exc_info=True)
            return False, str(e)
    
    def _integrate_with_aiserver(
        self,
        submission_file_path: str,
        dataset_id: int,
        evaluation_metric: str
    ) -> Optional[Dict]:
        """
        Integrate with Beep.AI.Server for actual evaluation
        
        This method should:
        1. Use AIServerClient to submit evaluation job
        2. Return job ID for polling
        3. Poll for results
        4. Return evaluation result
        
        Args:
            submission_file_path: Path to submission file
            dataset_id: Dataset ID
            evaluation_metric: Evaluation metric
            
        Returns:
            Dictionary with evaluation result or None if failed
        """
        # TODO: Implement actual Beep.AI.Server integration
        # Example:
        # try:
        #     from app.clients.aiserver_client import AIServerClient
        #     client = AIServerClient()
        #     
        #     # Submit evaluation job
        #     job = client.submit_evaluation_job(
        #         submission_file=submission_file_path,
        #         dataset_id=dataset_id,
        #         metric=evaluation_metric
        #     )
        #     
        #     job_id = job.get('job_id')
        #     
        #     # Poll for results
        #     while True:
        #         status = client.get_evaluation_status(job_id)
        #         if status['status'] == 'completed':
        #             return status['result']
        #         elif status['status'] == 'failed':
        #             return None
        #         time.sleep(2)  # Poll every 2 seconds
        #         
        # except Exception as e:
        #     logger.error(f"Error integrating with AIServer: {e}")
        #     return None
        
        return None
