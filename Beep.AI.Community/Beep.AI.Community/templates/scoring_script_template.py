"""
Competition Scoring Script Template

This script will be executed to score submitted models.
The script must define a function called 'score' with the following signature:

    def score(model_path: str, test_data_path: str) -> float:
        # Load the model
        # Load the test data
        # Evaluate the model on test data
        # Return the score (float)

The function will be called by the system with:
    - model_path: Path to the submitted model file
    - test_data_path: Path to the test dataset file

IMPORTANT:
    - The score should be a float value
    - Higher scores are typically better (for competitions)
    - For metrics where lower is better (e.g., RMSE), consider returning negative values or (1.0 - normalized_value)
    - The script should handle errors gracefully (but exceptions will be caught by the system)
"""

import pandas as pd
import pickle
import numpy as np
from pathlib import Path


def score(model_path: str, test_data_path: str) -> float:
    """
    Score a model on test data
    
    Args:
        model_path: Path to the model file (can be .pkl, .h5, .onnx, .pt, etc.)
        test_data_path: Path to the test dataset file (CSV, Parquet, etc.)
        
    Returns:
        float: Model score (higher is better)
    """
    # Load test data
    test_df = pd.read_csv(test_data_path)
    
    # Separate features and target
    # Adjust column names based on your dataset structure
    feature_columns = [col for col in test_df.columns if col != 'target']
    X_test = test_df[feature_columns].values
    y_test = test_df['target'].values if 'target' in test_df.columns else None
    
    # Load model
    model_file = Path(model_path)
    if model_file.suffix == '.pkl' or model_file.suffix == '.pickle':
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
    elif model_file.suffix == '.h5' or model_file.suffix == '.hdf5':
        from tensorflow import keras
        model = keras.models.load_model(model_path)
    elif model_file.suffix in ['.pt', '.pth']:
        import torch
        model = torch.load(model_path, map_location='cpu')
        model.eval()  # Set to evaluation mode
    else:
        raise ValueError(f"Unsupported model format: {model_file.suffix}")
    
    # Make predictions
    if hasattr(model, 'predict'):
        # Scikit-learn or Keras style
        predictions = model.predict(X_test)
    elif hasattr(model, '__call__'):
        # PyTorch or other callable models
        import torch
        X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
        with torch.no_grad():
            predictions = model(X_test_tensor).numpy()
    else:
        raise ValueError("Model does not support prediction interface")
    
    # Calculate score (example: accuracy for classification, R² for regression)
    # ADJUST THIS BASED ON YOUR COMPETITION METRIC
    if y_test is not None:
        # Example 1: Accuracy for classification
        if len(predictions.shape) > 1 and predictions.shape[1] > 1:
            # Multi-class classification - get class predictions
            y_pred = np.argmax(predictions, axis=1)
        else:
            # Binary classification or regression
            y_pred = (predictions > 0.5).astype(int) if len(np.unique(y_test)) <= 2 else predictions
        
        # Accuracy metric
        accuracy = np.mean(y_pred == y_test)
        return float(accuracy)
        
        # Example 2: R² score for regression
        # from sklearn.metrics import r2_score
        # r2 = r2_score(y_test, predictions.flatten())
        # return float(r2)
        
        # Example 3: RMSE (lower is better, so return negative)
        # rmse = np.sqrt(np.mean((y_test - predictions.flatten()) ** 2))
        # return -float(rmse)  # Negative because higher is better in competitions
        
    else:
        # If no ground truth, return a placeholder score
        # In practice, you should always have ground truth for scoring
        return 0.0


# Alternative implementation examples:

def score_with_sklearn_metrics(model_path: str, test_data_path: str) -> float:
    """Example using sklearn metrics"""
    from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
    
    # Load model and data (same as above)
    # ... (implementation similar to above)
    
    # Calculate metric
    # For classification:
    # return float(accuracy_score(y_test, y_pred))
    
    # For regression with R²:
    # return float(r2_score(y_test, y_pred))
    
    # For regression with RMSE (lower is better):
    # rmse = mean_squared_error(y_test, y_pred, squared=False)
    # return -float(rmse)  # Negative because competitions prefer higher scores
    pass


def score_with_custom_metric(model_path: str, test_data_path: str) -> float:
    """Example with custom metric calculation"""
    # Load model and data
    # ... (implementation)
    
    # Calculate custom metric
    # Example: F1 score, precision, recall, custom business metric, etc.
    # return float(custom_score)
    pass
