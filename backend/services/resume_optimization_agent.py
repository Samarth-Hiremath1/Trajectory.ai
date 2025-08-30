"""
Resume Optimization Agent for comprehensive resume analysis and improvement suggestions
"""
import logging
import json
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

from models.agent import (
    AgentType, AgentRequest, AgentResponse, AgentCapability, 
    MessageType, RequestType
)
from services.base_agent import BaseAgent
from services.ai_service import AIService, ModelType
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class ResumeOptimizationAgent(BaseAgent):
    """
    Specialized agent for comprehensive resume analysis and optimization.
    Provides resume structure analysis, keyword optimization, and ATS compatibility improvements.
    """
    
    def __init__(
        self,
        agent_id: str,
        ai_service: AIService,
        embedding_service: EmbeddingService,
        max_concurrent_requests: int = 3
    ):
        """
        Initialize Resume Optimization Agent
        
        Args:
            agent_id: Unique identifier for this agent instance
            ai_service: AI service for LLM interactions
            embedding_service: Embedding service for ChromaDB access
            max_concurrent_requests: Maximum concurrent requests
        """
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.RESUME_OPTIMIZATION,
            ai_service=ai_service,
            max_concurrent_requests=max_concurrent_requests,
            default_confidence_threshold=0.8
        )
        
        self.embedding_service = embedding_service
        
        # Register message handlers for inter-agent communication
        self._register_message_handlers()
        
        # Resume optimization knowledge base
        self.ats_keywords_database = self._load_ats_keywords_database()
        self.resume_templates = self._load_resume_templates()
        self.industry_standards = self._load_industry_standards()
        
        logger.info(f"Resume Optimization Agent {agent_id} initialized")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of the Resume Optimization Agent"""
        return [
            AgentCapability(
                name="resume_structure_analysis",
                description="Analyze resume structure and provide improvement suggestions",
                input_types=["resume_content", "target_role", "industry"],
                output_types=["structure_analysis", "improvement_suggestions", "formatting_recommendations"],
                confidence_threshold=0.85,
                max_processing_time=30
            ),
            AgentCapability(
                name="keyword_optimization",
                description="Optimize resume keywords for ATS compatibility and target roles",
                input_types=["resume_content", "job_descriptions", "target_role"],
                output_types=["keyword_analysis", "ats_optimization", "keyword_suggestions"],
                confidence_threshold=0.8,
                max_processing_time=25
            ),
            AgentCapability(
                name="achievement_validation",
                description="Validate and quantify resume achievements and accomplishments",
                input_types=["achievements", "work_experience", "industry_context"],
                output_types=["achievement_analysis", "quantification_suggestions", "impact_metrics"],
                confidence_threshold=0.8,
                max_processing_time=35
            ),
            AgentCapability(
                name="formatting_optimization",
                description="Optimize resume formatting and presentation for maximum impact",
                input_types=["resume_format", "target_audience", "industry_standards"],
                output_types=["formatting_recommendations", "design_suggestions", "readability_improvements"],
                confidence_threshold=0.75,
                max_processing_time=20
            ),
            AgentCapability(
                name="ats_compatibility_check",
                description="Check and improve ATS (Applicant Tracking System) compatibility",
                input_types=["resume_content", "ats_requirements", "target_systems"],
                output_types=["ats_score", "compatibility_issues", "optimization_recommendations"],
                confidence_threshold=0.8,
                max_processing_time=25
            )
        ]
    
    def _register_message_handlers(self):
        """Register handlers for inter-agent messages"""
        self.register_message_handler(
            MessageType.COLLABORATION_REQUEST,
            self._handle_collaboration_request
        )
        self.register_message_handler(
            MessageType.CONTEXT_SHARE,
            self._handle_context_share
        )
        self.register_message_handler(
            MessageType.INSIGHT_SHARE,
            self._handle_insight_share
        )
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Process a resume optimization request
        
        Args:
            request: The request to process
            
        Returns:
            AgentResponse with resume optimization results
        """
        try:
            # Extract request details
            content = request.content
            context = request.context
            request_type = request.request_type
            
            # Route to appropriate handler based on request type
            if request_type == RequestType.RESUME_REVIEW:
                result = await self._perform_comprehensive_resume_analysis(content, context)
            elif request_type == RequestType.CAREER_TRANSITION:
                result = await self._optimize_resume_for_transition(content, context)
            elif request_type == RequestType.ROADMAP_GENERATION:
                result = await self._contribute_to_roadmap_resume_optimization(content, context)
            else:
                # Default to general resume advice
                result = await self._provide_resume_optimization_advice(content, context)
            
            # Calculate confidence score based on result quality
            confidence = self._calculate_confidence(result, request)
            
            return AgentResponse(
                request_id=request.id,
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=result,
                confidence_score=confidence,
                processing_time=0.0,  # Will be set by base class
                metadata={
                    "optimization_type": request_type.value,
                    "sections_analyzed": len(result.get("section_analysis", {})),
                    "keywords_suggested": len(result.get("keyword_suggestions", [])),
                    "improvements_identified": len(result.get("improvement_suggestions", []))
                }
            )
            
        except Exception as e:
            logger.error(f"Resume Optimization Agent failed to process request: {str(e)}")
            raise 
   
    async def _perform_comprehensive_resume_analysis(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive resume analysis"""
        user_id = content.get("user_id", "")
        target_role = content.get("target_role", "")
        
        # Get user resume content
        resume_content = await self._get_user_resume_content(user_id)
        
        # Perform analysis
        structure_analysis = await self._analyze_resume_structure(resume_content, target_role)
        keyword_analysis = await self._analyze_keywords_and_ats_compatibility(resume_content, target_role, [])
        achievement_analysis = await self._analyze_and_validate_achievements(resume_content, target_role)
        formatting_analysis = await self._analyze_formatting_and_presentation(resume_content, target_role)
        
        # Generate recommendations
        optimization_recommendations = await self._generate_optimization_recommendations(
            structure_analysis, keyword_analysis, achievement_analysis, formatting_analysis
        )
        
        # Calculate overall score
        resume_score = self._calculate_overall_resume_score(
            structure_analysis, keyword_analysis, achievement_analysis, formatting_analysis
        )
        
        return {
            "comprehensive_analysis": {
                "overall_score": resume_score,
                "target_role": target_role,
                "analysis_date": datetime.utcnow().isoformat(),
                "key_strengths": self._identify_resume_strengths(structure_analysis, achievement_analysis),
                "critical_issues": self._identify_critical_issues(structure_analysis, keyword_analysis)
            },
            "structure_analysis": structure_analysis,
            "keyword_analysis": keyword_analysis,
            "achievement_analysis": achievement_analysis,
            "formatting_analysis": formatting_analysis,
            "optimization_recommendations": optimization_recommendations
        }
    
    async def _optimize_resume_for_transition(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize resume for career transition"""
        current_role = content.get("current_role", "")
        target_role = content.get("target_role", "")
        user_id = content.get("user_id", "")
        
        resume_content = await self._get_user_resume_content(user_id)
        
        return {
            "transition_optimization": {
                "current_role": current_role,
                "target_role": target_role,
                "transition_difficulty": self._assess_resume_transition_difficulty(current_role, target_role),
                "optimization_strategy": "Emphasize transferable skills and relevant experience"
            },
            "transition_recommendations": [
                {"recommendation": "Highlight transferable skills", "priority": "high"},
                {"recommendation": "Reframe achievements for target role", "priority": "high"}
            ]
        }
    
    async def _contribute_to_roadmap_resume_optimization(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Contribute resume optimization to roadmap"""
        user_id = content.get("user_id", "")
        target_role = content.get("target_role", "")
        timeline = content.get("timeline", "12 months")
        
        return {
            "resume_optimization_contribution": {
                "improvement_timeline": self._create_resume_improvement_timeline(timeline),
                "achievement_building_strategy": self._create_achievement_building_strategy(target_role),
                "continuous_optimization_plan": self._create_continuous_optimization_plan(timeline)
            }
        }
    
    async def _provide_resume_optimization_advice(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general resume optimization advice"""
        question = content.get("question", content.get("message", ""))
        user_id = content.get("user_id", "")
        
        resume_content = await self._get_user_resume_content(user_id)
        
        advice_prompt = self._create_resume_optimization_advice_prompt(question, resume_content)
        
        advice_content = await self.generate_ai_response(
            prompt=advice_prompt,
            system_prompt=self._get_resume_optimization_advice_system_prompt(),
            model_type=ModelType.GEMINI_FLASH,
            max_tokens=800,
            temperature=0.7
        )
        
        return {
            "resume_optimization_advice": advice_content,
            "actionable_recommendations": self._extract_actionable_recommendations(advice_content),
            "quick_wins": self._identify_quick_resume_wins(question, resume_content),
            "common_mistakes_to_avoid": self._identify_common_resume_mistakes(question),
            "industry_specific_tips": self._provide_industry_specific_tips(question)
        }
    
    async def _get_user_resume_content(self, user_id: str) -> Dict[str, Any]:
        """Retrieve user resume content"""
        if not user_id:
            return self._get_default_resume_content()
        
        try:
            resume_results = self.embedding_service.search_user_context(
                user_id=user_id,
                query="resume work experience education skills achievements projects",
                n_results=15
            )
            
            combined_content = {
                "raw_content": "",
                "sections": {
                    "contact_info": "",
                    "summary": "",
                    "experience": [],
                    "education": [],
                    "skills": [],
                    "achievements": [],
                    "projects": [],
                    "certifications": []
                },
                "metadata": {
                    "length": 0,
                    "format": "unknown",
                    "last_updated": None
                }
            }
            
            for result in resume_results:
                content = result.get("content", "")
                source = result.get("source", "unknown")
                
                if source == "resume":
                    combined_content["raw_content"] += f" {content}"
                    structured_info = self._extract_structured_resume_info(content)
                    self._merge_resume_sections(combined_content["sections"], structured_info)
            
            combined_content["metadata"]["length"] = len(combined_content["raw_content"])
            combined_content["metadata"]["last_updated"] = datetime.utcnow().isoformat()
            
            return combined_content if combined_content["raw_content"] else self._get_default_resume_content()
            
        except Exception as e:
            logger.error(f"Failed to get user resume content: {str(e)}")
            return self._get_default_resume_content()
    
    def _get_default_resume_content(self) -> Dict[str, Any]:
        """Get default resume content for testing/fallback"""
        return {
            "raw_content": "Software Engineer with 3 years experience in Python, JavaScript, and SQL. Led team projects and improved system performance.",
            "sections": {
                "contact_info": "John Doe, Software Engineer",
                "summary": "Experienced software engineer",
                "experience": ["Software Engineer at Tech Corp (2021-2024)"],
                "education": ["BS Computer Science"],
                "skills": ["Python", "JavaScript", "SQL"],
                "achievements": ["Improved system performance by 25%"],
                "projects": ["E-commerce platform"],
                "certifications": []
            },
            "metadata": {
                "length": 150,
                "format": "text",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    
    def _calculate_confidence(self, result: Dict[str, Any], request: AgentRequest) -> float:
        """Calculate confidence score for the response"""
        base_confidence = 0.8
        
        if len(str(result)) < 1000:
            base_confidence -= 0.1
        
        if request.request_type == RequestType.RESUME_REVIEW:
            base_confidence += 0.05
        
        if result.get("structure_analysis") and result.get("keyword_analysis"):
            base_confidence += 0.05
        
        return min(max(base_confidence, 0.0), 1.0)    
  
  # Helper methods for resume analysis
    def _extract_structured_resume_info(self, content: str) -> Dict[str, Any]:
        """Extract structured information from resume text"""
        structured_info = {
            "experience": [],
            "education": [],
            "skills": [],
            "achievements": [],
            "projects": [],
            "certifications": []
        }
        
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["experience", "work", "employment"]):
            structured_info["experience"].append(content)
        
        if any(word in content_lower for word in ["education", "degree", "university", "college"]):
            structured_info["education"].append(content)
        
        if any(word in content_lower for word in ["skills", "technologies", "programming"]):
            structured_info["skills"].append(content)
        
        return structured_info
    
    def _merge_resume_sections(self, existing_sections: Dict[str, Any], new_info: Dict[str, Any]):
        """Merge new resume information into existing sections"""
        for section, content in new_info.items():
            if section in existing_sections:
                if isinstance(existing_sections[section], list):
                    existing_sections[section].extend(content if isinstance(content, list) else [content])
                else:
                    existing_sections[section] += f" {content}" if content else ""
    
    # Analysis methods
    async def _analyze_resume_structure(self, resume_content: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        """Analyze resume structure and organization"""
        sections = resume_content.get('sections', {})
        
        expected_sections = ['summary', 'experience', 'education', 'skills']
        present_sections = sum(1 for section in expected_sections if section in sections and sections[section])
        structure_score = present_sections / len(expected_sections)
        
        missing_sections = [section for section in expected_sections if section not in sections or not sections[section]]
        
        if 'engineer' in target_role.lower() and 'projects' not in sections:
            missing_sections.append('projects')
        
        return {
            "organization_rating": structure_score,
            "missing_sections": missing_sections,
            "structure_score": structure_score,
            "recommendations": [f"Add {section} section" for section in missing_sections]
        }
    
    async def _analyze_keywords_and_ats_compatibility(
        self, resume_content: Dict[str, Any], target_role: str, job_descriptions: List[str]
    ) -> Dict[str, Any]:
        """Analyze keywords and ATS compatibility"""
        content = resume_content.get('raw_content', '')
        
        current_keywords = self._extract_keywords_from_resume(content)
        target_keywords = self._get_target_role_keywords(target_role)
        keyword_match_score = self._calculate_keyword_match_score(current_keywords, target_keywords)
        ats_score = self._calculate_ats_score(resume_content)
        
        return {
            "keyword_analysis": {
                "keyword_match_score": keyword_match_score,
                "missing_critical_keywords": self._identify_missing_keywords(current_keywords, target_keywords),
                "current_keywords": current_keywords
            },
            "ats_compatibility": {
                "ats_score": ats_score,
                "compatibility_issues": self._identify_ats_issues(resume_content),
                "ats_recommendations": self._generate_ats_recommendations(resume_content)
            }
        }
    
    async def _analyze_and_validate_achievements(self, resume_content: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        """Analyze and validate resume achievements"""
        achievements = resume_content.get('sections', {}).get('achievements', [])
        experience = resume_content.get('sections', {}).get('experience', [])
        
        all_achievements = achievements + experience
        categorized = self._categorize_achievements(all_achievements)
        achievement_scores = self._calculate_achievement_scores(categorized)
        
        return {
            "achievement_scores": achievement_scores,
            "quantification_opportunities": self._identify_quantification_opportunities(all_achievements),
            "categorized_achievements": categorized
        }
    
    async def _analyze_formatting_and_presentation(self, resume_content: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        """Analyze resume formatting and presentation"""
        content_length = len(resume_content.get('raw_content', ''))
        readability_score = self._calculate_readability_score(resume_content)
        length_assessment = self._assess_resume_length(content_length, target_role)
        
        return {
            "readability_score": readability_score,
            "ats_formatting_score": 0.8,
            "length_assessment": length_assessment
        }
    
    # Helper methods for keyword and ATS analysis
    def _extract_keywords_from_resume(self, content: str) -> List[str]:
        """Extract keywords from resume content"""
        technical_keywords = re.findall(r'\b(?:Python|Java|JavaScript|React|SQL|AWS|Docker|Kubernetes|Git)\b', content, re.IGNORECASE)
        soft_keywords = re.findall(r'\b(?:leadership|management|communication|collaboration|problem-solving)\b', content, re.IGNORECASE)
        return list(set(technical_keywords + soft_keywords))
    
    def _get_target_role_keywords(self, target_role: str) -> List[str]:
        """Get target keywords for a specific role"""
        role_keywords = {
            "software engineer": ["Python", "Java", "JavaScript", "SQL", "Git", "Agile"],
            "product manager": ["Product Management", "Roadmap", "Stakeholder", "Analytics"],
            "data scientist": ["Python", "Machine Learning", "Statistics", "SQL", "Data Analysis"],
            "default": ["Leadership", "Communication", "Problem-solving", "Team collaboration"]
        }
        
        role_lower = target_role.lower()
        for role, keywords in role_keywords.items():
            if role in role_lower:
                return keywords
        
        return role_keywords["default"]
    
    def _calculate_keyword_match_score(self, current_keywords: List[str], target_keywords: List[str]) -> float:
        """Calculate keyword match score"""
        if not target_keywords:
            return 0.5
        
        current_lower = [k.lower() for k in current_keywords]
        matches = sum(1 for keyword in target_keywords if keyword.lower() in current_lower)
        return matches / len(target_keywords)
    
    def _identify_missing_keywords(self, current_keywords: List[str], target_keywords: List[str]) -> List[str]:
        """Identify missing critical keywords"""
        current_lower = [k.lower() for k in current_keywords]
        return [keyword for keyword in target_keywords if keyword.lower() not in current_lower]
    
    def _calculate_ats_score(self, resume_content: Dict[str, Any]) -> float:
        """Calculate ATS compatibility score"""
        content = resume_content.get('raw_content', '')
        sections = resume_content.get('sections', {})
        
        score = 0.8
        
        required_sections = ['experience', 'education', 'skills']
        present_sections = sum(1 for section in required_sections if section in sections and sections[section])
        score += (present_sections / len(required_sections)) * 0.2
        
        if len(content) < 300:
            score -= 0.2
        
        return min(max(score, 0.0), 1.0)
    
    def _identify_ats_issues(self, resume_content: Dict[str, Any]) -> List[str]:
        """Identify ATS compatibility issues"""
        issues = []
        
        content = resume_content.get('raw_content', '')
        sections = resume_content.get('sections', {})
        
        if len(content) < 300:
            issues.append("Resume content too short for effective ATS parsing")
        
        if not sections.get('skills'):
            issues.append("Missing skills section")
        
        if not sections.get('experience'):
            issues.append("Missing work experience section")
        
        return issues
    
    def _generate_ats_recommendations(self, resume_content: Dict[str, Any]) -> List[str]:
        """Generate ATS optimization recommendations"""
        recommendations = []
        issues = self._identify_ats_issues(resume_content)
        
        for issue in issues:
            if "skills section" in issue:
                recommendations.append("Add a dedicated skills section with relevant technical and soft skills")
            elif "experience section" in issue:
                recommendations.append("Add detailed work experience with job titles, companies, and achievements")
            elif "too short" in issue:
                recommendations.append("Expand resume content with more detailed descriptions and achievements")
        
        return recommendations    

    # Achievement analysis methods
    def _categorize_achievements(self, achievements: List[str]) -> Dict[str, List[str]]:
        """Categorize achievements by type"""
        categorized = {
            "quantified": [],
            "leadership": [],
            "technical": [],
            "unquantified": []
        }
        
        for achievement in achievements:
            achievement_text = str(achievement).lower()
            
            if any(char.isdigit() for char in achievement_text) or '%' in achievement_text:
                categorized["quantified"].append(achievement)
            else:
                categorized["unquantified"].append(achievement)
            
            if any(word in achievement_text for word in ['led', 'managed', 'directed']):
                categorized["leadership"].append(achievement)
            
            if any(word in achievement_text for word in ['developed', 'implemented', 'built']):
                categorized["technical"].append(achievement)
        
        return categorized
    
    def _calculate_achievement_scores(self, categorized_achievements: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate scores for different achievement categories"""
        total_achievements = sum(len(achievements) for achievements in categorized_achievements.values())
        
        if total_achievements == 0:
            return {"quantification": 0.0, "diversity": 0.0, "overall": 0.0}
        
        quantified_ratio = len(categorized_achievements.get("quantified", [])) / total_achievements
        categories_with_content = sum(1 for achievements in categorized_achievements.values() if len(achievements) > 0)
        diversity_score = categories_with_content / len(categorized_achievements)
        
        return {
            "quantification": quantified_ratio,
            "diversity": diversity_score,
            "overall": (quantified_ratio * 0.6 + diversity_score * 0.4)
        }
    
    def _identify_quantification_opportunities(self, achievements: List[str]) -> List[Dict[str, str]]:
        """Identify opportunities to quantify achievements"""
        opportunities = []
        
        for achievement in achievements[:3]:
            achievement_text = str(achievement)
            if not any(char.isdigit() for char in achievement_text) and '%' not in achievement_text:
                opportunities.append({
                    "original": achievement_text,
                    "suggestion": "Add specific metrics like percentages, dollar amounts, or time savings"
                })
        
        return opportunities
    
    def _calculate_readability_score(self, resume_content: Dict[str, Any]) -> float:
        """Calculate resume readability score"""
        content = resume_content.get('raw_content', '')
        
        if not content:
            return 0.5
        
        word_count = len(content.split())
        sentence_count = max(content.count('.') + content.count('!') + content.count('?'), 1)
        avg_words_per_sentence = word_count / sentence_count
        
        if 15 <= avg_words_per_sentence <= 20:
            return 0.9
        elif 10 <= avg_words_per_sentence <= 25:
            return 0.7
        else:
            return 0.5
    
    def _assess_resume_length(self, content_length: int, target_role: str) -> Dict[str, Any]:
        """Assess resume length appropriateness"""
        word_count = content_length // 5
        
        if any(word in target_role.lower() for word in ['senior', 'director', 'manager']):
            optimal_range = (800, 1200)
        else:
            optimal_range = (400, 700)
        
        if optimal_range[0] <= word_count <= optimal_range[1]:
            status = "optimal"
            recommendation = "Resume length is appropriate for the target role"
        elif word_count < optimal_range[0]:
            status = "too_short"
            recommendation = f"Expand content by approximately {optimal_range[0] - word_count} words"
        else:
            status = "too_long"
            recommendation = f"Reduce content by approximately {word_count - optimal_range[1]} words"
        
        return {
            "current_words": word_count,
            "optimal_range": optimal_range,
            "status": status,
            "recommendation": recommendation
        }
    
    # Generation and scoring methods
    async def _generate_optimization_recommendations(
        self, structure_analysis: Dict[str, Any], keyword_analysis: Dict[str, Any], 
        achievement_analysis: Dict[str, Any], formatting_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive optimization recommendations"""
        recommendations = []
        
        missing_sections = structure_analysis.get("missing_sections", [])
        if missing_sections:
            recommendations.append({
                "category": "structure",
                "priority": "high",
                "title": "Add Missing Resume Sections",
                "description": f"Add missing sections: {', '.join(missing_sections)}",
                "impact": "Improves completeness and ATS parsing"
            })
        
        missing_keywords = keyword_analysis.get("keyword_analysis", {}).get("missing_critical_keywords", [])
        if missing_keywords:
            recommendations.append({
                "category": "keywords",
                "priority": "high",
                "title": "Add Critical Keywords",
                "description": f"Incorporate keywords: {', '.join(missing_keywords[:5])}",
                "impact": "Significantly improves ATS matching"
            })
        
        quantification_ops = achievement_analysis.get("quantification_opportunities", [])
        if quantification_ops:
            recommendations.append({
                "category": "achievements",
                "priority": "medium",
                "title": "Quantify Achievements",
                "description": "Add specific numbers, percentages, and metrics to achievements",
                "impact": "Makes accomplishments more credible and impactful"
            })
        
        return recommendations
    
    def _calculate_overall_resume_score(
        self, structure_analysis: Dict[str, Any], keyword_analysis: Dict[str, Any],
        achievement_analysis: Dict[str, Any], formatting_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall resume score"""
        structure_score = structure_analysis.get("organization_rating", 0.7) * 0.25
        keyword_score = keyword_analysis.get("keyword_analysis", {}).get("keyword_match_score", 0.6) * 0.30
        achievement_score = achievement_analysis.get("achievement_scores", {}).get("overall", 0.6) * 0.25
        formatting_score = formatting_analysis.get("readability_score", 0.7) * 0.20
        
        overall_score = structure_score + keyword_score + achievement_score + formatting_score
        
        return {
            "overall_score": min(max(overall_score, 0.0), 1.0),
            "breakdown": {
                "structure": structure_score / 0.25,
                "keywords": keyword_score / 0.30,
                "achievements": achievement_score / 0.25,
                "formatting": formatting_score / 0.20
            },
            "grade": self._score_to_grade(overall_score),
            "percentile": int(overall_score * 100)
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B+"
        elif score >= 0.6:
            return "B"
        elif score >= 0.5:
            return "C+"
        else:
            return "C"
    
    def _identify_resume_strengths(self, structure_analysis: Dict[str, Any], achievement_analysis: Dict[str, Any]) -> List[str]:
        """Identify resume strengths"""
        strengths = []
        
        if structure_analysis.get("organization_rating", 0) > 0.8:
            strengths.append("Well-organized structure with all key sections")
        
        if achievement_analysis.get("achievement_scores", {}).get("quantification", 0) > 0.7:
            strengths.append("Good use of quantified achievements")
        
        if achievement_analysis.get("achievement_scores", {}).get("diversity", 0) > 0.6:
            strengths.append("Diverse range of accomplishments")
        
        return strengths if strengths else ["Professional presentation", "Relevant experience included"]
    
    def _identify_critical_issues(self, structure_analysis: Dict[str, Any], keyword_analysis: Dict[str, Any]) -> List[str]:
        """Identify critical resume issues"""
        issues = []
        
        missing_sections = structure_analysis.get("missing_sections", [])
        if missing_sections:
            issues.append(f"Missing critical sections: {', '.join(missing_sections)}")
        
        missing_keywords = keyword_analysis.get("keyword_analysis", {}).get("missing_critical_keywords", [])
        if len(missing_keywords) > 3:
            issues.append("Lacks key industry keywords for ATS optimization")
        
        ats_score = keyword_analysis.get("ats_compatibility", {}).get("ats_score", 0.8)
        if ats_score < 0.6:
            issues.append("Poor ATS compatibility may limit visibility")
        
        return issues if issues else ["Minor formatting improvements needed"]
    
    # Transition and roadmap methods
    def _assess_resume_transition_difficulty(self, current_role: str, target_role: str) -> str:
        """Assess difficulty of resume transition"""
        if current_role.lower() in target_role.lower() or target_role.lower() in current_role.lower():
            return "low"
        elif any(keyword in current_role.lower() and keyword in target_role.lower() 
                for keyword in ["manager", "analyst", "engineer"]):
            return "medium"
        else:
            return "high"
    
    def _create_resume_improvement_timeline(self, timeline: str) -> Dict[str, str]:
        """Create timeline for resume improvements"""
        return {
            "month_1": "Complete structure optimization and add missing sections",
            "month_2": "Quantify achievements and optimize keywords",
            "month_3": "Final formatting and ATS optimization",
            "ongoing": "Regular updates based on job applications and feedback"
        }
    
    def _create_achievement_building_strategy(self, target_role: str) -> Dict[str, Any]:
        """Create strategy for building achievements"""
        return {
            "strategy": f"Focus on achievements relevant to {target_role} success",
            "metrics_focus": ["Performance improvements", "Team leadership", "Project outcomes"],
            "documentation_approach": "Track quantifiable results from current work"
        }
    
    def _create_continuous_optimization_plan(self, timeline: str) -> Dict[str, Any]:
        """Create continuous optimization plan"""
        return {
            "plan": "Monthly resume reviews and updates based on market feedback",
            "tracking": "Monitor application response rates and adjust accordingly",
            "updates": "Incorporate new achievements and skills as they develop"
        }
    
    # Advice generation methods
    def _create_resume_optimization_advice_prompt(self, question: str, resume_content: Dict[str, Any]) -> str:
        """Create prompt for resume optimization advice"""
        return f"""
        Provide specific resume optimization advice for: {question}
        
        Resume Context:
        - Content Length: {len(resume_content.get('raw_content', ''))} characters
        - Sections Present: {list(resume_content.get('sections', {}).keys())}
        
        Focus on actionable, specific recommendations that address the question while considering:
        1. Current resume optimization best practices
        2. ATS compatibility requirements
        3. Recruiter and hiring manager preferences
        4. Industry-specific considerations
        5. Measurable improvement strategies
        
        Provide practical, implementable recommendations with immediate impact.
        """
    
    def _get_resume_optimization_advice_system_prompt(self) -> str:
        """Get system prompt for resume optimization advice"""
        return """You are a resume optimization specialist providing targeted advice for resume improvement. 
        Focus on actionable, specific recommendations that address the user's question while considering 
        current best practices in resume writing, ATS optimization, and recruiter preferences."""
    
    def _extract_actionable_recommendations(self, advice_content: str) -> List[Dict[str, str]]:
        """Extract actionable recommendations from advice"""
        return [
            {"action": "Quantify achievements with specific metrics", "priority": "high", "timeframe": "immediate"},
            {"action": "Add relevant keywords for target role", "priority": "high", "timeframe": "1-2 hours"},
            {"action": "Improve formatting for ATS compatibility", "priority": "medium", "timeframe": "2-3 hours"}
        ]
    
    def _identify_quick_resume_wins(self, question: str, resume_content: Dict[str, Any]) -> List[str]:
        """Identify quick wins for resume improvement"""
        quick_wins = []
        
        sections = resume_content.get('sections', {})
        
        if not sections.get('summary'):
            quick_wins.append("Add a compelling professional summary at the top")
        
        if len(sections.get('skills', [])) < 5:
            quick_wins.append("Expand skills section with relevant technical and soft skills")
        
        quick_wins.extend([
            "Use action verbs to start bullet points (developed, implemented, led)",
            "Add specific numbers and percentages to achievements",
            "Ensure consistent formatting throughout the document"
        ])
        
        return quick_wins[:5]
    
    def _identify_common_resume_mistakes(self, question: str) -> List[str]:
        """Identify common resume mistakes to avoid"""
        return [
            "Using passive language instead of active action verbs",
            "Including irrelevant work experience or outdated skills",
            "Failing to customize resume for specific job applications",
            "Using generic objective statements instead of targeted summaries",
            "Having inconsistent formatting or fonts throughout",
            "Listing job duties instead of achievements and accomplishments"
        ]
    
    def _provide_industry_specific_tips(self, question: str) -> List[str]:
        """Provide industry-specific resume tips"""
        if any(word in question.lower() for word in ['tech', 'software', 'engineering', 'developer']):
            return [
                "Include a projects section showcasing technical work",
                "List programming languages and frameworks prominently",
                "Mention contributions to open source projects",
                "Quantify technical achievements (performance improvements, user growth)"
            ]
        elif any(word in question.lower() for word in ['finance', 'banking', 'investment']):
            return [
                "Emphasize quantifiable financial results and ROI",
                "Include relevant certifications (CFA, FRM, etc.)",
                "Highlight regulatory compliance experience",
                "Show progression in responsibility and deal size"
            ]
        else:
            return [
                "Tailor resume to specific industry requirements",
                "Use industry-relevant keywords and terminology",
                "Highlight transferable skills for career transitions",
                "Research industry-specific resume formats and expectations"
            ]
    
    # Knowledge base loading methods
    def _load_ats_keywords_database(self) -> Dict[str, Any]:
        """Load ATS keywords database"""
        return {
            "common_ats_keywords": ["experience", "skills", "education", "achievements"],
            "industry_specific": {
                "tech": ["programming", "software", "development", "engineering"],
                "finance": ["analysis", "financial", "investment", "portfolio"],
                "healthcare": ["patient", "clinical", "medical", "healthcare"]
            },
            "role_specific": {
                "manager": ["leadership", "team", "management", "strategy"],
                "analyst": ["analysis", "data", "research", "insights"],
                "engineer": ["technical", "design", "implementation", "systems"]
            }
        }
    
    def _load_resume_templates(self) -> Dict[str, Any]:
        """Load resume templates and formats"""
        return {
            "templates": ["chronological", "functional", "combination"],
            "best_practices": [
                "Use consistent formatting",
                "Include quantified achievements",
                "Optimize for ATS systems",
                "Tailor to specific roles"
            ],
            "industry_standards": {
                "tech": "Focus on projects and technical skills",
                "finance": "Emphasize quantifiable results and certifications",
                "creative": "Include portfolio and creative achievements"
            }
        }
    
    def _load_industry_standards(self) -> Dict[str, Any]:
        """Load industry-specific resume standards"""
        return {
            "tech": {
                "key_sections": ["summary", "technical_skills", "projects", "experience"],
                "preferred_length": "1-2 pages",
                "important_keywords": ["programming", "frameworks", "methodologies"]
            },
            "finance": {
                "key_sections": ["summary", "experience", "education", "certifications"],
                "preferred_length": "1-2 pages",
                "important_keywords": ["analysis", "financial", "risk", "compliance"]
            },
            "healthcare": {
                "key_sections": ["summary", "clinical_experience", "education", "licenses"],
                "preferred_length": "2-3 pages",
                "important_keywords": ["patient_care", "clinical", "medical", "healthcare"]
            }
        }
    
    # Message handlers for inter-agent communication
    async def _handle_collaboration_request(self, message):
        """Handle collaboration requests from other agents"""
        logger.info(f"Resume Optimization Agent received collaboration request: {message.content}")
    
    async def _handle_context_share(self, message):
        """Handle context sharing from other agents"""
        logger.info(f"Resume Optimization Agent received context share: {message.content}")
    
    async def _handle_insight_share(self, message):
        """Handle insight sharing from other agents"""
        logger.info(f"Resume Optimization Agent received insight share: {message.content}")