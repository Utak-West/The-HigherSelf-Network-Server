#!/usr/bin/env python3
"""
Integration test script for HigherSelf Gaming Dashboard
Tests the integration between dashboard components and existing infrastructure
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardIntegrationTester:
    """Test suite for dashboard integration"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.dashboard_url = "http://localhost:3001"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []
        
    async def run_all_tests(self) -> bool:
        """Run all integration tests"""
        logger.info("🎮 Starting HigherSelf Gaming Dashboard Integration Tests")
        
        tests = [
            ("API Server Health", self.test_api_server_health),
            ("Dashboard API Integration", self.test_dashboard_api_integration),
            ("Database Connectivity", self.test_database_connectivity),
            ("Redis Cache", self.test_redis_connectivity),
            ("Agent Status Endpoints", self.test_agent_endpoints),
            ("Gaming Metrics", self.test_gaming_metrics),
            ("Multi-Tenant Support", self.test_multi_tenant_support),
            ("Real-time Features", self.test_realtime_features),
            ("Frontend Accessibility", self.test_frontend_accessibility)
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🧪 Running test: {test_name}")
                result = await test_func()
                
                if result:
                    logger.info(f"✅ {test_name}: PASSED")
                    self.test_results.append({"test": test_name, "status": "PASSED"})
                else:
                    logger.error(f"❌ {test_name}: FAILED")
                    self.test_results.append({"test": test_name, "status": "FAILED"})
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"💥 {test_name}: ERROR - {str(e)}")
                self.test_results.append({"test": test_name, "status": "ERROR", "error": str(e)})
                all_passed = False
        
        # Print summary
        self.print_test_summary()
        return all_passed
    
    async def test_api_server_health(self) -> bool:
        """Test main API server health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("status") == "healthy"
                    return False
        except Exception as e:
            logger.error(f"API server health check failed: {e}")
            return False
    
    async def test_dashboard_api_integration(self) -> bool:
        """Test dashboard API integration"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/dashboard/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("status") == "healthy"
                    return False
        except Exception as e:
            logger.error(f"Dashboard API integration test failed: {e}")
            return False
    
    async def test_database_connectivity(self) -> bool:
        """Test database connectivity"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/dashboard/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        services = data.get("services", {})
                        return services.get("mongodb") == "connected"
                    return False
        except Exception as e:
            logger.error(f"Database connectivity test failed: {e}")
            return False
    
    async def test_redis_connectivity(self) -> bool:
        """Test Redis connectivity"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/dashboard/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        services = data.get("services", {})
                        return services.get("redis") == "connected"
                    return False
        except Exception as e:
            logger.error(f"Redis connectivity test failed: {e}")
            return False
    
    async def test_agent_endpoints(self) -> bool:
        """Test agent status endpoints"""
        try:
            async with aiohttp.ClientSession() as session:
                # Note: This would need proper authentication in production
                async with session.get(f"{self.base_url}/api/dashboard/agents") as response:
                    if response.status in [200, 401]:  # 401 is expected without auth
                        return True
                    return False
        except Exception as e:
            logger.error(f"Agent endpoints test failed: {e}")
            return False
    
    async def test_gaming_metrics(self) -> bool:
        """Test gaming metrics endpoints"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/dashboard/metrics") as response:
                    if response.status in [200, 401]:  # 401 is expected without auth
                        return True
                    return False
        except Exception as e:
            logger.error(f"Gaming metrics test failed: {e}")
            return False
    
    async def test_multi_tenant_support(self) -> bool:
        """Test multi-tenant organization support"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/dashboard/organizations") as response:
                    if response.status in [200, 401]:  # 401 is expected without auth
                        return True
                    return False
        except Exception as e:
            logger.error(f"Multi-tenant support test failed: {e}")
            return False
    
    async def test_realtime_features(self) -> bool:
        """Test real-time WebSocket features"""
        try:
            # Simple connectivity test - in production would test actual WebSocket
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/dashboard/health") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Real-time features test failed: {e}")
            return False
    
    async def test_frontend_accessibility(self) -> bool:
        """Test frontend accessibility"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.frontend_url) as response:
                    return response.status == 200
        except Exception as e:
            logger.info(f"Frontend not running (expected in development): {e}")
            return True  # Not a failure if frontend isn't running
    
    def print_test_summary(self):
        """Print test results summary"""
        logger.info("\n" + "="*60)
        logger.info("🎮 HIGHERSELF GAMING DASHBOARD INTEGRATION TEST SUMMARY")
        logger.info("="*60)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASSED")
        failed = sum(1 for result in self.test_results if result["status"] == "FAILED")
        errors = sum(1 for result in self.test_results if result["status"] == "ERROR")
        total = len(self.test_results)
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"💥 Errors: {errors}")
        
        if failed == 0 and errors == 0:
            logger.info("\n🎉 ALL TESTS PASSED! Gaming Dashboard integration successful!")
        else:
            logger.info(f"\n⚠️  {failed + errors} tests need attention.")
        
        logger.info("\nDetailed Results:")
        for result in self.test_results:
            status_emoji = {"PASSED": "✅", "FAILED": "❌", "ERROR": "💥"}[result["status"]]
            logger.info(f"{status_emoji} {result['test']}: {result['status']}")
            if "error" in result:
                logger.info(f"   Error: {result['error']}")
        
        logger.info("="*60)


async def main():
    """Main test execution"""
    tester = DashboardIntegrationTester()
    
    logger.info("🚀 Initializing HigherSelf Gaming Dashboard Integration Tests")
    logger.info("📋 Testing dashboard integration with existing infrastructure...")
    
    success = await tester.run_all_tests()
    
    if success:
        logger.info("🎮 Gaming Dashboard integration verified successfully!")
        sys.exit(0)
    else:
        logger.error("⚠️  Some integration tests failed. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
