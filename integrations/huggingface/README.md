# Hugging Face Pro Integration for The HigherSelf Network

This integration connects Hugging Face Pro capabilities with The HigherSelf Network Server, maintaining Notion as the central data hub for all operations as required by The HigherSelf Network standards. The integration is coordinated by the Grace Fields Master Orchestrator to ensure seamless workflow management and business entity awareness.

## Features

- **Notion-Centric Architecture**: All Hugging Face resources are tracked in Notion databases
- **Model Hub Integration**: Access and use over 300,000 ML models
- **Spaces Integration**: Deploy and manage interactive ML applications
- **Dataset Management**: Work with public and private datasets
- **Inference API**: Production-ready model inference endpoints
- **Agent Integration**: Build intelligent AI agents with `smolagents`

## Setup

### 1. Environment Variables

Add the following environment variables to your `.env` file:

```
# Hugging Face Pro Configuration
HF_API_KEY=your_huggingface_pro_api_key
HF_ORGANIZATION=your_organization_name  # Optional
HF_DEFAULT_MODEL_ID=your_default_model  # Optional

# Notion Integration for Hugging Face
NOTION_HF_DATABASE_ID=your_notion_database_id
NOTION_HF_SYNC_INTERVAL=60  # Minutes between auto-syncs
NOTION_HF_HISTORY_LOG=true  # Enable detailed history logging

# Optional: Custom Inference Endpoints
HF_ENDPOINT_text=your-text-inference-endpoint
HF_ENDPOINT_image=your-image-inference-endpoint
```

### 2. Notion Database Setup

Create a Notion database with the following properties:

#### For Models:
- `Name` (Title)
- `Model ID` (Text)
- `Type` (Select: text-generation, image-generation, etc.)
- `Description` (Text)
- `Status` (Select: active, inactive, etc.)
- `URL` (URL)
- `Tags` (Multi-select)
- `Last Updated` (Date)

#### For Spaces:
- `Name` (Title)
- `Space ID` (Text)
- `Framework` (Select: gradio, streamlit, etc.)
- `Description` (Text)
- `Status` (Select: active, inactive, etc.)
- `URL` (URL)
- `Hardware` (Select: cpu-basic, gpu-t4, etc.)
- `Tags` (Multi-select)
- `Last Updated` (Date)
- `Persistent` (Checkbox)

#### For Agents:
- `Name` (Title)
- `Base Model` (Text)
- `Description` (Text)
- `Status` (Select: active, inactive, etc.)
- `Tools` (Multi-select)
- `Memory Enabled` (Checkbox)
- `Max Iterations` (Number)
- `Last Updated` (Date)
- `History Log` (Text)

## Usage

### Initialize the Hugging Face Service

```python
from integrations.huggingface.utils import create_huggingface_service
from agents.agent_personalities import create_grace_orchestrator
from services.notion_service import get_notion_client

# Get Notion client
notion_client = get_notion_client()

# Create Grace Fields orchestrator
grace_fields = create_grace_orchestrator(notion_client)

# Create service instance
hf = create_huggingface_service()

# Register with Grace Fields
await grace_fields.register_service("huggingface", hf)

# List available models
models = hf.list_models({"search": "text-generation", "limit": 10})
print(f"Found {len(models)} models")

# Run inference through Grace Fields for proper business entity routing
result = await grace_fields.route_event("huggingface_inference", {
    "model_id": "gpt2",
    "inputs": "The HigherSelf Network is",
    "parameters": {"max_length": 50},
    "business_entity_id": "connection_practice"
})
print(result)
```

### Integration with Notion

```python
from services.notion_service import get_notion_client
from integrations.huggingface.utils import create_notion_sync

# Get Notion client
notion_client = get_notion_client()

# Create Notion sync instance
notion_sync = create_notion_sync(notion_client)

# Sync models and spaces
notion_sync.full_sync()

# Get models from Notion
models = notion_sync.get_models_from_notion()
print(f"Found {len(models)} models in Notion")
```

## API Endpoints

The integration provides the following FastAPI endpoints:

- `GET /huggingface/models` - List available models
- `GET /huggingface/models/{model_id}` - Get model details
- `POST /huggingface/models/notion` - Sync a model to Notion
- `GET /huggingface/spaces` - List available spaces
- `POST /huggingface/spaces/notion` - Sync a space to Notion
- `POST /huggingface/inference` - Run model inference
- `POST /huggingface/notion/sync` - Run a full sync with Notion

## Roadmap

- Add support for model fine-tuning
- Implement dataset synchronization
- Create custom agent workflows
- Add monitoring and analytics for Hugging Face resources
