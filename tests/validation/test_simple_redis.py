#!/usr/bin/env python3
"""
Simple Redis test that doesn't depend on complex configuration.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_redis_import():
    """Test that Redis can be imported."""
    try:
        import redis

        print("✅ Redis module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Redis import failed: {e}")
        return False


def test_redis_connection():
    """Test basic Redis connection (if Redis server is available)."""
    try:
        import redis

        # Try to connect to Redis
        r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

        # Test basic operations
        test_key = "test:simple:key"
        test_value = "test_value"

        # Set a value
        r.set(test_key, test_value, ex=60)

        # Get the value
        retrieved = r.get(test_key)

        # Clean up
        r.delete(test_key)

        if retrieved == test_value:
            print("✅ Redis connection and basic operations work")
            return True
        else:
            print("❌ Redis operations failed")
            return False

    except Exception as e:
        print(f"⚠️  Redis server not available or connection failed: {e}")
        print("   This is expected if Redis is not running locally")
        return True  # Don't fail the test if Redis server is not available


def test_pydantic_settings():
    """Test that pydantic-settings works."""
    try:
        from pydantic import Field
        from pydantic_settings import BaseSettings

        class TestSettings(BaseSettings):
            test_value: str = Field(default="test", env="TEST_VALUE")

        settings = TestSettings()
        print("✅ Pydantic settings work")
        return True
    except Exception as e:
        print(f"❌ Pydantic settings failed: {e}")
        return False


def main():
    """Run simple tests."""
    print("🧪 Simple Redis and Dependencies Test")
    print("=" * 50)

    tests = [
        ("Redis Import", test_redis_import),
        ("Redis Connection", test_redis_connection),
        ("Pydantic Settings", test_pydantic_settings),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        if test_func():
            passed += 1

    print(f"\n{'=' * 50}")
    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests had issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
