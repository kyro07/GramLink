# database/supabase_client.py
# This file creates the connection to Supabase database

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("https://ejfpslmafznkhtfbdvjd.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVqZnBzbG1hZnpua2h0ZmJkdmpkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDk1MTY0MSwiZXhwIjoyMDkwNTI3NjQxfQ.xuYmzmdHyukQo59zucLfJjc7NvxRlnJgZ0B47vA17c8")  # Use service key for backend

# Create Supabase client (this is like "connecting to database")
supabase: Client = create_client("https://ejfpslmafznkhtfbdvjd.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVqZnBzbG1hZnpua2h0ZmJkdmpkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDk1MTY0MSwiZXhwIjoyMDkwNTI3NjQxfQ.xuYmzmdHyukQo59zucLfJjc7NvxRlnJgZ0B47vA17c8")

def get_supabase() -> Client:
    """Returns the Supabase client instance"""
    return supabase

