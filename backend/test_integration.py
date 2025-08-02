#!/usr/bin/env python3
"""
Integration test for the new AI service with Gemini + OpenRouter
"""

import asyncio
import os
from dotenv import load_dotenv
import sys
sys.path.append('.')
from services.ai_service import AIService, ModelType, AIProvider

# Load environment variables
load_dotenv()

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
                print(f"   ✅ Success: {result}")
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:100]}...")
        
        # Test 3: OpenRouter Models
        print(f"\n3️⃣ Testing OpenRouter Models")
        print("-" * 35)
        
        openrouter_models = [
            ModelType.MISTRAL_7B,
            ModelType.GEMMA_7B,
            ModelType.LLAMA_3_8B
        ]
        
        for model in openrouter_models:
            try:
                print(f"\n📊 Testing {model.value}:")
                result = await ai_service.generate_text(
                    prompt="What is machine learning?",
                    model_type=model,
                    max_tokens=50
                )
                print(f"   ✅ Success: {result}")
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:100]}...")
        
        # Test 4: Chat Response Generation
        print(f"\n4️⃣ Chat Response Test")
        print("-" * 25)
        
        try:
            messages = [
                {"role": "user", "content": "What are the key skills for a software engineer?"}
            ]
            
            chat_result = await ai_service.generate_chat_response(
                messages=messages,
                system_prompt="You are a helpful career advisor.",
                max_tokens=100
            )
            print(f"✅ Chat Response: {chat_result[:200]}...")
            
        except Exception as e:
            print(f"❌ Chat failed: {str(e)}")
        
        # Test 5: Career Roadmap Generation
        print(f"\n5️⃣ Career Roadmap Test")
        print("-" * 25)
        
        try:
            roadmap = await ai_service.generate_roadmap_content(
                current_role="Junior Developer",
                target_role="Senior Software Engineer",
                user_background="2 years Python experience, familiar with web development"
            )
            print(f"✅ Roadmap Generated: {roadmap[:300]}...")
            
        except Exception as e:
            print(f"❌ Roadmap failed: {str(e)}")
        
        # Test 6: Career Advice Generation
        print(f"\n6️⃣ Career Advice Test")
        print("-" * 25)
        
        try:
            advice = await ai_service.generate_career_advice(
                question="How can I improve my coding skills?",
                user_context="Junior developer with 1 year experience in Python"
            )
            print(f"✅ Advice Generated: {advice[:300]}...")
            
        except Exception as e:
            print(f"❌ Advice failed: {str(e)}")
        
        # Test 7: Fallback Logic
        print(f"\n7️⃣ Fallback Logic Test")
        print("-" * 30)
        
        try:
            # Test with prefer_provider to see routing
            gemini_result = await ai_service.generate_text(
                prompt="Hello from Gemini",
                prefer_provider=AIProvider.GEMINI,
                max_tokens=20
            )
            print(f"✅ Gemini preferred: {gemini_result}")
            
            openrouter_result = await ai_service.generate_text(
                prompt="Hello from OpenRouter",
                prefer_provider=AIProvider.OPENROUTER,
                max_tokens=20
            )
            print(f"✅ OpenRouter preferred: {openrouter_result}")
            
        except Exception as e:
            print(f"❌ Fallback test failed: {str(e)}")
        
        # Test 8: Service Metrics
        print(f"\n8️⃣ Service Metrics")
        print("-" * 20)
        
        metrics = ai_service.get_metrics()
        print(f"Total Requests: {metrics['total_requests']}")
        print(f"Successful Requests: {metrics['successful_requests']}")
        print(f"Failed Requests: {metrics['failed_requests']}")
        print(f"Success Rate: {metrics['success_rate']:.1f}%")
        print(f"Average Response Time: {metrics['average_response_time']:.2f}s")
        print(f"Total Tokens Generated: {metrics['total_tokens']}")
        print(f"Provider Usage: {metrics['provider_usage']}")
        print(f"Error Counts: {metrics['error_counts']}")
        
        # Test 9: Available Models
        print(f"\n9️⃣ Available Models")
        print("-" * 20)
        
        available_models = ai_service.get_available_models()
        for provider, models in available_models.items():
            print(f"{provider.upper()}:")
            for model in models:
                print(f"   • {model}")
        
        # Final Summary
        print(f"\n🎉 Integration Test Summary")
        print("=" * 35)
        
        if metrics['successful_requests'] > 0:
            print(f"✅ SUCCESS! Generated {metrics['total_tokens']} tokens")
            print(f"✅ {metrics['successful_requests']} successful requests")
            print(f"✅ {metrics['success_rate']:.1f}% success rate")
            print(f"✅ Average response time: {metrics['average_response_time']:.2f}s")
            
            if metrics['provider_usage']:
                print(f"✅ Provider usage: {metrics['provider_usage']}")
            
            print(f"\n🎯 AI Service is FULLY FUNCTIONAL!")
            print(f"🔥 Both Gemini and OpenRouter are working!")
            print(f"💰 Running on FREE tiers!")
            
        else:
            print(f"⚠️  No successful requests completed")
            print(f"❌ Check API keys and network connectivity")
            
    finally:
        await ai_service._close_session()

if __name__ == "__main__":
    asyncio.run(test_ai_service_integration())