#!/usr/bin/env python3
"""
Grace Fields Training Module

This module provides training capabilities for the Grace Fields orchestrator,
ensuring it understands agent best practices and can effectively coordinate
the agent collective in The HigherSelf Network Server.
"""

import os
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from services.notion_service import NotionService
from services.ai_router import AIRouter
from utils.message_bus import MessageBus, AgentMessage
from models.base import AgentCapability
from agents import (
    Nyra, Solari, Ruvo, Liora, Sage, Elan, Zevi,
    create_grace_orchestrator
)


class GraceFieldsTrainer:
    """
    Trainer for the Grace Fields orchestrator.
    
    This class provides methods to train Grace Fields on agent best practices,
    workflow patterns, and effective coordination strategies.
    """
    
    def __init__(self, notion_service: NotionService, ai_router: Optional[AIRouter] = None):
        """
        Initialize the Grace Fields trainer.
        
        Args:
            notion_service: NotionService instance for data persistence
            ai_router: Optional AIRouter for advanced training capabilities
        """
        self.notion_service = notion_service
        self.ai_router = ai_router
        self.message_bus = MessageBus(notion_service)
        self.logger = logging.getLogger("grace_fields_trainer")
        
        # Initialize agents and Grace
        self.agents = {}
        self.grace = None
        
    async def initialize(self):
        """Initialize the training environment."""
        # Initialize all agent personalities
        self.agents = {
            "nyra": Nyra(notion_client=self.notion_service),
            "solari": Solari(notion_client=self.notion_service),
            "ruvo": Ruvo(notion_client=self.notion_service),
            "liora": Liora(notion_client=self.notion_service),
            "sage": Sage(notion_client=self.notion_service),
            "elan": Elan(notion_client=self.notion_service),
            "zevi": Zevi(notion_client=self.notion_service)
        }
        
        # Create Grace Fields orchestrator
        self.grace = create_grace_orchestrator(self.notion_service, self.message_bus)
        
        # Subscribe all agents to the message bus
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'process_message'):
                self.message_bus.subscribe(agent_id, agent.process_message)
        
        # Subscribe Grace to the message bus
        self.message_bus.subscribe("grace", self.grace.process_message)
        
        # Subscribe to training monitor
        self.message_bus.subscribe("training_monitor", self.monitor_message)
        
        self.logger.info("Training environment initialized")
        
    async def train_on_best_practices(self):
        """Train Grace Fields on agent best practices."""
        self.logger.info("Starting best practices training")
        
        # Load best practices from Notion
        best_practices = await self.load_best_practices()
        
        # Train on each best practice
        for practice in best_practices:
            await self.train_on_practice(practice)
            
        self.logger.info("Best practices training completed")
        
    async def load_best_practices(self) -> List[Dict[str, Any]]:
        """Load agent best practices from Notion."""
        # Query the Best Practices database in Notion
        filter_conditions = {
            "property": "status",
            "select": {
                "equals": "Active"
            }
        }
        
        practices = await self.notion_service.query_database(
            "AgentBestPractices", 
            filter_conditions
        )
        
        return practices
        
    async def train_on_practice(self, practice: Dict[str, Any]):
        """Train Grace on a specific best practice."""
        practice_name = practice.get("name", "Unnamed Practice")
        practice_type = practice.get("type", "General")
        practice_description = practice.get("description", "")
        
        self.logger.info(f"Training on: {practice_name} ({practice_type})")
        
        # Create a training message
        training_message = AgentMessage(
            sender="GraceFieldsTrainer",
            recipient="GraceOrchestrator",
            message_type="training_best_practice",
            payload={
                "practice_name": practice_name,
                "practice_type": practice_type,
                "practice_description": practice_description,
                "examples": practice.get("examples", []),
                "is_training": True
            }
        )
        
        # Send the training message
        await self.message_bus.publish(training_message)
        
        # Allow time for processing
        await asyncio.sleep(1)
        
    async def train_on_workflow_patterns(self):
        """Train Grace Fields on effective workflow patterns."""
        self.logger.info("Starting workflow patterns training")
        
        # Load workflow patterns from Notion
        patterns = await self.load_workflow_patterns()
        
        # Train on each workflow pattern
        for pattern in patterns:
            await self.train_on_pattern(pattern)
            
        self.logger.info("Workflow patterns training completed")
        
    async def load_workflow_patterns(self) -> List[Dict[str, Any]]:
        """Load workflow patterns from Notion."""
        # Query the Workflow Patterns database in Notion
        filter_conditions = {
            "property": "status",
            "select": {
                "equals": "Active"
            }
        }
        
        patterns = await self.notion_service.query_database(
            "WorkflowPatterns", 
            filter_conditions
        )
        
        return patterns
        
    async def train_on_pattern(self, pattern: Dict[str, Any]):
        """Train Grace on a specific workflow pattern."""
        pattern_name = pattern.get("name", "Unnamed Pattern")
        pattern_description = pattern.get("description", "")
        pattern_steps = pattern.get("steps", [])
        
        self.logger.info(f"Training on workflow pattern: {pattern_name}")
        
        # Create a training message
        training_message = AgentMessage(
            sender="GraceFieldsTrainer",
            recipient="GraceOrchestrator",
            message_type="training_workflow_pattern",
            payload={
                "pattern_name": pattern_name,
                "pattern_description": pattern_description,
                "pattern_steps": pattern_steps,
                "is_training": True
            }
        )
        
        # Send the training message
        await self.message_bus.publish(training_message)
        
        # Allow time for processing
        await asyncio.sleep(1)
        
    async def run_training_scenarios(self):
        """Run training scenarios to test Grace's understanding."""
        self.logger.info("Starting training scenarios")
        
        # Run lead capture scenario
        await self.run_lead_capture_scenario()
        
        # Run content lifecycle scenario
        await self.run_content_lifecycle_scenario()
        
        # Run error handling scenario
        await self.run_error_handling_scenario()
        
        self.logger.info("Training scenarios completed")
        
    async def run_lead_capture_scenario(self):
        """Run a lead capture training scenario."""
        self.logger.info("Running lead capture scenario")
        
        # Simulate a new lead
        lead_data = {
            "source": "training_scenario",
            "form_id": "contact_form",
            "business_entity_id": "the_connection_practice",
            "form_data": {
                "name": "Training User",
                "email": "training@example.com",
                "phone": "+1-555-000-0000",
                "interest": "Training Scenario",
                "message": "This is a training scenario for lead capture."
            },
            "is_training": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Process the lead through Grace
        result = await self.grace.route_event("website_form", lead_data)
        
        # Evaluate the result
        self.evaluate_training_result("lead_capture", result)
        
    async def run_content_lifecycle_scenario(self):
        """Run a content lifecycle training scenario."""
        self.logger.info("Running content lifecycle scenario")
        
        # Simulate content creation
        content_data = {
            "content_type": "blog_post",
            "business_entity_id": "the_7_space",
            "title": "Training Content",
            "description": "This is a training scenario for content lifecycle.",
            "is_training": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Process the content through Grace
        result = await self.grace.route_event("content_idea", content_data)
        
        # Evaluate the result
        self.evaluate_training_result("content_lifecycle", result)
        
    async def run_error_handling_scenario(self):
        """Run an error handling training scenario."""
        self.logger.info("Running error handling scenario")
        
        # Simulate an error condition
        error_data = {
            "business_entity_id": "the_connection_practice",
            "error_type": "missing_data",
            "is_training": True,
            "should_trigger_error": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Process the error through Grace
        result = await self.grace.route_event("process_booking", error_data)
        
        # Evaluate the result
        self.evaluate_training_result("error_handling", result)
        
    def evaluate_training_result(self, scenario_type: str, result: Dict[str, Any]):
        """Evaluate the result of a training scenario."""
        success = False
        
        if scenario_type == "lead_capture":
            # Check if Nyra processed the lead
            success = "nyra" in result and result["nyra"].get("status") != "error"
        elif scenario_type == "content_lifecycle":
            # Check if Elan processed the content
            success = "elan" in result and result["elan"].get("status") != "error"
        elif scenario_type == "error_handling":
            # Check if Grace handled the error appropriately
            success = "error" in result or result.get("status") == "error"
            
        if success:
            self.logger.info(f"Training scenario {scenario_type} completed successfully")
        else:
            self.logger.warning(f"Training scenario {scenario_type} failed")
            
        # Record training result in Notion
        asyncio.create_task(self.record_training_result(scenario_type, success, result))
        
    async def record_training_result(self, scenario_type: str, success: bool, result: Dict[str, Any]):
        """Record training result in Notion."""
        training_record = {
            "scenario_type": scenario_type,
            "success": success,
            "result": json.dumps(result),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.notion_service.create_page("AgentTrainingResults", training_record)
        
    async def monitor_message(self, message: AgentMessage):
        """Monitor messages during training."""
        if message.message_type.startswith("training_"):
            self.logger.info(f"Training message: {message.message_type} from {message.sender} to {message.recipient}")


async def run_training():
    """Run the Grace Fields training process."""
    # Initialize Notion service
    notion_service = NotionService.from_env()
    
    # Initialize AI router if available
    ai_router = None
    try:
        from services.ai_router import AIRouter
        ai_router = AIRouter()
        await ai_router.initialize()
    except Exception as e:
        logging.warning(f"Could not initialize AI router: {e}")
    
    # Create and initialize trainer
    trainer = GraceFieldsTrainer(notion_service, ai_router)
    await trainer.initialize()
    
    # Run training
    await trainer.train_on_best_practices()
    await trainer.train_on_workflow_patterns()
    await trainer.run_training_scenarios()
    
    logging.info("Grace Fields training completed")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run the training
    asyncio.run(run_training())
