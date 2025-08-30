"""
Agent Learning and Improvement System
Implements feedback loops and learning mechanisms for agent optimization
"""
import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
import statistics
import pickle
import os

from models.agent import (
    AgentType, AgentRequest, AgentResponse, RequestType
)
from services.ai_service import AIService

logger = logging.getLogger(__name__)

@dataclass
class LearningExample:
    """Example for agent learning"""
    request_id: str
    agent_id: str
    agent_type: AgentType
    request_content: Dict[str, Any]
    response_content: Dict[str, Any]
    quality_score: float
    user_feedback: Optional[str]
    success_indicators: Dict[str, Any]
    timestamp: datetime

@dataclass
class ImprovementSuggestion:
    """Suggestion for agent improvement"""
    agent_id: str
    suggestion_type: str  # "prompt", "strategy", "parameter"
    description: str
    expected_improvement: float
    confidence: float
    implementation_priority: int
    created_at: datetime

@dataclass
class LearningPattern:
    """Identified learning pattern"""
    pattern_id: str
    agent_type: AgentType
    pattern_description: str
    success_conditions: Dict[str, Any]
    failure_conditions: Dict[str, Any]
    improvement_actions: List[str]
    confidence: float
    examples_count: int

class AgentLearningSystem:
    """
    System for agent learning and continuous improvement
    """
    
    def __init__(self, ai_service: AIService, learning_data_dir: str = "agent_learning_data"):
        """
        Initialize learning system
        
        Args:
            ai_service: AI service for analysis and improvement generation
            learning_data_dir: Directory to store learning data
        """
        self.ai_service = ai_service
        self.learning_data_dir = learning_data_dir
        
        # Create learning data directory
        os.makedirs(learning_data_dir, exist_ok=True)
        
        # Learning data storage
        self.learning_examples: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.improvement_suggestions: Dict[str, List[ImprovementSuggestion]] = defaultdict(list)
        self.learning_patterns: Dict[str, List[LearningPattern]] = defaultdict(list)
        
        # Agent knowledge bases
        self.agent_knowledge: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.prompt_templates: Dict[AgentType, Dict[str, str]] = defaultdict(dict)
        
        # Learning configuration
        self.learning_config = {
            "min_examples_for_pattern": 10,
            "quality_threshold_for_learning": 0.7,
            "improvement_confidence_threshold": 0.6,
            "pattern_analysis_interval": 3600,  # 1 hour
            "knowledge_update_interval": 1800,  # 30 minutes
        }
        
        # Performance tracking
        self.learning_metrics = {
            "total_examples_collected": 0,
            "patterns_identified": 0,
            "improvements_suggested": 0,
            "improvements_implemented": 0,
            "average_quality_improvement": 0.0
        }
        
        # Load existing learning data
        self._load_learning_data()
        
        logger.info("Agent Learning System initialized")
    
    async def start_learning(self):
        """Start the learning system background tasks"""
        asyncio.create_task(self._analyze_patterns_periodically())
        asyncio.create_task(self._update_knowledge_bases())
        asyncio.create_task(self._generate_improvements())
        
        logger.info("Agent learning system started")
    
    def record_learning_example(
        self,
        request: AgentRequest,
        response: AgentResponse,
        quality_score: float,
        user_feedback: Optional[str] = None,
        success_indicators: Optional[Dict[str, Any]] = None
    ):
        """
        Record a learning example from agent interaction
        
        Args:
            request: The original request
            response: The agent response
            quality_score: Quality assessment score
            user_feedback: Optional user feedback
            success_indicators: Success/failure indicators
        """
        example = LearningExample(
            request_id=request.id,
            agent_id=response.agent_id,
            agent_type=response.agent_type,
            request_content=request.content,
            response_content=response.response_content,
            quality_score=quality_score,
            user_feedback=user_feedback,
            success_indicators=success_indicators or {},
            timestamp=datetime.utcnow()
        )
        
        self.learning_examples[response.agent_id].append(example)
        self.learning_metrics["total_examples_collected"] += 1
        
        # Trigger immediate learning if we have enough high-quality examples
        if (quality_score >= self.learning_config["quality_threshold_for_learning"] and
            len(self.learning_examples[response.agent_id]) % 10 == 0):
            asyncio.create_task(self._analyze_agent_patterns(response.agent_id))
        
        logger.debug(f"Recorded learning example for agent {response.agent_id}")
    
    async def generate_improvement_suggestions(self, agent_id: str) -> List[ImprovementSuggestion]:
        """
        Generate improvement suggestions for a specific agent
        
        Args:
            agent_id: ID of the agent to improve
            
        Returns:
            List of improvement suggestions
        """
        examples = list(self.learning_examples[agent_id])
        if len(examples) < self.learning_config["min_examples_for_pattern"]:
            return []
        
        # Analyze performance patterns
        patterns = await self._identify_performance_patterns(agent_id, examples)
        
        # Generate suggestions based on patterns
        suggestions = []
        for pattern in patterns:
            pattern_suggestions = await self._generate_suggestions_from_pattern(agent_id, pattern)
            suggestions.extend(pattern_suggestions)
        
        # Store suggestions
        self.improvement_suggestions[agent_id].extend(suggestions)
        self.learning_metrics["improvements_suggested"] += len(suggestions)
        
        return suggestions
    
    async def apply_improvement(self, agent_id: str, suggestion: ImprovementSuggestion) -> bool:
        """
        Apply an improvement suggestion to an agent
        
        Args:
            agent_id: ID of the agent to improve
            suggestion: The improvement suggestion to apply
            
        Returns:
            True if improvement was applied successfully
        """
        try:
            if suggestion.suggestion_type == "prompt":
                return await self._apply_prompt_improvement(agent_id, suggestion)
            elif suggestion.suggestion_type == "strategy":
                return await self._apply_strategy_improvement(agent_id, suggestion)
            elif suggestion.suggestion_type == "parameter":
                return await self._apply_parameter_improvement(agent_id, suggestion)
            else:
                logger.warning(f"Unknown improvement type: {suggestion.suggestion_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to apply improvement for agent {agent_id}: {str(e)}")
            return False
    
    def get_agent_knowledge(self, agent_id: str) -> Dict[str, Any]:
        """
        Get accumulated knowledge for an agent
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary with agent knowledge
        """
        return self.agent_knowledge.get(agent_id, {})
    
    def update_agent_knowledge(self, agent_id: str, knowledge_update: Dict[str, Any]):
        """
        Update knowledge base for an agent
        
        Args:
            agent_id: ID of the agent
            knowledge_update: Knowledge to add/update
        """
        if agent_id not in self.agent_knowledge:
            self.agent_knowledge[agent_id] = {}
        
        self.agent_knowledge[agent_id].update(knowledge_update)
        
        # Save updated knowledge
        self._save_agent_knowledge(agent_id)
        
        logger.info(f"Updated knowledge for agent {agent_id}")
    
    def get_learning_metrics(self) -> Dict[str, Any]:
        """
        Get learning system metrics
        
        Returns:
            Dictionary with learning metrics
        """
        # Calculate additional metrics
        total_agents_with_examples = len([
            agent_id for agent_id, examples in self.learning_examples.items()
            if len(examples) > 0
        ])
        
        avg_examples_per_agent = (
            self.learning_metrics["total_examples_collected"] / max(total_agents_with_examples, 1)
        )
        
        return {
            **self.learning_metrics,
            "total_agents_with_examples": total_agents_with_examples,
            "avg_examples_per_agent": avg_examples_per_agent,
            "learning_patterns_count": sum(len(patterns) for patterns in self.learning_patterns.values()),
            "pending_suggestions": sum(len(suggestions) for suggestions in self.improvement_suggestions.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _analyze_patterns_periodically(self):
        """Background task to analyze learning patterns"""
        while True:
            try:
                # Analyze patterns for all agents with sufficient examples
                for agent_id, examples in self.learning_examples.items():
                    if len(examples) >= self.learning_config["min_examples_for_pattern"]:
                        await self._analyze_agent_patterns(agent_id)
                
                await asyncio.sleep(self.learning_config["pattern_analysis_interval"])
                
            except Exception as e:
                logger.error(f"Error in pattern analysis: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _update_knowledge_bases(self):
        """Background task to update agent knowledge bases"""
        while True:
            try:
                for agent_id in self.learning_examples.keys():
                    await self._update_agent_knowledge_base(agent_id)
                
                await asyncio.sleep(self.learning_config["knowledge_update_interval"])
                
            except Exception as e:
                logger.error(f"Error updating knowledge bases: {str(e)}")
                await asyncio.sleep(300)
    
    async def _generate_improvements(self):
        """Background task to generate improvement suggestions"""
        while True:
            try:
                for agent_id in self.learning_examples.keys():
                    suggestions = await self.generate_improvement_suggestions(agent_id)
                    if suggestions:
                        logger.info(f"Generated {len(suggestions)} improvement suggestions for agent {agent_id}")
                
                await asyncio.sleep(3600)  # Generate improvements every hour
                
            except Exception as e:
                logger.error(f"Error generating improvements: {str(e)}")
                await asyncio.sleep(300)
    
    async def _analyze_agent_patterns(self, agent_id: str):
        """Analyze patterns for a specific agent"""
        examples = list(self.learning_examples[agent_id])
        if len(examples) < self.learning_config["min_examples_for_pattern"]:
            return
        
        # Identify patterns using AI analysis
        patterns = await self._identify_performance_patterns(agent_id, examples)
        
        # Store identified patterns
        self.learning_patterns[agent_id] = patterns
        self.learning_metrics["patterns_identified"] += len(patterns)
        
        logger.info(f"Identified {len(patterns)} patterns for agent {agent_id}")
    
    async def _identify_performance_patterns(
        self,
        agent_id: str,
        examples: List[LearningExample]
    ) -> List[LearningPattern]:
        """Identify performance patterns from examples using AI analysis"""
        
        # Separate high and low quality examples
        high_quality = [ex for ex in examples if ex.quality_score >= 0.7]
        low_quality = [ex for ex in examples if ex.quality_score < 0.5]
        
        if len(high_quality) < 3 or len(low_quality) < 3:
            return []
        
        # Analyze patterns using AI
        analysis_prompt = self._create_pattern_analysis_prompt(high_quality, low_quality)
        
        try:
            analysis_result = await self.ai_service.generate_text(
                prompt=analysis_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse analysis result into patterns
            patterns = self._parse_pattern_analysis(agent_id, analysis_result, examples)
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze patterns for agent {agent_id}: {str(e)}")
            return []
    
    def _create_pattern_analysis_prompt(
        self,
        high_quality_examples: List[LearningExample],
        low_quality_examples: List[LearningExample]
    ) -> str:
        """Create prompt for AI pattern analysis"""
        
        prompt_parts = [
            "Analyze the following agent performance examples to identify patterns that lead to high vs low quality responses.",
            "",
            "HIGH QUALITY EXAMPLES (score >= 0.7):",
        ]
        
        for i, example in enumerate(high_quality_examples[:5]):  # Limit to 5 examples
            prompt_parts.extend([
                f"\nExample {i+1}:",
                f"Request: {json.dumps(example.request_content, indent=2)[:500]}...",
                f"Response: {json.dumps(example.response_content, indent=2)[:500]}...",
                f"Quality Score: {example.quality_score}",
                f"User Feedback: {example.user_feedback or 'None'}"
            ])
        
        prompt_parts.extend([
            "",
            "LOW QUALITY EXAMPLES (score < 0.5):",
        ])
        
        for i, example in enumerate(low_quality_examples[:5]):
            prompt_parts.extend([
                f"\nExample {i+1}:",
                f"Request: {json.dumps(example.request_content, indent=2)[:500]}...",
                f"Response: {json.dumps(example.response_content, indent=2)[:500]}...",
                f"Quality Score: {example.quality_score}",
                f"User Feedback: {example.user_feedback or 'None'}"
            ])
        
        prompt_parts.extend([
            "",
            "Please identify:",
            "1. Common characteristics of high-quality responses",
            "2. Common characteristics of low-quality responses", 
            "3. Specific patterns that correlate with success/failure",
            "4. Actionable improvement recommendations",
            "",
            "Format your response as JSON with the following structure:",
            "{",
            '  "success_patterns": ["pattern1", "pattern2", ...],',
            '  "failure_patterns": ["pattern1", "pattern2", ...],',
            '  "improvement_actions": ["action1", "action2", ...],',
            '  "confidence": 0.8',
            "}"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_pattern_analysis(
        self,
        agent_id: str,
        analysis_result: str,
        examples: List[LearningExample]
    ) -> List[LearningPattern]:
        """Parse AI analysis result into learning patterns"""
        
        try:
            # Try to parse JSON from the analysis result
            import re
            json_match = re.search(r'\{.*\}', analysis_result, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                logger.warning("Could not parse JSON from pattern analysis")
                return []
            
            # Create learning pattern
            pattern = LearningPattern(
                pattern_id=f"{agent_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                agent_type=examples[0].agent_type if examples else AgentType.CAREER_STRATEGY,
                pattern_description=f"Analysis of {len(examples)} examples",
                success_conditions={
                    "patterns": analysis_data.get("success_patterns", [])
                },
                failure_conditions={
                    "patterns": analysis_data.get("failure_patterns", [])
                },
                improvement_actions=analysis_data.get("improvement_actions", []),
                confidence=analysis_data.get("confidence", 0.5),
                examples_count=len(examples)
            )
            
            return [pattern]
            
        except Exception as e:
            logger.error(f"Failed to parse pattern analysis: {str(e)}")
            return []
    
    async def _generate_suggestions_from_pattern(
        self,
        agent_id: str,
        pattern: LearningPattern
    ) -> List[ImprovementSuggestion]:
        """Generate improvement suggestions from a learning pattern"""
        
        suggestions = []
        
        for i, action in enumerate(pattern.improvement_actions):
            suggestion = ImprovementSuggestion(
                agent_id=agent_id,
                suggestion_type="strategy",  # Default type
                description=action,
                expected_improvement=0.1 * pattern.confidence,  # Estimate improvement
                confidence=pattern.confidence,
                implementation_priority=i + 1,
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    async def _apply_prompt_improvement(
        self,
        agent_id: str,
        suggestion: ImprovementSuggestion
    ) -> bool:
        """Apply a prompt-based improvement"""
        # This would integrate with the agent's prompt system
        # For now, just store the improvement in knowledge base
        
        knowledge_update = {
            "prompt_improvements": self.agent_knowledge[agent_id].get("prompt_improvements", [])
        }
        knowledge_update["prompt_improvements"].append({
            "suggestion": suggestion.description,
            "applied_at": datetime.utcnow().isoformat(),
            "expected_improvement": suggestion.expected_improvement
        })
        
        self.update_agent_knowledge(agent_id, knowledge_update)
        self.learning_metrics["improvements_implemented"] += 1
        
        return True
    
    async def _apply_strategy_improvement(
        self,
        agent_id: str,
        suggestion: ImprovementSuggestion
    ) -> bool:
        """Apply a strategy-based improvement"""
        # Store strategy improvement in knowledge base
        
        knowledge_update = {
            "strategy_improvements": self.agent_knowledge[agent_id].get("strategy_improvements", [])
        }
        knowledge_update["strategy_improvements"].append({
            "suggestion": suggestion.description,
            "applied_at": datetime.utcnow().isoformat(),
            "expected_improvement": suggestion.expected_improvement
        })
        
        self.update_agent_knowledge(agent_id, knowledge_update)
        self.learning_metrics["improvements_implemented"] += 1
        
        return True
    
    async def _apply_parameter_improvement(
        self,
        agent_id: str,
        suggestion: ImprovementSuggestion
    ) -> bool:
        """Apply a parameter-based improvement"""
        # Store parameter improvement in knowledge base
        
        knowledge_update = {
            "parameter_improvements": self.agent_knowledge[agent_id].get("parameter_improvements", [])
        }
        knowledge_update["parameter_improvements"].append({
            "suggestion": suggestion.description,
            "applied_at": datetime.utcnow().isoformat(),
            "expected_improvement": suggestion.expected_improvement
        })
        
        self.update_agent_knowledge(agent_id, knowledge_update)
        self.learning_metrics["improvements_implemented"] += 1
        
        return True
    
    async def _update_agent_knowledge_base(self, agent_id: str):
        """Update knowledge base for a specific agent"""
        examples = list(self.learning_examples[agent_id])
        if len(examples) < 5:
            return
        
        # Extract knowledge from recent high-quality examples
        recent_examples = [ex for ex in examples[-20:] if ex.quality_score >= 0.7]
        
        if recent_examples:
            # Analyze successful patterns
            knowledge_update = await self._extract_knowledge_from_examples(recent_examples)
            self.update_agent_knowledge(agent_id, knowledge_update)
    
    async def _extract_knowledge_from_examples(
        self,
        examples: List[LearningExample]
    ) -> Dict[str, Any]:
        """Extract actionable knowledge from examples"""
        
        # Group examples by request type
        by_request_type = defaultdict(list)
        for example in examples:
            request_type = example.request_content.get("request_type", "unknown")
            by_request_type[request_type].append(example)
        
        knowledge = {
            "successful_patterns": {},
            "best_practices": [],
            "common_success_factors": [],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Analyze patterns for each request type
        for request_type, type_examples in by_request_type.items():
            if len(type_examples) >= 3:
                # Extract common elements from successful responses
                common_elements = self._find_common_response_elements(type_examples)
                knowledge["successful_patterns"][request_type] = common_elements
        
        return knowledge
    
    def _find_common_response_elements(self, examples: List[LearningExample]) -> Dict[str, Any]:
        """Find common elements in successful responses"""
        
        # This is a simplified implementation
        # In practice, this would use more sophisticated analysis
        
        common_elements = {
            "response_structure": {},
            "content_patterns": [],
            "quality_indicators": []
        }
        
        # Analyze response structures
        structures = []
        for example in examples:
            if isinstance(example.response_content, dict):
                structures.append(list(example.response_content.keys()))
        
        if structures:
            # Find most common keys
            all_keys = [key for structure in structures for key in structure]
            key_counts = defaultdict(int)
            for key in all_keys:
                key_counts[key] += 1
            
            # Keys that appear in >50% of responses
            common_keys = [
                key for key, count in key_counts.items()
                if count > len(examples) * 0.5
            ]
            common_elements["response_structure"]["common_keys"] = common_keys
        
        return common_elements
    
    def _load_learning_data(self):
        """Load existing learning data from disk"""
        try:
            # Load agent knowledge
            knowledge_file = os.path.join(self.learning_data_dir, "agent_knowledge.pkl")
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'rb') as f:
                    self.agent_knowledge = pickle.load(f)
            
            # Load learning patterns
            patterns_file = os.path.join(self.learning_data_dir, "learning_patterns.pkl")
            if os.path.exists(patterns_file):
                with open(patterns_file, 'rb') as f:
                    self.learning_patterns = pickle.load(f)
            
            logger.info("Loaded existing learning data")
            
        except Exception as e:
            logger.warning(f"Could not load learning data: {str(e)}")
    
    def _save_agent_knowledge(self, agent_id: str):
        """Save agent knowledge to disk"""
        try:
            knowledge_file = os.path.join(self.learning_data_dir, "agent_knowledge.pkl")
            with open(knowledge_file, 'wb') as f:
                pickle.dump(dict(self.agent_knowledge), f)
                
        except Exception as e:
            logger.error(f"Failed to save agent knowledge: {str(e)}")
    
    def save_all_learning_data(self):
        """Save all learning data to disk"""
        try:
            # Save agent knowledge
            knowledge_file = os.path.join(self.learning_data_dir, "agent_knowledge.pkl")
            with open(knowledge_file, 'wb') as f:
                pickle.dump(dict(self.agent_knowledge), f)
            
            # Save learning patterns
            patterns_file = os.path.join(self.learning_data_dir, "learning_patterns.pkl")
            with open(patterns_file, 'wb') as f:
                pickle.dump(dict(self.learning_patterns), f)
            
            # Save metrics
            metrics_file = os.path.join(self.learning_data_dir, "learning_metrics.json")
            with open(metrics_file, 'w') as f:
                json.dump(self.learning_metrics, f, indent=2)
            
            logger.info("Saved all learning data")
            
        except Exception as e:
            logger.error(f"Failed to save learning data: {str(e)}")