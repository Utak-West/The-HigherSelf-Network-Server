#!/usr/bin/env python3
"""
Project 2: Multi-Entity Intelligent Workflow Expansion Test Suite

Comprehensive test suite for the multi-entity workflow expansion system
that scales automation across The 7 Space, AM Consulting, and HigherSelf Core.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List

import aiohttp
import pytest
from loguru import logger


class MultiEntityWorkflowTester:
    """Test suite for multi-entity workflow expansion."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
        # Test data for each entity
        self.test_contacts = {
            "the_7_space": [
                {
                    "email": "artist@the7space.com",
                    "first_name": "Gallery",
                    "last_name": "Artist",
                    "message": "I'm interested in exhibiting my artwork at your gallery",
                    "interests": ["art", "gallery", "exhibition"],
                    "source": "gallery_website"
                },
                {
                    "email": "wellness@the7space.com",
                    "first_name": "Wellness",
                    "last_name": "Seeker",
                    "message": "I'd like to book a meditation session",
                    "interests": ["wellness", "meditation", "healing"],
                    "source": "wellness_website"
                }
            ],
            "am_consulting": [
                {
                    "email": "ceo@startup.com",
                    "first_name": "Business",
                    "last_name": "Owner",
                    "message": "We need strategic consulting for our growing startup",
                    "interests": ["business", "consulting", "strategy"],
                    "source": "referral"
                },
                {
                    "email": "manager@company.com",
                    "first_name": "Project",
                    "last_name": "Manager",
                    "message": "Looking for help with our digital transformation",
                    "interests": ["business", "transformation", "technology"],
                    "source": "linkedin"
                }
            ],
            "higherself_core": [
                {
                    "email": "member@higherself.com",
                    "first_name": "Growth",
                    "last_name": "Seeker",
                    "message": "I want to join the HigherSelf community for personal development",
                    "interests": ["personal_growth", "community", "development"],
                    "source": "community_platform"
                },
                {
                    "email": "leader@higherself.com",
                    "first_name": "Thought",
                    "last_name": "Leader",
                    "message": "Interested in sharing content and connecting with like-minded individuals",
                    "interests": ["content", "networking", "leadership"],
                    "source": "content_platform"
                }
            ]
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_multi_entity_health(self) -> bool:
        """Test multi-entity workflow system health."""
        try:
            async with self.session.get(f"{self.base_url}/api/multi-entity-workflows/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"Multi-entity system health: {health_data}")
                    return health_data.get("status") == "healthy"
                return False
        except Exception as e:
            logger.error(f"Multi-entity health check failed: {e}")
            return False
    
    async def test_supported_entities(self) -> Dict[str, Any]:
        """Test getting supported business entities."""
        try:
            async with self.session.get(f"{self.base_url}/api/multi-entity-workflows/entities") as response:
                if response.status == 200:
                    entities_data = await response.json()
                    logger.info(f"Supported entities: {entities_data}")
                    return entities_data
                else:
                    logger.error(f"Failed to get entities: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting supported entities: {e}")
            return {}
    
    async def test_workflow_templates(self) -> Dict[str, Any]:
        """Test getting workflow templates for all entities."""
        try:
            async with self.session.get(f"{self.base_url}/api/multi-entity-workflows/templates") as response:
                if response.status == 200:
                    templates_data = await response.json()
                    logger.info(f"Workflow templates: {templates_data}")
                    return templates_data
                else:
                    logger.error(f"Failed to get templates: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting workflow templates: {e}")
            return {}
    
    async def test_entity_specific_workflows(self) -> Dict[str, List[Dict[str, Any]]]:
        """Test entity-specific workflow execution."""
        results = {}
        
        for entity_name, contacts in self.test_contacts.items():
            entity_results = []
            
            for contact in contacts:
                try:
                    # Get optimal workflow for this contact
                    optimal_workflow = await self._get_optimal_workflow(entity_name, contact)
                    
                    # Execute the workflow
                    workflow_result = await self._execute_workflow(
                        entity_name, optimal_workflow, contact
                    )
                    
                    entity_results.append({
                        "contact": contact["email"],
                        "optimal_workflow": optimal_workflow,
                        "execution_result": workflow_result,
                        "success": workflow_result.get("success", False)
                    })
                    
                    logger.info(f"Executed {entity_name} workflow for {contact['email']}")
                    
                    # Small delay between executions
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error testing {entity_name} workflow for {contact['email']}: {e}")
                    entity_results.append({
                        "contact": contact["email"],
                        "error": str(e),
                        "success": False
                    })
            
            results[entity_name] = entity_results
        
        return results
    
    async def _get_optimal_workflow(self, entity_name: str, contact_data: Dict[str, Any]) -> str:
        """Get optimal workflow for a contact."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/multi-entity-workflows/optimize-workflow",
                json={
                    "contact_data": contact_data,
                    "entity_name": entity_name
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("recommended_workflow", "default")
                else:
                    logger.warning(f"Failed to get optimal workflow, using default")
                    return "default"
        except Exception as e:
            logger.error(f"Error getting optimal workflow: {e}")
            return "default"
    
    async def _execute_workflow(
        self, entity_name: str, template_name: str, contact_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow for an entity."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/multi-entity-workflows/execute",
                json={
                    "entity_name": entity_name,
                    "template_name": template_name,
                    "contact_data": contact_data,
                    "trigger_context": {"test_mode": True}
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_bulk_workflow_execution(self) -> Dict[str, Any]:
        """Test bulk workflow execution across multiple entities."""
        try:
            # Prepare bulk workflow requests
            bulk_workflows = []
            
            for entity_name, contacts in self.test_contacts.items():
                for contact in contacts:
                    optimal_workflow = await self._get_optimal_workflow(entity_name, contact)
                    bulk_workflows.append({
                        "entity_name": entity_name,
                        "template_name": optimal_workflow,
                        "contact_data": contact,
                        "trigger_context": {"test_mode": True, "bulk_execution": True}
                    })
            
            # Execute bulk workflows
            async with self.session.post(
                f"{self.base_url}/api/multi-entity-workflows/execute-bulk",
                json={
                    "workflows": bulk_workflows,
                    "execution_mode": "parallel"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Bulk workflow execution completed: {result}")
                    return result
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error in bulk workflow execution: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_workflow_metrics(self) -> Dict[str, Any]:
        """Test workflow metrics and analytics."""
        try:
            async with self.session.get(f"{self.base_url}/api/multi-entity-workflows/metrics") as response:
                if response.status == 200:
                    metrics_data = await response.json()
                    logger.info(f"Workflow metrics: {metrics_data}")
                    return metrics_data
                else:
                    logger.error(f"Failed to get metrics: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting workflow metrics: {e}")
            return {}
    
    async def test_workflow_status_monitoring(self) -> Dict[str, Any]:
        """Test workflow status monitoring."""
        try:
            # Test overall status
            async with self.session.get(f"{self.base_url}/api/multi-entity-workflows/status") as response:
                if response.status == 200:
                    overall_status = await response.json()
                    logger.info(f"Overall workflow status: {overall_status}")
                else:
                    overall_status = {"error": f"HTTP {response.status}"}
            
            # Test entity-specific status
            entity_statuses = {}
            for entity_name in self.test_contacts.keys():
                async with self.session.get(
                    f"{self.base_url}/api/multi-entity-workflows/status",
                    params={"entity_name": entity_name}
                ) as response:
                    if response.status == 200:
                        entity_status = await response.json()
                        entity_statuses[entity_name] = entity_status
                        logger.info(f"{entity_name} status: {entity_status}")
                    else:
                        entity_statuses[entity_name] = {"error": f"HTTP {response.status}"}
            
            return {
                "overall_status": overall_status,
                "entity_statuses": entity_statuses
            }
            
        except Exception as e:
            logger.error(f"Error testing workflow status: {e}")
            return {"error": str(e)}
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive multi-entity workflow test suite."""
        logger.info("🧪 Starting Project 2: Multi-Entity Workflow Expansion Test Suite...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "project": "Project 2: Multi-Entity Intelligent Workflow Expansion",
            "tests": {},
            "overall_success": False
        }
        
        # Test 1: System Health
        logger.info("Testing multi-entity system health...")
        results["tests"]["system_health"] = await self.test_multi_entity_health()
        
        if not results["tests"]["system_health"]:
            logger.error("❌ Multi-entity system health check failed - aborting tests")
            return results
        
        # Test 2: Supported Entities
        logger.info("Testing supported entities...")
        entities_data = await self.test_supported_entities()
        results["tests"]["supported_entities"] = bool(entities_data.get("success"))
        results["entities_data"] = entities_data
        
        # Test 3: Workflow Templates
        logger.info("Testing workflow templates...")
        templates_data = await self.test_workflow_templates()
        results["tests"]["workflow_templates"] = bool(templates_data.get("success"))
        results["templates_data"] = templates_data
        
        # Test 4: Entity-Specific Workflows
        logger.info("Testing entity-specific workflows...")
        workflow_results = await self.test_entity_specific_workflows()
        entity_success = all(
            any(result.get("success", False) for result in entity_results)
            for entity_results in workflow_results.values()
        )
        results["tests"]["entity_specific_workflows"] = entity_success
        results["workflow_execution_results"] = workflow_results
        
        # Test 5: Bulk Workflow Execution
        logger.info("Testing bulk workflow execution...")
        bulk_result = await self.test_bulk_workflow_execution()
        results["tests"]["bulk_workflow_execution"] = bulk_result.get("success", False)
        results["bulk_execution_data"] = bulk_result
        
        # Test 6: Workflow Metrics
        logger.info("Testing workflow metrics...")
        metrics_data = await self.test_workflow_metrics()
        results["tests"]["workflow_metrics"] = bool(metrics_data.get("success"))
        results["metrics_data"] = metrics_data
        
        # Test 7: Status Monitoring
        logger.info("Testing workflow status monitoring...")
        status_data = await self.test_workflow_status_monitoring()
        results["tests"]["status_monitoring"] = not status_data.get("error")
        results["status_data"] = status_data
        
        # Calculate overall success
        test_results = [v for k, v in results["tests"].items() if isinstance(v, bool)]
        success_rate = sum(test_results) / len(test_results) if test_results else 0
        results["overall_success"] = success_rate >= 0.8  # 80% success rate
        results["success_rate"] = success_rate
        
        # Log results
        if results["overall_success"]:
            logger.info(f"✅ Project 2 test suite completed successfully! Success rate: {success_rate:.1%}")
        else:
            logger.warning(f"⚠️ Project 2 test suite completed with issues. Success rate: {success_rate:.1%}")
        
        return results


async def main():
    """Main test function."""
    print("🚀 Project 2: Multi-Entity Intelligent Workflow Expansion Test Suite")
    print("=" * 70)
    
    async with MultiEntityWorkflowTester() as tester:
        results = await tester.run_comprehensive_test()
        
        print("\n📊 Project 2 Test Results Summary:")
        print("=" * 40)
        
        for test_name, result in results["tests"].items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Success Rate: {results['success_rate']:.1%}")
        print(f"Overall Status: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}")
        
        # Entity-specific results
        if "workflow_execution_results" in results:
            print(f"\n📈 Entity-Specific Results:")
            for entity, entity_results in results["workflow_execution_results"].items():
                successful = sum(1 for r in entity_results if r.get("success", False))
                total = len(entity_results)
                print(f"  {entity.replace('_', ' ').title()}: {successful}/{total} workflows successful")
        
        # Save detailed results
        with open("test_results_project2_multi_entity.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed results saved to: test_results_project2_multi_entity.json")
        
        if not results["overall_success"]:
            print("\n🔧 Troubleshooting Tips:")
            print("- Ensure the enhanced server is running: python main_realtime_enhanced.py")
            print("- Check that multi-entity workflow automation is initialized")
            print("- Verify that all entity templates are loaded correctly")
            print("- Check server logs for detailed error information")


if __name__ == "__main__":
    asyncio.run(main())
