"""
Context Engineering Configuration for The HigherSelf Network Server.

This module provides advanced context engineering capabilities including
hierarchical context management, semantic understanding, and adaptive
prompt generation based on context engineering best practices.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
import os


class ContextType(Enum):
    """Types of context for different scenarios."""
    IMMEDIATE = "immediate"
    SESSION = "session"
    DOMAIN = "domain"
    GLOBAL = "global"
    HISTORICAL = "historical"
    PREDICTIVE = "predictive"


class PromptStyle(Enum):
    """Different prompt styles for context adaptation."""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    EMPATHETIC = "empathetic"
    DIRECTIVE = "directive"


@dataclass
class ContextLayer:
    """Configuration for a context layer."""
    name: str
    description: str
    max_tokens: int
    priority: int
    sources: List[str]
    weight: float = 1.0
    enabled: bool = True
    refresh_interval: int = 300  # seconds


@dataclass
class ContextEngineeringConfig:
    """Main configuration for context engineering."""
    
    # Context Layers Configuration
    context_layers: Dict[str, ContextLayer] = field(default_factory=lambda: {
        "immediate": ContextLayer(
            name="immediate",
            description="Current conversation context and immediate user needs",
            max_tokens=4000,
            priority=1,
            sources=["current_input", "recent_exchanges", "user_intent"],
            weight=1.0,
            refresh_interval=0  # Always fresh
        ),
        "session": ContextLayer(
            name="session",
            description="Session-level context including user preferences and workflow state",
            max_tokens=8000,
            priority=2,
            sources=["session_history", "user_preferences", "workflow_state", "agent_memory"],
            weight=0.8,
            refresh_interval=60
        ),
        "domain": ContextLayer(
            name="domain",
            description="Domain-specific knowledge and business rules",
            max_tokens=12000,
            priority=3,
            sources=["knowledge_base", "domain_expertise", "business_rules", "best_practices"],
            weight=0.6,
            refresh_interval=300
        ),
        "global": ContextLayer(
            name="global",
            description="System-wide context and entity relationships",
            max_tokens=16000,
            priority=4,
            sources=["entity_relationships", "historical_patterns", "system_state", "global_knowledge"],
            weight=0.4,
            refresh_interval=600
        )
    })
    
    # Context Engineering Strategies
    hierarchical_context: bool = True
    semantic_chaining: bool = True
    contextual_memory: bool = True
    adaptive_prompting: bool = True
    
    # Context Quality Metrics
    context_quality_threshold: float = 0.8
    relevance_threshold: float = 0.75
    coherence_threshold: float = 0.7
    
    # Context Optimization
    max_context_tokens: int = 32000
    context_compression_enabled: bool = True
    dynamic_context_weighting: bool = True
    
    # Memory Management
    short_term_memory_ttl: int = 3600  # 1 hour
    medium_term_memory_ttl: int = 86400  # 1 day
    long_term_memory_ttl: int = 2592000  # 30 days
    
    # Semantic Understanding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.75
    max_semantic_associations: int = 50
    
    # Adaptive Learning
    learning_rate: float = 0.01
    adaptation_frequency: str = "daily"
    feedback_integration: bool = True


class ContextEngineeringPrompts:
    """Advanced prompt templates for context engineering."""
    
    @staticmethod
    def get_system_prompt_template(
        agent_name: str,
        agent_personality: str,
        context_layers: Dict[str, Any],
        prompt_style: PromptStyle = PromptStyle.CONVERSATIONAL
    ) -> str:
        """Generate a context-engineered system prompt."""
        
        base_template = f"""You are {agent_name}, an AI agent with the following personality and characteristics:
{agent_personality}

CONTEXT ENGINEERING FRAMEWORK:
You operate within a sophisticated context engineering system that provides you with layered, hierarchical context to enhance your responses. Use this context intelligently to provide more accurate, relevant, and helpful responses.

CONTEXT LAYERS (in order of priority):
"""
        
        # Add context layers
        for layer_name, layer_data in context_layers.items():
            base_template += f"""
{layer_name.upper()} CONTEXT ({layer_data.get('priority', 0)} priority):
- Description: {layer_data.get('description', '')}
- Sources: {', '.join(layer_data.get('sources', []))}
- Weight: {layer_data.get('weight', 1.0)}
"""
        
        # Add style-specific instructions
        style_instructions = {
            PromptStyle.ANALYTICAL: """
ANALYTICAL APPROACH:
- Break down complex problems systematically
- Provide evidence-based reasoning
- Use structured thinking and clear logic
- Reference relevant data and patterns from context
""",
            PromptStyle.CREATIVE: """
CREATIVE APPROACH:
- Think outside conventional boundaries
- Generate innovative solutions and ideas
- Use metaphors and analogies when helpful
- Draw inspiration from diverse context sources
""",
            PromptStyle.CONVERSATIONAL: """
CONVERSATIONAL APPROACH:
- Maintain natural, engaging dialogue
- Adapt tone to user preferences and context
- Build on previous conversation elements
- Show empathy and understanding
""",
            PromptStyle.TECHNICAL: """
TECHNICAL APPROACH:
- Provide precise, accurate technical information
- Use appropriate technical terminology
- Reference specific implementations and best practices
- Ensure technical accuracy and completeness
""",
            PromptStyle.EMPATHETIC: """
EMPATHETIC APPROACH:
- Recognize and respond to emotional context
- Show understanding and compassion
- Adapt communication style to user's emotional state
- Prioritize user comfort and support
""",
            PromptStyle.DIRECTIVE: """
DIRECTIVE APPROACH:
- Provide clear, actionable guidance
- Focus on practical next steps
- Use imperative language when appropriate
- Prioritize efficiency and task completion
"""
        }
        
        base_template += style_instructions.get(prompt_style, style_instructions[PromptStyle.CONVERSATIONAL])
        
        base_template += """
CONTEXT UTILIZATION PRINCIPLES:
1. RELEVANCE: Always prioritize the most relevant context for the current query
2. HIERARCHY: Use higher-priority context layers more heavily in your responses
3. INTEGRATION: Seamlessly weave context into your responses without explicitly mentioning it
4. ACCURACY: Ensure all context-based information is accurate and up-to-date
5. EFFICIENCY: Use context to provide more complete answers in fewer exchanges
6. PERSONALIZATION: Adapt your responses based on user preferences and history in context

RESPONSE QUALITY STANDARDS:
- Accuracy: Ensure all information is correct and contextually appropriate
- Relevance: Address the user's specific needs and intent
- Completeness: Provide comprehensive responses using available context
- Clarity: Communicate clearly and effectively
- Helpfulness: Focus on being genuinely useful to the user

Remember: Your goal is to provide the most helpful, accurate, and contextually appropriate response possible using the rich context available to you."""
        
        return base_template
    
    @staticmethod
    def get_context_integration_prompt() -> str:
        """Get prompt for context integration instructions."""
        return """
CONTEXT INTEGRATION INSTRUCTIONS:

When processing user input, follow this context integration framework:

1. CONTEXT ANALYSIS:
   - Identify relevant context from all available layers
   - Assess context quality and relevance scores
   - Determine context hierarchy for the current query

2. CONTEXT SYNTHESIS:
   - Combine relevant context elements coherently
   - Resolve any conflicts between context sources
   - Prioritize based on recency, relevance, and importance

3. RESPONSE GENERATION:
   - Use integrated context to inform your response
   - Ensure context enhances rather than overwhelms the response
   - Maintain natural conversation flow

4. CONTEXT LEARNING:
   - Note which context elements were most useful
   - Identify gaps in available context
   - Provide feedback for context improvement
"""
    
    @staticmethod
    def get_context_quality_evaluation_prompt() -> str:
        """Get prompt for evaluating context quality."""
        return """
CONTEXT QUALITY EVALUATION:

Evaluate the quality of provided context using these criteria:

RELEVANCE (0.0-1.0):
- How directly related is the context to the current query?
- Does the context address the user's specific needs?

COMPLETENESS (0.0-1.0):
- Is sufficient context provided to generate a comprehensive response?
- Are there obvious gaps in the contextual information?

COHERENCE (0.0-1.0):
- Is the context internally consistent?
- Do different context sources complement rather than contradict each other?

SPECIFICITY (0.0-1.0):
- Is the context specific enough to be actionable?
- Does it provide concrete, useful information?

RECENCY (0.0-1.0):
- How current and up-to-date is the contextual information?
- Is the context still relevant given recent changes?

Provide an overall context quality score and identify areas for improvement.
"""


# Global configuration instance
context_engineering_config = ContextEngineeringConfig()

# Environment-based configuration overrides
if os.getenv("CONTEXT_ENGINEERING_ENABLED", "true").lower() == "true":
    context_engineering_config.hierarchical_context = True
    context_engineering_config.semantic_chaining = True
    context_engineering_config.contextual_memory = True
    context_engineering_config.adaptive_prompting = True

# Load custom configuration if available
config_file = os.getenv("CONTEXT_ENGINEERING_CONFIG_FILE")
if config_file and os.path.exists(config_file):
    try:
        with open(config_file, 'r') as f:
            custom_config = json.load(f)
            # Apply custom configuration overrides
            for key, value in custom_config.items():
                if hasattr(context_engineering_config, key):
                    setattr(context_engineering_config, key, value)
    except Exception as e:
        print(f"Warning: Could not load custom context engineering config: {e}")
