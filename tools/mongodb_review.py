#!/usr/bin/env python3
"""
MongoDB Configuration Review Script for HigherSelf Network

This script provides a comprehensive review of the current MongoDB configuration,
including connection details, collections, indexes, and data validation.
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import pymongo
    from pymongo import MongoClient
    from pymongo.errors import (ConnectionFailure, OperationFailure,
                                ServerSelectionTimeoutError)
except ImportError:
    print("❌ PyMongo not installed. Please run: pip install pymongo")
    sys.exit(1)

from dotenv import load_dotenv


# Color codes for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}\n")


def print_section(text: str):
    """Print a section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}📋 {text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.END}")


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


def print_data(label: str, value: Any):
    """Print formatted data."""
    print(f"{Colors.CYAN}{label}:{Colors.END} {value}")


class MongoDBReviewer:
    """MongoDB configuration reviewer for HigherSelf Network."""

    def __init__(self):
        """Initialize the reviewer."""
        load_dotenv()

        self.mongo_uri = os.environ.get("MONGODB_URI")
        self.db_name = os.environ.get("MONGODB_DB_NAME", "higherselfnetwork")
        self.client = None
        self.db = None

        # Expected collections for HigherSelf Network
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

    def connect(self) -> bool:
        """Connect to MongoDB with multiple URI attempts."""
        connection_attempts = []

        # Try environment URI first
        if self.mongo_uri:
            connection_attempts.append(self.mongo_uri)

        # Try common local configurations
        connection_attempts.extend(
            [
                "mongodb://localhost:27017/higherselfnetwork",
                "mongodb://higherself_app:secure_app_password@localhost:27017/higherselfnetwork",
                "mongodb://admin:secure_root_password@localhost:27017/higherselfnetwork",
                "mongodb://127.0.0.1:27017/higherselfnetwork",
            ]
        )

        for uri in connection_attempts:
            try:
                print_info(
                    f"Attempting connection to: {uri.split('@')[-1] if '@' in uri else uri}"
                )

                self.client = MongoClient(
                    uri, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000
                )

                # Test connection
                self.client.admin.command("ping")
                self.db = self.client[self.db_name]

                print_success(f"Successfully connected to MongoDB!")
                self.mongo_uri = uri
                return True

            except Exception as e:
                print_warning(f"Connection failed: {str(e)[:100]}...")
                continue

        print_error("Could not connect to MongoDB with any configuration")
        return False

    def review_connection_details(self):
        """Review MongoDB connection details."""
        print_section("1. MongoDB Connection Details")

        try:
            # Server info
            server_info = self.client.server_info()
            print_data("MongoDB Version", server_info.get("version", "Unknown"))
            print_data(
                "Connection URI",
                (
                    self.mongo_uri.split("@")[-1]
                    if "@" in self.mongo_uri
                    else self.mongo_uri
                ),
            )
            print_data("Database Name", self.db_name)

            # Connection status
            is_master = self.db.command("isMaster")
            print_data(
                "Server Type", "Primary" if is_master.get("ismaster") else "Secondary"
            )
            print_data("Max Wire Version", is_master.get("maxWireVersion", "Unknown"))

            # Database list
            databases = self.client.list_database_names()
            print_data("Available Databases", ", ".join(databases))

            print_success("Connection details retrieved successfully")

        except Exception as e:
            print_error(f"Failed to get connection details: {e}")

    def review_collections(self):
        """Review collections and document counts."""
        print_section("2. Collections and Document Counts")

        try:
            existing_collections = self.db.list_collection_names()

            if not existing_collections:
                print_warning("No collections found in database")
                return

            print_info(f"Found {len(existing_collections)} collections:")
            print()

            # Table header
            print(f"{'Collection Name':<30} {'Documents':<12} {'Status':<15}")
            print("-" * 60)

            total_documents = 0

            for collection_name in sorted(existing_collections):
                try:
                    count = self.db[collection_name].count_documents({})
                    total_documents += count

                    # Check if it's an expected collection
                    status = (
                        "✓ Expected"
                        if collection_name in self.expected_collections
                        else "⚠ Additional"
                    )

                    print(f"{collection_name:<30} {count:<12} {status:<15}")

                except Exception as e:
                    print(f"{collection_name:<30} {'Error':<12} {'✗ Failed':<15}")

            print("-" * 60)
            print(f"{'TOTAL':<30} {total_documents:<12}")
            print()

            # Check for missing expected collections
            missing_collections = set(self.expected_collections) - set(
                existing_collections
            )
            if missing_collections:
                print_warning(
                    f"Missing expected collections: {', '.join(missing_collections)}"
                )
            else:
                print_success("All expected collections are present")

        except Exception as e:
            print_error(f"Failed to review collections: {e}")

    def review_indexes(self):
        """Review indexes for key collections."""
        print_section("3. Index Validation")

        key_collections = [
            "agents",
            "workflows",
            "tasks",
            "system_health",
            "agent_communication",
        ]

        try:
            for collection_name in key_collections:
                if collection_name not in self.db.list_collection_names():
                    print_warning(
                        f"Collection '{collection_name}' not found, skipping index check"
                    )
                    continue

                print_info(f"Indexes for '{collection_name}':")

                collection = self.db[collection_name]
                indexes = list(collection.list_indexes())

                for index in indexes:
                    index_name = index.get("name", "Unknown")
                    index_keys = list(index.get("key", {}).keys())
                    unique = index.get("unique", False)

                    unique_marker = " (UNIQUE)" if unique else ""
                    print(f"  ✓ {index_name}: {', '.join(index_keys)}{unique_marker}")

                print()

        except Exception as e:
            print_error(f"Failed to review indexes: {e}")

    def review_database_stats(self):
        """Review database statistics."""
        print_section("4. Database Statistics and Performance")

        try:
            # Database stats
            db_stats = self.db.command("dbStats")

            print_info("Storage Statistics:")
            print_data(
                "  Data Size", f"{db_stats.get('dataSize', 0) / 1024 / 1024:.2f} MB"
            )
            print_data(
                "  Storage Size",
                f"{db_stats.get('storageSize', 0) / 1024 / 1024:.2f} MB",
            )
            print_data(
                "  Index Size", f"{db_stats.get('indexSize', 0) / 1024 / 1024:.2f} MB"
            )
            print_data("  Collections", db_stats.get("collections", 0))
            print_data("  Indexes", db_stats.get("indexes", 0))
            print_data("  Objects", db_stats.get("objects", 0))

            # Server status (if accessible)
            try:
                server_status = self.db.command("serverStatus")

                print_info("Performance Metrics:")
                connections = server_status.get("connections", {})
                print_data("  Current Connections", connections.get("current", "N/A"))
                print_data(
                    "  Available Connections", connections.get("available", "N/A")
                )

                opcounters = server_status.get("opcounters", {})
                print_data("  Total Inserts", opcounters.get("insert", "N/A"))
                print_data("  Total Queries", opcounters.get("query", "N/A"))
                print_data("  Total Updates", opcounters.get("update", "N/A"))

                memory = server_status.get("mem", {})
                print_data("  Resident Memory", f"{memory.get('resident', 0)} MB")
                print_data("  Virtual Memory", f"{memory.get('virtual', 0)} MB")

            except Exception:
                print_warning(
                    "Server status not accessible (may require admin privileges)"
                )

        except Exception as e:
            print_error(f"Failed to get database statistics: {e}")

    def review_authentication(self):
        """Review authentication and user permissions."""
        print_section("5. Authentication and User Permissions")

        try:
            # Check current user
            try:
                connection_status = self.db.command("connectionStatus")
                auth_info = connection_status.get("authInfo", {})

                authenticated_users = auth_info.get("authenticatedUsers", [])
                if authenticated_users:
                    for user in authenticated_users:
                        print_data("Authenticated User", user.get("user", "Unknown"))
                        print_data("Database", user.get("db", "Unknown"))
                else:
                    print_info("No authentication required or user info not available")

                authenticated_user_roles = auth_info.get("authenticatedUserRoles", [])
                if authenticated_user_roles:
                    print_data(
                        "User Roles",
                        ", ".join(
                            [
                                role.get("role", "Unknown")
                                for role in authenticated_user_roles
                            ]
                        ),
                    )

            except Exception:
                print_warning("Authentication details not accessible")

            # Test basic permissions
            try:
                # Try to read
                test_collection = self.db["test_permissions"]
                test_collection.find_one()
                print_success("Read permission: ✓")

                # Try to write
                test_doc = {"test": True, "timestamp": datetime.utcnow()}
                result = test_collection.insert_one(test_doc)
                print_success("Write permission: ✓")

                # Clean up
                test_collection.delete_one({"_id": result.inserted_id})
                print_success("Delete permission: ✓")

            except Exception as e:
                print_warning(f"Permission test failed: {e}")

        except Exception as e:
            print_error(f"Failed to review authentication: {e}")

    def review_initial_data(self):
        """Review initial seeded data."""
        print_section("6. Initial Data Review")

        try:
            # Check agent communication patterns
            if "agent_communication_registry" in self.db.list_collection_names():
                patterns = list(self.db["agent_communication_registry"].find())
                print_info(f"Agent Communication Patterns ({len(patterns)} found):")

                for pattern in patterns:
                    pattern_id = pattern.get("pattern_id", "Unknown")
                    name = pattern.get("name", "Unknown")
                    print(f"  ✓ {pattern_id}: {name}")

                if not patterns:
                    print_warning("No agent communication patterns found")
            else:
                print_warning("Agent communication registry collection not found")

            # Check system health records
            if "system_health" in self.db.list_collection_names():
                health_count = self.db["system_health"].count_documents({})
                print_data("System Health Records", health_count)

                if health_count > 0:
                    latest_health = self.db["system_health"].find_one(
                        sort=[("timestamp", -1)]
                    )
                    if latest_health:
                        print_data(
                            "Latest Health Check",
                            latest_health.get("timestamp", "Unknown"),
                        )

            # Check for any existing agents
            if "agents" in self.db.list_collection_names():
                agent_count = self.db["agents"].count_documents({})
                print_data("Registered Agents", agent_count)

                if agent_count > 0:
                    agents = list(self.db["agents"].find({}, {"name": 1, "status": 1}))
                    for agent in agents:
                        name = agent.get("name", "Unknown")
                        status = agent.get("status", "Unknown")
                        print(f"  ✓ {name} ({status})")

        except Exception as e:
            print_error(f"Failed to review initial data: {e}")

    def review_higherself_alignment(self):
        """Review alignment with HigherSelf Network requirements."""
        print_section("7. HigherSelf Network Alignment Check")

        requirements_check = {
            "Agent State Management": "agents" in self.db.list_collection_names(),
            "Workflow Execution": "workflows" in self.db.list_collection_names()
            and "workflow_instances" in self.db.list_collection_names(),
            "Task Management": "tasks" in self.db.list_collection_names(),
            "Agent Communication": "agent_communication"
            in self.db.list_collection_names(),
            "API Integration Management": "api_integrations"
            in self.db.list_collection_names(),
            "System Health Monitoring": "system_health"
            in self.db.list_collection_names(),
            "Business Entity Registry": "business_entities"
            in self.db.list_collection_names(),
            "Community Hub": "community_hub" in self.db.list_collection_names(),
            "Marketing Campaigns": "marketing_campaigns"
            in self.db.list_collection_names(),
        }

        print_info("HigherSelf Network Requirements Check:")

        all_requirements_met = True
        for requirement, status in requirements_check.items():
            if status:
                print_success(f"  {requirement}")
            else:
                print_error(f"  {requirement}")
                all_requirements_met = False

        if all_requirements_met:
            print_success("\n🎉 All HigherSelf Network requirements are met!")
        else:
            print_warning(
                "\n⚠️  Some requirements are missing. Consider running the setup script."
            )

    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()


def main():
    """Main review function."""
    print_header("MongoDB Configuration Review - HigherSelf Network")

    reviewer = MongoDBReviewer()

    try:
        # Connect to MongoDB
        if not reviewer.connect():
            print_error("Cannot proceed without MongoDB connection")
            print_info("Please ensure MongoDB is running and accessible")
            sys.exit(1)

        # Perform comprehensive review
        reviewer.review_connection_details()
        reviewer.review_collections()
        reviewer.review_indexes()
        reviewer.review_database_stats()
        reviewer.review_authentication()
        reviewer.review_initial_data()
        reviewer.review_higherself_alignment()

        print_header("Review Complete")
        print_success("MongoDB configuration review completed successfully!")
        print_info("Your MongoDB setup is ready for HigherSelf Network operations.")

    except KeyboardInterrupt:
        print_warning("\nReview interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error during review: {e}")
        sys.exit(1)
    finally:
        reviewer.close()


if __name__ == "__main__":
    main()
