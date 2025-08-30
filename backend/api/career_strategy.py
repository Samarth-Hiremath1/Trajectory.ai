"""
Career Strategy API endpoints for multi-agent system integration
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from services.multi_agent_service import get_multi_agent_service
from models.agent import RequestType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/career-strategy", tags=["career-strategy"])

class CareerTransitionRequest(BaseModel):
    """Request model for career transition analysis"""
    user_id: str
    current_role: str
    target_role: str
    timeline: Optional[str] = "12 months"
    constraints: Optional[Dict[str, Any]] = None

class StrategicRoadmapRequest(BaseModel):
    """Request model for strategic roadmap generation"""
    user_id: str
    current_role: str
    target_role: str
    constraints: Optional[Dict[str, Any]] = None

class StrategicAdviceRequest(BaseModel):
    """Request model for strategic career advice"""
    user_id: str
    question: str

class CareerStrategyResponse(BaseModel):
    """Response model for career strategy operations"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    workflow_id: Optional[str] = None
    agents_used: Optional[List[str]] = None
    processing_time: Optional[float] = None

@router.post("/transition-analysis", response_model=CareerStrategyResponse)
async def analyze_career_transition(request: CareerTransitionRequest):
    """
    Analyze a career transition and provide strategic recommendations
    
    Args:
        request: Career transition analysis request
        
    Returns:
        Career transition analysis with strategic recommendations
    """
    try:
        logger.info(f"Processing career transition analysis for user {request.user_id}")
        
        # Get multi-agent service
        service = await get_multi_agent_service()
        
        # Process career transition analysis
        result = await service.get_career_strategy_analysis(
            user_id=request.user_id,
            current_role=request.current_role,
            target_role=request.target_role,
            timeline=request.timeline
        )
        
        if result["success"]:
            return CareerStrategyResponse(
                success=True,
                data=result.get("final_response", {}),
                workflow_id=result.get("workflow_id"),
                agents_used=[r.get("agent_type") for r in result.get("responses", [])],
                processing_time=result.get("execution_time")
            )
        else:
            return CareerStrategyResponse(
                success=False,
                error=result.get("error", "Unknown error occurred")
            )
            
    except Exception as e:
        logger.error(f"Career transition analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategic-roadmap", response_model=CareerStrategyResponse)
async def generate_strategic_roadmap(request: StrategicRoadmapRequest):
    """
    Generate a strategic career roadmap
    
    Args:
        request: Strategic roadmap generation request
        
    Returns:
        Strategic career roadmap with phases and milestones
    """
    try:
        logger.info(f"Generating strategic roadmap for user {request.user_id}")
        
        # Get multi-agent service
        service = await get_multi_agent_service()
        
        # Generate strategic roadmap
        result = await service.generate_strategic_roadmap(
            user_id=request.user_id,
            current_role=request.current_role,
            target_role=request.target_role,
            constraints=request.constraints
        )
        
        if result["success"]:
            return CareerStrategyResponse(
                success=True,
                data=result.get("final_response", {}),
                workflow_id=result.get("workflow_id"),
                agents_used=[r.get("agent_type") for r in result.get("responses", [])],
                processing_time=result.get("execution_time")
            )
        else:
            return CareerStrategyResponse(
                success=False,
                error=result.get("error", "Unknown error occurred")
            )
            
    except Exception as e:
        logger.error(f"Strategic roadmap generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategic-advice", response_model=CareerStrategyResponse)
async def get_strategic_advice(request: StrategicAdviceRequest):
    """
    Get strategic career advice
    
    Args:
        request: Strategic advice request
        
    Returns:
        Strategic career advice and recommendations
    """
    try:
        logger.info(f"Providing strategic advice for user {request.user_id}")
        
        # Get multi-agent service
        service = await get_multi_agent_service()
        
        # Get strategic career advice
        result = await service.get_strategic_career_advice(
            user_id=request.user_id,
            question=request.question
        )
        
        if result["success"]:
            return CareerStrategyResponse(
                success=True,
                data=result.get("final_response", {}),
                workflow_id=result.get("workflow_id"),
                agents_used=[r.get("agent_type") for r in result.get("responses", [])],
                processing_time=result.get("execution_time")
            )
        else:
            return CareerStrategyResponse(
                success=False,
                error=result.get("error", "Unknown error occurred")
            )
            
    except Exception as e:
        logger.error(f"Strategic advice failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-status")
async def get_agent_status():
    """
    Get status of the Career Strategy Agent and multi-agent system
    
    Returns:
        Status information for all agents and the orchestrator
    """
    try:
        # Get multi-agent service
        service = await get_multi_agent_service()
        
        # Get service status
        status = service.get_service_status()
        
        return {
            "success": True,
            "status": status,
            "health": await service.health_check()
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-agents")
async def get_available_agents():
    """
    Get list of available agents and their capabilities
    
    Returns:
        List of available agents with their capabilities
    """
    try:
        # Get multi-agent service
        service = await get_multi_agent_service()
        
        # Get available agents
        agents = service.get_available_agents()
        
        return {
            "success": True,
            "agents": agents
        }
        
    except Exception as e:
        logger.error(f"Failed to get available agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/health-check")
async def health_check():
    """
    Perform health check on the multi-agent system
    
    Returns:
        Health status of all services and agents
    """
    try:
        # Get multi-agent service
        service = await get_multi_agent_service()
        
        # Perform health check
        health = await service.health_check()
        
        return {
            "success": True,
            "health": health
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Example usage endpoints for testing
@router.post("/test/career-transition")
async def test_career_transition():
    """Test endpoint for career transition analysis"""
    test_request = CareerTransitionRequest(
        user_id="test_user_api",
        current_role="Software Engineer",
        target_role="Product Manager",
        timeline="18 months"
    )
    
    return await analyze_career_transition(test_request)

@router.post("/test/strategic-roadmap")
async def test_strategic_roadmap():
    """Test endpoint for strategic roadmap generation"""
    test_request = StrategicRoadmapRequest(
        user_id="test_user_api",
        current_role="Software Engineer",
        target_role="Product Manager",
        constraints={
            "timeline": "18 months",
            "budget": "moderate",
            "availability": "part-time learning"
        }
    )
    
    return await generate_strategic_roadmap(test_request)

@router.post("/test/strategic-advice")
async def test_strategic_advice():
    """Test endpoint for strategic career advice"""
    test_request = StrategicAdviceRequest(
        user_id="test_user_api",
        question="What are the most important strategic considerations for transitioning from engineering to product management in the current market?"
    )
    
    return await get_strategic_advice(test_request)