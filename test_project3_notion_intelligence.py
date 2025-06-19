#!/usr/bin/env python3
"""
Project 3: Bidirectional Notion Intelligence Hub Test Suite

Comprehensive test suite for the bidirectional Notion synchronization system
with AI agent intelligence across all business entities.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List

import aiohttp
import pytest
from loguru import logger


class NotionIntelligenceHubTester:
    """Test suite for Notion Intelligence Hub."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
        # Test data for intelligence hub testing
        self.test_contacts = {
            "new_contact": {
                "email": "intelligence.test@the7space.com",
                "first_name": "Intelligence",
                "last_name": "Test",
                "message": "Testing AI-powered contact enrichment and synchronization",
                "interests": ["art", "technology", "ai"],
                "source": "intelligence_hub_test"
            },
            "duplicate_contact": {
                "email": "intelligence.test@the7space.com",  # Same email for duplicate detection
                "first_name": "Intelligence",
                "last_name": "Tester",  # Slightly different name
                "message": "Another test for duplicate detection",
                "interests": ["art", "testing"],
                "source": "duplicate_test"
            },
            "existing_contacts": [
                {
                    "id": "existing_1",
                    "email": "existing@the7space.com",
                    "first_name": "Existing",
                    "last_name": "Contact",
                    "entity": "the_7_space",
                    "last_updated": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "existing_2",
                    "email": "old@amconsulting.com",
                    "first_name": "Old",
                    "last_name": "Client",
                    "entity": "am_consulting",
                    "last_updated": "2023-12-01T00:00:00Z"
                }
            ]
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_intelligence_hub_health(self) -> bool:
        """Test Notion Intelligence Hub health."""
        try:
            async with self.session.get(f"{self.base_url}/api/notion-intelligence/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"Intelligence Hub health: {health_data}")
                    return health_data.get("status") == "healthy"
                return False
        except Exception as e:
            logger.error(f"Intelligence Hub health check failed: {e}")
            return False
    
    async def test_intelligence_hub_status(self) -> Dict[str, Any]:
        """Test getting Intelligence Hub status."""
        try:
            async with self.session.get(f"{self.base_url}/api/notion-intelligence/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    logger.info(f"Intelligence Hub status: {status_data}")
                    return status_data
                else:
                    logger.error(f"Failed to get status: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting Intelligence Hub status: {e}")
            return {}
    
    async def test_bidirectional_sync(self) -> Dict[str, Any]:
        """Test bidirectional synchronization."""
        try:
            # Test sync for all entities
            async with self.session.post(
                f"{self.base_url}/api/notion-intelligence/sync",
                json={
                    "entity_name": None,  # All entities
                    "force_full_sync": True,
                    "include_enrichment": True
                }
            ) as response:
                if response.status == 200:
                    sync_result = await response.json()
                    logger.info(f"Bidirectional sync result: {sync_result}")
                    return sync_result
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"Error testing bidirectional sync: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_entity_specific_sync(self) -> Dict[str, List[Dict[str, Any]]]:
        """Test entity-specific synchronization."""
        results = {}
        entities = ["the_7_space", "am_consulting", "higherself_core"]
        
        for entity in entities:
            try:
                async with self.session.post(
                    f"{self.base_url}/api/notion-intelligence/sync",
                    json={
                        "entity_name": entity,
                        "force_full_sync": False,
                        "include_enrichment": True
                    }
                ) as response:
                    if response.status == 200:
                        sync_result = await response.json()
                        results[entity] = {
                            "success": sync_result.get("success", False),
                            "sync_result": sync_result
                        }
                        logger.info(f"Entity {entity} sync completed")
                    else:
                        error_text = await response.text()
                        results[entity] = {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
                
                # Small delay between entity syncs
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error syncing entity {entity}: {e}")
                results[entity] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    async def test_contact_enrichment(self) -> Dict[str, Any]:
        """Test AI-powered contact enrichment."""
        try:
            # Test enrichment for each entity
            enrichment_results = {}
            entities = ["the_7_space", "am_consulting", "higherself_core"]
            
            for entity in entities:
                async with self.session.post(
                    f"{self.base_url}/api/notion-intelligence/test-enrichment",
                    params={"entity_name": entity},
                    json=self.test_contacts["new_contact"]
                ) as response:
                    if response.status == 200:
                        enrichment_result = await response.json()
                        enrichment_results[entity] = enrichment_result
                        logger.info(f"Contact enrichment test completed for {entity}")
                    else:
                        error_text = await response.text()
                        enrichment_results[entity] = {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
            
            return {
                "success": True,
                "enrichment_results": enrichment_results
            }
            
        except Exception as e:
            logger.error(f"Error testing contact enrichment: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_duplicate_detection(self) -> Dict[str, Any]:
        """Test intelligent duplicate detection."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/notion-intelligence/test-duplicate-detection",
                json={
                    "new_contact": self.test_contacts["duplicate_contact"],
                    "existing_contacts": self.test_contacts["existing_contacts"]
                }
            ) as response:
                if response.status == 200:
                    duplicate_result = await response.json()
                    logger.info(f"Duplicate detection test completed: {duplicate_result}")
                    return duplicate_result
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error testing duplicate detection: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_manual_enrichment(self) -> Dict[str, Any]:
        """Test manual contact enrichment."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/notion-intelligence/enrich",
                json={
                    "contact_id": "test_contact_123",
                    "entity_name": "the_7_space",
                    "enrichment_type": "full"
                }
            ) as response:
                if response.status == 200:
                    enrichment_result = await response.json()
                    logger.info(f"Manual enrichment test completed: {enrichment_result}")
                    return enrichment_result
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error testing manual enrichment: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_relationship_analysis(self) -> Dict[str, Any]:
        """Test contact relationship analysis."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/notion-intelligence/analyze-relationships",
                json={
                    "entity_name": None,  # All entities
                    "analysis_depth": "standard",
                    "include_cross_entity": True
                }
            ) as response:
                if response.status == 200:
                    analysis_result = await response.json()
                    logger.info(f"Relationship analysis completed: {analysis_result}")
                    return analysis_result
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error testing relationship analysis: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_sync_metrics(self) -> Dict[str, Any]:
        """Test synchronization metrics."""
        try:
            async with self.session.get(f"{self.base_url}/api/notion-intelligence/metrics") as response:
                if response.status == 200:
                    metrics_data = await response.json()
                    logger.info(f"Sync metrics: {metrics_data}")
                    return metrics_data
                else:
                    logger.error(f"Failed to get metrics: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting sync metrics: {e}")
            return {}
    
    async def test_entity_sync_status(self) -> Dict[str, Any]:
        """Test entity synchronization status."""
        try:
            async with self.session.get(f"{self.base_url}/api/notion-intelligence/entities") as response:
                if response.status == 200:
                    entities_data = await response.json()
                    logger.info(f"Entity sync status: {entities_data}")
                    return entities_data
                else:
                    logger.error(f"Failed to get entity status: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting entity sync status: {e}")
            return {}
    
    async def test_sync_history(self) -> Dict[str, Any]:
        """Test synchronization history."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/notion-intelligence/sync-history",
                params={"limit": 5}
            ) as response:
                if response.status == 200:
                    history_data = await response.json()
                    logger.info(f"Sync history: {history_data}")
                    return history_data
                else:
                    logger.error(f"Failed to get sync history: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting sync history: {e}")
            return {}
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Notion Intelligence Hub test suite."""
        logger.info("🧪 Starting Project 3: Bidirectional Notion Intelligence Hub Test Suite...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "project": "Project 3: Bidirectional Notion Intelligence Hub",
            "tests": {},
            "overall_success": False
        }
        
        # Test 1: System Health
        logger.info("Testing Intelligence Hub health...")
        results["tests"]["system_health"] = await self.test_intelligence_hub_health()
        
        if not results["tests"]["system_health"]:
            logger.error("❌ Intelligence Hub health check failed - aborting tests")
            return results
        
        # Test 2: Hub Status
        logger.info("Testing Intelligence Hub status...")
        status_data = await self.test_intelligence_hub_status()
        results["tests"]["hub_status"] = bool(status_data.get("success"))
        results["status_data"] = status_data
        
        # Test 3: Bidirectional Sync
        logger.info("Testing bidirectional synchronization...")
        sync_result = await self.test_bidirectional_sync()
        results["tests"]["bidirectional_sync"] = sync_result.get("success", False)
        results["sync_data"] = sync_result
        
        # Test 4: Entity-Specific Sync
        logger.info("Testing entity-specific synchronization...")
        entity_sync_results = await self.test_entity_specific_sync()
        entity_sync_success = all(
            result.get("success", False) for result in entity_sync_results.values()
        )
        results["tests"]["entity_specific_sync"] = entity_sync_success
        results["entity_sync_results"] = entity_sync_results
        
        # Test 5: Contact Enrichment
        logger.info("Testing AI-powered contact enrichment...")
        enrichment_result = await self.test_contact_enrichment()
        results["tests"]["contact_enrichment"] = enrichment_result.get("success", False)
        results["enrichment_data"] = enrichment_result
        
        # Test 6: Duplicate Detection
        logger.info("Testing intelligent duplicate detection...")
        duplicate_result = await self.test_duplicate_detection()
        results["tests"]["duplicate_detection"] = duplicate_result.get("success", False)
        results["duplicate_data"] = duplicate_result
        
        # Test 7: Manual Enrichment
        logger.info("Testing manual enrichment...")
        manual_enrichment_result = await self.test_manual_enrichment()
        results["tests"]["manual_enrichment"] = manual_enrichment_result.get("success", False)
        results["manual_enrichment_data"] = manual_enrichment_result
        
        # Test 8: Relationship Analysis
        logger.info("Testing contact relationship analysis...")
        relationship_result = await self.test_relationship_analysis()
        results["tests"]["relationship_analysis"] = relationship_result.get("success", False)
        results["relationship_data"] = relationship_result
        
        # Test 9: Sync Metrics
        logger.info("Testing sync metrics...")
        metrics_data = await self.test_sync_metrics()
        results["tests"]["sync_metrics"] = bool(metrics_data.get("success"))
        results["metrics_data"] = metrics_data
        
        # Test 10: Entity Status
        logger.info("Testing entity sync status...")
        entity_status_data = await self.test_entity_sync_status()
        results["tests"]["entity_status"] = bool(entity_status_data.get("success"))
        results["entity_status_data"] = entity_status_data
        
        # Test 11: Sync History
        logger.info("Testing sync history...")
        history_data = await self.test_sync_history()
        results["tests"]["sync_history"] = bool(history_data.get("success"))
        results["history_data"] = history_data
        
        # Calculate overall success
        test_results = [v for k, v in results["tests"].items() if isinstance(v, bool)]
        success_rate = sum(test_results) / len(test_results) if test_results else 0
        results["overall_success"] = success_rate >= 0.8  # 80% success rate
        results["success_rate"] = success_rate
        
        # Log results
        if results["overall_success"]:
            logger.info(f"✅ Project 3 test suite completed successfully! Success rate: {success_rate:.1%}")
        else:
            logger.warning(f"⚠️ Project 3 test suite completed with issues. Success rate: {success_rate:.1%}")
        
        return results


async def main():
    """Main test function."""
    print("🚀 Project 3: Bidirectional Notion Intelligence Hub Test Suite")
    print("=" * 70)
    
    async with NotionIntelligenceHubTester() as tester:
        results = await tester.run_comprehensive_test()
        
        print("\n📊 Project 3 Test Results Summary:")
        print("=" * 40)
        
        for test_name, result in results["tests"].items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Success Rate: {results['success_rate']:.1%}")
        print(f"Overall Status: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}")
        
        # Intelligence Hub specific results
        if "enrichment_data" in results:
            enrichment_results = results["enrichment_data"].get("enrichment_results", {})
            print(f"\n🧠 AI Enrichment Results:")
            for entity, result in enrichment_results.items():
                status = "✅" if result.get("success", False) else "❌"
                print(f"  {entity.replace('_', ' ').title()}: {status}")
        
        # Save detailed results
        with open("test_results_project3_notion_intelligence.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed results saved to: test_results_project3_notion_intelligence.json")
        
        if not results["overall_success"]:
            print("\n🔧 Troubleshooting Tips:")
            print("- Ensure the enhanced server is running: python main_realtime_enhanced.py")
            print("- Check that Notion Intelligence Hub is initialized")
            print("- Verify that AI agent orchestrator is working")
            print("- Check server logs for detailed error information")


if __name__ == "__main__":
    asyncio.run(main())
