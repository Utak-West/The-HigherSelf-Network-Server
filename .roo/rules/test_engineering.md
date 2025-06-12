# HigherSelf Test Engineer

## Description
Specialized mode for creating and maintaining tests for The HigherSelf Network Server

## Instructions
- Create unit tests for agent functionality
- Implement integration tests for workflow processes
- Use mock Notion responses for testing
- Test event handling with different event types
- Ensure idempotent behavior with duplicate events
- Implement performance testing for critical paths
- Create fixtures for common test scenarios

## Capabilities
- Analyze existing code for test coverage
- Generate unit and integration tests
- Create mock objects and fixtures
- Implement test scenarios for workflows
- Design performance benchmarks

## Test Template

```python
"""
Tests for {component_name} in The HigherSelf Network Server.

This module contains unit and integration tests for {component_description}.
"""

import os
import json
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import components to test
from {module_path} import {component_name}

# Import test utilities
from tests.utils import create_mock_notion_service, create_test_workflow_instance


# Fixtures

@pytest.fixture
def mock_notion_service():
    """Create a mock Notion service for testing."""
    return create_mock_notion_service()

@pytest.fixture
def {component_instance_name}(mock_notion_service):
    """Create a {component_name} instance for testing."""
    return {component_name}(notion_client=mock_notion_service)

@pytest.fixture
def sample_event_data():
    """Create sample event data for testing."""
    return {
        "tracking_id": "test-tracking-id",
        "timestamp": datetime.now().isoformat(),
        # Add component-specific test data
    }


# Unit Tests

def test_{component_name}_initialization({component_instance_name}):
    """Test that {component_name} initializes correctly."""
    assert {component_instance_name}.name == "{expected_name}"
    assert {component_instance_name}.agent_id == "{expected_agent_id}"
    # Add more initialization assertions


@pytest.mark.asyncio
async def test_process_event_valid({component_instance_name}, sample_event_data):
    """Test processing a valid event."""
    # Arrange
    event_type = "{valid_event_type}"

    # Act
    result = await {component_instance_name}.process_event(event_type, sample_event_data)

    # Assert
    assert result["status"] == "processed"
    # Add more assertions based on expected behavior


@pytest.mark.asyncio
async def test_process_event_invalid({component_instance_name}, sample_event_data):
    """Test processing an invalid event."""
    # Arrange
    event_type = "invalid_event_type"

    # Act
    result = await {component_instance_name}.process_event(event_type, sample_event_data)

    # Assert
    assert result["status"] == "error"
    assert "Unsupported event type" in result["message"]


@pytest.mark.asyncio
async def test_check_health({component_instance_name}):
    """Test health check functionality."""
    # Act
    health_result = await {component_instance_name}.check_health()

    # Assert
    assert health_result["status"] in ["healthy", "degraded", "unhealthy"]
    assert "timestamp" in health_result
    assert health_result["agent_id"] == {component_instance_name}.agent_id


# Integration Tests

@pytest.mark.asyncio
async def test_workflow_integration(mock_notion_service):
    """Test integration with workflow system."""
    # Arrange
    {component_instance_name} = {component_name}(notion_client=mock_notion_service)
    workflow_instance = create_test_workflow_instance()

    # Mock necessary dependencies
    # ...

    # Act
    # Perform workflow steps

    # Assert
    # Verify workflow state and side effects


@pytest.mark.asyncio
async def test_error_handling({component_instance_name}, sample_event_data):
    """Test error handling during event processing."""
    # Arrange
    event_type = "{valid_event_type}"

    # Create a condition that will cause an error
    with patch.object({component_instance_name}, "run", side_effect=Exception("Test error")):
        # Act
        result = await {component_instance_name}.process_event(event_type, sample_event_data)

        # Assert
        assert result["status"] == "error"
        assert "Test error" in result["message"]


# Performance Tests

@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance({component_instance_name}, sample_event_data):
    """Test performance of event processing."""
    # Arrange
    event_type = "{valid_event_type}"
    iterations = 100

    # Act
    start_time = datetime.now()

    for _ in range(iterations):
        await {component_instance_name}.process_event(event_type, sample_event_data)

    execution_time = (datetime.now() - start_time).total_seconds()

    # Assert
    assert execution_time / iterations < 0.1  # Average execution time should be less than 100ms
```

## Test Scenarios

### Agent Tests
- Test event routing logic
- Test agent capabilities registration
- Test error handling and recovery
- Test interaction with Notion databases
- Test message bus communication

### Workflow Tests
- Test workflow state transitions
- Test multi-agent workflow orchestration
- Test workflow error handling
- Test workflow persistence
- Test workflow visualization

### Integration Tests
- Test Notion API integration
- Test external service integrations
- Test webhook handling
- Test data synchronization
- Test error recovery mechanisms

### Performance Tests
- Test event processing throughput
- Test concurrent workflow execution
- Test database query performance
- Test memory usage under load
- Test system recovery after failures
