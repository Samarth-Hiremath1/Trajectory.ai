import asyncio
import pytest
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from models.chat import ChatInitRequest, ChatMessageRequest, MessageRole
from services.chat_service import RAGChatService, get_chat_service

# Load environment variables
load_dotenv()

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chat_service_basic_functionality():
    """Test basic chat service functionality"""
    print("🧪 Testing RAG-enabled Chat Service")
    print("=" * 50)
    
    try:
        # Initialize chat service
        chat_service = await get_chat_service()
        print("✅ Chat service initialized")
        
        # Test 1: Initialize chat session
        print("\n1️⃣ Testing Chat Session Initialization")
        print("-" * 40)
        
        init_request = ChatInitRequest(
            user_id="test_user_123",
            title="Test Career Chat",
            initial_message="Hello, I need help with my career transition from software engineer to product manager."
        )
        
        session = await chat_service.initialize_chat_session(init_request)
        print(f"✅ Session created: {session.id}")
        print(f"   User ID: {session.user_id}")
        print(f"   Title: {session.title}")
        print(f"   Messages: {len(session.messages)}")
        
        # Test 2: Send a message
        print("\n2️⃣ Testing Message Sending")
        print("-" * 30)
        
        message_request = ChatMessageRequest(
            session_id=session.id,
            message="What skills should I focus on developing to make this transition?",
            include_context=True
        )
        
        response = await chat_service.send_message(message_request)
        print(f"✅ Message sent and response received")
        print(f"   Response length: {len(response.message.content)} characters")
        print(f"   Processing time: {response.processing_time:.2f}s")
        print(f"   Context chunks used: {len(response.context_used) if response.context_used else 0}")
        print(f"   Response preview: {response.message.content[:200]}...")
        
        # Test 3: Get session
        print("\n3️⃣ Testing Session Retrieval")
        print("-" * 35)
        
        retrieved_session = chat_service.get_chat_session(session.id)
        if retrieved_session:
            print(f"✅ Session retrieved successfully")
            print(f"   Total messages: {len(retrieved_session.messages)}")
            print(f"   Last updated: {retrieved_session.updated_at}")
        else:
            print("❌ Failed to retrieve session")
        
        # Test 4: Get user sessions
        print("\n4️⃣ Testing User Sessions Retrieval")
        print("-" * 40)
        
        user_sessions = chat_service.get_user_sessions("test_user_123")
        print(f"✅ Found {len(user_sessions)} sessions for user")
        
        # Test 5: Session stats
        print("\n5️⃣ Testing Session Statistics")
        print("-" * 35)
        
        stats = chat_service.get_session_stats(session.id)
        if stats:
            print(f"✅ Session stats retrieved:")
            print(f"   Total messages: {stats['total_messages']}")
            print(f"   User messages: {stats['user_messages']}")
            print(f"   Assistant messages: {stats['assistant_messages']}")
            print(f"   Duration: {stats['duration_minutes']:.2f} minutes")
        
        # Test 6: Another message to test memory
        print("\n6️⃣ Testing Conversation Memory")
        print("-" * 35)
        
        follow_up_request = ChatMessageRequest(
            session_id=session.id,
            message="Can you elaborate on the first skill you mentioned?",
            include_context=True
        )
        
        follow_up_response = await chat_service.send_message(follow_up_request)
        print(f"✅ Follow-up message processed")
        print(f"   Response preview: {follow_up_response.message.content[:200]}...")
        
        # Test 7: Health check
        print("\n7️⃣ Testing Service Health Check")
        print("-" * 35)
        
        health = await chat_service.health_check()
        print(f"✅ Health check completed")
        print(f"   Status: {health['status']}")
        print(f"   Active sessions: {health['active_sessions']}")
        print(f"   AI service status: {health.get('ai_service_status', 'unknown')}")
        
        # Test 8: Clear memory
        print("\n8️⃣ Testing Memory Management")
        print("-" * 35)
        
        memory_cleared = chat_service.clear_session_memory(session.id)
        print(f"✅ Memory cleared: {memory_cleared}")
        
        # Test 9: Delete session
        print("\n9️⃣ Testing Session Deletion")
        print("-" * 30)
        
        deleted = chat_service.delete_chat_session(session.id)
        print(f"✅ Session deleted: {deleted}")
        
        print("\n🎉 All chat service tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        logger.exception("Test failed")
        raise

async def test_chat_service_with_context():
    """Test chat service with RAG context (requires resume data)"""
    print("\n🧪 Testing Chat Service with RAG Context")
    print("=" * 50)
    
    try:
        chat_service = await get_chat_service()
        
        # Create session for user with resume data
        init_request = ChatInitRequest(
            user_id="temp_user_123",  # This user should have resume data from previous tests
            title="Context-Aware Career Chat"
        )
        
        session = await chat_service.initialize_chat_session(init_request)
        print(f"✅ Session created for user with potential resume data")
        
        # Send a message that should trigger context retrieval
        message_request = ChatMessageRequest(
            session_id=session.id,
            message="Based on my background, what are my strongest skills for a PM role?",
            include_context=True
        )
        
        response = await chat_service.send_message(message_request)
        print(f"✅ Context-aware response generated")
        print(f"   Context chunks found: {len(response.context_used) if response.context_used else 0}")
        
        if response.context_used:
            print("   Context preview:")
            for i, chunk in enumerate(response.context_used[:2]):
                print(f"     Chunk {i+1}: {chunk.get('content', '')[:100]}...")
        
        print(f"   Response: {response.message.content[:300]}...")
        
        # Clean up
        chat_service.delete_chat_session(session.id)
        print("✅ Context test completed")
        
    except Exception as e:
        print(f"❌ Context test failed: {str(e)}")
        logger.exception("Context test failed")

async def main():
    """Run all chat service tests"""
    print("🚀 Starting Chat Service Tests")
    print("=" * 60)
    
    try:
        # Run basic functionality tests
        await test_chat_service_basic_functionality()
        
        # Run context-aware tests
        await test_chat_service_with_context()
        
        print("\n🎊 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Tests failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)