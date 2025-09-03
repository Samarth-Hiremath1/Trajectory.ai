import asyncio
import json
import logging
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import uuid

from models.roadmap import (
    Roadmap, RoadmapPhase, Skill, LearningResource, Milestone,
    RoadmapRequest, RoadmapGenerationResult, SkillLevel, ResourceType
)
from services.ai_service import get_ai_service, ModelType
from services.roadmap_scraper import get_roadmap_scraper
from services.database_service import DatabaseService

# Optional embedding service import
try:
    from services.embedding_service import get_embedding_service
    EMBEDDING_AVAILABLE = True
except ImportError:
    get_embedding_service = None
    EMBEDDING_AVAILABLE = False

# Multi-Agent System import
try:
    from services.multi_agent_service import get_multi_agent_service, MultiAgentService
    from models.agent import RequestType
    MULTI_AGENT_AVAILABLE = True
except ImportError:
    get_multi_agent_service = None
    MultiAgentService = None
    RequestType = None
    MULTI_AGENT_AVAILABLE = False

logger = logging.getLogger(__name__)

class RoadmapService:
    """Service for generating and managing career roadmaps"""
    
    def __init__(self):
        self.ai_service = None
        self.scraper = None
        self.embedding_service = None
        self.db_service = DatabaseService()
        self.multi_agent_service = None
    
    async def _init_services(self):
        """Initialize required services"""
        if not self.ai_service:
            self.ai_service = await get_ai_service()
        if not self.scraper:
            self.scraper = await get_roadmap_scraper()
        if not self.embedding_service and EMBEDDING_AVAILABLE:
            try:
                self.embedding_service = get_embedding_service()
            except Exception as e:
                logger.warning(f"Could not initialize embedding service: {str(e)}")
                self.embedding_service = None
        if not self.multi_agent_service and MULTI_AGENT_AVAILABLE:
            try:
                self.multi_agent_service = await get_multi_agent_service()
                logger.info("Multi-Agent Service initialized for roadmap service")
            except Exception as e:
                logger.warning(f"Could not initialize multi-agent service: {str(e)}")
                self.multi_agent_service = None
    
    def _create_roadmap_generation_prompt(
        self,
        current_role: str,
        target_role: str,
        user_background: str,
        timeline_preference: Optional[str] = None,
        focus_areas: List[str] = None,
        constraints: List[str] = None,
        learning_resources: List[LearningResource] = None
    ) -> str:
        """Create LangChain-style prompt for roadmap generation"""
        
        focus_areas = focus_areas or []
        learning_resources = learning_resources or []
        
        # Build resource context
        resource_context = ""
        if learning_resources:
            resource_context = "\n\nAvailable Learning Resources:\n"
            for resource in learning_resources[:10]:  # Limit to avoid token overflow
                resource_context += f"- {resource.title} ({resource.provider}): {resource.description}\n"
                if resource.skills_covered:
                    resource_context += f"  Skills: {', '.join(resource.skills_covered)}\n"
        
        # Build focus areas context
        focus_context = ""
        if focus_areas:
            focus_context = f"\n\nSpecial Focus Areas: {', '.join(focus_areas)}"
        
        # Timeline context
        timeline_context = ""
        if timeline_preference:
            timeline_context = f"\n\nPreferred Timeline: {timeline_preference}"
        
        # Build constraints context with emphasis
        constraints_context = ""
        if constraints:
            constraints_context = f"\n\nIMPORTANT CONSTRAINTS TO CONSIDER:\n"
            for constraint in constraints:
                constraints_context += f"- {constraint}\n"
            constraints_context += "These constraints MUST be reflected in the roadmap design, timeline, and milestone planning."

        prompt = f"""You are an expert career advisor creating a detailed, actionable career roadmap. 
Create a structured transition plan from {current_role} to {target_role}.

User Background:
{user_background}
{timeline_context}
{focus_context}
{constraints_context}
{resource_context}

Create a roadmap with the following structure:

ROADMAP TITLE: [Create a compelling title]

OVERVIEW: [2-3 sentence summary of the transition strategy, considering user constraints and focus areas]

PHASE 1: [Phase Title]
Duration: [X weeks - adjust based on user constraints and timeline preference]
Description: [What this phase accomplishes, considering user constraints]
Skills to Develop:
- [Skill 1]: [Current level] → [Target level] ([Priority 1-5])
- [Skill 2]: [Current level] → [Target level] ([Priority 1-5])
Learning Resources:
- [Resource 1]: [Description] ([Duration])
- [Resource 2]: [Description] ([Duration])
Milestones (3-5 MILESTONES RECOMMENDED):
- Week [X]: [Milestone title] - [Detailed description with specific steps, estimated time (e.g., 10-15 hours), and success criteria. Include specific links to courses, tutorials, or resources when applicable. Consider user constraints in time estimates.]
- Week [Y]: [Milestone title] - [Detailed description with specific steps, estimated time, and success criteria. Include specific links to courses, tutorials, or resources when applicable. Consider user constraints in time estimates.]
- Week [Z]: [Milestone title] - [Detailed description with specific steps, estimated time, and success criteria. Include specific links to courses, tutorials, or resources when applicable. Consider user constraints in time estimates.]
[Add 1-2 more milestones if the phase duration and complexity warrant it]
Prerequisites: [What's needed before starting, considering user constraints]
Outcomes: [What you'll achieve after completion]

PHASE 2: [Phase Title]
[Same structure as Phase 1 - 3-5 MILESTONES RECOMMENDED based on phase complexity]

[Continue for 3-6 phases total - EACH PHASE SHOULD HAVE 3-5 MILESTONES based on complexity and duration]

TOTAL TIMELINE: [X weeks/months - must align with user timeline preference and constraints]

KEY SUCCESS FACTORS:
- [Factor 1 - consider user constraints]
- [Factor 2 - consider user focus areas]
- [Factor 3 - consider user background]

POTENTIAL CHALLENGES:
- [Challenge 1]: [Mitigation strategy considering user constraints]
- [Challenge 2]: [Mitigation strategy considering user constraints]

CRITICAL REQUIREMENTS:
- Each phase should have 3-5 milestones based on complexity and duration
- Each milestone MUST include detailed steps, estimated time commitment, and specific resources/links
- Include real course names, tutorial links, and specific tools/technologies
- Make milestones actionable with clear deliverables
- Ensure each phase builds logically on the previous one
- Reference specific technologies, frameworks, and industry standards relevant to the target role
- ALWAYS consider and accommodate user constraints in timeline, resource recommendations, and time estimates
- Tailor the roadmap to user's focus areas and background experience
- Adjust milestone complexity and number based on phase duration and user constraints"""

        return prompt
    
    def _parse_roadmap_response(self, response: str, request: RoadmapRequest) -> Roadmap:
        """Parse AI response into structured Roadmap object"""
        
        # Extract title
        title_match = re.search(r'ROADMAP TITLE:\s*(.+)', response, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else f"{request.current_role} to {request.target_role} Roadmap"
        
        # Extract overview
        overview_match = re.search(r'OVERVIEW:\s*(.+?)(?=\n\n|\nPHASE)', response, re.IGNORECASE | re.DOTALL)
        description = overview_match.group(1).strip() if overview_match else ""
        
        # Extract phases
        phases = self._extract_phases(response)
        
        # Calculate total timeline
        total_weeks = sum(phase.duration_weeks for phase in phases)
        
        # Create roadmap
        roadmap = Roadmap(
            id=str(uuid.uuid4()),
            user_id="",  # Will be set by the API endpoint
            title=title,
            description=description,
            current_role=request.current_role,
            target_role=request.target_role,
            phases=phases,
            total_estimated_weeks=total_weeks,
            generated_with_model="AI Generated",
            user_context_used={
                "background": request.user_background,
                "timeline_preference": request.timeline_preference,
                "focus_areas": request.focus_areas,
                "constraints": request.constraints
            }
        )
        
        return roadmap
    
    def _extract_phases(self, response: str) -> List[RoadmapPhase]:
        """Extract phases from AI response"""
        phases = []
        
        # Find all phase sections
        phase_pattern = r'PHASE\s+(\d+):\s*(.+?)(?=PHASE\s+\d+:|TOTAL TIMELINE:|KEY SUCCESS FACTORS:|$)'
        phase_matches = re.findall(phase_pattern, response, re.IGNORECASE | re.DOTALL)
        
        for phase_num, phase_content in phase_matches:
            phase = self._parse_phase_content(int(phase_num), phase_content.strip())
            if phase:
                phases.append(phase)
        
        return phases
    
    def _parse_phase_content(self, phase_number: int, content: str) -> Optional[RoadmapPhase]:
        """Parse individual phase content"""
        try:
            # Extract title (first line after phase number)
            lines = content.split('\n')
            title = lines[0].strip() if lines else f"Phase {phase_number}"
            
            # Extract duration
            duration_match = re.search(r'Duration:\s*(\d+)\s*weeks?', content, re.IGNORECASE)
            duration_weeks = int(duration_match.group(1)) if duration_match else 4
            
            # Extract description
            desc_match = re.search(r'Description:\s*(.+?)(?=\n[A-Z]|\nSkills|\nLearning|\nMilestones)', content, re.IGNORECASE | re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Extract skills
            skills = self._extract_skills_from_content(content)
            
            # Extract learning resources
            learning_resources = self._extract_learning_resources_from_content(content)
            
            # Extract milestones
            milestones = self._extract_milestones_from_content(content)
            
            # Extract prerequisites and outcomes
            prerequisites = self._extract_list_items(content, r'Prerequisites:\s*(.+?)(?=\n[A-Z]|$)')
            outcomes = self._extract_list_items(content, r'Outcomes:\s*(.+?)(?=\n[A-Z]|$)')
            
            phase = RoadmapPhase(
                phase_number=phase_number,
                title=title,
                description=description,
                duration_weeks=duration_weeks,
                skills_to_develop=skills,
                learning_resources=learning_resources,
                milestones=milestones,
                prerequisites=prerequisites,
                outcomes=outcomes
            )
            
            return phase
            
        except Exception as e:
            logger.error(f"Error parsing phase {phase_number}: {str(e)}")
            return None
    
    def _extract_skills_from_content(self, content: str) -> List[Skill]:
        """Extract skills from phase content"""
        skills = []
        
        # Find skills section
        skills_match = re.search(r'Skills to Develop:\s*(.+?)(?=\nLearning Resources:|$)', content, re.IGNORECASE | re.DOTALL)
        if not skills_match:
            return skills
        
        skills_text = skills_match.group(1)
        
        # Parse individual skills
        skill_lines = [line.strip() for line in skills_text.split('\n') if line.strip().startswith('-')]
        
        for line in skill_lines:
            # Parse format: - Skill Name: beginner → intermediate (Priority 3)
            skill_match = re.search(r'-\s*([^:]+):\s*(\w+)\s*→\s*(\w+)\s*\(Priority\s*(\d+)\)', line, re.IGNORECASE)
            if skill_match:
                name = skill_match.group(1).strip()
                current_level = self._parse_skill_level(skill_match.group(2))
                target_level = self._parse_skill_level(skill_match.group(3))
                priority = int(skill_match.group(4))
                
                skill = Skill(
                    name=name,
                    current_level=current_level,
                    target_level=target_level,
                    priority=priority
                )
                skills.append(skill)
            else:
                # Fallback: just extract skill name
                skill_name = line.replace('-', '').strip()
                if skill_name:
                    skill = Skill(name=skill_name)
                    skills.append(skill)
        
        return skills
    
    def _extract_learning_resources_from_content(self, content: str) -> List[LearningResource]:
        """Extract learning resources from phase content"""
        resources = []
        
        # Find learning resources section
        resources_match = re.search(r'Learning Resources:\s*(.+?)(?=\nMilestones:|$)', content, re.IGNORECASE | re.DOTALL)
        if not resources_match:
            return resources
        
        resources_text = resources_match.group(1)
        
        # Parse individual resources
        resource_lines = [line.strip() for line in resources_text.split('\n') if line.strip().startswith('-')]
        
        for line in resource_lines:
            # Parse format: - Resource Name: Description (Duration)
            resource_match = re.search(r'-\s*([^:]+):\s*([^(]+)\s*\(([^)]+)\)', line)
            if resource_match:
                title = resource_match.group(1).strip()
                description = resource_match.group(2).strip()
                duration = resource_match.group(3).strip()
                
                resource = LearningResource(
                    title=title,
                    description=description,
                    duration=duration,
                    resource_type=ResourceType.COURSE,
                    provider=""
                )
                resources.append(resource)
        
        return resources
    
    def _extract_milestones_from_content(self, content: str) -> List[Milestone]:
        """Extract milestones from phase content with detailed descriptions"""
        milestones = []
        
        # Find milestones section
        milestones_match = re.search(r'Milestones.*?:\s*(.+?)(?=\nPrerequisites:|$)', content, re.IGNORECASE | re.DOTALL)
        if not milestones_match:
            return milestones
        
        milestones_text = milestones_match.group(1)
        
        # Split by milestone markers (- Week X:)
        milestone_sections = re.split(r'(?=- Week \d+:)', milestones_text)
        
        for section in milestone_sections:
            section = section.strip()
            if not section or not section.startswith('- Week'):
                continue
                
            # Parse format: - Week X: Milestone title - Detailed description...
            milestone_match = re.search(r'- Week\s*(\d+):\s*([^-]+)\s*-\s*(.+)', section, re.IGNORECASE | re.DOTALL)
            if milestone_match:
                week = int(milestone_match.group(1))
                title = milestone_match.group(2).strip()
                full_description = milestone_match.group(3).strip()
                
                # Extract links from description
                links = re.findall(r'https?://[^\s\)]+', full_description)
                
                # Extract estimated time if mentioned
                time_match = re.search(r'(\d+[-–]\d+|\d+)\s*hours?', full_description, re.IGNORECASE)
                estimated_hours = time_match.group(1) if time_match else None
                
                # Split description into main description and success criteria
                # Look for patterns like "Success criteria:", "You will:", "Deliverables:", etc.
                criteria_patterns = [
                    r'Success criteria?:\s*(.+?)(?=\n|$)',
                    r'You will:\s*(.+?)(?=\n|$)',
                    r'Deliverables?:\s*(.+?)(?=\n|$)',
                    r'Complete when:\s*(.+?)(?=\n|$)'
                ]
                
                success_criteria = []
                description = full_description
                
                for pattern in criteria_patterns:
                    criteria_match = re.search(pattern, full_description, re.IGNORECASE | re.DOTALL)
                    if criteria_match:
                        criteria_text = criteria_match.group(1).strip()
                        # Split by common delimiters
                        criteria_items = [item.strip() for item in re.split(r'[,;]|\sand\s', criteria_text) if item.strip()]
                        success_criteria.extend(criteria_items)
                        # Remove criteria from description
                        description = re.sub(pattern, '', description, flags=re.IGNORECASE | re.DOTALL).strip()
                        break
                
                # If no explicit success criteria found, use the full description as one criterion
                if not success_criteria:
                    success_criteria = [full_description]
                
                # Create deliverables from description if mentioned
                deliverables = []
                deliverable_patterns = [
                    r'build\s+([^,.]+)',
                    r'create\s+([^,.]+)',
                    r'develop\s+([^,.]+)',
                    r'implement\s+([^,.]+)',
                    r'complete\s+([^,.]+)'
                ]
                
                for pattern in deliverable_patterns:
                    matches = re.findall(pattern, description, re.IGNORECASE)
                    deliverables.extend([match.strip() for match in matches])
                
                milestone = Milestone(
                    title=title,
                    description=description,
                    estimated_completion_weeks=week,
                    success_criteria=success_criteria[:3],  # Limit to 3 criteria
                    deliverables=deliverables[:2] if deliverables else []  # Limit to 2 deliverables
                )
                milestones.append(milestone)
        
        return milestones
    
    def _extract_list_items(self, content: str, pattern: str) -> List[str]:
        """Extract list items using regex pattern"""
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if not match:
            return []
        
        text = match.group(1)
        items = []
        
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                items.append(line.replace('-', '').strip())
            elif line and not line.startswith('['):
                items.append(line)
        
        return [item for item in items if item]
    
    def _parse_skill_level(self, level_str: str) -> SkillLevel:
        """Parse skill level string to enum"""
        level_lower = level_str.lower().strip()
        
        if level_lower in ['beginner', 'basic', 'novice']:
            return SkillLevel.BEGINNER
        elif level_lower in ['intermediate', 'medium', 'mid']:
            return SkillLevel.INTERMEDIATE
        elif level_lower in ['advanced', 'high', 'senior']:
            return SkillLevel.ADVANCED
        elif level_lower in ['expert', 'master', 'guru']:
            return SkillLevel.EXPERT
        else:
            return SkillLevel.INTERMEDIATE
    
    async def _generate_strengths_weaknesses_analysis(
        self,
        request: RoadmapRequest,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate analysis of user's current strengths and weaknesses for the target role"""
        
        try:
            # Build context from user background and resume
            context_text = request.user_background or ""
            if user_context:
                resume_context = user_context.get('resume_summary', '')
                if resume_context:
                    context_text += f"\n\nResume Summary: {resume_context}"
            
            # Build additional context for analysis
            focus_areas_text = ""
            if request.focus_areas:
                focus_areas_text = f"\nFocus Areas: {', '.join(request.focus_areas)}"
            
            constraints_text = ""
            if request.constraints:
                constraints_text = f"\nConstraints: {', '.join(request.constraints)}"
            
            timeline_text = ""
            if request.timeline_preference:
                timeline_text = f"\nTimeline Preference: {request.timeline_preference}"

            analysis_prompt = f"""Analyze the user's current strengths and weaknesses for transitioning from {request.current_role} to {request.target_role}.

User Background:
{context_text}

Current Role: {request.current_role}
Target Role: {request.target_role}{timeline_text}{focus_areas_text}{constraints_text}

Provide a concise analysis in the following format. IMPORTANT: Each section should contain UNIQUE items - do not repeat the same skills, strengths, or challenges across different sections.

ROADMAP RATIONALE:
[Provide a 1-2 paragraph explanation of WHY this specific roadmap was created based on their background, focus areas, constraints, and timeline preference. Be specific about key technologies or experiences that influenced the roadmap design. Explain how the roadmap addresses their constraints and emphasizes their focus areas. DO NOT include bullet points here - only narrative text.]

CURRENT STRENGTHS:
- [Strength 1]: [Brief explanation of existing skills/experience that will help in the transition]
- [Strength 2]: [Brief explanation of existing skills/experience that will help in the transition]
- [Strength 3]: [Brief explanation of existing skills/experience that will help in the transition]

AREAS FOR IMPROVEMENT:
- [Gap 1]: [Specific skill or knowledge area that needs development for the target role]
- [Gap 2]: [Specific skill or knowledge area that needs development for the target role]
- [Gap 3]: [Specific skill or knowledge area that needs development for the target role]

KEY TRANSFERABLE SKILLS:
- [Skill 1]: [Existing skill from current role that applies to target role in a different context]
- [Skill 2]: [Existing skill from current role that applies to target role in a different context]

BIGGEST CHALLENGES:
- [Challenge 1]: [Major obstacle or difficulty in the transition with brief mitigation approach]
- [Challenge 2]: [Major obstacle or difficulty in the transition with brief mitigation approach]

COMPETITIVE ADVANTAGES:
- [Advantage 1]: [Unique combination of skills or experience that sets you apart]
- [Advantage 2]: [Unique combination of skills or experience that sets you apart]

CRITICAL REQUIREMENTS:
- Each section must contain DIFFERENT items - no duplicates across sections
- Current Strengths = what you already have and can leverage
- Areas for Improvement = what you need to learn/develop
- Transferable Skills = existing skills that apply differently in the new role
- Challenges = obstacles you'll face during transition
- Competitive Advantages = what makes you unique for this transition
- Keep explanations concise and actionable"""

            response = await self.ai_service.generate_text(
                prompt=analysis_prompt,
                model_type=ModelType.GEMINI_FLASH,
                max_tokens=1200,
                temperature=0.7
            )
            
            # Parse the analysis into structured data
            analysis = self._parse_strengths_weaknesses_response(response)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating strengths/weaknesses analysis: {str(e)}")
            return {
                "roadmap_rationale": "",
                "strengths": [],
                "weaknesses": [],
                "transferable_skills": [],
                "challenges": [],
                "advantages": []
            }
    
    def _parse_strengths_weaknesses_response(self, response: str) -> Dict[str, Any]:
        """Parse the strengths/weaknesses analysis response"""
        
        analysis = {
            "roadmap_rationale": "",
            "strengths": [],
            "weaknesses": [],
            "transferable_skills": [],
            "challenges": [],
            "advantages": []
        }
        
        # Extract roadmap rationale first - only the first paragraph, not the bullet points
        rationale_match = re.search(r'ROADMAP RATIONALE:\s*(.+?)(?=\n\n|\nCURRENT STRENGTHS:|$)', response, re.IGNORECASE | re.DOTALL)
        if rationale_match:
            rationale_text = rationale_match.group(1).strip()
            # Remove any bullet points from the rationale - keep only the first paragraph(s)
            lines = rationale_text.split('\n')
            rationale_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    break  # Stop at first bullet point
                if line:
                    rationale_lines.append(line)
            analysis["roadmap_rationale"] = '\n'.join(rationale_lines).strip()
        
        # Split the response into sections more reliably
        sections_text = {}
        
        # Find all section headers and their positions
        section_headers = [
            ('CURRENT STRENGTHS:', 'strengths'),
            ('AREAS FOR IMPROVEMENT:', 'weaknesses'),
            ('KEY TRANSFERABLE SKILLS:', 'transferable_skills'),
            ('BIGGEST CHALLENGES:', 'challenges'),
            ('COMPETITIVE ADVANTAGES:', 'advantages')
        ]
        
        # Find positions of each section header
        section_positions = []
        for header, key in section_headers:
            match = re.search(rf'{re.escape(header)}\s*', response, re.IGNORECASE)
            if match:
                section_positions.append((match.end(), key, header))
        
        # Sort by position
        section_positions.sort()
        
        # Extract content for each section
        for i, (start_pos, key, header) in enumerate(section_positions):
            # Find the end position (start of next section or end of text)
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][0]
                # Find the actual start of the next section header
                next_header = section_positions[i + 1][2]
                next_match = re.search(rf'{re.escape(next_header)}', response[start_pos:], re.IGNORECASE)
                if next_match:
                    end_pos = start_pos + next_match.start()
            else:
                end_pos = len(response)
            
            section_content = response[start_pos:end_pos].strip()
            sections_text[key] = section_content
        
        # Parse each section's content
        for key, section_content in sections_text.items():
            items = []
            
            # Split into lines and process each bullet point
            lines = section_content.split('\n')
            current_item = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this is a new bullet point
                if line.startswith('-') or line.startswith('•'):
                    # Save previous item if exists
                    if current_item:
                        items.append(current_item)
                    
                    # Parse new item: - Title: Description
                    bullet_content = line[1:].strip()  # Remove bullet
                    if ':' in bullet_content:
                        title_part, desc_part = bullet_content.split(':', 1)
                        current_item = {
                            "title": title_part.strip(),
                            "description": desc_part.strip()
                        }
                    else:
                        current_item = {
                            "title": bullet_content,
                            "description": ""
                        }
                elif current_item and line:
                    # This is a continuation of the description
                    if current_item["description"]:
                        current_item["description"] += " " + line
                    else:
                        current_item["description"] = line
            
            # Don't forget the last item
            if current_item:
                items.append(current_item)
            
            analysis[key] = items
        
        return analysis
    
    def _should_use_multi_agent_for_roadmap(self, request: RoadmapRequest) -> bool:
        """Determine if roadmap generation should use multi-agent system"""
        if not MULTI_AGENT_AVAILABLE or not self.multi_agent_service:
            return False
        
        # Use multi-agent system for complex requests
        complexity_indicators = [
            len(request.focus_areas or []) > 2,  # Multiple focus areas
            len(request.constraints or []) > 1,  # Multiple constraints
            request.timeline_preference and ("month" in request.timeline_preference.lower()),  # Specific timeline
            len(request.user_background or "") > 200,  # Detailed background
            request.current_role.lower() != request.target_role.lower()  # Career transition
        ]
        
        # Use multi-agent system if 2 or more complexity indicators are present
        return sum(1 for indicator in complexity_indicators if indicator) >= 2

    async def generate_roadmap(
        self,
        request: RoadmapRequest,
        user_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> RoadmapGenerationResult:
        """Generate a career roadmap based on request"""
        
        start_time = datetime.utcnow()
        
        try:
            await self._init_services()
            
            # Check if we should use multi-agent system generation
            if self._should_use_multi_agent_for_roadmap(request):
                try:
                    return await self._generate_roadmap_with_multi_agent_system(request, user_id, user_context, start_time)
                except Exception as multi_agent_error:
                    logger.warning(f"Multi-agent roadmap generation failed, falling back to direct generation: {multi_agent_error}")
                    # Fall back to direct generation
            
            # Direct roadmap generation (existing logic)
            return await self._generate_roadmap_direct(request, user_id, user_context, start_time)
            
        except Exception as e:
            logger.error(f"Error generating roadmap: {str(e)}")
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            return RoadmapGenerationResult(
                success=False,
                error_message=str(e),
                generation_time_seconds=generation_time
            )
    
    async def _generate_roadmap_with_multi_agent_system(
        self,
        request: RoadmapRequest,
        user_id: str,
        user_context: Optional[Dict[str, Any]],
        start_time: datetime
    ) -> RoadmapGenerationResult:
        """Generate roadmap using optimized Multi-Agent System with LangGraph workflows"""
        
        # Prepare request content for multi-agent system
        request_content = {
            "current_role": request.current_role,
            "target_role": request.target_role,
            "user_background": request.user_background,
            "timeline_preference": request.timeline_preference,
            "focus_areas": request.focus_areas or [],
            "constraints": request.constraints or [],
            "user_context": user_context or {},
            "user_id": user_id
        }
        
        # Use LangGraph workflow for comprehensive roadmap generation
        try:
            result = await self.multi_agent_service.execute_career_transition_workflow(
                user_id=user_id,
                current_role=request.current_role,
                target_role=request.target_role,
                timeline=request.timeline_preference or "12 months",
                constraints={
                    "focus_areas": request.focus_areas or [],
                    "constraints": request.constraints or [],
                    "user_background": request.user_background
                }
            )
        except Exception as workflow_error:
            logger.warning(f"LangGraph workflow failed, falling back to standard multi-agent: {workflow_error}")
            # Fallback to standard multi-agent processing
            result = await self.multi_agent_service.process_request(
                user_id=user_id,
                request_type=RequestType.ROADMAP_GENERATION,
                content=request_content,
                context=user_context or {}
            )
        
        if result["success"]:
            # Extract roadmap from multi-agent result
            final_response = result.get("final_response", {})
            
            # Convert multi-agent response to roadmap with enhanced processing
            roadmap = await self._convert_multi_agent_response_to_roadmap(
                final_response, request, user_id
            )
            
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract comprehensive analysis from multi-agent response
            # For now, use empty analysis - multi-agent system should provide its own analysis
            strengths_analysis = {
                "roadmap_rationale": "This roadmap was generated using our advanced multi-agent system, which analyzed your background, constraints, and focus areas to create a personalized career transition plan.",
                "strengths": [],
                "weaknesses": [],
                "transferable_skills": [],
                "challenges": [],
                "advantages": []
            }
            
            logger.info(f"Generated roadmap using optimized multi-agent system for {user_id}: {request.current_role} → {request.target_role} in {generation_time:.2f}s")
            
            return RoadmapGenerationResult(
                success=True,
                roadmap=roadmap,
                generation_time_seconds=generation_time,
                model_used="Multi-Agent LangGraph Workflow",
                strengths_analysis=strengths_analysis
            )
        else:
            raise Exception(f"Multi-agent processing failed: {result.get('error', 'Unknown error')}")
    
    async def _generate_roadmap_direct(
        self,
        request: RoadmapRequest,
        user_id: str,
        user_context: Optional[Dict[str, Any]],
        start_time: datetime
    ) -> RoadmapGenerationResult:
        """Generate roadmap using direct AI service (existing logic)"""
        
        # Generate strengths and weaknesses analysis first
        strengths_analysis = await self._generate_strengths_weaknesses_analysis(
            request, user_context
        )
        
        # Get learning resources from scraper
        learning_resources = await self.scraper.get_resources_for_transition(
            request.current_role,
            request.target_role,
            max_resources=15
        )
        
        # Enhance user background with context if available
        enhanced_background = request.user_background or ""
        if user_context:
            resume_context = user_context.get('resume_summary', '')
            if resume_context:
                enhanced_background += f"\n\nResume Summary: {resume_context}"
        
        # Create generation prompt
        prompt = self._create_roadmap_generation_prompt(
            current_role=request.current_role,
            target_role=request.target_role,
            user_background=enhanced_background,
            timeline_preference=request.timeline_preference,
            focus_areas=request.focus_areas,
            constraints=request.constraints,
            learning_resources=learning_resources
        )
        
        # Generate roadmap using AI service
        response = await self.ai_service.generate_text(
            prompt=prompt,
            model_type=ModelType.GEMINI_FLASH,  # Use fast model for roadmap generation
            max_tokens=2000,
            temperature=0.7
        )
        
        # Parse response into structured roadmap
        roadmap = self._parse_roadmap_response(response, request)
        roadmap.user_id = user_id
        roadmap.generation_prompt = prompt[:500] + "..." if len(prompt) > 500 else prompt
        
        # Ensure each phase has at least 3 milestones
        await self._ensure_minimum_milestones(roadmap)
        
        # Enhance with scraped learning resources
        self._enhance_roadmap_with_resources(roadmap, learning_resources)
        
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"Generated roadmap for {user_id}: {request.current_role} → {request.target_role}")
        
        return RoadmapGenerationResult(
            success=True,
            roadmap=roadmap,
            generation_time_seconds=generation_time,
            model_used="Gemini Flash",
            strengths_analysis=strengths_analysis
        )
    
    async def _convert_multi_agent_response_to_roadmap(
        self,
        multi_agent_response: Dict[str, Any],
        request: RoadmapRequest,
        user_id: str
    ) -> Roadmap:
        """Convert multi-agent response to structured Roadmap object"""
        
        # If the response is a synthesized response, try to parse it as JSON
        if isinstance(multi_agent_response, dict) and "synthesized_response" in multi_agent_response:
            try:
                # Try to parse the synthesized response as a roadmap
                synthesized = multi_agent_response["synthesized_response"]
                if isinstance(synthesized, str):
                    # Try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', synthesized, re.DOTALL)
                    if json_match:
                        parsed_roadmap = json.loads(json_match.group())
                        return self._create_roadmap_from_parsed_data(parsed_roadmap, request, user_id)
                elif isinstance(synthesized, dict):
                    return self._create_roadmap_from_parsed_data(synthesized, request, user_id)
            except Exception as e:
                logger.warning(f"Failed to parse synthesized response as roadmap: {e}")
        
        # Fallback: create a basic roadmap structure
        return self._create_fallback_roadmap(multi_agent_response, request, user_id)
    
    def _create_roadmap_from_parsed_data(
        self,
        parsed_data: Dict[str, Any],
        request: RoadmapRequest,
        user_id: str
    ) -> Roadmap:
        """Create roadmap from parsed JSON data"""
        
        # Create roadmap title
        title = parsed_data.get("title", f"{request.current_role} to {request.target_role} Roadmap")
        
        # Create description
        description = parsed_data.get("description", "Career transition roadmap generated by multi-agent system")
        
        # Create phases from parsed data
        phases = []
        phases_data = parsed_data.get("phases", [])
        
        for i, phase_data in enumerate(phases_data):
            phase = RoadmapPhase(
                name=phase_data.get("name", f"Phase {i+1}"),
                description=phase_data.get("description", ""),
                duration_weeks=phase_data.get("duration_weeks", 4),
                skills=[],
                milestones=[],
                learning_resources=[]
            )
            
            # Add skills
            for skill_data in phase_data.get("skills", []):
                if isinstance(skill_data, str):
                    skill = Skill(name=skill_data, level=SkillLevel.INTERMEDIATE)
                else:
                    skill = Skill(
                        name=skill_data.get("name", ""),
                        level=SkillLevel(skill_data.get("level", "intermediate")),
                        description=skill_data.get("description", "")
                    )
                phase.skills.append(skill)
            
            # Add milestones
            for milestone_data in phase_data.get("milestones", []):
                if isinstance(milestone_data, str):
                    milestone = Milestone(
                        title=milestone_data,
                        description="",
                        week=1
                    )
                else:
                    milestone = Milestone(
                        title=milestone_data.get("title", ""),
                        description=milestone_data.get("description", ""),
                        week=milestone_data.get("week", 1)
                    )
                phase.milestones.append(milestone)
            
            phases.append(phase)
        
        # Create roadmap
        roadmap = Roadmap(
            user_id=user_id,
            title=title,
            description=description,
            current_role=request.current_role,
            target_role=request.target_role,
            phases=phases,
            total_duration_weeks=sum(phase.duration_weeks for phase in phases),
            created_at=datetime.utcnow()
        )
        
        return roadmap
    
    def _create_fallback_roadmap(
        self,
        multi_agent_response: Dict[str, Any],
        request: RoadmapRequest,
        user_id: str
    ) -> Roadmap:
        """Create a fallback roadmap when parsing fails"""
        
        # Create a basic 3-phase roadmap
        phases = [
            RoadmapPhase(
                name="Foundation Phase",
                description="Build foundational skills and knowledge",
                duration_weeks=4,
                skills=[Skill(name="Core Skills", level=SkillLevel.BEGINNER)],
                milestones=[
                    Milestone(title="Complete initial assessment", description="", week=1),
                    Milestone(title="Start learning core concepts", description="", week=2),
                    Milestone(title="Practice fundamental skills", description="", week=4)
                ],
                learning_resources=[]
            ),
            RoadmapPhase(
                name="Development Phase", 
                description="Develop intermediate skills and experience",
                duration_weeks=8,
                skills=[Skill(name="Intermediate Skills", level=SkillLevel.INTERMEDIATE)],
                milestones=[
                    Milestone(title="Complete intermediate projects", description="", week=2),
                    Milestone(title="Build portfolio", description="", week=4),
                    Milestone(title="Gain practical experience", description="", week=8)
                ],
                learning_resources=[]
            ),
            RoadmapPhase(
                name="Mastery Phase",
                description="Achieve advanced proficiency and transition readiness",
                duration_weeks=4,
                skills=[Skill(name="Advanced Skills", level=SkillLevel.ADVANCED)],
                milestones=[
                    Milestone(title="Complete advanced projects", description="", week=2),
                    Milestone(title="Prepare for transition", description="", week=3),
                    Milestone(title="Ready for new role", description="", week=4)
                ],
                learning_resources=[]
            )
        ]
        
        roadmap = Roadmap(
            user_id=user_id,
            title=f"{request.current_role} to {request.target_role} Roadmap",
            description="Career transition roadmap generated by multi-agent system",
            current_role=request.current_role,
            target_role=request.target_role,
            phases=phases,
            total_duration_weeks=16,
            created_at=datetime.utcnow()
        )
        
        return roadmap

    async def _convert_workflow_response_to_roadmap(
        self,
        workflow_response: Dict[str, Any],
        request: RoadmapRequest,
        user_id: str
    ) -> Roadmap:
        """Convert workflow response to structured Roadmap object (legacy method)"""
        
        # This method is kept for backward compatibility
        # but should be replaced with multi-agent system
        return await self._convert_multi_agent_response_to_roadmap(workflow_response, request, user_id)
        phases = await self._create_phases_from_workflow_outputs(
            career_strategy, skills_analysis, learning_resources, request
        )
        
        # Calculate total timeline
        total_weeks = sum(phase.duration_weeks for phase in phases)
        
        # Create roadmap
        roadmap = Roadmap(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            description=description,
            current_role=request.current_role,
            target_role=request.target_role,
            phases=phases,
            total_estimated_weeks=total_weeks,
            generated_with_model="Multi-Agent Workflow",
            user_context_used={
                "background": request.user_background,
                "timeline_preference": request.timeline_preference,
                "focus_areas": request.focus_areas,
                "constraints": request.constraints,
                "workflow_used": True
            }
        )
        
        return roadmap
    
    async def _create_phases_from_workflow_outputs(
        self,
        career_strategy: Dict[str, Any],
        skills_analysis: Dict[str, Any],
        learning_resources: Dict[str, Any],
        request: RoadmapRequest
    ) -> List[RoadmapPhase]:
        """Create roadmap phases from multi-agent workflow outputs"""
        
        phases = []
        
        # Get recommended phases from career strategy
        strategy_phases = career_strategy.get("recommended_phases", [])
        skill_gaps = skills_analysis.get("skill_gaps", [])
        recommended_resources = learning_resources.get("recommended_resources", [])
        
        # If we have structured phases from workflow, use them
        if strategy_phases:
            for i, phase_data in enumerate(strategy_phases[:6]):  # Limit to 6 phases
                phase = await self._create_phase_from_workflow_data(
                    phase_data, i + 1, skill_gaps, recommended_resources
                )
                phases.append(phase)
        else:
            # Create default phases based on skill gaps and resources
            phases = await self._create_default_phases_from_workflow(
                skill_gaps, recommended_resources, request
            )
        
        return phases
    
    async def _create_phase_from_workflow_data(
        self,
        phase_data: Dict[str, Any],
        phase_number: int,
        skill_gaps: List[Dict[str, Any]],
        resources: List[Dict[str, Any]]
    ) -> RoadmapPhase:
        """Create a roadmap phase from workflow phase data"""
        
        # Extract phase information
        title = phase_data.get("title", f"Phase {phase_number}")
        description = phase_data.get("description", "")
        duration_weeks = phase_data.get("duration_weeks", 4)
        
        # Create skills from phase data and skill gaps
        skills = []
        phase_skills = phase_data.get("skills", [])
        for skill_name in phase_skills:
            # Find matching skill gap for more details
            skill_gap = next((gap for gap in skill_gaps if gap.get("skill", "").lower() == skill_name.lower()), {})
            
            skill = Skill(
                name=skill_name,
                description=skill_gap.get("description", ""),
                current_level=self._parse_skill_level(skill_gap.get("current_level", "beginner")),
                target_level=self._parse_skill_level(skill_gap.get("target_level", "intermediate")),
                priority=skill_gap.get("priority", 3)
            )
            skills.append(skill)
        
        # Create learning resources for this phase
        phase_resources = []
        phase_resource_names = phase_data.get("resources", [])
        for resource_name in phase_resource_names:
            # Find matching resource
            resource_data = next((res for res in resources if res.get("title", "").lower() == resource_name.lower()), {})
            
            if resource_data:
                resource = LearningResource(
                    title=resource_data.get("title", resource_name),
                    description=resource_data.get("description", ""),
                    url=resource_data.get("url", ""),
                    resource_type=ResourceType.COURSE,  # Default type
                    provider=resource_data.get("provider", ""),
                    duration=resource_data.get("duration", ""),
                    skills_covered=resource_data.get("skills_covered", [])
                )
                phase_resources.append(resource)
        
        # Create milestones
        milestones = []
        phase_milestones = phase_data.get("milestones", [])
        for i, milestone_data in enumerate(phase_milestones):
            if isinstance(milestone_data, str):
                milestone = Milestone(
                    title=milestone_data,
                    description=f"Complete {milestone_data}",
                    estimated_completion_weeks=i + 1
                )
            else:
                milestone = Milestone(
                    title=milestone_data.get("title", f"Milestone {i + 1}"),
                    description=milestone_data.get("description", ""),
                    estimated_completion_weeks=milestone_data.get("week", i + 1),
                    success_criteria=milestone_data.get("success_criteria", []),
                    deliverables=milestone_data.get("deliverables", [])
                )
            milestones.append(milestone)
        
        # Ensure minimum 3 milestones
        while len(milestones) < 3:
            milestones.append(Milestone(
                title=f"Milestone {len(milestones) + 1}",
                description=f"Complete phase {phase_number} objectives",
                estimated_completion_weeks=len(milestones) + 1
            ))
        
        return RoadmapPhase(
            phase_number=phase_number,
            title=title,
            description=description,
            duration_weeks=duration_weeks,
            skills_to_develop=skills,
            learning_resources=phase_resources,
            milestones=milestones,
            prerequisites=phase_data.get("prerequisites", []),
            outcomes=phase_data.get("outcomes", [])
        )
    
    async def _create_default_phases_from_workflow(
        self,
        skill_gaps: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        request: RoadmapRequest
    ) -> List[RoadmapPhase]:
        """Create default phases when workflow doesn't provide structured phases"""
        
        phases = []
        
        # Group skills by priority/category
        high_priority_skills = [gap for gap in skill_gaps if gap.get("priority", 3) >= 4]
        medium_priority_skills = [gap for gap in skill_gaps if gap.get("priority", 3) == 3]
        low_priority_skills = [gap for gap in skill_gaps if gap.get("priority", 3) <= 2]
        
        # Create phases based on skill priorities
        if high_priority_skills:
            phase1 = await self._create_skills_phase(
                "Foundation Skills", high_priority_skills, resources, 1, 4
            )
            phases.append(phase1)
        
        if medium_priority_skills:
            phase2 = await self._create_skills_phase(
                "Core Development", medium_priority_skills, resources, 2, 6
            )
            phases.append(phase2)
        
        if low_priority_skills:
            phase3 = await self._create_skills_phase(
                "Advanced Skills", low_priority_skills, resources, 3, 4
            )
            phases.append(phase3)
        
        # Add a final integration phase
        integration_phase = RoadmapPhase(
            phase_number=len(phases) + 1,
            title="Integration & Application",
            description=f"Apply learned skills in real-world projects and prepare for {request.target_role} role",
            duration_weeks=4,
            skills_to_develop=[],
            learning_resources=[],
            milestones=[
                Milestone(title="Complete capstone project", estimated_completion_weeks=2),
                Milestone(title="Build portfolio", estimated_completion_weeks=3),
                Milestone(title="Practice interviews", estimated_completion_weeks=4)
            ],
            prerequisites=["Complete previous phases"],
            outcomes=[f"Ready to apply for {request.target_role} positions"]
        )
        phases.append(integration_phase)
        
        return phases
    
    async def _create_skills_phase(
        self,
        title: str,
        skill_gaps: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        phase_number: int,
        duration_weeks: int
    ) -> RoadmapPhase:
        """Create a phase focused on specific skills"""
        
        # Create skills
        skills = []
        for gap in skill_gaps[:5]:  # Limit to 5 skills per phase
            skill = Skill(
                name=gap.get("skill", "Unknown Skill"),
                description=gap.get("description", ""),
                current_level=self._parse_skill_level(gap.get("current_level", "beginner")),
                target_level=self._parse_skill_level(gap.get("target_level", "intermediate")),
                priority=gap.get("priority", 3)
            )
            skills.append(skill)
        
        # Find relevant resources
        phase_resources = []
        for resource_data in resources[:3]:  # Limit to 3 resources per phase
            resource = LearningResource(
                title=resource_data.get("title", "Learning Resource"),
                description=resource_data.get("description", ""),
                url=resource_data.get("url", ""),
                resource_type=ResourceType.COURSE,
                provider=resource_data.get("provider", ""),
                duration=resource_data.get("duration", ""),
                skills_covered=resource_data.get("skills_covered", [])
            )
            phase_resources.append(resource)
        
        # Create milestones
        milestones = [
            Milestone(
                title=f"Master {skills[0].name if skills else 'core concepts'}",
                description=f"Achieve proficiency in key {title.lower()} concepts",
                estimated_completion_weeks=2
            ),
            Milestone(
                title="Complete practical exercises",
                description="Apply learned concepts through hands-on practice",
                estimated_completion_weeks=duration_weeks - 1
            ),
            Milestone(
                title="Phase assessment",
                description="Demonstrate mastery of phase objectives",
                estimated_completion_weeks=duration_weeks
            )
        ]
        
        return RoadmapPhase(
            phase_number=phase_number,
            title=title,
            description=f"Focus on developing {title.lower()} essential for career transition",
            duration_weeks=duration_weeks,
            skills_to_develop=skills,
            learning_resources=phase_resources,
            milestones=milestones,
            prerequisites=[],
            outcomes=[f"Proficiency in {title.lower()}"]
        )
    
    def _calculate_target_milestone_count(self, phase: RoadmapPhase) -> int:
        """Calculate the target number of milestones for a phase based on duration and complexity"""
        
        # Base milestone count on phase duration
        if phase.duration_weeks <= 2:
            base_count = 3  # Short phases get minimum 3 milestones
        elif phase.duration_weeks <= 4:
            base_count = 4  # Medium phases get 4 milestones
        elif phase.duration_weeks <= 8:
            base_count = 5  # Longer phases get 5 milestones
        else:
            base_count = 6  # Very long phases get 6+ milestones
        
        # Adjust based on complexity (number of skills to develop)
        skill_count = len(phase.skills_to_develop)
        if skill_count > 5:
            base_count += 1  # Add extra milestone for complex phases
        elif skill_count < 2:
            base_count = max(3, base_count - 1)  # Reduce for simple phases, but keep minimum of 3
        
        # Ensure we stay within reasonable bounds (3-7 milestones)
        return max(3, min(7, base_count))

    async def _ensure_minimum_milestones(self, roadmap: Roadmap):
        """Ensure each phase has appropriate number of milestones (3-7 based on complexity), generate additional ones if needed"""
        
        for phase in roadmap.phases:
            # Determine target milestone count based on phase duration and complexity
            target_milestone_count = self._calculate_target_milestone_count(phase)
            
            if len(phase.milestones) < target_milestone_count:
                # Generate additional milestones for this phase
                missing_count = target_milestone_count - len(phase.milestones)
                
                try:
                    additional_milestones_prompt = f"""Generate {missing_count} additional detailed milestones for this phase:

Phase: {phase.title}
Description: {phase.description}
Duration: {phase.duration_weeks} weeks
Skills to develop: {', '.join([skill.name for skill in phase.skills_to_develop])}

Existing milestones:
{chr(10).join([f"- Week {m.estimated_completion_weeks}: {m.title}" for m in phase.milestones])}

Generate {missing_count} new milestones that:
1. Fill gaps in the timeline (weeks 1-{phase.duration_weeks})
2. Are specific and actionable
3. Include detailed descriptions with steps, estimated time (e.g., 8-12 hours), and resources
4. Have clear success criteria and deliverables
5. Build logically on existing milestones

Format each milestone as:
- Week [X]: [Milestone title] - [Detailed description with specific steps, estimated time commitment, success criteria, and relevant links/resources when applicable]

Only provide the milestone entries, no additional text."""

                    response = await self.ai_service.generate_text(
                        prompt=additional_milestones_prompt,
                        model_type=ModelType.GEMINI_FLASH,
                        max_tokens=800,
                        temperature=0.7
                    )
                    
                    # Parse the additional milestones
                    additional_milestones = self._extract_milestones_from_content(f"Milestones:\n{response}")
                    
                    # Add them to the phase
                    phase.milestones.extend(additional_milestones)
                    
                    # Sort milestones by week
                    phase.milestones.sort(key=lambda m: m.estimated_completion_weeks)
                    
                    logger.info(f"Added {len(additional_milestones)} milestones to phase {phase.phase_number}")
                    
                except Exception as e:
                    logger.error(f"Error generating additional milestones for phase {phase.phase_number}: {str(e)}")
                    
                    # Fallback: create basic milestones
                    for i in range(missing_count):
                        week = min(phase.duration_weeks, len(phase.milestones) + i + 1)
                        fallback_milestone = Milestone(
                            title=f"Complete {phase.title} Milestone {len(phase.milestones) + i + 1}",
                            description=f"Work on developing skills and completing objectives for {phase.title}. Spend 8-10 hours this week focusing on practical application and skill building.",
                            estimated_completion_weeks=week,
                            success_criteria=[f"Complete assigned tasks for week {week}", "Demonstrate progress in key skills"],
                            deliverables=[f"Week {week} progress report"]
                        )
                        phase.milestones.append(fallback_milestone)
                    
                    logger.info(f"Added {missing_count} fallback milestones to phase {phase.phase_number} (target: {target_milestone_count})")

    def _enhance_roadmap_with_resources(self, roadmap: Roadmap, scraped_resources: List[LearningResource]):
        """Enhance roadmap phases with scraped learning resources"""
        
        for phase in roadmap.phases:
            # Match resources to phase skills
            phase_skills = [skill.name.lower() for skill in phase.skills_to_develop]
            
            # Find relevant resources
            relevant_resources = []
            for resource in scraped_resources:
                resource_skills = [skill.lower() for skill in resource.skills_covered]
                
                # Check if resource matches any phase skill
                if any(phase_skill in resource_skill or resource_skill in phase_skill 
                       for phase_skill in phase_skills 
                       for resource_skill in resource_skills):
                    relevant_resources.append(resource)
            
            # Add top 3 relevant resources to phase
            phase.learning_resources.extend(relevant_resources[:3])
    
    async def get_roadmap_suggestions(
        self,
        current_role: str,
        user_background: str,
        max_suggestions: int = 5
    ) -> List[str]:
        """Get suggested target roles based on current role and background"""
        
        try:
            await self._init_services()
            
            prompt = f"""Based on the current role and background, suggest {max_suggestions} realistic career transition options.

Current Role: {current_role}
Background: {user_background}

Provide {max_suggestions} specific target roles that would be good career moves. Consider:
- Natural progression paths
- Transferable skills
- Market demand
- Growth potential

Format as a simple list:
1. [Target Role 1]
2. [Target Role 2]
3. [Target Role 3]
etc.

Only provide the role names, no additional explanation."""
            
            response = await self.ai_service.generate_text(
                prompt=prompt,
                model_type=ModelType.GEMINI_FLASH,
                max_tokens=300,
                temperature=0.8
            )
            
            # Parse suggestions
            suggestions = []
            for line in response.split('\n'):
                line = line.strip()
                if re.match(r'^\d+\.', line):
                    suggestion = re.sub(r'^\d+\.\s*', '', line).strip()
                    if suggestion:
                        suggestions.append(suggestion)
            
            return suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Error getting roadmap suggestions: {str(e)}")
            return []
    
    # Database persistence methods
    async def save_roadmap(self, roadmap: Roadmap) -> str:
        """Save roadmap to database"""
        return await self.db_service.save_roadmap(roadmap)
    
    async def load_roadmap(self, roadmap_id: str) -> Optional[Roadmap]:
        """Load roadmap from database"""
        return await self.db_service.load_roadmap(roadmap_id)
    
    async def load_user_roadmaps(self, user_id: str) -> List[Roadmap]:
        """Load all roadmaps for a user"""
        return await self.db_service.load_user_roadmaps(user_id)
    
    async def update_roadmap_progress(self, roadmap_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update roadmap progress"""
        return await self.db_service.update_roadmap_progress(roadmap_id, progress_data)
    
    async def delete_roadmap(self, roadmap_id: str) -> bool:
        """Delete a roadmap"""
        return await self.db_service.delete_roadmap(roadmap_id)

# Singleton instance
_roadmap_service_instance = None

async def get_roadmap_service() -> RoadmapService:
    """Get or create singleton roadmap service instance"""
    global _roadmap_service_instance
    
    if _roadmap_service_instance is None:
        _roadmap_service_instance = RoadmapService()
    
    return _roadmap_service_instance