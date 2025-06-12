"""
Agent Training Pipeline for The HigherSelf Network Server.

This module provides a training pipeline for AI agents using OpenML datasets.
It coordinates dataset processing, model training, and evaluation.
"""

import asyncio
import json
import os
import pickle
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.svm import SVC, SVR

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
from training.dataset_processor import DatasetProcessor
from utils.message_bus import AgentMessage, MessageBus


class AgentTrainingPipeline:
    """Training pipeline for AI agents."""

    def __init__(self, message_bus: Optional[MessageBus] = None):
        """
        Initialize the agent training pipeline.

        Args:
            message_bus: Optional message bus for inter-agent communication
        """
        self.dataset_processor = DatasetProcessor()
        self.metadata_repo = DatasetMetadataRepository()
        self.version_repo = DatasetVersionRepository()
        self.training_repo = DatasetTrainingResultRepository()
        self.message_bus = message_bus

        # Ensure model directory exists
        os.makedirs("models/trained", exist_ok=True)

    async def train_agent(
        self, config: DatasetTrainingConfig
    ) -> Optional[DatasetTrainingResult]:
        """
        Train an agent using a dataset.

        Args:
            config: Dataset training configuration

        Returns:
            Training result or None if training failed
        """
        # Create training result record
        training_id = f"tr-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        training_result = DatasetTrainingResult(
            training_id=training_id,
            dataset_id=config.dataset_id,
            version_id=config.version_id or "",
            agent_id=config.agent_id,
            started_at=datetime.now(),
            status="in_progress",
        )

        # Save initial training result
        await self.training_repo.async_save(training_result)

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
                # Process the dataset to create a version
                version = await self.dataset_processor.process_dataset(
                    config.dataset_id, config.target_column
                )

            if not version:
                # Update training result with error
                training_result.status = "failed"
                training_result.error_message = (
                    f"Failed to get or create version for dataset {config.dataset_id}"
                )
                training_result.completed_at = datetime.now()
                await self.training_repo.async_save(training_result)
                return training_result

            # Update version ID in training result
            training_result.version_id = version.version_id
            await self.training_repo.async_save(training_result)

            # Prepare training data
            (
                X_train,
                X_test,
                y_train,
                y_test,
            ) = await self.dataset_processor.prepare_training_data(config)

            if X_train is None:
                # Update training result with error
                training_result.status = "failed"
                training_result.error_message = (
                    f"Failed to prepare training data for dataset {config.dataset_id}"
                )
                training_result.completed_at = datetime.now()
                await self.training_repo.async_save(training_result)
                return training_result

            # Train model
            model = await self._train_model(X_train, y_train, config)

            if model is None:
                # Update training result with error
                training_result.status = "failed"
                training_result.error_message = (
                    f"Failed to train model for agent {config.agent_id}"
                )
                training_result.completed_at = datetime.now()
                await self.training_repo.async_save(training_result)
                return training_result

            # Make predictions
            y_pred = model.predict(X_test)

            # Evaluate model
            metrics = await self.dataset_processor.evaluate_model(
                y_test, y_pred, config.evaluation_metrics
            )

            # Save model
            model_path = f"models/trained/{config.agent_id}_{training_id}.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(model, f)

            # Update training result
            training_result.status = "completed"
            training_result.completed_at = datetime.now()
            training_result.metrics = metrics
            training_result.model_path = model_path
            await self.training_repo.async_save(training_result)

            # Notify agent about training completion
            if self.message_bus:
                await self._notify_agent(config.agent_id, training_result)

            return training_result

        except Exception as e:
            logger.error(f"Error training agent {config.agent_id}: {e}")

            # Update training result with error
            training_result.status = "failed"
            training_result.error_message = str(e)
            training_result.completed_at = datetime.now()
            await self.training_repo.async_save(training_result)

            return training_result

    async def _train_model(
        self, X_train: pd.DataFrame, y_train: pd.Series, config: DatasetTrainingConfig
    ) -> Optional[Any]:
        """
        Train a model for an agent.

        Args:
            X_train: Training features
            y_train: Training labels
            config: Training configuration

        Returns:
            Trained model or None if training failed
        """
        try:
            # Determine if this is a classification or regression task
            unique_values = y_train.nunique()
            is_classification = (
                unique_values < 10
            )  # Heuristic: if fewer than 10 unique values, treat as classification

            # Get model type from config
            model_type = config.training_parameters.get("model_type", "auto")

            if model_type == "auto":
                # Automatically select model based on task type
                if is_classification:
                    if unique_values == 2:
                        model_type = "logistic_regression"
                    else:
                        model_type = "random_forest"
                else:
                    model_type = "linear_regression"

            # Create model based on type
            if model_type == "random_forest":
                if is_classification:
                    model = RandomForestClassifier(
                        n_estimators=config.training_parameters.get(
                            "n_estimators", 100
                        ),
                        max_depth=config.training_parameters.get("max_depth", None),
                        random_state=config.training_parameters.get("random_state", 42),
                    )
                else:
                    model = RandomForestRegressor(
                        n_estimators=config.training_parameters.get(
                            "n_estimators", 100
                        ),
                        max_depth=config.training_parameters.get("max_depth", None),
                        random_state=config.training_parameters.get("random_state", 42),
                    )
            elif model_type == "svm":
                if is_classification:
                    model = SVC(
                        C=config.training_parameters.get("C", 1.0),
                        kernel=config.training_parameters.get("kernel", "rbf"),
                        random_state=config.training_parameters.get("random_state", 42),
                    )
                else:
                    model = SVR(
                        C=config.training_parameters.get("C", 1.0),
                        kernel=config.training_parameters.get("kernel", "rbf"),
                    )
            elif model_type == "neural_network":
                if is_classification:
                    model = MLPClassifier(
                        hidden_layer_sizes=config.training_parameters.get(
                            "hidden_layer_sizes", (100,)
                        ),
                        max_iter=config.training_parameters.get("max_iter", 200),
                        random_state=config.training_parameters.get("random_state", 42),
                    )
                else:
                    model = MLPRegressor(
                        hidden_layer_sizes=config.training_parameters.get(
                            "hidden_layer_sizes", (100,)
                        ),
                        max_iter=config.training_parameters.get("max_iter", 200),
                        random_state=config.training_parameters.get("random_state", 42),
                    )
            elif model_type == "logistic_regression":
                model = LogisticRegression(
                    C=config.training_parameters.get("C", 1.0),
                    max_iter=config.training_parameters.get("max_iter", 100),
                    random_state=config.training_parameters.get("random_state", 42),
                )
            elif model_type == "linear_regression":
                model = LinearRegression()
            else:
                logger.error(f"Unsupported model type: {model_type}")
                return None

            # Train the model
            model.fit(X_train, y_train)

            return model

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return None

    async def _notify_agent(
        self, agent_id: str, training_result: DatasetTrainingResult
    ) -> None:
        """
        Notify an agent about training completion.

        Args:
            agent_id: ID of the agent to notify
            training_result: Training result
        """
        if not self.message_bus:
            return

        try:
            # Create notification message
            message = AgentMessage(
                sender="AgentTrainingPipeline",
                recipient=agent_id,
                message_type="training_completed",
                payload={
                    "training_id": training_result.training_id,
                    "dataset_id": training_result.dataset_id,
                    "version_id": training_result.version_id,
                    "status": training_result.status,
                    "metrics": training_result.metrics,
                    "model_path": training_result.model_path,
                    "completed_at": training_result.completed_at.isoformat()
                    if training_result.completed_at
                    else None,
                },
            )

            # Publish message
            await self.message_bus.publish(message)

        except Exception as e:
            logger.error(f"Error notifying agent {agent_id}: {e}")

    async def get_training_results(self, agent_id: str) -> List[DatasetTrainingResult]:
        """
        Get training results for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of training results
        """
        return await self.training_repo.async_find_results_for_agent(agent_id)

    async def get_training_result(
        self, training_id: str
    ) -> Optional[DatasetTrainingResult]:
        """
        Get a specific training result.

        Args:
            training_id: ID of the training run

        Returns:
            Training result or None if not found
        """
        return await self.training_repo.async_find_by_training_id(training_id)

    async def load_trained_model(self, training_id: str) -> Optional[Any]:
        """
        Load a trained model.

        Args:
            training_id: ID of the training run

        Returns:
            Trained model or None if not found
        """
        try:
            # Get training result
            training_result = await self.training_repo.async_find_by_training_id(
                training_id
            )
            if not training_result or not training_result.model_path:
                return None

            # Load model
            with open(training_result.model_path, "rb") as f:
                model = pickle.load(f)

            return model

        except Exception as e:
            logger.error(f"Error loading trained model: {e}")
            return None
