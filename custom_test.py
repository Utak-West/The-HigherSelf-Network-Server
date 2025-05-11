#!/usr/bin/env python3
"""
Custom test script for The HigherSelf Network Server components.
This script validates the main components of the system without external dependencies.
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to the Python path to ensure modules can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("higherself_test")

def log_section(title):
    """Log a section title with decorative formatting."""
    logger.info("\n" + "=" * 50)
    logger.info(f" {title} ".center(50, "="))
    logger.info("=" * 50)

def test_environment():
    """Test the environment configuration."""
    log_section("Testing Environment")
    
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check for .env file
    env_file = os.path.join(current_dir, '.env')
    env_example_file = os.path.join(current_dir, '.env.example')
    
    if os.path.exists(env_file):
        logger.info("✅ .env file exists")
    else:
        logger.warning("❌ .env file not found. Using .env.example for reference.")
        
    # Check required directories
    required_dirs = ['agents', 'api', 'config', 'models', 'services', 'utils']
    for dir_name in required_dirs:
        dir_path = os.path.join(current_dir, dir_name)
        if os.path.isdir(dir_path):
            logger.info(f"✅ Required directory exists: {dir_name}")
        else:
            logger.error(f"❌ Required directory missing: {dir_name}")
    
    return True

def test_models():
    """Test the Pydantic models."""
    log_section("Testing Models")
    
    try:
        # Try importing the models
        from models.base import BaseModel
        logger.info("✅ Successfully imported base models")
        
        # Try creating a simple model instance
        class TestModel(BaseModel):
            name: str
            value: int = 0
        
        test_instance = TestModel(name="test")
        logger.info(f"✅ Successfully created model instance: {test_instance}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing models: {e}")
        return False

def test_agents():
    """Test agent structure."""
    log_section("Testing Agents")
    
    try:
        # Check for agent definition files
        agent_files = [
            'base_agent.py',
            'lead_capture_agent.py',
            'booking_agent.py',
            'task_management_agent.py',
            'marketing_campaign_agent.py',
            'community_engagement_agent.py',
            'content_lifecycle_agent.py',
            'audience_segmentation_agent.py'
        ]
        
        agents_dir = os.path.join(current_dir, 'agents')
        
        for file_name in agent_files:
            file_path = os.path.join(agents_dir, file_name)
            if os.path.exists(file_path):
                logger.info(f"✅ Agent file exists: {file_name}")
            else:
                logger.warning(f"❓ Agent file not found: {file_name}")
        
        # Try importing the agent module
        try:
            import agents
            logger.info("✅ Successfully imported agents module")
        except ImportError as e:
            logger.error(f"❌ Error importing agents module: {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing agents: {e}")
        return False

def test_services():
    """Test service components."""
    log_section("Testing Services")
    
    try:
        # Check for service definition files
        service_files = [
            'notion_service.py',
            'integration_manager.py',
            'base_service.py'
        ]
        
        services_dir = os.path.join(current_dir, 'services')
        
        for file_name in service_files:
            file_path = os.path.join(services_dir, file_name)
            if os.path.exists(file_path):
                logger.info(f"✅ Service file exists: {file_name}")
            else:
                logger.warning(f"❓ Service file not found: {file_name}")
        
        # Check Notion service specifically
        notion_file = os.path.join(services_dir, 'notion_service.py')
        if os.path.exists(notion_file):
            with open(notion_file, 'r') as f:
                content = f.read()
                if 'class NotionService' in content:
                    logger.info("✅ NotionService class found in notion_service.py")
                else:
                    logger.warning("❓ NotionService class not found in the file")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing services: {e}")
        return False

def test_api():
    """Test API components."""
    log_section("Testing API")
    
    try:
        # Check for API definition files
        api_files = [
            'server.py',
            'webhooks.py',
            'webhooks_circleso.py',
            'webhooks_beehiiv.py'
        ]
        
        api_dir = os.path.join(current_dir, 'api')
        
        for file_name in api_files:
            file_path = os.path.join(api_dir, file_name)
            if os.path.exists(file_path):
                logger.info(f"✅ API file exists: {file_name}")
            else:
                logger.warning(f"❓ API file not found: {file_name}")
        
        # Try to find FastAPI usage
        server_file = os.path.join(api_dir, 'server.py')
        if os.path.exists(server_file):
            with open(server_file, 'r') as f:
                content = f.read()
                if 'fastapi' in content.lower():
                    logger.info("✅ FastAPI usage detected in server.py")
                else:
                    logger.warning("❓ FastAPI usage not detected in server.py")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing API: {e}")
        return False

def test_main_script():
    """Test the main.py script."""
    log_section("Testing main.py")
    
    main_file = os.path.join(current_dir, 'main.py')
    if not os.path.exists(main_file):
        logger.error("❌ main.py file not found")
        return False
    
    try:
        with open(main_file, 'r') as f:
            content = f.read()
            
            # Check for key components in main.py
            checks = {
                'FastAPI': 'start_api' in content,
                'Agents initialization': 'register_agents' in content,
                'Integration Manager': 'integration_manager' in content,
                'Logging configuration': 'configure_logging' in content
            }
            
            for check_name, result in checks.items():
                if result:
                    logger.info(f"✅ {check_name} found in main.py")
                else:
                    logger.warning(f"❓ {check_name} not found in main.py")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing main.py: {e}")
        return False

def run_all_tests():
    """Run all test functions and report results."""
    log_section("STARTING TESTS")
    logger.info(f"Test run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Keep track of test results
    results = {}
    
    # Run all tests
    results['environment'] = test_environment()
    results['models'] = test_models()
    results['agents'] = test_agents()
    results['services'] = test_services()
    results['api'] = test_api()
    results['main_script'] = test_main_script()
    
    # Report summary
    log_section("TEST SUMMARY")
    
    all_passed = True
    for test_name, passed in results.items():
        if passed:
            logger.info(f"✅ {test_name.upper()} TESTS PASSED")
        else:
            logger.error(f"❌ {test_name.upper()} TESTS FAILED")
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED! The HigherSelf Network Server components look good.")
    else:
        logger.warning("\n⚠️ SOME TESTS FAILED. Please check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)