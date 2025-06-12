#!/usr/bin/env python3
"""
Graphiti Integration Demo for The HigherSelf Network Server

This example demonstrates how to use Graphiti's temporal knowledge graph
capabilities with The HigherSelf Network's AI agents for enhanced memory
and context management across business operations.
"""

import asyncio
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from loguru import logger

from models.graphiti_models import (GraphitiAgentName, GraphitiBusinessContext,
                                    GraphitiEpisodeRequest,
                                    GraphitiEpisodeType)
from services.graphiti_service import graphiti_service
from utils.graphiti_utils import (create_episode_from_agent_interaction,
                                  create_search_request,
                                  create_structured_episode,
                                  format_search_results_for_agent,
                                  validate_graphiti_config)


async def demo_basic_graphiti_operations():
    """Demonstrate basic Graphiti operations."""
    logger.info("=== Basic Graphiti Operations Demo ===")

    # 1. Add a text episode from Nyra (Lead Capture Agent)
    logger.info("1. Adding text episode from Nyra...")

    episode_uuid = await graphiti_service.add_episode(
        name="Nyra_lead_capture_20250129",
        episode_body="New lead captured: Sarah Johnson from wellness center inquiry. Interested in meditation classes and wellness coaching. Contact: sarah.j@email.com, phone: 555-0123. Preferred contact time: evenings.",
        source=GraphitiEpisodeType.TEXT,
        source_description="Lead capture interaction",
        agent_name=GraphitiAgentName.NYRA,
        business_context=GraphitiBusinessContext.WELLNESS_CENTER,
    )

    if episode_uuid:
        logger.info(f"✅ Episode added successfully with UUID: {episode_uuid}")
    else:
        logger.error("❌ Failed to add episode")
        return

    # 2. Add a structured episode from Solari (Booking Agent)
    logger.info("2. Adding structured episode from Solari...")

    booking_data = {
        "client_name": "Sarah Johnson",
        "service": "Wellness Coaching Session",
        "date": "2025-02-05",
        "time": "18:00",
        "duration": "60 minutes",
        "status": "confirmed",
        "payment_status": "paid",
        "notes": "First-time client, interested in stress management",
    }

    booking_episode = create_structured_episode(
        agent_name="Solari",
        data=booking_data,
        business_context="wellness_center",
        episode_type="booking_confirmation",
    )

    booking_uuid = await graphiti_service.add_episode(
        name=booking_episode.name,
        episode_body=booking_episode.episode_body,
        source=booking_episode.source,
        source_description=booking_episode.source_description,
        agent_name=booking_episode.agent_name,
        business_context=booking_episode.business_context,
    )

    if booking_uuid:
        logger.info(f"✅ Booking episode added with UUID: {booking_uuid}")
    else:
        logger.error("❌ Failed to add booking episode")

    # 3. Search for information about Sarah Johnson
    logger.info("3. Searching for information about Sarah Johnson...")

    search_results = await graphiti_service.search(
        query="Sarah Johnson wellness coaching meditation",
        limit=5,
        agent_name=GraphitiAgentName.GRACE,
        business_context=GraphitiBusinessContext.WELLNESS_CENTER,
    )

    if search_results:
        logger.info(f"✅ Found {len(search_results)} relevant results")
        for i, result in enumerate(search_results, 1):
            logger.info(f"   {i}. {result.fact}")
    else:
        logger.info("No search results found")

    # 4. Get agent context for Nyra
    logger.info("4. Getting agent context for Nyra...")

    context = await graphiti_service.get_agent_context(
        agent_name="Nyra", business_context="wellness_center", limit=10
    )

    if context:
        logger.info(
            f"✅ Retrieved context with {len(context.get('search_results', []))} search results"
        )
        logger.info(f"   Recent episodes: {len(context.get('recent_episodes', []))}")
    else:
        logger.info("No context found for Nyra")


async def demo_agent_workflow_integration():
    """Demonstrate how Graphiti integrates with agent workflows."""
    logger.info("\n=== Agent Workflow Integration Demo ===")

    # Simulate a multi-agent workflow for art gallery operations
    logger.info("Simulating art gallery client interaction workflow...")

    # 1. Nyra captures a lead
    lead_interaction = create_episode_from_agent_interaction(
        agent_name="Nyra",
        interaction_content="New art collector inquiry: Marcus Chen interested in contemporary paintings. Budget: $50k-100k. Prefers abstract and modern pieces. Available for gallery visit next week.",
        business_context="art_gallery",
        interaction_type="lead_capture",
    )

    lead_uuid = await graphiti_service.add_episode(
        name=lead_interaction.name,
        episode_body=lead_interaction.episode_body,
        source=lead_interaction.source,
        source_description=lead_interaction.source_description,
        agent_name=lead_interaction.agent_name,
        business_context=lead_interaction.business_context,
    )

    logger.info(f"1. Nyra captured lead: {lead_uuid}")

    # 2. Liora creates a marketing campaign
    campaign_data = {
        "campaign_name": "Contemporary Art Showcase",
        "target_audience": "High-value art collectors",
        "budget": 5000,
        "channels": ["email", "social_media", "gallery_events"],
        "duration": "30 days",
        "key_pieces": ["Abstract Series by Local Artist", "Modern Sculptures"],
        "expected_leads": 25,
    }

    campaign_episode = create_structured_episode(
        agent_name="Liora",
        data=campaign_data,
        business_context="art_gallery",
        episode_type="marketing_campaign",
    )

    campaign_uuid = await graphiti_service.add_episode(
        name=campaign_episode.name,
        episode_body=campaign_episode.episode_body,
        source=campaign_episode.source,
        source_description=campaign_episode.source_description,
        agent_name=campaign_episode.agent_name,
        business_context=campaign_episode.business_context,
    )

    logger.info(f"2. Liora created campaign: {campaign_uuid}")

    # 3. Solari schedules a gallery visit
    visit_data = {
        "client_name": "Marcus Chen",
        "visit_type": "Private Gallery Tour",
        "date": "2025-02-10",
        "time": "14:00",
        "duration": "90 minutes",
        "curator": "Senior Art Advisor",
        "focus_areas": ["Contemporary paintings", "Abstract art"],
        "preparation_notes": "Prepare portfolio of pieces in $50k-100k range",
    }

    visit_episode = create_structured_episode(
        agent_name="Solari",
        data=visit_data,
        business_context="art_gallery",
        episode_type="gallery_visit_booking",
    )

    visit_uuid = await graphiti_service.add_episode(
        name=visit_episode.name,
        episode_body=visit_episode.episode_body,
        source=visit_episode.source,
        source_description=visit_episode.source_description,
        agent_name=visit_episode.agent_name,
        business_context=visit_episode.business_context,
    )

    logger.info(f"3. Solari scheduled visit: {visit_uuid}")

    # 4. Grace orchestrates and searches for related information
    logger.info("4. Grace orchestrating workflow and gathering context...")

    search_request = create_search_request(
        query="Marcus Chen art collector contemporary paintings budget",
        agent_name="Grace",
        business_context="art_gallery",
        limit=10,
    )

    orchestration_results = await graphiti_service.search(
        query=search_request.query,
        agent_name=search_request.agent_name,
        business_context=search_request.business_context,
        limit=search_request.limit,
    )

    if orchestration_results:
        formatted_results = format_search_results_for_agent(
            [result.model_dump() for result in orchestration_results],
            "Grace",
            max_results=5,
        )
        logger.info("Grace's orchestration context:")
        logger.info(formatted_results)

    # 5. Get comprehensive context for the art gallery business
    gallery_context = await graphiti_service.get_agent_context(
        agent_name="Grace", business_context="art_gallery", limit=20
    )

    logger.info(
        f"5. Gallery context retrieved: {len(gallery_context.get('search_results', []))} facts"
    )


async def demo_health_and_validation():
    """Demonstrate health checking and configuration validation."""
    logger.info("\n=== Health and Validation Demo ===")

    # 1. Validate configuration
    logger.info("1. Validating Graphiti configuration...")
    config_validation = validate_graphiti_config()

    if config_validation["valid"]:
        logger.info("✅ Configuration is valid")
        logger.info(f"   Config: {config_validation['config']}")
    else:
        logger.error("❌ Configuration issues found:")
        for error in config_validation["errors"]:
            logger.error(f"   - {error}")

    if config_validation["warnings"]:
        logger.warning("Configuration warnings:")
        for warning in config_validation["warnings"]:
            logger.warning(f"   - {warning}")

    # 2. Check service health
    logger.info("2. Checking Graphiti service health...")
    health_status = await graphiti_service.get_health_status()

    logger.info(f"Service status: {health_status.get('status', 'unknown')}")
    logger.info(f"Cache TTL: {health_status.get('cache_ttl', 'unknown')} seconds")
    logger.info(f"Last check: {health_status.get('last_check', 'unknown')}")

    if health_status.get("error"):
        logger.error(f"Health check error: {health_status['error']}")


async def main():
    """Main demo function."""
    # Load environment variables
    load_dotenv()

    logger.info(
        "🚀 Starting Graphiti Integration Demo for The HigherSelf Network Server"
    )

    # Check if Graphiti is enabled
    if os.environ.get("GRAPHITI_ENABLED", "true").lower() != "true":
        logger.error(
            "Graphiti is disabled. Please set GRAPHITI_ENABLED=true in your .env file"
        )
        return

    try:
        # Initialize Graphiti service
        logger.info("Initializing Graphiti service...")
        success = await graphiti_service.initialize()

        if not success:
            logger.error("Failed to initialize Graphiti service")
            return

        logger.info("✅ Graphiti service initialized successfully")

        # Run demos
        await demo_basic_graphiti_operations()
        await demo_agent_workflow_integration()
        await demo_health_and_validation()

        logger.info("🎉 Demo completed successfully!")

    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        logger.exception(e)

    finally:
        # Clean up
        try:
            await graphiti_service.close()
            logger.info("Graphiti service closed")
        except Exception as e:
            logger.error(f"Error closing Graphiti service: {e}")


if __name__ == "__main__":
    asyncio.run(main())
