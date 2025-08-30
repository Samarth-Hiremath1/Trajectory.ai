"""
LangGraph Workflows API endpoints
"""
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from services.multi_agent_service import get_multi_agent_service, MultiAgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["langgraph-workflows"])

# Request/Response Models
class CareerTransitionWorkflowRequest(BaseModel):
    """Request model for career transition workflow"""
    user_id: str
    current_role: str
    target_role: str
    timeline: str = Field(default="12 months", description="Desired timeline for transition")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="Optional constraints and preferences")

class RoadmapEnhancementWorkflowRequest(BaseModel):
    """Request model for roadmap enhancement workflow"""
    user_id: str
    existing_roadmap: Dict[str, Any] = Field(description="Existing roadmap to enhance")
    enhancement_goals: List[str] = Field(description="Goals for roadmap enhancement")

class ComprehensiveAnalysisWorkflowRequest(BaseModel):
    """Request model for comprehensive analysis workflow"""
    user_id: str
    analysis_request: Dict[str, Any] = Field(description="Analysis request details")

class WorkflowResponse(BaseModel):
    """Response model for workflow execution"""
    success: bool
    workflow_id: Optional[str] = None
    final_response: Optional[Dict[str, Any]] = None
    steps_completed: List[str] = Field(default_factory=list)
    error_messages: List[str] = Field(default_factory=list)
    error: Optional[str] = None

class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status"""
    workflow_id: str
    status: str
    current_step: Optional[str] = None
    steps_completed: List[str] = Field(default_factory=list)
    error: Optional[str] = None

@router.post("/career-transition", response_model=WorkflowResponse)
async def execute_career_transition_workflow(
    request: CareerTransitionWorkflowRequest,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service)
) -> WorkflowResponse:
    """
    Execute comprehensive career transition workflow using LangGraph
    
    This workflow coordinates multiple AI agents:
    1. Career Strategy Agent - Analyzes transition feasibility and strategy
    2. Skills Analysis Agent - Identifies skill gaps and development priorities
    3. Learning Resource Agent - Curates personalized learning resources
    
    The workflow uses Redis checkpointing for state persistence and recovery.
    
    Args:
        request: Career transition workflow request
        multi_agent_service: Multi-agent service instance
        
    Returns:
        Comprehensive career transition analysis from coordinated agents
    """
    try:
        logger.info(f"Executing career transition workflow for user {request.user_id}: {request.current_role} → {request.target_role}")
        
        # Execute LangGraph workflow
        result = await multi_agent_service.execute_career_transition_workflow(
            user_id=request.user_id,
            current_role=request.current_role,
            target_role=request.target_role,
            timeline=request.timeline,
            constraints=request.constraints
        )
        
        return WorkflowResponse(
            success=result.get("success", False),
            workflow_id=result.get("workflow_id"),
            final_response=result.get("final_response"),
            steps_completed=result.get("steps_completed", []),
            error_messages=result.get("error_messages", []),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Career transition workflow failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.post("/roadmap-enhancement", response_model=WorkflowResponse)
async def execute_roadmap_enhancement_workflow(
    request: RoadmapEnhancementWorkflowRequest,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service)
) -> WorkflowResponse:
    """
    Execute roadmap enhancement workflow using LangGraph
    
    This workflow systematically improves existing roadmaps by:
    1. Analyzing current roadmap for improvement opportunities
    2. Enhancing strategy using Career Strategy Agent
    3. Updating skills assessment using Skills Analysis Agent
    4. Refreshing learning resources using Learning Resource Agent
    
    Args:
        request: Roadmap enhancement workflow request
        multi_agent_service: Multi-agent service instance
        
    Returns:
        Enhanced roadmap with improved recommendations
    """
    try:
        logger.info(f"Executing roadmap enhancement workflow for user {request.user_id}")
        
        # Execute LangGraph workflow
        result = await multi_agent_service.execute_roadmap_enhancement_workflow(
            user_id=request.user_id,
            existing_roadmap=request.existing_roadmap,
            enhancement_goals=request.enhancement_goals
        )
        
        return WorkflowResponse(
            success=result.get("success", False),
            workflow_id=result.get("workflow_id"),
            final_response=result.get("final_response"),
            steps_completed=result.get("steps_completed", []),
            error_messages=result.get("error_messages", []),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Roadmap enhancement workflow failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.post("/comprehensive-analysis", response_model=WorkflowResponse)
async def execute_comprehensive_analysis_workflow(
    request: ComprehensiveAnalysisWorkflowRequest,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service)
) -> WorkflowResponse:
    """
    Execute comprehensive analysis workflow using LangGraph
    
    This workflow runs multiple agents in parallel and cross-validates results:
    1. Parallel execution of all available agents
    2. Cross-validation of agent outputs
    3. Synthesis of comprehensive response
    
    Args:
        request: Comprehensive analysis workflow request
        multi_agent_service: Multi-agent service instance
        
    Returns:
        Comprehensive analysis from all coordinated agents
    """
    try:
        logger.info(f"Executing comprehensive analysis workflow for user {request.user_id}")
        
        # Execute LangGraph workflow
        result = await multi_agent_service.execute_comprehensive_analysis_workflow(
            user_id=request.user_id,
            analysis_request=request.analysis_request
        )
        
        return WorkflowResponse(
            success=result.get("success", False),
            workflow_id=result.get("workflow_id"),
            final_response=result.get("final_response"),
            steps_completed=result.get("steps_completed", []),
            error_messages=result.get("error_messages", []),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Comprehensive analysis workflow failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service)
) -> WorkflowStatusResponse:
    """
    Get status of a running LangGraph workflow
    
    Args:
        workflow_id: Workflow identifier
        multi_agent_service: Multi-agent service instance
        
    Returns:
        Current workflow status and progress
    """
    try:
        logger.info(f"Getting status for workflow {workflow_id}")
        
        status = await multi_agent_service.get_workflow_status(workflow_id)
        
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status=status.get("status", "unknown"),
            current_step=status.get("current_step"),
            steps_completed=status.get("steps_completed", []),
            error=status.get("error")
        )
        
    except Exception as e:
        logger.error(f"Failed to get workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@router.post("/resume/{workflow_id}")
async def resume_workflow(
    workflow_id: str,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service)
) -> Dict[str, Any]:
    """
    Resume a workflow from Redis checkpoint
    
    Args:
        workflow_id: Workflow identifier
        multi_agent_service: Multi-agent service instance
        
    Returns:
        Workflow resumption results
    """
    try:
        logger.info(f"Resuming workflow {workflow_id}")
        
        result = await multi_agent_service.resume_workflow(workflow_id)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "resumed": result.get("resumed", False),
            "message": result.get("message", "Workflow resumed"),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Failed to resume workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")

@router.get("/available")
async def get_available_workflows(
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service)
) -> Dict[str, Any]:
    """
    Get list of available LangGraph workflows
    
    Args:
        multi_agent_service: Multi-agent service instance
        
    Returns:
        List of available workflow names and descriptions
    """
    try:
        workflows = multi_agent_service.get_available_workflows()
        
        workflow_descriptions = {
            "career_transition": {
                "name": "Career Transition Workflow",
                "description": "Comprehensive career transition analysis using multiple coordinated agents",
                "agents_involved": ["Career Strategy", "Skills Analysis", "Learning Resources"],
                "features": ["Sequential agent coordination", "State persistence", "Error recovery"]
            },
            "roadmap_enhancement": {
                "name": "Roadmap Enhancement Workflow", 
                "description": "Systematic improvement of existing career roadmaps",
                "agents_involved": ["Career Strategy", "Skills Analysis", "Learning Resources"],
                "features": ["Roadmap analysis", "Strategic enhancement", "Resource refresh"]
            },
            "comprehensive_analysis": {
                "name": "Comprehensive Analysis Workflow",
                "description": "Parallel execution and cross-validation of all agents",
                "agents_involved": ["All available agents"],
                "features": ["Parallel execution", "Cross-validation", "Comprehensive synthesis"]
            }
        }
        
        return {
            "success": True,
            "available_workflows": workflows,
            "workflow_details": {name: workflow_descriptions.get(name, {}) for name in workflows},
            "total_workflows": len(workflows)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get available workflows: {str(e)}")

@router.get("/health")
async def workflow_health_check(
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service)
) -> Dict[str, Any]:
    """
    Health check for LangGraph workflow system
    
    Args:
        multi_agent_service: Multi-agent service instance
        
    Returns:
        Health status of workflow system
    """
    try:
        # Get overall health status
        health_status = await multi_agent_service.health_check()
        
        # Extract LangGraph-specific status
        langgraph_status = health_status.get("langgraph_orchestrator", {})
        
        return {
            "status": "healthy" if langgraph_status.get("status") == "healthy" else "unhealthy",
            "langgraph_orchestrator": langgraph_status,
            "workflows_available": langgraph_status.get("workflows_available", 0),
            "workflow_names": langgraph_status.get("workflow_names", []),
            "redis_available": langgraph_status.get("redis_available", False),
            "agents_registered": langgraph_status.get("agents_registered", 0),
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Workflow health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }