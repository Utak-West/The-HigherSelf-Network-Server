"""
Pydantic models for Hugging Face Pro integration with Notion.
These models enforce data validation and structure for all Hugging Face API interactions.
"""
from datetime import datetime
from enum import Enum

from pydantic import (Any, BaseModel, Dict, Field, HttpUrl, List, Optional,
                      Union, field_validatorfrom, import, typing)


class ModelType(str, Enum):
    """Types of models available in Hugging Face."""
    TEXT_GENERATION = "text-generation"
    TEXT_CLASSIFICATION = "text-classification"
    TOKEN_CLASSIFICATION = "token-classification"
    QUESTION_ANSWERING = "question-answering"
    ZERO_SHOT_CLASSIFICATION = "zero-shot-classification"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    FEATURE_EXTRACTION = "feature-extraction"
    TEXT_2_TEXT_GENERATION = "text2text-generation"
    FILL_MASK = "fill-mask"
    SENTENCE_SIMILARITY = "sentence-similarity"
    IMAGE_CLASSIFICATION = "image-classification"
    OBJECT_DETECTION = "object-detection"
    IMAGE_SEGMENTATION = "image-segmentation"
    AUDIO_CLASSIFICATION = "audio-classification"
    AUTOMATIC_SPEECH_RECOGNITION = "automatic-speech-recognition"


class SpaceFramework(str, Enum):
    """Supported frameworks for Hugging Face Spaces."""
    GRADIO = "gradio"
    STREAMLIT = "streamlit"
    STATIC = "static"
    DOCKER = "docker"
    JUPYTER = "jupyter"


class NotionHuggingFaceModel(BaseModel):
    """Base model for Notion integration with Hugging Face."""
    notion_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    status: str = "active"
    history_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    def add_to_history(self, action: str, details: Optional[Dict[str, Any]] = None):
        """Add an entry to the history log."""
        log_entry = {
            "timestamp": datetime.now(),
            "action": action,
            "details": details or {}
        }
        self.history_log.append(log_entry)
        self.updated_at = datetime.now()


class HuggingFaceModelReference(NotionHuggingFaceModel):
    """Reference to a Hugging Face model used in Notion."""
    model_id: str
    model_type: ModelType
    model_version: Optional[str] = None
    hub_url: HttpUrl
    inference_endpoint: Optional[str] = None
    quantized: bool = False
    fine_tuned: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
@field_validator('hub_url', mode='before')    def validate_hub_url(cls, v, values):
        """Validate that the hub URL contains the model ID."""
        if 'model_id' in values and values['model_id'] not in v:
            raise ValueError(f"hub_url must contain model_id {values['model_id']}")
        return v


class HuggingFaceSpace(NotionHuggingFaceModel):
    """Hugging Face Space reference for Notion integration."""
    space_id: str
    space_url: HttpUrl
    framework: SpaceFramework
    hardware: str = "cpu-basic"
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    persistent: bool = True
    

class HuggingFaceDataset(NotionHuggingFaceModel):
    """Hugging Face Dataset reference for Notion integration."""
    dataset_id: str
    dataset_url: HttpUrl
    version: Optional[str] = None
    num_rows: Optional[int] = None
    private: bool = True
    format: str = "json"


class AgentToolConfig(BaseModel):
    """Configuration for Hugging Face Agent tools."""
    tool_name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class HuggingFaceAgent(NotionHuggingFaceModel):
    """Hugging Face Agent configuration for Notion integration."""
    base_model_id: str
    tools: List[AgentToolConfig] = Field(default_factory=list)
    memory_enabled: bool = True
    system_prompt: Optional[str] = None
    max_iterations: int = 10
    max_execution_time: int = 60  # seconds
    logging_level: str = "INFO"
