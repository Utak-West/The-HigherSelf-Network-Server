#!/usr/bin/env python3
"""Test script to verify settings configuration after Pydantic V2 fixes."""

import sys
import os
sys.path.append('.')

os.environ['TESTING_MODE'] = 'true'
os.environ['NOTION_API_TOKEN'] = 'test_token_12345678901234567890123456789012345678901234567890'
os.environ['TEST_MODE'] = 'true'
os.environ['REDIS_URI'] = 'redis://localhost:6379/0'
os.environ['SERVER_WEBHOOK_SECRET'] = 'test_webhook_secret_12345'

try:
    from config.settings import settings
    print('✅ Settings loaded successfully')
    print(f'Notion token valid: {settings.notion.is_token_valid}')
    print(f'Redis URI: {settings.redis.uri}')
    print('✅ All settings configurations working properly')
except Exception as e:
    print(f'❌ Settings failed: {e}')
    import traceback
    traceback.print_exc()
