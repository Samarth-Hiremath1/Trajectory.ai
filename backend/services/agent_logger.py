"""
Agent Activity Logger for tracking agent interactions and performance
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class ActivityType(Enum):
    REQUEST_RECEIVED = "request_received"
    REQUEST_PROCESSED = "request_processed"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    AGENT_COLLABORATION = "agent_collaboration"
    MESSAGE_SENT = "message_sent"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"

@dataclass
class AgentLogEntry:
    timestamp: datetime
    agent_id: str
    agent_type: str
    activity_type: ActivityType
    level: LogLevel
    message: str
    metadata: Dict[str, Any]
    request_id: Optional[str] = None
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None

class AgentLogger:
    """
    Centralized logger for agent activities with structured logging
    """
    
    def __init__(self, max_entries: int = 10000):
        """
        Initialize the agent logger
        
        Args:
            max_entries: Maximum number of log entries to keep in memory
        """
        self.max_entries = max_entries
        self.log_entries: List[AgentLogEntry] = []
        
        # Set up Python logger
        self.logger = logging.getLogger("agent_system")
        self.logger.setLevel(logging.INFO)
        
        # Create formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def log_activity(
        self,
        agent_id: str,
        agent_type: str,
        activity_type: ActivityType,
        message: str,
        level: LogLevel = LogLevel.INFO,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Log an agent activity
        
        Args:
            agent_id: ID of the agent performing the activity
            agent_type: Type of the agent
            activity_type: Type of activity being logged
            message: Human-readable message describing the activity
            level: Log level
            metadata: Additional metadata about the activity
            request_id: Associated request ID if applicable
            workflow_id: Associated workflow ID if applicable
            user_id: Associated user ID if applicable
        """
        entry = AgentLogEntry(
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            agent_type=agent_type,
            activity_type=activity_type,
            level=level,
            message=message,
            metadata=metadata or {},
            request_id=request_id,
            workflow_id=workflow_id,
            user_id=user_id
        )
        
        # Add to in-memory storage
        self.log_entries.append(entry)
        
        # Trim entries if we exceed max size
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]
        
        # Log to Python logger
        log_data = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "activity_type": activity_type.value,
            "request_id": request_id,
            "workflow_id": workflow_id,
            "user_id": user_id,
            "metadata": metadata
        }
        
        log_message = f"{message} | {json.dumps(log_data, default=str)}"
        
        if level == LogLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.logger.error(log_message)
    
    def log_request_received(
        self,
        agent_id: str,
        agent_type: str,
        request_id: str,
        request_type: str,
        user_id: Optional[str] = None
    ):
        """Log when an agent receives a request"""
        self.log_activity(
            agent_id=agent_id,
            agent_type=agent_type,
            activity_type=ActivityType.REQUEST_RECEIVED,
            message=f"Agent received {request_type} request",
            metadata={"request_type": request_type},
            request_id=request_id,
            user_id=user_id
        )
    
    def log_request_processed(
        self,
        agent_id: str,
        agent_type: str,
        request_id: str,
        processing_time: float,
        confidence_score: float,
        success: bool,
        user_id: Optional[str] = None
    ):
        """Log when an agent completes processing a request"""
        self.log_activity(
            agent_id=agent_id,
            agent_type=agent_type,
            activity_type=ActivityType.REQUEST_PROCESSED,
            message=f"Agent processed request in {processing_time:.2f}s with {confidence_score:.2f} confidence",
            level=LogLevel.INFO if success else LogLevel.WARNING,
            metadata={
                "processing_time": processing_time,
                "confidence_score": confidence_score,
                "success": success
            },
            request_id=request_id,
            user_id=user_id
        )
    
    def log_workflow_started(
        self,
        orchestrator_id: str,
        workflow_id: str,
        request_type: str,
        participating_agents: List[str],
        user_id: Optional[str] = None
    ):
        """Log when a workflow is started"""
        self.log_activity(
            agent_id=orchestrator_id,
            agent_type="orchestrator",
            activity_type=ActivityType.WORKFLOW_STARTED,
            message=f"Started {request_type} workflow with {len(participating_agents)} agents",
            metadata={
                "request_type": request_type,
                "participating_agents": participating_agents,
                "agent_count": len(participating_agents)
            },
            workflow_id=workflow_id,
            user_id=user_id
        )
    
    def log_workflow_completed(
        self,
        orchestrator_id: str,
        workflow_id: str,
        execution_time: float,
        success: bool,
        steps_completed: int,
        user_id: Optional[str] = None
    ):
        """Log when a workflow is completed"""
        self.log_activity(
            agent_id=orchestrator_id,
            agent_type="orchestrator",
            activity_type=ActivityType.WORKFLOW_COMPLETED,
            message=f"Workflow completed in {execution_time:.2f}s with {steps_completed} steps",
            level=LogLevel.INFO if success else LogLevel.ERROR,
            metadata={
                "execution_time": execution_time,
                "success": success,
                "steps_completed": steps_completed
            },
            workflow_id=workflow_id,
            user_id=user_id
        )
    
    def log_agent_collaboration(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: str,
        workflow_id: Optional[str] = None
    ):
        """Log inter-agent collaboration"""
        self.log_activity(
            agent_id=sender_id,
            agent_type="unknown",  # Will be filled by caller if needed
            activity_type=ActivityType.AGENT_COLLABORATION,
            message=f"Agent collaboration: {message_type} message to {recipient_id}",
            metadata={
                "recipient_id": recipient_id,
                "message_type": message_type
            },
            workflow_id=workflow_id
        )
    
    def log_error(
        self,
        agent_id: str,
        agent_type: str,
        error_message: str,
        error_type: str,
        request_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Log an error that occurred during agent processing"""
        self.log_activity(
            agent_id=agent_id,
            agent_type=agent_type,
            activity_type=ActivityType.ERROR_OCCURRED,
            message=f"Agent error: {error_message}",
            level=LogLevel.ERROR,
            metadata={
                "error_type": error_type,
                "error_message": error_message
            },
            request_id=request_id,
            workflow_id=workflow_id,
            user_id=user_id
        )
    
    def get_recent_activities(
        self,
        limit: int = 100,
        agent_id: Optional[str] = None,
        activity_type: Optional[ActivityType] = None,
        level: Optional[LogLevel] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent agent activities with optional filtering
        
        Args:
            limit: Maximum number of entries to return
            agent_id: Filter by specific agent ID
            activity_type: Filter by activity type
            level: Filter by log level
            
        Returns:
            List of log entries as dictionaries
        """
        filtered_entries = self.log_entries
        
        # Apply filters
        if agent_id:
            filtered_entries = [e for e in filtered_entries if e.agent_id == agent_id]
        
        if activity_type:
            filtered_entries = [e for e in filtered_entries if e.activity_type == activity_type]
        
        if level:
            filtered_entries = [e for e in filtered_entries if e.level == level]
        
        # Sort by timestamp (most recent first) and limit
        sorted_entries = sorted(filtered_entries, key=lambda x: x.timestamp, reverse=True)
        limited_entries = sorted_entries[:limit]
        
        # Convert to dictionaries
        return [asdict(entry) for entry in limited_entries]
    
    def get_activity_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about agent activities
        
        Returns:
            Dictionary with activity statistics
        """
        if not self.log_entries:
            return {
                "total_activities": 0,
                "activities_by_type": {},
                "activities_by_agent": {},
                "activities_by_level": {},
                "recent_activity_count": 0
            }
        
        # Count activities by type
        activities_by_type = {}
        for entry in self.log_entries:
            activity_type = entry.activity_type.value
            activities_by_type[activity_type] = activities_by_type.get(activity_type, 0) + 1
        
        # Count activities by agent
        activities_by_agent = {}
        for entry in self.log_entries:
            agent_id = entry.agent_id
            activities_by_agent[agent_id] = activities_by_agent.get(agent_id, 0) + 1
        
        # Count activities by level
        activities_by_level = {}
        for entry in self.log_entries:
            level = entry.level.value
            activities_by_level[level] = activities_by_level.get(level, 0) + 1
        
        # Count recent activities (last hour)
        one_hour_ago = datetime.utcnow().replace(microsecond=0).replace(second=0).replace(minute=0)
        recent_activities = [e for e in self.log_entries if e.timestamp >= one_hour_ago]
        
        return {
            "total_activities": len(self.log_entries),
            "activities_by_type": activities_by_type,
            "activities_by_agent": activities_by_agent,
            "activities_by_level": activities_by_level,
            "recent_activity_count": len(recent_activities),
            "oldest_entry": self.log_entries[0].timestamp.isoformat() if self.log_entries else None,
            "newest_entry": self.log_entries[-1].timestamp.isoformat() if self.log_entries else None
        }
    
    def clear_logs(self):
        """Clear all log entries"""
        self.log_entries.clear()
        self.logger.info("Agent activity logs cleared")

# Global logger instance
agent_logger = AgentLogger()