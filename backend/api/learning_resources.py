"""
Learning Resources API endpoints
"""
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from services.multi_agent_service import get_multi_agent_service, MultiAgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning-resources", tags=["learning-resources"])

# Request/Response Models
class LearningPathRequest(BaseModel):
    """Request model for creating personalized learning paths"""
    user_id: str
    skills_to_learn: List[str]
    learning_style: str = Field(default="mixed", description="Preferred learning style: visual, auditory, hands-on, reading, mixed")
    timeline: str = Field(default="3 months", description="Available timeline for learning")
    budget: str = Field(default="flexible", description="Budget constraints: free, low, medium, high, flexible")
    current_level: str = Field(default="beginner", description="Current skill level: beginner, intermediate, advanced")

class SkillResourceRequest(BaseModel):
    """Request model for skill-specific resource recommendations"""
    user_id: str
    skills_needed: List[str]
    skill_gaps: Optional[Dict[str, Any]] = Field(default=None, description="Optional skill gap analysis")
    priority_skills: Optional[List[str]] = Field(default=None, description="Optional priority skills list")

class LearningAdviceRequest(BaseModel):
    """Request model for learning resource advice"""
    user_id: str
    question: str = Field(description="Learning-related question or topic")

class LearningPathResponse(BaseModel):
    """Response model for learning path creation"""
    success: bool
    learning_path: Optional[Dict[str, Any]] = None
    resource_recommendations: Optional[Dict[str, Any]] = None
    milestone_plan: Optional[Dict[str, Any]] = None
    project_suggestions: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    request_id: Optional[str] = None

class ResourceRecommendationResponse(BaseModel):
    """Response model for resource recommendations"""
    success: bool
    skill_resources: Optional[Dict[str, Any]] = None
    learning_sequence: Optional[List[Dict[str, Any]]] = None
    validation_methods: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    request_id: Optional[str] = None

class LearningAdviceResponse(BaseModel):
    """Response model for learning advice"""
    success: bool
    advice: Optional[str] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    strategies: Optional[List[str]] = None
    platforms: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None
    error: Optional[str] = None
    request_id: Optional[str] = None

@router.post("/learning-path", response_model=LearningPathResponse)
async def create_learning_path(
    request: LearningPathRequest,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service)
) -> LearningPathResponse:
    """
    Create a personalized learning path based on user requirements
    
    Args:
        request: Learning path request with user requirements
        multi_agent_service: Multi-agent service instance
        
    Returns:
        Personalized learning path with resources and milestones
    """
    try:
        logger.info(f"Creating learning path for user {request.user_id} with skills: {request.skills_to_learn}")
        
        # Process request through multi-agent system
        result = await multi_agent_service.create_personalized_learning_path(
            user_id=request.user_id,
            skills_to_learn=request.skills_to_learn,
            learning_style=request.learning_style,
            timeline=request.timeline,
            budget=request.budget,
            current_level=request.current_level
        )
        
        if result.get("success", False):
            # Extract learning path data from agent responses
            learning_path_data = None
            resource_recommendations = None
            milestone_plan = None
            project_suggestions = None
            
            for response in result.get("responses", []):
                if response.get("agent_type") == "learning_resource":
                    response_content = response.get("response_content", {})
                    learning_path_data = response_content.get("personalized_learning_path")
                    resource_recommendations = response_content.get("resource_recommendations")
                    milestone_plan = response_content.get("milestone_plan")
                    project_suggestions = response_content.get("project_suggestions")
                    break
            
            return LearningPathResponse(
                success=True,
                learning_path=learning_path_data,
                resource_recommendations=resource_recommendations,
                milestone_plan=milestone_plan,
                project_suggestions=project_suggestions,
                request_id=result.get("request_id")
            )
        else:
            return LearningPathResponse(
                success=False,
                error=result.get("error", "Failed to create learning path"),
                request_id=result.get("request_id")
            )
            
    except Exception as e:
        logger.error(f"Error creating learning path: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create learning path: {str(e)}")

@router.post("/skill-resources", response_model=ResourceRecommendationResponse)
async def get_skill_resources(
    request: SkillResourceRequest,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service)
) -> ResourceRecommendationResponse:
    """
    Get learning resource recommendations for specific skills
    
    Args:
        request: Skill resource request
        multi_agent_service: Multi-agent service instance
        
    Returns:
        Skill-specific learning resource recommendations
    """
    try:
        logger.info(f"Getting skill resources for user {request.user_id} with skills: {request.skills_needed}")
        
        # Process request through multi-agent system
        result = await multi_agent_service.get_learning_resource_recommendations(
            user_id=request.user_id,
            skills_needed=request.skills_needed,
            skill_gaps=request.skill_gaps,
            priority_skills=request.priority_skills
        )
        
        if result.get("success", False):
            # Extract resource data from agent responses
            skill_resources = None
            learning_sequence = None
            validation_methods = None
            
            for response in result.get("responses", []):
                if response.get("agent_type") == "learning_resource":
                    response_content = response.get("response_content", {})
                    skill_learning_resources = response_content.get("skill_learning_resources", {})
                    skill_resources = skill_learning_resources.get("skill_specific_resources")
                    learning_sequence = skill_learning_resources.get("optimized_learning_sequence")
                    validation_methods = skill_learning_resources.get("skill_validation_methods")
                    break
            
            return ResourceRecommendationResponse(
                success=True,
                skill_resources=skill_resources,
                learning_sequence=learning_sequence,
                validation_methods=validation_methods,
                request_id=result.get("request_id")
            )
        else:
            return ResourceRecommendationResponse(
                success=False,
                error=result.get("error", "Failed to get skill resources"),
                request_id=result.get("request_id")
            )
            
    except Exception as e:
        logger.error(f"Error getting skill resources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get skill resources: {str(e)}")

@router.post("/advice", response_model=LearningAdviceResponse)
async def get_learning_advice(
    request: LearningAdviceRequest,
    multi_agent_service: MultiAgentService = Depends(get_multi_agent_service)
) -> LearningAdviceResponse:
    """
    Get learning resource advice for general queries
    
    Args:
        request: Learning advice request
        multi_agent_service: Multi-agent service instance
        
    Returns:
        Learning resource advice and recommendations
    """
    try:
        logger.info(f"Getting learning advice for user {request.user_id}: {request.question}")
        
        # Process request through multi-agent system
        result = await multi_agent_service.get_learning_resource_advice(
            user_id=request.user_id,
            question=request.question
        )
        
        if result.get("success", False):
            # Extract advice data from agent responses
            advice = None
            recommendations = None
            strategies = None
            platforms = None
            next_steps = None
            
            for response in result.get("responses", []):
                if response.get("agent_type") == "learning_resource":
                    response_content = response.get("response_content", {})
                    advice = response_content.get("learning_resource_advice")
                    recommendations = response_content.get("specific_recommendations")
                    strategies = response_content.get("learning_strategies")
                    platforms = response_content.get("platform_suggestions")
                    next_steps = response_content.get("next_steps")
                    break
            
            return LearningAdviceResponse(
                success=True,
                advice=advice,
                recommendations=recommendations,
                strategies=strategies,
                platforms=platforms,
                next_steps=next_steps,
                request_id=result.get("request_id")
            )
        else:
            return LearningAdviceResponse(
                success=False,
                error=result.get("error", "Failed to get learning advice"),
                request_id=result.get("request_id")
            )
            
    except Exception as e:
        logger.error(f"Error getting learning advice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get learning advice: {str(e)}")

@router.get("/platforms")
async def get_learning_platforms() -> Dict[str, Any]:
    """
    Get information about available learning platforms
    
    Returns:
        Learning platforms information
    """
    try:
        platforms = {
            "coursera": {
                "name": "Coursera",
                "type": "MOOC",
                "strengths": ["University partnerships", "Certificates", "Structured courses"],
                "cost_model": "Subscription or per-course",
                "best_for": ["Academic subjects", "Professional certificates"],
                "url": "https://www.coursera.org"
            },
            "udemy": {
                "name": "Udemy",
                "type": "Marketplace",
                "strengths": ["Practical skills", "Lifetime access", "Frequent sales"],
                "cost_model": "One-time purchase",
                "best_for": ["Technical skills", "Creative skills", "Business skills"],
                "url": "https://www.udemy.com"
            },
            "pluralsight": {
                "name": "Pluralsight",
                "type": "Professional",
                "strengths": ["Technology focus", "Skill assessments", "Learning paths"],
                "cost_model": "Subscription",
                "best_for": ["Software development", "IT skills", "Creative tools"],
                "url": "https://www.pluralsight.com"
            },
            "edx": {
                "name": "edX",
                "type": "MOOC",
                "strengths": ["University courses", "Free options", "MicroMasters"],
                "cost_model": "Free with paid certificates",
                "best_for": ["Academic subjects", "Computer science", "Data science"],
                "url": "https://www.edx.org"
            },
            "linkedin_learning": {
                "name": "LinkedIn Learning",
                "type": "Professional",
                "strengths": ["Business skills", "Professional development", "Integration with LinkedIn"],
                "cost_model": "Subscription",
                "best_for": ["Business skills", "Leadership", "Professional development"],
                "url": "https://www.linkedin.com/learning"
            },
            "youtube": {
                "name": "YouTube",
                "type": "Free",
                "strengths": ["Free content", "Diverse creators", "Visual learning"],
                "cost_model": "Free (with ads)",
                "best_for": ["Tutorials", "Quick learning", "Visual demonstrations"],
                "url": "https://www.youtube.com"
            }
        }
        
        return {
            "success": True,
            "platforms": platforms,
            "total_platforms": len(platforms)
        }
        
    except Exception as e:
        logger.error(f"Error getting learning platforms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get learning platforms: {str(e)}")

@router.get("/certifications/{role}")
async def get_role_certifications(
    role: str,
    level: Optional[str] = Query(default="all", description="Certification level: entry, mid, senior, all")
) -> Dict[str, Any]:
    """
    Get certification recommendations for a specific role
    
    Args:
        role: Target role (e.g., "software engineer", "data scientist")
        level: Career level filter
        
    Returns:
        Role-specific certification recommendations
    """
    try:
        # This would typically use the Learning Resource Agent
        # For now, providing static recommendations
        
        role_lower = role.lower()
        certifications = {}
        
        if "software" in role_lower or "developer" in role_lower:
            certifications = {
                "aws_certified_developer": {
                    "name": "AWS Certified Developer - Associate",
                    "provider": "Amazon Web Services",
                    "level": "mid",
                    "cost": "$150",
                    "validity": "3 years",
                    "skills": ["AWS services", "Cloud development", "Serverless architecture"]
                },
                "google_cloud_developer": {
                    "name": "Google Cloud Professional Cloud Developer",
                    "provider": "Google Cloud",
                    "level": "mid",
                    "cost": "$200",
                    "validity": "2 years",
                    "skills": ["GCP services", "Application development", "DevOps"]
                }
            }
        elif "data" in role_lower:
            certifications = {
                "aws_data_analytics": {
                    "name": "AWS Certified Data Analytics - Specialty",
                    "provider": "Amazon Web Services",
                    "level": "senior",
                    "cost": "$300",
                    "validity": "3 years",
                    "skills": ["Data lakes", "Analytics", "Machine learning"]
                },
                "google_data_engineer": {
                    "name": "Google Cloud Professional Data Engineer",
                    "provider": "Google Cloud",
                    "level": "mid",
                    "cost": "$200",
                    "validity": "2 years",
                    "skills": ["Data pipelines", "BigQuery", "Machine learning"]
                }
            }
        
        # Filter by level if specified
        if level != "all":
            certifications = {
                k: v for k, v in certifications.items() 
                if v.get("level") == level
            }
        
        return {
            "success": True,
            "role": role,
            "level_filter": level,
            "certifications": certifications,
            "total_certifications": len(certifications)
        }
        
    except Exception as e:
        logger.error(f"Error getting role certifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get role certifications: {str(e)}")

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for learning resources API
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "learning_resources_api",
        "timestamp": "2024-01-01T00:00:00Z"
    }