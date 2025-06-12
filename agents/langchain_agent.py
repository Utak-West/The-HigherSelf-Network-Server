"""
Base LangChain agent class for The HigherSelf Network Server.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool

try:
    from langchain_openai import ChatOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_anthropic import ChatAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from agents.base_agent import BaseAgent
from config.langchain_config import langchain_config
from monitoring.langchain_callbacks import (MonitoringCallback,
                                            PerformanceCallback)
from security.input_validator import OutputFilter, SecureInput
from utils.error_handling import ErrorHandler


class LangChainAgent(BaseAgent, ABC):
    """Base agent class with LangChain capabilities."""

    def __init__(self, name: str, notion_client, personality: str, **kwargs):
        super().__init__(name=name, notion_client=notion_client, **kwargs)
        self.personality = personality
        self.llm = self._initialize_llm()
        self.memory = self._initialize_memory()
        self.tools = self._initialize_tools()
        self.agent_executor = None  # Will be created after tools are initialized
        self.callback_handler = MonitoringCallback(self.name, notion_client)
        self.performance_callback = PerformanceCallback(self.name)
        self._create_agent_executor()

    def _initialize_llm(self):
        """Initialize the LLM with fallback support."""
        try:
            # Try OpenAI first
            if langchain_config.openai_api_key and OPENAI_AVAILABLE:
                return ChatOpenAI(
                    temperature=0.7,
                    model_name=langchain_config.default_model,
                    openai_api_key=langchain_config.openai_api_key,
                    callbacks=[self.callback_handler, self.performance_callback],
                    max_retries=langchain_config.max_retries,
                    request_timeout=langchain_config.timeout,
                )
            # Try Anthropic as fallback
            elif langchain_config.anthropic_api_key and ANTHROPIC_AVAILABLE:
                return ChatAnthropic(
                    temperature=0.7,
                    model="claude-3-sonnet-20240229",
                    anthropic_api_key=langchain_config.anthropic_api_key,
                    callbacks=[self.callback_handler, self.performance_callback],
                )
            else:
                raise ValueError(
                    "No LLM API key provided or required packages not installed. "
                    "Please install langchain-openai or langchain-anthropic and provide API keys."
                )
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM for {self.name}: {e}")
            raise

    def _initialize_memory(self):
        """Initialize conversation memory."""
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=langchain_config.memory_max_tokens,
        )

    @abstractmethod
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize agent-specific tools. Must be implemented by subclasses."""
        pass

    def _create_agent_executor(self):
        """Create the agent executor with personality-aware prompts."""
        if not self.tools:
            self.logger.warning(f"No tools initialized for {self.name}")
            return

        try:
            system_prompt = self._create_system_prompt()

            agent = create_structured_chat_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self._create_prompt_template(system_prompt),
            )

            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=langchain_config.max_iterations,
                max_execution_time=langchain_config.max_execution_time,
            )

            self.logger.info(
                f"Agent executor created for {self.name} with {len(self.tools)} tools"
            )

        except Exception as e:
            self.logger.error(f"Failed to create agent executor for {self.name}: {e}")
            raise

    def _create_system_prompt(self) -> str:
        """Create system prompt with personality."""
        return f"""You are {self.name}, a digital agent with the following personality:
        {self.personality}
        
        You work as part of The Higher Self Network, helping with business automation for:
        - Art Gallery operations and exhibitions
        - Wellness Center management and programs
        - Consultancy services and client relationships
        
        Core Principles:
        - Always maintain your unique personality while being helpful and efficient
        - Use the available tools to complete tasks effectively
        - Provide clear, actionable responses
        - Collaborate with other agents when needed
        - Prioritize client satisfaction and business growth
        - Maintain confidentiality and professionalism
        
        When using tools, be precise and purposeful. When communicating with other agents,
        be clear about context and expectations. Always aim to exceed expectations while
        staying true to your personality.
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
            input_variables=[
                "input",
                "chat_history",
                "agent_scratchpad",
                "tools",
                "tool_names",
            ],
        )

    async def process_with_langchain(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process input using LangChain capabilities."""
        try:
            # Validate input if enabled
            if langchain_config.enable_input_validation:
                secure_input = SecureInput(
                    user_input=str(input_data.get("input", "")),
                    agent_name=self.name,
                    task_type=input_data.get("task_type", "general"),
                )
                validated_input = secure_input.user_input
            else:
                validated_input = str(input_data.get("input", ""))

            # Process with agent executor
            if not self.agent_executor:
                raise ValueError(f"Agent executor not initialized for {self.name}")

            result = await self.agent_executor.ainvoke({"input": validated_input})

            # Filter output if enabled
            if langchain_config.enable_output_filtering:
                if isinstance(result.get("output"), str):
                    result["output"] = OutputFilter.filter_sensitive_data(
                        result["output"]
                    )

            return {
                "success": True,
                "result": result,
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat(),
                "performance": self.performance_callback.get_performance_summary(),
            }

        except Exception as e:
            self.logger.error(f"Error in LangChain processing for {self.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_capabilities(self) -> str:
        """Return agent capabilities description."""
        tool_names = [tool.name for tool in self.tools] if self.tools else []
        return f"{self.personality}. Available tools: {', '.join(tool_names)}"

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this agent."""
        return self.performance_callback.get_performance_summary()

    async def clear_memory(self):
        """Clear conversation memory."""
        try:
            self.memory.clear()
            self.logger.info(f"Memory cleared for {self.name}")
        except Exception as e:
            self.logger.error(f"Error clearing memory for {self.name}: {e}")

    async def add_to_memory(self, human_input: str, ai_output: str):
        """Add interaction to memory."""
        try:
            self.memory.save_context({"input": human_input}, {"output": ai_output})
        except Exception as e:
            self.logger.error(f"Error adding to memory for {self.name}: {e}")

    def validate_tools(self) -> bool:
        """Validate that all tools are properly configured."""
        if not self.tools:
            self.logger.warning(f"No tools configured for {self.name}")
            return False

        for tool in self.tools:
            try:
                # Basic validation - check if tool has required attributes
                if not hasattr(tool, "name") or not hasattr(tool, "description"):
                    self.logger.error(
                        f"Invalid tool configuration for {self.name}: {tool}"
                    )
                    return False
            except Exception as e:
                self.logger.error(f"Error validating tools for {self.name}: {e}")
                return False

        return True

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for the agent."""
        try:
            # Check LLM connectivity
            test_result = await self.llm.ainvoke("Hello")
            llm_healthy = bool(test_result)

            # Check tools
            tools_healthy = self.validate_tools()

            # Check agent executor
            executor_healthy = self.agent_executor is not None

            overall_healthy = llm_healthy and tools_healthy and executor_healthy

            return {
                "agent": self.name,
                "healthy": overall_healthy,
                "components": {
                    "llm": llm_healthy,
                    "tools": tools_healthy,
                    "executor": executor_healthy,
                },
                "performance": self.get_performance_metrics(),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Health check failed for {self.name}: {e}")
            return {
                "agent": self.name,
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
