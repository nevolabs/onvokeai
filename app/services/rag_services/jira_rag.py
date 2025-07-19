import os
from supabase import create_client
from dotenv import load_dotenv
from app.core.initializers import get_supabase_client, generate_embeddings
from app.config.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Load environment variables (still needed for other configs)
load_dotenv()

# Use centralized services
supabase = get_supabase_client()

def get_free_embedding(text: str):
    """
    Generate embeddings using Gemini embedding model.
    """
    return generate_embeddings(text)

def fetch_relevant_jira_issues(user_id: str, query: str, top_k: int = 2):
    """
    Fetch relevant Jira issues for a user by first filtering on `user_id`,
    then performing a vector similarity search on the `embedding` column.

    Args:
        user_id (str): The user's unique ID.
        query (str): The search query to find similar Jira issues.
        top_k (int): Number of relevant results to fetch.

    Returns:
        list: List of relevant Jira issues with their `issue_id`, `text_data`, and score.
    """
    try:
        # ✅ Generate embedding for the query (NOT stored in Supabase)
        query_embedding = get_free_embedding(query)

        # ✅ Run vector similarity search in Supabase
        response = supabase.rpc("match_jira_vectors", {
            "query_embedding": query_embedding,  # ✅ Used in SQL function, NOT a table column
            "user_id": user_id,
            "top_k": top_k
        }).execute()

        # ✅ Check for errors
        if not response.data:
            raise Exception("No matching Jira issues found.")

        # ✅ Extract relevant results
        relevant_issues = [
            {
                "issue_id": row["issue_id"],  
                "text_data": row["text_data"],  
                "score": row["score"]  # ✅ Higher means more relevant
            }
            for row in response.data
        ]

        return relevant_issues

    except Exception as e:
        logger.error(f"Error fetching JIRA issues: {str(e)}")
        return []
