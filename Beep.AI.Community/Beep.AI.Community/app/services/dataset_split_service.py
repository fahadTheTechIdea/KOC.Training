"""
Dataset Split Service - Split datasets into training and test sets
"""
import os
import random
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class DatasetSplitService:
    """Service for splitting datasets into training and test sets"""
    
    def __init__(self):
        self.supported_formats = {'.csv', '.parquet', '.json', '.xlsx', '.xls'}
    
    def split_dataset(
        self,
        source_file_path: str,
        train_ratio: float = 0.8,
        output_dir: str = None,
        random_seed: int = 42
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Split a dataset file into training and test sets
        
        Args:
            source_file_path: Path to source dataset file
            train_ratio: Ratio for training set (default 0.8 = 80% train, 20% test)
            output_dir: Directory to save split files (default: same as source)
            random_seed: Random seed for reproducibility
            
        Returns:
            Tuple of (training_file_path, test_file_path, error_message)
        """
        try:
            source_path = Path(source_file_path)
            if not source_path.exists():
                return None, None, f"Source file not found: {source_file_path}"
            
            # Determine output directory
            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = source_path.parent
            
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Get file extension
            file_ext = source_path.suffix.lower()
            
            if file_ext not in self.supported_formats:
                return None, None, f"Unsupported file format: {file_ext}. Supported: {', '.join(self.supported_formats)}"
            
            # Set random seed for reproducibility
            random.seed(random_seed)
            
            # Split based on file type
            if file_ext == '.csv':
                train_path, test_path = self._split_csv(source_path, output_path, train_ratio, random_seed)
            elif file_ext in {'.parquet', '.pq'}:
                train_path, test_path = self._split_parquet(source_path, output_path, train_ratio, random_seed)
            elif file_ext == '.json':
                train_path, test_path = self._split_json(source_path, output_path, train_ratio, random_seed)
            elif file_ext in {'.xlsx', '.xls'}:
                train_path, test_path = self._split_excel(source_path, output_path, train_ratio, random_seed)
            else:
                return None, None, f"Split not implemented for format: {file_ext}"
            
            if train_path and test_path:
                logger.info(f"Dataset split successfully: train={train_path}, test={test_path}")
                return str(train_path), str(test_path), None
            else:
                return None, None, "Failed to split dataset"
                
        except Exception as e:
            logger.error(f"Error splitting dataset: {e}", exc_info=True)
            return None, None, str(e)
    
    def _split_csv(
        self,
        source_path: Path,
        output_path: Path,
        train_ratio: float,
        random_seed: int
    ) -> Tuple[Path, Path]:
        """Split CSV file into train/test"""
        try:
            # Read CSV
            df = pd.read_csv(source_path)
            
            # Shuffle dataframe
            df = df.sample(frac=1, random_state=random_seed).reset_index(drop=True)
            
            # Split
            split_index = int(len(df) * train_ratio)
            train_df = df[:split_index]
            test_df = df[split_index:]
            
            # Generate output filenames
            stem = source_path.stem
            train_path = output_path / f"{stem}_train.csv"
            test_path = output_path / f"{stem}_test.csv"
            
            # Save
            train_df.to_csv(train_path, index=False)
            test_df.to_csv(test_path, index=False)
            
            return train_path, test_path
        except Exception as e:
            logger.error(f"Error splitting CSV: {e}")
            return None, None
    
    def _split_parquet(
        self,
        source_path: Path,
        output_path: Path,
        train_ratio: float,
        random_seed: int
    ) -> Tuple[Path, Path]:
        """Split Parquet file into train/test"""
        try:
            # Read parquet
            df = pd.read_parquet(source_path)
            
            # Shuffle dataframe
            df = df.sample(frac=1, random_state=random_seed).reset_index(drop=True)
            
            # Split
            split_index = int(len(df) * train_ratio)
            train_df = df[:split_index]
            test_df = df[split_index:]
            
            # Generate output filenames
            stem = source_path.stem
            train_path = output_path / f"{stem}_train.parquet"
            test_path = output_path / f"{stem}_test.parquet"
            
            # Save
            train_df.to_parquet(train_path, index=False)
            test_df.to_parquet(test_path, index=False)
            
            return train_path, test_path
        except Exception as e:
            logger.error(f"Error splitting Parquet: {e}")
            return None, None
    
    def _split_json(
        self,
        source_path: Path,
        output_path: Path,
        train_ratio: float,
        random_seed: int
    ) -> Tuple[Path, Path]:
        """Split JSON file into train/test (assumes array of objects)"""
        try:
            import json
            
            # Read JSON
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                # If it's a single object, wrap it in a list
                data = [data]
            
            # Shuffle
            random.seed(random_seed)
            random.shuffle(data)
            
            # Split
            split_index = int(len(data) * train_ratio)
            train_data = data[:split_index]
            test_data = data[split_index:]
            
            # Generate output filenames
            stem = source_path.stem
            train_path = output_path / f"{stem}_train.json"
            test_path = output_path / f"{stem}_test.json"
            
            # Save
            with open(train_path, 'w', encoding='utf-8') as f:
                json.dump(train_data, f, indent=2, ensure_ascii=False)
            with open(test_path, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2, ensure_ascii=False)
            
            return train_path, test_path
        except Exception as e:
            logger.error(f"Error splitting JSON: {e}")
            return None, None
    
    def _split_excel(
        self,
        source_path: Path,
        output_path: Path,
        train_ratio: float,
        random_seed: int
    ) -> Tuple[Path, Path]:
        """Split Excel file into train/test"""
        try:
            # Read Excel (first sheet)
            df = pd.read_excel(source_path)
            
            # Shuffle dataframe
            df = df.sample(frac=1, random_state=random_seed).reset_index(drop=True)
            
            # Split
            split_index = int(len(df) * train_ratio)
            train_df = df[:split_index]
            test_df = df[split_index:]
            
            # Generate output filenames
            stem = source_path.stem
            train_path = output_path / f"{stem}_train.xlsx"
            test_path = output_path / f"{stem}_test.xlsx"
            
            # Save
            train_df.to_excel(train_path, index=False)
            test_df.to_excel(test_path, index=False)
            
            return train_path, test_path
        except Exception as e:
            logger.error(f"Error splitting Excel: {e}")
            return None, None
    
    def get_split_info(
        self,
        train_path: str,
        test_path: str
    ) -> Dict:
        """
        Get information about split files (sizes, row counts, etc.)
        
        Args:
            train_path: Path to training file
            test_path: Path to test file
            
        Returns:
            Dictionary with split information
        """
        try:
            train_file = Path(train_path)
            test_file = Path(test_path)
            
            info = {
                'train_file_size': train_file.stat().st_size if train_file.exists() else 0,
                'test_file_size': test_file.stat().st_size if test_file.exists() else 0,
                'train_rows': None,
                'test_rows': None
            }
            
            # Try to get row counts for supported formats
            if train_file.suffix.lower() == '.csv' and train_file.exists():
                try:
                    df = pd.read_csv(train_file)
                    info['train_rows'] = len(df)
                except:
                    pass
            
            if test_file.suffix.lower() == '.csv' and test_file.exists():
                try:
                    df = pd.read_csv(test_file)
                    info['test_rows'] = len(df)
                except:
                    pass
            
            return info
        except Exception as e:
            logger.error(f"Error getting split info: {e}")
            return {}
