#!/usr/bin/env python3
"""
Multi-Entity Workflow API Endpoints

API endpoints for managing and monitoring multi-entity workflows across
The 7 Space, AM Consulting, and HigherSelf Core business entities.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from services.multi_entity_workflow_automation import MultiEntityWorkflowAutomation
from services.notion_service import NotionService


# Initialize services
notion_service = NotionService()
multi_entity_automation = MultiEntityWorkflowAutomation(notion_service)

router = APIRouter(prefix="/multi-entity-workflows", tags=["Multi-Entity Workflows"])


class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution."""
    entity_name: str
    template_name: str
    contact_data: Dict[str, Any]
    trigger_context: Optional[Dict[str, Any]] = None


class BulkWorkflowRequest(BaseModel):
    """Request model for bulk workflow execution."""
    workflows: List[WorkflowExecutionRequest]
    execution_mode: str = "parallel"  # parallel or sequential


@router.post("/execute")
async def execute_entity_workflow(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks
):
    """Execute a specific entity workflow."""
    try:
        logger.info(f"Executing {request.entity_name} workflow: {request.template_name}")
        
        # Execute workflow
        result = await multi_entity_automation.execute_entity_workflow(
            entity_name=request.entity_name,
            template_name=request.template_name,
            contact_data=request.contact_data,
            trigger_context=request.trigger_context
        )
        
        return {
            "success": True,
            "message": f"Workflow {request.template_name} executed for {request.entity_name}",
            "execution_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.post("/execute-bulk")
async def execute_bulk_workflows(
    request: BulkWorkflowRequest,
    background_tasks: BackgroundTasks
):
    """Execute multiple workflows in bulk."""
    try:
        logger.info(f"Executing {len(request.workflows)} workflows in {request.execution_mode} mode")
        
        results = []
        
        if request.execution_mode == "parallel":
            # Execute workflows in parallel
            import asyncio
            tasks = [
                multi_entity_automation.execute_entity_workflow(
                    entity_name=workflow.entity_name,
                    template_name=workflow.template_name,
                    contact_data=workflow.contact_data,
                    trigger_context=workflow.trigger_context
                )
                for workflow in request.workflows
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        else:  # sequential
            # Execute workflows sequentially
            for workflow in request.workflows:
                result = await multi_entity_automation.execute_entity_workflow(
                    entity_name=workflow.entity_name,
                    template_name=workflow.template_name,
                    contact_data=workflow.contact_data,
                    trigger_context=workflow.trigger_context
                )
                results.append(result)
        
        successful_executions = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        
        return {
            "success": True,
            "message": f"Bulk workflow execution completed",
            "total_workflows": len(request.workflows),
            "successful_executions": successful_executions,
            "execution_mode": request.execution_mode,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing bulk workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk workflow execution failed: {str(e)}")


@router.get("/status")
async def get_workflow_status(
    entity_name: Optional[str] = Query(None, description="Specific entity to check")
):
    """Get workflow status for entities."""
    try:
        status = await multi_entity_automation.get_entity_workflow_status(entity_name)
        
        return {
            "success": True,
            "workflow_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")


@router.get("/templates")
async def get_workflow_templates(
    entity_name: Optional[str] = Query(None, description="Specific entity to get templates for")
):
    """Get available workflow templates."""
    try:
        if entity_name:
            templates = multi_entity_automation.entity_templates.get(entity_name, {})
            template_info = {
                name: {
                    "entity": template.entity_name,
                    "actions_count": len(template.actions),
                    "created_at": template.created_at.isoformat()
                }
                for name, template in templates.items()
            }
        else:
            template_info = {}
            for entity, templates in multi_entity_automation.entity_templates.items():
                template_info[entity] = {
                    name: {
                        "entity": template.entity_name,
                        "actions_count": len(template.actions),
                        "created_at": template.created_at.isoformat()
                    }
                    for name, template in templates.items()
                }
        
        return {
            "success": True,
            "templates": template_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.get("/metrics")
async def get_workflow_metrics():
    """Get workflow execution metrics across all entities."""
    try:
        metrics = multi_entity_automation.workflow_metrics
        
        # Calculate aggregate metrics
        total_executed = sum(entity_metrics["executed"] for entity_metrics in metrics.values())
        total_successful = sum(entity_metrics["successful"] for entity_metrics in metrics.values())
        overall_success_rate = (total_successful / total_executed * 100) if total_executed > 0 else 0
        
        return {
            "success": True,
            "metrics": {
                "entity_metrics": metrics,
                "aggregate_metrics": {
                    "total_workflows_executed": total_executed,
                    "total_successful_workflows": total_successful,
                    "overall_success_rate": round(overall_success_rate, 2),
                    "active_workflows": len(multi_entity_automation.active_workflows)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/optimize-workflow")
async def optimize_workflow_selection(
    contact_data: Dict[str, Any],
    entity_name: str,
    analysis_result: Optional[Dict[str, Any]] = None
):
    """Get optimal workflow recommendation for a contact."""
    try:
        if analysis_result is None:
            analysis_result = {}
        
        optimal_workflow = await multi_entity_automation.identify_optimal_workflow(
            contact_data=contact_data,
            entity_name=entity_name,
            analysis_result=analysis_result
        )
        
        return {
            "success": True,
            "recommended_workflow": optimal_workflow,
            "entity": entity_name,
            "contact_email": contact_data.get("email"),
            "reasoning": f"Selected based on contact data analysis for {entity_name}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error optimizing workflow selection: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow optimization failed: {str(e)}")


@router.get("/entities")
async def get_supported_entities():
    """Get list of supported business entities."""
    try:
        entities = list(multi_entity_automation.entity_templates.keys())
        
        entity_info = {}
        for entity in entities:
            templates = multi_entity_automation.entity_templates[entity]
            metrics = multi_entity_automation.workflow_metrics.get(entity, {})
            
            entity_info[entity] = {
                "display_name": entity.replace("_", " ").title(),
                "template_count": len(templates),
                "workflows_executed": metrics.get("executed", 0),
                "success_rate": (
                    round(metrics.get("successful", 0) / metrics.get("executed", 1) * 100, 2)
                    if metrics.get("executed", 0) > 0 else 0
                ),
                "avg_completion_time": round(metrics.get("avg_completion_time", 0), 2)
            }
        
        return {
            "success": True,
            "supported_entities": entity_info,
            "total_entities": len(entities),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting supported entities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get entities: {str(e)}")


@router.post("/test-workflow")
async def test_workflow_execution(
    entity_name: str,
    template_name: str,
    test_contact_data: Optional[Dict[str, Any]] = None
):
    """Test workflow execution with sample data."""
    try:
        # Use default test data if none provided
        if test_contact_data is None:
            test_contact_data = {
                "email": f"test@{entity_name}.com",
                "first_name": "Test",
                "last_name": "Contact",
                "message": f"Testing {template_name} workflow for {entity_name}",
                "interests": ["testing"],
                "source": "api_test"
            }
        
        # Execute test workflow
        result = await multi_entity_automation.execute_entity_workflow(
            entity_name=entity_name,
            template_name=template_name,
            contact_data=test_contact_data,
            trigger_context={"test_mode": True}
        )
        
        return {
            "success": True,
            "message": f"Test workflow executed successfully",
            "test_data": test_contact_data,
            "execution_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow test failed: {str(e)}")


@router.get("/health")
async def workflow_health_check():
    """Health check for multi-entity workflow system."""
    try:
        # Check system components
        health_status = {
            "status": "healthy",
            "components": {
                "notion_service": notion_service is not None,
                "multi_entity_automation": multi_entity_automation is not None,
                "entity_templates_loaded": len(multi_entity_automation.entity_templates) > 0,
                "workflow_metrics_tracking": len(multi_entity_automation.workflow_metrics) > 0
            },
            "statistics": {
                "total_entities": len(multi_entity_automation.entity_templates),
                "total_templates": sum(
                    len(templates) for templates in multi_entity_automation.entity_templates.values()
                ),
                "active_workflows": len(multi_entity_automation.active_workflows)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine overall health
        all_healthy = all(health_status["components"].values())
        health_status["status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
