import os
import json
import requests
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException
from supabase import create_client
from sentence_transformers import SentenceTransformer

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ✅ Supabase Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials are missing")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()

# ✅ Load Free Hugging Face Embedding Model
embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")  # 🔹 Change this model

# ✅ Jira API Constants
JIRA_TOKEN_URL = "https://auth.atlassian.com/oauth/token"

def get_jira_tokens(user_id: str):
    """
    Retrieve Jira OAuth tokens from Supabase.
    """
    response = supabase.table("user_integrations").select(
        "access_token, refresh_token, expires_at"
    ).eq("user_id", user_id).eq("integration_type", "jira").execute()

    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Jira tokens not found for user")

    token_data = response.data[0]

    # Check if token is expired
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        token_data["access_token"] = refresh_jira_token(token_data["refresh_token"], user_id)

    return token_data["access_token"]

def refresh_jira_token(refresh_token: str, user_id: str):
    """
    Refresh expired Jira OAuth token and update in Supabase.
    """
    payload = {
        "grant_type": "refresh_token",
        "client_id": os.getenv("JIRA_CLIENT_ID"),
        "client_secret": os.getenv("JIRA_CLIENT_SECRET"),
        "refresh_token": refresh_token
    }

    response = requests.post(JIRA_TOKEN_URL, json=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Failed to refresh Jira token")

    new_token_data = response.json()

    # ✅ Update Supabase with new tokens
    supabase.table("user_integrations").update({
        "access_token": new_token_data["access_token"],
        "expires_at": (datetime.now(timezone.utc) + 
                      timedelta(seconds=new_token_data["expires_in"])).isoformat()
    }).eq("user_id", user_id).eq("integration_type", "jira").execute()

    return new_token_data["access_token"]

def fetch_jira_issues(user_id: str):
    """
    Fetch Jira issues dynamically using the user's stored access token.
    """
    access_token = get_jira_tokens(user_id)

    # ✅ Fetch Cloud ID first
    cloud_id_response = requests.get(
        "https://api.atlassian.com/oauth/token/accessible-resources",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    )

    if cloud_id_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Jira Cloud ID")

    cloud_id = cloud_id_response.json()[0]["id"]  # Assuming one Jira Cloud instance

    # ✅ Fetch Jira issues
    jira_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search?expand=names,schema"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    issues_response = requests.get(jira_url, headers=headers)

    if issues_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Jira issues")

    return issues_response.json()["issues"]

def get_free_embedding(text: str):
    """
    Generate embeddings using the Hugging Face sentence transformer model.
    """
    return embedding_model.encode(text).tolist()  # Convert to list for storage


@app.post("/rag/ingest")
async def ingest_jira_issues(user_id: str):
    """
    Fetch Jira issues, generate embeddings using Hugging Face, and store in Supabase.
    """
    try:
        # ✅ Fetch Jira issues dynamically
        jira_data = fetch_jira_issues(user_id)

        # ✅ Convert Jira issues to text format
        for issue in jira_data:
            issue_text = f"Issue ID: {issue['key']}, Summary: {issue['fields']['summary']}, Description: {issue['fields'].get('description', 'No description')}"
            embedding_vector = get_free_embedding(issue_text)

            # ✅ Insert embedding into Supabase
            response = supabase.table("rag_jira_embeddings").insert({
                "user_id": user_id,
                "integration_type": "jira",
                "issue_id": issue["key"],
                "embedding": embedding_vector,
                "text_data": issue_text
            }).execute()

            if "error" in response and response["error"]:
                raise HTTPException(status_code=500, detail=f"Failed to insert into Supabase: {response['error']}")


        return {"message": f"Jira issues ingested successfully for user {user_id}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)