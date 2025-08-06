import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import re
from dataclasses import dataclass
from models.roadmap import LearningResource, ResourceType, SkillLevel

logger = logging.getLogger(__name__)

@dataclass
class ScrapedResource:
    """Scraped learning resource data"""
    title: str
    description: str
    url: str
    resource_type: str
    provider: str
    skills: List[str]
    difficulty: Optional[str] = None
    duration: Optional[str] = None

class RoadmapScraper:
    """Service for scraping roadmap.sh and other learning resources"""
    
    def __init__(self, max_concurrent_requests: int = 5, request_timeout: int = 10):
        self.max_concurrent_requests = max_concurrent_requests
        self.request_timeout = request_timeout
        self.session = None
        
        # Known roadmap.sh paths for different roles
        self.roadmap_paths = {
            "frontend": "frontend",
            "backend": "backend", 
            "devops": "devops",
            "android": "android",
            "ios": "ios",
            "python": "python",
            "java": "java",
            "javascript": "javascript",
            "react": "react",
            "vue": "vue",
            "angular": "angular",
            "nodejs": "nodejs",
            "go": "golang",
            "rust": "rust",
            "cpp": "cpp",
            "system-design": "system-design",
            "software-architect": "software-architect",
            "qa": "qa",
            "product-manager": "product-manager",
            "data-scientist": "data-scientist",
            "machine-learning": "ai-data-scientist",
            "blockchain": "blockchain",
            "cyber-security": "cyber-security",
            "ux-design": "ux-design"
        }
        
        # Learning platforms to scrape
        self.learning_platforms = {
            "coursera": "https://www.coursera.org",
            "edx": "https://www.edx.org", 
            "udemy": "https://www.udemy.com",
            "pluralsight": "https://www.pluralsight.com",
            "codecademy": "https://www.codecademy.com"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()
    
    async def _init_session(self):
        """Initialize aiohttp session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from URL with error handling"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def _extract_skills_from_role(self, role: str) -> List[str]:
        """Extract relevant skills from role name"""
        role_lower = role.lower()
        
        # Common skill mappings
        skill_mappings = {
            "software engineer": ["programming", "algorithms", "data structures", "system design"],
            "frontend": ["html", "css", "javascript", "react", "vue", "angular"],
            "backend": ["api design", "databases", "server architecture", "microservices"],
            "full stack": ["frontend", "backend", "databases", "deployment"],
            "devops": ["docker", "kubernetes", "ci/cd", "cloud platforms", "monitoring"],
            "data scientist": ["python", "machine learning", "statistics", "data analysis"],
            "product manager": ["product strategy", "user research", "analytics", "roadmapping"],
            "mobile": ["ios", "android", "mobile ui", "app store optimization"],
            "machine learning": ["python", "tensorflow", "pytorch", "deep learning", "nlp"],
            "security": ["cybersecurity", "penetration testing", "security auditing"],
            "qa": ["testing", "automation", "quality assurance", "test planning"]
        }
        
        skills = []
        for key, skill_list in skill_mappings.items():
            if key in role_lower:
                skills.extend(skill_list)
        
        return list(set(skills))  # Remove duplicates
    
    async def scrape_roadmap_sh(self, role_key: str) -> List[ScrapedResource]:
        """Scrape roadmap.sh for a specific role"""
        if not self.session:
            await self._init_session()
        
        resources = []
        
        # Get the roadmap path
        roadmap_path = self.roadmap_paths.get(role_key.lower())
        if not roadmap_path:
            logger.warning(f"No roadmap path found for role: {role_key}")
            return resources
        
        # Construct URL
        base_url = "https://roadmap.sh"
        roadmap_url = f"{base_url}/{roadmap_path}"
        
        try:
            content = await self._fetch_url(roadmap_url)
            if not content:
                return resources
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract roadmap topics/skills
            # roadmap.sh uses various selectors, we'll try common ones
            selectors = [
                '.roadmap-topic',
                '.topic',
                '[data-group-id]',
                '.group-title',
                'text[data-group-id]'
            ]
            
            skills = self._extract_skills_from_role(role_key)
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 2:
                        skills.append(text)
            
            # Create generic resources based on extracted skills
            for skill in list(set(skills))[:20]:  # Limit to 20 skills
                resource = ScrapedResource(
                    title=f"Learn {skill.title()}",
                    description=f"Master {skill} skills for {role_key} role",
                    url=roadmap_url,
                    resource_type="course",
                    provider="roadmap.sh",
                    skills=[skill],
                    difficulty="intermediate"
                )
                resources.append(resource)
            
            logger.info(f"Scraped {len(resources)} resources from roadmap.sh for {role_key}")
            
        except Exception as e:
            logger.error(f"Error scraping roadmap.sh for {role_key}: {str(e)}")
        
        return resources
    
    async def scrape_learning_resources(self, skills: List[str], max_per_skill: int = 3) -> List[ScrapedResource]:
        """Scrape learning resources for specific skills"""
        if not self.session:
            await self._init_session()
        
        all_resources = []
        
        # Create mock resources based on skills (since actual scraping would be complex)
        # In a real implementation, you'd scrape actual course platforms
        
        resource_templates = [
            {
                "provider": "Coursera",
                "resource_type": "course",
                "duration": "4-6 weeks",
                "difficulty": "intermediate"
            },
            {
                "provider": "edX",
                "resource_type": "course", 
                "duration": "6-8 weeks",
                "difficulty": "beginner"
            },
            {
                "provider": "Udemy",
                "resource_type": "course",
                "duration": "10-20 hours",
                "difficulty": "intermediate"
            },
            {
                "provider": "Pluralsight",
                "resource_type": "course",
                "duration": "2-4 hours",
                "difficulty": "advanced"
            },
            {
                "provider": "YouTube",
                "resource_type": "video",
                "duration": "1-2 hours",
                "difficulty": "beginner"
            }
        ]
        
        for skill in skills[:10]:  # Limit to 10 skills
            for i, template in enumerate(resource_templates[:max_per_skill]):
                resource = ScrapedResource(
                    title=f"{skill.title()} Mastery - {template['provider']}",
                    description=f"Comprehensive {skill} training from {template['provider']}",
                    url=f"https://example.com/{skill.lower().replace(' ', '-')}-course-{i+1}",
                    resource_type=template["resource_type"],
                    provider=template["provider"],
                    skills=[skill],
                    difficulty=template["difficulty"],
                    duration=template["duration"]
                )
                all_resources.append(resource)
        
        logger.info(f"Generated {len(all_resources)} learning resources for {len(skills)} skills")
        return all_resources
    
    def _map_difficulty(self, difficulty_str: str) -> SkillLevel:
        """Map difficulty string to SkillLevel enum"""
        if not difficulty_str:
            return SkillLevel.INTERMEDIATE
        
        difficulty_lower = difficulty_str.lower()
        if "beginner" in difficulty_lower or "basic" in difficulty_lower:
            return SkillLevel.BEGINNER
        elif "advanced" in difficulty_lower or "expert" in difficulty_lower:
            return SkillLevel.ADVANCED
        else:
            return SkillLevel.INTERMEDIATE
    
    def _map_resource_type(self, type_str: str) -> ResourceType:
        """Map resource type string to ResourceType enum"""
        if not type_str:
            return ResourceType.COURSE
        
        type_lower = type_str.lower()
        if "course" in type_lower:
            return ResourceType.COURSE
        elif "certification" in type_lower or "cert" in type_lower:
            return ResourceType.CERTIFICATION
        elif "project" in type_lower:
            return ResourceType.PROJECT
        elif "book" in type_lower:
            return ResourceType.BOOK
        elif "article" in type_lower:
            return ResourceType.ARTICLE
        elif "video" in type_lower:
            return ResourceType.VIDEO
        elif "practice" in type_lower:
            return ResourceType.PRACTICE
        else:
            return ResourceType.COURSE
    
    def convert_to_learning_resources(self, scraped_resources: List[ScrapedResource]) -> List[LearningResource]:
        """Convert scraped resources to LearningResource models"""
        learning_resources = []
        
        for scraped in scraped_resources:
            resource = LearningResource(
                title=scraped.title,
                description=scraped.description,
                url=scraped.url,
                resource_type=self._map_resource_type(scraped.resource_type),
                provider=scraped.provider,
                duration=scraped.duration,
                difficulty=self._map_difficulty(scraped.difficulty) if scraped.difficulty else None,
                skills_covered=scraped.skills
            )
            learning_resources.append(resource)
        
        return learning_resources
    
    async def get_resources_for_transition(
        self, 
        current_role: str, 
        target_role: str,
        max_resources: int = 20
    ) -> List[LearningResource]:
        """Get learning resources for a career transition"""
        
        # Extract role keys for roadmap.sh
        current_key = self._extract_role_key(current_role)
        target_key = self._extract_role_key(target_role)
        
        all_scraped = []
        
        # Scrape roadmap.sh for target role
        if target_key:
            target_resources = await self.scrape_roadmap_sh(target_key)
            all_scraped.extend(target_resources)
        
        # Extract skills needed for transition
        target_skills = self._extract_skills_from_role(target_role)
        current_skills = self._extract_skills_from_role(current_role)
        
        # Find skills gap
        skills_gap = [skill for skill in target_skills if skill not in current_skills]
        
        # Scrape additional learning resources for skills gap
        if skills_gap:
            additional_resources = await self.scrape_learning_resources(skills_gap)
            all_scraped.extend(additional_resources)
        
        # Convert to LearningResource models
        learning_resources = self.convert_to_learning_resources(all_scraped)
        
        # Limit and return
        return learning_resources[:max_resources]
    
    def _extract_role_key(self, role: str) -> Optional[str]:
        """Extract roadmap.sh key from role name"""
        role_lower = role.lower()
        
        # Direct mappings
        for key in self.roadmap_paths.keys():
            if key in role_lower:
                return key
        
        # Fuzzy matching
        if "frontend" in role_lower or "front-end" in role_lower:
            return "frontend"
        elif "backend" in role_lower or "back-end" in role_lower:
            return "backend"
        elif "full stack" in role_lower or "fullstack" in role_lower:
            return "backend"  # Default to backend for full stack
        elif "mobile" in role_lower:
            return "android"  # Default to android for mobile
        elif "data" in role_lower and "scientist" in role_lower:
            return "data-scientist"
        elif "product" in role_lower and "manager" in role_lower:
            return "product-manager"
        elif "devops" in role_lower:
            return "devops"
        elif "security" in role_lower:
            return "cyber-security"
        elif "qa" in role_lower or "test" in role_lower:
            return "qa"
        
        return None

# Singleton instance
_scraper_instance = None

async def get_roadmap_scraper() -> RoadmapScraper:
    """Get or create singleton scraper instance"""
    global _scraper_instance
    
    if _scraper_instance is None:
        _scraper_instance = RoadmapScraper()
        await _scraper_instance._init_session()
    
    return _scraper_instance

async def cleanup_scraper():
    """Cleanup singleton scraper instance"""
    global _scraper_instance
    
    if _scraper_instance:
        await _scraper_instance._close_session()
        _scraper_instance = None