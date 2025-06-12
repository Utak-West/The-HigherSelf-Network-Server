#!/usr/bin/env python3
"""
MongoDB Management Script for HigherSelf Network

This script provides common MongoDB management operations including:
- Database backup and restore
- Collection management
- Index optimization
- Data cleanup
- Performance monitoring
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pymongo
from dotenv import load_dotenv
from loguru import logger
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure


# Color codes for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


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


class MongoDBManager:
    """MongoDB management operations for HigherSelf Network."""

    def __init__(self):
        """Initialize the MongoDB manager."""
        load_dotenv()

        self.mongo_uri = os.environ.get("MONGODB_URI")
        self.db_name = os.environ.get("MONGODB_DB_NAME", "higherselfnetwork")
        self.client = None
        self.db = None

        if not self.mongo_uri:
            raise ValueError("MONGODB_URI not found in environment variables")

    def connect(self) -> bool:
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            print_success(f"Connected to MongoDB: {self.db_name}")
            return True
        except Exception as e:
            print_error(f"Failed to connect to MongoDB: {e}")
            return False

    def backup_database(self, backup_path: str = None) -> bool:
        """Create a backup of the database."""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"./backups/mongodb_backup_{timestamp}.json"

        os.makedirs(os.path.dirname(backup_path), exist_ok=True)

        try:
            backup_data = {}
            collections = self.db.list_collection_names()

            print_info(f"Backing up {len(collections)} collections...")

            for collection_name in collections:
                collection = self.db[collection_name]
                documents = list(collection.find())

                # Convert ObjectId to string for JSON serialization
                for doc in documents:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])

                backup_data[collection_name] = documents
                print_info(
                    f"Backed up collection '{collection_name}': {len(documents)} documents"
                )

            with open(backup_path, "w") as f:
                json.dump(backup_data, f, indent=2, default=str)

            print_success(f"Database backup completed: {backup_path}")
            return True

        except Exception as e:
            print_error(f"Backup failed: {e}")
            return False

    def restore_database(self, backup_path: str, overwrite: bool = False) -> bool:
        """Restore database from backup."""
        if not os.path.exists(backup_path):
            print_error(f"Backup file not found: {backup_path}")
            return False

        try:
            with open(backup_path, "r") as f:
                backup_data = json.load(f)

            print_info(f"Restoring {len(backup_data)} collections...")

            for collection_name, documents in backup_data.items():
                collection = self.db[collection_name]

                if overwrite:
                    collection.drop()
                    print_info(f"Dropped existing collection '{collection_name}'")

                if documents:
                    collection.insert_many(documents)
                    print_info(
                        f"Restored collection '{collection_name}': {len(documents)} documents"
                    )

            print_success(f"Database restore completed from: {backup_path}")
            return True

        except Exception as e:
            print_error(f"Restore failed: {e}")
            return False

    def cleanup_old_data(self, days: int = 30) -> bool:
        """Clean up old data from system collections."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        try:
            # Clean up old system health records
            health_collection = self.db["system_health"]
            result = health_collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            print_info(f"Cleaned up {result.deleted_count} old system health records")

            # Clean up old agent communication logs
            comm_collection = self.db["agent_communication"]
            result = comm_collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            print_info(f"Cleaned up {result.deleted_count} old communication records")

            print_success(f"Data cleanup completed (older than {days} days)")
            return True

        except Exception as e:
            print_error(f"Data cleanup failed: {e}")
            return False

    def optimize_indexes(self) -> bool:
        """Optimize database indexes."""
        try:
            collections = self.db.list_collection_names()

            for collection_name in collections:
                collection = self.db[collection_name]

                # Reindex collection
                self.db.command("reIndex", collection_name)
                print_info(f"Reindexed collection '{collection_name}'")

            print_success("Index optimization completed")
            return True

        except Exception as e:
            print_error(f"Index optimization failed: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections."""
        try:
            stats = {}
            collections = self.db.list_collection_names()

            for collection_name in collections:
                collection = self.db[collection_name]
                collection_stats = self.db.command("collStats", collection_name)

                stats[collection_name] = {
                    "count": collection_stats.get("count", 0),
                    "size": collection_stats.get("size", 0),
                    "avgObjSize": collection_stats.get("avgObjSize", 0),
                    "storageSize": collection_stats.get("storageSize", 0),
                    "indexes": collection_stats.get("nindexes", 0),
                    "indexSize": collection_stats.get("totalIndexSize", 0),
                }

            return stats

        except Exception as e:
            print_error(f"Failed to get collection stats: {e}")
            return {}

    def print_collection_stats(self):
        """Print formatted collection statistics."""
        stats = self.get_collection_stats()

        if not stats:
            return

        print_info("Collection Statistics:")
        print(f"{'Collection':<25} {'Documents':<12} {'Size (MB)':<12} {'Indexes':<8}")
        print("-" * 65)

        for collection_name, collection_stats in stats.items():
            size_mb = collection_stats["size"] / 1024 / 1024
            print(
                f"{collection_name:<25} {collection_stats['count']:<12} {size_mb:<12.2f} {collection_stats['indexes']:<8}"
            )

    def monitor_performance(self) -> Dict[str, Any]:
        """Monitor database performance metrics."""
        try:
            # Get server status
            server_status = self.db.command("serverStatus")

            # Get database stats
            db_stats = self.db.command("dbStats")

            # Get current operations
            current_ops = self.db.command("currentOp")

            performance_data = {
                "connections": server_status.get("connections", {}),
                "opcounters": server_status.get("opcounters", {}),
                "memory": server_status.get("mem", {}),
                "database_size": db_stats.get("dataSize", 0),
                "active_operations": len(current_ops.get("inprog", [])),
            }

            return performance_data

        except Exception as e:
            print_error(f"Performance monitoring failed: {e}")
            return {}

    def print_performance_stats(self):
        """Print formatted performance statistics."""
        perf_data = self.monitor_performance()

        if not perf_data:
            return

        print_info("Performance Statistics:")

        # Connections
        connections = perf_data.get("connections", {})
        print(
            f"Connections - Current: {connections.get('current', 0)}, Available: {connections.get('available', 0)}"
        )

        # Operations
        opcounters = perf_data.get("opcounters", {})
        print(
            f"Operations - Insert: {opcounters.get('insert', 0)}, Query: {opcounters.get('query', 0)}, Update: {opcounters.get('update', 0)}"
        )

        # Memory
        memory = perf_data.get("memory", {})
        print(
            f"Memory - Resident: {memory.get('resident', 0)} MB, Virtual: {memory.get('virtual', 0)} MB"
        )

        # Database size
        db_size_mb = perf_data.get("database_size", 0) / 1024 / 1024
        print(f"Database Size: {db_size_mb:.2f} MB")

        # Active operations
        print(f"Active Operations: {perf_data.get('active_operations', 0)}")

    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="MongoDB Management for HigherSelf Network"
    )
    parser.add_argument(
        "command",
        choices=["backup", "restore", "cleanup", "optimize", "stats", "performance"],
        help="Management command to execute",
    )

    parser.add_argument("--backup-path", help="Path for backup file")
    parser.add_argument(
        "--days", type=int, default=30, help="Days for cleanup (default: 30)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing data during restore",
    )

    args = parser.parse_args()

    manager = MongoDBManager()

    try:
        if not manager.connect():
            sys.exit(1)

        if args.command == "backup":
            success = manager.backup_database(args.backup_path)
        elif args.command == "restore":
            if not args.backup_path:
                print_error("--backup-path required for restore command")
                sys.exit(1)
            success = manager.restore_database(args.backup_path, args.overwrite)
        elif args.command == "cleanup":
            success = manager.cleanup_old_data(args.days)
        elif args.command == "optimize":
            success = manager.optimize_indexes()
        elif args.command == "stats":
            manager.print_collection_stats()
            success = True
        elif args.command == "performance":
            manager.print_performance_stats()
            success = True
        else:
            print_error(f"Unknown command: {args.command}")
            success = False

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print_warning("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        manager.close()


if __name__ == "__main__":
    main()
