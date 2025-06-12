# Hugging Face Agent Integration Guide

This guide explains how to use the enhanced Hugging Face integration with agents in The HigherSelf Network Server.

## Overview

The Hugging Face integration has been optimized to provide intelligent model selection capabilities for all agents in the system. This allows agents to automatically select the most appropriate Hugging Face models for their specific tasks based on their capabilities, the nature of the task, and resource constraints.

Key features:
- Comprehensive model registry with detailed metadata
- Agent-specific model selection based on agent capabilities
- Task-specific model recommendations
- Performance priority options (speed, quality, balanced)
- Easy-to-use agent mixin for quick integration

## Using the Hugging Face Mixin

The simplest way to add Hugging Face capabilities to an agent is to use the `HuggingFaceMixin`:

```python
from agents.base_agent import BaseAgent
from agents.mixins.huggingface_mixin import HuggingFaceMixin
from models.base import AgentCapability, ApiPlatform
from services.ai_router import AIRouter

class MyAgent(BaseAgent, HuggingFaceMixin):
    """An agent with Hugging Face capabilities."""

    def __init__(self, ai_router: AIRouter = None, **kwargs):
        # Initialize base agent
        BaseAgent.__init__(
            self,
            agent_id="my_agent",
            name="My Agent",
            description="An agent with Hugging Face capabilities",
            capabilities=[
                AgentCapability.CONTENT_CREATION,
                AgentCapability.AI_INTEGRATION
            ],
            apis_utilized=[
                ApiPlatform.NOTION,
                ApiPlatform.HUGGINGFACE
            ],
            **kwargs
        )

        # Initialize Hugging Face mixin
        HuggingFaceMixin.__init__(self, ai_router=ai_router)
```

### Setting Up the Mixin

Before using the Hugging Face capabilities, you need to set up the mixin:

```python
# In your agent's initialization or setup method
await self.setup_huggingface(ai_router)
```

### Using Hugging Face Models

The mixin provides several convenience methods for common tasks:

```python
# Summarize text
summary = await self.summarize_text("Long text to summarize...")

# Generate text
generated_text = await self.generate_text("Prompt for text generation...")

# Translate text
translation = await self.translate_text("Text to translate", source_lang="en", target_lang="fr")

# Analyze sentiment
sentiment = await self.analyze_sentiment("Text to analyze sentiment...")

# Answer questions
answer = await self.answer_question("What is the capital of France?", "France is a country in Europe...")
```

### Advanced Usage

For more control, you can use the generic method:

```python
result = await self.get_huggingface_completion(
    task_type="summarize_content",
    content="Text to process",
    language="en",
    performance_priority="balanced"  # Options: "speed", "quality", "balanced"
)
```

## Model Registry

The system includes a comprehensive model registry with detailed metadata about Hugging Face models:

```python
from models.huggingface_model_registry import model_registry

# Get all available tasks
tasks = model_registry.get_all_tasks()

# Get models for a specific task
summarization_models = model_registry.get_models_for_task("summarization")

# Get metadata for a specific model
model_info = model_registry.get_model_metadata("facebook/bart-large-cnn")

# Select the best model for a task
best_model = model_registry.select_model_for_task(
    task="summarization",
    size_preference="medium",
    speed_preference="fast",
    language="en"
)
```

## Agent Model Service

For more advanced use cases, you can use the Agent Model Service directly:

```python
from services.agent_model_service import AgentModelService, AgentModelRequest
from services.ai_router import AIRouter

# Create service
ai_router = AIRouter()
await ai_router.initialize()
agent_model_service = AgentModelService(ai_router=ai_router)

# Create request
request = AgentModelRequest(
    agent_id="my_agent",
    agent_capabilities=[AgentCapability.CONTENT_CREATION],
    task_type="summarize_content",
    content="Text to summarize",
    content_language="en",
    performance_priority="balanced"
)

# Process request
response = await agent_model_service.process_agent_request(request)
print(response.text)
```

## AI Router Integration

The AI Router has been enhanced to automatically select the best provider and model for a given task:

```python
from services.ai_router import AIRouter
from services.ai_providers import AICompletionRequest

# Create router
ai_router = AIRouter()
await ai_router.initialize()

# Create request
request = AICompletionRequest(
    prompt="Summarize the following text: ..."
)

# Get completion (provider and model will be automatically selected)
response = await ai_router.get_completion(request)
print(response.text)
```

## Agent-Specific Model Selection

The system automatically selects models based on agent capabilities:

- Content creation agents get larger, higher-quality models
- Task automation agents get smaller, faster models
- Client communication agents get balanced models

This selection happens automatically when using the Hugging Face mixin.

## Performance Considerations

When selecting models, consider the following:

- Larger models provide better quality but are slower and use more resources
- Smaller models are faster but may produce lower quality results
- For real-time applications, prefer "speed" priority
- For content creation, prefer "quality" priority
- For most use cases, "balanced" priority works well

## Example Implementation

See `examples/huggingface_agent_example.py` for a complete example of an agent using the Hugging Face mixin.

## Supported Tasks

The system supports the following Hugging Face tasks:

- `text-generation`: Generate text from a prompt
- `summarization`: Summarize long texts
- `translation`: Translate between languages
- `sentiment-analysis`: Analyze sentiment of text
- `question-answering`: Answer questions based on context
- `text-classification`: Classify text into categories

Each task has recommended models with different size and speed characteristics.

## Extending the Model Registry

To add new models to the registry, edit `models/huggingface_model_registry.py`:

```python
# In the _initialize_registry method
self._register_model(ModelMetadata(
    id="new-model-id",
    task="task-type",
    description="Model description",
    size_category="medium",
    parameters=100,  # Millions of parameters
    languages=["en"],
    specialties=["area of specialty"],
    limitations=["known limitations"],
    default_parameters={"param": value},
    performance_metrics={"metric": value},
    memory_requirements="2GB",
    inference_speed="fast",
    recommended_for=["use case"],
    not_recommended_for=["use case to avoid"]
))
```
