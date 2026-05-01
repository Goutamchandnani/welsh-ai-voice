"""
scripts/generate_key.py

Phase A — API Key Generator

This script generates a secure, random API key and stores its SHA-256 hash 
in Supabase. We NEVER store the raw key in the database — this prevents 
attackers (or even us) from stealing active keys if the database is breached.

Usage:
    python3 scripts/generate_key.py --email user@example.com --tier free --env live
"""

import os
import sys
import argparse
import secrets
import hashlib
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing from .env")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_key(email: str, tier: str, environment: str):
    """
    Generates a new API key, hashes it, and stores it in Supabase.
    """
    # 1. Determine prefix
    prefix = f"lc_{environment}_"  # e.g., 'lc_live_' or 'lc_test_'
    
    # 2. Generate random 32-byte token (secure against brute-force)
    random_part = secrets.token_urlsafe(32)
    
    # 3. Create the final raw key (what the user sees)
    raw_key = f"{prefix}{random_part}"
    
    # 4. Hash the entire key using SHA-256
    # We store the hash so we can verify incoming keys without storing them
    key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    
    # 5. Save to Supabase
    try:
        response = supabase.table("api_keys").insert({
            "key_hash": key_hash,
            "prefix": prefix,
            "user_email": email,
            "status": "active",
            "tier": tier
        }).execute()
        
        print("\n✅ API Key generated successfully!")
        print("-" * 50)
        print(f"User:  {email}")
        print(f"Tier:  {tier}")
        print(f"Env:   {environment}")
        print("-" * 50)
        print("🔑 YOUR RAW API KEY (COPY THIS NOW):")
        print(raw_key)
        print("-" * 50)
        print("⚠️  Warning: This key is only shown once. We do not store it.")
        
    except Exception as e:
        print(f"\n❌ Error saving to Supabase: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Llais Cymraeg API Key")
    parser.add_argument("--email", required=True, help="Email of the user")
    parser.add_argument("--tier", choices=["free", "pro"], default="free", help="Billing tier")
    parser.add_argument("--env", choices=["live", "test"], default="live", help="Environment (live or test)")
    
    args = parser.parse_args()
    generate_key(args.email, args.tier, args.env)
