"""
Integration Tests for Supabase & OpenAI
Tests that user input is stored in Supabase and AI responses are saved
"""

import os
import json
import uuid
from dotenv import load_dotenv
from database.service import log_chat_to_db, get_session_history, verify_database_connection
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

client = OpenAI(api_key=openai_key)

def test_database_connection():
    """Test 1: Verify Supabase connection is working"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    try:
        success = verify_database_connection()
        if success:
            print("✓ PASSED: Database connection successful")
            return True
        else:
            print("✗ FAILED: Database connection could not be verified")
            return False
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_openai_api():
    """Test 2: Verify OpenAI API is working"""
    print("\n" + "="*60)
    print("TEST 2: OpenAI API Connection")
    print("="*60)
    try:
        print("Making test request to OpenAI...")
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello from integration test' and nothing else"}]
        )
        
        response = completion.choices[0].message.content
        tokens = completion.usage.total_tokens
        
        print(f"✓ Response received: {response}")
        print(f"✓ Tokens used: {tokens}")
        print("✓ PASSED: OpenAI API connection successful")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_save_single_message():
    """Test 3: Save a single message to database"""
    print("\n" + "="*60)
    print("TEST 3: Save Single Message to Database")
    print("="*60)
    
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    try:
        # Create test data
        test_prompt = "What is 2+2?"
        print(f"Test prompt: {test_prompt}")
        
        # Get response from OpenAI
        print("Getting OpenAI response...")
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": test_prompt}]
        )
        
        ai_response = completion.choices[0].message.content
        tokens = completion.usage.total_tokens
        metadata = completion.model_dump()
        
        print(f"AI Response: {ai_response}")
        print(f"Tokens: {tokens}")
        
        # Save to database
        print("Saving to database...")
        result = log_chat_to_db(
            user_prompt=test_prompt,
            ai_response=ai_response,
            tokens=tokens,
            session_id=session_id,
            metadata=metadata
        )
        
        print("✓ PASSED: Message saved successfully")
        return True, session_id
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False, None


def test_retrieve_messages(session_id):
    """Test 4: Retrieve messages from database"""
    print("\n" + "="*60)
    print("TEST 4: Retrieve Messages from Database")
    print("="*60)
    
    if not session_id:
        print("✗ FAILED: No session ID provided (previous test failed)")
        return False
    
    try:
        print(f"Retrieving messages for session: {session_id}")
        messages = get_session_history(session_id)
        
        if not messages:
            print("✗ FAILED: No messages found")
            return False
        
        print(f"✓ Retrieved {len(messages)} message(s):")
        for i, msg in enumerate(messages, 1):
            print(f"\n  Message {i}:")
            print(f"    User Prompt: {msg.get('prompt', 'N/A')[:100]}")
            print(f"    AI Response: {msg.get('response', 'N/A')[:100]}")
            print(f"    Tokens Used: {msg.get('tokens_used', 'N/A')}")
            print(f"    Created At: {msg.get('created_at', 'N/A')}")
        
        print("\n✓ PASSED: Messages retrieved successfully")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_conversation_flow():
    """Test 5: Full conversation flow (simulate user interaction)"""
    print("\n" + "="*60)
    print("TEST 5: Full Conversation Flow")
    print("="*60)
    
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    test_prompts = [
        "Tell me a short joke",
        "What's the capital of France?",
        "Explain quantum computing in one sentence"
    ]
    
    try:
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n  Message {i}: {prompt}")
            
            # Get response
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            response = completion.choices[0].message.content
            tokens = completion.usage.total_tokens
            
            print(f"    Response: {response[:80]}...")
            print(f"    Tokens: {tokens}")
            
            # Save to database
            log_chat_to_db(
                user_prompt=prompt,
                ai_response=response,
                tokens=tokens,
                session_id=session_id,
                metadata=completion.model_dump()
            )
        
        # Retrieve all messages
        print(f"\n  Retrieving all {len(test_prompts)} messages from session...")
        messages = get_session_history(session_id)
        
        if len(messages) == len(test_prompts):
            print(f"✓ PASSED: All {len(test_prompts)} messages stored and retrieved successfully")
            return True
        else:
            print(f"✗ FAILED: Expected {len(test_prompts)} messages, got {len(messages)}")
            return False
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def run_all_tests():
    """Run all integration tests"""
    print("\n\n")
    print("█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  SUPABASE & OPENAI INTEGRATION TESTS".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)
    
    results = {
        "test_1_db_connection": test_database_connection(),
        "test_2_openai_api": test_openai_api(),
    }
    
    # Test 3 returns tuple
    test3_result, session_id = test_save_single_message()
    results["test_3_save_single"] = test3_result
    
    # Test 4 uses session_id from test 3
    results["test_4_retrieve"] = test_retrieve_messages(session_id)
    
    # Test 5 - full flow
    results["test_5_conversation"] = test_conversation_flow()
    
    # Summary
    print("\n\n")
    print("█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  TEST SUMMARY".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print("█" * 60)
    print(f"\nTotal: {passed}/{total} tests passed\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your integration is working correctly!\n")
        return True
    else:
        print("⚠ Some tests failed. Please review the output above.\n")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        exit(1)
