"""
API endpoints for agent transparency and monitoring
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
import logging

from services.multi_agent_service import get_multi_agent_service, MultiAgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

async def get_multi_agent_service_safe() -> Optional[MultiAgentService]:
    """Get the multi-agent service instance safely"""
    try:
        service = await get_multi_agent_service()
        logger.info(f"Multi-agent service retrieved: initialized={service.is_initialized}, running={service.is_running}, agents={len(service.agents)}")
        
        # Ensure service is properly initialized and running
        if not service.is_initialized:
            logger.info("Service not initialized, initializing now...")
            await service.initialize()
        
        if not service.is_running:
            logger.info("Service not running, starting now...")
            await service.start()
        
        return service
    except Exception as e:
        logger.error(f"Failed to get multi-agent service: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

@router.get("/status")
async def get_agent_status():
    """
    Get current status of all registered agents
    """
    try:
        multi_agent_service = await get_multi_agent_service_safe()
        if not multi_agent_service:
            logger.warning("Multi-agent service not available, returning empty status")
            return {
                "agents": [],
                "summary": {
                    "total": 0,
                    "active": 0,
                    "processing": 0,
                    "idle": 0
                },
                "service_status": {
                    "initialized": False,
                    "running": False,
                    "agents_count": 0,
                    "error": "Multi-agent service not available"
                }
            }
        
        # Get service status
        service_status = multi_agent_service.get_service_status()
        logger.info(f"Service status: {service_status}")
        
        # Transform agent status for frontend
        agents = []
        if multi_agent_service.orchestrator and multi_agent_service.orchestrator.agents:
            logger.info(f"Processing {len(multi_agent_service.orchestrator.agents)} agents")
            for agent_id, agent in multi_agent_service.orchestrator.agents.items():
                try:
                    agent_status = agent.get_status()
                    agents.append({
                        "id": agent_id,
                        "type": agent_status.agent_type.value,
                        "status": _determine_agent_status(agent_status),
                        "currentLoad": agent_status.current_load,
                        "maxLoad": agent_status.max_concurrent_requests,
                        "isActive": agent_status.is_active,
                        "lastHeartbeat": agent_status.last_heartbeat.isoformat(),
                        "capabilities": [cap.dict() for cap in agent_status.capabilities]
                    })
                except Exception as agent_error:
                    logger.error(f"Error processing agent {agent_id}: {str(agent_error)}")
                    # Add a basic entry for the failed agent
                    agents.append({
                        "id": agent_id,
                        "type": getattr(agent, 'agent_type', 'unknown').value if hasattr(getattr(agent, 'agent_type', None), 'value') else 'unknown',
                        "status": "error",
                        "currentLoad": 0,
                        "maxLoad": 0,
                        "isActive": False,
                        "lastHeartbeat": "1970-01-01T00:00:00",
                        "capabilities": [],
                        "error": str(agent_error)
                    })
        else:
            logger.warning("No orchestrator or agents found")
        
        result = {
            "agents": agents,
            "summary": {
                "total": len(agents),
                "active": len([a for a in agents if a["status"] not in ["offline", "error"]]),
                "processing": len([a for a in agents if a["status"] == "processing"]),
                "idle": len([a for a in agents if a["status"] == "idle"])
            },
            "service_status": service_status
        }
        
        logger.info(f"Returning agent status: {len(agents)} agents")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return a safe fallback response instead of raising an exception
        return {
            "agents": [],
            "summary": {
                "total": 0,
                "active": 0,
                "processing": 0,
                "idle": 0
            },
            "service_status": {
                "initialized": False,
                "running": False,
                "agents_count": 0,
                "error": str(e)
            }
        }

@router.get("/workflows")
async def get_active_workflows():
    """
    Get information about active workflows
    """
    try:
        multi_agent_service = await get_multi_agent_service_safe()
        if not multi_agent_service or not multi_agent_service.orchestrator:
            return {
                "workflows": [],
                "recentWorkflows": [],
                "summary": {
                    "active": 0,
                    "totalCompleted": 0
                }
            }
        
        orchestrator = multi_agent_service.orchestrator
        
        # Get active workflows
        active_workflows = []
        for workflow_id, workflow in orchestrator.active_workflows.items():
            workflow_data = {
                "id": workflow_id,
                "requestType": workflow.metadata.get("request_type", "unknown"),
                "participatingAgents": workflow.participating_agents,
                "status": workflow.status.value,
                "createdAt": workflow.created_at.isoformat(),
                "steps": []
            }
            
            # Add step information
            for step_dict in workflow.workflow_steps:
                step_data = {
                    "stepId": step_dict.get("step_id", "unknown"),
                    "agentId": step_dict.get("agent_id", "unknown"),
                    "agentType": step_dict.get("agent_type", "unknown"),
                    "stepName": step_dict.get("step_name", "Unknown Step"),
                    "status": step_dict.get("status", "pending"),
                    "startedAt": step_dict.get("started_at"),
                    "completedAt": step_dict.get("completed_at")
                }
                workflow_data["steps"].append(step_data)
            
            active_workflows.append(workflow_data)
        
        # Get recent completed workflows (last 5)
        recent_workflows = []
        for workflow in orchestrator.workflow_history[-5:]:
            workflow_data = {
                "id": workflow.id,
                "requestType": workflow.metadata.get("request_type", "unknown"),
                "participatingAgents": workflow.participating_agents,
                "status": workflow.status.value,
                "createdAt": workflow.created_at.isoformat(),
                "completedAt": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "stepCount": len(workflow.workflow_steps)
            }
            recent_workflows.append(workflow_data)
        
        return {
            "workflows": active_workflows,
            "recentWorkflows": recent_workflows,
            "summary": {
                "active": len(active_workflows),
                "totalCompleted": len(orchestrator.workflow_history)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflows: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow information")

@router.get("/metrics")
async def get_agent_metrics():
    """
    Get performance metrics for agents and the system
    """
    try:
        multi_agent_service = await get_multi_agent_service_safe()
        if not multi_agent_service:
            return {
                "system": {
                    "registeredAgents": 0,
                    "activeWorkflows": 0,
                    "totalMessages": 0,
                    "systemLoad": 0
                },
                "agents": {},
                "orchestrator": {}
            }
        
        # Get service status
        service_status = multi_agent_service.get_service_status()
        
        # System-level metrics
        system_metrics = {
            "registeredAgents": len(multi_agent_service.agents),
            "activeWorkflows": 0,
            "totalMessages": 0,
            "systemLoad": 0
        }
        
        # Agent-level metrics
        agent_metrics = {}
        
        if multi_agent_service.orchestrator:
            orchestrator = multi_agent_service.orchestrator
            status = orchestrator.get_status()
            
            system_metrics.update({
                "registeredAgents": status["registered_agents"],
                "activeWorkflows": status["active_workflows"],
                "totalMessages": status["communication_stats"]["total_messages"],
                "systemLoad": _calculate_system_load(orchestrator)
            })
            
            # Agent-level metrics
            for agent_id, agent in orchestrator.agents.items():
                agent_status = agent.get_status()
                metrics = agent_status.performance_metrics
                
                agent_metrics[agent_status.agent_type.value] = {
                    "totalRequests": metrics.get("total_requests", 0),
                    "successfulRequests": metrics.get("successful_requests", 0),
                    "failedRequests": metrics.get("failed_requests", 0),
                    "averageProcessingTime": metrics.get("average_processing_time", 0.0),
                    "averageConfidence": metrics.get("average_confidence", 0.0),
                    "lastRequestTime": metrics.get("last_request_time")
                }
        
        return {
            "system": system_metrics,
            "agents": agent_metrics,
            "orchestrator": service_status.get("orchestrator", {}),
            "service_status": service_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent metrics")

@router.get("/communication/history")
async def get_communication_history(
    agent_id: Optional[str] = None,
    message_type: Optional[str] = None,
    limit: int = 50
):
    """
    Get inter-agent communication history
    """
    try:
        multi_agent_service = await get_multi_agent_service_safe()
        if not multi_agent_service or not multi_agent_service.orchestrator:
            return {
                "messages": [],
                "statistics": {}
            }
        
        orchestrator = multi_agent_service.orchestrator
        
        # Get message history from communication bus
        messages = orchestrator.communication_bus.get_message_history(
            agent_id=agent_id,
            message_type=message_type,
            limit=limit
        )
        
        # Transform messages for frontend
        message_data = []
        for msg in messages:
            message_data.append({
                "id": msg.id,
                "senderId": msg.sender_agent_id,
                "recipientId": msg.recipient_agent_id,
                "messageType": msg.message_type.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "acknowledged": msg.acknowledged
            })
        
        return {
            "messages": message_data,
            "statistics": orchestrator.communication_bus.get_statistics()
        }
        
    except Exception as e:
        logger.error(f"Failed to get communication history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve communication history")

@router.get("/logs")
async def get_agent_logs(
    limit: int = 100,
    agent_id: Optional[str] = None,
    activity_type: Optional[str] = None,
    level: Optional[str] = None
):
    """
    Get agent activity logs
    """
    try:
        from services.agent_logger import agent_logger, ActivityType, LogLevel
        
        # Convert string parameters to enums if provided
        activity_type_enum = None
        if activity_type:
            try:
                activity_type_enum = ActivityType(activity_type)
            except ValueError:
                pass
        
        level_enum = None
        if level:
            try:
                level_enum = LogLevel(level)
            except ValueError:
                pass
        
        # Get logs
        logs = agent_logger.get_recent_activities(
            limit=limit,
            agent_id=agent_id,
            activity_type=activity_type_enum,
            level=level_enum
        )
        
        # Get statistics
        stats = agent_logger.get_activity_statistics()
        
        return {
            "logs": logs,
            "statistics": stats,
            "filters": {
                "agent_id": agent_id,
                "activity_type": activity_type,
                "level": level,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent logs")

@router.post("/debug/toggle-visibility")
async def toggle_debug_visibility(component: str, visible: bool):
    """
    Toggle visibility of debug components (development only)
    """
    # This endpoint would typically be protected or only available in development
    # For now, it just returns success as the frontend handles visibility locally
    return {
        "component": component,
        "visible": visible,
        "message": f"Debug visibility for {component} set to {visible}"
    }

@router.post("/initialize")
async def initialize_agents():
    """
    Manually initialize the multi-agent service (for debugging)
    """
    try:
        from services.multi_agent_service import get_multi_agent_service
        multi_agent_service = await get_multi_agent_service()
        
        return {
            "success": True,
            "initialized": multi_agent_service.is_initialized,
            "running": multi_agent_service.is_running,
            "agents_count": len(multi_agent_service.agents),
            "orchestrator_agents": len(multi_agent_service.orchestrator.agents) if multi_agent_service.orchestrator else 0
        }
    except Exception as e:
        logger.error(f"Failed to initialize agents: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/health")
async def agents_health_check():
    """
    Health check for the agents system
    """
    try:
        multi_agent_service = await get_multi_agent_service_safe()
        
        if not multi_agent_service:
            return {
                "status": "unhealthy",
                "message": "Multi-agent service not available"
            }
        
        health = await multi_agent_service.health_check()
        
        return {
            "status": "healthy" if multi_agent_service.is_running else "unhealthy",
            "details": health
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/test")
async def test_endpoint():
    """
    Simple test endpoint to verify the API is working
    """
    return {
        "status": "ok",
        "message": "Agents API is working",
        "timestamp": "2025-08-17T20:15:00Z"
    }

def _determine_agent_status(agent_status) -> str:
    """
    Determine the display status of an agent based on its current state
    """
    if not agent_status.is_active:
        return "offline"
    elif agent_status.current_load > 0:
        return "processing"
    elif agent_status.current_load == 0:
        return "idle"
    else:
        return "active"

def _calculate_system_load(orchestrator) -> float:
    """
    Calculate overall system load as a percentage
    """
    if not orchestrator or not orchestrator.agents:
        return 0.0
    
    total_load = sum(agent.current_load for agent in orchestrator.agents.values())
    total_capacity = sum(agent.max_concurrent_requests for agent in orchestrator.agents.values())
    
    if total_capacity == 0:
        return 0.0
    
    return (total_load / total_capacity) * 100