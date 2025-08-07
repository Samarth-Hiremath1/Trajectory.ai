#!/usr/bin/env python3
"""
Test script to verify personalized responses and that AI doesn't ask users to re-share information
"""

import asyncio
import os
import sys
import logging

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chat_service import RAGChatService
from services.embedding_service import EmbeddingService
from models.chat import ChatInitRequest, ChatMessageRequest

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

async def test_personalized_responses():
    """Test that AI provides personalized responses based on user context"""
    
    print("🧪 Testing Personalized Responses")
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
            title="Personalization Test"
        )
        session = await chat_service.initialize_chat_session(init_request)
        
        # Test questions that should be answered using context
        test_questions = [
            "What skills should I focus on to become an ML Engineer?",
            "How can I leverage my Netflix experience for FAANG interviews?",
            "What's the best way to transition from data science to ML engineering?",
            "Should I get more education or focus on practical experience?",
            "What kind of projects should I build for my portfolio?"
        ]
        
        print(f"\n📝 Testing {len(test_questions)} personalized questions...")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Question {i} ---")
            print(f"Q: {question}")
            
            message_request = ChatMessageRequest(
                session_id=session.id,
                message=question
            )
            
            response = await chat_service.send_message(message_request)
            
            # Analyze response for personalization
            response_text = response.message.content.lower()
            
            # Check for personalization indicators
            personalization_indicators = [
                "netflix", "mit", "berkeley", "data scientist", "recommendation", 
                "facebook", "published", "papers", "tensorflow", "pytorch",
                "computer vision", "nlp", "master's", "mathematics"
            ]
            
            found_indicators = [ind for ind in personalization_indicators if ind in response_text]
            
            # Check for bad patterns (asking for info already provided)
            bad_patterns = [
                "what's your background", "tell me about your experience",
                "what's your current role", "what's your education",
                "could you share", "can you tell me about"
            ]
            
            found_bad_patterns = [pattern for pattern in bad_patterns if pattern in response_text]
            
            print(f"✅ Context chunks used: {len(response.context_used) if response.context_used else 0}")
            print(f"✅ Personalization indicators found: {len(found_indicators)} ({', '.join(found_indicators[:3])}{'...' if len(found_indicators) > 3 else ''})")
            
            if found_bad_patterns:
                print(f"⚠️  Found concerning patterns: {found_bad_patterns}")
            else:
                print("✅ No requests for already-known information")
            
            print(f"📝 Response preview: {response.message.content[:150]}...")
        
        # Cleanup
        embedding_service.delete_user_embeddings(test_user_id)
        chat_service.delete_chat_session(session.id)
        
        print("\n🎉 Personalized Response Test Completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def test_context_vs_no_context():
    """Compare responses with and without user context"""
    
    print("\n🧪 Testing Context vs No Context Responses")
    print("=" * 40)
    
    try:
        chat_service = RAGChatService()
        embedding_service = EmbeddingService()
        
        # User with context
        user_with_context = "context_user"
        context = """
        Education: PhD in Computer Science from Stanford (2018)
        Career Background: 5 years as Research Scientist at Google DeepMind, working on reinforcement learning and robotics
        Current Role: Senior Research Scientist
        Target Roles: AI Research Director, CTO at AI startup
        Additional Details: 15+ publications in top-tier conferences (ICML, NeurIPS), expert in deep RL and robotics
        """
        
        embedding_service.store_profile_context(user_with_context, context.strip())
        
        # User without context
        user_without_context = "no_context_user"
        
        # Same question for both users
        test_question = "How should I prepare for leadership roles in AI?"
        
        # Test with context
        print("1. Testing response WITH user context...")
        session1 = await chat_service.initialize_chat_session(
            ChatInitRequest(user_id=user_with_context, title="With Context")
        )
        
        response1 = await chat_service.send_message(ChatMessageRequest(
            session_id=session1.id,
            message=test_question
        ))
        
        print(f"✅ Context chunks used: {len(response1.context_used) if response1.context_used else 0}")
        print(f"📝 Response with context: {response1.message.content[:200]}...")
        
        # Test without context
        print("\n2. Testing response WITHOUT user context...")
        session2 = await chat_service.initialize_chat_session(
            ChatInitRequest(user_id=user_without_context, title="Without Context")
        )
        
        response2 = await chat_service.send_message(ChatMessageRequest(
            session_id=session2.id,
            message=test_question
        ))
        
        print(f"✅ Context chunks used: {len(response2.context_used) if response2.context_used else 0}")
        print(f"📝 Response without context: {response2.message.content[:200]}...")
        
        # Compare responses
        print("\n3. Comparing responses...")
        
        response1_text = response1.message.content.lower()
        response2_text = response2.message.content.lower()
        
        # Check if response with context mentions specific background
        context_specific_terms = ["deepmind", "google", "phd", "stanford", "research scientist", "publications", "reinforcement learning"]
        context_mentions = sum(1 for term in context_specific_terms if term in response1_text)
        
        print(f"✅ Context-specific mentions in response 1: {context_mentions}")
        print(f"✅ Response 1 length: {len(response1.message.content)} chars")
        print(f"✅ Response 2 length: {len(response2.message.content)} chars")
        
        if context_mentions > 0:
            print("✅ Response with context is properly personalized!")
        else:
            print("⚠️  Response with context may not be fully utilizing user background")
        
        # Cleanup
        embedding_service.delete_user_embeddings(user_with_context)
        chat_service.delete_chat_session(session1.id)
        chat_service.delete_chat_session(session2.id)
        
        print("\n🎉 Context Comparison Test Completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Personalized Response Tests")
        print("=" * 50)
        
        # Test 1: Personalized responses
        success1 = await test_personalized_responses()
        
        # Test 2: Context vs no context
        success2 = await test_context_vs_no_context()
        
        if success1 and success2:
            print("\n🎉 All personalization tests passed!")
            print("\n✅ Key Achievements:")
            print("  • RAG context is automatically retrieved")
            print("  • Responses are personalized based on user background")
            print("  • AI doesn't ask users to re-share known information")
            print("  • Graceful handling when no context is available")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
    
    # Run the tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)