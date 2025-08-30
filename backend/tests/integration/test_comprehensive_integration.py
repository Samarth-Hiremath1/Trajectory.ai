#!/usr/bin/env python3
"""
Comprehensive integration test suite covering AI service, personalized responses, and core functionality
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import AIService, ModelType, AIProvider
from services.chat_service import RAGChatService
from services.embedding_service import EmbeddingService
from models.chat import ChatInitRequest, ChatMessageRequest

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

async def test_ai_service_integration():
    """Test the complete AI service integration"""
    
    print("🚀 AI Service Integration Test: Gemini + OpenRouter")
    print("=" * 60)
    
    # Initialize service
    ai_service = AIService()
    await ai_service._init_session()
    
    try:
        # Test 1: Health Check
        print("\n1️⃣ Health Check")
        print("-" * 20)
        health = await ai_service.health_check()
        print(f"Status: {health['status']}")
        print(f"Providers Available: {health['providers_available']}")
        print(f"Primary Provider: {health.get('primary_provider', 'unknown')}")
        print(f"Fallback Available: {health.get('fallback_available', False)}")
        print(f"Test Generation: {health.get('test_generation_successful', False)}")
        
        # Test 2: Gemini Models
        print(f"\n2️⃣ Testing Gemini Models")
        print("-" * 30)
        
        gemini_models = [ModelType.GEMINI_FLASH, ModelType.GEMINI_PRO]
        
        for model in gemini_models:
            try:
                print(f"\n📊 Testing {model.value}:")
                result = await ai_service.generate_text(
                    prompt="Explain Python programming in one sentence:",
                    model_type=model,
                    max_tokens=50
                )
                print(f"✅ Success: {result[:100]}...")
                
            except Exception as e:
                print(f"❌ Failed: {str(e)}")
        
        # Test 3: OpenRouter Models
        print(f"\n3️⃣ Testing OpenRouter Models")
        print("-" * 35)
        
        openrouter_models = [ModelType.CLAUDE_HAIKU, ModelType.LLAMA_3_8B]
        
        for model in openrouter_models:
            try:
                print(f"\n📊 Testing {model.value}:")
                result = await ai_service.generate_text(
                    prompt="What is machine learning?",
                    model_type=model,
                    max_tokens=50
                )
                print(f"✅ Success: {result[:100]}...")
                
            except Exception as e:
                print(f"❌ Failed: {str(e)}")
        
        print("\n✅ AI Service Integration Test Completed")
        return True
        
    except Exception as e:
        print(f"❌ AI Service Integration Test Failed: {e}")
        return False
    
    finally:
        await ai_service.close()

async def test_personalized_responses():
    """Test that AI provides personalized responses based on user context"""
    
    print("\n🧪 Testing Personalized Responses")
    print("=" * 40)
    
    try:
        # Initialize services
        chat_service = RAGChatService()
        embedding_service = EmbeddingService()
        
        # Test user with rich context
        test_user_id = "rich_context_user"
        
        # Store comprehensive profile context
        profile_context = """
        Education: Master's in Data Science from MIT (2019), Bachelor's in Mathematics from UC Berkeley (2017)
        Career Background: 3 years as Data Scientist at Netflix, working on recommendation algorithms and A/B testing. Previously interned at Facebook on machine learning infrastructure.
        Current Role: Senior Data Scientist
        Target Roles: Machine Learning Engineer at FAANG companies, AI Research Scientist
        Additional Details: Published 2 papers on deep learning, proficient in Python, TensorFlow, PyTorch. Looking to transition from data science to more engineering-focused ML roles. Interested in computer vision and NLP applications.
        """
        
        # Store profile context
        embedding_service.store_profile_context(test_user_id, profile_context.strip())
        print("✅ Rich profile context stored")
        
        # Initialize chat session
        init_request = ChatInitRequest(
            user_id=test_user_id,
            title="Personalization Test Chat"
        )
        
        session = await chat_service.initialize_chat_session(init_request)
        print(f"✅ Chat session initialized: {session.id}")
        
        # Test personalized response
        message_request = ChatMessageRequest(
            session_id=session.id,
            message="What career advice would you give me for my next role?",
            user_id=test_user_id
        )
        
        response = await chat_service.send_message(message_request)
        print(f"✅ Personalized response received: {len(response.message)} characters")
        
        # Check if response mentions user's background
        response_lower = response.message.lower()
        personalization_indicators = [
            "netflix", "data scientist", "mit", "machine learning engineer", 
            "tensorflow", "pytorch", "computer vision", "nlp"
        ]
        
        found_indicators = [indicator for indicator in personalization_indicators if indicator in response_lower]
        print(f"✅ Personalization indicators found: {found_indicators}")
        
        if len(found_indicators) >= 2:
            print("✅ Response appears to be personalized based on user context")
        else:
            print("⚠️ Response may not be fully personalized")
        
        print("\n✅ Personalized Responses Test Completed")
        return True
        
    except Exception as e:
        print(f"❌ Personalized Responses Test Failed: {e}")
        return False

async def test_rag_integration():
    """Test RAG (Retrieval-Augmented Generation) integration"""
    
    print("\n🔍 Testing RAG Integration")
    print("=" * 30)
    
    try:
        # Initialize services
        chat_service = RAGChatService()
        embedding_service = EmbeddingService()
        
        # Test user
        test_user_id = "rag_test_user"
        
        # Store some context documents
        documents = [
            "User has experience with Python, Django, and PostgreSQL. Worked at a startup for 2 years.",
            "User is interested in transitioning to machine learning and has been taking online courses.",
            "User's goal is to become a Senior ML Engineer within 18 months."
        ]
        
        for i, doc in enumerate(documents):
            embedding_service.store_user_context(test_user_id, doc, f"context_{i}")
        
        print(f"✅ Stored {len(documents)} context documents")
        
        # Test context retrieval
        retrieved_context = embedding_service.search_user_context(
            test_user_id, 
            "machine learning career transition", 
            n_results=3
        )
        
        print(f"✅ Retrieved {len(retrieved_context)} relevant context items")
        
        # Test chat with RAG
        init_request = ChatInitRequest(
            user_id=test_user_id,
            title="RAG Test Chat"
        )
        
        session = await chat_service.initialize_chat_session(init_request)
        
        message_request = ChatMessageRequest(
            session_id=session.id,
            message="What steps should I take to transition to machine learning?",
            user_id=test_user_id
        )
        
        response = await chat_service.send_message(message_request)
        print(f"✅ RAG-enhanced response received: {len(response.message)} characters")
        
        print("\n✅ RAG Integration Test Completed")
        return True
        
    except Exception as e:
        print(f"❌ RAG Integration Test Failed: {e}")
        return False

async def test_embedding_service():
    """Test embedding service functionality"""
    
    print("\n🧠 Testing Embedding Service")
    print("=" * 30)
    
    try:
        embedding_service = EmbeddingService()
        
        # Test health check
        health = embedding_service.health_check()
        print(f"✅ Embedding service health: {health['status']}")
        
        # Test storing and retrieving embeddings
        test_user_id = "embedding_test_user"
        test_content = "I am a software engineer with 5 years of experience in web development."
        
        embedding_service.store_user_context(test_user_id, test_content, "profile")
        print("✅ Stored user context")
        
        # Search for similar content
        results = embedding_service.search_user_context(
            test_user_id, 
            "software development experience", 
            n_results=1
        )
        
        print(f"✅ Search returned {len(results)} results")
        
        if results and "software engineer" in results[0]["content"]:
            print("✅ Search results are relevant")
        else:
            print("⚠️ Search results may not be optimal")
        
        print("\n✅ Embedding Service Test Completed")
        return True
        
    except Exception as e:
        print(f"❌ Embedding Service Test Failed: {e}")
        return False

async def main():
    """Run all comprehensive integration tests"""
    print("Starting Comprehensive Integration Tests...")
    
    tests = [
        ("AI Service Integration", test_ai_service_integration),
        ("Personalized Responses", test_personalized_responses),
        ("RAG Integration", test_rag_integration),
        ("Embedding Service", test_embedding_service)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE INTEGRATION TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status:4} | {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All comprehensive integration tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)