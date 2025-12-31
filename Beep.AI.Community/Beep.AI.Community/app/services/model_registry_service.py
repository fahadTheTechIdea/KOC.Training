"""
Model Registry Service - Model registration and management
"""
import os
import base64
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from app import db
from app.models.model_registry import ModelRegistry
import logging
import uuid

logger = logging.getLogger(__name__)


class ModelRegistryService:
    """Service for model registry operations"""
    
    def __init__(self, upload_folder: str = 'uploads/models'):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)
    
    def register_model_from_mlstudio(
        self,
        owner_id: int,
        model_name: str,
        model_file_data: Optional[str] = None,  # base64 encoded or file path
        model_file_path: Optional[str] = None,  # path to existing file
        model_type: Optional[str] = None,
        framework: Optional[str] = None,
        metrics: Optional[Dict] = None,
        description: Optional[str] = None,
        input_schema: Optional[Dict] = None,
        output_schema: Optional[Dict] = None,
        mlstudio_source_id: Optional[str] = None,
        is_public: bool = True
    ) -> Tuple[Optional[ModelRegistry], Optional[str]]:
        """
        Register a model from MLStudio
        
        Args:
            owner_id: User ID who owns the model
            model_name: Name of the model
            model_file_data: Base64 encoded model file data OR file path
            model_file_path: Path to model file (if file already exists)
            model_type: Type of model (e.g., 'classification', 'regression')
            framework: Framework used (e.g., 'tensorflow', 'pytorch')
            metrics: Model metrics dictionary
            description: Model description
            input_schema: Input schema dictionary
            output_schema: Output schema dictionary
            mlstudio_source_id: Original MLStudio model ID (optional)
            is_public: Whether model is public
            
        Returns:
            Tuple of (model_registry_object, error_message)
        """
        try:
            # Determine final file path
            final_file_path = None
            
            if model_file_path:
                # Use provided file path
                final_file_path = model_file_path
            elif model_file_data:
                # Decode base64 and save file
                try:
                    # Check if it's base64 encoded
                    if model_file_data.startswith('data:'):
                        # Remove data URL prefix if present
                        model_file_data = model_file_data.split(',')[1]
                    
                    file_data = base64.b64decode(model_file_data)
                    
                    # Generate unique filename
                    file_ext = '.pkl'  # Default extension, could be determined from metadata
                    unique_id = str(uuid.uuid4())[:8]
                    filename = f"{secure_filename(model_name)}_{unique_id}{file_ext}"
                    final_file_path = str(self.upload_folder / filename)
                    
                    # Save file
                    with open(final_file_path, 'wb') as f:
                        f.write(file_data)
                    
                    logger.info(f"Model file saved: {final_file_path}")
                except Exception as e:
                    logger.error(f"Error decoding/saving model file: {e}")
                    return None, f"Failed to save model file: {str(e)}"
            else:
                return None, "Either model_file_data or model_file_path must be provided"
            
            # Serialize JSON fields
            metrics_json = json.dumps(metrics) if metrics else None
            input_schema_json = json.dumps(input_schema) if input_schema else None
            output_schema_json = json.dumps(output_schema) if output_schema else None
            
            # Create model registry entry
            model = ModelRegistry(
                name=model_name,
                description=description,
                owner_id=owner_id,
                model_type=model_type,
                framework=framework,
                model_file_path=final_file_path,
                metrics=metrics_json,
                input_schema=input_schema_json,
                output_schema=output_schema_json,
                is_public=is_public
            )
            
            # Add optional fields if they exist (may need migration)
            if hasattr(model, 'mlstudio_source_id'):
                model.mlstudio_source_id = mlstudio_source_id
            if hasattr(model, 'source'):
                model.source = 'mlstudio'
            
            db.session.add(model)
            db.session.commit()
            
            logger.info(f"Model registered: {model.id} ({model_name}) by user {owner_id}")
            return model, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering model: {e}", exc_info=True)
            return None, str(e)
    
    def get_user_models(
        self,
        user_id: int,
        limit: int = 100,
        is_public: Optional[bool] = None
    ) -> List[ModelRegistry]:
        """
        Get user's registered models
        
        Args:
            user_id: User ID
            limit: Maximum number of models to return
            is_public: Filter by public status (None for all)
            
        Returns:
            List of ModelRegistry objects
        """
        query = ModelRegistry.query.filter_by(owner_id=user_id)
        
        if is_public is not None:
            query = query.filter_by(is_public=is_public)
        
        models = query.order_by(ModelRegistry.created_at.desc()).limit(limit).all()
        return models
    
    def get_model_by_id(self, model_id: int) -> Optional[ModelRegistry]:
        """Get model by ID"""
        return ModelRegistry.query.get(model_id)
    
    def get_model_by_mlstudio_id(self, mlstudio_source_id: str) -> Optional[ModelRegistry]:
        """Get model by MLStudio source ID (if field exists)"""
        if hasattr(ModelRegistry, 'mlstudio_source_id'):
            return ModelRegistry.query.filter_by(mlstudio_source_id=mlstudio_source_id).first()
        return None
    
    def update_model(
        self,
        model_id: int,
        owner_id: int,
        updates: Dict
    ) -> Tuple[Optional[ModelRegistry], Optional[str]]:
        """
        Update model registry entry
        
        Args:
            model_id: Model ID
            owner_id: Owner ID (for authorization)
            updates: Dictionary of fields to update
            
        Returns:
            Tuple of (updated_model, error_message)
        """
        try:
            model = ModelRegistry.query.get(model_id)
            if not model:
                return None, "Model not found"
            
            if model.owner_id != owner_id:
                return None, "Not authorized to update this model"
            
            # Update allowed fields
            allowed_fields = [
                'name', 'description', 'model_type', 'framework',
                'metrics', 'input_schema', 'output_schema', 'is_public'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field in ['metrics', 'input_schema', 'output_schema']:
                        # Serialize JSON fields
                        setattr(model, field, json.dumps(value) if value else None)
                    else:
                        setattr(model, field, value)
            
            model.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Model updated: {model_id}")
            return model, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating model: {e}")
            return None, str(e)
    
    def delete_model(
        self,
        model_id: int,
        owner_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a model
        
        Args:
            model_id: Model ID
            owner_id: Owner ID (for authorization)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            model = ModelRegistry.query.get(model_id)
            if not model:
                return False, "Model not found"
            
            if model.owner_id != owner_id:
                return False, "Not authorized to delete this model"
            
            # Delete model file if it exists
            if model.model_file_path and Path(model.model_file_path).exists():
                try:
                    Path(model.model_file_path).unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete model file: {e}")
            
            db.session.delete(model)
            db.session.commit()
            
            logger.info(f"Model deleted: {model_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting model: {e}")
            return False, str(e)
