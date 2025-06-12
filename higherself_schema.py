from __future__ import \
    annotations  # To allow forward references for type hints

from datetime import datetime
from enum import Enum
from typing import (Dict,  # Ensure all necessary typing imports are present
                    List, Literal, Optional, Union)

from pydantic import BaseModel, Field

# Attempt to import Enums from models.base
try:
    from models.base import AgentCapability, AgentPersonality, AgentRole
except ImportError:
    # Define placeholders if models.base is not yet updated or available to the worker
    # This is a fallback, ideally the enums from models.base should be used.
    class AgentPersonality(str, Enum):
        NYRA = "nyra"
        PLACEHOLDER = "placeholder"  # Add more if known

    class AgentRole(str, Enum):
        LEAD_CAPTURE = "lead_capture"
        PLACEHOLDER = "placeholder"  # Add more if known

    class AgentCapability(str, Enum):
        BOOKING_DETECTION = "Booking Detection"
        PLACEHOLDER = "placeholder"  # Add more if known


# --- Core Server Components ---
class ServerComponent(BaseModel):
    name: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    configuration_requirements: Dict[str, str] = Field(default_factory=dict)


class APIEndpoint(BaseModel):
    path: str
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    description: str
    parameters: Dict[str, str] = Field(default_factory=dict)
    response_schema: Dict[str, str] = Field(default_factory=dict)
    authentication_required: bool = True
    example_request: Optional[str] = None
    example_response: Optional[str] = None


class IntegrationType(str, Enum):
    NOTION = "notion"
    AIRTABLE = "airtable"
    WEBHOOK = "webhook"
    API = "api"
    DATABASE = "database"
    HUGGINGFACE = "huggingface"
    VECTOR_DB = "vector_db"


class Integration(BaseModel):
    type: IntegrationType
    name: str
    description: str
    configuration_keys: List[str] = Field(default_factory=list)
    setup_instructions: str
    limitations: List[str] = Field(default_factory=list)
    best_practices: List[str] = Field(default_factory=list)


# --- Agent System ---
# AgentPersonality and AgentRole Enums are imported from models.base
# AgentCapability Enum is imported from models.base


# This Agent model is defined as per the issue specification for HigherSelfNetworkServer schema
class Agent(BaseModel):
    personality: AgentPersonality
    role: AgentRole
    personality_traits: List[str] = Field(default_factory=list)
    primary_capabilities: List[AgentCapability] = Field(default_factory=list)
    collaborates_with: List[AgentPersonality] = Field(default_factory=list)
    database_access: List[str] = Field(default_factory=list)


# --- Notion Database Structure ---
class NotionDatabaseType(str, Enum):
    BUSINESS_ENTITIES = "business_entities"
    CONTACTS_PROFILES = "contacts_profiles"
    COMMUNITY_HUB = "community_hub"
    PRODUCTS_SERVICES = "products_services"
    ACTIVE_WORKFLOWS = "active_workflows"
    MARKETING_CAMPAIGNS = "marketing_campaigns"
    FEEDBACK_SURVEYS = "feedback_surveys"
    REWARDS_BOUNTIES = "rewards_bounties"
    TASKS = "tasks"
    AGENT_COMMUNICATION = "agent_communication"
    AGENT_REGISTRY = "agent_registry"
    API_INTEGRATIONS = "api_integrations"
    DATA_TRANSFORMATIONS = "data_transformations"
    NOTIFICATIONS_TEMPLATES = "notifications_templates"
    USE_CASES = "use_cases"
    WORKFLOWS_LIBRARY = "workflows_library"


class NotionDatabase(BaseModel):
    type: NotionDatabaseType
    description: str
    key_properties: Dict[str, str] = Field(default_factory=dict)
    relations: Dict[str, NotionDatabaseType] = Field(default_factory=dict)
    example_records: List[Dict[str, str]] = Field(default_factory=list)


# --- Workflow System ---
class WorkflowState(str, Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class WorkflowTransition(BaseModel):
    from_state: WorkflowState
    to_state: WorkflowState
    trigger: str
    conditions: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    responsible_agent: Optional[AgentPersonality] = None


# This Workflow model is defined as per the issue specification for HigherSelfNetworkServer schema
class Workflow(BaseModel):
    name: str
    description: str
    business_application: List[str] = Field(default_factory=list)
    states: List[WorkflowState] = Field(
        default_factory=list
    )  # Note: Existing model has Dict, schema asks for List
    transitions: List[WorkflowTransition] = Field(default_factory=list)
    involved_agents: List[AgentPersonality] = Field(default_factory=list)
    involved_databases: List[NotionDatabaseType] = Field(default_factory=list)
    example_execution: str


# --- RAG System ---
class EmbeddingProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    MOCK = "mock"


class RAGComponent(BaseModel):
    name: str
    description: str
    embedding_provider: EmbeddingProvider
    vector_dimensions: int
    retrieval_strategy: str
    context_window_size: int
    example_usage: str


# --- Deployment Options ---
class DeploymentOption(str, Enum):
    DOCKER = "docker"
    PYTHON = "python"
    AWS_ECS = "aws_ecs"
    GOOGLE_CLOUD_RUN = "google_cloud_run"
    AZURE_CONTAINER = "azure_container"
    DIGITAL_OCEAN = "digital_ocean"


class DeploymentConfiguration(BaseModel):
    option: DeploymentOption
    prerequisites: List[str] = Field(default_factory=list)
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    setup_steps: List[str] = Field(default_factory=list)
    monitoring_setup: Optional[str] = None
    scaling_configuration: Optional[Dict[str, str]] = None
    estimated_resources: Dict[str, str] = Field(default_factory=dict)


# --- Learning Modules ---
class LearningModuleDifficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningModule(BaseModel):
    title: str
    difficulty: LearningModuleDifficulty
    prerequisites: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    key_concepts: Dict[str, str] = Field(default_factory=dict)
    practical_exercises: List[str] = Field(default_factory=list)
    evaluation_criteria: List[str] = Field(default_factory=list)
    estimated_completion_time: str


# --- Complete Server Documentation ---
class HigherSelfNetworkServer(BaseModel):
    version: str = "1.0.0"
    components: List[ServerComponent]
    api_endpoints: List[APIEndpoint]
    integrations: List[Integration]
    agents: List[Agent]  # Uses the Agent model defined above (as per issue spec)
    notion_databases: List[NotionDatabase]
    workflows: List[
        Workflow
    ]  # Uses the Workflow model defined above (as per issue spec)
    rag_components: List[RAGComponent]
    deployment_options: List[DeploymentConfiguration]
    learning_modules: List[LearningModule]
    last_updated: datetime = Field(default_factory=datetime.now)
