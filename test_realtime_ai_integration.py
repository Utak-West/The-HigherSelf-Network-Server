#!/usr/bin/env python3
"""
Real-Time AI Integration Test Suite

This script tests the enhanced Nyra real-time contact processing capabilities
and integration with the WordPress webhook system.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

import aiohttp
import pytest
from loguru import logger


class RealtimeAITester:
    """Test suite for real-time AI integration."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_server_health(self) -> bool:
        """Test if the enhanced server is running and healthy."""
        try:
            async with self.session.get(f"{self.base_url}/api/health/realtime") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"Server health: {health_data}")
                    return health_data.get("status") == "healthy"
                return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def test_ai_status(self) -> Dict[str, Any]:
        """Test AI agent status endpoint."""
        try:
            async with self.session.get(f"{self.base_url}/api/ai/status") as response:
                if response.status == 200:
                    ai_status = await response.json()
                    logger.info(f"AI Status: {ai_status}")
                    return ai_status
                else:
                    logger.error(f"AI status check failed: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"AI status test failed: {e}")
            return {}
    
    async def test_contact_processing(self) -> bool:
        """Test manual contact processing through AI pipeline."""
        test_contact = {
            "email": "test@the7space.com",
            "first_name": "Test",
            "last_name": "Artist",
            "phone": "+1-555-0123",
            "message": "I'm interested in exhibiting my artwork at The 7 Space gallery.",
            "interests": ["art", "gallery", "exhibition"],
            "source": "website_test",
            "source_metadata": {
                "page": "contact_form",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/ai/process-contact",
                json=test_contact
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Contact processing result: {result}")
                    return result.get("success", False)
                else:
                    logger.error(f"Contact processing failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Contact processing test failed: {e}")
            return False
    
    async def test_webhook_integration(self) -> bool:
        """Test WordPress webhook integration with AI processing."""
        webhook_payload = {
            "email": "webhook.test@the7space.com",
            "first_name": "Webhook",
            "last_name": "Test",
            "phone": "+1-555-0456",
            "message": "Testing webhook integration with AI processing for wellness services.",
            "interests": ["wellness", "meditation", "healing"],
            "source_metadata": {
                "form_id": "contact_form_7",
                "page_url": "https://the7space.com/contact",
                "user_agent": "Test Agent"
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/contact-workflows/register",
                json=webhook_payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Webhook integration result: {result}")
                    return (
                        result.get("success", False) and 
                        result.get("ai_processing_queued", False)
                    )
                else:
                    logger.error(f"Webhook integration failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Webhook integration test failed: {e}")
            return False
    
    async def test_ai_metrics(self) -> Dict[str, Any]:
        """Test AI metrics endpoint."""
        try:
            async with self.session.get(f"{self.base_url}/api/ai/metrics") as response:
                if response.status == 200:
                    metrics = await response.json()
                    logger.info(f"AI Metrics: {metrics}")
                    return metrics
                else:
                    logger.error(f"AI metrics check failed: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"AI metrics test failed: {e}")
            return {}
    
    async def test_multi_entity_processing(self) -> bool:
        """Test multi-entity contact processing."""
        test_contacts = [
            {
                "email": "artist@the7space.com",
                "first_name": "Gallery",
                "last_name": "Artist",
                "message": "I want to exhibit my paintings",
                "interests": ["art", "gallery"],
                "source": "the7space_website"
            },
            {
                "email": "client@amconsulting.com",
                "first_name": "Business",
                "last_name": "Client",
                "message": "I need consulting services for my startup",
                "interests": ["business", "consulting"],
                "source": "am_consulting_referral"
            },
            {
                "email": "member@higherself.com",
                "first_name": "Community",
                "last_name": "Member",
                "message": "I want to join the HigherSelf community",
                "interests": ["community", "personal_growth"],
                "source": "higherself_platform"
            }
        ]
        
        success_count = 0
        
        for contact in test_contacts:
            try:
                async with self.session.post(
                    f"{self.base_url}/api/ai/process-contact",
                    json=contact
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success", False):
                            success_count += 1
                            logger.info(f"Multi-entity contact processed: {contact['email']}")
                    
                # Small delay between requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Multi-entity test failed for {contact['email']}: {e}")
        
        return success_count == len(test_contacts)
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        logger.info("🧪 Starting Real-Time AI Integration Test Suite...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_success": False
        }
        
        # Test 1: Server Health
        logger.info("Testing server health...")
        results["tests"]["server_health"] = await self.test_server_health()
        
        if not results["tests"]["server_health"]:
            logger.error("❌ Server health check failed - aborting tests")
            return results
        
        # Test 2: AI Status
        logger.info("Testing AI status...")
        ai_status = await self.test_ai_status()
        results["tests"]["ai_status"] = bool(ai_status)
        results["ai_status_data"] = ai_status
        
        # Test 3: Contact Processing
        logger.info("Testing contact processing...")
        results["tests"]["contact_processing"] = await self.test_contact_processing()
        
        # Test 4: Webhook Integration
        logger.info("Testing webhook integration...")
        results["tests"]["webhook_integration"] = await self.test_webhook_integration()
        
        # Test 5: Multi-Entity Processing
        logger.info("Testing multi-entity processing...")
        results["tests"]["multi_entity_processing"] = await self.test_multi_entity_processing()
        
        # Test 6: AI Metrics
        logger.info("Testing AI metrics...")
        metrics = await self.test_ai_metrics()
        results["tests"]["ai_metrics"] = bool(metrics)
        results["ai_metrics_data"] = metrics
        
        # Calculate overall success
        test_results = [v for k, v in results["tests"].items() if isinstance(v, bool)]
        success_rate = sum(test_results) / len(test_results) if test_results else 0
        results["overall_success"] = success_rate >= 0.8  # 80% success rate
        results["success_rate"] = success_rate
        
        # Log results
        if results["overall_success"]:
            logger.info(f"✅ Test suite completed successfully! Success rate: {success_rate:.1%}")
        else:
            logger.warning(f"⚠️ Test suite completed with issues. Success rate: {success_rate:.1%}")
        
        return results


async def main():
    """Main test function."""
    print("🚀 HigherSelf Network Real-Time AI Integration Test Suite")
    print("=" * 60)
    
    async with RealtimeAITester() as tester:
        results = await tester.run_comprehensive_test()
        
        print("\n📊 Test Results Summary:")
        print("=" * 30)
        
        for test_name, result in results["tests"].items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Success Rate: {results['success_rate']:.1%}")
        print(f"Overall Status: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}")
        
        # Save detailed results
        with open("test_results_realtime_ai.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed results saved to: test_results_realtime_ai.json")
        
        if not results["overall_success"]:
            print("\n🔧 Troubleshooting Tips:")
            print("- Ensure the enhanced server is running: python main_realtime_enhanced.py")
            print("- Check that Notion API credentials are configured")
            print("- Verify that Nyra real-time agent is initialized")
            print("- Check server logs for detailed error information")


if __name__ == "__main__":
    asyncio.run(main())
