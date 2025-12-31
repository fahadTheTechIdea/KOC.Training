"""
Model Validator Service - Validate submitted model files
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import importlib.util

logger = logging.getLogger(__name__)


class ModelValidator:
    """Service for validating model files"""
    
    # Format to extension mapping
    FORMAT_EXTENSIONS = {
        'pkl': ['.pkl', '.pickle'],
        'h5': ['.h5', '.hdf5'],
        'onnx': ['.onnx'],
        'pt': ['.pt', '.pth'],
        'pth': ['.pt', '.pth'],
        'keras': ['.keras'],
        'tflite': ['.tflite'],
        'pb': ['.pb'],  # TensorFlow SavedModel
        'joblib': ['.joblib']
    }
    
    def validate_model_file(
        self,
        file_path: str,
        allowed_formats: str = None,
        expected_input_schema: str = None,
        expected_output_schema: str = None
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Validate a model file
        
        Args:
            file_path: Path to model file
            allowed_formats: Comma-separated list of allowed formats (e.g., "pkl,h5,onnx")
            expected_input_schema: JSON string of expected input schema
            expected_output_schema: JSON string of expected output schema
            
        Returns:
            Tuple of (is_valid, error_message, validation_details)
        """
        details = {
            'format': None,
            'file_size': 0,
            'loadable': False,
            'schema_valid': None,
            'errors': []
        }
        
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return False, "Model file not found", details
            
            # Get file info
            details['file_size'] = file_path_obj.stat().st_size
            file_ext = file_path_obj.suffix.lower()
            
            # Check format
            if allowed_formats:
                allowed_list = [f.strip().lower() for f in allowed_formats.split(',')]
                format_match = False
                detected_format = None
                
                for fmt, exts in self.FORMAT_EXTENSIONS.items():
                    if file_ext in exts:
                        detected_format = fmt
                        if fmt in allowed_list:
                            format_match = True
                        break
                
                if not format_match:
                    error_msg = f"Model format not allowed. Detected: {detected_format or 'unknown'}, Allowed: {', '.join(allowed_list)}"
                    details['errors'].append(error_msg)
                    return False, error_msg, details
                
                details['format'] = detected_format
            else:
                # Detect format anyway
                for fmt, exts in self.FORMAT_EXTENSIONS.items():
                    if file_ext in exts:
                        details['format'] = fmt
                        break
            
            # Try to load the model
            loadable, load_error = self._try_load_model(file_path, details.get('format'))
            details['loadable'] = loadable
            
            if not loadable:
                error_msg = f"Model file cannot be loaded: {load_error}"
                details['errors'].append(error_msg)
                return False, error_msg, details
            
            # Validate schemas if provided
            if expected_input_schema or expected_output_schema:
                schema_valid, schema_error = self._validate_schemas(
                    file_path,
                    expected_input_schema,
                    expected_output_schema
                )
                details['schema_valid'] = schema_valid
                
                if not schema_valid:
                    error_msg = f"Schema validation failed: {schema_error}"
                    details['errors'].append(error_msg)
                    # Schema validation is optional, so we still return True if format and loadability are OK
                    # But log the schema warning
                    logger.warning(f"Schema validation warning for {file_path}: {schema_error}")
            
            return True, None, details
            
        except Exception as e:
            logger.error(f"Error validating model file: {e}", exc_info=True)
            details['errors'].append(str(e))
            return False, f"Validation error: {str(e)}", details
    
    def _try_load_model(
        self,
        file_path: str,
        detected_format: str = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Try to load/deserialize the model file
        
        Args:
            file_path: Path to model file
            detected_format: Detected format (optional)
            
        Returns:
            Tuple of (can_load, error_message)
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # Try different loading methods based on format
            if detected_format == 'pkl' or file_ext in {'.pkl', '.pickle'}:
                return self._try_load_pickle(file_path)
            elif detected_format == 'h5' or file_ext in {'.h5', '.hdf5'}:
                return self._try_load_h5(file_path)
            elif detected_format == 'onnx' or file_ext == '.onnx':
                return self._try_load_onnx(file_path)
            elif detected_format in {'pt', 'pth'} or file_ext in {'.pt', '.pth'}:
                return self._try_load_pytorch(file_path)
            elif detected_format == 'keras' or file_ext == '.keras':
                return self._try_load_keras(file_path)
            elif detected_format == 'joblib' or file_ext == '.joblib':
                return self._try_load_joblib(file_path)
            else:
                # Try generic pickle first
                try_pickle, pickle_err = self._try_load_pickle(file_path)
                if try_pickle:
                    return True, None
                
                # If pickle fails, return format-specific error
                return False, f"Unable to load model format: {detected_format or 'unknown'}"
                
        except Exception as e:
            return False, str(e)
    
    def _try_load_pickle(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Try loading as pickle"""
        try:
            import pickle
            with open(file_path, 'rb') as f:
                pickle.load(f)
            return True, None
        except Exception as e:
            return False, f"Pickle load failed: {str(e)}"
    
    def _try_load_h5(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Try loading as HDF5/Keras"""
        try:
            import h5py
            with h5py.File(file_path, 'r') as f:
                # Just check if we can open it
                pass
            return True, None
        except ImportError:
            return False, "h5py not available"
        except Exception as e:
            return False, f"HDF5 load failed: {str(e)}"
    
    def _try_load_onnx(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Try loading as ONNX"""
        try:
            import onnx
            onnx_model = onnx.load(file_path)
            onnx.checker.check_model(onnx_model)
            return True, None
        except ImportError:
            return False, "onnx not available"
        except Exception as e:
            return False, f"ONNX load failed: {str(e)}"
    
    def _try_load_pytorch(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Try loading as PyTorch"""
        try:
            import torch
            torch.load(file_path, map_location='cpu')
            return True, None
        except ImportError:
            return False, "torch not available"
        except Exception as e:
            return False, f"PyTorch load failed: {str(e)}"
    
    def _try_load_keras(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Try loading as Keras"""
        try:
            from tensorflow import keras
            keras.models.load_model(file_path)
            return True, None
        except ImportError:
            return False, "tensorflow/keras not available"
        except Exception as e:
            return False, f"Keras load failed: {str(e)}"
    
    def _try_load_joblib(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Try loading as joblib"""
        try:
            import joblib
            joblib.load(file_path)
            return True, None
        except ImportError:
            return False, "joblib not available"
        except Exception as e:
            return False, f"Joblib load failed: {str(e)}"
    
    def _validate_schemas(
        self,
        file_path: str,
        expected_input_schema: str = None,
        expected_output_schema: str = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate model input/output schemas
        
        This is a placeholder implementation. In a real scenario, you would:
        1. Load the model
        2. Inspect its input/output signatures
        3. Compare with expected schemas
        
        Args:
            file_path: Path to model file
            expected_input_schema: JSON string of expected input schema
            expected_output_schema: JSON string of expected output schema
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # TODO: Implement actual schema validation
        # For now, we'll do basic JSON schema validation
        try:
            if expected_input_schema:
                try:
                    json.loads(expected_input_schema)
                except json.JSONDecodeError:
                    return False, "Invalid input schema JSON"
            
            if expected_output_schema:
                try:
                    json.loads(expected_output_schema)
                except json.JSONDecodeError:
                    return False, "Invalid output schema JSON"
            
            # Actual model schema validation would require loading the model
            # and inspecting its signature, which is format-specific
            # This is a complex operation that would need format-specific implementations
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    def validate_model_with_test_data(
        self,
        model_path: str,
        test_data_path: str,
        target_columns: List[str],
        task_type: str,
        id_column: str = None,
        sample_size: int = 100
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Validate model can generate predictions on test data
        
        Args:
            model_path: Path to model file
            test_data_path: Path to test dataset
            target_columns: List of target column names
            task_type: ML task type
            id_column: ID column name (to exclude from features)
            sample_size: Number of rows to sample for validation
        
        Returns:
            (is_valid, error_message, validation_details)
        """
        details = {
            'model_loadable': False,
            'test_data_loadable': False,
            'predictions_generated': False,
            'prediction_shape': None,
            'expected_shape': None,
            'prediction_type': None,
            'errors': []
        }
        
        try:
            import pandas as pd
            import numpy as np
            
            # Check if files exist
            model_file = Path(model_path)
            test_file = Path(test_data_path)
            
            if not model_file.exists():
                return False, "Model file not found", details
            
            if not test_file.exists():
                return False, "Test data file not found", details
            
            # Load model using scoring service logic
            try:
                from app.services.scoring_service import ScoringService
                scoring_service = ScoringService()
                model = scoring_service._load_model(model_path)
                details['model_loadable'] = True
            except Exception as e:
                error_msg = f"Model could not be loaded: {str(e)}"
                details['errors'].append(error_msg)
                return False, error_msg, details
            
            # Load sample of test data
            try:
                file_ext = test_file.suffix.lower()
                if file_ext == '.csv':
                    df_test = pd.read_csv(test_data_path, nrows=sample_size)
                elif file_ext in {'.parquet', '.pq'}:
                    df_test = pd.read_parquet(test_data_path)
                    df_test = df_test.head(sample_size)
                elif file_ext == '.json':
                    df_test = pd.read_json(test_data_path, lines=False, nrows=sample_size)
                elif file_ext in {'.xlsx', '.xls'}:
                    df_test = pd.read_excel(test_data_path, nrows=sample_size)
                else:
                    return False, f"Unsupported test data format: {file_ext}", details
                
                if df_test.empty:
                    return False, "Test data is empty", details
                
                details['test_data_loadable'] = True
            except Exception as e:
                error_msg = f"Test data could not be loaded: {str(e)}"
                details['errors'].append(error_msg)
                return False, error_msg, details
            
            # Extract features (exclude target and ID columns)
            feature_columns = [col for col in df_test.columns 
                             if col not in target_columns and col != id_column]
            
            if not feature_columns:
                error_msg = "No feature columns available (all columns are target or ID)"
                details['errors'].append(error_msg)
                return False, error_msg, details
            
            X_test = df_test[feature_columns].values
            
            # Validate features
            if np.any(np.isnan(X_test)) or np.any(np.isinf(X_test)):
                # Handle NaN/Inf - replace with 0 or mean for validation
                X_test = np.nan_to_num(X_test, nan=0.0, posinf=0.0, neginf=0.0)
                if 'warnings' not in details:
                    details['warnings'] = []
                details['warnings'].append('Test data contains NaN/Inf values, replaced with 0 for validation')
            
            # Generate predictions
            try:
                from app.services.scoring_service import ScoringService
                scoring_service = ScoringService()
                model_suffix = Path(model_path).suffix.lower()
                predictions = scoring_service._make_predictions(model, X_test, model_suffix)
                
                if predictions is None:
                    error_msg = "Model failed to generate predictions"
                    details['errors'].append(error_msg)
                    return False, error_msg, details
                
                details['predictions_generated'] = True
                details['prediction_shape'] = list(predictions.shape)
                
            except Exception as e:
                error_msg = f"Error generating predictions: {str(e)}"
                details['errors'].append(error_msg)
                return False, error_msg, details
            
            # Validate prediction shape and type
            num_samples = len(X_test)
            num_targets = len(target_columns)
            
            # Determine expected shape based on task type
            if task_type in {'multilabel_classification', 'multioutput_regression'}:
                # Multi-target: predictions should be (num_samples, num_targets)
                expected_shape = [num_samples, num_targets]
                details['expected_shape'] = expected_shape
                
                if predictions.ndim != 2:
                    error_msg = f"Multi-target task requires 2D predictions, got {predictions.ndim}D"
                    details['errors'].append(error_msg)
                    return False, error_msg, details
                
                if predictions.shape[1] != num_targets:
                    error_msg = f"Prediction shape mismatch: expected {expected_shape}, got {list(predictions.shape)}"
                    details['errors'].append(error_msg)
                    return False, error_msg, details
            else:
                # Single-target: predictions should be (num_samples,) or (num_samples, 1)
                if predictions.ndim > 2:
                    error_msg = f"Single-target task requires 1D or 2D predictions, got {predictions.ndim}D"
                    details['errors'].append(error_msg)
                    return False, error_msg, details
                
                # Flatten if needed for validation
                original_shape = predictions.shape
                if predictions.ndim == 2 and predictions.shape[1] == 1:
                    predictions = predictions.flatten()
                elif predictions.ndim == 2 and predictions.shape[1] > 1:
                    error_msg = f"Single-target task: prediction has {predictions.shape[1]} outputs, expected 1"
                    details['errors'].append(error_msg)
                    return False, error_msg, details
                
                expected_shape = [num_samples]
                details['expected_shape'] = expected_shape
                details['prediction_shape'] = list(predictions.shape)
            
            # Validate prediction type (classification vs regression)
            if task_type in {'classification', 'text_classification', 'multilabel_classification'}:
                # Classification: predictions should be integers or probabilities
                if predictions.dtype in {np.float32, np.float64}:
                    # Check if they look like probabilities (0-1 range)
                    if np.all((predictions >= 0) & (predictions <= 1)):
                        details['prediction_type'] = 'probabilities'
                    else:
                        # Might be logits or wrong format
                        if 'warnings' not in details:
                            details['warnings'] = []
                        details['warnings'].append(
                            'Classification predictions are floats outside [0,1] range - may need conversion'
                        )
                else:
                    details['prediction_type'] = 'classes'
            
            # Check for NaN/Inf in predictions
            if np.any(np.isnan(predictions)) or np.any(np.isinf(predictions)):
                error_msg = "Predictions contain NaN or Inf values"
                details['errors'].append(error_msg)
                return False, error_msg, details
            
            # All validations passed
            return True, None, details
            
        except Exception as e:
            logger.error(f"Error validating model with test data: {e}", exc_info=True)
            error_msg = f"Validation error: {str(e)}"
            details['errors'].append(error_msg)
            return False, error_msg, details
