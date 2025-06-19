#!/usr/bin/env python3
"""
Notion Intelligence Hub API Endpoints

API endpoints for managing bidirectional Notion synchronization with AI intelligence
across The 7 Space, AM Consulting, and HigherSelf Core business entities.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from agents.multi_entity_agent_orchestrator import MultiEntityAgentOrchestrator
from services.notion_intelligence_hub import NotionIntelligenceHub
from services.notion_service import NotionService


# Initialize services
notion_service = NotionService()
agent_orchestrator = MultiEntityAgentOrchestrator(notion_service)
intelligence_hub = NotionIntelligenceHub(notion_service, agent_orchestrator)

router = APIRouter(prefix="/notion-intelligence", tags=["Notion Intelligence Hub"])


class SyncRequest(BaseModel):
    """Request model for synchronization."""
    entity_name: Optional[str] = None
    force_full_sync: bool = False
    include_enrichment: bool = True


class EnrichmentRequest(BaseModel):
    """Request model for manual enrichment."""
    contact_id: str
    entity_name: str
    enrichment_type: str = "full"  # full, basic, targeted


class RelationshipAnalysisRequest(BaseModel):
    """Request model for relationship analysis."""
    entity_name: Optional[str] = None
    analysis_depth: str = "standard"  # basic, standard, deep
    include_cross_entity: bool = True


@router.post("/sync")
async def trigger_bidirectional_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks
):
    """Trigger bidirectional Notion synchronization with AI intelligence."""
    try:
        logger.info(f"Triggering bidirectional sync for {request.entity_name or 'all entities'}")
        
        # Execute synchronization
        sync_result = await intelligence_hub.perform_bidirectional_sync(
            entity_name=request.entity_name
        )
        
        return {
            "success": True,
            "message": f"Bidirectional sync {'completed' if sync_result['success'] else 'failed'}",
            "sync_result": sync_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/status")
async def get_intelligence_hub_status():
    """Get Notion Intelligence Hub status and metrics."""
    try:
        status = await intelligence_hub.get_intelligence_hub_status()
        
        return {
            "success": True,
            "intelligence_hub_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting intelligence hub status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/enrich")
async def trigger_manual_enrichment(
    request: EnrichmentRequest,
    background_tasks: BackgroundTasks
):
    """Manually trigger AI enrichment for a specific contact."""
    try:
        logger.info(f"Triggering manual enrichment for contact {request.contact_id}")
        
        # Execute enrichment
        enrichment_result = await intelligence_hub.trigger_manual_enrichment(
            contact_id=request.contact_id,
            entity_name=request.entity_name
        )
        
        return {
            "success": True,
            "message": f"Manual enrichment {'completed' if enrichment_result['success'] else 'failed'}",
            "enrichment_result": enrichment_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering enrichment: {e}")
        raise HTTPException(status_code=500, detail=f"Enrichment failed: {str(e)}")


@router.post("/analyze-relationships")
async def analyze_contact_relationships(
    request: RelationshipAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Analyze contact relationships and cross-entity opportunities."""
    try:
        logger.info(f"Analyzing contact relationships for {request.entity_name or 'all entities'}")
        
        # Execute relationship analysis
        analysis_result = await intelligence_hub.analyze_contact_relationships(
            entity_name=request.entity_name
        )
        
        return {
            "success": True,
            "message": "Contact relationship analysis completed",
            "analysis_result": analysis_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing relationships: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/metrics")
async def get_sync_metrics():
    """Get synchronization metrics and analytics."""
    try:
        status = await intelligence_hub.get_intelligence_hub_status()
        sync_metrics = status.get("sync_metrics", {})
        
        # Calculate additional metrics
        total_contacts = sync_metrics.get("contacts_synchronized", 0)
        total_enriched = sync_metrics.get("contacts_enriched", 0)
        enrichment_rate = (total_enriched / total_contacts * 100) if total_contacts > 0 else 0
        
        duplicate_detection_rate = (
            sync_metrics.get("duplicates_detected", 0) / total_contacts * 100
        ) if total_contacts > 0 else 0
        
        return {
            "success": True,
            "metrics": {
                "sync_metrics": sync_metrics,
                "calculated_metrics": {
                    "enrichment_rate": round(enrichment_rate, 2),
                    "duplicate_detection_rate": round(duplicate_detection_rate, 2),
                    "sync_success_rate": 100 - (sync_metrics.get("sync_errors", 0) / max(1, total_contacts) * 100)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting sync metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/entities")
async def get_entity_sync_status():
    """Get synchronization status for all entities."""
    try:
        status = await intelligence_hub.get_intelligence_hub_status()
        entity_databases = status.get("entity_databases", {})
        
        entity_status = {}
        for entity_name, database_id in entity_databases.items():
            # Get entity-specific metrics (simulated)
            entity_status[entity_name] = {
                "display_name": entity_name.replace("_", " ").title(),
                "database_id": database_id,
                "sync_enabled": True,
                "last_sync": status.get("sync_metrics", {}).get("last_sync_timestamp"),
                "contact_count": await _get_entity_contact_count(entity_name),
                "enrichment_status": "active"
            }
        
        return {
            "success": True,
            "entity_sync_status": entity_status,
            "total_entities": len(entity_status),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting entity sync status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get entity status: {str(e)}")


async def _get_entity_contact_count(entity_name: str) -> int:
    """Get contact count for an entity (simulated)."""
    # Simulate contact counts based on known data
    contact_counts = {
        "the_7_space": 191,
        "am_consulting": 1300,
        "higherself_core": 1300
    }
    return contact_counts.get(entity_name, 0)


@router.post("/test-enrichment")
async def test_contact_enrichment(
    entity_name: str,
    test_contact_data: Optional[Dict[str, Any]] = None
):
    """Test contact enrichment with sample data."""
    try:
        # Use default test data if none provided
        if test_contact_data is None:
            test_contact_data = {
                "email": f"test.enrichment@{entity_name}.com",
                "first_name": "Test",
                "last_name": "Contact",
                "message": f"Testing enrichment for {entity_name}",
                "interests": ["testing", "enrichment"],
                "source": "api_test"
            }
        
        # Test enrichment
        enriched_contact = await intelligence_hub.enrichment_engine.enrich_contact(
            test_contact_data, entity_name
        )
        
        return {
            "success": True,
            "message": "Contact enrichment test completed",
            "original_contact": test_contact_data,
            "enriched_contact": enriched_contact,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing enrichment: {e}")
        raise HTTPException(status_code=500, detail=f"Enrichment test failed: {str(e)}")


@router.post("/test-duplicate-detection")
async def test_duplicate_detection(
    new_contact: Dict[str, Any],
    existing_contacts: List[Dict[str, Any]]
):
    """Test duplicate detection with sample data."""
    try:
        # Test duplicate detection
        duplicates = await intelligence_hub.duplicate_engine.detect_duplicates(
            new_contact, existing_contacts
        )
        
        return {
            "success": True,
            "message": "Duplicate detection test completed",
            "new_contact": new_contact,
            "existing_contacts_count": len(existing_contacts),
            "duplicates_found": len(duplicates),
            "duplicate_details": duplicates,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing duplicate detection: {e}")
        raise HTTPException(status_code=500, detail=f"Duplicate detection test failed: {str(e)}")


@router.get("/sync-history")
async def get_sync_history(
    entity_name: Optional[str] = Query(None, description="Specific entity to get history for"),
    limit: int = Query(10, description="Number of sync records to return")
):
    """Get synchronization history."""
    try:
        # Simulate sync history (in production, this would come from a database)
        sync_history = []
        
        for i in range(limit):
            sync_record = {
                "sync_id": f"sync_{i+1}",
                "entity": entity_name or "all_entities",
                "timestamp": datetime.now().isoformat(),
                "contacts_processed": 5 + i,
                "contacts_enriched": 4 + i,
                "duplicates_detected": 1 if i % 3 == 0 else 0,
                "success": True,
                "duration_seconds": 15.5 + i
            }
            sync_history.append(sync_record)
        
        return {
            "success": True,
            "sync_history": sync_history,
            "total_records": len(sync_history),
            "entity_filter": entity_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting sync history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync history: {str(e)}")


@router.get("/health")
async def intelligence_hub_health_check():
    """Health check for Notion Intelligence Hub."""
    try:
        # Check system components
        status = await intelligence_hub.get_intelligence_hub_status()
        
        health_status = {
            "status": "healthy",
            "components": {
                "notion_service": notion_service is not None,
                "agent_orchestrator": agent_orchestrator is not None,
                "intelligence_hub": intelligence_hub is not None,
                "enrichment_engine": status.get("engines", {}).get("enrichment_engine") == "active",
                "duplicate_engine": status.get("engines", {}).get("duplicate_engine") == "active"
            },
            "statistics": {
                "total_entities": len(status.get("entity_databases", {})),
                "sync_metrics": status.get("sync_metrics", {}),
                "last_sync": status.get("sync_metrics", {}).get("last_sync_timestamp")
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine overall health
        all_healthy = all(health_status["components"].values())
        health_status["status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Intelligence hub health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
