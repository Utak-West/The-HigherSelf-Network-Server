"""
Hugging Face Model Registry

This module provides a comprehensive registry of Hugging Face models with metadata
and intelligent model selection capabilities for The HigherSelf Network Server.
"""

from typing import Dict, List, Any, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field
import json
import os
from loguru import logger

class ModelMetadata(BaseModel):
    """Detailed metadata about a Hugging Face model."""
    id: str = Field(..., description="Hugging Face model ID")
    task: str = Field(..., description="Primary task the model is designed for")
    description: str = Field(..., description="Human-readable description")
    size_category: str = Field("medium", description="Size category: tiny, small, medium, large, xlarge")
    parameters: Optional[int] = Field(None, description="Number of parameters (millions)")
    languages: List[str] = Field(default_factory=lambda: ["en"], description="Supported languages")
    specialties: List[str] = Field(default_factory=list, description="Areas where this model excels")
    limitations: List[str] = Field(default_factory=list, description="Known limitations")
    default_parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters for this model")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics on benchmarks")
    
    # Resource requirements
    memory_requirements: Optional[str] = Field(None, description="Estimated memory requirements")
    inference_speed: Optional[str] = Field(None, description="Inference speed category: fast, medium, slow")
    
    # Usage information
    recommended_for: List[str] = Field(default_factory=list, description="Recommended use cases")
    not_recommended_for: List[str] = Field(default_factory=list, description="Use cases to avoid")


class HuggingFaceModelRegistry:
    """
    Registry of Hugging Face models with metadata and selection capabilities.
    Provides intelligent model selection based on task requirements.
    """
    
    def __init__(self):
        """Initialize the model registry with predefined models."""
        self.models: Dict[str, ModelMetadata] = {}
        self.task_to_models: Dict[str, List[str]] = {}
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize the registry with predefined models and their metadata."""
        # Text Generation Models
        self._register_model(ModelMetadata(
            id="gpt2",
            task="text-generation",
            description="OpenAI GPT-2 model for text generation",
            size_category="medium",
            parameters=124,
            languages=["en"],
            specialties=["creative writing", "completion"],
            limitations=["outdated knowledge", "no instruction following"],
            default_parameters={"temperature": 0.7, "max_length": 100, "top_p": 0.9},
            performance_metrics={"perplexity": 35.13},
            memory_requirements="2GB",
            inference_speed="fast",
            recommended_for=["creative content", "simple completions"],
            not_recommended_for=["factual QA", "reasoning"]
        ))
        
        self._register_model(ModelMetadata(
            id="distilgpt2",
            task="text-generation",
            description="Distilled version of GPT-2",
            size_category="small",
            parameters=82,
            languages=["en"],
            specialties=["efficient text generation"],
            limitations=["lower quality than full GPT-2", "outdated knowledge"],
            default_parameters={"temperature": 0.7, "max_length": 100, "top_p": 0.9},
            performance_metrics={"perplexity": 37.2},
            memory_requirements="1GB",
            inference_speed="very fast",
            recommended_for=["resource-constrained environments", "simple completions"],
            not_recommended_for=["complex generation", "factual QA"]
        ))
        
        self._register_model(ModelMetadata(
            id="EleutherAI/gpt-neo-1.3B",
            task="text-generation",
            description="GPT-Neo 1.3B parameters model",
            size_category="large",
            parameters=1300,
            languages=["en"],
            specialties=["creative writing", "longer completions"],
            limitations=["resource intensive", "outdated knowledge"],
            default_parameters={"temperature": 0.7, "max_length": 200, "top_p": 0.9},
            performance_metrics={"perplexity": 18.5},
            memory_requirements="5GB",
            inference_speed="medium",
            recommended_for=["creative content", "longer text generation"],
            not_recommended_for=["mobile applications", "real-time generation"]
        ))
        
        # Summarization Models
        self._register_model(ModelMetadata(
            id="facebook/bart-large-cnn",
            task="summarization",
            description="BART model fine-tuned on CNN Daily Mail",
            size_category="large",
            parameters=406,
            languages=["en"],
            specialties=["news summarization", "article summarization"],
            limitations=["struggles with very technical content"],
            default_parameters={"min_length": 30, "max_length": 100},
            performance_metrics={"rouge-1": 44.16, "rouge-2": 21.28, "rouge-l": 40.90},
            memory_requirements="3GB",
            inference_speed="medium",
            recommended_for=["news articles", "blog posts", "general content"],
            not_recommended_for=["very short texts", "highly technical documents"]
        ))
        
        self._register_model(ModelMetadata(
            id="sshleifer/distilbart-cnn-12-6",
            task="summarization",
            description="Distilled BART for summarization",
            size_category="medium",
            parameters=306,
            languages=["en"],
            specialties=["efficient summarization"],
            limitations=["lower quality than full BART"],
            default_parameters={"min_length": 30, "max_length": 100},
            performance_metrics={"rouge-1": 42.76, "rouge-2": 19.87, "rouge-l": 39.11},
            memory_requirements="2GB",
            inference_speed="fast",
            recommended_for=["efficient summarization", "resource-constrained environments"],
            not_recommended_for=["premium content summarization"]
        ))
        
        # Translation Models
        self._register_model(ModelMetadata(
            id="Helsinki-NLP/opus-mt-en-fr",
            task="translation",
            description="English to French translation",
            size_category="medium",
            parameters=77,
            languages=["en", "fr"],
            specialties=["English to French translation"],
            limitations=["struggles with idiomatic expressions"],
            default_parameters={},
            performance_metrics={"bleu": 38.5},
            memory_requirements="1GB",
            inference_speed="fast",
            recommended_for=["general English to French translation"],
            not_recommended_for=["literary translation", "highly technical content"]
        ))
        
        self._register_model(ModelMetadata(
            id="Helsinki-NLP/opus-mt-en-es",
            task="translation",
            description="English to Spanish translation",
            size_category="medium",
            parameters=77,
            languages=["en", "es"],
            specialties=["English to Spanish translation"],
            limitations=["struggles with idiomatic expressions"],
            default_parameters={},
            performance_metrics={"bleu": 39.2},
            memory_requirements="1GB",
            inference_speed="fast",
            recommended_for=["general English to Spanish translation"],
            not_recommended_for=["literary translation", "highly technical content"]
        ))
        
        # Sentiment Analysis Models
        self._register_model(ModelMetadata(
            id="distilbert-base-uncased-finetuned-sst-2-english",
            task="sentiment-analysis",
            description="DistilBERT fine-tuned for sentiment",
            size_category="small",
            parameters=66,
            languages=["en"],
            specialties=["binary sentiment classification"],
            limitations=["only positive/negative, no nuance"],
            default_parameters={},
            performance_metrics={"accuracy": 91.3},
            memory_requirements="1GB",
            inference_speed="very fast",
            recommended_for=["customer feedback analysis", "review sentiment"],
            not_recommended_for=["nuanced emotion detection", "multi-class sentiment"]
        ))
        
        # Question Answering Models
        self._register_model(ModelMetadata(
            id="deepset/roberta-base-squad2",
            task="question-answering",
            description="RoBERTa fine-tuned on SQuAD2",
            size_category="medium",
            parameters=125,
            languages=["en"],
            specialties=["extractive QA"],
            limitations=["requires context passage", "no generative answers"],
            default_parameters={},
            performance_metrics={"f1": 79.97, "exact_match": 72.4},
            memory_requirements="2GB",
            inference_speed="medium",
            recommended_for=["extractive QA", "information retrieval"],
            not_recommended_for=["open-ended questions", "questions without context"]
        ))
        
        self._register_model(ModelMetadata(
            id="distilbert-base-cased-distilled-squad",
            task="question-answering",
            description="Distilled BERT for QA",
            size_category="small",
            parameters=65,
            languages=["en"],
            specialties=["efficient extractive QA"],
            limitations=["lower accuracy than larger models", "requires context passage"],
            default_parameters={},
            performance_metrics={"f1": 77.7, "exact_match": 68.8},
            memory_requirements="1GB",
            inference_speed="fast",
            recommended_for=["resource-constrained QA", "mobile applications"],
            not_recommended_for=["high-stakes QA", "complex questions"]
        ))
    
    def _register_model(self, model_metadata: ModelMetadata):
        """Register a model with its metadata."""
        model_id = model_metadata.id
        self.models[model_id] = model_metadata
        
        # Add to task mapping
        task = model_metadata.task
        if task not in self.task_to_models:
            self.task_to_models[task] = []
        self.task_to_models[task].append(model_id)
    
    def get_model_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """Get metadata for a specific model."""
        return self.models.get(model_id)
    
    def get_models_for_task(self, task: str) -> List[ModelMetadata]:
        """Get all models suitable for a specific task."""
        model_ids = self.task_to_models.get(task, [])
        return [self.models[model_id] for model_id in model_ids]
    
    def select_model_for_task(self, task: str, 
                              size_preference: str = "medium",
                              speed_preference: str = "medium",
                              language: str = "en") -> Optional[ModelMetadata]:
        """
        Select the best model for a specific task based on preferences.
        
        Args:
            task: The task to perform
            size_preference: Preferred model size (tiny, small, medium, large, xlarge)
            speed_preference: Preferred inference speed (fast, medium, slow)
            language: Preferred language
            
        Returns:
            Best matching model metadata or None if no suitable model found
        """
        models = self.get_models_for_task(task)
        if not models:
            return None
        
        # Filter by language
        models = [m for m in models if language in m.languages]
        if not models:
            return None
        
        # Score models based on preferences
        size_ranks = {"tiny": 1, "small": 2, "medium": 3, "large": 4, "xlarge": 5}
        speed_ranks = {"very fast": 1, "fast": 2, "medium": 3, "slow": 4, "very slow": 5}
        
        size_target = size_ranks.get(size_preference, 3)
        speed_target = speed_ranks.get(speed_preference, 3)
        
        # Calculate score based on how close the model is to preferences
        scored_models = []
        for model in models:
            size_score = abs(size_ranks.get(model.size_category, 3) - size_target)
            speed_score = abs(speed_ranks.get(model.inference_speed, 3) - speed_target)
            total_score = size_score + speed_score
            scored_models.append((model, total_score))
        
        # Sort by score (lower is better)
        scored_models.sort(key=lambda x: x[1])
        return scored_models[0][0] if scored_models else None
    
    def get_all_tasks(self) -> List[str]:
        """Get all available tasks."""
        return list(self.task_to_models.keys())
    
    def get_all_model_ids(self) -> List[str]:
        """Get all registered model IDs."""
        return list(self.models.keys())


# Create singleton instance
model_registry = HuggingFaceModelRegistry()
