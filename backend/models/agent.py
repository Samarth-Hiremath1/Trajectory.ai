"""
Agent system data models for multi-agent coordination
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class AgentType(Enum):
    """Types of specialized agents in the system"""
    ORCHESTRATOR = "orchestrator"
    CAREER_STRATEGY = "career_strategy"
    SKILLS_ANALYSIS = "skills_analysis"
    LEARNING_RESOURCE = "learning_resource"
    RESUME_OPTIMIZATION = "resume_optimization"
    CAREER_MENTOR = "career_mentor"

class RequestType(Enum):
    """Types of requests that can be processed by agents"""
    ROADMAP_GENERATION = "roadmap_generation"
    SKILL_ANALYSIS = "skill_analysis"
    RESUME_REVIEW = "resume_review"
    CAREER_ADVICE = "career_advice"
    LEARNING_PATH = "learning_path"
    INTERVIEW_PREP = "interview_prep"
    CAREER_TRANSITION = "career_transition"

class RequestPriority(Enum):
    """Priority levels for agent requests"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class RequestStatus(Enum):
    """Status of agent requests"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowStatus(Enum):
    """Status of agent workflows"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MessageType(Enum):
    """Types of inter-agent messages"""
    CONTEXT_SHARE = "context_share"
    COLLABORATION_REQUEST = "collaboration_request"
    INSIGHT_SHARE = "insight_share"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"

class AgentRequest(BaseModel):
    """Model for agent processing requests"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    request_type: RequestType
    content: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: RequestPriority = RequestPriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: RequestStatus = RequestStatus.PENDING
    assigned_agents: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentResponse(BaseModel):
    """Model for agent responses"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    agent_id: str
    agent_type: AgentType
    response_content: Dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AgentWorkflow(BaseModel):
    """Model for tracking multi-agent workflows"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    orchestrator_id: str
    participating_agents: List[str]
    workflow_steps: List[Dict[str, Any]] = Field(default_factory=list)
    current_step: int = 0
    status: WorkflowStatus = WorkflowStatus.CREATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentMessage(BaseModel):
    """Model for inter-agent communication"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_agent_id: str
    recipient_agent_id: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentCapability(BaseModel):
    """Model for defining agent capabilities"""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    confidence_threshold: float = 0.7
    max_processing_time: int = 30  # seconds

class AgentStatus(BaseModel):
    """Model for tracking agent status"""
    agent_id: str
    agent_type: AgentType
    is_active: bool = True
    current_load: int = 0
    max_concurrent_requests: int = 5
    capabilities: List[AgentCapability] = Field(default_factory=list)
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

class WorkflowStep(BaseModel):
    """Model for individual workflow steps"""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    agent_type: AgentType
    step_name: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: RequestStatus = RequestStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)  # List of step_ids this step depends on

class RequestAnalysis(BaseModel):
    """Model for request analysis results"""
    request_id: str
    complexity_score: float = Field(ge=0.0, le=1.0)
    required_agents: List[AgentType]
    estimated_processing_time: int  # seconds
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)
    risk_factors: List[str] = Field(default_factory=list)
    success_probability: float = Field(ge=0.0, le=1.0)

class AgentCollaboration(BaseModel):
    """Model for tracking agent collaborations"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    primary_agent_id: str
    collaborating_agents: List[str]
    collaboration_type: str  # e.g., "parallel", "sequential", "consensus"
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    coordination_rules: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)