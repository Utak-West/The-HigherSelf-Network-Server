#!/usr/bin/env python3
"""
MongoDB Setup Validation Script for HigherSelf Network

This script validates the MongoDB configuration and setup for the HigherSelf Network server.
It checks connections, collections, indexes, and performs basic functionality tests.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import pymongo
from dotenv import load_dotenv
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import (ConnectionFailure, OperationFailure,
                            ServerSelectionTimeoutError)


# Color codes for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


class MongoDBValidator:
    """MongoDB setup validator for HigherSelf Network."""

    def __init__(self):
        """Initialize the validator."""
        self.mongo_uri = None
        self.db_name = None
        self.client = None
        self.db = None
        self.async_client = None
        self.async_db = None

        # Expected collections
        self.expected_collections = [
            "agents",
            "workflows",
            "workflow_instances",
            "tasks",
            "agent_communication",
            "agent_communication_registry",
            "api_integrations",
            "system_health",
            "data_transformations",
            "notification_templates",
            "use_cases",
            "business_entities",
            "contacts_profiles",
            "community_hub",
            "products_services",
            "marketing_campaigns",
            "feedback_surveys",
            "rewards_bounties",
        ]

        # Expected indexes for key collections
        self.expected_indexes = {
            "agents": ["id_", "name_", "status_", "agent_type_", "last_active_"],
            "workflows": ["id_", "name_", "workflow_type_", "created_at_"],
            "tasks": ["id_", "assigned_agent_", "status_", "priority_", "due_date_"],
            "system_health": ["timestamp_"],
        }

    def load_environment(self) -> bool:
        """Load and validate environment variables."""
        print_info("Loading environment variables...")

        # Load .env file
        load_dotenv()

        # Get MongoDB configuration
        self.mongo_uri = os.environ.get("MONGODB_URI")
        self.db_name = os.environ.get("MONGODB_DB_NAME", "higherselfnetwork")

        if not self.mongo_uri:
            print_error("MONGODB_URI not found in environment variables")
            return False

        print_success(f"MongoDB URI: {self.mongo_uri}")
        print_success(f"Database name: {self.db_name}")
        return True

    def test_connection(self) -> bool:
        """Test MongoDB connection."""
        print_info("Testing MongoDB connection...")

        try:
            # Create client with timeout
            self.client = MongoClient(
                self.mongo_uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000
            )

            # Test connection
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]

            print_success("Successfully connected to MongoDB")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print_error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            print_error(f"Unexpected error connecting to MongoDB: {e}")
            return False

    async def test_async_connection(self) -> bool:
        """Test async MongoDB connection."""
        print_info("Testing async MongoDB connection...")

        try:
            # Create async client
            self.async_client = AsyncIOMotorClient(
                self.mongo_uri, serverSelectionTimeoutMS=5000
            )

            # Test connection
            await self.async_client.admin.command("ping")
            self.async_db = self.async_client[self.db_name]

            print_success("Successfully connected to MongoDB (async)")
            return True

        except Exception as e:
            print_error(f"Failed to connect to MongoDB (async): {e}")
            return False

    def validate_collections(self) -> bool:
        """Validate that all expected collections exist."""
        print_info("Validating collections...")

        try:
            existing_collections = self.db.list_collection_names()
            missing_collections = []

            for collection in self.expected_collections:
                if collection in existing_collections:
                    print_success(f"Collection '{collection}' exists")
                else:
                    missing_collections.append(collection)
                    print_warning(f"Collection '{collection}' missing")

            if missing_collections:
                print_error(f"Missing collections: {', '.join(missing_collections)}")
                return False
            else:
                print_success("All expected collections exist")
                return True

        except Exception as e:
            print_error(f"Error validating collections: {e}")
            return False

    def validate_indexes(self) -> bool:
        """Validate that expected indexes exist."""
        print_info("Validating indexes...")

        try:
            all_indexes_valid = True

            for collection_name, expected_indexes in self.expected_indexes.items():
                if collection_name not in self.db.list_collection_names():
                    print_warning(
                        f"Collection '{collection_name}' not found, skipping index validation"
                    )
                    continue

                collection = self.db[collection_name]
                existing_indexes = [idx["name"] for idx in collection.list_indexes()]

                print_info(f"Checking indexes for '{collection_name}':")

                for expected_index in expected_indexes:
                    if expected_index in existing_indexes:
                        print_success(f"  Index '{expected_index}' exists")
                    else:
                        print_warning(f"  Index '{expected_index}' missing")
                        all_indexes_valid = False

            return all_indexes_valid

        except Exception as e:
            print_error(f"Error validating indexes: {e}")
            return False

    def test_basic_operations(self) -> bool:
        """Test basic CRUD operations."""
        print_info("Testing basic CRUD operations...")

        try:
            test_collection = self.db["test_validation"]
            test_doc = {
                "test_id": "validation_test",
                "timestamp": datetime.utcnow(),
                "data": "MongoDB validation test",
            }

            # Insert
            result = test_collection.insert_one(test_doc)
            print_success(f"Insert operation successful: {result.inserted_id}")

            # Find
            found_doc = test_collection.find_one({"test_id": "validation_test"})
            if found_doc:
                print_success("Find operation successful")
            else:
                print_error("Find operation failed")
                return False

            # Update
            update_result = test_collection.update_one(
                {"test_id": "validation_test"}, {"$set": {"updated": True}}
            )
            if update_result.modified_count == 1:
                print_success("Update operation successful")
            else:
                print_error("Update operation failed")
                return False

            # Delete
            delete_result = test_collection.delete_one({"test_id": "validation_test"})
            if delete_result.deleted_count == 1:
                print_success("Delete operation successful")
            else:
                print_error("Delete operation failed")
                return False

            # Clean up test collection
            test_collection.drop()
            print_success("Test collection cleaned up")

            return True

        except Exception as e:
            print_error(f"Error testing basic operations: {e}")
            return False

    async def test_async_operations(self) -> bool:
        """Test async CRUD operations."""
        print_info("Testing async CRUD operations...")

        try:
            test_collection = self.async_db["test_async_validation"]
            test_doc = {
                "test_id": "async_validation_test",
                "timestamp": datetime.utcnow(),
                "data": "MongoDB async validation test",
            }

            # Insert
            result = await test_collection.insert_one(test_doc)
            print_success(f"Async insert operation successful: {result.inserted_id}")

            # Find
            found_doc = await test_collection.find_one(
                {"test_id": "async_validation_test"}
            )
            if found_doc:
                print_success("Async find operation successful")
            else:
                print_error("Async find operation failed")
                return False

            # Clean up
            await test_collection.drop()
            print_success("Async test collection cleaned up")

            return True

        except Exception as e:
            print_error(f"Error testing async operations: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        print_info("Gathering database statistics...")

        try:
            stats = self.db.command("dbStats")

            print_info(f"Database: {stats.get('db', 'N/A')}")
            print_info(f"Collections: {stats.get('collections', 'N/A')}")
            print_info(f"Data size: {stats.get('dataSize', 0) / 1024 / 1024:.2f} MB")
            print_info(
                f"Storage size: {stats.get('storageSize', 0) / 1024 / 1024:.2f} MB"
            )
            print_info(f"Indexes: {stats.get('indexes', 'N/A')}")
            print_info(f"Index size: {stats.get('indexSize', 0) / 1024 / 1024:.2f} MB")

            return stats

        except Exception as e:
            print_error(f"Error getting database stats: {e}")
            return {}

    def cleanup(self):
        """Clean up connections."""
        if self.client:
            self.client.close()
        if self.async_client:
            self.async_client.close()


async def main():
    """Main validation function."""
    print_header("MongoDB Setup Validation for HigherSelf Network")

    validator = MongoDBValidator()

    try:
        # Load environment
        if not validator.load_environment():
            sys.exit(1)

        # Test sync connection
        if not validator.test_connection():
            sys.exit(1)

        # Test async connection
        if not await validator.test_async_connection():
            sys.exit(1)

        # Validate collections
        collections_valid = validator.validate_collections()

        # Validate indexes
        indexes_valid = validator.validate_indexes()

        # Test basic operations
        basic_ops_valid = validator.test_basic_operations()

        # Test async operations
        async_ops_valid = await validator.test_async_operations()

        # Get database stats
        validator.get_database_stats()

        # Summary
        print_header("Validation Summary")

        if all([collections_valid, indexes_valid, basic_ops_valid, async_ops_valid]):
            print_success("✅ MongoDB setup validation PASSED")
            print_info(
                "Your MongoDB configuration is ready for HigherSelf Network operations"
            )
        else:
            print_error("❌ MongoDB setup validation FAILED")
            print_info(
                "Please review the errors above and run the setup script if needed"
            )
            sys.exit(1)

    except KeyboardInterrupt:
        print_warning("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error during validation: {e}")
        sys.exit(1)
    finally:
        validator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
