"""
Agent Performance Monitoring Service
Tracks and analyzes agent performance metrics, response quality, and system optimization
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
import statistics
import json

from models.agent import (
    AgentType, AgentRequest, AgentResponse, AgentStatus,
    RequestType, RequestStatus, WorkflowStatus
)

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric data point"""
    timestamp: datetime
    agent_id: str
    agent_type: AgentType
    metric_name: str
    value: float
    metadata: Dict[str, Any]

@dataclass
class QualityAssessment:
    """Quality assessment for an agent response"""
    response_id: str
    agent_id: str
    quality_score: float  # 0.0 to 1.0
    assessment_criteria: Dict[str, float]
    feedback: str
    timestamp: datetime

@dataclass
class AgentPerformanceProfile:
    """Comprehensive performance profile for an agent"""
    agent_id: str
    agent_type: AgentType
    
    # Performance metrics
    avg_response_time: float
    success_rate: float
    avg_confidence: float
    throughput: float  # requests per minute
    
    # Quality metrics
    avg_quality_score: float
    consistency_score: float
    reliability_score: float
    
    # Load metrics
    current_load: int
    peak_load: int
    load_efficiency: float
    
    # Trend analysis
    performance_trend: str  # "improving", "stable", "declining"
    last_updated: datetime

class AgentPerformanceMonitor:
    """
    Service for monitoring and analyzing agent performance
    """
    
    def __init__(self, history_window_hours: int = 24):
        """
        Initialize performance monitor
        
        Args:
            history_window_hours: Hours of history to maintain for analysis
        """
        self.history_window = timedelta(hours=history_window_hours)
        
        # Performance data storage
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.quality_assessments: Dict[str, List[QualityAssessment]] = defaultdict(list)
        self.agent_profiles: Dict[str, AgentPerformanceProfile] = {}
        
        # Real-time monitoring
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.performance_alerts: List[Dict[str, Any]] = []
        
        # System-wide metrics
        self.system_metrics = {
            "total_requests_processed": 0,
            "average_system_response_time": 0.0,
            "system_success_rate": 0.0,
            "peak_concurrent_requests": 0,
            "agent_utilization": {}
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            "response_time_warning": 10.0,  # seconds
            "response_time_critical": 30.0,
            "success_rate_warning": 0.8,
            "success_rate_critical": 0.6,
            "quality_score_warning": 0.7,
            "quality_score_critical": 0.5
        }
        
        logger.info("Agent Performance Monitor initialized")
    
    async def start_monitoring(self):
        """Start the performance monitoring service"""
        # Start background tasks
        asyncio.create_task(self._cleanup_old_data())
        asyncio.create_task(self._update_agent_profiles())
        asyncio.create_task(self._detect_performance_issues())
        
        logger.info("Performance monitoring started")
    
    def record_request_start(self, request: AgentRequest, agent_id: str):
        """
        Record the start of request processing
        
        Args:
            request: The agent request
            agent_id: ID of the agent processing the request
        """
        self.active_requests[request.id] = {
            "agent_id": agent_id,
            "agent_type": None,  # Will be filled when we have agent info
            "request_type": request.request_type,
            "start_time": datetime.utcnow(),
            "user_id": request.user_id,
            "priority": request.priority
        }
    
    def record_request_completion(self, response: AgentResponse):
        """
        Record the completion of request processing
        
        Args:
            response: The agent response
        """
        request_info = self.active_requests.get(response.request_id)
        if not request_info:
            logger.warning(f"No active request found for response {response.id}")
            return
        
        # Calculate metrics
        end_time = datetime.utcnow()
        processing_time = response.processing_time
        
        # Record performance metrics
        self._record_metric(
            agent_id=response.agent_id,
            agent_type=response.agent_type,
            metric_name="response_time",
            value=processing_time,
            metadata={
                "request_type": request_info["request_type"].value,
                "success": response.confidence_score > 0,
                "user_id": request_info.get("user_id")
            }
        )
        
        self._record_metric(
            agent_id=response.agent_id,
            agent_type=response.agent_type,
            metric_name="confidence_score",
            value=response.confidence_score,
            metadata={
                "request_type": request_info["request_type"].value
            }
        )
        
        # Update system metrics
        self.system_metrics["total_requests_processed"] += 1
        
        # Remove from active requests
        del self.active_requests[response.request_id]
        
        logger.debug(f"Recorded completion for request {response.request_id}")
    
    def record_request_failure(self, request_id: str, agent_id: str, error: str):
        """
        Record a failed request
        
        Args:
            request_id: ID of the failed request
            agent_id: ID of the agent that failed
            error: Error message
        """
        request_info = self.active_requests.get(request_id)
        if request_info:
            processing_time = (datetime.utcnow() - request_info["start_time"]).total_seconds()
            
            # Record failure metrics
            self._record_metric(
                agent_id=agent_id,
                agent_type=request_info.get("agent_type"),
                metric_name="failure",
                value=1.0,
                metadata={
                    "error": error,
                    "processing_time": processing_time,
                    "request_type": request_info["request_type"].value
                }
            )
            
            # Remove from active requests
            del self.active_requests[request_id]
    
    def assess_response_quality(
        self,
        response: AgentResponse,
        assessment_criteria: Optional[Dict[str, float]] = None
    ) -> QualityAssessment:
        """
        Assess the quality of an agent response
        
        Args:
            response: The agent response to assess
            assessment_criteria: Custom criteria for assessment
            
        Returns:
            QualityAssessment object
        """
        if assessment_criteria is None:
            assessment_criteria = self._get_default_quality_criteria(response)
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(response, assessment_criteria)
        
        # Generate feedback
        feedback = self._generate_quality_feedback(response, assessment_criteria, quality_score)
        
        assessment = QualityAssessment(
            response_id=response.id,
            agent_id=response.agent_id,
            quality_score=quality_score,
            assessment_criteria=assessment_criteria,
            feedback=feedback,
            timestamp=datetime.utcnow()
        )
        
        # Store assessment
        self.quality_assessments[response.agent_id].append(assessment)
        
        # Keep only recent assessments
        cutoff_time = datetime.utcnow() - self.history_window
        self.quality_assessments[response.agent_id] = [
            a for a in self.quality_assessments[response.agent_id]
            if a.timestamp > cutoff_time
        ]
        
        return assessment
    
    def get_agent_performance_profile(self, agent_id: str) -> Optional[AgentPerformanceProfile]:
        """
        Get comprehensive performance profile for an agent
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            AgentPerformanceProfile or None if not found
        """
        return self.agent_profiles.get(agent_id)
    
    def get_system_performance_summary(self) -> Dict[str, Any]:
        """
        Get system-wide performance summary
        
        Returns:
            Dictionary with system performance metrics
        """
        # Calculate current system metrics
        active_agents = len(set(req["agent_id"] for req in self.active_requests.values()))
        current_load = len(self.active_requests)
        
        # Get recent performance data
        recent_metrics = self._get_recent_system_metrics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_agents": active_agents,
            "current_concurrent_requests": current_load,
            "peak_concurrent_requests": self.system_metrics["peak_concurrent_requests"],
            "total_requests_processed": self.system_metrics["total_requests_processed"],
            "average_response_time": recent_metrics.get("avg_response_time", 0.0),
            "system_success_rate": recent_metrics.get("success_rate", 0.0),
            "agent_utilization": self._calculate_agent_utilization(),
            "performance_alerts": len(self.performance_alerts),
            "top_performing_agents": self._get_top_performing_agents(5),
            "underperforming_agents": self._get_underperforming_agents(5)
        }
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """
        Get current performance alerts
        
        Returns:
            List of performance alerts
        """
        return self.performance_alerts.copy()
    
    def clear_performance_alerts(self):
        """Clear all performance alerts"""
        self.performance_alerts.clear()
        logger.info("Performance alerts cleared")
    
    def _record_metric(
        self,
        agent_id: str,
        agent_type: Optional[AgentType],
        metric_name: str,
        value: float,
        metadata: Dict[str, Any]
    ):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            agent_type=agent_type,
            metric_name=metric_name,
            value=value,
            metadata=metadata
        )
        
        self.metrics_history[agent_id].append(metric)
    
    def _get_default_quality_criteria(self, response: AgentResponse) -> Dict[str, float]:
        """Get default quality assessment criteria based on response type"""
        base_criteria = {
            "relevance": 0.3,      # How relevant is the response to the request
            "completeness": 0.25,   # How complete is the response
            "accuracy": 0.25,       # How accurate is the information
            "clarity": 0.2          # How clear and well-structured is the response
        }
        
        # Adjust criteria based on agent type
        if response.agent_type == AgentType.CAREER_STRATEGY:
            base_criteria.update({
                "strategic_depth": 0.15,
                "actionability": 0.15
            })
        elif response.agent_type == AgentType.SKILLS_ANALYSIS:
            base_criteria.update({
                "analytical_depth": 0.15,
                "specificity": 0.15
            })
        elif response.agent_type == AgentType.LEARNING_RESOURCE:
            base_criteria.update({
                "resource_quality": 0.15,
                "personalization": 0.15
            })
        
        return base_criteria
    
    def _calculate_quality_score(
        self,
        response: AgentResponse,
        criteria: Dict[str, float]
    ) -> float:
        """Calculate quality score based on response and criteria"""
        # This is a simplified quality assessment
        # In a real implementation, this would use more sophisticated analysis
        
        base_score = response.confidence_score
        
        # Adjust based on response content analysis
        content = response.response_content
        
        # Check for error indicators
        if isinstance(content, dict) and content.get("error"):
            return 0.1
        
        # Check response length and structure
        content_str = str(content)
        length_score = min(len(content_str) / 500, 1.0)  # Normalize to 500 chars
        
        # Check for structured content
        structure_score = 0.8 if isinstance(content, dict) else 0.6
        
        # Combine scores
        quality_score = (
            base_score * 0.4 +
            length_score * 0.3 +
            structure_score * 0.3
        )
        
        return min(quality_score, 1.0)
    
    def _generate_quality_feedback(
        self,
        response: AgentResponse,
        criteria: Dict[str, float],
        quality_score: float
    ) -> str:
        """Generate feedback based on quality assessment"""
        if quality_score >= 0.8:
            return "Excellent response quality. Well-structured and comprehensive."
        elif quality_score >= 0.6:
            return "Good response quality. Minor improvements possible in detail or structure."
        elif quality_score >= 0.4:
            return "Moderate response quality. Consider improving completeness and clarity."
        else:
            return "Poor response quality. Significant improvements needed in content and structure."
    
    async def _cleanup_old_data(self):
        """Background task to clean up old performance data"""
        while True:
            try:
                cutoff_time = datetime.utcnow() - self.history_window
                
                # Clean up metrics history
                for agent_id in list(self.metrics_history.keys()):
                    metrics = self.metrics_history[agent_id]
                    # Remove old metrics
                    while metrics and metrics[0].timestamp < cutoff_time:
                        metrics.popleft()
                    
                    # Remove empty queues
                    if not metrics:
                        del self.metrics_history[agent_id]
                
                # Clean up quality assessments
                for agent_id in list(self.quality_assessments.keys()):
                    assessments = self.quality_assessments[agent_id]
                    self.quality_assessments[agent_id] = [
                        a for a in assessments if a.timestamp > cutoff_time
                    ]
                    
                    if not self.quality_assessments[agent_id]:
                        del self.quality_assessments[agent_id]
                
                # Clean up old alerts
                self.performance_alerts = [
                    alert for alert in self.performance_alerts
                    if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
                ]
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _update_agent_profiles(self):
        """Background task to update agent performance profiles"""
        while True:
            try:
                for agent_id in self.metrics_history.keys():
                    profile = self._calculate_agent_profile(agent_id)
                    if profile:
                        self.agent_profiles[agent_id] = profile
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error updating agent profiles: {str(e)}")
                await asyncio.sleep(60)
    
    async def _detect_performance_issues(self):
        """Background task to detect performance issues and generate alerts"""
        while True:
            try:
                # Check for performance issues
                for agent_id, profile in self.agent_profiles.items():
                    self._check_agent_performance_thresholds(profile)
                
                # Check system-wide issues
                self._check_system_performance_thresholds()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in performance issue detection: {str(e)}")
                await asyncio.sleep(30)
    
    def _calculate_agent_profile(self, agent_id: str) -> Optional[AgentPerformanceProfile]:
        """Calculate comprehensive performance profile for an agent"""
        metrics = list(self.metrics_history[agent_id])
        if not metrics:
            return None
        
        # Get agent type from most recent metric
        agent_type = next((m.agent_type for m in reversed(metrics) if m.agent_type), None)
        if not agent_type:
            return None
        
        # Calculate performance metrics
        response_times = [m.value for m in metrics if m.metric_name == "response_time"]
        confidence_scores = [m.value for m in metrics if m.metric_name == "confidence_score"]
        failures = [m for m in metrics if m.metric_name == "failure"]
        
        avg_response_time = statistics.mean(response_times) if response_times else 0.0
        avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
        
        total_requests = len(response_times) + len(failures)
        success_rate = len(response_times) / total_requests if total_requests > 0 else 0.0
        
        # Calculate throughput (requests per minute)
        if metrics:
            time_span = (metrics[-1].timestamp - metrics[0].timestamp).total_seconds() / 60
            throughput = total_requests / max(time_span, 1.0)
        else:
            throughput = 0.0
        
        # Calculate quality metrics
        quality_assessments = self.quality_assessments.get(agent_id, [])
        avg_quality_score = statistics.mean([a.quality_score for a in quality_assessments]) if quality_assessments else 0.0
        
        # Calculate consistency (standard deviation of quality scores)
        if len(quality_assessments) > 1:
            quality_scores = [a.quality_score for a in quality_assessments]
            consistency_score = 1.0 - min(statistics.stdev(quality_scores), 1.0)
        else:
            consistency_score = 1.0
        
        # Calculate reliability (success rate weighted by quality)
        reliability_score = success_rate * avg_quality_score
        
        # Determine performance trend
        performance_trend = self._calculate_performance_trend(agent_id)
        
        return AgentPerformanceProfile(
            agent_id=agent_id,
            agent_type=agent_type,
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            avg_confidence=avg_confidence,
            throughput=throughput,
            avg_quality_score=avg_quality_score,
            consistency_score=consistency_score,
            reliability_score=reliability_score,
            current_load=0,  # This would be updated from agent status
            peak_load=0,     # This would be tracked separately
            load_efficiency=reliability_score / max(avg_response_time, 1.0),
            performance_trend=performance_trend,
            last_updated=datetime.utcnow()
        )
    
    def _calculate_performance_trend(self, agent_id: str) -> str:
        """Calculate performance trend for an agent"""
        metrics = list(self.metrics_history[agent_id])
        if len(metrics) < 10:
            return "stable"
        
        # Get recent vs older metrics
        mid_point = len(metrics) // 2
        older_metrics = metrics[:mid_point]
        recent_metrics = metrics[mid_point:]
        
        # Compare average response times
        older_avg = statistics.mean([m.value for m in older_metrics if m.metric_name == "response_time"])
        recent_avg = statistics.mean([m.value for m in recent_metrics if m.metric_name == "response_time"])
        
        if recent_avg < older_avg * 0.9:
            return "improving"
        elif recent_avg > older_avg * 1.1:
            return "declining"
        else:
            return "stable"
    
    def _check_agent_performance_thresholds(self, profile: AgentPerformanceProfile):
        """Check if agent performance exceeds thresholds and generate alerts"""
        alerts = []
        
        # Check response time
        if profile.avg_response_time > self.performance_thresholds["response_time_critical"]:
            alerts.append({
                "type": "critical",
                "agent_id": profile.agent_id,
                "metric": "response_time",
                "value": profile.avg_response_time,
                "threshold": self.performance_thresholds["response_time_critical"],
                "message": f"Agent {profile.agent_id} has critically high response time"
            })
        elif profile.avg_response_time > self.performance_thresholds["response_time_warning"]:
            alerts.append({
                "type": "warning",
                "agent_id": profile.agent_id,
                "metric": "response_time",
                "value": profile.avg_response_time,
                "threshold": self.performance_thresholds["response_time_warning"],
                "message": f"Agent {profile.agent_id} has high response time"
            })
        
        # Check success rate
        if profile.success_rate < self.performance_thresholds["success_rate_critical"]:
            alerts.append({
                "type": "critical",
                "agent_id": profile.agent_id,
                "metric": "success_rate",
                "value": profile.success_rate,
                "threshold": self.performance_thresholds["success_rate_critical"],
                "message": f"Agent {profile.agent_id} has critically low success rate"
            })
        elif profile.success_rate < self.performance_thresholds["success_rate_warning"]:
            alerts.append({
                "type": "warning",
                "agent_id": profile.agent_id,
                "metric": "success_rate",
                "value": profile.success_rate,
                "threshold": self.performance_thresholds["success_rate_warning"],
                "message": f"Agent {profile.agent_id} has low success rate"
            })
        
        # Add alerts with timestamp
        for alert in alerts:
            alert["timestamp"] = datetime.utcnow().isoformat()
            self.performance_alerts.append(alert)
    
    def _check_system_performance_thresholds(self):
        """Check system-wide performance thresholds"""
        # Update peak concurrent requests
        current_load = len(self.active_requests)
        if current_load > self.system_metrics["peak_concurrent_requests"]:
            self.system_metrics["peak_concurrent_requests"] = current_load
        
        # Check for system overload
        if current_load > 50:  # Arbitrary threshold
            self.performance_alerts.append({
                "type": "warning",
                "metric": "system_load",
                "value": current_load,
                "threshold": 50,
                "message": f"System has high concurrent load: {current_load} requests",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def _get_recent_system_metrics(self) -> Dict[str, float]:
        """Calculate recent system-wide metrics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        all_recent_metrics = []
        for metrics in self.metrics_history.values():
            recent_metrics = [m for m in metrics if m.timestamp > cutoff_time]
            all_recent_metrics.extend(recent_metrics)
        
        if not all_recent_metrics:
            return {}
        
        response_times = [m.value for m in all_recent_metrics if m.metric_name == "response_time"]
        failures = [m for m in all_recent_metrics if m.metric_name == "failure"]
        
        total_requests = len(response_times) + len(failures)
        success_rate = len(response_times) / total_requests if total_requests > 0 else 0.0
        avg_response_time = statistics.mean(response_times) if response_times else 0.0
        
        return {
            "success_rate": success_rate,
            "avg_response_time": avg_response_time
        }
    
    def _calculate_agent_utilization(self) -> Dict[str, float]:
        """Calculate current agent utilization"""
        utilization = {}
        
        # Count active requests per agent
        agent_loads = defaultdict(int)
        for req_info in self.active_requests.values():
            agent_loads[req_info["agent_id"]] += 1
        
        # Calculate utilization based on known agent capacities
        for agent_id, load in agent_loads.items():
            # Assume max capacity of 5 for now (this should come from agent status)
            utilization[agent_id] = min(load / 5.0, 1.0)
        
        return utilization
    
    def _get_top_performing_agents(self, limit: int) -> List[Dict[str, Any]]:
        """Get top performing agents"""
        profiles = list(self.agent_profiles.values())
        profiles.sort(key=lambda p: p.reliability_score, reverse=True)
        
        return [
            {
                "agent_id": p.agent_id,
                "agent_type": p.agent_type.value,
                "reliability_score": p.reliability_score,
                "success_rate": p.success_rate,
                "avg_quality_score": p.avg_quality_score
            }
            for p in profiles[:limit]
        ]
    
    def _get_underperforming_agents(self, limit: int) -> List[Dict[str, Any]]:
        """Get underperforming agents"""
        profiles = list(self.agent_profiles.values())
        profiles.sort(key=lambda p: p.reliability_score)
        
        return [
            {
                "agent_id": p.agent_id,
                "agent_type": p.agent_type.value,
                "reliability_score": p.reliability_score,
                "success_rate": p.success_rate,
                "avg_quality_score": p.avg_quality_score,
                "performance_trend": p.performance_trend
            }
            for p in profiles[:limit]
        ]