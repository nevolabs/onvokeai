"""
Database connection and configuration module.
"""
import os
from supabase import create_client, Client
from app.core.initializers import get_supabase_client as get_initialized_supabase_client

# For backward compatibility, we'll provide the same interface
# but use the centralized initialization
def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance.
    Now uses the centralized initialization system.
    """
    return get_initialized_supabase_client()
