from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class RoadmapStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class ResourceType(str, Enum):
    COURSE = "course"
    CERTIFICATION = "certification"
    PROJECT = "project"
    BOOK = "book"
    ARTICLE = "article"
    VIDEO = "video"
    PRACTICE = "practice"

class Skill(BaseModel):
    """Individual skill model"""
    name: str
    description: Optional[str] = None
    current_level: SkillLevel = SkillLevel.BEGINNER
    target_level: SkillLevel = SkillLevel.INTERMEDIATE
    priority: int = Field(ge=1, le=5, default=3)  # 1 = highest, 5 = lowest
    estimated_hours: Optional[int] = None

class LearningResource(BaseModel):
    """Learning resource model"""
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    resource_type: ResourceType
    provider: Optional[str] = None
    duration: Optional[str] = None  # e.g., "4 weeks", "20 hours"
    cost: Optional[str] = None  # e.g., "Free", "$49", "Subscription"
    difficulty: Optional[SkillLevel] = None
    rating: Optional[float] = Field(ge=0, le=5, default=None)
    skills_covered: List[str] = Field(default_factory=list)

class Milestone(BaseModel):
    """Milestone within a phase"""
    title: str
    description: Optional[str] = None
    estimated_completion_weeks: int = Field(ge=1, default=1)
    success_criteria: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)
    is_completed: bool = False
    completed_date: Optional[datetime] = None

class RoadmapPhase(BaseModel):
    """Individual phase in a career roadmap"""
    phase_number: int = Field(ge=1)
    title: str
    description: str
    duration_weeks: int = Field(ge=1)
    skills_to_develop: List[Skill] = Field(default_factory=list)
    learning_resources: List[LearningResource] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)  # Skills/knowledge needed before starting
    outcomes: List[str] = Field(default_factory=list)  # What you'll achieve after completing
    is_completed: bool = False
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

class RoadmapRequest(BaseModel):
    """Request model for roadmap generation"""
    current_role: str
    target_role: str
    user_background: Optional[str] = None
    timeline_preference: Optional[str] = None  # e.g., "6 months", "1 year", "flexible"
    focus_areas: List[str] = Field(default_factory=list)  # Specific areas to emphasize
    constraints: List[str] = Field(default_factory=list)  # Time, budget, or other constraints

class Roadmap(BaseModel):
    """Complete career roadmap model"""
    id: Optional[str] = None
    user_id: str
    title: str
    description: Optional[str] = None
    current_role: str
    target_role: str
    status: RoadmapStatus = RoadmapStatus.DRAFT
    
    # Roadmap content
    phases: List[RoadmapPhase] = Field(default_factory=list)
    total_estimated_weeks: int = Field(ge=1, default=1)
    
    # Metadata
    created_date: datetime = Field(default_factory=datetime.utcnow)
    updated_date: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_date: Optional[datetime] = None
    
    # Progress tracking
    overall_progress_percentage: float = Field(ge=0, le=100, default=0.0)
    current_phase: Optional[int] = None
    
    # Generation metadata
    generated_with_model: Optional[str] = None
    generation_prompt: Optional[str] = None
    user_context_used: Optional[Dict[str, Any]] = None

class RoadmapResponse(BaseModel):
    """Response model for roadmap operations"""
    id: str
    title: str
    current_role: str
    target_role: str
    status: RoadmapStatus
    total_estimated_weeks: int
    phase_count: int
    overall_progress_percentage: float
    created_date: datetime
    updated_date: datetime

class RoadmapGenerationResult(BaseModel):
    """Result of roadmap generation operation"""
    model_config = {"protected_namespaces": ()}
    
    success: bool
    roadmap: Optional[Roadmap] = None
    error_message: Optional[str] = None
    generation_time_seconds: Optional[float] = None
    model_used: Optional[str] = None

class PhaseUpdateRequest(BaseModel):
    """Request to update phase progress"""
    phase_number: int
    milestone_updates: Optional[List[Dict[str, Any]]] = None
    is_completed: Optional[bool] = None
    notes: Optional[str] = None