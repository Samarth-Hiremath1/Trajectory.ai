"""
Agent Performance Monitoring and Optimization API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
import logging

from services.agent_orchestrator_service import AgentOrchestratorService
from services.ai_service import AIService
from services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents/performance", tags=["agent-performance"])

# Global service instances (these would be properly injected in a real app)
orchestrator_service = None
ai_service = None
db_service = None

def get_orchestrator_service():
    """Get orchestrator service instance"""
    global orchestrator_service
    if orchestrator_service is None:
        # Initialize services (this would be done in app startup)
        global ai_service, db_service
        if ai_service is None:
            ai_service = AIService()
        if db_service is None:
            db_service = DatabaseService()
        orchestrator_service = AgentOrchestratorService(ai_service)
    return orchestrator_service

@router.get("/status")
async def get_performance_status(
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Get overall system performance status
    """
    try:
        return orchestrator.get_performance_metrics()
    except Exception as e:
        logger.error(f"Failed to get performance status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-summary")
async def get_system_performance_summary(
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Get system-wide performance summary
    """
    try:
        return orchestrator.performance_monitor.get_system_performance_summary()
    except Exception as e:
        logger.error(f"Failed to get system performance summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/profile")
async def get_agent_performance_profile(
    agent_id: str,
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Get detailed performance profile for a specific agent
    """
    try:
        profile = orchestrator.performance_monitor.get_agent_performance_profile(agent_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Agent performance profile not found")
        
        return {
            "agent_id": profile.agent_id,
            "agent_type": profile.agent_type.value,
            "performance_metrics": {
                "avg_response_time": profile.avg_response_time,
                "success_rate": profile.success_rate,
                "avg_confidence": profile.avg_confidence,
                "throughput": profile.throughput
            },
            "quality_metrics": {
                "avg_quality_score": profile.avg_quality_score,
                "consistency_score": profile.consistency_score,
                "reliability_score": profile.reliability_score
            },
            "load_metrics": {
                "current_load": profile.current_load,
                "peak_load": profile.peak_load,
                "load_efficiency": profile.load_efficiency
            },
            "performance_trend": profile.performance_trend,
            "last_updated": profile.last_updated.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent performance profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/load-balancing")
async def get_load_balancing_status(
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Get load balancing status and metrics
    """
    try:
        return orchestrator.load_balancer.get_load_balancing_status()
    except Exception as e:
        logger.error(f"Failed to get load balancing status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/load-balancing/rebalance")
async def trigger_load_rebalancing(
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Trigger load rebalancing across agents
    """
    try:
        await orchestrator.load_balancer.rebalance_load()
        return {
            "message": "Load rebalancing completed",
            "status": orchestrator.load_balancer.get_load_balancing_status()
        }
    except Exception as e:
        logger.error(f"Failed to trigger load rebalancing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning")
async def get_learning_metrics(
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Get learning system metrics and status
    """
    try:
        return orchestrator.learning_system.get_learning_metrics()
    except Exception as e:
        logger.error(f"Failed to get learning metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/improvements")
async def get_agent_improvement_suggestions(
    agent_id: str,
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Get improvement suggestions for a specific agent
    """
    try:
        suggestions = await orchestrator.learning_system.generate_improvement_suggestions(agent_id)
        
        return {
            "agent_id": agent_id,
            "suggestions_count": len(suggestions),
            "suggestions": [
                {
                    "suggestion_type": s.suggestion_type,
                    "description": s.description,
                    "expected_improvement": s.expected_improvement,
                    "confidence": s.confidence,
                    "priority": s.implementation_priority,
                    "created_at": s.created_at.isoformat()
                }
                for s in suggestions
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get improvement suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_id}/improvements/apply")
async def apply_agent_improvements(
    agent_id: str,
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Apply pending improvements for a specific agent
    """
    try:
        result = await orchestrator.apply_agent_improvements(agent_id)
        return result
    except Exception as e:
        logger.error(f"Failed to apply agent improvements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conflicts")
async def get_conflict_status(
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Get conflict resolution status and metrics
    """
    try:
        return orchestrator.conflict_resolver.get_conflict_status()
    except Exception as e:
        logger.error(f"Failed to get conflict status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_performance_alerts(
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Get current performance alerts
    """
    try:
        alerts = orchestrator.performance_monitor.get_performance_alerts()
        return {
            "alerts_count": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Failed to get performance alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/alerts")
async def clear_performance_alerts(
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Clear all performance alerts
    """
    try:
        orchestrator.performance_monitor.clear_performance_alerts()
        return {"message": "Performance alerts cleared"}
    except Exception as e:
        logger.error(f"Failed to clear performance alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def optimize_system_performance(
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Trigger comprehensive system performance optimization
    """
    try:
        result = await orchestrator.optimize_system_performance()
        return {
            "message": "System optimization completed",
            "results": result
        }
    except Exception as e:
        logger.error(f"Failed to optimize system performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/knowledge")
async def get_agent_knowledge(
    agent_id: str,
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Get accumulated knowledge for a specific agent
    """
    try:
        knowledge = orchestrator.learning_system.get_agent_knowledge(agent_id)
        return {
            "agent_id": agent_id,
            "knowledge": knowledge
        }
    except Exception as e:
        logger.error(f"Failed to get agent knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/agents/{agent_id}/knowledge")
async def update_agent_knowledge(
    agent_id: str,
    knowledge_update: Dict[str, Any],
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Update knowledge base for a specific agent
    """
    try:
        orchestrator.learning_system.update_agent_knowledge(agent_id, knowledge_update)
        return {
            "message": f"Knowledge updated for agent {agent_id}",
            "agent_id": agent_id
        }
    except Exception as e:
        logger.error(f"Failed to update agent knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/export")
async def export_performance_metrics(
    orchestrator: AgentOrchestratorService = Depends(get_orchestrator_service)
) -> Dict[str, Any]:
    """
    Export comprehensive performance metrics for analysis
    """
    try:
        return {
            "export_timestamp": orchestrator.performance_monitor.get_system_performance_summary()["timestamp"],
            "system_performance": orchestrator.performance_monitor.get_system_performance_summary(),
            "load_balancing": orchestrator.load_balancer.get_load_balancing_status(),
            "learning_metrics": orchestrator.learning_system.get_learning_metrics(),
            "conflict_resolution": orchestrator.conflict_resolver.get_conflict_status(),
            "orchestrator_status": orchestrator.get_status()
        }
    except Exception as e:
        logger.error(f"Failed to export performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))