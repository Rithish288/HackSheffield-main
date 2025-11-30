import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

# 2. Fetch the secrets
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# 3. Check if they exist (Good for debugging)
if not url or not key:
    print("⚠️  Warning: Supabase credentials not found in .env file")
    print("   Set SUPABASE_URL and SUPABASE_KEY to enable database features")
    supabase = None
else:
    try:
        # 4. Create the connection "object"
        supabase: Client = create_client(url, key)
    except Exception as e:
        print(f"⚠️  Warning: Failed to connect to Supabase: {e}")
        supabase = None