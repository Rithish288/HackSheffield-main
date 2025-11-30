"""
Quick Supabase Connection Test (without OpenAI)
Use this to quickly verify your database setup before running full integration tests
"""

import os
from dotenv import load_dotenv
from database.service import verify_database_connection, log_chat_to_db, get_session_history
import uuid

load_dotenv()

def quick_test():
    print("\n" + "="*60)
    print("QUICK SUPABASE CONNECTION TEST")
    print("="*60)
    
    # Test 1: Connection
    print("\n1️⃣  Testing database connection...")
    try:
        if verify_database_connection():
            print("   ✓ Connection successful!\n")
        else:
            print("   ✗ Connection failed!\n")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False
    
    # Test 2: Save test data
    print("2️⃣  Saving test message to database...")
    session_id = str(uuid.uuid4())
    try:
        log_chat_to_db(
            user_prompt="This is a test message",
            ai_response="This is a test response",
            tokens=10,
            session_id=session_id,
            metadata={"test": True}
        )
        print("   ✓ Message saved!\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False
    
    # Test 3: Retrieve data
    print("3️⃣  Retrieving test message from database...")
    try:
        messages = get_session_history(session_id)
        if messages:
            print(f"   ✓ Retrieved {len(messages)} message(s)!")
            for msg in messages:
                print(f"      - Prompt: {msg.get('prompt')}")
                print(f"      - Response: {msg.get('response')}")
                print(f"      - Created: {msg.get('created_at')}")
            print()
            return True
        else:
            print("   ✗ No messages found\n")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False

if __name__ == "__main__":
    print("\n🚀 Starting Supabase connection test...\n")
    
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
        success = quick_test()
        if success:
            print("="*60)
            print("✅ ALL TESTS PASSED - Ready for integration!")
            print("="*60 + "\n")
        else:
            print("="*60)
            print("❌ TESTS FAILED - Check your configuration")
            print("="*60 + "\n")
    else:
        print("❌ ERROR: Missing Supabase credentials in .env file")
        print("   Please configure SUPABASE_URL and SUPABASE_KEY\n")
