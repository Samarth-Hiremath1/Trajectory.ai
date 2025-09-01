"""
Agent Orchestrator Service for coordinating multiple agents
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

from models.agent import (
    AgentType, AgentRequest, AgentResponse, AgentWorkflow, WorkflowStep,
    RequestType, RequestStatus, WorkflowStatus, RequestAnalysis,
    AgentCollaboration, MessageType
)
from services.base_agent import BaseAgent
from services.agent_communication_bus import AgentCommunicationBus
from services.ai_service import AIService
from services.agent_logger import agent_logger, ActivityType, LogLevel
from services.agent_performance_monitor import AgentPerformanceMonitor
from services.agent_load_balancer import AgentLoadBalancer
from services.agent_learning_system import AgentLearningSystem
from services.agent_conflict_resolution import AgentConflictResolver

logger = logging.getLogger(__name__)

class AgentOrchestratorService:
    """
    Orchestrator service for coordinating multiple specialized agents.
    Manages agent workflows, request routing, and response synthesis.
    """
    
    def __init__(self, ai_service: AIService):
        """
        Initialize the orchestrator service
        
        Args:
            ai_service: AI service instance for LLM interactions
        """
        self.ai_service = ai_service
        
        # Agent management
        self.agents: Dict[str, BaseAgent] = {}
        self.agents_by_type: Dict[AgentType, List[BaseAgent]] = {}
        
        # Communication
        self.communication_bus = AgentCommunicationBus()
        
        # Workflow management
        self.active_workflows: Dict[str, AgentWorkflow] = {}
        self.workflow_history: List[AgentWorkflow] = []
        
        # Request routing rules
        self.routing_rules = self._initialize_routing_rules()
        
        # Performance and optimization systems
        self.performance_monitor = AgentPerformanceMonitor()
        self.load_balancer = AgentLoadBalancer(self.performance_monitor)
        self.learning_system = AgentLearningSystem(ai_service)
        self.conflict_resolver = AgentConflictResolver(ai_service)
        
        # Performance tracking
        self.orchestrator_metrics = {
            "total_requests": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_workflow_time": 0.0,
            "agent_utilization": {}
        }
        
        logger.info("Agent Orchestrator Service initialized with performance monitoring and optimization")
    
    async def start(self):
        """Start the orchestrator service"""
        await self.communication_bus.start()
        await self.performance_monitor.start_monitoring()
        await self.learning_system.start_learning()
        logger.info("Agent Orchestrator Service started with all monitoring systems")
    
    async def stop(self):
        """Stop the orchestrator service"""
        # Stop all active workflows
        for workflow in self.active_workflows.values():
            workflow.status = WorkflowStatus.CANCELLED
        
        # Shutdown all agents
        for agent in self.agents.values():
            await agent.shutdown()
        
        await self.communication_bus.stop()
        logger.info("Agent Orchestrator Service stopped")
    
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the orchestrator
        
        Args:
            agent: The agent instance to register
        """
        self.agents[agent.agent_id] = agent
        
        # Add to type-based registry
        if agent.agent_type not in self.agents_by_type:
            self.agents_by_type[agent.agent_type] = []
        self.agents_by_type[agent.agent_type].append(agent)
        
        # Register with communication bus
        self.communication_bus.register_agent(agent.agent_id, agent)
        
        # Register with load balancer
        self.load_balancer.register_agent(agent)
        
        logger.info(f"Registered agent {agent.agent_id} of type {agent.agent_type.value}")
    
    def unregister_agent(self, agent_id: str):
        """
        Unregister an agent from the orchestrator
        
        Args:
            agent_id: ID of the agent to unregister
        """
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            
            # Remove from type-based registry
            if agent.agent_type in self.agents_by_type:
                self.agents_by_type[agent.agent_type] = [
                    a for a in self.agents_by_type[agent.agent_type] 
                    if a.agent_id != agent_id
                ]
            
            # Remove from main registry
            del self.agents[agent_id]
            
            # Unregister from communication bus
            self.communication_bus.unregister_agent(agent_id)
            
            # Unregister from load balancer
            self.load_balancer.unregister_agent(agent_id)
            
            logger.info(f"Unregistered agent {agent_id}")
    
    async def process_request(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Process a request by coordinating multiple agents
        
        Args:
            request: The request to process
            
        Returns:
            Dictionary with the final response and workflow information
        """
        try:
            self.orchestrator_metrics["total_requests"] += 1
            
            # Analyze the request
            analysis = await self._analyze_request(request)
            
            # Create workflow
            workflow = await self._create_workflow(request, analysis)
            
            # Execute workflow
            result = await self._execute_workflow(workflow)
            
            # Update metrics
            if result["success"]:
                self.orchestrator_metrics["successful_workflows"] += 1
            else:
                self.orchestrator_metrics["failed_workflows"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process request {request.id}: {str(e)}")
            self.orchestrator_metrics["failed_workflows"] += 1
            
            return {
                "success": False,
                "error": str(e),
                "request_id": request.id,
                "workflow_id": None,
                "responses": []
            }
    
    async def _analyze_request(self, request: AgentRequest) -> RequestAnalysis:
        """
        Analyze a request to determine required agents and complexity
        
        Args:
            request: The request to analyze
            
        Returns:
            RequestAnalysis with analysis results
        """
        # Get routing rules for request type
        routing_rule = self.routing_rules.get(request.request_type, {})
        required_agents = routing_rule.get("required_agents", [])
        
        # Calculate complexity based on request content
        complexity_score = self._calculate_complexity(request)
        
        # Estimate processing time
        estimated_time = self._estimate_processing_time(request, required_agents)
        
        # Assess success probability
        success_probability = self._assess_success_probability(request, required_agents)
        
        return RequestAnalysis(
            request_id=request.id,
            complexity_score=complexity_score,
            required_agents=required_agents,
            estimated_processing_time=estimated_time,
            success_probability=success_probability,
            resource_requirements={"agents": len(required_agents)},
            risk_factors=self._identify_risk_factors(request)
        )
    
    async def _create_workflow(self, request: AgentRequest, analysis: RequestAnalysis) -> AgentWorkflow:
        """
        Create a workflow for processing the request
        
        Args:
            request: The original request
            analysis: Request analysis results
            
        Returns:
            AgentWorkflow instance
        """
        workflow_id = str(uuid.uuid4())
        
        # Create workflow steps
        steps = await self._create_workflow_steps(request, analysis)
        
        # Get participating agents
        participating_agents = [step.agent_id for step in steps]
        
        workflow = AgentWorkflow(
            id=workflow_id,
            request_id=request.id,
            orchestrator_id="orchestrator",
            participating_agents=participating_agents,
            workflow_steps=[step.model_dump() for step in steps],
            status=WorkflowStatus.CREATED,
            metadata={
                "request_type": request.request_type.value,
                "complexity_score": analysis.complexity_score,
                "estimated_time": analysis.estimated_processing_time,
                "user_id": request.user_id
            }
        )
        
        self.active_workflows[workflow_id] = workflow
        
        # Log workflow creation
        agent_logger.log_workflow_started(
            orchestrator_id="orchestrator",
            workflow_id=workflow_id,
            request_type=request.request_type.value,
            participating_agents=participating_agents,
            user_id=request.user_id
        )
        
        logger.info(f"Created workflow {workflow_id} with {len(steps)} steps")
        
        return workflow
    
    async def _create_workflow_steps(self, request: AgentRequest, analysis: RequestAnalysis) -> List[WorkflowStep]:
        """
        Create workflow steps based on request analysis
        
        Args:
            request: The original request
            analysis: Request analysis results
            
        Returns:
            List of WorkflowStep instances
        """
        steps = []
        
        for i, agent_type in enumerate(analysis.required_agents):
            # Find available agent of this type
            available_agents = self.agents_by_type.get(agent_type, [])
            if not available_agents:
                logger.warning(f"No agents available for type {agent_type}")
                continue
            
            # Select best agent (for now, just pick the first available one)
            selected_agent = self._select_best_agent(available_agents, request)
            
            if selected_agent:
                step = WorkflowStep(
                    agent_id=selected_agent.agent_id,
                    agent_type=agent_type,
                    step_name=f"Process with {agent_type.value}",
                    input_data={
                        "request": request.model_dump(),
                        "context": request.context,
                        "step_index": i
                    }
                )
                steps.append(step)
        
        return steps
    
    async def _execute_workflow(self, workflow: AgentWorkflow) -> Dict[str, Any]:
        """
        Execute a workflow by coordinating agent steps
        
        Args:
            workflow: The workflow to execute
            
        Returns:
            Dictionary with execution results
        """
        start_time = datetime.utcnow()
        workflow.status = WorkflowStatus.RUNNING
        
        try:
            responses = []
            
            # Execute steps (for now, sequentially - can be made parallel later)
            for step_dict in workflow.workflow_steps:
                # Convert dict back to WorkflowStep object
                step = WorkflowStep(**step_dict)
                step.status = RequestStatus.PROCESSING
                step.started_at = datetime.utcnow()
                
                # Get agent using load balancer
                agent_request = AgentRequest(
                    user_id=workflow.metadata.get("user_id", "system"),
                    request_type=RequestType(workflow.metadata.get("request_type", "career_advice")),
                    content=step.input_data,
                    context=step.input_data.get("context", {})
                )
                
                # Use load balancer to select best agent
                agent = await self.load_balancer.balance_request(
                    agent_request,
                    step.agent_type
                )
                
                if not agent:
                    # Try to get any available agent of the required type
                    available_agents = [a for a in self.agents_by_type.get(step.agent_type, []) if a.is_active]
                    if available_agents:
                        agent = available_agents[0]
                    else:
                        raise Exception(f"No available agents of type {step.agent_type}")
                
                # Record request start for monitoring
                self.performance_monitor.record_request_start(agent_request, agent.agent_id)
                
                # Process with agent
                response = await agent.handle_request(agent_request)
                responses.append(response)
                
                # Record completion for monitoring
                self.performance_monitor.record_request_completion(response)
                
                # Assess response quality and record for learning
                quality_assessment = self.performance_monitor.assess_response_quality(response)
                self.learning_system.record_learning_example(
                    agent_request,
                    response,
                    quality_assessment.quality_score,
                    success_indicators={"workflow_step": True}
                )
                
                # Update step
                step.output_data = response.model_dump()
                step.status = RequestStatus.COMPLETED if response.confidence_score > 0 else RequestStatus.FAILED
                step.completed_at = datetime.utcnow()
                
                # Update the step in workflow
                for i, ws in enumerate(workflow.workflow_steps):
                    if ws["step_id"] == step.step_id:
                        workflow.workflow_steps[i] = step.model_dump()
                        break
                
                logger.info(f"Completed workflow step with agent {step.agent_id}")
            
            # Detect and resolve conflicts between responses
            if len(responses) > 1:
                conflicts = await self.conflict_resolver.detect_conflicts(responses)
                if conflicts:
                    logger.info(f"Detected {len(conflicts)} conflicts in workflow {workflow.id}")
                    # Build consensus to resolve conflicts
                    consensus_result = await self.conflict_resolver.build_consensus(responses)
                    final_response = consensus_result.consensus_response
                else:
                    # No conflicts, synthesize normally
                    final_response = await self._synthesize_responses(responses, workflow)
            else:
                # Single response, no synthesis needed
                final_response = responses[0].response_content if responses else {}
            
            # Update workflow
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            
            # Move to history
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow.id]
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_workflow_metrics(execution_time)
            
            # Log workflow completion
            agent_logger.log_workflow_completed(
                orchestrator_id="orchestrator",
                workflow_id=workflow.id,
                execution_time=execution_time,
                success=True,
                steps_completed=len([s for s in workflow.workflow_steps if s.get("status") == RequestStatus.COMPLETED.value]),
                user_id=workflow.metadata.get("user_id")
            )
            
            return {
                "success": True,
                "workflow_id": workflow.id,
                "responses": [r.model_dump() for r in responses],
                "final_response": final_response,
                "execution_time": execution_time,
                "steps_completed": len([s for s in workflow.workflow_steps if s.get("status") == RequestStatus.COMPLETED.value])
            }
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.utcnow()
            
            logger.error(f"Workflow {workflow.id} failed: {str(e)}")
            
            return {
                "success": False,
                "workflow_id": workflow.id,
                "error": str(e),
                "responses": [],
                "execution_time": (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def _synthesize_responses(self, responses: List[AgentResponse], workflow: AgentWorkflow) -> Dict[str, Any]:
        """
        Synthesize multiple agent responses into a final response
        
        Args:
            responses: List of agent responses
            workflow: The workflow context
            
        Returns:
            Synthesized final response
        """
        if not responses:
            return {"error": "No responses to synthesize"}
        
        if len(responses) == 1:
            return responses[0].response_content
        
        # Combine responses using AI
        synthesis_prompt = self._create_synthesis_prompt(responses, workflow)
        
        try:
            synthesized_content = await self.ai_service.generate_text(
                prompt=synthesis_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            return {
                "synthesized_response": synthesized_content,
                "individual_responses": [r.response_content for r in responses],
                "confidence_scores": [r.confidence_score for r in responses],
                "average_confidence": sum(r.confidence_score for r in responses) / len(responses)
            }
            
        except Exception as e:
            logger.error(f"Failed to synthesize responses: {str(e)}")
            
            # Fallback: return the response with highest confidence
            best_response = max(responses, key=lambda r: r.confidence_score)
            return {
                "response": best_response.response_content,
                "source_agent": best_response.agent_id,
                "confidence": best_response.confidence_score,
                "synthesis_failed": True
            }
    
    def _create_synthesis_prompt(self, responses: List[AgentResponse], workflow: AgentWorkflow) -> str:
        """Create prompt for synthesizing multiple agent responses"""
        prompt_parts = [
            "You are an AI coordinator tasked with synthesizing responses from multiple specialized agents.",
            f"Request type: {workflow.metadata.get('request_type', 'unknown')}",
            "",
            "Agent responses to synthesize:"
        ]
        
        for i, response in enumerate(responses, 1):
            prompt_parts.extend([
                f"\nAgent {i} ({response.agent_type.value}):",
                f"Confidence: {response.confidence_score:.2f}",
                f"Response: {response.response_content}",
                ""
            ])
        
        prompt_parts.extend([
            "Please synthesize these responses into a coherent, comprehensive answer that:",
            "1. Combines the best insights from each agent",
            "2. Resolves any conflicts or contradictions",
            "3. Provides a clear, actionable response",
            "4. Maintains the expertise and specificity of the individual responses",
            "",
            "Synthesized response:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _select_best_agent(self, available_agents: List[BaseAgent], request: AgentRequest) -> Optional[BaseAgent]:
        """
        Select the best agent from available options
        
        Args:
            available_agents: List of available agents
            request: The request to process
            
        Returns:
            Selected agent or None if none suitable
        """
        # For now, simple selection based on load and availability
        suitable_agents = [agent for agent in available_agents if agent.can_handle_request(request)]
        
        if not suitable_agents:
            return None
        
        # Select agent with lowest current load
        return min(suitable_agents, key=lambda a: a.current_load)
    
    def _initialize_routing_rules(self) -> Dict[RequestType, Dict[str, Any]]:
        """Initialize request routing rules"""
        return {
            RequestType.ROADMAP_GENERATION: {
                "required_agents": [AgentType.CAREER_STRATEGY, AgentType.SKILLS_ANALYSIS, AgentType.LEARNING_RESOURCE],
                "parallel": False
            },
            RequestType.SKILL_ANALYSIS: {
                "required_agents": [AgentType.SKILLS_ANALYSIS],
                "parallel": False
            },
            RequestType.RESUME_REVIEW: {
                "required_agents": [AgentType.RESUME_OPTIMIZATION, AgentType.SKILLS_ANALYSIS],
                "parallel": True
            },
            RequestType.CAREER_ADVICE: {
                "required_agents": [AgentType.CAREER_STRATEGY, AgentType.CAREER_MENTOR],
                "parallel": False
            },
            RequestType.LEARNING_PATH: {
                "required_agents": [AgentType.LEARNING_RESOURCE, AgentType.SKILLS_ANALYSIS],
                "parallel": False
            },
            RequestType.INTERVIEW_PREP: {
                "required_agents": [AgentType.CAREER_MENTOR, AgentType.SKILLS_ANALYSIS],
                "parallel": False
            },
            RequestType.CAREER_TRANSITION: {
                "required_agents": [AgentType.CAREER_STRATEGY, AgentType.SKILLS_ANALYSIS, AgentType.CAREER_MENTOR],
                "parallel": False
            }
        }
    
    def _calculate_complexity(self, request: AgentRequest) -> float:
        """Calculate request complexity score (0.0 to 1.0)"""
        # Simple complexity calculation based on content size and type
        content_size = len(str(request.content))
        base_complexity = min(content_size / 1000, 0.5)  # Max 0.5 for content size
        
        # Add complexity based on request type
        type_complexity = {
            RequestType.CAREER_ADVICE: 0.2,
            RequestType.SKILL_ANALYSIS: 0.3,
            RequestType.RESUME_REVIEW: 0.4,
            RequestType.LEARNING_PATH: 0.5,
            RequestType.INTERVIEW_PREP: 0.6,
            RequestType.ROADMAP_GENERATION: 0.8,
            RequestType.CAREER_TRANSITION: 0.9
        }.get(request.request_type, 0.5)
        
        return min(base_complexity + type_complexity, 1.0)
    
    def _estimate_processing_time(self, request: AgentRequest, required_agents: List[AgentType]) -> int:
        """Estimate processing time in seconds"""
        base_time = 10  # Base processing time
        agent_time = len(required_agents) * 5  # 5 seconds per agent
        complexity_multiplier = 1 + self._calculate_complexity(request)
        
        return int((base_time + agent_time) * complexity_multiplier)
    
    def _assess_success_probability(self, request: AgentRequest, required_agents: List[AgentType]) -> float:
        """Assess probability of successful processing"""
        # Check agent availability
        available_count = sum(1 for agent_type in required_agents if agent_type in self.agents_by_type)
        availability_score = available_count / max(len(required_agents), 1)
        
        # Base success rate
        base_success = 0.8
        
        return min(base_success * availability_score, 1.0)
    
    def _identify_risk_factors(self, request: AgentRequest) -> List[str]:
        """Identify potential risk factors for request processing"""
        risks = []
        
        # Check for missing agents
        routing_rule = self.routing_rules.get(request.request_type, {})
        required_agents = routing_rule.get("required_agents", [])
        
        for agent_type in required_agents:
            if agent_type not in self.agents_by_type or not self.agents_by_type[agent_type]:
                risks.append(f"No {agent_type.value} agent available")
        
        # Check system load
        total_load = sum(agent.current_load for agent in self.agents.values())
        if total_load > len(self.agents) * 2:  # Average load > 2
            risks.append("High system load")
        
        return risks
    
    def _update_workflow_metrics(self, execution_time: float):
        """Update workflow execution metrics"""
        successful_workflows = self.orchestrator_metrics["successful_workflows"]
        
        if successful_workflows <= 1:
            self.orchestrator_metrics["average_workflow_time"] = execution_time
        else:
            current_avg = self.orchestrator_metrics["average_workflow_time"]
            total_time = current_avg * (successful_workflows - 1)
            self.orchestrator_metrics["average_workflow_time"] = (total_time + execution_time) / successful_workflows
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status and metrics"""
        return {
            "registered_agents": len(self.agents),
            "agents_by_type": {
                agent_type.value: len(agents) 
                for agent_type, agents in self.agents_by_type.items()
            },
            "active_workflows": len(self.active_workflows),
            "workflow_history_size": len(self.workflow_history),
            "metrics": self.orchestrator_metrics,
            "communication_stats": self.communication_bus.get_statistics(),
            "performance_summary": self.performance_monitor.get_system_performance_summary(),
            "load_balancing_status": self.load_balancer.get_load_balancing_status(),
            "learning_metrics": self.learning_system.get_learning_metrics(),
            "conflict_status": self.conflict_resolver.get_conflict_status()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        return {
            "system_performance": self.performance_monitor.get_system_performance_summary(),
            "load_balancing": self.load_balancer.get_load_balancing_status(),
            "learning_system": self.learning_system.get_learning_metrics(),
            "conflict_resolution": self.conflict_resolver.get_conflict_status(),
            "performance_alerts": self.performance_monitor.get_performance_alerts()
        }
    
    async def optimize_system_performance(self) -> Dict[str, Any]:
        """Trigger system performance optimization"""
        optimization_results = {}
        
        try:
            # Rebalance load across agents
            await self.load_balancer.rebalance_load()
            optimization_results["load_rebalancing"] = "completed"
            
            # Generate improvement suggestions for underperforming agents
            underperforming_agents = self.performance_monitor._get_underperforming_agents(5)
            improvement_count = 0
            
            for agent_info in underperforming_agents:
                agent_id = agent_info["agent_id"]
                suggestions = await self.learning_system.generate_improvement_suggestions(agent_id)
                improvement_count += len(suggestions)
            
            optimization_results["improvement_suggestions"] = improvement_count
            
            # Clear old performance alerts
            self.performance_monitor.clear_performance_alerts()
            optimization_results["alerts_cleared"] = True
            
            logger.info("System performance optimization completed")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Failed to optimize system performance: {str(e)}")
            return {"error": str(e)}
    
    async def apply_agent_improvements(self, agent_id: str) -> Dict[str, Any]:
        """Apply pending improvements for a specific agent"""
        try:
            suggestions = self.learning_system.improvement_suggestions.get(agent_id, [])
            
            if not suggestions:
                return {"message": "No pending improvements for agent", "applied": 0}
            
            applied_count = 0
            for suggestion in suggestions[:3]:  # Apply top 3 suggestions
                if suggestion.confidence >= 0.6:  # Only apply high-confidence suggestions
                    success = await self.learning_system.apply_improvement(agent_id, suggestion)
                    if success:
                        applied_count += 1
            
            # Clear applied suggestions
            if applied_count > 0:
                self.learning_system.improvement_suggestions[agent_id] = suggestions[applied_count:]
            
            return {
                "agent_id": agent_id,
                "improvements_applied": applied_count,
                "remaining_suggestions": len(self.learning_system.improvement_suggestions.get(agent_id, []))
            }
            
        except Exception as e:
            logger.error(f"Failed to apply improvements for agent {agent_id}: {str(e)}")
            return {"error": str(e)}