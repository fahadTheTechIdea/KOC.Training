"""
Scoring Service - Execute Python scoring scripts to evaluate models
"""
import os
import sys
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for executing scoring scripts to evaluate models"""
    
    def __init__(self, timeout: int = 300, max_output_size: int = 1024 * 1024):  # 5 min timeout, 1MB output
        self.timeout = timeout
        self.max_output_size = max_output_size
    
    def execute_scoring_script(
        self,
        script_path: str,
        model_path: str,
        test_data_path: str,
        output_dir: str = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """
        Execute a scoring script to evaluate a model
        
        Expected script interface:
            def score(model_path: str, test_data_path: str) -> float:
                # Load model
                # Load test data
                # Evaluate and return score
                return score_value
        
        Args:
            script_path: Path to Python scoring script
            model_path: Path to model file to evaluate
            test_data_path: Path to test dataset
            output_dir: Optional directory for output files
            
        Returns:
            Tuple of (score, error_message, execution_details)
        """
        details = {
            'execution_time': None,
            'stdout': '',
            'stderr': '',
            'return_code': None
        }
        
        try:
            script_file = Path(script_path)
            model_file = Path(model_path)
            test_data_file = Path(test_data_path)
            
            if not script_file.exists():
                return None, f"Scoring script not found: {script_path}", details
            
            if not model_file.exists():
                return None, f"Model file not found: {model_path}", details
            
            if not test_data_file.exists():
                return None, f"Test data file not found: {test_data_path}", details
            
            # Validate script syntax first
            syntax_valid, syntax_error = self._validate_script_syntax(script_path)
            if not syntax_valid:
                return None, f"Script syntax error: {syntax_error}", details
            
            # Create wrapper script that calls the score function
            import time
            start_time = time.time()
            
            wrapper_script = self._create_wrapper_script(script_path, model_path, test_data_path)
            
            try:
                # Execute wrapper script
                result = subprocess.run(
                    [sys.executable, str(wrapper_script)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=str(script_file.parent)
                )
                
                execution_time = time.time() - start_time
                details['execution_time'] = execution_time
                details['return_code'] = result.returncode
                details['stdout'] = result.stdout[:self.max_output_size]
                details['stderr'] = result.stderr[:self.max_output_size]
                
                if result.returncode != 0:
                    error_msg = f"Script execution failed with return code {result.returncode}"
                    if result.stderr:
                        error_msg += f": {result.stderr[:500]}"
                    return None, error_msg, details
                
                # Parse output - expect JSON with 'score' field or just float on stdout
                try:
                    # Try to parse as JSON first
                    output_lines = result.stdout.strip().split('\n')
                    for line in reversed(output_lines):
                        if line.strip():
                            try:
                                output_data = json.loads(line)
                                if 'score' in output_data:
                                    return float(output_data['score']), None, details
                            except json.JSONDecodeError:
                                # Try parsing as float
                                try:
                                    score = float(line.strip())
                                    return score, None, details
                                except ValueError:
                                    continue
                    
                    # If no valid output found, return error
                    return None, f"No valid score found in output. Output: {result.stdout[:200]}", details
                    
                except Exception as e:
                    return None, f"Error parsing score from output: {str(e)}", details
                    
            finally:
                # Clean up wrapper script
                try:
                    wrapper_script.unlink()
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            return None, f"Script execution timed out after {self.timeout} seconds", details
        except Exception as e:
            logger.error(f"Error executing scoring script: {e}", exc_info=True)
            return None, f"Execution error: {str(e)}", details
    
    def _validate_script_syntax(self, script_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Python script syntax
        
        Args:
            script_path: Path to Python script
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', script_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr[:500] if result.stderr else "Syntax error"
        except Exception as e:
            return False, str(e)
    
    def _create_wrapper_script(
        self,
        script_path: str,
        model_path: str,
        test_data_path: str
    ) -> Path:
        """
        Create a wrapper script that imports the scoring script and calls score()
        
        Args:
            script_path: Path to scoring script
            model_path: Path to model file
            test_data_path: Path to test data file
            
        Returns:
            Path to wrapper script
        """
        script_file = Path(script_path)
        wrapper_dir = script_file.parent
        
        # Create temporary wrapper script
        wrapper_script = wrapper_dir / f"_scoring_wrapper_{os.getpid()}.py"
        
        wrapper_content = f'''#!/usr/bin/env python3
"""
Temporary wrapper script for executing scoring function
"""
import sys
import json
from pathlib import Path

# Add script directory to path
sys.path.insert(0, r"{script_file.parent.absolute()}")

# Import the scoring script module
script_name = "{script_file.stem}"
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(script_name, r"{script_path}")
    scoring_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scoring_module)
except Exception as e:
    print(json.dumps({{"error": f"Failed to import scoring script: {{e}}"}}), file=sys.stderr)
    sys.exit(1)

# Call the score function
try:
    model_path = r"{model_path}"
    test_data_path = r"{test_data_path}"
    
    # Check if score function exists
    if not hasattr(scoring_module, 'score'):
        print(json.dumps({{"error": "Scoring script must define a 'score(model_path, test_data_path)' function"}}), file=sys.stderr)
        sys.exit(1)
    
    score_value = scoring_module.score(model_path, test_data_path)
    
    # Output score as JSON
    result = {{"score": float(score_value)}}
    print(json.dumps(result))
    sys.exit(0)
    
except Exception as e:
    import traceback
    error_msg = f"Error executing score function: {{e}}"
    print(json.dumps({{"error": error_msg}}), file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
'''
        
        wrapper_script.write_text(wrapper_content, encoding='utf-8')
        return wrapper_script
    
    def validate_scoring_script(self, script_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that scoring script has the required interface
        
        Args:
            script_path: Path to scoring script
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check syntax
            syntax_valid, syntax_error = self._validate_script_syntax(script_path)
            if not syntax_valid:
                return False, f"Syntax error: {syntax_error}"
            
            # Try to import and check for score function
            import importlib.util
            script_file = Path(script_path)
            spec = importlib.util.spec_from_file_location("scoring_module", script_path)
            if spec is None or spec.loader is None:
                return False, "Unable to load script module"
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check for score function
            if not hasattr(module, 'score'):
                return False, "Script must define a 'score(model_path, test_data_path)' function"
            
            import inspect
            score_func = getattr(module, 'score')
            if not callable(score_func):
                return False, "'score' is not callable"
            
            # Check signature (optional but helpful)
            sig = inspect.signature(score_func)
            params = list(sig.parameters.keys())
            if len(params) < 2:
                return False, "score() function must accept at least 2 parameters: model_path, test_data_path"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating scoring script: {e}", exc_info=True)
            return False, f"Validation error: {str(e)}"
    
    def execute_standard_scoring(
        self,
        model_path: str,
        test_data_path: str,
        target_column: str = None,
        target_columns: list = None,
        metric: str = None,
        task_type: str = None,
        prediction_format: str = None,
        evaluation_config: dict = None,
        id_column: str = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """
        Execute standard scoring by comparing model predictions with ground truth labels
        
        Args:
            model_path: Path to model file to evaluate
            test_data_path: Path to test dataset (CSV/Parquet/images/etc.) containing features and ground truth
            target_column: Column name in test data containing ground truth labels (legacy, use target_columns)
            target_columns: List of column names for multi-output scenarios
            metric: Metric name (accuracy, precision, recall, f1, rmse, mae, r2, etc.)
            task_type: Type of ML task (classification, regression, multilabel_classification, etc.)
            prediction_format: Expected prediction format (classes, probabilities, bounding_boxes, etc.)
            evaluation_config: Task-specific evaluation configuration (dict)
            
        Returns:
            Tuple of (score, error_message, execution_details)
        """
        import time
        import json
        
        # Determine task type (default to classification if not specified)
        if not task_type:
            task_type = 'classification'  # Default
        
        # Auto-determine metric if not provided
        if not metric:
            metric = self._get_default_metric_for_task_type(task_type)
        
        # Normalize target columns (support legacy target_column)
        if target_columns is None:
            if target_column:
                target_columns = [target_column]
            else:
                return None, "Either target_column or target_columns must be provided", {}
        
        details = {
            'execution_time': None,
            'metric_used': metric,
            'task_type': task_type,
            'target_columns': target_columns,
            'predictions_count': None,
            'error': None
        }
        
        start_time = time.time()
        
        try:
            # Route to task-specific scoring method
            if task_type in {'classification', 'regression'}:
                score, error, task_details = self._score_classification_regression(
                    model_path, test_data_path, target_columns[0] if len(target_columns) == 1 else None,
                    metric, prediction_format, id_column
                )
            elif task_type == 'multilabel_classification':
                score, error, task_details = self._score_multilabel_classification(
                    model_path, test_data_path, target_columns, metric, prediction_format, evaluation_config, id_column
                )
            elif task_type == 'multioutput_regression':
                score, error, task_details = self._score_multioutput_regression(
                    model_path, test_data_path, target_columns, metric, evaluation_config, id_column
                )
            elif task_type == 'time_series':
                score, error, task_details = self._score_time_series(
                    model_path, test_data_path, target_columns, metric, evaluation_config, id_column
                )
            elif task_type == 'object_detection':
                score, error, task_details = self._score_object_detection(
                    model_path, test_data_path, metric, evaluation_config
                )
            elif task_type == 'segmentation':
                score, error, task_details = self._score_segmentation(
                    model_path, test_data_path, metric, evaluation_config
                )
            elif task_type in {'text_classification', 'ner'}:
                score, error, task_details = self._score_text_classification(
                    model_path, test_data_path, target_columns[0] if len(target_columns) == 1 else None,
                    metric, prediction_format, id_column
                )
            elif task_type == 'ranking':
                score, error, task_details = self._score_ranking(
                    model_path, test_data_path, metric, evaluation_config
                )
            elif task_type == 'recommendation':
                score, error, task_details = self._score_recommendation(
                    model_path, test_data_path, metric, evaluation_config
                )
            else:
                return None, f"Unsupported task type: {task_type}", details
            
            execution_time = time.time() - start_time
            details['execution_time'] = execution_time
            details.update(task_details)
            
            if error:
                details['error'] = error
                return None, error, details
            
            logger.info(f"Scoring completed: task={task_type}, metric={metric}, score={score:.4f} in {execution_time:.2f}s")
            return float(score), None, details
            
        except Exception as e:
            execution_time = time.time() - start_time
            details['execution_time'] = execution_time
            details['error'] = str(e)
            logger.error(f"Error in standard scoring: {e}", exc_info=True)
            return None, f"Standard scoring error: {str(e)}", details
    
    def _load_model(self, model_path: str):
        """Load model from file based on extension"""
        model_file = Path(model_path)
        suffix = model_file.suffix.lower()
        
        if suffix in {'.pkl', '.pickle'}:
            import pickle
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        
        elif suffix in {'.h5', '.hdf5', '.keras'}:
            try:
                from tensorflow import keras
                return keras.models.load_model(model_path)
            except ImportError:
                raise ImportError("TensorFlow/Keras not available for loading .h5/.keras models")
        
        elif suffix in {'.pt', '.pth'}:
            try:
                import torch
                model = torch.load(model_path, map_location='cpu')
                if hasattr(model, 'eval'):
                    model.eval()
                return model
            except ImportError:
                raise ImportError("PyTorch not available for loading .pt/.pth models")
        
        elif suffix == '.onnx':
            try:
                import onnxruntime as ort
                return ort.InferenceSession(model_path)
            except ImportError:
                raise ImportError("onnxruntime not available for loading .onnx models")
        
        elif suffix == '.joblib':
            try:
                import joblib
                return joblib.load(model_path)
            except ImportError:
                raise ImportError("joblib not available for loading .joblib models")
        
        else:
            # Try pickle as fallback
            try:
                import pickle
                with open(model_path, 'rb') as f:
                    return pickle.load(f)
            except:
                raise ValueError(f"Unsupported model format: {suffix}")
    
    def _make_predictions(self, model, X_test, model_suffix: str):
        """Make predictions using loaded model"""
        import numpy as np
        
        try:
            # Scikit-learn style
            if hasattr(model, 'predict'):
                predictions = model.predict(X_test)
                return predictions.flatten() if predictions.ndim > 1 else predictions
            
            # ONNX model
            elif model_suffix == '.onnx':
                # ONNX models need input name
                input_name = model.get_inputs()[0].name
                outputs = model.run(None, {input_name: X_test.astype(np.float32)})
                predictions = outputs[0]
                return predictions.flatten() if predictions.ndim > 1 else predictions
            
            # PyTorch style
            elif hasattr(model, '__call__') or hasattr(model, 'forward'):
                try:
                    import torch
                    X_tensor = torch.tensor(X_test, dtype=torch.float32)
                    if hasattr(model, 'eval'):
                        model.eval()
                    with torch.no_grad():
                        outputs = model(X_tensor)
                        # Handle different output formats
                        if isinstance(outputs, torch.Tensor):
                            predictions = outputs.cpu().numpy()
                        else:
                            predictions = outputs[0].cpu().numpy() if isinstance(outputs, (list, tuple)) else outputs
                        
                        # For classification with logits, get class predictions
                        if predictions.ndim > 1 and predictions.shape[1] > 1:
                            predictions = np.argmax(predictions, axis=1)
                        
                        return predictions.flatten() if predictions.ndim > 1 else predictions
                except Exception as e:
                    logger.warning(f"PyTorch prediction failed: {e}, trying alternative")
                    # Fallback: try direct call
                    predictions = model(X_test)
                    return np.array(predictions).flatten()
            
            else:
                # Try calling model directly
                predictions = model(X_test)
                return np.array(predictions).flatten()
                
        except Exception as e:
            logger.error(f"Error making predictions: {e}", exc_info=True)
            return None
    
    def _calculate_metric(self, y_true, y_pred, metric: str) -> Optional[float]:
        """Calculate metric comparing predictions with ground truth"""
        import numpy as np
        
        try:
            metric_lower = metric.lower()
            
            # Classification metrics
            if metric_lower == 'accuracy':
                return float(np.mean(y_true == y_pred))
            
            elif metric_lower in {'precision', 'recall', 'f1', 'f1_score'}:
                try:
                    from sklearn.metrics import precision_score, recall_score, f1_score
                    average = 'binary' if len(np.unique(y_true)) == 2 else 'weighted'
                    
                    if metric_lower == 'precision':
                        return float(precision_score(y_true, y_pred, average=average, zero_division=0))
                    elif metric_lower == 'recall':
                        return float(recall_score(y_true, y_pred, average=average, zero_division=0))
                    else:  # f1 or f1_score
                        return float(f1_score(y_true, y_pred, average=average, zero_division=0))
                except ImportError:
                    # Fallback to manual calculation for binary classification
                    if len(np.unique(y_true)) == 2:
                        tp = np.sum((y_true == 1) & (y_pred == 1))
                        fp = np.sum((y_true == 0) & (y_pred == 1))
                        fn = np.sum((y_true == 1) & (y_pred == 0))
                        
                        if metric_lower == 'precision':
                            return float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
                        elif metric_lower == 'recall':
                            return float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
                        else:  # f1
                            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                            return float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
                    return None
            
            elif metric_lower == 'f1_macro':
                try:
                    from sklearn.metrics import f1_score
                    return float(f1_score(y_true, y_pred, average='macro', zero_division=0))
                except ImportError:
                    return None
            
            elif metric_lower == 'f1_weighted':
                try:
                    from sklearn.metrics import f1_score
                    return float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
                except ImportError:
                    return None
            
            elif metric_lower in {'roc_auc', 'auc', 'roc_auc_score'}:
                try:
                    from sklearn.metrics import roc_auc_score
                    # For binary classification, use probabilities if available
                    if y_pred.ndim == 1 and len(np.unique(y_true)) == 2:
                        # Convert class predictions to probabilities (simple approach)
                        # In practice, models should return probabilities for ROC-AUC
                        return float(roc_auc_score(y_true, y_pred))
                    return None
                except ImportError:
                    return None
            
            # Regression metrics (return negative for lower-is-better metrics)
            elif metric_lower == 'rmse':
                rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
                return -rmse  # Negative because competitions prefer higher scores
            
            elif metric_lower == 'mse':
                mse = float(np.mean((y_true - y_pred) ** 2))
                return -mse  # Negative because competitions prefer higher scores
            
            elif metric_lower == 'mae':
                mae = float(np.mean(np.abs(y_true - y_pred)))
                return -mae  # Negative because competitions prefer higher scores
            
            elif metric_lower == 'mape':
                # Mean Absolute Percentage Error
                mape = float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10)) * 100))
                return -mape  # Negative because competitions prefer higher scores
            
            elif metric_lower in {'r2', 'r2_score', 'r_squared'}:
                try:
                    from sklearn.metrics import r2_score
                    return float(r2_score(y_true, y_pred))
                except ImportError:
                    # Manual calculation
                    ss_res = np.sum((y_true - y_pred) ** 2)
                    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
                    if ss_tot == 0:
                        return 0.0
                    return float(1 - (ss_res / ss_tot))
            
            else:
                logger.warning(f"Unknown metric: {metric}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating metric {metric}: {e}", exc_info=True)
            return None
    
    # ==================== Task-Specific Scoring Methods ====================
    
    def _score_classification_regression(
        self,
        model_path: str,
        test_data_path: str,
        target_column: str,
        metric: str,
        prediction_format: str = None,
        id_column: str = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """Score classification or regression task (single target)"""
        import numpy as np
        
        details = {}
        
        try:
            model_file = Path(model_path)
            test_data_file = Path(test_data_path)
            
            if not model_file.exists():
                return None, f"Model file not found: {model_path}", details
            
            if not test_data_file.exists():
                return None, f"Test data file not found: {test_data_path}", details
            
            if not target_column:
                return None, "Target column is required for classification/regression", details
            
            # Load test data
            logger.info(f"Loading test data from {test_data_path}")
            df = self._load_tabular_data(test_data_path)
            if df is None:
                return None, f"Failed to load test data from {test_data_path}", details
            
            # Check if target column exists
            if target_column not in df.columns:
                available_cols = ', '.join(df.columns.tolist())
                return None, f"Target column '{target_column}' not found. Available: {available_cols}", details
            
            # Extract features and labels (exclude target and ID columns)
            exclude_columns = [target_column]
            if id_column:
                exclude_columns.append(id_column)
            feature_columns = [col for col in df.columns if col not in exclude_columns]
            if not feature_columns:
                return None, "No feature columns found", details
            
            X_test = df[feature_columns].values
            y_true = df[target_column].values
            
            # Load model
            model = self._load_model(model_path)
            
            # Make predictions
            if prediction_format == 'probabilities' and hasattr(model, 'predict_proba'):
                y_pred_proba = model.predict_proba(X_test)
                if y_pred_proba.ndim > 1 and y_pred_proba.shape[1] > 1:
                    # For classification, use probabilities directly if metric requires it
                    if metric and 'roc_auc' in metric.lower():
                        y_pred = y_pred_proba[:, 1] if y_pred_proba.shape[1] == 2 else y_pred_proba
                    else:
                        y_pred = np.argmax(y_pred_proba, axis=1)
                else:
                    y_pred = y_pred_proba.flatten()
            else:
                y_pred = self._make_predictions(model, X_test, model_file.suffix.lower())
            
            if y_pred is None:
                return None, "Failed to generate predictions", details
            
            details['predictions_count'] = len(y_pred)
            
            # Calculate metric
            score = self._calculate_metric(y_true, y_pred, metric)
            
            if score is None:
                return None, f"Failed to calculate {metric} metric", details
            
            return float(score), None, details
            
        except Exception as e:
            logger.error(f"Error in classification/regression scoring: {e}", exc_info=True)
            return None, f"Scoring error: {str(e)}", details
    
    def _score_multilabel_classification(
        self,
        model_path: str,
        test_data_path: str,
        target_columns: list,
        metric: str,
        prediction_format: str = None,
        evaluation_config: dict = None,
        id_column: str = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """Score multi-label classification task"""
        import numpy as np
        import pandas as pd
        
        details = {}
        threshold = evaluation_config.get('threshold', 0.5) if evaluation_config else 0.5
        
        try:
            df = self._load_tabular_data(test_data_path)
            if df is None:
                return None, f"Failed to load test data", details
            
            # Validate target columns
            missing_cols = [col for col in target_columns if col not in df.columns]
            if missing_cols:
                return None, f"Target columns not found: {', '.join(missing_cols)}", details
            
            # Extract features (exclude target and ID columns)
            exclude_columns = list(target_columns)
            if id_column:
                exclude_columns.append(id_column)
            feature_columns = [col for col in df.columns if col not in exclude_columns]
            if not feature_columns:
                return None, "No feature columns found", details
            
            X_test = df[feature_columns].values
            y_true = df[target_columns].values  # Shape: (n_samples, n_labels)
            
            # Load model and make predictions
            model = self._load_model(model_path)
            
            if prediction_format == 'probabilities' and hasattr(model, 'predict_proba'):
                y_pred_proba = model.predict_proba(X_test)
                # Apply threshold
                y_pred = (y_pred_proba >= threshold).astype(int)
            elif hasattr(model, 'predict'):
                y_pred = model.predict(X_test)
                # Ensure binary format
                if y_pred.dtype != int or (y_pred.max() > 1 or y_pred.min() < 0):
                    y_pred = (y_pred >= threshold).astype(int)
            else:
                return None, "Model does not support multi-label prediction", details
            
            # Ensure predictions match ground truth shape
            if y_pred.shape != y_true.shape:
                if y_pred.ndim == 1:
                    # Reshape if needed (assume binary encoding)
                    return None, "Prediction shape mismatch for multi-label classification", details
            
            # Calculate metric
            score = self._calculate_multilabel_metric(y_true, y_pred, metric)
            
            if score is None:
                return None, f"Failed to calculate {metric} for multi-label classification", details
            
            details['predictions_count'] = len(y_pred)
            return float(score), None, details
            
        except Exception as e:
            logger.error(f"Error in multi-label scoring: {e}", exc_info=True)
            return None, f"Multi-label scoring error: {str(e)}", details
    
    def _score_multioutput_regression(
        self,
        model_path: str,
        test_data_path: str,
        target_columns: list,
        metric: str,
        evaluation_config: dict = None,
        id_column: str = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """Score multi-output regression task"""
        import numpy as np
        
        details = {}
        
        try:
            df = self._load_tabular_data(test_data_path)
            if df is None:
                return None, f"Failed to load test data", details
            
            missing_cols = [col for col in target_columns if col not in df.columns]
            if missing_cols:
                return None, f"Target columns not found: {', '.join(missing_cols)}", details
            
            # Extract features (exclude target and ID columns)
            exclude_columns = list(target_columns)
            if id_column:
                exclude_columns.append(id_column)
            feature_columns = [col for col in df.columns if col not in exclude_columns]
            X_test = df[feature_columns].values
            y_true = df[target_columns].values  # Shape: (n_samples, n_outputs)
            
            model = self._load_model(model_path)
            y_pred = self._make_predictions(model, X_test, Path(model_path).suffix.lower())
            
            if y_pred is None:
                return None, "Failed to generate predictions", details
            
            # Ensure predictions match shape
            if y_pred.shape != y_true.shape:
                return None, f"Prediction shape {y_pred.shape} does not match ground truth shape {y_true.shape}", details
            
            # Calculate metric (mean across outputs)
            score = self._calculate_multioutput_metric(y_true, y_pred, metric)
            
            if score is None:
                return None, f"Failed to calculate {metric} for multi-output regression", details
            
            details['predictions_count'] = len(y_pred)
            return float(score), None, details
            
        except Exception as e:
            logger.error(f"Error in multi-output regression scoring: {e}", exc_info=True)
            return None, f"Multi-output regression error: {str(e)}", details
    
    def _score_time_series(
        self,
        model_path: str,
        test_data_path: str,
        target_columns: list,
        metric: str,
        evaluation_config: dict = None,
        id_column: str = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """Score time series forecasting task"""
        import numpy as np
        
        details = {}
        
        try:
            df = self._load_tabular_data(test_data_path)
            if df is None:
                return None, f"Failed to load test data", details
            
            # Time series assumes temporal ordering, may need windowing
            target_col = target_columns[0] if target_columns else None
            if not target_col or target_col not in df.columns:
                return None, f"Target column not found for time series", details
            
            # Extract features (exclude target and ID columns)
            exclude_columns = [target_col]
            if id_column:
                exclude_columns.append(id_column)
            feature_columns = [col for col in df.columns if col not in exclude_columns]
            X_test = df[feature_columns].values
            y_true = df[target_col].values
            
            model = self._load_model(model_path)
            y_pred = self._make_predictions(model, X_test, Path(model_path).suffix.lower())
            
            if y_pred is None:
                return None, "Failed to generate predictions", details
            
            # Calculate time series metric
            score = self._calculate_time_series_metric(y_true, y_pred, metric)
            
            if score is None:
                return None, f"Failed to calculate {metric} for time series", details
            
            details['predictions_count'] = len(y_pred)
            return float(score), None, details
            
        except Exception as e:
            logger.error(f"Error in time series scoring: {e}", exc_info=True)
            return None, f"Time series scoring error: {str(e)}", details
    
    def _score_object_detection(
        self,
        model_path: str,
        test_data_path: str,
        metric: str,
        evaluation_config: dict = None,
        id_column: str = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """Score object detection task"""
        # Placeholder - would require image loading and bounding box evaluation
        # This would need COCO evaluation tools or similar
        return None, "Object detection scoring not yet implemented", {}
    
    def _score_segmentation(
        self,
        model_path: str,
        test_data_path: str,
        metric: str,
        evaluation_config: dict = None,
        id_column: str = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """Score image segmentation task"""
        # Placeholder - would require image and mask loading
        return None, "Segmentation scoring not yet implemented", {}
    
    def _score_text_classification(
        self,
        model_path: str,
        test_data_path: str,
        target_column: str,
        metric: str,
        prediction_format: str = None,
        id_column: str = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """Score text classification task (similar to classification but with text preprocessing)"""
        # For now, treat as regular classification
        # Could add text preprocessing here if needed
        return self._score_classification_regression(model_path, test_data_path, target_column, metric, prediction_format, id_column)
    
    def _score_ranking(
        self,
        model_path: str,
        test_data_path: str,
        metric: str,
        evaluation_config: dict = None,
        id_column: str = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """Score learning-to-rank task"""
        # Placeholder - would require query-document structure
        return None, "Ranking scoring not yet implemented", {}
    
    def _score_recommendation(
        self,
        model_path: str,
        test_data_path: str,
        metric: str,
        evaluation_config: dict = None
    ) -> Tuple[Optional[float], Optional[str], Dict]:
        """Score recommendation system task"""
        # Placeholder - would require user-item interaction data
        return None, "Recommendation scoring not yet implemented", {}
    
    # ==================== Helper Methods ====================
    
    def _load_tabular_data(self, test_data_path: str):
        """Load tabular data (CSV/Parquet)"""
        import pandas as pd
        test_file = Path(test_data_path)
        
        try:
            if test_file.suffix.lower() == '.csv':
                return pd.read_csv(test_data_path)
            elif test_file.suffix.lower() in {'.parquet', '.pq'}:
                return pd.read_parquet(test_data_path)
            else:
                logger.error(f"Unsupported tabular data format: {test_file.suffix}")
                return None
        except Exception as e:
            logger.error(f"Error loading tabular data: {e}", exc_info=True)
            return None
    
    def _calculate_multilabel_metric(self, y_true, y_pred, metric: str) -> Optional[float]:
        """Calculate metric for multi-label classification"""
        import numpy as np
        
        try:
            metric_lower = metric.lower()
            
            if metric_lower in {'hamming_loss', 'hamming'}:
                try:
                    from sklearn.metrics import hamming_loss
                    return float(hamming_loss(y_true, y_pred))
                except ImportError:
                    # Manual calculation
                    return float(np.mean(y_true != y_pred))
            
            elif metric_lower in {'jaccard_score', 'jaccard'}:
                try:
                    from sklearn.metrics import jaccard_score
                    return float(jaccard_score(y_true, y_pred, average='macro', zero_division=0))
                except ImportError:
                    return None
            
            elif metric_lower in {'f1', 'f1_score', 'f1_micro'}:
                try:
                    from sklearn.metrics import f1_score
                    return float(f1_score(y_true, y_pred, average='micro', zero_division=0))
                except ImportError:
                    return None
            
            elif metric_lower == 'f1_macro':
                try:
                    from sklearn.metrics import f1_score
                    return float(f1_score(y_true, y_pred, average='macro', zero_division=0))
                except ImportError:
                    return None
            
            elif metric_lower == 'f1_weighted':
                try:
                    from sklearn.metrics import f1_score
                    return float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
                except ImportError:
                    return None
            
            elif metric_lower == 'subset_accuracy':
                try:
                    from sklearn.metrics import accuracy_score
                    return float(accuracy_score(y_true, y_pred))
                except ImportError:
                    # Exact match
                    return float(np.mean(np.all(y_true == y_pred, axis=1)))
            
            else:
                logger.warning(f"Unknown multi-label metric: {metric}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating multi-label metric {metric}: {e}", exc_info=True)
            return None
    
    def _calculate_multioutput_metric(self, y_true, y_pred, metric: str) -> Optional[float]:
        """Calculate metric for multi-output regression (mean across outputs)"""
        import numpy as np
        
        try:
            metric_lower = metric.lower()
            
            if metric_lower == 'rmse':
                rmse_per_output = np.sqrt(np.mean((y_true - y_pred) ** 2, axis=0))
                mean_rmse = np.mean(rmse_per_output)
                return -float(mean_rmse)  # Negative for competitions
            
            elif metric_lower == 'mae':
                mae_per_output = np.mean(np.abs(y_true - y_pred), axis=0)
                mean_mae = np.mean(mae_per_output)
                return -float(mean_mae)  # Negative for competitions
            
            elif metric_lower in {'r2', 'r2_score'}:
                try:
                    from sklearn.metrics import r2_score
                    r2_per_output = [r2_score(y_true[:, i], y_pred[:, i]) for i in range(y_true.shape[1])]
                    return float(np.mean(r2_per_output))
                except ImportError:
                    # Manual calculation
                    ss_res_per_output = np.sum((y_true - y_pred) ** 2, axis=0)
                    ss_tot_per_output = np.sum((y_true - np.mean(y_true, axis=0)) ** 2, axis=0)
                    r2_per_output = 1 - (ss_res_per_output / (ss_tot_per_output + 1e-10))
                    return float(np.mean(r2_per_output))
            
            else:
                logger.warning(f"Unknown multi-output metric: {metric}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating multi-output metric {metric}: {e}", exc_info=True)
            return None
    
    def _calculate_time_series_metric(self, y_true, y_pred, metric: str) -> Optional[float]:
        """Calculate metric for time series"""
        import numpy as np
        
        try:
            metric_lower = metric.lower()
            
            if metric_lower == 'rmse':
                rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
                return -rmse  # Negative for competitions
            
            elif metric_lower == 'mae':
                mae = float(np.mean(np.abs(y_true - y_pred)))
                return -mae
            
            elif metric_lower == 'mape':
                mape = float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10)) * 100))
                return -mape
            
            elif metric_lower == 'smape':
                # Symmetric MAPE
                smape = float(np.mean(200 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-10)))
                return -smape
            
            elif metric_lower == 'directional_accuracy':
                # Percentage of correct direction predictions
                if len(y_true) < 2:
                    return None
                true_direction = np.sign(y_true[1:] - y_true[:-1])
                pred_direction = np.sign(y_pred[1:] - y_pred[:-1])
                accuracy = float(np.mean(true_direction == pred_direction))
                return accuracy
            
            else:
                # Fall back to standard regression metrics
                return self._calculate_metric(y_true, y_pred, metric)
                
        except Exception as e:
            logger.error(f"Error calculating time series metric {metric}: {e}", exc_info=True)
            return None
    
    def _get_default_metric_for_task_type(self, task_type: str) -> str:
        """Get default evaluation metric for task type"""
        metric_map = {
            'classification': 'accuracy',
            'regression': 'r2',
            'multilabel_classification': 'f1_micro',
            'multioutput_regression': 'r2',
            'time_series': 'rmse',
            'text_classification': 'accuracy'
        }
        return metric_map.get(task_type, 'accuracy')
