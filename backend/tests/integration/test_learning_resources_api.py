"""
Test script for Learning Resources API endpoints
"""
import asyncio
import logging
import sys
import os
import json

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from api.learning_resources import router
from fastapi import FastAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_learning_resources_api():
    """Test the Learning Resources API endpoints"""
    
    try:
        logger.info("Starting Learning Resources API test...")
        
        # Create test app
        app = FastAPI()
        app.include_router(router)
        
        # Create test client
        client = TestClient(app)
        
        # Test 1: Health check
        logger.info("\n=== Test 1: Health Check ===")
        response = client.get("/learning-resources/health")
        logger.info(f"Health check status: {response.status_code}")
        logger.info(f"Health check response: {response.json()}")
        assert response.status_code == 200
        
        # Test 2: Get learning platforms
        logger.info("\n=== Test 2: Get Learning Platforms ===")
        response = client.get("/learning-resources/platforms")
        logger.info(f"Platforms status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Success: {data.get('success')}")
            logger.info(f"Total platforms: {data.get('total_platforms')}")
            
            platforms = data.get('platforms', {})
            for platform_name in list(platforms.keys())[:3]:
                platform = platforms[platform_name]
                logger.info(f"- {platform['name']}: {platform['type']} - {platform['cost_model']}")
        
        # Test 3: Get role certifications
        logger.info("\n=== Test 3: Get Role Certifications ===")
        response = client.get("/learning-resources/certifications/software engineer")
        logger.info(f"Certifications status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Success: {data.get('success')}")
            logger.info(f"Role: {data.get('role')}")
            logger.info(f"Total certifications: {data.get('total_certifications')}")
            
            certifications = data.get('certifications', {})
            for cert_name in list(certifications.keys())[:2]:
                cert = certifications[cert_name]
                logger.info(f"- {cert['name']}: {cert['provider']} - {cert['cost']}")
        
        # Test 4: Get role certifications with level filter
        logger.info("\n=== Test 4: Get Role Certifications (Mid Level) ===")
        response = client.get("/learning-resources/certifications/data scientist?level=mid")
        logger.info(f"Filtered certifications status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Success: {data.get('success')}")
            logger.info(f"Level filter: {data.get('level_filter')}")
            logger.info(f"Total certifications: {data.get('total_certifications')}")
        
        # Note: The following tests would require the multi-agent service to be running
        # and properly configured, so we'll skip them for now
        
        logger.info("\n=== Skipping Multi-Agent Service Tests ===")
        logger.info("The following endpoints require a running multi-agent service:")
        logger.info("- POST /learning-resources/learning-path")
        logger.info("- POST /learning-resources/skill-resources")
        logger.info("- POST /learning-resources/advice")
        logger.info("These would be tested in integration tests with proper service setup.")
        
        logger.info("\n🎉 Learning Resources API test completed successfully!")
        
    except Exception as e:
        logger.error(f"API test failed with error: {str(e)}")
        raise

def test_request_response_models():
    """Test the request and response models"""
    
    try:
        logger.info("\n=== Testing Request/Response Models ===")
        
        from api.learning_resources import (
            LearningPathRequest, SkillResourceRequest, LearningAdviceRequest,
            LearningPathResponse, ResourceRecommendationResponse, LearningAdviceResponse
        )
        
        # Test LearningPathRequest
        learning_path_req = LearningPathRequest(
            user_id="test_user_123",
            skills_to_learn=["Python", "Machine Learning"],
            learning_style="hands-on",
            timeline="6 months",
            budget="medium",
            current_level="beginner"
        )
        logger.info(f"LearningPathRequest created: {learning_path_req.user_id}")
        logger.info(f"Skills to learn: {learning_path_req.skills_to_learn}")
        logger.info(f"Learning style: {learning_path_req.learning_style}")
        
        # Test SkillResourceRequest
        skill_resource_req = SkillResourceRequest(
            user_id="test_user_123",
            skills_needed=["React", "Node.js"],
            skill_gaps={"React": {"level": "beginner"}},
            priority_skills=["React"]
        )
        logger.info(f"SkillResourceRequest created: {skill_resource_req.user_id}")
        logger.info(f"Skills needed: {skill_resource_req.skills_needed}")
        
        # Test LearningAdviceRequest
        advice_req = LearningAdviceRequest(
            user_id="test_user_123",
            question="What are the best resources to learn web development?"
        )
        logger.info(f"LearningAdviceRequest created: {advice_req.user_id}")
        logger.info(f"Question: {advice_req.question}")
        
        # Test Response models
        learning_path_resp = LearningPathResponse(
            success=True,
            learning_path={"phases": []},
            resource_recommendations={"phase1": []},
            request_id="test_request_123"
        )
        logger.info(f"LearningPathResponse created: {learning_path_resp.success}")
        
        resource_resp = ResourceRecommendationResponse(
            success=True,
            skill_resources={"Python": []},
            learning_sequence=[],
            request_id="test_request_123"
        )
        logger.info(f"ResourceRecommendationResponse created: {resource_resp.success}")
        
        advice_resp = LearningAdviceResponse(
            success=True,
            advice="Here's some learning advice...",
            recommendations=[],
            strategies=["hands-on learning"],
            request_id="test_request_123"
        )
        logger.info(f"LearningAdviceResponse created: {advice_resp.success}")
        
        logger.info("✅ All request/response models validated successfully!")
        
    except Exception as e:
        logger.error(f"Model validation failed: {str(e)}")
        raise

def main():
    """Main test function"""
    try:
        test_learning_resources_api()
        test_request_response_models()
        
        logger.info("\n🎉 All API tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()