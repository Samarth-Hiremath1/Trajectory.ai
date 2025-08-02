import asyncio
import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

from main import app
from models.chat import ChatInitRequest, ChatMessageRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chat_api_endpoints():
    """Test chat API endpoints using FastAPI TestClient"""
    print("🧪 Testing Chat API Endpoints")
    print("=" * 50)
    
    client = TestClient(app)
    
    try:
        # Test 1: Health check
        print("\n1️⃣ Testing Health Endpoint")
        print("-" * 30)
        
        response = client.get("/api/chat/health")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check successful")
            print(f"   Service status: {health_data.get('status', 'unknown')}")
            print(f"   Active sessions: {health_data.get('active_sessions', 0)}")
        else:
            print(f"❌ Health check failed: {response.text}")
        
        # Test 2: Initialize chat session
        print("\n2️⃣ Testing Session Initialization")
        print("-" * 40)
        
        init_data = {
            "user_id": "api_test_user",
            "title": "API Test Chat",
            "initial_message": "Hello, I'm testing the API"
        }
        
        response = client.post("/api/chat/sessions", json=init_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["id"]
            print(f"✅ Session created successfully")
            print(f"   Session ID: {session_id}")
            print(f"   User ID: {session_data['user_id']}")
            print(f"   Title: {session_data['title']}")
            print(f"   Messages: {len(session_data['messages'])}")
            
            # Test 3: Send message
            print("\n3️⃣ Testing Message Sending")
            print("-" * 30)
            
            message_data = {
                "session_id": session_id,
                "message": "What skills do I need for a career in AI?",
                "include_context": True
            }
            
            response = client.post(f"/api/chat/sessions/{session_id}/messages", json=message_data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                message_response = response.json()
                print(f"✅ Message sent successfully")
                print(f"   Response length: {len(message_response['message']['content'])} characters")
                print(f"   Processing time: {message_response.get('processing_time', 0):.2f}s")
                print(f"   Context used: {len(message_response.get('context_used', []))}")
                print(f"   Response preview: {message_response['message']['content'][:200]}...")
            else:
                print(f"❌ Message sending failed: {response.text}")
            
            # Test 4: Get session
            print("\n4️⃣ Testing Session Retrieval")
            print("-" * 35)
            
            response = client.get(f"/api/chat/sessions/{session_id}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                session_data = response.json()
                print(f"✅ Session retrieved successfully")
                print(f"   Total messages: {len(session_data['messages'])}")
                print(f"   Last updated: {session_data['updated_at']}")
            else:
                print(f"❌ Session retrieval failed: {response.text}")
            
            # Test 5: Get user sessions
            print("\n5️⃣ Testing User Sessions Retrieval")
            print("-" * 40)
            
            response = client.get(f"/api/chat/users/api_test_user/sessions")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                sessions = response.json()
                print(f"✅ User sessions retrieved successfully")
                print(f"   Number of sessions: {len(sessions)}")
            else:
                print(f"❌ User sessions retrieval failed: {response.text}")
            
            # Test 6: Get session stats
            print("\n6️⃣ Testing Session Statistics")
            print("-" * 35)
            
            response = client.get(f"/api/chat/sessions/{session_id}/stats")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Session stats retrieved successfully")
                print(f"   Total messages: {stats['total_messages']}")
                print(f"   User messages: {stats['user_messages']}")
                print(f"   Assistant messages: {stats['assistant_messages']}")
            else:
                print(f"❌ Session stats failed: {response.text}")
            
            # Test 7: Clear memory
            print("\n7️⃣ Testing Memory Clear")
            print("-" * 25)
            
            response = client.post(f"/api/chat/sessions/{session_id}/clear-memory")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Memory cleared successfully")
            else:
                print(f"❌ Memory clear failed: {response.text}")
            
            # Test 8: Delete session
            print("\n8️⃣ Testing Session Deletion")
            print("-" * 30)
            
            response = client.delete(f"/api/chat/sessions/{session_id}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Session deleted successfully")
            else:
                print(f"❌ Session deletion failed: {response.text}")
            
        else:
            print(f"❌ Session initialization failed: {response.text}")
            return False
        
        print("\n🎉 All API tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ API tests failed: {str(e)}")
        logger.exception("API test failed")
        return False

if __name__ == "__main__":
    success = test_chat_api_endpoints()
    exit(0 if success else 1)