# OpenML Integration Guide

This guide explains how to use OpenML datasets to enhance AI agent training in The HigherSelf Network Server.

## Overview

The HigherSelf Network Server now integrates with [OpenML](https://www.openml.org/), a platform for sharing and organizing datasets and machine learning workflows. This integration enables:

1. **Data-Driven Agent Training**: Access to high-quality, diverse datasets to improve agent capabilities
2. **Specialized Domain Knowledge**: Datasets tailored to each agent's specific domain
3. **Performance Evaluation**: Metrics to measure improvements in agent performance
4. **Continuous Learning**: Regular updates with new datasets to keep agents current

## Architecture

The OpenML integration consists of several components:

1. **OpenML Service**: Core service for interacting with the OpenML API
2. **Dataset Models**: Pydantic models for dataset metadata and versioning
3. **Dataset Repository**: MongoDB storage for dataset metadata and training results
4. **Dataset Processor**: Utilities for preprocessing datasets
5. **Agent Training Pipeline**: Framework for training agents with datasets
6. **API Endpoints**: RESTful API for managing datasets and training

## Getting Started

### Prerequisites

- The HigherSelf Network Server with Redis and MongoDB configured
- Python packages: `pandas`, `numpy`, `scikit-learn`

### Basic Usage

#### 1. Search for Datasets

```python
from services.openml_service import openml_service

# Search for classification datasets
datasets = await openml_service.search_datasets(tag="classification", limit=5)
for dataset in datasets:
    print(f"Dataset {dataset.dataset_id}: {dataset.name} ({dataset.row_count} rows)")
```

#### 2. Import a Dataset

```python
from training.dataset_processor import DatasetProcessor

processor = DatasetProcessor()
dataset = await processor.import_dataset("40945")  # Titanic dataset
```

#### 3. Process a Dataset

```python
# Process the dataset with default preprocessing
version = await processor.process_dataset(
    dataset_id="40945",
    target_column="survived"
)
```

#### 4. Train an Agent

```python
from models.dataset_models import DatasetTrainingConfig
from training.agent_training_pipeline import AgentTrainingPipeline

# Create training configuration
config = DatasetTrainingConfig(
    dataset_id="40945",  # Titanic dataset
    agent_id="nyra_lead_capture_agent",
    evaluation_metrics=["accuracy", "precision", "recall", "f1"],
    training_parameters={
        "model_type": "random_forest",
        "n_estimators": 100,
        "test_size": 0.2
    }
)

# Train the agent
pipeline = AgentTrainingPipeline()
result = await pipeline.train_agent(config)
```

## API Endpoints

The OpenML integration provides the following API endpoints:

### Dataset Management

- `GET /openml/search`: Search for datasets on OpenML
- `GET /openml/dataset/{dataset_id}`: Get metadata for a specific dataset
- `POST /openml/dataset/{dataset_id}/import`: Import a dataset from OpenML
- `POST /openml/dataset/{dataset_id}/process`: Process a dataset and create a new version
- `GET /openml/dataset/{dataset_id}/versions`: Get all versions for a dataset
- `GET /openml/version/{version_id}`: Get a specific dataset version

### Agent Training

- `POST /openml/train`: Train an agent using a dataset
- `GET /openml/training/{training_id}`: Get a specific training result
- `GET /openml/agent/{agent_id}/training`: Get all training results for an agent

## Agent-Specific Datasets

Each agent in The HigherSelf Network Server can benefit from specific types of datasets:

### Grace Fields (Orchestrator)

- **Multi-label classification datasets**: For event routing decisions
- **Time series datasets**: For workflow orchestration timing
- **Graph datasets**: For understanding agent relationships

### Nyra (Lead Capture Agent)

- **Classification datasets**: For lead qualification
- **Customer segmentation datasets**: For lead categorization
- **Conversion prediction datasets**: For lead scoring

### Solari (Booking Agent)

- **Time series datasets**: For booking pattern analysis
- **Regression datasets**: For pricing optimization
- **Classification datasets**: For booking type prediction

### Ruvo (Task Management Agent)

- **Task prioritization datasets**: For task scheduling
- **Resource allocation datasets**: For task assignment
- **Time estimation datasets**: For task duration prediction

### Liora (Marketing Campaign Agent)

- **Customer response datasets**: For campaign effectiveness prediction
- **A/B testing datasets**: For message optimization
- **Engagement datasets**: For timing optimization

### Sage (Community Engagement Agent)

- **Sentiment analysis datasets**: For community sentiment tracking
- **Topic modeling datasets**: For discussion categorization
- **User engagement datasets**: For community health metrics

### Elan (Content Lifecycle Agent)

- **Content performance datasets**: For content effectiveness prediction
- **Topic classification datasets**: For content categorization
- **Engagement prediction datasets**: For content scheduling

### Zevi (Audience Segmentation Agent)

- **Customer segmentation datasets**: For audience clustering
- **Behavioral datasets**: For user pattern recognition
- **Demographic datasets**: For segment characterization

## Training Workflow

The recommended workflow for training agents with OpenML datasets is:

1. **Search** for relevant datasets based on the agent's domain
2. **Import** the selected datasets into the system
3. **Process** the datasets with appropriate preprocessing steps
4. **Configure** training parameters for each agent
5. **Train** the agents using the processed datasets
6. **Evaluate** the results using the provided metrics
7. **Deploy** the improved agent models

## Conclusion

The OpenML integration provides a powerful framework for enhancing AI agent capabilities in The HigherSelf Network Server. By leveraging high-quality, diverse datasets, agents can continuously improve their performance in specialized domains, leading to more effective automation and better business outcomes.
