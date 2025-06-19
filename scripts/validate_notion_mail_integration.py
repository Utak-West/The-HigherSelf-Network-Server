#!/usr/bin/env python3
"""
Notion Mail Integration Validation Script

Validates the complete setup and configuration of the Notion Mail Integration
following the implementation requirements and success criteria.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import requests
from loguru import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from services.notion_mail_integration import (
    EmailCategory,
    EmailContent,
    NotionMailIntegrationConfig,
    NotionMailIntegrationService,
)


class NotionMailIntegrationValidator:
    """Validator for Notion Mail Integration setup and configuration."""

    def __init__(self):
        """Initialize the validator."""
        self.validation_results = {
            "configuration": {},
            "classification_configs": {},
            "api_endpoints": {},
            "business_entity_boundaries": {},
            "performance_metrics": {},
            "overall_status": "unknown"
        }
        
        # Load configuration
        self.config = self._load_configuration()
        
        # Initialize service for testing
        if self.config:
            self.service = NotionMailIntegrationService(self.config)
        else:
            self.service = None

    def _load_configuration(self) -> NotionMailIntegrationConfig:
        """Load configuration from environment variables."""
        try:
            return NotionMailIntegrationConfig(
                notion_api_token=os.getenv("NOTION_API_TOKEN", ""),
                openai_api_key=os.getenv("OPENAI_API_KEY", ""),
                enable_auto_classification=os.getenv("ENABLE_EMAIL_AUTO_CLASSIFICATION", "true").lower() == "true",
                enable_workflow_automation=os.getenv("ENABLE_EMAIL_WORKFLOW_AUTOMATION", "true").lower() == "true",
                confidence_threshold=float(os.getenv("EMAIL_CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.7")),
                testing_mode=os.getenv("TESTING_MODE", "false").lower() == "true",
                am_consulting_response_time=int(os.getenv("AM_CONSULTING_RESPONSE_TIME", "4")),
                the_7_space_response_time=int(os.getenv("THE_7_SPACE_RESPONSE_TIME", "24")),
                higherself_core_response_time=int(os.getenv("HIGHERSELF_CORE_RESPONSE_TIME", "12"))
            )
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return None

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration setup."""
        logger.info("🔧 Validating configuration setup...")
        
        results = {
            "environment_variables": {},
            "service_initialization": False,
            "api_tokens": {},
            "response_time_slas": {},
            "feature_flags": {}
        }
        
        # Check environment variables
        required_env_vars = [
            "NOTION_API_TOKEN",
            "OPENAI_API_KEY",
            "ENABLE_EMAIL_AUTO_CLASSIFICATION",
            "ENABLE_EMAIL_WORKFLOW_AUTOMATION",
            "EMAIL_CLASSIFICATION_CONFIDENCE_THRESHOLD"
        ]
        
        for var in required_env_vars:
            value = os.getenv(var)
            results["environment_variables"][var] = {
                "present": value is not None,
                "value_set": bool(value and value.strip()),
                "value": "***" if "TOKEN" in var or "KEY" in var else value
            }
        
        # Check service initialization
        if self.service:
            results["service_initialization"] = True
            results["classification_configs_loaded"] = len(self.service.classification_configs)
        
        # Check API tokens (without exposing values)
        if self.config:
            results["api_tokens"]["notion"] = bool(self.config.notion_api_token)
            results["api_tokens"]["openai"] = bool(self.config.openai_api_key)
            
            # Check response time SLAs
            results["response_time_slas"] = {
                "am_consulting": self.config.am_consulting_response_time,
                "the_7_space": self.config.the_7_space_response_time,
                "higherself_core": self.config.higherself_core_response_time
            }
            
            # Check feature flags
            results["feature_flags"] = {
                "auto_classification": self.config.enable_auto_classification,
                "workflow_automation": self.config.enable_workflow_automation,
                "testing_mode": self.config.testing_mode
            }
        
        self.validation_results["configuration"] = results
        return results

    def validate_classification_configs(self) -> Dict[str, Any]:
        """Validate email classification configuration files."""
        logger.info("📋 Validating classification configuration files...")
        
        results = {
            "config_files": {},
            "category_completeness": {},
            "business_entity_mapping": {},
            "confidence_thresholds": {}
        }
        
        config_dir = Path("config/email_classification")
        
        # Check each category configuration file
        for category in EmailCategory:
            category_key = category.value.lower().replace(' ', '_').replace('|', '').replace('.', '')
            config_file = config_dir / f"{category_key}.json"
            
            file_result = {
                "exists": config_file.exists(),
                "readable": False,
                "valid_json": False,
                "required_fields": {},
                "configuration": {}
            }
            
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    
                    file_result["readable"] = True
                    file_result["valid_json"] = True
                    
                    # Check required fields
                    required_fields = [
                        "category", "priority", "color", "business_entity",
                        "confidence_threshold", "keywords", "domain_patterns"
                    ]
                    
                    for field in required_fields:
                        file_result["required_fields"][field] = field in config_data
                    
                    # Store key configuration details
                    file_result["configuration"] = {
                        "category": config_data.get("category"),
                        "priority": config_data.get("priority"),
                        "business_entity": config_data.get("business_entity"),
                        "confidence_threshold": config_data.get("confidence_threshold"),
                        "expected_daily_volume": config_data.get("expected_daily_volume"),
                        "target_accuracy": config_data.get("target_accuracy")
                    }
                    
                except Exception as e:
                    logger.error(f"Error reading {config_file}: {e}")
                    file_result["error"] = str(e)
            
            results["config_files"][category.value] = file_result
        
        # Validate business entity mapping
        if self.service:
            for category in EmailCategory:
                entity = self.service.category_config.get(category, {}).get("entity")
                results["business_entity_mapping"][category.value] = entity
        
        self.validation_results["classification_configs"] = results
        return results

    async def validate_email_classification(self) -> Dict[str, Any]:
        """Validate email classification functionality."""
        logger.info("🤖 Validating email classification functionality...")
        
        results = {
            "test_classifications": {},
            "accuracy_validation": {},
            "boundary_enforcement": {},
            "performance_metrics": {}
        }
        
        if not self.service:
            results["error"] = "Service not initialized"
            return results
        
        # Test sample emails for each category
        test_emails = {
            "AM Consulting": EmailContent(
                sender_email="ceo@businesscorp.com",
                sender_name="Business CEO",
                subject="Strategic Consulting Proposal Request",
                body="We need consulting services for our business transformation initiative. Please provide a proposal for strategic planning and implementation.",
                received_at=datetime.utcnow(),
                message_id="test_am_001"
            ),
            "The 7 Space Gallery": EmailContent(
                sender_email="artist@studio.com",
                sender_name="Local Artist",
                subject="Art Exhibition Proposal - Contemporary Collection",
                body="I would like to propose an art exhibition at The 7 Space gallery featuring my contemporary art collection and mixed media installations.",
                received_at=datetime.utcnow(),
                message_id="test_gallery_001"
            ),
            "The 7 Space Wellness": EmailContent(
                sender_email="client@wellness.com",
                sender_name="Wellness Client",
                subject="Wellness Session Booking - Meditation and Healing",
                body="I'm interested in booking wellness sessions including meditation, energy healing, and holistic therapy treatments at your wellness center.",
                received_at=datetime.utcnow(),
                message_id="test_wellness_001"
            ),
            "HigherSelf Network": EmailContent(
                sender_email="member@join.higherselflife.com",
                sender_name="Network Member",
                subject="HigherSelf Network Community Platform Access",
                body="I want to join the HigherSelf Network community platform for networking, personal development, and professional growth opportunities.",
                received_at=datetime.utcnow(),
                message_id="test_network_001"
            )
        }
        
        # Test classification for each sample
        for test_name, email in test_emails.items():
            try:
                start_time = datetime.utcnow()
                classification = await self.service.classify_email(email)
                end_time = datetime.utcnow()
                
                processing_time = (end_time - start_time).total_seconds() * 1000
                
                results["test_classifications"][test_name] = {
                    "success": True,
                    "category": classification.category.value,
                    "confidence": classification.confidence,
                    "business_entity": classification.business_entity,
                    "priority_score": classification.priority_score,
                    "processing_time_ms": processing_time,
                    "reasoning": classification.reasoning[:100] + "..." if len(classification.reasoning) > 100 else classification.reasoning
                }
                
            except Exception as e:
                logger.error(f"Classification failed for {test_name}: {e}")
                results["test_classifications"][test_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        self.validation_results["classification_performance"] = results
        return results

    def validate_api_endpoints(self) -> Dict[str, Any]:
        """Validate API endpoints are accessible."""
        logger.info("🌐 Validating API endpoints...")
        
        results = {
            "health_check": {},
            "classification_endpoint": {},
            "categories_endpoint": {},
            "stats_endpoint": {}
        }
        
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        
        # Test health check endpoint
        try:
            response = requests.get(f"{base_url}/notion-mail/health", timeout=10)
            results["health_check"] = {
                "accessible": True,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "healthy": response.status_code == 200
            }
            
            if response.status_code == 200:
                health_data = response.json()
                results["health_check"]["service_status"] = health_data.get("status")
                results["health_check"]["testing_mode"] = health_data.get("testing_mode")
                
        except Exception as e:
            results["health_check"] = {
                "accessible": False,
                "error": str(e)
            }
        
        # Test other endpoints
        endpoints = [
            ("categories", "/notion-mail/categories"),
            ("stats", "/notion-mail/stats")
        ]
        
        for endpoint_name, endpoint_path in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint_path}", timeout=10)
                results[f"{endpoint_name}_endpoint"] = {
                    "accessible": True,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            except Exception as e:
                results[f"{endpoint_name}_endpoint"] = {
                    "accessible": False,
                    "error": str(e)
                }
        
        self.validation_results["api_endpoints"] = results
        return results

    def validate_business_entity_boundaries(self) -> Dict[str, Any]:
        """Validate strict business entity boundary enforcement."""
        logger.info("🏢 Validating business entity boundaries...")
        
        results = {
            "boundary_rules": {},
            "entity_separation": {},
            "cross_contamination_check": {}
        }
        
        # Define expected business entity mappings
        expected_mappings = {
            EmailCategory.AM_CONSULTING: "am_consulting",
            EmailCategory.HIGHERSELF_NETWORK: "higherself_core",
            EmailCategory.THE_7_SPACE_GALLERY: "the_7_space",
            EmailCategory.THE_7_SPACE_WELLNESS: "the_7_space",
            EmailCategory.HIGHERSELF: "higherself_core",
            EmailCategory.TECHNICAL: None,
            EmailCategory.PERSONAL: None,
            EmailCategory.OTHER: None
        }
        
        if self.service:
            for category, expected_entity in expected_mappings.items():
                actual_entity = self.service.category_config.get(category, {}).get("entity")
                results["boundary_rules"][category.value] = {
                    "expected_entity": expected_entity,
                    "actual_entity": actual_entity,
                    "correct_mapping": actual_entity == expected_entity
                }
        
        # Check for proper separation
        business_entities = ["am_consulting", "the_7_space", "higherself_core"]
        for entity in business_entities:
            entity_categories = [
                cat.value for cat, config in self.service.category_config.items()
                if config.get("entity") == entity
            ]
            results["entity_separation"][entity] = {
                "categories": entity_categories,
                "category_count": len(entity_categories)
            }
        
        self.validation_results["business_entity_boundaries"] = results
        return results

    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        logger.info("📊 Generating validation report...")
        
        # Calculate overall status
        all_passed = True
        critical_failures = []
        
        # Check configuration
        config_results = self.validation_results.get("configuration", {})
        if not config_results.get("service_initialization"):
            all_passed = False
            critical_failures.append("Service initialization failed")
        
        # Check classification configs
        classification_results = self.validation_results.get("classification_configs", {})
        config_files = classification_results.get("config_files", {})
        for category, file_result in config_files.items():
            if not file_result.get("exists") or not file_result.get("valid_json"):
                all_passed = False
                critical_failures.append(f"Configuration file missing or invalid for {category}")
        
        # Check API endpoints
        api_results = self.validation_results.get("api_endpoints", {})
        health_check = api_results.get("health_check", {})
        if not health_check.get("accessible") or not health_check.get("healthy"):
            all_passed = False
            critical_failures.append("Health check endpoint failed")
        
        # Set overall status
        if all_passed:
            self.validation_results["overall_status"] = "✅ PASSED"
        else:
            self.validation_results["overall_status"] = "❌ FAILED"
        
        self.validation_results["critical_failures"] = critical_failures
        self.validation_results["validation_timestamp"] = datetime.utcnow().isoformat()
        
        return self.validation_results

    def print_validation_summary(self):
        """Print validation summary to console."""
        print("\n" + "="*80)
        print("🔍 NOTION MAIL INTEGRATION VALIDATION REPORT")
        print("="*80)
        
        print(f"\n📅 Validation Time: {self.validation_results.get('validation_timestamp', 'Unknown')}")
        print(f"🎯 Overall Status: {self.validation_results.get('overall_status', 'Unknown')}")
        
        # Configuration Summary
        config = self.validation_results.get("configuration", {})
        print(f"\n🔧 Configuration:")
        print(f"   Service Initialized: {'✅' if config.get('service_initialization') else '❌'}")
        print(f"   Classification Configs: {config.get('classification_configs_loaded', 0)}/8")
        
        # API Endpoints Summary
        api = self.validation_results.get("api_endpoints", {})
        health = api.get("health_check", {})
        print(f"\n🌐 API Endpoints:")
        print(f"   Health Check: {'✅' if health.get('healthy') else '❌'}")
        print(f"   Response Time: {health.get('response_time_ms', 0):.1f}ms")
        
        # Business Entity Boundaries
        boundaries = self.validation_results.get("business_entity_boundaries", {})
        boundary_rules = boundaries.get("boundary_rules", {})
        correct_mappings = sum(1 for rule in boundary_rules.values() if rule.get("correct_mapping"))
        print(f"\n🏢 Business Entity Boundaries:")
        print(f"   Correct Mappings: {correct_mappings}/{len(boundary_rules)}")
        
        # Critical Failures
        failures = self.validation_results.get("critical_failures", [])
        if failures:
            print(f"\n❌ Critical Failures:")
            for failure in failures:
                print(f"   • {failure}")
        
        print("\n" + "="*80)


async def main():
    """Main validation function."""
    logger.info("🚀 Starting Notion Mail Integration validation...")
    
    validator = NotionMailIntegrationValidator()
    
    # Run all validations
    await asyncio.gather(
        asyncio.create_task(asyncio.to_thread(validator.validate_configuration)),
        asyncio.create_task(asyncio.to_thread(validator.validate_classification_configs)),
        asyncio.create_task(validator.validate_email_classification()),
        asyncio.create_task(asyncio.to_thread(validator.validate_api_endpoints)),
        asyncio.create_task(asyncio.to_thread(validator.validate_business_entity_boundaries))
    )
    
    # Generate and display report
    validator.generate_validation_report()
    validator.print_validation_summary()
    
    # Save detailed report
    report_file = f"validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(validator.validation_results, f, indent=2, default=str)
    
    logger.info(f"📄 Detailed report saved to: {report_file}")
    
    # Exit with appropriate code
    if validator.validation_results["overall_status"] == "✅ PASSED":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
