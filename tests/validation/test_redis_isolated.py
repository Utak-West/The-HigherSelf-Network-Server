#!/usr/bin/env python3
"""Isolated test script to verify Redis service functionality without importing other services."""

import os
import sys

sys.path.append(".")

os.environ["TESTING_MODE"] = "true"
os.environ["TEST_MODE"] = "true"
os.environ["REDIS_URI"] = "redis://localhost:6379/0"

try:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "redis_service",
        "/home/ubuntu/repos/The-HigherSelf-Network-Server/services/redis_service.py",
    )
    redis_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(redis_module)

    RedisService = redis_module.RedisService
    rs = RedisService()
    print("✅ Redis service initialized successfully with environment variable caching")

    RedisService.refresh_env_cache()
    print("✅ Redis service cache refresh functionality working")

except Exception as e:
    print(f"❌ Redis service failed: {e}")
    import traceback

    traceback.print_exc()
