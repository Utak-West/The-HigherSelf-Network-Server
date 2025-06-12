"""
Custom callbacks for monitoring LangChain operations.
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.callbacks.base import BaseCallbackHandler
from loguru import logger

# Optional metrics - only use if prometheus_client is available
try:
    from prometheus_client import Counter, Gauge, Histogram

    LANGCHAIN_REQUESTS = Counter(
        "langchain_requests_total", "Total LangChain requests", ["agent", "model"]
    )
    LANGCHAIN_ERRORS = Counter(
        "langchain_errors_total", "Total LangChain errors", ["agent", "error_type"]
    )
    LANGCHAIN_DURATION = Histogram(
        "langchain_duration_seconds", "LangChain request duration", ["agent", "model"]
    )
    LANGCHAIN_TOKEN_USAGE = Counter(
        "langchain_token_usage_total", "Total tokens used", ["agent", "model", "type"]
    )
    LANGCHAIN_ACTIVE_AGENTS = Gauge(
        "langchain_active_agents", "Number of active LangChain agents"
    )

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    logger.warning("Prometheus metrics not available for LangChain monitoring")


class MonitoringCallback(BaseCallbackHandler):
    """Custom callback for monitoring LangChain operations."""

    def __init__(self, agent_name: str, notion_client=None):
        self.agent_name = agent_name
        self.notion_client = notion_client
        self.start_time = None
        self.current_model = None
        self.session_id = None
        self.operation_count = 0

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Log when LLM starts processing."""
        self.start_time = time.time()
        self.current_model = serialized.get("name", "unknown")
        self.operation_count += 1

        if METRICS_AVAILABLE:
            LANGCHAIN_REQUESTS.labels(
                agent=self.agent_name, model=self.current_model
            ).inc()
            LANGCHAIN_ACTIVE_AGENTS.inc()

        logger.info(
            f"LLM started for {self.agent_name} using {self.current_model} "
            f"(prompt length: {sum(len(p) for p in prompts)} chars)"
        )

    def on_llm_end(self, response, **kwargs):
        """Log when LLM completes processing."""
        if self.start_time:
            duration = time.time() - self.start_time

            if METRICS_AVAILABLE:
                LANGCHAIN_DURATION.labels(
                    agent=self.agent_name, model=self.current_model
                ).observe(duration)
                LANGCHAIN_ACTIVE_AGENTS.dec()

                # Track token usage if available
                if hasattr(response, "llm_output") and response.llm_output:
                    token_usage = response.llm_output.get("token_usage", {})
                    if token_usage:
                        LANGCHAIN_TOKEN_USAGE.labels(
                            agent=self.agent_name,
                            model=self.current_model,
                            type="prompt",
                        ).inc(token_usage.get("prompt_tokens", 0))

                        LANGCHAIN_TOKEN_USAGE.labels(
                            agent=self.agent_name,
                            model=self.current_model,
                            type="completion",
                        ).inc(token_usage.get("completion_tokens", 0))

            logger.info(
                f"LLM completed for {self.agent_name} in {duration:.2f}s "
                f"(operation #{self.operation_count})"
            )

    def on_llm_error(self, error: Exception, **kwargs):
        """Log LLM errors."""
        error_type = type(error).__name__

        if METRICS_AVAILABLE:
            LANGCHAIN_ERRORS.labels(agent=self.agent_name, error_type=error_type).inc()
            LANGCHAIN_ACTIVE_AGENTS.dec()

        logger.error(f"LLM error for {self.agent_name}: {error_type} - {str(error)}")

        # Log to Notion if available
        if self.notion_client:
            self._log_error_to_notion(error, error_type)

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """Log when tool starts."""
        tool_name = serialized.get("name", "unknown")
        logger.debug(
            f"Tool {tool_name} started for {self.agent_name} "
            f"(input length: {len(input_str)} chars)"
        )

    def on_tool_end(self, output: str, **kwargs):
        """Log when tool completes."""
        logger.debug(
            f"Tool completed for {self.agent_name} "
            f"(output length: {len(output)} chars)"
        )

    def on_tool_error(self, error: Exception, **kwargs):
        """Log tool errors."""
        error_type = type(error).__name__
        logger.error(f"Tool error for {self.agent_name}: {error_type} - {str(error)}")

    def on_agent_action(self, action, **kwargs):
        """Log agent actions."""
        logger.debug(f"Agent {self.agent_name} taking action: {action.tool}")

    def on_agent_finish(self, finish, **kwargs):
        """Log agent completion."""
        logger.info(f"Agent {self.agent_name} finished processing")

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs
    ):
        """Log when chain starts."""
        chain_name = serialized.get("name", "unknown")
        logger.debug(f"Chain {chain_name} started for {self.agent_name}")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
        """Log when chain completes."""
        logger.debug(f"Chain completed for {self.agent_name}")

    def on_chain_error(self, error: Exception, **kwargs):
        """Log chain errors."""
        error_type = type(error).__name__
        logger.error(f"Chain error for {self.agent_name}: {error_type} - {str(error)}")

    def _log_error_to_notion(self, error: Exception, error_type: str):
        """Log error to Notion for persistent tracking."""
        try:
            if not self.notion_client:
                return

            error_data = {
                "agent": self.agent_name,
                "error_type": error_type,
                "error_message": str(error),
                "timestamp": datetime.utcnow().isoformat(),
                "operation_count": self.operation_count,
                "model": self.current_model,
            }

            # This would need to be implemented based on your Notion schema
            # self.notion_client.create_page(
            #     database_id="error_logs_database_id",
            #     properties={
            #         "Agent": {"select": {"name": self.agent_name}},
            #         "Error Type": {"select": {"name": error_type}},
            #         "Details": {"rich_text": [{"text": {"content": json.dumps(error_data)}}]},
            #         "Timestamp": {"date": {"start": error_data["timestamp"]}}
            #     }
            # )

        except Exception as e:
            logger.error(f"Failed to log error to Notion: {e}")


class PerformanceCallback(BaseCallbackHandler):
    """Callback focused on performance monitoring."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.performance_data = {
            "total_requests": 0,
            "total_duration": 0,
            "total_tokens": 0,
            "errors": 0,
        }

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Track request start."""
        self.performance_data["total_requests"] += 1
        self.start_time = time.time()

    def on_llm_end(self, response, **kwargs):
        """Track request completion."""
        if hasattr(self, "start_time"):
            duration = time.time() - self.start_time
            self.performance_data["total_duration"] += duration

            # Track tokens if available
            if hasattr(response, "llm_output") and response.llm_output:
                token_usage = response.llm_output.get("token_usage", {})
                if token_usage:
                    total_tokens = token_usage.get("total_tokens", 0)
                    self.performance_data["total_tokens"] += total_tokens

    def on_llm_error(self, error: Exception, **kwargs):
        """Track errors."""
        self.performance_data["errors"] += 1

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        avg_duration = (
            self.performance_data["total_duration"]
            / self.performance_data["total_requests"]
            if self.performance_data["total_requests"] > 0
            else 0
        )

        error_rate = (
            self.performance_data["errors"] / self.performance_data["total_requests"]
            if self.performance_data["total_requests"] > 0
            else 0
        )

        return {
            "agent": self.agent_name,
            "total_requests": self.performance_data["total_requests"],
            "average_duration": round(avg_duration, 2),
            "total_tokens": self.performance_data["total_tokens"],
            "error_rate": round(error_rate * 100, 2),
            "errors": self.performance_data["errors"],
        }
