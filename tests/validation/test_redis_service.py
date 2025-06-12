#!/usr/bin/env python3
"""Test script to verify Redis service functionality after environment variable caching optimization."""

import os
import sys

sys.path.append(".")

os.environ["TESTING_MODE"] = "true"
os.environ[
    "NOTION_API_TOKEN"
] = "test_token_12345678901234567890123456789012345678901234567890"
os.environ["TEST_MODE"] = "true"
os.environ["REDIS_URI"] = "redis://localhost:6379/0"

try:
    from services.redis_service import RedisService

    rs = RedisService()
    print("✅ Redis service initialized successfully with environment variable caching")

    RedisService.refresh_env_cache()
    print("✅ Redis service cache refresh functionality working")

except Exception as e:
    print(f"❌ Redis service failed: {e}")
    import traceback

    traceback.print_exc()
