#!/usr/bin/env python3
"""
Contact Workflow Automation Validation Script

This script validates the deployment of the contact workflow automation system
without requiring full service initialization. It checks file structure,
configurations, and basic functionality.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

from loguru import logger
from notion_client import Client

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class WorkflowDeploymentValidator:
    """
    Validates the contact workflow automation deployment.
    
    Performs comprehensive validation of all components without
    requiring full service initialization.
    """

    def __init__(self):
        """Initialize the validator."""
        self.notion = Client(auth=os.getenv('NOTION_API_KEY'))
        self.contacts_db_id = os.getenv('NOTION_CONTACTS_PROFILES_DB')
        self.workflows_db_id = os.getenv('NOTION_ACTIVE_WORKFLOW_INSTANCES_DB')
        self.tasks_db_id = os.getenv('NOTION_TASKS_DB')
        
        logger.info("Workflow Deployment Validator initialized")

    async def validate_deployment(self) -> Dict[str, Any]:
        """
        Validate the complete workflow automation deployment.
        
        Returns:
            Dict containing validation results
        """
        logger.info("🔍 VALIDATING CONTACT WORKFLOW AUTOMATION DEPLOYMENT")
        logger.info("=" * 70)
        
        validation_results = {
            "start_time": datetime.now().isoformat(),
            "validations": {},
            "status": "in_progress"
        }
        
        try:
            # Step 1: Validate Environment
            logger.info("📋 Step 1: Validating Environment Configuration")
            env_validation = await self._validate_environment()
            validation_results["validations"]["environment"] = env_validation
            
            # Step 2: Validate File Structure
            logger.info("📁 Step 2: Validating File Structure")
            file_validation = self._validate_file_structure()
            validation_results["validations"]["files"] = file_validation
            
            # Step 3: Validate Notion Databases
            logger.info("🗄️ Step 3: Validating Notion Database Connections")
            db_validation = await self._validate_notion_databases()
            validation_results["validations"]["databases"] = db_validation
            
            # Step 4: Validate Configuration Files
            logger.info("⚙️ Step 4: Validating Configuration Files")
            config_validation = self._validate_configurations()
            validation_results["validations"]["configurations"] = config_validation
            
            # Step 5: Validate API Integration
            logger.info("🌐 Step 5: Validating API Integration")
            api_validation = self._validate_api_integration()
            validation_results["validations"]["api"] = api_validation
            
            # Determine overall status
            all_valid = all(
                v.get("valid", False) for v in validation_results["validations"].values()
            )
            
            validation_results["end_time"] = datetime.now().isoformat()
            validation_results["status"] = "passed" if all_valid else "failed"
            
            if all_valid:
                logger.info("✅ Contact Workflow Automation Deployment Validation PASSED!")
            else:
                logger.warning("⚠️ Contact Workflow Automation Deployment Validation has issues")
            
            self._print_validation_summary(validation_results)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            validation_results["status"] = "error"
            validation_results["error"] = str(e)
            validation_results["end_time"] = datetime.now().isoformat()
            return validation_results

    async def _validate_environment(self) -> Dict[str, Any]:
        """Validate environment configuration."""
        validation_result = {"valid": True, "issues": [], "checks": {}}
        
        # Check required environment variables
        required_vars = [
            'NOTION_API_KEY',
            'NOTION_CONTACTS_PROFILES_DB',
            'NOTION_ACTIVE_WORKFLOW_INSTANCES_DB',
            'NOTION_TASKS_DB'
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Missing environment variable: {var}")
                validation_result["checks"][var] = "missing"
                logger.error(f"   ❌ Missing: {var}")
            else:
                validation_result["checks"][var] = "present"
                logger.info(f"   ✅ Present: {var}")
        
        # Test Notion API connection
        try:
            await self.notion.users.me()
            validation_result["checks"]["notion_api_connection"] = "success"
            logger.info("   ✅ Notion API connection successful")
        except Exception as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Notion API connection failed: {e}")
            validation_result["checks"]["notion_api_connection"] = "failed"
            logger.error(f"   ❌ Notion API connection failed: {e}")
        
        return validation_result

    def _validate_file_structure(self) -> Dict[str, Any]:
        """Validate required files are present."""
        validation_result = {"valid": True, "issues": [], "files": {}}
        
        required_files = [
            "services/contact_workflow_automation.py",
            "services/workflow_orchestrator.py",
            "config/business_entity_workflows.py",
            "templates/contact_engagement_templates.py",
            "api/contact_workflow_webhooks.py",
            "docs/CONTACT_WORKFLOW_AUTOMATION_GUIDE.md"
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                validation_result["files"][file_path] = "present"
                logger.info(f"   ✅ {file_path}")
            else:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Missing file: {file_path}")
                validation_result["files"][file_path] = "missing"
                logger.error(f"   ❌ Missing: {file_path}")
        
        return validation_result

    async def _validate_notion_databases(self) -> Dict[str, Any]:
        """Validate Notion database connections."""
        validation_result = {"valid": True, "issues": [], "databases": {}}
        
        databases = {
            "contacts": self.contacts_db_id,
            "workflows": self.workflows_db_id,
            "tasks": self.tasks_db_id
        }
        
        for db_name, db_id in databases.items():
            if not db_id:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Missing database ID for {db_name}")
                validation_result["databases"][db_name] = {"status": "missing_id"}
                logger.error(f"   ❌ {db_name}: Missing database ID")
                continue
                
            try:
                response = await self.notion.databases.retrieve(database_id=db_id)
                validation_result["databases"][db_name] = {
                    "status": "accessible",
                    "title": response.get("title", [{}])[0].get("text", {}).get("content", "Unknown"),
                    "id": db_id
                }
                logger.info(f"   ✅ {db_name}: Accessible")
            except Exception as e:
                validation_result["valid"] = False
                validation_result["issues"].append(f"{db_name} database error: {e}")
                validation_result["databases"][db_name] = {
                    "status": "error",
                    "error": str(e),
                    "id": db_id
                }
                logger.error(f"   ❌ {db_name}: {e}")
        
        return validation_result

    def _validate_configurations(self) -> Dict[str, Any]:
        """Validate configuration files can be imported."""
        validation_result = {"valid": True, "issues": [], "configs": {}}
        
        # Test business entity workflows
        try:
            # Import without triggering service initialization
            import importlib.util
            
            # Load business entity workflows
            spec = importlib.util.spec_from_file_location(
                "business_entity_workflows", 
                "config/business_entity_workflows.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Test instantiation
            workflows = module.BusinessEntityWorkflows()
            entity_configs = workflows.entity_configs
            workflow_templates = workflows.workflow_templates
            
            validation_result["configs"]["business_entity_workflows"] = {
                "status": "valid",
                "entity_count": len(entity_configs),
                "template_count": len(workflow_templates)
            }
            logger.info(f"   ✅ Business Entity Workflows: {len(entity_configs)} entities, {len(workflow_templates)} templates")
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Business entity workflows error: {e}")
            validation_result["configs"]["business_entity_workflows"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"   ❌ Business Entity Workflows: {e}")
        
        # Test engagement templates
        try:
            spec = importlib.util.spec_from_file_location(
                "contact_engagement_templates", 
                "templates/contact_engagement_templates.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Test instantiation
            templates = module.ContactEngagementTemplates()
            template_count = len(templates.templates)
            
            validation_result["configs"]["contact_engagement_templates"] = {
                "status": "valid",
                "template_count": template_count
            }
            logger.info(f"   ✅ Contact Engagement Templates: {template_count} templates")
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Contact engagement templates error: {e}")
            validation_result["configs"]["contact_engagement_templates"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"   ❌ Contact Engagement Templates: {e}")
        
        return validation_result

    def _validate_api_integration(self) -> Dict[str, Any]:
        """Validate API integration is properly configured."""
        validation_result = {"valid": True, "issues": [], "integration": {}}
        
        # Check if API router is added to server.py
        try:
            with open("api/server.py", "r") as f:
                server_content = f.read()
            
            if "contact_workflow_router" in server_content:
                validation_result["integration"]["router_imported"] = "yes"
                logger.info("   ✅ Contact workflow router imported")
            else:
                validation_result["valid"] = False
                validation_result["issues"].append("Contact workflow router not imported in server.py")
                validation_result["integration"]["router_imported"] = "no"
                logger.error("   ❌ Contact workflow router not imported")
            
            if "app.include_router(contact_workflow_router)" in server_content:
                validation_result["integration"]["router_registered"] = "yes"
                logger.info("   ✅ Contact workflow router registered")
            else:
                validation_result["valid"] = False
                validation_result["issues"].append("Contact workflow router not registered in server.py")
                validation_result["integration"]["router_registered"] = "no"
                logger.error("   ❌ Contact workflow router not registered")
                
        except Exception as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Server.py validation error: {e}")
            validation_result["integration"]["server_check"] = f"error: {e}"
            logger.error(f"   ❌ Server.py validation error: {e}")
        
        return validation_result

    def _print_validation_summary(self, results: Dict[str, Any]):
        """Print a comprehensive validation summary."""
        logger.info("\n" + "=" * 70)
        logger.info("📋 CONTACT WORKFLOW AUTOMATION VALIDATION SUMMARY")
        logger.info("=" * 70)
        
        # Environment
        env = results.get("validations", {}).get("environment", {})
        env_status = "✅ PASSED" if env.get("valid") else "❌ FAILED"
        logger.info(f"🌍 Environment: {env_status}")
        if env.get("issues"):
            for issue in env["issues"]:
                logger.info(f"   • {issue}")
        
        # Files
        files = results.get("validations", {}).get("files", {})
        files_status = "✅ PASSED" if files.get("valid") else "❌ FAILED"
        logger.info(f"📁 File Structure: {files_status}")
        
        # Databases
        db = results.get("validations", {}).get("databases", {})
        db_status = "✅ PASSED" if db.get("valid") else "❌ FAILED"
        logger.info(f"🗄️ Notion Databases: {db_status}")
        
        # Configurations
        config = results.get("validations", {}).get("configurations", {})
        config_status = "✅ PASSED" if config.get("valid") else "❌ FAILED"
        logger.info(f"⚙️ Configurations: {config_status}")
        
        # API Integration
        api = results.get("validations", {}).get("api", {})
        api_status = "✅ PASSED" if api.get("valid") else "❌ FAILED"
        logger.info(f"🌐 API Integration: {api_status}")
        
        # Overall Status
        overall_status = results.get("status", "unknown")
        if overall_status == "passed":
            logger.info("\n🎉 DEPLOYMENT VALIDATION: ✅ PASSED")
            logger.info("\n🚀 NEXT STEPS:")
            logger.info("   1. Start the HigherSelf Network Server: python3 main.py")
            logger.info("   2. Test API endpoints: curl http://localhost:8000/contact-workflows/status")
            logger.info("   3. Enable contact monitoring: POST /contact-workflows/start-monitoring")
            logger.info("   4. Test workflow execution: POST /contact-workflows/trigger")
        else:
            logger.info("\n⚠️ DEPLOYMENT VALIDATION: ❌ FAILED")
            logger.info("\n🔧 REQUIRED ACTIONS:")
            logger.info("   1. Fix the issues listed above")
            logger.info("   2. Re-run validation: python3 tools/validate_workflow_deployment.py")
            logger.info("   3. Proceed with deployment once all validations pass")
        
        logger.info("=" * 70)


async def main():
    """Main validation function."""
    validator = WorkflowDeploymentValidator()
    results = await validator.validate_deployment()
    
    if results["status"] == "passed":
        logger.info("🎉 Validation completed successfully!")
        return 0
    else:
        logger.error("❌ Validation failed!")
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
