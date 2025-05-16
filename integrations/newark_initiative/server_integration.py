"""
Newark Initiative Integration Module for HigherSelf Network Server

This module provides the integration point between the Newark specialized agents
and the main HigherSelf Network Server. It initializes Grace Fields and the other
Newark agents and registers them with the server.
"""

import os
import asyncio
from typing import Dict, Any, Optional
from loguru import logger

# Import Newark components
from server_protocols.newark_config import NewarkConfig
from server_protocols.newark_orchestration import GraceFieldsOrchestrator
from server_protocols.newark_knowledge_agent import KnowledgeManagementAgent
from server_protocols.newark_wellness_agent import WellnessCoordinatorAgent
from server_protocols.newark_outreach_agent import OutreachCoordinatorAgent
from server_protocols.newark_evaluation_agent import ProgramEvaluatorAgent
from server_protocols.newark_api_integration import newark_router

# Import HigherSelf Server components
from agents.base_agent import AgentRegistry
from utils.notion_client import get_notion_client


class NewarkIntegration:
    """Integration class for the Newark Well initiative agents."""
    
    def __init__(self):
        """Initialize the Newark integration."""
        self.initialized = False
        self.grace_fields = None
        self.notion_client = None
        self.agents = {}
        
    async def initialize(self) -> bool:
        """
        Initialize all Newark agents and register them with the HigherSelf Network Server.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        logger.info("Initializing Newark Well initiative integration...")
        
        # Check if Newark integration is enabled
        if not self._is_enabled():
            logger.warning("Newark integration is disabled. Set NEWARK_API_ENABLED=True to enable.")
            return False
            
        # Check if configuration is valid
        if not NewarkConfig.is_configured():
            logger.error("Newark integration is not properly configured.")
            logger.error("Please set all required environment variables as specified in the documentation.")
            return False
            
        try:
            # Get agent configurations
            agent_configs = NewarkConfig.get_agent_configs()
            
            # Get Notion client
            self.notion_client = get_notion_client()
            
            # Initialize specialized agents
            logger.info("Initializing Newark specialized agents...")
            
            # Cora: Knowledge Management Agent
            cora = KnowledgeManagementAgent(
                notion_client=self.notion_client,
                knowledge_db_id=agent_configs['cora']['knowledge_db_id'],
                training_materials_id=agent_configs['cora']['training_materials_id']
            )
            
            # Cassia: Wellness Coordinator Agent
            cassia = WellnessCoordinatorAgent(
                notion_client=self.notion_client,
                wellness_resources_id=agent_configs['cassia']['wellness_resources_id'],
                wellness_checkins_id=agent_configs['cassia']['wellness_checkins_id']
            )
            
            # Terra: Outreach Coordinator Agent
            terra = OutreachCoordinatorAgent(
                notion_client=self.notion_client,
                client_interactions_id=agent_configs['terra']['client_interactions_id'],
                service_providers_id=agent_configs['terra']['service_providers_id'],
                resource_availability_id=agent_configs['terra']['resource_availability_id']
            )
            
            # Vesta: Program Evaluator Agent
            vesta = ProgramEvaluatorAgent(
                notion_client=self.notion_client,
                program_metrics_id=agent_configs['vesta']['program_metrics_id'],
                report_configurations_id=agent_configs['vesta']['report_configurations_id'],
                report_outputs_id=agent_configs['vesta']['report_outputs_id']
            )
            
            # Initialize Grace Fields: Orchestration Agent
            self.grace_fields = GraceFieldsOrchestrator(
                knowledge_agent=cora,
                wellness_agent=cassia,
                outreach_agent=terra,
                evaluation_agent=vesta
            )
            
            # Store agents for access
            self.agents = {
                "grace_fields": self.grace_fields,
                "cora": cora,
                "cassia": cassia,
                "terra": terra,
                "vesta": vesta
            }
            
            # Register agents with HigherSelf Network Server
            self._register_agents()
            
            # Set initialization flag
            self.initialized = True
            
            logger.info("Newark Well initiative integration successfully initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Newark integration: {str(e)}")
            return False
    
    def _is_enabled(self) -> bool:
        """Check if Newark integration is enabled."""
        return os.getenv("NEWARK_API_ENABLED", "False").lower() == "true"
    
    def _register_agents(self) -> None:
        """Register Newark agents with the HigherSelf Network Server's AgentRegistry."""
        if not self.agents:
            logger.warning("No Newark agents to register")
            return
            
        # Register all agents with the registry
        for name, agent in self.agents.items():
            try:
                AgentRegistry.register_agent(name, agent)
                logger.debug(f"Registered Newark agent: {name}")
            except Exception as e:
                logger.error(f"Failed to register agent {name}: {str(e)}")
    
    def get_grace_fields(self) -> Optional[GraceFieldsOrchestrator]:
        """
        Get the Grace Fields agent.
        
        Returns:
            Optional[GraceFieldsOrchestrator]: Grace Fields agent if initialized, None otherwise
        """
        return self.grace_fields if self.initialized else None
    
    def get_agent(self, agent_name: str) -> Any:
        """
        Get a specific Newark agent by name.
        
        Args:
            agent_name (str): Name of the agent to retrieve
            
        Returns:
            Any: The requested agent if found and initialized, None otherwise
        """
        return self.agents.get(agent_name) if self.initialized else None


# Create singleton instance
newark = NewarkIntegration()


async def initialize_newark() -> bool:
    """
    Initialize the Newark integration.
    This function should be called during server startup.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    return await newark.initialize()


def get_newark_router():
    """
    Get the Newark API router.
    This function should be called when setting up the FastAPI application.
    
    Returns:
        APIRouter: The Newark API router
    """
    return newark_router


# Helper function to get Grace Fields
def get_grace_fields():
    """Get the Grace Fields agent."""
    return newark.get_grace_fields()


# Usage example
if __name__ == "__main__":
    # This is just for testing/demonstration
    async def main():
        success = await initialize_newark()
        if success:
            grace = get_grace_fields()
            print(f"Grace Fields initialized: {grace is not None}")
            
            # Example of checking agent health
            health = await grace.check_health()
            print(f"Grace Fields health: {health}")
    
    asyncio.run(main())
