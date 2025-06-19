#!/usr/bin/env python3
"""
The 7 Space Demo Environment Validation Script

This script validates that the demo environment is properly configured and running,
including all services, database connections, and workflow automation capabilities.
"""

import os
import sys
import time
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import pymongo
import redis


class DemoValidator:
    """Validates The 7 Space demo environment"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.grafana_url = "http://localhost:3001"
        self.prometheus_url = "http://localhost:9091"
        self.consul_url = "http://localhost:8501"
        self.mongodb_uri = "mongodb://demo_user:demo_password@localhost:27018/higherself_demo"
        self.redis_host = "localhost"
        self.redis_port = 6380
        self.redis_password = "demo_redis_password"
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": "demo",
            "business_entity": "the_7_space",
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
    
    def log_test(self, test_name: str, status: str, message: str, details: Optional[Dict] = None):
        """Log test result"""
        test_result = {
            "test_name": test_name,
            "status": status,  # PASS, FAIL, WARN
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.results["tests"].append(test_result)
        self.results["summary"]["total_tests"] += 1
        
        if status == "PASS":
            self.results["summary"]["passed"] += 1
            print(f"✅ {test_name}: {message}")
        elif status == "FAIL":
            self.results["summary"]["failed"] += 1
            print(f"❌ {test_name}: {message}")
        elif status == "WARN":
            self.results["summary"]["warnings"] += 1
            print(f"⚠️  {test_name}: {message}")
    
    def test_service_health(self):
        """Test main application health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log_test(
                    "Service Health Check",
                    "PASS",
                    "Main application is healthy",
                    health_data
                )
                return True
            else:
                self.log_test(
                    "Service Health Check",
                    "FAIL",
                    f"Health check failed with status {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Service Health Check",
                "FAIL",
                f"Health check failed: {str(e)}"
            )
            return False
    
    def test_mongodb_connection(self):
        """Test MongoDB connection and demo database"""
        try:
            client = pymongo.MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            client.admin.command('ping')
            
            # Check demo database
            db = client.higherself_demo
            collections = db.list_collection_names()
            
            expected_collections = [
                'contacts', 'workflows', 'tasks', 'notifications', 
                'business_entities', 'workflow_instances'
            ]
            
            missing_collections = [col for col in expected_collections if col not in collections]
            
            if not missing_collections:
                # Check business entity
                business_entity = db.business_entities.find_one({"_id": "the_7_space"})
                if business_entity:
                    self.log_test(
                        "MongoDB Connection",
                        "PASS",
                        "MongoDB connected and demo database configured",
                        {"collections": collections, "business_entity": "configured"}
                    )
                    return True
                else:
                    self.log_test(
                        "MongoDB Connection",
                        "WARN",
                        "MongoDB connected but business entity not configured",
                        {"collections": collections}
                    )
                    return False
            else:
                self.log_test(
                    "MongoDB Connection",
                    "WARN",
                    f"MongoDB connected but missing collections: {missing_collections}",
                    {"collections": collections, "missing": missing_collections}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "MongoDB Connection",
                "FAIL",
                f"MongoDB connection failed: {str(e)}"
            )
            return False
    
    def test_redis_connection(self):
        """Test Redis connection"""
        try:
            r = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                decode_responses=True,
                socket_timeout=5
            )
            
            # Test connection
            r.ping()
            
            # Test basic operations
            r.set("demo_test", "validation", ex=60)
            value = r.get("demo_test")
            
            if value == "validation":
                info = r.info()
                self.log_test(
                    "Redis Connection",
                    "PASS",
                    "Redis connected and operational",
                    {"version": info.get("redis_version"), "memory": info.get("used_memory_human")}
                )
                return True
            else:
                self.log_test(
                    "Redis Connection",
                    "FAIL",
                    "Redis connected but operations failed"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Redis Connection",
                "FAIL",
                f"Redis connection failed: {str(e)}"
            )
            return False
    
    def test_monitoring_services(self):
        """Test monitoring services (Grafana, Prometheus, Consul)"""
        services = [
            ("Grafana", self.grafana_url, "/api/health"),
            ("Prometheus", self.prometheus_url, "/-/ready"),
            ("Consul", self.consul_url, "/v1/status/leader")
        ]
        
        all_healthy = True
        
        for service_name, base_url, endpoint in services:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.log_test(
                        f"{service_name} Health",
                        "PASS",
                        f"{service_name} is healthy and accessible"
                    )
                else:
                    self.log_test(
                        f"{service_name} Health",
                        "WARN",
                        f"{service_name} returned status {response.status_code}"
                    )
                    all_healthy = False
            except Exception as e:
                self.log_test(
                    f"{service_name} Health",
                    "WARN",
                    f"{service_name} not accessible: {str(e)}"
                )
                all_healthy = False
        
        return all_healthy
    
    def test_notion_integration(self):
        """Test Notion API integration"""
        try:
            response = requests.get(f"{self.base_url}/api/notion/status", timeout=10)
            if response.status_code == 200:
                notion_status = response.json()
                if notion_status.get("connected"):
                    self.log_test(
                        "Notion Integration",
                        "PASS",
                        "Notion API connected and configured",
                        notion_status
                    )
                    return True
                else:
                    self.log_test(
                        "Notion Integration",
                        "FAIL",
                        "Notion API not connected",
                        notion_status
                    )
                    return False
            else:
                self.log_test(
                    "Notion Integration",
                    "FAIL",
                    f"Notion status check failed with status {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Notion Integration",
                "WARN",
                f"Notion integration test failed: {str(e)}"
            )
            return False
    
    def test_workflow_automation(self):
        """Test workflow automation capabilities"""
        try:
            response = requests.get(f"{self.base_url}/api/workflows/status", timeout=10)
            if response.status_code == 200:
                workflow_status = response.json()
                if workflow_status.get("automation_enabled"):
                    self.log_test(
                        "Workflow Automation",
                        "PASS",
                        "Workflow automation is enabled and configured",
                        workflow_status
                    )
                    return True
                else:
                    self.log_test(
                        "Workflow Automation",
                        "WARN",
                        "Workflow automation is disabled",
                        workflow_status
                    )
                    return False
            else:
                self.log_test(
                    "Workflow Automation",
                    "WARN",
                    f"Workflow status check failed with status {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Workflow Automation",
                "WARN",
                f"Workflow automation test failed: {str(e)}"
            )
            return False
    
    def test_business_entity_config(self):
        """Test business entity configuration"""
        try:
            response = requests.get(f"{self.base_url}/api/business-entities/the_7_space", timeout=10)
            if response.status_code == 200:
                entity_config = response.json()
                if entity_config.get("entity_id") == "the_7_space":
                    self.log_test(
                        "Business Entity Config",
                        "PASS",
                        "The 7 Space business entity properly configured",
                        entity_config
                    )
                    return True
                else:
                    self.log_test(
                        "Business Entity Config",
                        "FAIL",
                        "Business entity configuration mismatch"
                    )
                    return False
            else:
                self.log_test(
                    "Business Entity Config",
                    "WARN",
                    f"Business entity check failed with status {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Business Entity Config",
                "WARN",
                f"Business entity test failed: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Starting The 7 Space Demo Environment Validation")
        print("=" * 60)
        
        # Core service tests
        self.test_service_health()
        self.test_mongodb_connection()
        self.test_redis_connection()
        
        # Monitoring tests
        self.test_monitoring_services()
        
        # Integration tests
        self.test_notion_integration()
        self.test_workflow_automation()
        self.test_business_entity_config()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        summary = self.results["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        
        success_rate = (summary['passed'] / summary['total_tests']) * 100 if summary['total_tests'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if summary['failed'] == 0:
            print("\n🎉 Demo environment validation PASSED!")
            print("The 7 Space demo is ready for use.")
            return True
        else:
            print(f"\n⚠️  Demo environment validation completed with {summary['failed']} failures.")
            print("Please review failed tests and fix issues before proceeding.")
            return False
    
    def save_results(self, filename: str = "demo_validation_results.json"):
        """Save validation results to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Validation results saved to {filename}")


def main():
    """Main validation function"""
    validator = DemoValidator()
    
    try:
        success = validator.run_all_tests()
        validator.save_results()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Validation failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
