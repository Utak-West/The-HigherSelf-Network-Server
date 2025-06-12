"""
OpenML Service for The HigherSelf Network Server.

This service provides integration with the OpenML platform for accessing
high-quality datasets to train AI agents. It handles dataset search,
download, and preprocessing.

Features:
- Dataset search by name, tag, or ID
- Dataset download and caching
- Dataset preprocessing for agent training
- Integration with Redis for caching
- Integration with MongoDB for dataset metadata storage
"""

import asyncio
import json
import os
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import requests
from loguru import logger
from pydantic import BaseModel

from models.dataset_models import (DatasetMetadata, DatasetVersion,
                                   ProcessedDataset)
from services.redis_service import redis_service


class OpenMLService:
    """Service for interacting with the OpenML platform."""

    def __init__(self, cache_ttl: int = 86400):
        """
        Initialize the OpenML service.

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 day)
        """
        self.base_url = "https://www.openml.org/api/v1"
        self.cache_ttl = cache_ttl
        self.cache_prefix = "openml:dataset:"
        self._metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "processing_time_sum": 0,
            "processing_count": 0,
        }

    async def search_datasets(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[DatasetMetadata]:
        """
        Search for datasets on OpenML.

        Args:
            query: Search query string
            tag: Filter by tag
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of dataset metadata
        """
        # Build cache key
        cache_key = (
            f"{self.cache_prefix}search:{query or ''}:{tag or ''}:{limit}:{offset}"
        )

        # Try to get from cache
        cached_result = await redis_service.async_get(cache_key, as_json=True)
        if cached_result:
            self._metrics["cache_hits"] += 1
            return [DatasetMetadata(**item) for item in cached_result]

        self._metrics["cache_misses"] += 1

        # Build query parameters
        params = {"limit": limit, "offset": offset, "status": "active"}

        if query:
            params["q"] = query

        if tag:
            params["tag"] = tag

        # Make API request
        try:
            start_time = time.time()
            self._metrics["api_calls"] += 1

            response = requests.get(f"{self.base_url}/data/list", params=params)
            response.raise_for_status()
            data = response.json()

            # Process results
            datasets = []
            for item in data.get("data", {}).get("dataset", []):
                try:
                    dataset = DatasetMetadata(
                        dataset_id=item.get("did", ""),
                        name=item.get("name", ""),
                        description=item.get("description", ""),
                        format=item.get("format", ""),
                        creator=item.get("creator", ""),
                        contributor=item.get("contributor", ""),
                        collection_date=item.get("collection_date", ""),
                        upload_date=item.get("upload_date", ""),
                        language=item.get("language", ""),
                        licence=item.get("licence", ""),
                        url=item.get("url", ""),
                        default_target_attribute=item.get(
                            "default_target_attribute", ""
                        ),
                        row_count=int(item.get("NumberOfInstances", 0)),
                        feature_count=int(item.get("NumberOfFeatures", 0)),
                        tags=(
                            item.get("tags", {}).get("tag", [])
                            if isinstance(item.get("tags", {}), dict)
                            else []
                        ),
                    )
                    datasets.append(dataset)
                except Exception as e:
                    logger.warning(f"Error processing dataset metadata: {e}")

            # Cache results
            await redis_service.async_set(
                cache_key, [dataset.dict() for dataset in datasets], ex=self.cache_ttl
            )

            # Update metrics
            self._metrics["processing_time_sum"] += time.time() - start_time
            self._metrics["processing_count"] += 1

            return datasets

        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Error searching OpenML datasets: {e}")
            return []

    async def get_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """
        Get metadata for a specific dataset.

        Args:
            dataset_id: OpenML dataset ID

        Returns:
            Dataset metadata or None if not found
        """
        # Build cache key
        cache_key = f"{self.cache_prefix}metadata:{dataset_id}"

        # Try to get from cache
        cached_result = await redis_service.async_get(cache_key, as_json=True)
        if cached_result:
            self._metrics["cache_hits"] += 1
            return DatasetMetadata(**cached_result)

        self._metrics["cache_misses"] += 1

        # Make API request
        try:
            start_time = time.time()
            self._metrics["api_calls"] += 1

            response = requests.get(f"{self.base_url}/data/{dataset_id}")
            response.raise_for_status()
            data = response.json()

            # Process result
            dataset_info = data.get("data_set_description", {})

            dataset = DatasetMetadata(
                dataset_id=dataset_info.get("id", ""),
                name=dataset_info.get("name", ""),
                description=dataset_info.get("description", ""),
                format=dataset_info.get("format", ""),
                creator=dataset_info.get("creator", ""),
                contributor=dataset_info.get("contributor", ""),
                collection_date=dataset_info.get("collection_date", ""),
                upload_date=dataset_info.get("upload_date", ""),
                language=dataset_info.get("language", ""),
                licence=dataset_info.get("licence", ""),
                url=dataset_info.get("url", ""),
                default_target_attribute=dataset_info.get(
                    "default_target_attribute", ""
                ),
                row_count=int(dataset_info.get("number_of_instances", 0)),
                feature_count=int(dataset_info.get("number_of_features", 0)),
                tags=(
                    dataset_info.get("tag", [])
                    if isinstance(dataset_info.get("tag"), list)
                    else []
                ),
            )

            # Cache result
            await redis_service.async_set(cache_key, dataset.dict(), ex=self.cache_ttl)

            # Update metrics
            self._metrics["processing_time_sum"] += time.time() - start_time
            self._metrics["processing_count"] += 1

            return dataset

        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Error getting OpenML dataset {dataset_id}: {e}")
            return None

    async def download_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """
        Download a dataset from OpenML.

        Args:
            dataset_id: OpenML dataset ID

        Returns:
            Pandas DataFrame containing the dataset or None if download failed
        """
        # Get dataset metadata to find download URL
        dataset_meta = await self.get_dataset(dataset_id)
        if not dataset_meta:
            return None

        # Build cache key for the data
        cache_key = f"{self.cache_prefix}data:{dataset_id}"

        # Try to get from cache (as a file path)
        cached_path = await redis_service.async_get(cache_key)
        if cached_path and os.path.exists(cached_path):
            self._metrics["cache_hits"] += 1
            try:
                return pd.read_csv(cached_path)
            except Exception as e:
                logger.warning(f"Error reading cached dataset: {e}")
                # Continue to download if cache read fails

        self._metrics["cache_misses"] += 1

        # Make API request to get the data file URL
        try:
            start_time = time.time()
            self._metrics["api_calls"] += 1

            # Get the dataset download URL
            data_url = dataset_meta.url
            if not data_url:
                response = requests.get(f"{self.base_url}/data/features/{dataset_id}")
                response.raise_for_status()
                data = response.json()
                data_url = data.get("data_features", {}).get("url", "")

            if not data_url:
                logger.error(f"No download URL found for dataset {dataset_id}")
                return None

            # Download the data file
            response = requests.get(data_url)
            response.raise_for_status()

            # Save to a temporary file
            os.makedirs("data/openml", exist_ok=True)
            file_path = f"data/openml/dataset_{dataset_id}.csv"

            with open(file_path, "wb") as f:
                f.write(response.content)

            # Cache the file path
            await redis_service.async_set(cache_key, file_path, ex=self.cache_ttl)

            # Load the dataset
            df = pd.read_csv(file_path)

            # Update metrics
            self._metrics["processing_time_sum"] += time.time() - start_time
            self._metrics["processing_count"] += 1

            return df

        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Error downloading OpenML dataset {dataset_id}: {e}")
            return None

    async def preprocess_dataset(
        self,
        dataset_id: str,
        target_column: Optional[str] = None,
        preprocessing_steps: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[ProcessedDataset]:
        """
        Preprocess a dataset for agent training.

        Args:
            dataset_id: OpenML dataset ID
            target_column: Name of the target column (if None, uses default_target_attribute)
            preprocessing_steps: List of preprocessing steps to apply

        Returns:
            Processed dataset or None if processing failed
        """
        # Download the dataset
        df = await self.download_dataset(dataset_id)
        if df is None:
            return None

        # Get dataset metadata
        dataset_meta = await self.get_dataset(dataset_id)
        if not dataset_meta:
            return None

        # Determine target column
        if not target_column:
            target_column = dataset_meta.default_target_attribute

        # Apply preprocessing steps
        try:
            start_time = time.time()

            # Default preprocessing if none specified
            if not preprocessing_steps:
                preprocessing_steps = [
                    {"type": "drop_na", "params": {}},
                    {"type": "encode_categorical", "params": {}},
                ]

            # Apply each preprocessing step
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
                elif step_type == "custom":
                    # Custom preprocessing function would be applied here
                    pass

            # Create processed dataset
            processed = ProcessedDataset(
                dataset_id=dataset_id,
                name=dataset_meta.name,
                description=dataset_meta.description,
                processed_at=datetime.now(),
                preprocessing_steps=preprocessing_steps,
                feature_columns=[col for col in df.columns if col != target_column],
                target_column=target_column,
                row_count=len(df),
                feature_count=(
                    len(df.columns) - 1
                    if target_column in df.columns
                    else len(df.columns)
                ),
                sample_data=df.head(5).to_dict(orient="records"),
            )

            # Update metrics
            self._metrics["processing_time_sum"] += time.time() - start_time
            self._metrics["processing_count"] += 1

            return processed

        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Error preprocessing OpenML dataset {dataset_id}: {e}")
            return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        metrics = self._metrics.copy()

        # Calculate average processing time
        if metrics["processing_count"] > 0:
            metrics["avg_processing_time"] = (
                metrics["processing_time_sum"] / metrics["processing_count"]
            )
        else:
            metrics["avg_processing_time"] = 0

        return metrics


# Singleton instance
openml_service = OpenMLService()
