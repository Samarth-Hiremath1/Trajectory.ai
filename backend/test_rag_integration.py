#!/usr/bin/env python3
"""
Test script for RAG integration in AI mentor chat
This script tests the automatic context retrieval functionality
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chat_service import RAGChatService
from services.embedding_service import EmbeddingService
from models.chat import ChatInitRequest, ChatMessageRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_integration():
    """Test the RAG integration functionality"""
    
    print("🧪 Testing RAG Integration for AI Mentor Chat")
    print("=" * 50)
    
    try:
        # Initialize services
        print("1. Initializing services...")
        chat_service = RAGChatService()
        embedding_service = EmbeddingService()
        
        # Test user ID
        test_user_id = "test_user_123"
        
        # Test 1: Store some test profile context
        print("\n2. Storing test profile context...")
        test_profile_context = """
        Education: Bachelor's in Computer Science from Stanford University (2020)
        Career Background: 2 years as Software Engineer at Google, working on search algorithms
        Current Role: Software Engineer
        Target Roles: Product Manager, Technical Lead
        Additional Details: Interested in transitioning to product management, has experience with machine learning
        """
        
        success = embedding_service.store_profile_context(test_user_id, test_profile_context.strip())
        if success:
            print("✅ Profile context stored successfully")
        else:
            print("❌ Failed to store profile context")
            return
        
        # Test 2: Initialize chat session
        print("\n3. Initializing chat session...")
        init_request = ChatInitRequest(
            user_id=test_user_id,
            title="RAG Integration Test"
        )
        
        session = await chat_service.initialize_chat_session(init_request)
        print(f"✅ Chat session initialized: {session.id}")
        
        # Test 3: Send a message that should trigger RAG context retrieval
        print("\n4. Testing RAG context retrieval...")
        message_request = ChatMessageRequest(
            session_id=session.id,
            message="What skills should I develop to transition from my current role to product management?"
        )
        
        print("Sending message:", message_request.message)
        response = await chat_service.send_message(message_request)
        
        print(f"✅ Response received in {response.processing_time:.2f}s")
        print(f"📊 Context chunks used: {len(response.context_used) if response.context_used else 0}")
        
        if response.context_used:
            print("\n📋 Context used:")
            for i, chunk in enumerate(response.context_used):
                print(f"  {i+1}. Source: {chunk.get('source', 'unknown')}")
                print(f"     Content: {chunk['content'][:100]}...")
                print(f"     Distance: {chunk.get('distance', 'N/A')}")
        
        print(f"\n🤖 AI Response:")
        print(f"   {response.message.content}")
        
        # Test 4: Test context refresh
        print("\n5. Testing context refresh...")
        refresh_success = await chat_service.refresh_user_context(test_user_id)
        if refresh_success:
            print("✅ Context refresh successful")
        else:
            print("❌ Context refresh failed")
        
        # Test 5: Health check
        print("\n6. Running health check...")
        health = await chat_service.health_check()
        print(f"✅ Service status: {health['status']}")
        print(f"📊 Active sessions: {health.get('active_sessions', 0)}")
        print(f"🔧 Embedding available: {health.get('embedding_available', False)}")
        print(f"📄 Resume service available: {health.get('resume_available', False)}")
        
        # Cleanup
        print("\n7. Cleaning up...")
        embedding_service.delete_user_embeddings(test_user_id)
        chat_service.delete_chat_session(session.id)
        print("✅ Cleanup completed")
        
        print("\n🎉 RAG Integration Test Completed Successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("Test failed")
        return False
    
    return True

async def test_error_handling():
    """Test error handling and graceful degradation"""
    
    print("\n🧪 Testing Error Handling and Graceful Degradation")
    print("=" * 50)
    
    try:
        chat_service = RAGChatService()
        
        # Test with non-existent user (should gracefully handle missing context)
        test_user_id = "nonexistent_user_999"
        
        print("1. Testing with user who has no context...")
        init_request = ChatInitRequest(
            user_id=test_user_id,
            title="Error Handling Test"
        )
        
        session = await chat_service.initialize_chat_session(init_request)
        print(f"✅ Chat session initialized: {session.id}")
        
        message_request = ChatMessageRequest(
            session_id=session.id,
            message="Can you help me with my career goals?"
        )
        
        response = await chat_service.send_message(message_request)
        print(f"✅ Response received despite no user context")
        print(f"📊 Context chunks used: {len(response.context_used) if response.context_used else 0}")
        print(f"🤖 AI Response: {response.message.content[:200]}...")
        
        # Cleanup
        chat_service.delete_chat_session(session.id)
        print("✅ Error handling test completed")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    async def main():
        print("🚀 Starting RAG Integration Tests")
        print("=" * 50)
        
        # Test 1: Basic RAG integration
        success1 = await test_rag_integration()
        
        # Test 2: Error handling
        success2 = await test_error_handling()
        
        if success1 and success2:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
    
    # Run the tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)