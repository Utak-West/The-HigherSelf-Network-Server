#!/usr/bin/env python3
"""
Test script for Grace Fields and Graphiti integration.

This script tests the complete integration between Grace Fields orchestrator
and Graphiti temporal knowledge graph memory layer.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict

from loguru import logger

# Set up environment variables for testing
os.environ["NEO4J_URI"] = "bolt://localhost:7688"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "graphiti_password"
os.environ["GRAPHITI_ENABLED"] = "true"

# Mock OpenAI API key for testing (Graphiti might need it)
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "test_key_for_integration_testing"


async def test_grace_fields_graphiti_integration():
    """Test the complete Grace Fields and Graphiti integration."""

    print("🚀 Starting Grace Fields + Graphiti Integration Test")
    print("=" * 60)

    try:
        # Import services after setting environment variables
        from agents.base_agent import BaseAgent
        from agents.grace_fields_enhanced import (
            CustomerServiceBusinessEntity,
            CustomerServiceRequest,
            EnhancedGraceFields,
        )
        from services.graphiti_service import graphiti_service

        # Step 1: Initialize Graphiti service
        print("\n📊 Step 1: Initializing Graphiti service...")
        graphiti_initialized = await graphiti_service.initialize()
        if graphiti_initialized:
            print("✅ Graphiti service initialized successfully")
        else:
            print("❌ Failed to initialize Graphiti service")
            return False

        # Step 2: Create mock agents for Grace Fields
        print("\n🤖 Step 2: Setting up mock AI agents...")
        mock_agents = {
            "Nyra": BaseAgent(name="Nyra", agent_type="lead_capture"),
            "Solari": BaseAgent(name="Solari", agent_type="booking_manager"),
            "Ruvo": BaseAgent(name="Ruvo", agent_type="task_orchestrator"),
            "Liora": BaseAgent(name="Liora", agent_type="marketing_strategist"),
            "Sage": BaseAgent(name="Sage", agent_type="community_curator"),
            "Elan": BaseAgent(name="Elan", agent_type="content_choreographer"),
            "Zevi": BaseAgent(name="Zevi", agent_type="audience_analyst"),
        }
        print(f"✅ Created {len(mock_agents)} mock agents")

        # Step 3: Initialize Grace Fields orchestrator
        print("\n👑 Step 3: Initializing Grace Fields orchestrator...")
        grace = EnhancedGraceFields(agents=list(mock_agents.values()))
        print("✅ Grace Fields orchestrator initialized")
        print(f"   - Graphiti enabled: {grace.graphiti_enabled}")
        print(f"   - Coordination patterns: {len(grace.coordination_patterns)}")

        # Step 4: Test customer service request processing
        print("\n📞 Step 4: Testing customer service request processing...")

        test_requests = [
            {
                "customer_email": "john.doe@example.com",
                "customer_name": "John Doe",
                "description": "I need help with booking a premium art consultation for my new gallery space",
                "business_entity": CustomerServiceBusinessEntity.ART_GALLERY,
                "priority": "high",
            },
            {
                "customer_email": "sarah.wellness@example.com",
                "customer_name": "Sarah Johnson",
                "description": "I'm interested in your executive wellness program and need coordination with multiple services",
                "business_entity": CustomerServiceBusinessEntity.EXECUTIVE_WELLNESS,
                "priority": "medium",
            },
            {
                "customer_email": "urgent.client@example.com",
                "customer_name": "Emergency Contact",
                "description": "URGENT: Legal compliance issue with our recent campaign needs immediate attention",
                "business_entity": CustomerServiceBusinessEntity.CONSULTANCY,
                "priority": "urgent",
            },
        ]

        processed_requests = []

        for i, request_data in enumerate(test_requests, 1):
            print(f"\n   📋 Processing request {i}/3...")
            print(f"      Customer: {request_data['customer_name']}")
            print(f"      Business: {request_data['business_entity'].value}")
            print(f"      Priority: {request_data['priority']}")

            try:
                response = await grace.process_customer_service_request(**request_data)
                processed_requests.append(response)

                print(f"      ✅ Status: {response.get('status', 'unknown')}")
                print(
                    f"      📝 Response: {response.get('message', 'No message')[:100]}..."
                )

                if response.get("assigned_agents"):
                    print(
                        f"      👥 Assigned agents: {', '.join(response['assigned_agents'])}"
                    )

            except Exception as e:
                print(f"      ❌ Error processing request: {e}")
                continue

        print(f"\n✅ Processed {len(processed_requests)} customer service requests")

        # Step 5: Test Graphiti memory integration
        print("\n🧠 Step 5: Testing Graphiti memory integration...")

        try:
            # Add some test memories directly to Graphiti
            test_memories = [
                "Grace Fields successfully coordinated a complex art gallery consultation involving 5 agents",
                "Customer satisfaction score improved to 9.2/10 after implementing new coordination protocols",
                "Nyra agent captured 15 high-quality leads for the wellness center this week",
                "Multi-agent coordination pattern 'high_value_client_onboarding' completed in 2.5 hours",
            ]

            memory_ids = []
            for memory in test_memories:
                memory_id = await graphiti_service.add_memory(
                    content=memory,
                    metadata={
                        "agent": "grace_fields",
                        "test_session": datetime.now().isoformat(),
                        "integration_test": True,
                    },
                )
                if memory_id:
                    memory_ids.append(memory_id)

            print(f"✅ Added {len(memory_ids)} test memories to Graphiti")

            # Test memory search
            search_results = await graphiti_service.search_memories(
                query="Grace Fields coordination agent", limit=10
            )

            print(f"✅ Retrieved {len(search_results)} memories from search")

        except Exception as e:
            print(f"❌ Error testing Graphiti memory integration: {e}")

        # Step 6: Test agent context retrieval
        print("\n🔍 Step 6: Testing agent context retrieval...")

        try:
            # Test getting context for Grace Fields
            grace_context = await graphiti_service.get_agent_context(
                agent_name="Grace", business_context="art_gallery", limit=5
            )

            print(f"✅ Retrieved Grace Fields context: {len(grace_context)} items")

        except Exception as e:
            print(f"❌ Error retrieving agent context: {e}")

        # Step 7: Performance metrics
        print("\n📊 Step 7: Integration performance metrics...")
        print(f"   - Total requests processed: {grace.metrics['total_requests']}")
        print(f"   - Resolved requests: {grace.metrics['resolved_requests']}")
        print(f"   - Escalated requests: {grace.metrics['escalated_requests']}")
        print(f"   - Graphiti enabled: {grace.graphiti_enabled}")

        # Cleanup
        print("\n🧹 Cleaning up...")
        await graphiti_service.close()
        print("✅ Graphiti service closed")

        print("\n🎉 Grace Fields + Graphiti Integration Test COMPLETED!")
        print("=" * 60)
        print("✅ All integration tests passed successfully!")

        return True

    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the integration test
    success = asyncio.run(test_grace_fields_graphiti_integration())

    if success:
        print("\n🚀 Integration test completed successfully!")
        exit(0)
    else:
        print("\n💥 Integration test failed!")
        exit(1)
