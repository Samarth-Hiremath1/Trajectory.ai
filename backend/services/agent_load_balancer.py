"""
Agent Load Balancer Service
Manages agent workload distribution and resource optimization
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import heapq
import random

from models.agent import (
    AgentType, AgentRequest, AgentStatus, RequestPriority,
    RequestType, RequestStatus
)
from services.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class LoadBalancingStrategy:
    """Base class for load balancing strategies"""
    
    def select_agent(
        self,
        available_agents: List[BaseAgent],
        request: AgentRequest,
        agent_metrics: Dict[str, Any]
    ) -> Optional[BaseAgent]:
        """
        Select the best agent for a request
        
        Args:
            available_agents: List of available agents
            request: The request to process
            agent_metrics: Current agent performance metrics
            
        Returns:
            Selected agent or None
        """
        raise NotImplementedError

class RoundRobinStrategy(LoadBalancingStrategy):
    """Round-robin load balancing strategy"""
    
    def __init__(self):
        self.last_selected = {}
    
    def select_agent(
        self,
        available_agents: List[BaseAgent],
        request: AgentRequest,
        agent_metrics: Dict[str, Any]
    ) -> Optional[BaseAgent]:
        if not available_agents:
            return None
        
        agent_type = available_agents[0].agent_type
        last_index = self.last_selected.get(agent_type, -1)
        next_index = (last_index + 1) % len(available_agents)
        
        self.last_selected[agent_type] = next_index
        return available_agents[next_index]

class LeastLoadedStrategy(LoadBalancingStrategy):
    """Select agent with lowest current load"""
    
    def select_agent(
        self,
        available_agents: List[BaseAgent],
        request: AgentRequest,
        agent_metrics: Dict[str, Any]
    ) -> Optional[BaseAgent]:
        if not available_agents:
            return None
        
        return min(available_agents, key=lambda agent: agent.current_load)

class WeightedPerformanceStrategy(LoadBalancingStrategy):
    """Select agent based on weighted performance metrics"""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "response_time": -0.3,    # Lower is better
            "success_rate": 0.4,      # Higher is better
            "quality_score": 0.3,     # Higher is better
            "load": -0.2              # Lower is better
        }
    
    def select_agent(
        self,
        available_agents: List[BaseAgent],
        request: AgentRequest,
        agent_metrics: Dict[str, Any]
    ) -> Optional[BaseAgent]:
        if not available_agents:
            return None
        
        scored_agents = []
        
        for agent in available_agents:
            metrics = agent_metrics.get(agent.agent_id, {})
            
            # Calculate weighted score
            score = 0.0
            
            # Response time (normalize to 0-1, invert so lower is better)
            response_time = metrics.get("avg_response_time", 10.0)
            normalized_response_time = min(response_time / 30.0, 1.0)  # 30s max
            score += self.weights["response_time"] * normalized_response_time
            
            # Success rate (0-1, higher is better)
            success_rate = metrics.get("success_rate", 0.5)
            score += self.weights["success_rate"] * success_rate
            
            # Quality score (0-1, higher is better)
            quality_score = metrics.get("avg_quality_score", 0.5)
            score += self.weights["quality_score"] * quality_score
            
            # Current load (normalize to 0-1, lower is better)
            load = agent.current_load / max(agent.max_concurrent_requests, 1)
            score += self.weights["load"] * load
            
            scored_agents.append((score, agent))
        
        # Select agent with highest score
        scored_agents.sort(key=lambda x: x[0], reverse=True)
        return scored_agents[0][1]

class PriorityAwareStrategy(LoadBalancingStrategy):
    """Strategy that considers request priority"""
    
    def __init__(self, base_strategy: LoadBalancingStrategy):
        self.base_strategy = base_strategy
    
    def select_agent(
        self,
        available_agents: List[BaseAgent],
        request: AgentRequest,
        agent_metrics: Dict[str, Any]
    ) -> Optional[BaseAgent]:
        # For high priority requests, prefer agents with better performance
        if request.priority in [RequestPriority.HIGH, RequestPriority.URGENT]:
            # Filter to top-performing agents if available
            top_agents = self._filter_top_performers(available_agents, agent_metrics)
            if top_agents:
                available_agents = top_agents
        
        return self.base_strategy.select_agent(available_agents, request, agent_metrics)
    
    def _filter_top_performers(
        self,
        agents: List[BaseAgent],
        agent_metrics: Dict[str, Any]
    ) -> List[BaseAgent]:
        """Filter to top 50% of agents by performance"""
        if len(agents) <= 2:
            return agents
        
        # Score agents by reliability
        scored_agents = []
        for agent in agents:
            metrics = agent_metrics.get(agent.agent_id, {})
            reliability = (
                metrics.get("success_rate", 0.5) * 0.6 +
                metrics.get("avg_quality_score", 0.5) * 0.4
            )
            scored_agents.append((reliability, agent))
        
        # Return top 50%
        scored_agents.sort(key=lambda x: x[0], reverse=True)
        top_count = max(1, len(scored_agents) // 2)
        return [agent for _, agent in scored_agents[:top_count]]

class AgentLoadBalancer:
    """
    Service for managing agent workload distribution and resource optimization
    """
    
    def __init__(self, performance_monitor=None):
        """
        Initialize load balancer
        
        Args:
            performance_monitor: Performance monitor service for metrics
        """
        self.performance_monitor = performance_monitor
        
        # Agent registry
        self.agents: Dict[str, BaseAgent] = {}
        self.agents_by_type: Dict[AgentType, List[BaseAgent]] = defaultdict(list)
        
        # Load balancing strategies
        self.strategies = {
            "round_robin": RoundRobinStrategy(),
            "least_loaded": LeastLoadedStrategy(),
            "weighted_performance": WeightedPerformanceStrategy(),
            "priority_aware": PriorityAwareStrategy(WeightedPerformanceStrategy())
        }
        
        self.default_strategy = "weighted_performance"
        
        # Request queue management
        self.request_queues: Dict[AgentType, List[Tuple[float, AgentRequest]]] = defaultdict(list)
        self.queue_processors: Dict[AgentType, asyncio.Task] = {}
        
        # Load balancing metrics
        self.balancing_metrics = {
            "total_requests_balanced": 0,
            "agent_selections": defaultdict(int),
            "strategy_usage": defaultdict(int),
            "queue_wait_times": [],
            "load_distribution_variance": 0.0
        }
        
        # Configuration
        self.max_queue_size = 100
        self.queue_timeout = 300  # 5 minutes
        
        logger.info("Agent Load Balancer initialized")
    
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the load balancer
        
        Args:
            agent: The agent to register
        """
        self.agents[agent.agent_id] = agent
        self.agents_by_type[agent.agent_type].append(agent)
        
        # Start queue processor for this agent type if not already running
        if agent.agent_type not in self.queue_processors:
            self.queue_processors[agent.agent_type] = asyncio.create_task(
                self._process_request_queue(agent.agent_type)
            )
        
        logger.info(f"Registered agent {agent.agent_id} with load balancer")
    
    def unregister_agent(self, agent_id: str):
        """
        Unregister an agent from the load balancer
        
        Args:
            agent_id: ID of the agent to unregister
        """
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            
            # Remove from type registry
            self.agents_by_type[agent.agent_type] = [
                a for a in self.agents_by_type[agent.agent_type]
                if a.agent_id != agent_id
            ]
            
            # Remove from main registry
            del self.agents[agent_id]
            
            # Stop queue processor if no agents of this type remain
            if not self.agents_by_type[agent.agent_type] and agent.agent_type in self.queue_processors:
                self.queue_processors[agent.agent_type].cancel()
                del self.queue_processors[agent.agent_type]
            
            logger.info(f"Unregistered agent {agent_id} from load balancer")
    
    async def balance_request(
        self,
        request: AgentRequest,
        required_agent_type: AgentType,
        strategy: Optional[str] = None
    ) -> Optional[BaseAgent]:
        """
        Balance a request to an appropriate agent
        
        Args:
            request: The request to balance
            required_agent_type: Type of agent required
            strategy: Load balancing strategy to use
            
        Returns:
            Selected agent or None if none available
        """
        strategy_name = strategy or self.default_strategy
        strategy_obj = self.strategies.get(strategy_name)
        
        if not strategy_obj:
            logger.warning(f"Unknown strategy {strategy_name}, using default")
            strategy_obj = self.strategies[self.default_strategy]
            strategy_name = self.default_strategy
        
        # Get available agents of required type
        available_agents = self._get_available_agents(required_agent_type)
        
        if not available_agents:
            # Queue the request if no agents available
            await self._queue_request(request, required_agent_type)
            return None
        
        # Get current performance metrics
        agent_metrics = self._get_agent_metrics()
        
        # Select agent using strategy
        selected_agent = strategy_obj.select_agent(available_agents, request, agent_metrics)
        
        if selected_agent:
            # Update metrics
            self.balancing_metrics["total_requests_balanced"] += 1
            self.balancing_metrics["agent_selections"][selected_agent.agent_id] += 1
            self.balancing_metrics["strategy_usage"][strategy_name] += 1
            
            logger.debug(f"Balanced request {request.id} to agent {selected_agent.agent_id} using {strategy_name}")
        
        return selected_agent
    
    async def rebalance_load(self):
        """
        Perform load rebalancing across agents
        """
        logger.info("Starting load rebalancing")
        
        # Get current load distribution
        load_distribution = self._calculate_load_distribution()
        
        # Identify overloaded and underloaded agents
        overloaded_agents = []
        underloaded_agents = []
        
        for agent_type, agents in self.agents_by_type.items():
            if len(agents) < 2:
                continue  # Can't rebalance with single agent
            
            loads = [agent.current_load for agent in agents]
            avg_load = sum(loads) / len(loads)
            
            for agent in agents:
                if agent.current_load > avg_load * 1.5:  # 50% above average
                    overloaded_agents.append(agent)
                elif agent.current_load < avg_load * 0.5:  # 50% below average
                    underloaded_agents.append(agent)
        
        # Process queued requests to help with rebalancing
        for agent_type in self.agents_by_type.keys():
            await self._process_queued_requests(agent_type)
        
        # Update load distribution variance
        self._update_load_distribution_variance()
        
        logger.info(f"Load rebalancing complete. Overloaded: {len(overloaded_agents)}, Underloaded: {len(underloaded_agents)}")
    
    def get_load_balancing_status(self) -> Dict[str, Any]:
        """
        Get current load balancing status
        
        Returns:
            Dictionary with load balancing metrics and status
        """
        # Calculate current load distribution
        load_distribution = self._calculate_load_distribution()
        
        # Get queue status
        queue_status = {}
        for agent_type, queue in self.request_queues.items():
            queue_status[agent_type.value] = {
                "queue_size": len(queue),
                "oldest_request_age": self._get_oldest_request_age(queue)
            }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "registered_agents": len(self.agents),
            "agents_by_type": {
                agent_type.value: len(agents)
                for agent_type, agents in self.agents_by_type.items()
            },
            "load_distribution": load_distribution,
            "queue_status": queue_status,
            "balancing_metrics": dict(self.balancing_metrics),
            "active_strategies": list(self.strategies.keys()),
            "default_strategy": self.default_strategy
        }
    
    def set_default_strategy(self, strategy_name: str):
        """
        Set the default load balancing strategy
        
        Args:
            strategy_name: Name of the strategy to use as default
        """
        if strategy_name in self.strategies:
            self.default_strategy = strategy_name
            logger.info(f"Default load balancing strategy set to {strategy_name}")
        else:
            logger.warning(f"Unknown strategy {strategy_name}")
    
    def add_strategy(self, name: str, strategy: LoadBalancingStrategy):
        """
        Add a custom load balancing strategy
        
        Args:
            name: Name of the strategy
            strategy: Strategy implementation
        """
        self.strategies[name] = strategy
        logger.info(f"Added load balancing strategy: {name}")
    
    def _get_available_agents(self, agent_type: AgentType) -> List[BaseAgent]:
        """Get available agents of specified type"""
        agents = self.agents_by_type.get(agent_type, [])
        return [
            agent for agent in agents
            if agent.is_active and agent.current_load < agent.max_concurrent_requests
        ]
    
    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Get current agent performance metrics"""
        if not self.performance_monitor:
            return {}
        
        metrics = {}
        for agent_id in self.agents.keys():
            profile = self.performance_monitor.get_agent_performance_profile(agent_id)
            if profile:
                metrics[agent_id] = {
                    "avg_response_time": profile.avg_response_time,
                    "success_rate": profile.success_rate,
                    "avg_quality_score": profile.avg_quality_score,
                    "reliability_score": profile.reliability_score
                }
        
        return metrics
    
    async def _queue_request(self, request: AgentRequest, agent_type: AgentType):
        """Queue a request when no agents are available"""
        queue = self.request_queues[agent_type]
        
        if len(queue) >= self.max_queue_size:
            # Remove oldest request if queue is full
            heapq.heappop(queue)
            logger.warning(f"Queue full for {agent_type.value}, removed oldest request")
        
        # Add request with timestamp for priority
        priority = time.time()  # Use timestamp as priority (FIFO)
        if request.priority == RequestPriority.URGENT:
            priority -= 1000000  # High priority
        elif request.priority == RequestPriority.HIGH:
            priority -= 100000
        
        heapq.heappush(queue, (priority, request))
        logger.info(f"Queued request {request.id} for {agent_type.value}")
    
    async def _process_request_queue(self, agent_type: AgentType):
        """Background task to process queued requests"""
        while True:
            try:
                await self._process_queued_requests(agent_type)
                await asyncio.sleep(1)  # Check queue every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing queue for {agent_type.value}: {str(e)}")
                await asyncio.sleep(5)
    
    async def _process_queued_requests(self, agent_type: AgentType):
        """Process queued requests for a specific agent type"""
        queue = self.request_queues[agent_type]
        available_agents = self._get_available_agents(agent_type)
        
        while queue and available_agents:
            # Get next request from queue
            priority, request = heapq.heappop(queue)
            
            # Check if request has timed out
            request_age = time.time() - priority
            if request_age > self.queue_timeout:
                logger.warning(f"Request {request.id} timed out in queue")
                continue
            
            # Select agent for request
            agent_metrics = self._get_agent_metrics()
            strategy = self.strategies[self.default_strategy]
            selected_agent = strategy.select_agent(available_agents, request, agent_metrics)
            
            if selected_agent:
                # Process request with selected agent
                try:
                    await selected_agent.handle_request(request)
                    
                    # Record queue wait time
                    wait_time = time.time() - (-priority if priority < 0 else priority)
                    self.balancing_metrics["queue_wait_times"].append(wait_time)
                    
                    # Keep only recent wait times
                    if len(self.balancing_metrics["queue_wait_times"]) > 1000:
                        self.balancing_metrics["queue_wait_times"] = self.balancing_metrics["queue_wait_times"][-500:]
                    
                except Exception as e:
                    logger.error(f"Error processing queued request {request.id}: {str(e)}")
            
            # Update available agents list
            available_agents = self._get_available_agents(agent_type)
    
    def _calculate_load_distribution(self) -> Dict[str, Any]:
        """Calculate current load distribution across agents"""
        distribution = {}
        
        for agent_type, agents in self.agents_by_type.items():
            if not agents:
                continue
            
            loads = [agent.current_load for agent in agents]
            total_capacity = sum(agent.max_concurrent_requests for agent in agents)
            total_load = sum(loads)
            
            distribution[agent_type.value] = {
                "total_agents": len(agents),
                "total_load": total_load,
                "total_capacity": total_capacity,
                "utilization": total_load / max(total_capacity, 1),
                "load_variance": self._calculate_variance(loads),
                "agent_loads": {
                    agent.agent_id: {
                        "current_load": agent.current_load,
                        "max_capacity": agent.max_concurrent_requests,
                        "utilization": agent.current_load / max(agent.max_concurrent_requests, 1)
                    }
                    for agent in agents
                }
            }
        
        return distribution
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def _update_load_distribution_variance(self):
        """Update the overall load distribution variance metric"""
        all_utilizations = []
        
        for agents in self.agents_by_type.values():
            for agent in agents:
                utilization = agent.current_load / max(agent.max_concurrent_requests, 1)
                all_utilizations.append(utilization)
        
        if all_utilizations:
            self.balancing_metrics["load_distribution_variance"] = self._calculate_variance(all_utilizations)
    
    def _get_oldest_request_age(self, queue: List[Tuple[float, AgentRequest]]) -> Optional[float]:
        """Get age of oldest request in queue"""
        if not queue:
            return None
        
        oldest_priority = min(priority for priority, _ in queue)
        return time.time() - (-oldest_priority if oldest_priority < 0 else oldest_priority)

# Import time module
import time