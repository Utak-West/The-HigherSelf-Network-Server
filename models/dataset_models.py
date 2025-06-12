"""
Dataset models for The HigherSelf Network Server.

This module provides Pydantic models for dataset metadata, versioning,
and processing. These models are used for data validation and structured
interaction with the OpenML API and MongoDB.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    """
    Metadata for a dataset from OpenML.
    """

    dataset_id: str = Field(..., description="OpenML dataset ID")
    name: str = Field(..., description="Dataset name")
    description: str = Field("", description="Dataset description")
    format: str = Field("", description="Dataset format (e.g., ARFF, CSV)")
    creator: str = Field("", description="Dataset creator")
    contributor: str = Field("", description="Dataset contributor")
    collection_date: str = Field("", description="Date when data was collected")
    upload_date: str = Field("", description="Date when dataset was uploaded to OpenML")
    language: str = Field("", description="Dataset language")
    licence: str = Field("", description="Dataset license")
    url: str = Field("", description="URL to download the dataset")
    default_target_attribute: str = Field(
        "", description="Default target attribute/column"
    )
    row_count: int = Field(0, description="Number of instances/rows")
    feature_count: int = Field(0, description="Number of features/columns")
    tags: List[str] = Field(default_factory=list, description="Dataset tags")

    # Local tracking fields
    imported_at: Optional[datetime] = Field(
        None, description="When the dataset was imported"
    )
    last_used: Optional[datetime] = Field(
        None, description="When the dataset was last used"
    )
    usage_count: int = Field(0, description="Number of times the dataset was used")

    class Config:
        schema_extra = {
            "example": {
                "dataset_id": "40945",
                "name": "Titanic",
                "description": "Titanic dataset for survival prediction",
                "format": "ARFF",
                "creator": "Frank Kane",
                "contributor": "OpenML",
                "collection_date": "1912",
                "upload_date": "2019-06-26",
                "language": "English",
                "licence": "Public",
                "url": "https://www.openml.org/data/download/40945/titanic.arff",
                "default_target_attribute": "survived",
                "row_count": 1309,
                "feature_count": 14,
                "tags": ["titanic", "classification", "binary"],
                "imported_at": "2023-06-01T12:00:00",
                "last_used": "2023-06-02T15:30:00",
                "usage_count": 5,
            }
        }


class DatasetVersion(BaseModel):
    """
    Version information for a dataset.
    """

    version_id: str = Field(
        default_factory=lambda: f"v-{uuid4().hex[:8]}", description="Version ID"
    )
    dataset_id: str = Field(..., description="OpenML dataset ID")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Version creation timestamp"
    )
    preprocessing_steps: List[Dict[str, Any]] = Field(
        default_factory=list, description="Preprocessing steps applied"
    )
    feature_columns: List[str] = Field(
        default_factory=list, description="Feature column names"
    )
    target_column: Optional[str] = Field(None, description="Target column name")
    file_path: str = Field(..., description="Path to the processed dataset file")
    format: str = Field("csv", description="File format")
    row_count: int = Field(0, description="Number of rows after preprocessing")
    feature_count: int = Field(0, description="Number of features after preprocessing")

    class Config:
        schema_extra = {
            "example": {
                "version_id": "v-a1b2c3d4",
                "dataset_id": "40945",
                "created_at": "2023-06-01T12:00:00",
                "preprocessing_steps": [
                    {"type": "drop_na", "params": {}},
                    {"type": "encode_categorical", "params": {}},
                ],
                "feature_columns": [
                    "pclass",
                    "sex",
                    "age",
                    "sibsp",
                    "parch",
                    "fare",
                    "embarked",
                ],
                "target_column": "survived",
                "file_path": "data/processed/titanic_v-a1b2c3d4.csv",
                "format": "csv",
                "row_count": 1200,
                "feature_count": 7,
            }
        }


class ProcessedDataset(BaseModel):
    """
    Information about a processed dataset ready for agent training.
    """

    dataset_id: str = Field(..., description="OpenML dataset ID")
    name: str = Field(..., description="Dataset name")
    description: str = Field("", description="Dataset description")
    processed_at: datetime = Field(
        default_factory=datetime.now, description="Processing timestamp"
    )
    preprocessing_steps: List[Dict[str, Any]] = Field(
        default_factory=list, description="Preprocessing steps applied"
    )
    feature_columns: List[str] = Field(
        default_factory=list, description="Feature column names"
    )
    target_column: Optional[str] = Field(None, description="Target column name")
    row_count: int = Field(0, description="Number of rows after preprocessing")
    feature_count: int = Field(0, description="Number of features after preprocessing")
    sample_data: List[Dict[str, Any]] = Field(
        default_factory=list, description="Sample rows from the dataset"
    )

    class Config:
        schema_extra = {
            "example": {
                "dataset_id": "40945",
                "name": "Titanic",
                "description": "Titanic dataset for survival prediction",
                "processed_at": "2023-06-01T12:00:00",
                "preprocessing_steps": [
                    {"type": "drop_na", "params": {}},
                    {"type": "encode_categorical", "params": {}},
                ],
                "feature_columns": [
                    "pclass",
                    "sex",
                    "age",
                    "sibsp",
                    "parch",
                    "fare",
                    "embarked",
                ],
                "target_column": "survived",
                "row_count": 1200,
                "feature_count": 7,
                "sample_data": [
                    {
                        "pclass": 1,
                        "sex": 0,
                        "age": 22,
                        "sibsp": 1,
                        "parch": 0,
                        "fare": 7.25,
                        "embarked": 2,
                        "survived": 0,
                    },
                    {
                        "pclass": 1,
                        "sex": 1,
                        "age": 38,
                        "sibsp": 1,
                        "parch": 0,
                        "fare": 71.28,
                        "embarked": 0,
                        "survived": 1,
                    },
                ],
            }
        }


class DatasetTrainingConfig(BaseModel):
    """
    Configuration for training an agent with a dataset.
    """

    dataset_id: str = Field(..., description="OpenML dataset ID")
    version_id: Optional[str] = Field(
        None, description="Dataset version ID (if None, uses latest)"
    )
    agent_id: str = Field(..., description="ID of the agent to train")
    target_column: Optional[str] = Field(None, description="Target column to predict")
    feature_columns: Optional[List[str]] = Field(
        None, description="Feature columns to use (if None, uses all)"
    )
    training_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Training parameters"
    )
    evaluation_metrics: List[str] = Field(
        default_factory=list, description="Metrics to evaluate"
    )

    class Config:
        schema_extra = {
            "example": {
                "dataset_id": "40945",
                "version_id": "v-a1b2c3d4",
                "agent_id": "ruvo_task_agent",
                "target_column": "survived",
                "feature_columns": ["pclass", "sex", "age", "fare", "embarked"],
                "training_parameters": {
                    "epochs": 10,
                    "batch_size": 32,
                    "learning_rate": 0.001,
                },
                "evaluation_metrics": ["accuracy", "precision", "recall", "f1"],
            }
        }


class DatasetTrainingResult(BaseModel):
    """
    Results from training an agent with a dataset.
    """

    training_id: str = Field(
        default_factory=lambda: f"tr-{uuid4().hex[:8]}", description="Training ID"
    )
    dataset_id: str = Field(..., description="OpenML dataset ID")
    version_id: str = Field(..., description="Dataset version ID")
    agent_id: str = Field(..., description="ID of the trained agent")
    started_at: datetime = Field(
        default_factory=datetime.now, description="Training start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        None, description="Training completion timestamp"
    )
    status: str = Field("pending", description="Training status")
    metrics: Dict[str, float] = Field(
        default_factory=dict, description="Evaluation metrics"
    )
    model_path: Optional[str] = Field(None, description="Path to the trained model")
    error_message: Optional[str] = Field(
        None, description="Error message if training failed"
    )

    class Config:
        schema_extra = {
            "example": {
                "training_id": "tr-a1b2c3d4",
                "dataset_id": "40945",
                "version_id": "v-a1b2c3d4",
                "agent_id": "ruvo_task_agent",
                "started_at": "2023-06-01T12:00:00",
                "completed_at": "2023-06-01T12:05:30",
                "status": "completed",
                "metrics": {
                    "accuracy": 0.85,
                    "precision": 0.82,
                    "recall": 0.79,
                    "f1": 0.80,
                },
                "model_path": "models/ruvo_task_agent_tr-a1b2c3d4.pkl",
                "error_message": None,
            }
        }
