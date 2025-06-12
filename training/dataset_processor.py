"""
Dataset Processor for The HigherSelf Network Server.

This module provides utilities for preprocessing datasets for agent training.
It includes functions for data cleaning, transformation, and feature engineering.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

from models.dataset_models import (
    DatasetMetadata,
    DatasetTrainingConfig,
    DatasetTrainingResult,
    DatasetVersion,
    ProcessedDataset,
)
from repositories.dataset_repository import (
    DatasetMetadataRepository,
    DatasetTrainingResultRepository,
    DatasetVersionRepository,
)
from services.openml_service import openml_service


class DatasetProcessor:
    """Processor for preparing datasets for agent training."""

    def __init__(self):
        """Initialize the dataset processor."""
        self.metadata_repo = DatasetMetadataRepository()
        self.version_repo = DatasetVersionRepository()
        self.training_repo = DatasetTrainingResultRepository()

        # Ensure data directories exist
        os.makedirs("data/openml", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        os.makedirs("data/training", exist_ok=True)

    async def import_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """
        Import a dataset from OpenML.

        Args:
            dataset_id: OpenML dataset ID

        Returns:
            Dataset metadata or None if import failed
        """
        try:
            # Get dataset metadata from OpenML
            dataset_meta = await openml_service.get_dataset(dataset_id)
            if not dataset_meta:
                logger.error(f"Failed to get metadata for dataset {dataset_id}")
                return None

            # Check if dataset already exists in our repository
            existing_dataset = await self.metadata_repo.async_find_by_openml_id(
                dataset_id
            )
            if existing_dataset:
                # Update existing dataset
                existing_dataset.name = dataset_meta.name
                existing_dataset.description = dataset_meta.description
                existing_dataset.format = dataset_meta.format
                existing_dataset.creator = dataset_meta.creator
                existing_dataset.contributor = dataset_meta.contributor
                existing_dataset.collection_date = dataset_meta.collection_date
                existing_dataset.upload_date = dataset_meta.upload_date
                existing_dataset.language = dataset_meta.language
                existing_dataset.licence = dataset_meta.licence
                existing_dataset.url = dataset_meta.url
                existing_dataset.default_target_attribute = (
                    dataset_meta.default_target_attribute
                )
                existing_dataset.row_count = dataset_meta.row_count
                existing_dataset.feature_count = dataset_meta.feature_count
                existing_dataset.tags = dataset_meta.tags

                # Save updated dataset
                await self.metadata_repo.async_save(existing_dataset)
                return existing_dataset
            else:
                # Add import timestamp
                dataset_meta.imported_at = datetime.now()

                # Save new dataset
                await self.metadata_repo.async_save(dataset_meta)
                return dataset_meta

        except Exception as e:
            logger.error(f"Error importing dataset {dataset_id}: {e}")
            return None

    async def process_dataset(
        self,
        dataset_id: str,
        target_column: Optional[str] = None,
        preprocessing_steps: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[DatasetVersion]:
        """
        Process a dataset and create a new version.

        Args:
            dataset_id: OpenML dataset ID
            target_column: Name of the target column
            preprocessing_steps: List of preprocessing steps to apply

        Returns:
            Dataset version or None if processing failed
        """
        try:
            # Get dataset metadata
            dataset_meta = await self.metadata_repo.async_find_by_openml_id(dataset_id)
            if not dataset_meta:
                # Try to import the dataset
                dataset_meta = await self.import_dataset(dataset_id)
                if not dataset_meta:
                    return None

            # Process the dataset
            processed = await openml_service.preprocess_dataset(
                dataset_id, target_column, preprocessing_steps
            )
            if not processed:
                return None

            # Download the dataset
            df = await openml_service.download_dataset(dataset_id)
            if df is None:
                return None

            # Apply preprocessing steps
            if preprocessing_steps:
                for step in preprocessing_steps:
                    step_type = step.get("type", "")
                    params = step.get("params", {})

                    if step_type == "drop_na":
                        df = df.dropna()
                    elif step_type == "encode_categorical":
                        for col in df.select_dtypes(include=["object"]).columns:
                            df[col] = pd.factorize(df[col])[0]
                    elif step_type == "normalize":
                        for col in df.select_dtypes(include=["number"]).columns:
                            if col != target_column:
                                df[col] = (df[col] - df[col].mean()) / df[col].std()

            # Create a new version
            version_id = f"v-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            file_path = f"data/processed/{dataset_id}_{version_id}.csv"

            # Save processed dataset
            df.to_csv(file_path, index=False)

            # Create version record
            version = DatasetVersion(
                version_id=version_id,
                dataset_id=dataset_id,
                created_at=datetime.now(),
                preprocessing_steps=preprocessing_steps or [],
                feature_columns=[col for col in df.columns if col != target_column],
                target_column=target_column or dataset_meta.default_target_attribute,
                file_path=file_path,
                format="csv",
                row_count=len(df),
                feature_count=len(df.columns) - 1
                if target_column in df.columns
                else len(df.columns),
            )

            # Save version to repository
            await self.version_repo.async_save(version)

            # Update dataset usage stats
            await self.metadata_repo.async_update_usage_stats(dataset_id)

            return version

        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {e}")
            return None

    async def prepare_training_data(
        self, config: DatasetTrainingConfig
    ) -> Tuple[
        Optional[pd.DataFrame],
        Optional[pd.DataFrame],
        Optional[pd.DataFrame],
        Optional[pd.DataFrame],
    ]:
        """
        Prepare training and testing data for an agent.

        Args:
            config: Dataset training configuration

        Returns:
            Tuple of (X_train, X_test, y_train, y_test) or (None, None, None, None) if preparation failed
        """
        try:
            # Get dataset version
            if config.version_id:
                version = await self.version_repo.async_find_by_version_id(
                    config.version_id
                )
            else:
                version = await self.version_repo.async_get_latest_version(
                    config.dataset_id
                )

            if not version:
                logger.error(f"No version found for dataset {config.dataset_id}")
                return None, None, None, None

            # Load the dataset
            df = pd.read_csv(version.file_path)

            # Determine target column
            target_column = config.target_column or version.target_column
            if not target_column:
                logger.error(
                    f"No target column specified for dataset {config.dataset_id}"
                )
                return None, None, None, None

            # Determine feature columns
            if config.feature_columns:
                feature_columns = config.feature_columns
            else:
                feature_columns = [col for col in df.columns if col != target_column]

            # Split features and target
            X = df[feature_columns]
            y = df[target_column]

            # Split into training and testing sets
            test_size = config.training_parameters.get("test_size", 0.2)
            random_state = config.training_parameters.get("random_state", 42)

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )

            return X_train, X_test, y_train, y_test

        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return None, None, None, None

    async def evaluate_model(
        self, y_true: pd.Series, y_pred: np.ndarray, metrics: List[str]
    ) -> Dict[str, float]:
        """
        Evaluate a model using specified metrics.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            metrics: List of metrics to calculate

        Returns:
            Dictionary of metric names and values
        """
        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            mean_absolute_error,
            mean_squared_error,
            precision_score,
            r2_score,
            recall_score,
        )

        results = {}

        for metric in metrics:
            try:
                if metric == "accuracy":
                    results[metric] = float(accuracy_score(y_true, y_pred))
                elif metric == "precision":
                    results[metric] = float(
                        precision_score(y_true, y_pred, average="weighted")
                    )
                elif metric == "recall":
                    results[metric] = float(
                        recall_score(y_true, y_pred, average="weighted")
                    )
                elif metric == "f1":
                    results[metric] = float(
                        f1_score(y_true, y_pred, average="weighted")
                    )
                elif metric == "mse":
                    results[metric] = float(mean_squared_error(y_true, y_pred))
                elif metric == "mae":
                    results[metric] = float(mean_absolute_error(y_true, y_pred))
                elif metric == "r2":
                    results[metric] = float(r2_score(y_true, y_pred))
            except Exception as e:
                logger.warning(f"Error calculating metric {metric}: {e}")
                results[metric] = 0.0

        return results
