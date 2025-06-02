# LangChain Implementation Plan for The HigherSelf Network Server

## Phase 1: Foundation Implementation (Weeks 1-2)

### 1.1 Dependencies and Configuration

#### New Requirements File
**File**: `requirements-langchain.txt`
```txt
# LangChain Core
langchain==0.1.0
langchain-openai==0.0.5
langchain-anthropic==0.0.2
langchain-community==0.0.10

# Vector Stores & Embeddings
chromadb==0.4.22
faiss-cpu==1.7.4
sentence-transformers==2.2.2

# Token Management
tiktoken==0.5.2

# Additional Dependencies
pydantic>=2.0.0
redis>=5.0.1
prometheus-client>=0.19.0
```

#### Configuration Updates
**File**: `config/langchain_config.py` (NEW)
```python
import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field

class LangChainConfig(BaseSettings):
    """Configuration for LangChain integration."""
    
    # Model configurations
    default_model: str = Field(default="gpt-3.5-turbo", env="LANGCHAIN_DEFAULT_MODEL")
    fallback_model: str = Field(default="gpt-3.5-turbo", env="LANGCHAIN_FALLBACK_MODEL")
    
    # API keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Performance settings
    max_retries: int = Field(default=3, env="LANGCHAIN_MAX_RETRIES")
    timeout: int = Field(default=30, env="LANGCHAIN_TIMEOUT")
    max_concurrent_requests: int = Field(default=10, env="LANGCHAIN_MAX_CONCURRENT")
    
    # Caching
    enable_caching: bool = Field(default=True, env="LANGCHAIN_ENABLE_CACHING")
    cache_ttl: int = Field(default=3600, env="LANGCHAIN_CACHE_TTL")
    
    # Vector store
    vector_store_path: str = Field(default="./vector_store", env="LANGCHAIN_VECTOR_STORE_PATH")
    embedding_model: str = Field(default="text-embedding-ada-002", env="LANGCHAIN_EMBEDDING_MODEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

langchain_config = LangChainConfig()
```

### 1.2 Base LangChain Agent Class

**File**: `agents/langchain_agent.py` (NEW)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.tools import BaseTool
from langchain.callbacks.base import BaseCallbackHandler

from agents.base_agent import BaseAgent
from config.langchain_config import langchain_config
from monitoring.langchain_callbacks import MonitoringCallback
from security.input_validator import SecureInput
from utils.error_handling import ErrorHandler

class LangChainAgent(BaseAgent, ABC):
    """Base agent class with LangChain capabilities."""
    
    def __init__(self, name: str, notion_client, personality: str, **kwargs):
        super().__init__(name=name, notion_client=notion_client, **kwargs)
        self.personality = personality
        self.llm = self._initialize_llm()
        self.memory = self._initialize_memory()
        self.tools = self._initialize_tools()
        self.agent_executor = self._create_agent_executor()
        self.callback_handler = MonitoringCallback(self.name, notion_client)
    
    def _initialize_llm(self):
        """Initialize the LLM with fallback support."""
        try:
            if langchain_config.openai_api_key:
                return ChatOpenAI(
                    temperature=0.7,
                    model_name=langchain_config.default_model,
                    openai_api_key=langchain_config.openai_api_key,
                    callbacks=[self.callback_handler],
                    max_retries=langchain_config.max_retries,
                    request_timeout=langchain_config.timeout
                )
            elif langchain_config.anthropic_api_key:
                return ChatAnthropic(
                    temperature=0.7,
                    model="claude-3-sonnet-20240229",
                    anthropic_api_key=langchain_config.anthropic_api_key,
                    callbacks=[self.callback_handler]
                )
            else:
                raise ValueError("No LLM API key provided")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def _initialize_memory(self):
        """Initialize conversation memory."""
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=2000
        )
    
    @abstractmethod
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize agent-specific tools. Must be implemented by subclasses."""
        pass
    
    def _create_agent_executor(self):
        """Create the agent executor with personality-aware prompts."""
        system_prompt = self._create_system_prompt()
        
        agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self._create_prompt_template(system_prompt)
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            max_execution_time=60
        )
    
    def _create_system_prompt(self) -> str:
        """Create system prompt with personality."""
        return f"""You are {self.name}, a digital agent with the following personality:
        {self.personality}
        
        You work as part of The Higher Self Network, helping with business automation for:
        - Art Gallery operations
        - Wellness Center management  
        - Consultancy services
        
        Always maintain your personality while being helpful and efficient.
        Use the available tools to complete tasks effectively.
        Provide clear, actionable responses.
        """
    
    def _create_prompt_template(self, system_prompt: str) -> PromptTemplate:
        """Create prompt template for the agent."""
        template = f"""{system_prompt}

TOOLS:
------
You have access to the following tools:

{{tools}}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{{tool_names}}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

Begin!

Previous conversation history:
{{chat_history}}

New input: {{input}}
{{agent_scratchpad}}"""

        return PromptTemplate(
            template=template,
            input_variables=["input", "chat_history", "agent_scratchpad", "tools", "tool_names"]
        )
    
    async def process_with_langchain(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input using LangChain capabilities."""
        try:
            # Validate input
            secure_input = SecureInput(
                user_input=str(input_data),
                agent_name=self.name,
                task_type="general"
            )
            
            # Process with agent executor
            result = await self.agent_executor.ainvoke({
                "input": secure_input.user_input
            })
            
            return {
                "success": True,
                "result": result,
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in LangChain processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_capabilities(self) -> str:
        """Return agent capabilities description."""
        tool_names = [tool.name for tool in self.tools]
        return f"{self.personality}. Available tools: {', '.join(tool_names)}"
```

### 1.3 Security Framework

**File**: `security/input_validator.py` (NEW)
```python
from pydantic import BaseModel, validator
import re
from typing import List

class SecureInput(BaseModel):
    """Validates and sanitizes inputs before LLM processing."""
    
    user_input: str
    agent_name: str
    task_type: str
    
    @validator('user_input')
    def sanitize_input(cls, v):
        """Remove potentially harmful content."""
        # Remove potential injection attempts
        v = re.sub(r'<script.*?</script>', '', v, flags=re.DOTALL)
        v = re.sub(r'system:', '', v, flags=re.IGNORECASE)
        v = re.sub(r'assistant:', '', v, flags=re.IGNORECASE)
        v = re.sub(r'human:', '', v, flags=re.IGNORECASE)
        
        # Remove potential prompt injection
        injection_patterns = [
            r'ignore previous instructions',
            r'forget everything',
            r'new instructions:',
            r'system override',
            r'admin mode'
        ]
        
        for pattern in injection_patterns:
            v = re.sub(pattern, '', v, flags=re.IGNORECASE)
        
        # Limit length
        if len(v) > 10000:
            v = v[:10000]
        
        return v.strip()
    
    @validator('agent_name')
    def validate_agent(cls, v):
        """Ensure agent name is valid."""
        valid_agents = ["Nyra", "Solari", "Ruvo", "Liora", "Sage", "Elan", "Zevi", "Grace", "Atlas"]
        if v not in valid_agents:
            raise ValueError(f"Invalid agent name: {v}")
        return v
    
    @validator('task_type')
    def validate_task_type(cls, v):
        """Ensure task type is valid."""
        valid_types = [
            "lead_processing", "booking_management", "content_generation",
            "task_orchestration", "community_engagement", "audience_analysis",
            "knowledge_retrieval", "general"
        ]
        if v not in valid_types:
            v = "general"  # Default to general if invalid
        return v

class OutputFilter:
    """Filters LLM outputs for security and compliance."""
    
    @staticmethod
    def filter_sensitive_data(output: str) -> str:
        """Remove or mask sensitive information."""
        # Mask email addresses
        output = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL]', output)
        
        # Mask phone numbers
        output = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', output)
        
        # Mask credit card numbers
        output = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]', output)
        
        # Mask SSN
        output = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', output)
        
        return output
    
    @staticmethod
    def validate_json_output(output: str) -> dict:
        """Validate and sanitize JSON outputs."""
        try:
            import json
            data = json.loads(output)
            return OutputFilter._sanitize_dict(data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON output", "raw_output": output[:500]}
    
    @staticmethod
    def _sanitize_dict(data: dict) -> dict:
        """Recursively sanitize dictionary data."""
        if isinstance(data, dict):
            return {k: OutputFilter._sanitize_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [OutputFilter._sanitize_dict(item) for item in data]
        elif isinstance(data, str):
            return OutputFilter.filter_sensitive_data(data)
        else:
            return data
```

### 1.4 Monitoring and Callbacks

**File**: `monitoring/langchain_callbacks.py` (NEW)
```python
from langchain.callbacks.base import BaseCallbackHandler
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import time

from loguru import logger
from prometheus_client import Counter, Histogram, Gauge

# Metrics
LANGCHAIN_REQUESTS = Counter('langchain_requests_total', 'Total LangChain requests', ['agent', 'model'])
LANGCHAIN_ERRORS = Counter('langchain_errors_total', 'Total LangChain errors', ['agent', 'error_type'])
LANGCHAIN_DURATION = Histogram('langchain_duration_seconds', 'LangChain request duration', ['agent', 'model'])
LANGCHAIN_TOKEN_USAGE = Counter('langchain_token_usage_total', 'Total tokens used', ['agent', 'model', 'type'])

class MonitoringCallback(BaseCallbackHandler):
    """Custom callback for monitoring LangChain operations."""
    
    def __init__(self, agent_name: str, notion_client):
        self.agent_name = agent_name
        self.notion_client = notion_client
        self.start_time = None
        self.current_model = None
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Log when LLM starts processing."""
        self.start_time = time.time()
        self.current_model = serialized.get("name", "unknown")
        
        LANGCHAIN_REQUESTS.labels(agent=self.agent_name, model=self.current_model).inc()
        
        logger.info(f"LLM started for {self.agent_name} using {self.current_model}")
    
    def on_llm_end(self, response, **kwargs):
        """Log when LLM completes processing."""
        if self.start_time:
            duration = time.time() - self.start_time
            LANGCHAIN_DURATION.labels(agent=self.agent_name, model=self.current_model).observe(duration)
            
            # Track token usage if available
            if hasattr(response, 'llm_output') and response.llm_output:
                token_usage = response.llm_output.get("token_usage", {})
                if token_usage:
                    LANGCHAIN_TOKEN_USAGE.labels(
                        agent=self.agent_name, 
                        model=self.current_model, 
                        type='prompt'
                    ).inc(token_usage.get('prompt_tokens', 0))
                    
                    LANGCHAIN_TOKEN_USAGE.labels(
                        agent=self.agent_name, 
                        model=self.current_model, 
                        type='completion'
                    ).inc(token_usage.get('completion_tokens', 0))
            
            logger.info(f"LLM completed for {self.agent_name} in {duration:.2f}s")
    
    def on_llm_error(self, error: Exception, **kwargs):
        """Log LLM errors."""
        error_type = type(error).__name__
        LANGCHAIN_ERRORS.labels(agent=self.agent_name, error_type=error_type).inc()
        
        logger.error(f"LLM error for {self.agent_name}: {error}")
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """Log when tool starts."""
        tool_name = serialized.get("name", "unknown")
        logger.debug(f"Tool {tool_name} started for {self.agent_name}")
    
    def on_tool_end(self, output: str, **kwargs):
        """Log when tool completes."""
        logger.debug(f"Tool completed for {self.agent_name}")
    
    def on_tool_error(self, error: Exception, **kwargs):
        """Log tool errors."""
        logger.error(f"Tool error for {self.agent_name}: {error}")
    
    def on_agent_action(self, action, **kwargs):
        """Log agent actions."""
        logger.debug(f"Agent {self.agent_name} taking action: {action.tool}")
    
    def on_agent_finish(self, finish, **kwargs):
        """Log agent completion."""
        logger.info(f"Agent {self.agent_name} finished processing")
```

## Phase 2: Enhanced Agent Implementations (Weeks 3-4)

### 2.1 LangChain Tools Framework

**File**: `tools/notion_tools.py` (NEW)
```python
from langchain.tools import BaseTool
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
import json

from services.notion_service import NotionService

class NotionQueryInput(BaseModel):
    database_id: str = Field(description="Notion database ID")
    query: str = Field(description="Natural language query")

class NotionQueryTool(BaseTool):
    name = "notion_query"
    description = "Query Notion databases using natural language"
    args_schema: Type[BaseModel] = NotionQueryInput

    def __init__(self, notion_service: NotionService):
        super().__init__()
        self.notion_service = notion_service

    def _run(self, database_id: str, query: str) -> str:
        """Execute the query against Notion."""
        try:
            # Convert natural language to Notion filter
            filter_dict = self._parse_query_to_filter(query)
            results = self.notion_service.query_database(database_id, filter_dict)
            return self._format_results(results)
        except Exception as e:
            return f"Error querying Notion: {str(e)}"

    async def _arun(self, database_id: str, query: str) -> str:
        """Async version."""
        return self._run(database_id, query)

    def _parse_query_to_filter(self, query: str) -> Dict[str, Any]:
        """Convert natural language query to Notion filter."""
        # Simple implementation - can be enhanced with NLP
        filter_dict = {}

        if "status" in query.lower():
            if "active" in query.lower():
                filter_dict["Status"] = {"select": {"equals": "Active"}}
            elif "completed" in query.lower():
                filter_dict["Status"] = {"select": {"equals": "Completed"}}

        if "priority" in query.lower():
            if "high" in query.lower():
                filter_dict["Priority"] = {"select": {"equals": "High"}}

        return filter_dict

    def _format_results(self, results: Dict[str, Any]) -> str:
        """Format Notion results for LLM consumption."""
        if not results.get("results"):
            return "No results found."

        formatted = []
        for item in results["results"][:5]:  # Limit to 5 results
            title = "Untitled"
            if item.get("properties", {}).get("Name"):
                title_prop = item["properties"]["Name"]
                if title_prop.get("title"):
                    title = title_prop["title"][0]["text"]["content"]

            formatted.append(f"- {title} (ID: {item['id']})")

        return "\n".join(formatted)

class NotionCreatePageInput(BaseModel):
    database_id: str = Field(description="Notion database ID")
    title: str = Field(description="Page title")
    properties: Dict[str, Any] = Field(description="Page properties as JSON")

class NotionCreatePageTool(BaseTool):
    name = "notion_create_page"
    description = "Create a new page in a Notion database"
    args_schema: Type[BaseModel] = NotionCreatePageInput

    def __init__(self, notion_service: NotionService):
        super().__init__()
        self.notion_service = notion_service

    def _run(self, database_id: str, title: str, properties: Dict[str, Any]) -> str:
        """Create a new page in Notion."""
        try:
            # Ensure title is in properties
            if "Name" not in properties:
                properties["Name"] = {"title": [{"text": {"content": title}}]}

            result = self.notion_service.create_page(database_id, properties)
            return f"Created page: {title} (ID: {result['id']})"
        except Exception as e:
            return f"Error creating page: {str(e)}"

    async def _arun(self, database_id: str, title: str, properties: Dict[str, Any]) -> str:
        """Async version."""
        return self._run(database_id, title, properties)
```

**File**: `tools/communication_tools.py` (NEW)
```python
from langchain.tools import BaseTool
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
import json

from services.redis_service import redis_service

class AgentMessageInput(BaseModel):
    target_agent: str = Field(description="Target agent name")
    message: str = Field(description="Message content")
    priority: str = Field(default="normal", description="Message priority: low, normal, high")

class AgentCommunicationTool(BaseTool):
    name = "send_agent_message"
    description = "Send a message to another agent"
    args_schema: Type[BaseModel] = AgentMessageInput

    def __init__(self, sender_agent: str):
        super().__init__()
        self.sender_agent = sender_agent

    def _run(self, target_agent: str, message: str, priority: str = "normal") -> str:
        """Send message to another agent via Redis pub/sub."""
        try:
            message_data = {
                "from": self.sender_agent,
                "to": target_agent,
                "message": message,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat()
            }

            channel = f"higherself:agents:{target_agent.lower()}"
            redis_service.publish(channel, json.dumps(message_data))

            return f"Message sent to {target_agent}"
        except Exception as e:
            return f"Error sending message: {str(e)}"

    async def _arun(self, target_agent: str, message: str, priority: str = "normal") -> str:
        """Async version."""
        return self._run(target_agent, message, priority)

class WorkflowTriggerInput(BaseModel):
    workflow_name: str = Field(description="Workflow name to trigger")
    context: Dict[str, Any] = Field(description="Workflow context data")

class WorkflowTriggerTool(BaseTool):
    name = "trigger_workflow"
    description = "Trigger a workflow with context data"
    args_schema: Type[BaseModel] = WorkflowTriggerInput

    def _run(self, workflow_name: str, context: Dict[str, Any]) -> str:
        """Trigger a workflow."""
        try:
            # Store workflow trigger in Redis for processing
            workflow_data = {
                "workflow": workflow_name,
                "context": context,
                "triggered_by": self.sender_agent,
                "timestamp": datetime.utcnow().isoformat()
            }

            redis_service.lpush("higherself:workflows:queue", json.dumps(workflow_data))

            return f"Triggered workflow: {workflow_name}"
        except Exception as e:
            return f"Error triggering workflow: {str(e)}"

    async def _arun(self, workflow_name: str, context: Dict[str, Any]) -> str:
        """Async version."""
        return self._run(workflow_name, context)
```

### 2.2 Enhanced Nyra Implementation

**File**: `agents/nyra_enhanced.py` (NEW)
```python
from typing import List, Dict, Any
import json
from datetime import datetime

from langchain.tools import BaseTool
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from agents.langchain_agent import LangChainAgent
from tools.notion_tools import NotionQueryTool, NotionCreatePageTool
from tools.communication_tools import AgentCommunicationTool, WorkflowTriggerTool

class LeadQualificationTool(BaseTool):
    name = "qualify_lead"
    description = "Analyze and qualify a lead based on provided data"

    def _run(self, lead_data: str) -> str:
        """Qualify lead using business rules."""
        try:
            data = json.loads(lead_data) if isinstance(lead_data, str) else lead_data

            score = 0
            factors = []

            # Email quality
            if data.get("email") and "@" in data["email"]:
                score += 2
                factors.append("Valid email provided")

            # Message quality
            message = data.get("message", "").lower()
            if any(word in message for word in ["consultation", "retreat", "workshop", "booking"]):
                score += 3
                factors.append("Specific service interest")

            # Contact information
            if data.get("phone"):
                score += 2
                factors.append("Phone number provided")

            # Urgency indicators
            if any(word in message for word in ["urgent", "soon", "asap", "immediately"]):
                score += 2
                factors.append("Urgency indicated")

            # Budget indicators
            if any(word in message for word in ["budget", "investment", "cost", "price"]):
                score += 1
                factors.append("Budget awareness")

            quality_level = "Low"
            if score >= 7:
                quality_level = "High"
            elif score >= 4:
                quality_level = "Medium"

            return json.dumps({
                "score": score,
                "quality_level": quality_level,
                "factors": factors,
                "recommendation": self._get_recommendation(score)
            })

        except Exception as e:
            return f"Error qualifying lead: {str(e)}"

    def _get_recommendation(self, score: int) -> str:
        """Get recommendation based on score."""
        if score >= 7:
            return "High priority - immediate follow-up recommended"
        elif score >= 4:
            return "Medium priority - follow-up within 24 hours"
        else:
            return "Low priority - add to nurture sequence"

class NyraEnhanced(LangChainAgent):
    """Enhanced Nyra with LangChain capabilities for lead capture and qualification."""

    def __init__(self, notion_client, **kwargs):
        super().__init__(
            name="Nyra",
            notion_client=notion_client,
            personality="Intuitive & Responsive - I sense opportunities in every interaction and respond with care and precision. I excel at understanding people's needs and connecting them with the right solutions.",
            **kwargs
        )
        self.lead_chain = self._create_lead_chain()
        self.followup_chain = self._create_followup_chain()

    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize Nyra-specific tools."""
        return [
            LeadQualificationTool(),
            NotionQueryTool(self.notion_client),
            NotionCreatePageTool(self.notion_client),
            AgentCommunicationTool(self.name),
            WorkflowTriggerTool()
        ]

    def _create_lead_chain(self):
        """Create chain for lead analysis."""
        prompt = PromptTemplate(
            input_variables=["lead_data"],
            template="""As Nyra, analyze this lead with intuition and care:

Lead Data: {lead_data}

Provide a detailed analysis including:
1. Primary Interest/Need (be specific)
2. Urgency Level (Low/Medium/High) with reasoning
3. Business Type Match (Art Gallery/Wellness Center/Consultancy)
4. Personalization Opportunities
5. Recommended Next Steps
6. Potential Value Assessment

Format your response as JSON with clear, actionable insights."""
        )

        return LLMChain(llm=self.llm, prompt=prompt)

    def _create_followup_chain(self):
        """Create chain for follow-up generation."""
        prompt = PromptTemplate(
            input_variables=["lead_analysis", "business_type", "lead_data"],
            template="""As Nyra, create a warm, personalized follow-up message:

Lead Analysis: {lead_analysis}
Business Type: {business_type}
Original Lead Data: {lead_data}

Create a message that:
- Acknowledges their specific interest warmly
- Demonstrates understanding of their needs
- Offers immediate value or insight
- Suggests a clear, non-pressured next step
- Maintains my intuitive, caring tone
- Feels personal, not templated

Keep it under 150 words and make it feel like it comes from someone who truly cares about helping them."""
        )

        return LLMChain(llm=self.llm, prompt=prompt)

    async def process_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a new lead through the complete pipeline."""
        try:
            self.logger.info(f"Nyra processing lead: {lead_data.get('name', 'Unknown')}")

            # Step 1: Analyze the lead with LangChain
            analysis_result = await self.lead_chain.ainvoke({"lead_data": json.dumps(lead_data)})
            lead_analysis = json.loads(analysis_result["text"])

            # Step 2: Qualify the lead using the tool
            qualification_result = await self.tools[0]._arun(json.dumps(lead_data))
            qualification = json.loads(qualification_result)

            # Step 3: Create follow-up message
            followup_result = await self.followup_chain.ainvoke({
                "lead_analysis": json.dumps(lead_analysis),
                "business_type": lead_data.get("business_type", "general"),
                "lead_data": json.dumps(lead_data)
            })

            # Step 4: Create Notion contact
            contact_properties = self._build_contact_properties(lead_data, lead_analysis, qualification)
            contact_creation = await self.tools[2]._arun(
                database_id="contacts_db_id",  # Should be from config
                title=lead_data.get("name", "Unknown Lead"),
                properties=contact_properties
            )

            # Step 5: Trigger appropriate workflow
            workflow_name = self._determine_workflow(lead_analysis, qualification)
            workflow_trigger = await self.tools[4]._arun(
                workflow_name=workflow_name,
                context={
                    "lead_data": lead_data,
                    "analysis": lead_analysis,
                    "qualification": qualification
                }
            )

            # Step 6: Notify other agents if needed
            if qualification["quality_level"] == "High":
                await self.tools[3]._arun(
                    target_agent="Grace",
                    message=f"High-quality lead processed: {lead_data.get('name')}. Immediate attention recommended.",
                    priority="high"
                )

            return {
                "success": True,
                "lead_analysis": lead_analysis,
                "qualification": qualification,
                "followup_message": followup_result["text"],
                "contact_creation": contact_creation,
                "workflow_triggered": workflow_name,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error processing lead: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _build_contact_properties(self, lead_data: Dict[str, Any], analysis: Dict[str, Any], qualification: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion contact properties."""
        return {
            "Name": {"title": [{"text": {"content": lead_data.get("name", "Unknown")}}]},
            "Email": {"email": lead_data.get("email")},
            "Phone": {"phone_number": lead_data.get("phone")},
            "Source": {"select": {"name": lead_data.get("source", "Website")}},
            "Status": {"select": {"name": "New Lead"}},
            "Lead Score": {"number": qualification["score"]},
            "Quality Level": {"select": {"name": qualification["quality_level"]}},
            "Primary Interest": {"rich_text": [{"text": {"content": analysis.get("primary_interest", "")}}]},
            "Business Type": {"select": {"name": analysis.get("business_type_match", "General")}},
            "Urgency": {"select": {"name": analysis.get("urgency_level", "Low")}},
            "Notes": {"rich_text": [{"text": {"content": json.dumps(lead_data)}}]},
            "Created By": {"select": {"name": "Nyra"}},
            "Created Date": {"date": {"start": datetime.utcnow().isoformat()}}
        }

    def _determine_workflow(self, analysis: Dict[str, Any], qualification: Dict[str, Any]) -> str:
        """Determine appropriate workflow based on analysis."""
        if qualification["quality_level"] == "High":
            return "high_priority_lead_workflow"
        elif "consultation" in analysis.get("primary_interest", "").lower():
            return "consultation_booking_workflow"
        elif "retreat" in analysis.get("primary_interest", "").lower():
            return "retreat_inquiry_workflow"
        elif "workshop" in analysis.get("primary_interest", "").lower():
            return "workshop_registration_workflow"
        else:
            return "standard_nurture_workflow"
```

This completes the enhanced Nyra implementation. The plan continues with other enhanced agents and advanced features.
