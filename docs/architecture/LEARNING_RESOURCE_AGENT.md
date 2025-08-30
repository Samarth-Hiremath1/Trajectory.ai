# Learning Resource Agent

## Overview

The Learning Resource Agent is a specialized AI agent designed for personalized learning path curation and resource recommendations. It provides comprehensive learning guidance including course recommendations, certification suggestions, and project-based learning opportunities.

## Features

### Core Capabilities

1. **Personalized Learning Path Curation**
   - Creates customized learning paths based on user goals and constraints
   - Considers learning style, timeline, budget, and current skill level
   - Provides structured phase-based progression

2. **Course Recommendation System**
   - Recommends courses with filtering by difficulty, budget, and learning style
   - Integrates with multiple learning platforms (Coursera, Udemy, edX, etc.)
   - Provides comparison matrices and filtered options

3. **Certification Recommendation Engine**
   - Suggests certifications based on target roles and career goals
   - Prioritizes certifications by industry value and career impact
   - Provides preparation plans and timelines

4. **Project Suggestion System**
   - Recommends hands-on projects for skill development
   - Maps projects to specific skills and learning objectives
   - Provides implementation guides and portfolio building advice

5. **External Platform Integration**
   - Integrates with roadmap.sh and other learning resources
   - Scrapes and curates content from external platforms
   - Provides access information and platform comparisons

## Architecture

### Agent Structure

```python
class LearningResourceAgent(BaseAgent):
    - agent_type: AgentType.LEARNING_RESOURCE
    - capabilities: 5 specialized capabilities
    - knowledge_bases: Learning platforms, certifications, project templates
    - external_integrations: RoadmapScraper, learning platforms
```

### Key Components

1. **Knowledge Bases**
   - Learning platforms database (Coursera, Udemy, Pluralsight, etc.)
   - Certification database (AWS, Google Cloud, Microsoft, etc.)
   - Project templates by skill category

2. **External Integrations**
   - RoadmapScraper for roadmap.sh content
   - Learning platform APIs (future enhancement)
   - Community resources and forums

3. **AI Processing**
   - LLM-powered analysis and recommendations
   - Context-aware resource curation
   - Personalized learning strategy generation

## API Endpoints

### Learning Path Creation

```http
POST /learning-resources/learning-path
```

**Request Body:**
```json
{
  "user_id": "string",
  "skills_to_learn": ["Python", "Machine Learning"],
  "learning_style": "hands-on",
  "timeline": "6 months",
  "budget": "medium",
  "current_level": "beginner"
}
```

**Response:**
```json
{
  "success": true,
  "learning_path": {
    "overview": {...},
    "learning_phases": [...],
    "total_duration": "6 months",
    "estimated_hours": 120
  },
  "resource_recommendations": {...},
  "milestone_plan": {...},
  "project_suggestions": [...]
}
```

### Skill-Specific Resources

```http
POST /learning-resources/skill-resources
```

**Request Body:**
```json
{
  "user_id": "string",
  "skills_needed": ["React", "Node.js"],
  "skill_gaps": {
    "React": {"level": "beginner", "priority": "high"}
  },
  "priority_skills": ["React"]
}
```

### Learning Advice

```http
POST /learning-resources/advice
```

**Request Body:**
```json
{
  "user_id": "string",
  "question": "What are the best resources to learn web development?"
}
```

### Platform Information

```http
GET /learning-resources/platforms
```

Returns information about available learning platforms.

### Role Certifications

```http
GET /learning-resources/certifications/{role}?level={level}
```

Returns certification recommendations for specific roles.

## Usage Examples

### 1. Creating a Personalized Learning Path

```python
from services.multi_agent_service import get_multi_agent_service

# Get multi-agent service
service = await get_multi_agent_service()

# Create learning path
result = await service.create_personalized_learning_path(
    user_id="user_123",
    skills_to_learn=["Python", "Data Science", "Machine Learning"],
    learning_style="hands-on",
    timeline="8 months",
    budget="medium",
    current_level="beginner"
)

# Access learning path
learning_path = result["responses"][0]["response_content"]["personalized_learning_path"]
```

### 2. Getting Skill-Specific Resources

```python
# Get resources for specific skills
result = await service.get_learning_resource_recommendations(
    user_id="user_123",
    skills_needed=["React", "Node.js", "MongoDB"],
    skill_gaps={"React": {"level": "beginner", "priority": "high"}},
    priority_skills=["React"]
)

# Access skill resources
skill_resources = result["responses"][0]["response_content"]["skill_learning_resources"]
```

### 3. Getting Learning Advice

```python
# Get learning advice
result = await service.get_learning_resource_advice(
    user_id="user_123",
    question="What's the best way to transition from frontend to full-stack development?"
)

# Access advice
advice = result["responses"][0]["response_content"]["learning_resource_advice"]
```

## Configuration

### Environment Variables

```bash
# AI Service Configuration
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# ChromaDB Configuration
CHROMA_DB_PATH=./chroma_db

# Agent Configuration
MAX_CONCURRENT_REQUESTS=3
DEFAULT_CONFIDENCE_THRESHOLD=0.8
```

### Agent Initialization

```python
from services.learning_resource_agent import LearningResourceAgent
from services.ai_service import get_ai_service
from services.embedding_service import get_embedding_service
from services.roadmap_scraper import RoadmapScraper

# Initialize services
ai_service = await get_ai_service()
embedding_service = get_embedding_service()
roadmap_scraper = RoadmapScraper()

# Initialize agent
agent = LearningResourceAgent(
    agent_id="learning_resource_001",
    ai_service=ai_service,
    embedding_service=embedding_service,
    roadmap_scraper=roadmap_scraper,
    max_concurrent_requests=3
)
```

## Learning Platforms Supported

### MOOCs (Massive Open Online Courses)
- **Coursera**: University partnerships, certificates, structured courses
- **edX**: University courses, free options, MicroMasters programs

### Professional Platforms
- **Pluralsight**: Technology focus, skill assessments, learning paths
- **LinkedIn Learning**: Business skills, professional development

### Marketplace Platforms
- **Udemy**: Practical skills, lifetime access, frequent sales

### Free Resources
- **YouTube**: Tutorials, visual learning, diverse creators
- **GitHub**: Open source projects, code examples
- **Documentation**: Official platform and framework docs

## Certification Providers

### Cloud Platforms
- **AWS**: Cloud Practitioner, Solutions Architect, Developer
- **Google Cloud**: Cloud Engineer, Data Engineer, Cloud Architect
- **Microsoft Azure**: Fundamentals, Developer, Solutions Architect

### Technology Vendors
- **Oracle**: Database, Java, Cloud certifications
- **Cisco**: Networking, cybersecurity certifications
- **VMware**: Virtualization and cloud infrastructure

### Industry Standards
- **CompTIA**: IT fundamentals, security, networking
- **PMI**: Project management certifications
- **Scrum Alliance**: Agile and Scrum certifications

## Project Templates

### Web Development
- Personal Portfolio Website
- E-commerce Application
- Blog Platform with CMS
- Real-time Chat Application

### Data Science
- Data Analysis Dashboard
- Machine Learning Model
- Predictive Analytics System
- Data Visualization Project

### Mobile Development
- Cross-platform Mobile App
- Native iOS/Android App
- Progressive Web App (PWA)
- Mobile Game Development

### DevOps/Infrastructure
- CI/CD Pipeline Setup
- Container Orchestration
- Infrastructure as Code
- Monitoring and Logging System

## Testing

### Unit Tests

```bash
# Run basic agent tests
python backend/test_learning_resource_agent_simple.py

# Run API tests
python backend/test_learning_resources_api.py
```

### Integration Tests

```bash
# Run full integration tests (requires API keys)
python backend/test_learning_resource_agent.py
```

### Test Coverage

The test suite covers:
- Agent initialization and capabilities
- Knowledge base loading
- Resource filtering and recommendation logic
- AI response parsing
- API endpoint functionality
- Request/response model validation

## Performance Considerations

### Optimization Strategies

1. **Caching**: Cache frequently requested resources and recommendations
2. **Batch Processing**: Group similar resource requests for efficiency
3. **Async Operations**: Use async/await for external API calls
4. **Resource Limits**: Limit number of resources per request to prevent overload

### Monitoring Metrics

- Request processing time
- Confidence scores
- Resource recommendation accuracy
- User satisfaction ratings
- Platform integration success rates

## Future Enhancements

### Planned Features

1. **Advanced Personalization**
   - Learning style assessment
   - Progress tracking integration
   - Adaptive recommendation algorithms

2. **Enhanced Platform Integration**
   - Direct API integration with learning platforms
   - Real-time course availability and pricing
   - Automated enrollment assistance

3. **Community Features**
   - Peer learning recommendations
   - Study group formation
   - Mentor matching

4. **Analytics and Insights**
   - Learning path effectiveness analysis
   - Resource quality scoring
   - Market trend integration

### Technical Improvements

1. **Machine Learning**
   - Collaborative filtering for recommendations
   - Natural language processing for better query understanding
   - Predictive modeling for learning outcomes

2. **Data Sources**
   - Integration with job market data
   - Skills demand analysis
   - Industry trend monitoring

3. **User Experience**
   - Interactive learning path visualization
   - Progress tracking dashboards
   - Mobile-optimized interfaces

## Troubleshooting

### Common Issues

1. **API Key Configuration**
   ```bash
   # Ensure API keys are properly set
   export GEMINI_API_KEY=your_key
   export OPENROUTER_API_KEY=your_key
   ```

2. **ChromaDB Connection**
   ```bash
   # Check ChromaDB path and permissions
   ls -la ./chroma_db
   ```

3. **External Resource Scraping**
   ```python
   # Test roadmap scraper connectivity
   scraper = RoadmapScraper()
   resources = await scraper.scrape_learning_resources(["python"])
   ```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

### Development Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run tests:
   ```bash
   python backend/test_learning_resource_agent_simple.py
   ```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Include comprehensive docstrings
- Write unit tests for new functionality

### Pull Request Process

1. Create feature branch from main
2. Implement changes with tests
3. Update documentation
4. Submit pull request with detailed description

## License

This project is licensed under the MIT License. See LICENSE file for details.