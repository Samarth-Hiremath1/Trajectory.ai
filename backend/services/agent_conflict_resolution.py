"""
Agent Conflict Resolution System
Handles conflicts between agents and builds consensus for multi-agent responses
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict
import statistics
import json

from models.agent import (
    AgentType, AgentRequest, AgentResponse, MessageType
)
from services.ai_service import AIService

logger = logging.getLogger(__name__)

class ConflictType(Enum):
    """Types of conflicts between agents"""
    CONTRADICTORY_ADVICE = "contradictory_advice"
    DIFFERENT_PRIORITIES = "different_priorities"
    INCOMPATIBLE_STRATEGIES = "incompatible_strategies"
    RESOURCE_COMPETITION = "resource_competition"
    QUALITY_DISAGREEMENT = "quality_disagreement"

class ResolutionStrategy(Enum):
    """Strategies for resolving conflicts"""
    CONSENSUS_BUILDING = "consensus_building"
    EXPERT_ARBITRATION = "expert_arbitration"
    WEIGHTED_VOTING = "weighted_voting"
    CONFIDENCE_BASED = "confidence_based"
    USER_PREFERENCE = "user_preference"

@dataclass
class AgentConflict:
    """Represents a conflict between agents"""
    conflict_id: str
    conflict_type: ConflictType
    involved_agents: List[str]
    conflicting_responses: List[AgentResponse]
    conflict_description: str
    severity: float  # 0.0 to 1.0
    detected_at: datetime
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolved_at: Optional[datetime] = None
    resolution_result: Optional[Dict[str, Any]] = None

@dataclass
class ConsensusResult:
    """Result of consensus building process"""
    consensus_response: Dict[str, Any]
    confidence_score: float
    participating_agents: List[str]
    agreement_level: float  # 0.0 to 1.0
    dissenting_opinions: List[Dict[str, Any]]
    resolution_method: str

class AgentConflictResolver:
    """
    Service for detecting and resolving conflicts between agents
    """
    
    def __init__(self, ai_service: AIService):
        """
        Initialize conflict resolver
        
        Args:
            ai_service: AI service for conflict analysis and resolution
        """
        self.ai_service = ai_service
        
        # Conflict tracking
        self.active_conflicts: Dict[str, AgentConflict] = {}
        self.resolved_conflicts: List[AgentConflict] = []
        
        # Resolution strategies
        self.resolution_strategies = {
            ResolutionStrategy.CONSENSUS_BUILDING: self._resolve_by_consensus,
            ResolutionStrategy.EXPERT_ARBITRATION: self._resolve_by_expert_arbitration,
            ResolutionStrategy.WEIGHTED_VOTING: self._resolve_by_weighted_voting,
            ResolutionStrategy.CONFIDENCE_BASED: self._resolve_by_confidence,
            ResolutionStrategy.USER_PREFERENCE: self._resolve_by_user_preference
        }
        
        # Agent expertise weights for different domains
        self.agent_expertise_weights = {
            AgentType.CAREER_STRATEGY: {
                "career_planning": 0.9,
                "market_analysis": 0.8,
                "networking": 0.7,
                "skill_development": 0.6
            },
            AgentType.SKILLS_ANALYSIS: {
                "skill_assessment": 0.9,
                "gap_analysis": 0.8,
                "skill_development": 0.9,
                "certification": 0.7
            },
            AgentType.LEARNING_RESOURCE: {
                "course_recommendation": 0.9,
                "learning_paths": 0.8,
                "resource_quality": 0.8,
                "skill_development": 0.7
            },
            AgentType.RESUME_OPTIMIZATION: {
                "resume_structure": 0.9,
                "content_optimization": 0.8,
                "ats_optimization": 0.9,
                "formatting": 0.8
            },
            AgentType.CAREER_MENTOR: {
                "career_advice": 0.9,
                "interview_prep": 0.8,
                "motivation": 0.9,
                "decision_making": 0.8
            }
        }
        
        # Conflict detection thresholds
        self.conflict_thresholds = {
            "confidence_difference": 0.3,
            "content_similarity": 0.5,
            "recommendation_overlap": 0.3
        }
        
        # Resolution metrics
        self.resolution_metrics = {
            "total_conflicts_detected": 0,
            "conflicts_resolved": 0,
            "average_resolution_time": 0.0,
            "resolution_success_rate": 0.0,
            "consensus_agreements": 0,
            "arbitration_decisions": 0
        }
        
        logger.info("Agent Conflict Resolver initialized")
    
    async def detect_conflicts(
        self,
        responses: List[AgentResponse],
        request_context: Optional[Dict[str, Any]] = None
    ) -> List[AgentConflict]:
        """
        Detect conflicts between agent responses
        
        Args:
            responses: List of agent responses to analyze
            request_context: Optional context about the original request
            
        Returns:
            List of detected conflicts
        """
        if len(responses) < 2:
            return []
        
        conflicts = []
        
        # Check for different types of conflicts
        conflicts.extend(await self._detect_contradictory_advice(responses))
        conflicts.extend(await self._detect_priority_conflicts(responses))
        conflicts.extend(await self._detect_strategy_conflicts(responses))
        conflicts.extend(await self._detect_quality_disagreements(responses))
        
        # Store detected conflicts
        for conflict in conflicts:
            self.active_conflicts[conflict.conflict_id] = conflict
            self.resolution_metrics["total_conflicts_detected"] += 1
        
        if conflicts:
            logger.info(f"Detected {len(conflicts)} conflicts between {len(responses)} agent responses")
        
        return conflicts
    
    async def resolve_conflict(
        self,
        conflict: AgentConflict,
        strategy: Optional[ResolutionStrategy] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ConsensusResult:
        """
        Resolve a conflict between agents
        
        Args:
            conflict: The conflict to resolve
            strategy: Resolution strategy to use
            user_preferences: User preferences for resolution
            
        Returns:
            ConsensusResult with the resolution
        """
        start_time = datetime.utcnow()
        
        # Determine resolution strategy
        if strategy is None:
            strategy = self._select_resolution_strategy(conflict, user_preferences)
        
        # Apply resolution strategy
        resolver = self.resolution_strategies.get(strategy)
        if not resolver:
            raise ValueError(f"Unknown resolution strategy: {strategy}")
        
        try:
            result = await resolver(conflict, user_preferences)
            
            # Update conflict record
            conflict.resolution_strategy = strategy
            conflict.resolved_at = datetime.utcnow()
            conflict.resolution_result = result.__dict__
            
            # Move to resolved conflicts
            if conflict.conflict_id in self.active_conflicts:
                del self.active_conflicts[conflict.conflict_id]
            self.resolved_conflicts.append(conflict)
            
            # Update metrics
            resolution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_resolution_metrics(resolution_time, True)
            
            logger.info(f"Resolved conflict {conflict.conflict_id} using {strategy.value}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict {conflict.conflict_id}: {str(e)}")
            self._update_resolution_metrics(0, False)
            raise
    
    async def build_consensus(
        self,
        responses: List[AgentResponse],
        request_context: Optional[Dict[str, Any]] = None
    ) -> ConsensusResult:
        """
        Build consensus from multiple agent responses
        
        Args:
            responses: List of agent responses
            request_context: Optional request context
            
        Returns:
            ConsensusResult with consensus response
        """
        if len(responses) == 1:
            # Single response, no consensus needed
            return ConsensusResult(
                consensus_response=responses[0].response_content,
                confidence_score=responses[0].confidence_score,
                participating_agents=[responses[0].agent_id],
                agreement_level=1.0,
                dissenting_opinions=[],
                resolution_method="single_response"
            )
        
        # Detect conflicts first
        conflicts = await self.detect_conflicts(responses, request_context)
        
        if not conflicts:
            # No conflicts, build simple consensus
            return await self._build_simple_consensus(responses)
        
        # Resolve conflicts and build consensus
        resolved_responses = []
        for conflict in conflicts:
            resolution = await self.resolve_conflict(conflict)
            resolved_responses.append(resolution)
        
        # Combine resolved responses with non-conflicting responses
        non_conflicting_responses = self._get_non_conflicting_responses(responses, conflicts)
        
        return await self._build_final_consensus(resolved_responses, non_conflicting_responses)
    
    def get_conflict_status(self) -> Dict[str, Any]:
        """
        Get current conflict resolution status
        
        Returns:
            Dictionary with conflict status and metrics
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_conflicts": len(self.active_conflicts),
            "resolved_conflicts": len(self.resolved_conflicts),
            "conflict_types": self._get_conflict_type_distribution(),
            "resolution_strategies": self._get_strategy_usage_stats(),
            "metrics": self.resolution_metrics,
            "recent_conflicts": [
                {
                    "conflict_id": conflict.conflict_id,
                    "type": conflict.conflict_type.value,
                    "severity": conflict.severity,
                    "agents": conflict.involved_agents,
                    "detected_at": conflict.detected_at.isoformat()
                }
                for conflict in list(self.active_conflicts.values())[-5:]
            ]
        }
    
    async def _detect_contradictory_advice(self, responses: List[AgentResponse]) -> List[AgentConflict]:
        """Detect contradictory advice between responses"""
        conflicts = []
        
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                response1, response2 = responses[i], responses[j]
                
                # Use AI to detect contradictions
                contradiction_score = await self._analyze_contradiction(response1, response2)
                
                if contradiction_score > 0.7:  # High contradiction threshold
                    conflict = AgentConflict(
                        conflict_id=f"contradiction_{response1.agent_id}_{response2.agent_id}_{datetime.utcnow().timestamp()}",
                        conflict_type=ConflictType.CONTRADICTORY_ADVICE,
                        involved_agents=[response1.agent_id, response2.agent_id],
                        conflicting_responses=[response1, response2],
                        conflict_description=f"Contradictory advice detected between {response1.agent_type.value} and {response2.agent_type.value}",
                        severity=contradiction_score,
                        detected_at=datetime.utcnow()
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_priority_conflicts(self, responses: List[AgentResponse]) -> List[AgentConflict]:
        """Detect conflicts in priorities or recommendations"""
        conflicts = []
        
        # Extract priorities/recommendations from responses
        priorities = []
        for response in responses:
            response_priorities = self._extract_priorities(response)
            priorities.append((response, response_priorities))
        
        # Compare priorities between agents
        for i in range(len(priorities)):
            for j in range(i + 1, len(priorities)):
                response1, priorities1 = priorities[i]
                response2, priorities2 = priorities[j]
                
                conflict_score = self._calculate_priority_conflict(priorities1, priorities2)
                
                if conflict_score > 0.6:
                    conflict = AgentConflict(
                        conflict_id=f"priority_{response1.agent_id}_{response2.agent_id}_{datetime.utcnow().timestamp()}",
                        conflict_type=ConflictType.DIFFERENT_PRIORITIES,
                        involved_agents=[response1.agent_id, response2.agent_id],
                        conflicting_responses=[response1, response2],
                        conflict_description=f"Priority conflict between {response1.agent_type.value} and {response2.agent_type.value}",
                        severity=conflict_score,
                        detected_at=datetime.utcnow()
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_strategy_conflicts(self, responses: List[AgentResponse]) -> List[AgentConflict]:
        """Detect incompatible strategies between responses"""
        conflicts = []
        
        # This would analyze strategic approaches in responses
        # For now, simplified implementation
        
        strategy_responses = [r for r in responses if r.agent_type == AgentType.CAREER_STRATEGY]
        
        if len(strategy_responses) > 1:
            # Check for incompatible strategies
            for i in range(len(strategy_responses)):
                for j in range(i + 1, len(strategy_responses)):
                    response1, response2 = strategy_responses[i], strategy_responses[j]
                    
                    # Simplified strategy conflict detection
                    if response1.confidence_score > 0.8 and response2.confidence_score > 0.8:
                        # Both agents are confident but might have different strategies
                        similarity = await self._calculate_response_similarity(response1, response2)
                        
                        if similarity < 0.3:  # Low similarity might indicate conflict
                            conflict = AgentConflict(
                                conflict_id=f"strategy_{response1.agent_id}_{response2.agent_id}_{datetime.utcnow().timestamp()}",
                                conflict_type=ConflictType.INCOMPATIBLE_STRATEGIES,
                                involved_agents=[response1.agent_id, response2.agent_id],
                                conflicting_responses=[response1, response2],
                                conflict_description="Incompatible strategic approaches detected",
                                severity=1.0 - similarity,
                                detected_at=datetime.utcnow()
                            )
                            conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_quality_disagreements(self, responses: List[AgentResponse]) -> List[AgentConflict]:
        """Detect disagreements in quality assessments"""
        conflicts = []
        
        # Check for significant confidence score differences
        confidence_scores = [r.confidence_score for r in responses]
        
        if len(confidence_scores) > 1:
            max_confidence = max(confidence_scores)
            min_confidence = min(confidence_scores)
            
            if max_confidence - min_confidence > self.conflict_thresholds["confidence_difference"]:
                # Find the responses with extreme confidence differences
                high_confidence_responses = [r for r in responses if r.confidence_score == max_confidence]
                low_confidence_responses = [r for r in responses if r.confidence_score == min_confidence]
                
                for high_resp in high_confidence_responses:
                    for low_resp in low_confidence_responses:
                        conflict = AgentConflict(
                            conflict_id=f"quality_{high_resp.agent_id}_{low_resp.agent_id}_{datetime.utcnow().timestamp()}",
                            conflict_type=ConflictType.QUALITY_DISAGREEMENT,
                            involved_agents=[high_resp.agent_id, low_resp.agent_id],
                            conflicting_responses=[high_resp, low_resp],
                            conflict_description=f"Quality disagreement: confidence difference of {max_confidence - min_confidence:.2f}",
                            severity=max_confidence - min_confidence,
                            detected_at=datetime.utcnow()
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    async def _analyze_contradiction(self, response1: AgentResponse, response2: AgentResponse) -> float:
        """Analyze contradiction level between two responses using AI"""
        
        analysis_prompt = f"""
        Analyze these two agent responses for contradictions:
        
        Response 1 ({response1.agent_type.value}):
        {json.dumps(response1.response_content, indent=2)}
        
        Response 2 ({response2.agent_type.value}):
        {json.dumps(response2.response_content, indent=2)}
        
        Rate the level of contradiction on a scale of 0.0 to 1.0, where:
        - 0.0 = No contradiction, responses are compatible
        - 0.5 = Some conflicting elements but generally compatible
        - 1.0 = Direct contradiction, responses are incompatible
        
        Consider:
        1. Direct contradictions in advice or recommendations
        2. Conflicting priorities or approaches
        3. Incompatible timelines or strategies
        
        Respond with only a number between 0.0 and 1.0.
        """
        
        try:
            result = await self.ai_service.generate_text(
                prompt=analysis_prompt,
                max_tokens=50,
                temperature=0.1
            )
            
            # Extract number from result
            import re
            number_match = re.search(r'(\d+\.?\d*)', result.strip())
            if number_match:
                score = float(number_match.group(1))
                return min(max(score, 0.0), 1.0)  # Clamp to 0.0-1.0
            
        except Exception as e:
            logger.error(f"Failed to analyze contradiction: {str(e)}")
        
        return 0.0  # Default to no contradiction
    
    def _extract_priorities(self, response: AgentResponse) -> List[str]:
        """Extract priorities or key recommendations from a response"""
        priorities = []
        
        content = response.response_content
        if isinstance(content, dict):
            # Look for common priority indicators
            for key in ["priorities", "recommendations", "next_steps", "action_items"]:
                if key in content:
                    value = content[key]
                    if isinstance(value, list):
                        priorities.extend([str(item) for item in value])
                    else:
                        priorities.append(str(value))
        
        return priorities
    
    def _calculate_priority_conflict(self, priorities1: List[str], priorities2: List[str]) -> float:
        """Calculate conflict score between two priority lists"""
        if not priorities1 or not priorities2:
            return 0.0
        
        # Simple overlap calculation
        set1 = set(priorities1)
        set2 = set(priorities2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        overlap = intersection / union
        return 1.0 - overlap  # Higher conflict when lower overlap
    
    async def _calculate_response_similarity(self, response1: AgentResponse, response2: AgentResponse) -> float:
        """Calculate similarity between two responses"""
        
        # Simple similarity based on content overlap
        content1 = str(response1.response_content).lower()
        content2 = str(response2.response_content).lower()
        
        # Basic word overlap similarity
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _select_resolution_strategy(
        self,
        conflict: AgentConflict,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ResolutionStrategy:
        """Select appropriate resolution strategy for a conflict"""
        
        # Consider user preferences first
        if user_preferences and "resolution_strategy" in user_preferences:
            preferred_strategy = user_preferences["resolution_strategy"]
            if preferred_strategy in [s.value for s in ResolutionStrategy]:
                return ResolutionStrategy(preferred_strategy)
        
        # Select based on conflict type and characteristics
        if conflict.conflict_type == ConflictType.CONTRADICTORY_ADVICE:
            return ResolutionStrategy.EXPERT_ARBITRATION
        elif conflict.conflict_type == ConflictType.DIFFERENT_PRIORITIES:
            return ResolutionStrategy.WEIGHTED_VOTING
        elif conflict.conflict_type == ConflictType.INCOMPATIBLE_STRATEGIES:
            return ResolutionStrategy.CONSENSUS_BUILDING
        elif conflict.conflict_type == ConflictType.QUALITY_DISAGREEMENT:
            return ResolutionStrategy.CONFIDENCE_BASED
        else:
            return ResolutionStrategy.CONSENSUS_BUILDING  # Default
    
    async def _resolve_by_consensus(
        self,
        conflict: AgentConflict,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ConsensusResult:
        """Resolve conflict by building consensus"""
        
        responses = conflict.conflicting_responses
        
        # Use AI to build consensus
        consensus_prompt = self._create_consensus_prompt(responses, conflict)
        
        try:
            consensus_content = await self.ai_service.generate_text(
                prompt=consensus_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            # Calculate agreement level based on response similarities
            agreement_level = await self._calculate_agreement_level(responses)
            
            # Average confidence scores
            avg_confidence = statistics.mean([r.confidence_score for r in responses])
            
            self.resolution_metrics["consensus_agreements"] += 1
            
            return ConsensusResult(
                consensus_response={"consensus": consensus_content},
                confidence_score=avg_confidence,
                participating_agents=[r.agent_id for r in responses],
                agreement_level=agreement_level,
                dissenting_opinions=[],
                resolution_method="ai_consensus"
            )
            
        except Exception as e:
            logger.error(f"Failed to build consensus: {str(e)}")
            # Fallback to weighted voting
            return await self._resolve_by_weighted_voting(conflict, user_preferences)
    
    async def _resolve_by_expert_arbitration(
        self,
        conflict: AgentConflict,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ConsensusResult:
        """Resolve conflict by expert arbitration"""
        
        responses = conflict.conflicting_responses
        
        # Determine domain of conflict
        domain = self._determine_conflict_domain(conflict)
        
        # Find most expert agent for this domain
        expert_response = self._select_expert_response(responses, domain)
        
        if expert_response:
            self.resolution_metrics["arbitration_decisions"] += 1
            
            return ConsensusResult(
                consensus_response=expert_response.response_content,
                confidence_score=expert_response.confidence_score,
                participating_agents=[expert_response.agent_id],
                agreement_level=1.0,  # Expert decision is final
                dissenting_opinions=[
                    {"agent_id": r.agent_id, "response": r.response_content}
                    for r in responses if r.agent_id != expert_response.agent_id
                ],
                resolution_method="expert_arbitration"
            )
        else:
            # Fallback to confidence-based resolution
            return await self._resolve_by_confidence(conflict, user_preferences)
    
    async def _resolve_by_weighted_voting(
        self,
        conflict: AgentConflict,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ConsensusResult:
        """Resolve conflict by weighted voting"""
        
        responses = conflict.conflicting_responses
        domain = self._determine_conflict_domain(conflict)
        
        # Calculate weights for each response
        weighted_responses = []
        for response in responses:
            weight = self._calculate_agent_weight(response.agent_type, domain)
            weighted_responses.append((response, weight))
        
        # Select response with highest weight
        best_response, best_weight = max(weighted_responses, key=lambda x: x[1])
        
        return ConsensusResult(
            consensus_response=best_response.response_content,
            confidence_score=best_response.confidence_score * best_weight,
            participating_agents=[r.agent_id for r, _ in weighted_responses],
            agreement_level=best_weight,
            dissenting_opinions=[
                {"agent_id": r.agent_id, "response": r.response_content, "weight": w}
                for r, w in weighted_responses if r.agent_id != best_response.agent_id
            ],
            resolution_method="weighted_voting"
        )
    
    async def _resolve_by_confidence(
        self,
        conflict: AgentConflict,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ConsensusResult:
        """Resolve conflict based on confidence scores"""
        
        responses = conflict.conflicting_responses
        
        # Select response with highest confidence
        best_response = max(responses, key=lambda r: r.confidence_score)
        
        return ConsensusResult(
            consensus_response=best_response.response_content,
            confidence_score=best_response.confidence_score,
            participating_agents=[best_response.agent_id],
            agreement_level=best_response.confidence_score,
            dissenting_opinions=[
                {"agent_id": r.agent_id, "response": r.response_content, "confidence": r.confidence_score}
                for r in responses if r.agent_id != best_response.agent_id
            ],
            resolution_method="confidence_based"
        )
    
    async def _resolve_by_user_preference(
        self,
        conflict: AgentConflict,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ConsensusResult:
        """Resolve conflict based on user preferences"""
        
        # This would integrate with user preference system
        # For now, fallback to consensus building
        return await self._resolve_by_consensus(conflict, user_preferences)
    
    def _create_consensus_prompt(self, responses: List[AgentResponse], conflict: AgentConflict) -> str:
        """Create prompt for AI consensus building"""
        
        prompt_parts = [
            f"Build consensus from these conflicting agent responses about {conflict.conflict_description}:",
            ""
        ]
        
        for i, response in enumerate(responses, 1):
            prompt_parts.extend([
                f"Response {i} ({response.agent_type.value}, confidence: {response.confidence_score:.2f}):",
                json.dumps(response.response_content, indent=2),
                ""
            ])
        
        prompt_parts.extend([
            "Please create a consensus response that:",
            "1. Addresses the core conflict constructively",
            "2. Incorporates the best elements from each response",
            "3. Provides clear, actionable guidance",
            "4. Acknowledges any remaining uncertainties",
            "",
            "Consensus response:"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _calculate_agreement_level(self, responses: List[AgentResponse]) -> float:
        """Calculate overall agreement level between responses"""
        
        if len(responses) < 2:
            return 1.0
        
        similarities = []
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                similarity = await self._calculate_response_similarity(responses[i], responses[j])
                similarities.append(similarity)
        
        return statistics.mean(similarities) if similarities else 0.0
    
    def _determine_conflict_domain(self, conflict: AgentConflict) -> str:
        """Determine the domain of a conflict"""
        
        # Simple domain determination based on agent types involved
        agent_types = [r.agent_type for r in conflict.conflicting_responses]
        
        if AgentType.CAREER_STRATEGY in agent_types:
            return "career_planning"
        elif AgentType.SKILLS_ANALYSIS in agent_types:
            return "skill_assessment"
        elif AgentType.LEARNING_RESOURCE in agent_types:
            return "learning_paths"
        elif AgentType.RESUME_OPTIMIZATION in agent_types:
            return "resume_optimization"
        elif AgentType.CAREER_MENTOR in agent_types:
            return "career_advice"
        else:
            return "general"
    
    def _select_expert_response(self, responses: List[AgentResponse], domain: str) -> Optional[AgentResponse]:
        """Select the most expert response for a given domain"""
        
        expert_scores = []
        for response in responses:
            weight = self._calculate_agent_weight(response.agent_type, domain)
            expert_scores.append((response, weight))
        
        if expert_scores:
            return max(expert_scores, key=lambda x: x[1])[0]
        
        return None
    
    def _calculate_agent_weight(self, agent_type: AgentType, domain: str) -> float:
        """Calculate agent weight for a specific domain"""
        
        weights = self.agent_expertise_weights.get(agent_type, {})
        return weights.get(domain, 0.5)  # Default weight of 0.5
    
    async def _build_simple_consensus(self, responses: List[AgentResponse]) -> ConsensusResult:
        """Build simple consensus when no conflicts detected"""
        
        # Combine responses by confidence-weighted averaging
        total_weight = sum(r.confidence_score for r in responses)
        
        if total_weight == 0:
            # All responses have zero confidence
            return ConsensusResult(
                consensus_response={"error": "No confident responses available"},
                confidence_score=0.0,
                participating_agents=[r.agent_id for r in responses],
                agreement_level=0.0,
                dissenting_opinions=[],
                resolution_method="no_confidence"
            )
        
        # Weight responses by confidence
        weighted_content = {}
        for response in responses:
            weight = response.confidence_score / total_weight
            content = response.response_content
            
            if isinstance(content, dict):
                for key, value in content.items():
                    if key not in weighted_content:
                        weighted_content[key] = []
                    weighted_content[key].append((value, weight))
        
        # Create consensus content
        consensus_content = {}
        for key, values in weighted_content.items():
            # For now, just take the highest weighted value
            best_value, best_weight = max(values, key=lambda x: x[1])
            consensus_content[key] = best_value
        
        avg_confidence = statistics.mean([r.confidence_score for r in responses])
        agreement_level = await self._calculate_agreement_level(responses)
        
        return ConsensusResult(
            consensus_response=consensus_content,
            confidence_score=avg_confidence,
            participating_agents=[r.agent_id for r in responses],
            agreement_level=agreement_level,
            dissenting_opinions=[],
            resolution_method="weighted_consensus"
        )
    
    def _get_non_conflicting_responses(
        self,
        responses: List[AgentResponse],
        conflicts: List[AgentConflict]
    ) -> List[AgentResponse]:
        """Get responses that are not involved in any conflicts"""
        
        conflicting_agent_ids = set()
        for conflict in conflicts:
            conflicting_agent_ids.update(conflict.involved_agents)
        
        return [r for r in responses if r.agent_id not in conflicting_agent_ids]
    
    async def _build_final_consensus(
        self,
        resolved_responses: List[ConsensusResult],
        non_conflicting_responses: List[AgentResponse]
    ) -> ConsensusResult:
        """Build final consensus from resolved conflicts and non-conflicting responses"""
        
        # Combine all responses
        all_content = []
        all_agents = []
        all_confidences = []
        
        for resolution in resolved_responses:
            all_content.append(resolution.consensus_response)
            all_agents.extend(resolution.participating_agents)
            all_confidences.append(resolution.confidence_score)
        
        for response in non_conflicting_responses:
            all_content.append(response.response_content)
            all_agents.append(response.agent_id)
            all_confidences.append(response.confidence_score)
        
        # Create final consensus
        final_consensus = {
            "resolved_conflicts": len(resolved_responses),
            "additional_responses": len(non_conflicting_responses),
            "combined_guidance": all_content
        }
        
        avg_confidence = statistics.mean(all_confidences) if all_confidences else 0.0
        
        return ConsensusResult(
            consensus_response=final_consensus,
            confidence_score=avg_confidence,
            participating_agents=list(set(all_agents)),
            agreement_level=0.8,  # Assume good agreement after conflict resolution
            dissenting_opinions=[],
            resolution_method="final_consensus"
        )
    
    def _update_resolution_metrics(self, resolution_time: float, success: bool):
        """Update resolution metrics"""
        
        if success:
            self.resolution_metrics["conflicts_resolved"] += 1
            
            # Update average resolution time
            total_resolved = self.resolution_metrics["conflicts_resolved"]
            current_avg = self.resolution_metrics["average_resolution_time"]
            
            if total_resolved == 1:
                self.resolution_metrics["average_resolution_time"] = resolution_time
            else:
                total_time = current_avg * (total_resolved - 1)
                self.resolution_metrics["average_resolution_time"] = (total_time + resolution_time) / total_resolved
        
        # Update success rate
        total_attempts = self.resolution_metrics["conflicts_resolved"] + (0 if success else 1)
        self.resolution_metrics["resolution_success_rate"] = (
            self.resolution_metrics["conflicts_resolved"] / max(total_attempts, 1)
        )
    
    def _get_conflict_type_distribution(self) -> Dict[str, int]:
        """Get distribution of conflict types"""
        
        distribution = defaultdict(int)
        
        for conflict in self.resolved_conflicts:
            distribution[conflict.conflict_type.value] += 1
        
        for conflict in self.active_conflicts.values():
            distribution[conflict.conflict_type.value] += 1
        
        return dict(distribution)
    
    def _get_strategy_usage_stats(self) -> Dict[str, int]:
        """Get usage statistics for resolution strategies"""
        
        usage = defaultdict(int)
        
        for conflict in self.resolved_conflicts:
            if conflict.resolution_strategy:
                usage[conflict.resolution_strategy.value] += 1
        
        return dict(usage)