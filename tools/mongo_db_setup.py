"""
Utility script to create and configure the required MongoDB collections.
This script initializes the collection structure needed for The HigherSelf Network Server.
"""

import os
import sys
import asyncio
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from loguru import logger

# Configure colored terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(message: str) -> None:
    print(f"\n{Colors.HEADER}{Colors.BOLD}{message}{Colors.END}")

def print_info(message: str) -> None:
    print(f"{Colors.BLUE}[INFO]{Colors.END} {message}")

def print_success(message: str) -> None:
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {message}")

def print_warning(message: str) -> None:
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {message}")

def print_error(message: str) -> None:
    print(f"{Colors.RED}[ERROR]{Colors.END} {message}")


class MongoDBSetup:
    """Setup class for MongoDB collections and indexes."""
    
    def __init__(self, uri: str = None):
        """Initialize MongoDB setup with connection URI."""
        self.uri = uri or os.environ.get("MONGODB_URI", "mongodb://localhost:27017/higherselfnetwork")
        self.client = None
        self.db = None
        self.db_name = self.uri.split('/')[-1]
        
    def connect(self) -> bool:
        """Connect to MongoDB and return success status."""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            # Test connection
            self.client.admin.command('ping')
            print_info(f"Connected to MongoDB at {self.uri}")
            return True
        except (ConnectionFailure, OperationFailure) as e:
            print_error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def create_collection(self, name: str, validator: Dict[str, Any] = None) -> bool:
        """Create a collection with optional schema validation."""
        try:
            # Check if collection already exists
            if name in self.db.list_collection_names():
                print_warning(f"Collection '{name}' already exists")
                return True
            
            # Create collection with validator if provided
            if validator:
                self.db.create_collection(
                    name,
                    validator={"$jsonSchema": validator}
                )
            else:
                self.db.create_collection(name)
                
            print_success(f"Created collection '{name}'")
            return True
        except Exception as e:
            print_error(f"Failed to create collection '{name}': {e}")
            return False
    
    def create_index(self, collection_name: str, field_name: str, unique: bool = False) -> bool:
        """Create an index on a collection field."""
        try:
            self.db[collection_name].create_index([(field_name, ASCENDING)], unique=unique)
            print_info(f"Created index on '{collection_name}.{field_name}' (unique={unique})")
            return True
        except Exception as e:
            print_error(f"Failed to create index on '{collection_name}.{field_name}': {e}")
            return False
    
    def setup_agents_collection(self) -> bool:
        """Set up the agents collection with indexes."""
        validator = {
            "bsonType": "object",
            "required": ["name", "agent_type"],
            "properties": {
                "name": {"bsonType": "string"},
                "agent_type": {"bsonType": "string"},
                "status": {"enum": ["active", "inactive", "error", "maintenance"]}
            }
        }
        
        success = self.create_collection("agents", validator)
        if success:
            self.create_index("agents", "id", unique=True)
            self.create_index("agents", "name", unique=True)
            self.create_index("agents", "agent_type")
        return success
    
    def setup_workflows_collection(self) -> bool:
        """Set up the workflows collection with indexes."""
        validator = {
            "bsonType": "object",
            "required": ["name", "workflow_type"],
            "properties": {
                "name": {"bsonType": "string"},
                "workflow_type": {"bsonType": "string"},
                "version": {"bsonType": "string"}
            }
        }
        
        success = self.create_collection("workflows", validator)
        if success:
            self.create_index("workflows", "id", unique=True)
            self.create_index("workflows", "name")
            self.create_index("workflows", "workflow_type")
        return success
    
    def setup_workflow_instances_collection(self) -> bool:
        """Set up the workflow_instances collection with indexes."""
        validator = {
            "bsonType": "object",
            "required": ["workflow_id", "status"],
            "properties": {
                "workflow_id": {"bsonType": "string"},
                "status": {"enum": ["pending", "running", "completed", "failed", "cancelled"]}
            }
        }
        
        success = self.create_collection("workflow_instances", validator)
        if success:
            self.create_index("workflow_instances", "id", unique=True)
            self.create_index("workflow_instances", "workflow_id")
            self.create_index("workflow_instances", "status")
        return success
    
    def setup_tasks_collection(self) -> bool:
        """Set up the tasks collection with indexes."""
        validator = {
            "bsonType": "object",
            "required": ["title", "status"],
            "properties": {
                "title": {"bsonType": "string"},
                "status": {"enum": ["pending", "in_progress", "completed", "cancelled", "blocked"]}
            }
        }
        
        success = self.create_collection("tasks", validator)
        if success:
            self.create_index("tasks", "id", unique=True)
            self.create_index("tasks", "status")
            self.create_index("tasks", "assigned_to")
            self.create_index("tasks", "workflow_instance_id")
        return success
    
    def setup_agent_communication_collection(self) -> bool:
        """Set up the agent_communication collection with indexes."""
        validator = {
            "bsonType": "object",
            "required": ["pattern_name", "source_agent_id", "target_agent_id"],
            "properties": {
                "pattern_name": {"bsonType": "string"},
                "source_agent_id": {"bsonType": "string"},
                "target_agent_id": {"bsonType": "string"}
            }
        }
        
        success = self.create_collection("agent_communication", validator)
        if success:
            self.create_index("agent_communication", "id", unique=True)
            self.create_index("agent_communication", "pattern_name")
            self.create_index("agent_communication", "source_agent_id")
            self.create_index("agent_communication", "target_agent_id")
        return success
    
    def setup_api_integrations_collection(self) -> bool:
        """Set up the api_integrations collection with indexes."""
        validator = {
            "bsonType": "object",
            "required": ["name", "platform", "api_url"],
            "properties": {
                "name": {"bsonType": "string"},
                "platform": {"bsonType": "string"},
                "api_url": {"bsonType": "string"},
                "status": {"enum": ["active", "inactive", "error", "maintenance"]}
            }
        }
        
        success = self.create_collection("api_integrations", validator)
        if success:
            self.create_index("api_integrations", "id", unique=True)
            self.create_index("api_integrations", "name", unique=True)
            self.create_index("api_integrations", "platform")
        return success
    
    def setup_system_health_collection(self) -> bool:
        """Set up the system_health collection with indexes."""
        success = self.create_collection("system_health")
        if success:
            self.create_index("system_health", "timestamp")
        return success
    
    def create_env_file(self, output_path: str = ".env.mongodb") -> None:
        """Create an .env file with MongoDB configuration."""
        env_content = f"""# MongoDB Configuration
MONGODB_URI={self.uri}
MONGODB_DB_NAME={self.db_name}
MONGODB_ENABLED=true
"""
        
        try:
            with open(output_path, "w") as f:
                f.write(env_content)
            print_success(f"Created MongoDB environment file at {output_path}")
        except Exception as e:
            print_error(f"Failed to create environment file: {e}")


async def main():
    """Main entry point for the script."""
    # Load environment variables
    load_dotenv()
    
    print_header("=== MongoDB Setup for The HigherSelf Network Server ===")
    
    # Get MongoDB URI from environment or use default
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/higherselfnetwork")
    
    # Create setup instance
    setup = MongoDBSetup(mongo_uri)
    
    # Connect to MongoDB
    if not setup.connect():
        print_error("Failed to connect to MongoDB. Setup aborted.")
        sys.exit(1)
    
    # Create collections and indexes
    print_header("\nCreating MongoDB collections and indexes...")
    
    collections_setup = [
        ("Agents", setup.setup_agents_collection),
        ("Workflows", setup.setup_workflows_collection),
        ("Workflow Instances", setup.setup_workflow_instances_collection),
        ("Tasks", setup.setup_tasks_collection),
        ("Agent Communication", setup.setup_agent_communication_collection),
        ("API Integrations", setup.setup_api_integrations_collection),
        ("System Health", setup.setup_system_health_collection)
    ]
    
    all_success = True
    for name, setup_func in collections_setup:
        print_info(f"Setting up {name} collection...")
        if not setup_func():
            all_success = False
    
    if all_success:
        print_header("\n=== MongoDB Setup Complete ===\n")
        print_info("All collections and indexes were created successfully.")
        
        # Create environment file
        setup.create_env_file()
    else:
        print_header("\n=== MongoDB Setup Incomplete ===\n")
        print_warning("Some collections or indexes could not be created. Check the logs for details.")
    
    # Close MongoDB connection
    setup.client.close()


if __name__ == "__main__":
    asyncio.run(main())
