from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from models.roadmap import (
    RoadmapRequest, Roadmap, RoadmapResponse, RoadmapGenerationResult,
    PhaseUpdateRequest
)
from services.roadmap_service import get_roadmap_service

# Optional embedding service import
try:
    from services.embedding_service import get_embedding_service
    EMBEDDING_AVAILABLE = True
except ImportError:
    get_embedding_service = None
    EMBEDDING_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])

from fastapi import Header

async def get_current_user_id(x_user_id: str = Header(None)) -> str:
    """Get user ID from request headers"""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not provided in headers"
        )
    return x_user_id

@router.post("/generate", response_model=Dict[str, Any])
async def generate_roadmap(
    request: RoadmapRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Generate a career roadmap based on user request"""
    
    try:
        logger.info(f"Generating roadmap for user {user_id}: {request.current_role} → {request.target_role}")
        
        # Get roadmap service
        roadmap_service = await get_roadmap_service()
        
        # Get user context from embeddings if available
        user_context = {}
        if EMBEDDING_AVAILABLE:
            try:
                embedding_service = get_embedding_service()
                # Try to get user resume context
                resume_chunks = embedding_service.search_resume_embeddings(
                    user_id=user_id,
                    query=f"experience skills background {request.current_role}",
                    n_results=3
                )
                
                if resume_chunks:
                    resume_summary = " ".join([chunk.get('content', '') for chunk in resume_chunks])
                    user_context['resume_summary'] = resume_summary[:1000]  # Limit context size
                    
            except Exception as e:
                logger.warning(f"Could not retrieve user context: {str(e)}")
        
        # Generate roadmap
        result = await roadmap_service.generate_roadmap(
            request=request,
            user_id=user_id,
            user_context=user_context
        )
        
        if result.success:
            # Save roadmap to database
            roadmap_id = await roadmap_service.save_roadmap(result.roadmap)
            result.roadmap.id = roadmap_id
            
            # Convert roadmap to response format
            roadmap_response = {
                "success": True,
                "roadmap": {
                    "id": result.roadmap.id,
                    "title": result.roadmap.title,
                    "description": result.roadmap.description,
                    "current_role": result.roadmap.current_role,
                    "target_role": result.roadmap.target_role,
                    "total_estimated_weeks": result.roadmap.total_estimated_weeks,
                    "phase_count": len(result.roadmap.phases),
                    "phases": [
                        {
                            "phase_number": phase.phase_number,
                            "title": phase.title,
                            "description": phase.description,
                            "duration_weeks": phase.duration_weeks,
                            "skills_count": len(phase.skills_to_develop),
                            "resources_count": len(phase.learning_resources),
                            "milestones_count": len(phase.milestones),
                            "skills_to_develop": [
                                {
                                    "name": skill.name,
                                    "current_level": skill.current_level.value,
                                    "target_level": skill.target_level.value,
                                    "priority": skill.priority
                                }
                                for skill in phase.skills_to_develop
                            ],
                            "learning_resources": [
                                {
                                    "title": resource.title,
                                    "description": resource.description,
                                    "url": resource.url,
                                    "resource_type": resource.resource_type.value,
                                    "provider": resource.provider,
                                    "duration": resource.duration,
                                    "skills_covered": resource.skills_covered
                                }
                                for resource in phase.learning_resources
                            ],
                            "milestones": [
                                {
                                    "title": milestone.title,
                                    "description": milestone.description,
                                    "estimated_completion_weeks": milestone.estimated_completion_weeks,
                                    "success_criteria": milestone.success_criteria,
                                    "deliverables": milestone.deliverables
                                }
                                for milestone in phase.milestones
                            ],
                            "prerequisites": phase.prerequisites,
                            "outcomes": phase.outcomes
                        }
                        for phase in result.roadmap.phases
                    ],
                    "created_date": result.roadmap.created_date.isoformat(),
                    "generation_metadata": {
                        "model_used": result.model_used,
                        "generation_time_seconds": result.generation_time_seconds,
                        "user_context_used": bool(user_context)
                    },
                    "strengths_analysis": result.strengths_analysis
                }
            }
            
            logger.info(f"Successfully generated roadmap with {len(result.roadmap.phases)} phases")
            return roadmap_response
            
        else:
            logger.error(f"Roadmap generation failed: {result.error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate roadmap: {result.error_message}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in roadmap generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/suggestions/{current_role}")
async def get_career_suggestions(
    current_role: str,
    user_background: str = "",
    max_suggestions: int = 5,
    user_id: str = Depends(get_current_user_id)
):
    """Get suggested target roles for career transition"""
    
    try:
        logger.info(f"Getting career suggestions for {current_role}")
        
        # Get roadmap service
        roadmap_service = await get_roadmap_service()
        
        # Enhance background with user context if available
        enhanced_background = user_background
        if not enhanced_background and EMBEDDING_AVAILABLE:
            try:
                embedding_service = get_embedding_service()
                resume_chunks = embedding_service.search_resume_embeddings(
                    user_id=user_id,
                    query=f"experience skills background {current_role}",
                    n_results=2
                )
                
                if resume_chunks:
                    enhanced_background = " ".join([chunk.get('content', '') for chunk in resume_chunks])[:500]
                    
            except Exception as e:
                logger.warning(f"Could not retrieve user background: {str(e)}")
        
        # Get suggestions
        suggestions = await roadmap_service.get_roadmap_suggestions(
            current_role=current_role,
            user_background=enhanced_background,
            max_suggestions=max_suggestions
        )
        
        return {
            "success": True,
            "current_role": current_role,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error getting career suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get career suggestions: {str(e)}"
        )

@router.get("/health")
async def roadmap_health_check():
    """Health check for roadmap service"""
    
    try:
        # Test roadmap service initialization
        roadmap_service = await get_roadmap_service()
        
        # Test a simple suggestion request
        test_suggestions = await roadmap_service.get_roadmap_suggestions(
            current_role="Software Engineer",
            user_background="5 years experience in web development",
            max_suggestions=2
        )
        
        health_data = {
            "status": "healthy",
            "service": "roadmap",
            "test_suggestions_count": len(test_suggestions),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add workflow integration status
        health_data["workflow_integration"] = {
            "available": hasattr(roadmap_service, 'workflow_orchestrator') and roadmap_service.workflow_orchestrator is not None,
            "orchestrator_initialized": roadmap_service.workflow_orchestrator is not None if hasattr(roadmap_service, 'workflow_orchestrator') else False
        }
        
        if hasattr(roadmap_service, 'workflow_orchestrator') and roadmap_service.workflow_orchestrator:
            workflow_health = await roadmap_service.workflow_orchestrator.health_check()
            health_data["workflow_orchestrator"] = workflow_health
        
        return health_data
        
    except Exception as e:
        logger.error(f"Roadmap health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "roadmap",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/workflow-capabilities")
async def get_roadmap_workflow_capabilities():
    """Get workflow capabilities for roadmap generation"""
    
    try:
        roadmap_service = await get_roadmap_service()
        
        capabilities = {
            "workflow_available": hasattr(roadmap_service, 'workflow_orchestrator') and roadmap_service.workflow_orchestrator is not None,
            "supported_workflows": [],
            "complexity_thresholds": {
                "multiple_focus_areas": "> 2 focus areas",
                "multiple_constraints": "> 1 constraint", 
                "specific_timeline": "timeline preference specified",
                "detailed_background": "> 200 characters",
                "career_transition": "different current and target roles"
            }
        }
        
        if hasattr(roadmap_service, 'workflow_orchestrator') and roadmap_service.workflow_orchestrator:
            capabilities["supported_workflows"] = roadmap_service.workflow_orchestrator.get_available_workflows()
            
            templates = roadmap_service.workflow_orchestrator.get_workflow_templates()
            capabilities["workflow_templates"] = templates
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Failed to get workflow capabilities: {str(e)}")
        return {
            "workflow_available": False,
            "error": str(e),
            "supported_workflows": []
        }

@router.post("/test-generation")
async def test_roadmap_generation():
    """Test endpoint for roadmap generation"""
    
    try:
        # Create test request
        test_request = RoadmapRequest(
            current_role="Junior Software Engineer",
            target_role="Senior Software Engineer",
            user_background="2 years experience in Python and web development. Familiar with Django and React.",
            timeline_preference="6 months",
            focus_areas=["system design", "leadership skills"],
            constraints=["limited time on weekends"]
        )
        
        # Generate roadmap
        roadmap_service = await get_roadmap_service()
        result = await roadmap_service.generate_roadmap(
            request=test_request,
            user_id="test_user"
        )
        
        if result.success:
            return {
                "success": True,
                "message": "Test roadmap generated successfully",
                "roadmap_title": result.roadmap.title,
                "phase_count": len(result.roadmap.phases),
                "total_weeks": result.roadmap.total_estimated_weeks,
                "generation_time": result.generation_time_seconds
            }
        else:
            return {
                "success": False,
                "error": result.error_message
            }
            
    except Exception as e:
        logger.error(f"Test roadmap generation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
@router.get("/user/{user_id}")
async def get_user_roadmaps(user_id: str):
    """Get all roadmaps for a user"""
    
    try:
        roadmap_service = await get_roadmap_service()
        roadmaps = await roadmap_service.load_user_roadmaps(user_id)
        
        # Convert to response format
        roadmap_summaries = []
        for roadmap in roadmaps:
            roadmap_summaries.append({
                "id": roadmap.id,
                "title": roadmap.title,
                "current_role": roadmap.current_role,
                "target_role": roadmap.target_role,
                "status": roadmap.status.value,
                "total_estimated_weeks": roadmap.total_estimated_weeks,
                "phase_count": len(roadmap.phases),
                "overall_progress_percentage": roadmap.overall_progress_percentage,
                "created_date": roadmap.created_date.isoformat(),
                "updated_date": roadmap.updated_date.isoformat(),
                "last_accessed_date": roadmap.last_accessed_date.isoformat() if roadmap.last_accessed_date else None
            })
        
        return {
            "success": True,
            "roadmaps": roadmap_summaries,
            "count": len(roadmap_summaries)
        }
        
    except Exception as e:
        logger.error(f"Error getting user roadmaps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user roadmaps: {str(e)}"
        )

@router.get("/{roadmap_id}")
async def get_roadmap(roadmap_id: str):
    """Get a specific roadmap by ID"""
    
    try:
        roadmap_service = await get_roadmap_service()
        roadmap = await roadmap_service.load_roadmap(roadmap_id)
        
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Roadmap not found"
            )
        
        # Convert to detailed response format
        roadmap_data = {
            "id": roadmap.id,
            "title": roadmap.title,
            "description": roadmap.description,
            "current_role": roadmap.current_role,
            "target_role": roadmap.target_role,
            "status": roadmap.status.value,
            "total_estimated_weeks": roadmap.total_estimated_weeks,
            "overall_progress_percentage": roadmap.overall_progress_percentage,
            "current_phase": roadmap.current_phase,
            "phases": [
                {
                    "phase_number": phase.phase_number,
                    "title": phase.title,
                    "description": phase.description,
                    "duration_weeks": phase.duration_weeks,
                    "is_completed": phase.is_completed,
                    "started_date": phase.started_date.isoformat() if phase.started_date else None,
                    "completed_date": phase.completed_date.isoformat() if phase.completed_date else None,
                    "skills_to_develop": [
                        {
                            "name": skill.name,
                            "description": skill.description,
                            "current_level": skill.current_level.value,
                            "target_level": skill.target_level.value,
                            "priority": skill.priority,
                            "estimated_hours": skill.estimated_hours
                        }
                        for skill in phase.skills_to_develop
                    ],
                    "learning_resources": [
                        {
                            "title": resource.title,
                            "description": resource.description,
                            "url": resource.url,
                            "resource_type": resource.resource_type.value,
                            "provider": resource.provider,
                            "duration": resource.duration,
                            "cost": resource.cost,
                            "difficulty": resource.difficulty.value if resource.difficulty else None,
                            "rating": resource.rating,
                            "skills_covered": resource.skills_covered
                        }
                        for resource in phase.learning_resources
                    ],
                    "milestones": [
                        {
                            "title": milestone.title,
                            "description": milestone.description,
                            "estimated_completion_weeks": milestone.estimated_completion_weeks,
                            "success_criteria": milestone.success_criteria,
                            "deliverables": milestone.deliverables,
                            "is_completed": milestone.is_completed,
                            "completed_date": milestone.completed_date.isoformat() if milestone.completed_date else None
                        }
                        for milestone in phase.milestones
                    ],
                    "prerequisites": phase.prerequisites,
                    "outcomes": phase.outcomes
                }
                for phase in roadmap.phases
            ],
            "created_date": roadmap.created_date.isoformat(),
            "updated_date": roadmap.updated_date.isoformat(),
            "last_accessed_date": roadmap.last_accessed_date.isoformat() if roadmap.last_accessed_date else None,
            "generated_with_model": roadmap.generated_with_model,
            "user_context_used": roadmap.user_context_used
        }
        
        return {
            "success": True,
            "roadmap": roadmap_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting roadmap {roadmap_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get roadmap: {str(e)}"
        )

@router.put("/{roadmap_id}/progress")
async def update_roadmap_progress(roadmap_id: str, progress_data: Dict[str, Any]):
    """Update roadmap progress"""
    
    try:
        roadmap_service = await get_roadmap_service()
        success = await roadmap_service.update_roadmap_progress(roadmap_id, progress_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Roadmap not found or update failed"
            )
        
        return {
            "success": True,
            "message": "Roadmap progress updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating roadmap progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update roadmap progress: {str(e)}"
        )

@router.delete("/{roadmap_id}")
async def delete_roadmap(roadmap_id: str):
    """Delete a roadmap"""
    
    try:
        roadmap_service = await get_roadmap_service()
        success = await roadmap_service.delete_roadmap(roadmap_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Roadmap not found"
            )
        
        return {
            "success": True,
            "message": "Roadmap deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting roadmap: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete roadmap: {str(e)}"
        )
@router.get("/{roadmap_id}/export")
async def export_roadmap(roadmap_id: str, format: str = "json"):
    """Export a roadmap in various formats"""
    
    try:
        roadmap_service = await get_roadmap_service()
        roadmap = await roadmap_service.load_roadmap(roadmap_id)
        
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Roadmap not found"
            )
        
        if format.lower() == "json":
            # Export as JSON
            export_data = {
                "roadmap": {
                    "id": roadmap.id,
                    "title": roadmap.title,
                    "description": roadmap.description,
                    "current_role": roadmap.current_role,
                    "target_role": roadmap.target_role,
                    "status": roadmap.status.value,
                    "total_estimated_weeks": roadmap.total_estimated_weeks,
                    "overall_progress_percentage": roadmap.overall_progress_percentage,
                    "phases": [
                        {
                            "phase_number": phase.phase_number,
                            "title": phase.title,
                            "description": phase.description,
                            "duration_weeks": phase.duration_weeks,
                            "is_completed": phase.is_completed,
                            "skills_to_develop": [
                                {
                                    "name": skill.name,
                                    "description": skill.description,
                                    "current_level": skill.current_level.value,
                                    "target_level": skill.target_level.value,
                                    "priority": skill.priority,
                                    "estimated_hours": skill.estimated_hours
                                }
                                for skill in phase.skills_to_develop
                            ],
                            "learning_resources": [
                                {
                                    "title": resource.title,
                                    "description": resource.description,
                                    "url": resource.url,
                                    "resource_type": resource.resource_type.value,
                                    "provider": resource.provider,
                                    "duration": resource.duration,
                                    "cost": resource.cost,
                                    "skills_covered": resource.skills_covered
                                }
                                for resource in phase.learning_resources
                            ],
                            "milestones": [
                                {
                                    "title": milestone.title,
                                    "description": milestone.description,
                                    "estimated_completion_weeks": milestone.estimated_completion_weeks,
                                    "success_criteria": milestone.success_criteria,
                                    "deliverables": milestone.deliverables,
                                    "is_completed": milestone.is_completed
                                }
                                for milestone in phase.milestones
                            ],
                            "prerequisites": phase.prerequisites,
                            "outcomes": phase.outcomes
                        }
                        for phase in roadmap.phases
                    ],
                    "created_date": roadmap.created_date.isoformat(),
                    "updated_date": roadmap.updated_date.isoformat(),
                    "generated_with_model": roadmap.generated_with_model
                },
                "export_metadata": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "format": "json",
                    "version": "1.0"
                }
            }
            
            return export_data
            
        elif format.lower() == "markdown":
            # Export as Markdown
            markdown_content = f"""# {roadmap.title}

**Current Role:** {roadmap.current_role}  
**Target Role:** {roadmap.target_role}  
**Status:** {roadmap.status.value.title()}  
**Total Timeline:** {roadmap.total_estimated_weeks} weeks  
**Progress:** {roadmap.overall_progress_percentage}%

## Description
{roadmap.description or 'No description provided.'}

## Roadmap Phases

"""
            
            for phase in roadmap.phases:
                markdown_content += f"""### Phase {phase.phase_number}: {phase.title}

**Duration:** {phase.duration_weeks} weeks  
**Status:** {'✅ Completed' if phase.is_completed else '⏳ In Progress'}

{phase.description}

#### Skills to Develop
"""
                for skill in phase.skills_to_develop:
                    markdown_content += f"- **{skill.name}** ({skill.current_level.value} → {skill.target_level.value}) - Priority: {skill.priority}/5\n"
                    if skill.description:
                        markdown_content += f"  - {skill.description}\n"

                markdown_content += "\n#### Learning Resources\n"
                for resource in phase.learning_resources:
                    markdown_content += f"- **{resource.title}** ({resource.resource_type.value})\n"
                    if resource.description:
                        markdown_content += f"  - {resource.description}\n"
                    if resource.url:
                        markdown_content += f"  - Link: {resource.url}\n"
                    if resource.duration:
                        markdown_content += f"  - Duration: {resource.duration}\n"

                markdown_content += "\n#### Milestones\n"
                for milestone in phase.milestones:
                    status_icon = "✅" if milestone.is_completed else "⏳"
                    markdown_content += f"- {status_icon} **{milestone.title}** (Week {milestone.estimated_completion_weeks})\n"
                    if milestone.description:
                        markdown_content += f"  - {milestone.description}\n"
                    if milestone.success_criteria:
                        markdown_content += "  - Success Criteria:\n"
                        for criteria in milestone.success_criteria:
                            markdown_content += f"    - {criteria}\n"

                if phase.prerequisites:
                    markdown_content += "\n#### Prerequisites\n"
                    for prereq in phase.prerequisites:
                        markdown_content += f"- {prereq}\n"

                if phase.outcomes:
                    markdown_content += "\n#### Expected Outcomes\n"
                    for outcome in phase.outcomes:
                        markdown_content += f"- {outcome}\n"

                markdown_content += "\n---\n\n"

            markdown_content += f"""## Export Information

- **Exported:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- **Generated with:** {roadmap.generated_with_model or 'AI Assistant'}
- **Original creation:** {roadmap.created_date.strftime('%Y-%m-%d')}
"""

            return {
                "content": markdown_content,
                "filename": f"{roadmap.title.replace(' ', '_').lower()}_roadmap.md",
                "content_type": "text/markdown"
            }
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {format}. Supported formats: json, markdown"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting roadmap {roadmap_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export roadmap: {str(e)}"
        )