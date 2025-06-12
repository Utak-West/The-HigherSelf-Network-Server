"""
OpenML API Router for The HigherSelf Network Server.

This module provides API endpoints for managing OpenML datasets,
including search, import, processing, and training.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

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
from training.agent_training_pipeline import AgentTrainingPipeline
from training.dataset_processor import DatasetProcessor
from utils.message_bus import MessageBus, get_message_bus

# Initialize router
router = APIRouter(prefix="/openml", tags=["openml"])

# Initialize repositories
metadata_repo = DatasetMetadataRepository()
version_repo = DatasetVersionRepository()
training_repo = DatasetTrainingResultRepository()

# Initialize processor
dataset_processor = DatasetProcessor()


@router.get("/search", response_model=List[DatasetMetadata])
async def search_datasets(
    query: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
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
    datasets = await openml_service.search_datasets(query, tag, limit, offset)
    return datasets


@router.get("/dataset/{dataset_id}", response_model=DatasetMetadata)
async def get_dataset(dataset_id: str):
    """
    Get metadata for a specific dataset.

    Args:
        dataset_id: OpenML dataset ID

    Returns:
        Dataset metadata
    """
    # Try to get from local repository first
    dataset = await metadata_repo.async_find_by_openml_id(dataset_id)

    if not dataset:
        # Get from OpenML
        dataset = await openml_service.get_dataset(dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    return dataset


@router.post("/dataset/{dataset_id}/import", response_model=DatasetMetadata)
async def import_dataset(dataset_id: str):
    """
    Import a dataset from OpenML.

    Args:
        dataset_id: OpenML dataset ID

    Returns:
        Imported dataset metadata
    """
    dataset = await dataset_processor.import_dataset(dataset_id)

    if not dataset:
        raise HTTPException(
            status_code=400, detail=f"Failed to import dataset {dataset_id}"
        )

    return dataset


@router.post("/dataset/{dataset_id}/process", response_model=DatasetVersion)
async def process_dataset(
    dataset_id: str,
    target_column: Optional[str] = None,
    preprocessing_steps: Optional[List[Dict[str, Any]]] = None,
):
    """
    Process a dataset and create a new version.

    Args:
        dataset_id: OpenML dataset ID
        target_column: Name of the target column
        preprocessing_steps: List of preprocessing steps to apply

    Returns:
        Dataset version
    """
    version = await dataset_processor.process_dataset(
        dataset_id, target_column, preprocessing_steps
    )

    if not version:
        raise HTTPException(
            status_code=400, detail=f"Failed to process dataset {dataset_id}"
        )

    return version


@router.get("/dataset/{dataset_id}/versions", response_model=List[DatasetVersion])
async def get_dataset_versions(dataset_id: str):
    """
    Get all versions for a dataset.

    Args:
        dataset_id: OpenML dataset ID

    Returns:
        List of dataset versions
    """
    versions = await version_repo.async_find_versions_for_dataset(dataset_id)
    return versions


@router.get("/version/{version_id}", response_model=DatasetVersion)
async def get_dataset_version(version_id: str):
    """
    Get a specific dataset version.

    Args:
        version_id: Dataset version ID

    Returns:
        Dataset version
    """
    version = await version_repo.async_find_by_version_id(version_id)

    if not version:
        raise HTTPException(status_code=404, detail=f"Version {version_id} not found")

    return version


@router.post("/train", response_model=DatasetTrainingResult)
async def train_agent(
    config: DatasetTrainingConfig,
    background_tasks: BackgroundTasks,
    message_bus: MessageBus = Depends(get_message_bus),
):
    """
    Train an agent using a dataset.

    Args:
        config: Dataset training configuration
        background_tasks: FastAPI background tasks
        message_bus: Message bus for inter-agent communication

    Returns:
        Initial training result (training continues in background)
    """
    # Create training pipeline
    pipeline = AgentTrainingPipeline(message_bus)

    # Create initial training result
    training_id = f"tr-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    training_result = DatasetTrainingResult(
        training_id=training_id,
        dataset_id=config.dataset_id,
        version_id=config.version_id or "",
        agent_id=config.agent_id,
        started_at=datetime.now(),
        status="pending",
    )

    # Save initial training result
    await training_repo.async_save(training_result)

    # Start training in background
    background_tasks.add_task(pipeline.train_agent, config)

    return training_result


@router.get("/training/{training_id}", response_model=DatasetTrainingResult)
async def get_training_result(training_id: str):
    """
    Get a specific training result.

    Args:
        training_id: Training ID

    Returns:
        Training result
    """
    result = await training_repo.async_find_by_training_id(training_id)

    if not result:
        raise HTTPException(
            status_code=404, detail=f"Training result {training_id} not found"
        )

    return result


@router.get("/agent/{agent_id}/training", response_model=List[DatasetTrainingResult])
async def get_agent_training_results(agent_id: str):
    """
    Get all training results for an agent.

    Args:
        agent_id: Agent ID

    Returns:
        List of training results
    """
    results = await training_repo.async_find_results_for_agent(agent_id)
    return results


@router.get("/metrics", response_model=Dict[str, Any])
async def get_openml_service_metrics():
    """
    Get OpenML service metrics.

    Returns:
        Service metrics
    """
    return openml_service.get_metrics()
