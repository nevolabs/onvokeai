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
embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# ✅ Confluence API Constants
CONFLUENCE_TOKEN_URL = "https://auth.atlassian.com/oauth/token"

def get_confluence_tokens(user_id: str):
    """
    Retrieve Confluence OAuth tokens from Supabase.
    """
    response = supabase.table("user_integrations").select(
        "access_token, refresh_token, expires_at"
    ).eq("user_id", user_id).eq("integration_type", "confluence").execute()

    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Confluence tokens not found for user")

    token_data = response.data[0]

    # Check if token is expired
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        token_data["access_token"] = refresh_confluence_token(token_data["refresh_token"], user_id)

    return token_data["access_token"]

def refresh_confluence_token(refresh_token: str, user_id: str):
    """
    Refresh expired Confluence OAuth token and update in Supabase.
    """
    payload = {
        "grant_type": "refresh_token",
        "client_id": os.getenv("CONFLUENCE_CLIENT_ID"),  # Use Confluence client ID
        "client_secret": os.getenv("CONFLUENCE_CLIENT_SECRET"),  # Use Confluence client secret
        "refresh_token": refresh_token
    }

    response = requests.post(CONFLUENCE_TOKEN_URL, json=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Failed to refresh Confluence token")

    new_token_data = response.json()

    # ✅ Update Supabase with new tokens
    supabase.table("user_integrations").update({
        "access_token": new_token_data["access_token"],
        "expires_at": (datetime.now(timezone.utc) + 
                      timedelta(seconds=new_token_data["expires_in"])).isoformat()
    }).eq("user_id", user_id).eq("integration_type", "confluence").execute()

    return new_token_data["access_token"]

def fetch_confluence_pages(user_id: str):
    """
    Fetch Confluence pages dynamically using the user's stored access token.
    """
    access_token = get_confluence_tokens(user_id)

    # ✅ Fetch Cloud ID first
    cloud_id_response = requests.get(
        "https://api.atlassian.com/oauth/token/accessible-resources",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    )

    if cloud_id_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Confluence Cloud ID")

    cloud_id = cloud_id_response.json()[0]["id"]  # Assuming one Confluence Cloud instance

    # ✅ Fetch Confluence pages
    confluence_url = f"https://api.atlassian.com/ex/confluence/{cloud_id}/rest/api/content?type=page&expand=body.storage"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    pages_response = requests.get(confluence_url, headers=headers)

    if pages_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Confluence pages")

    return pages_response.json()["results"]

def get_free_embedding(text: str):
    """
    Generate embeddings using the Hugging Face sentence transformer model.
    """
    return embedding_model.encode(text).tolist()  # Convert to list for storage

@app.post("/rag/ingest")
async def ingest_confluence_pages(user_id: str):
    """
    Fetch Confluence pages, generate embeddings using Hugging Face, and store in Supabase.
    """
    try:
        # ✅ Fetch Confluence pages dynamically
        confluence_data = fetch_confluence_pages(user_id)

        # ✅ Convert Confluence pages to text format
        for page in confluence_data:
            page_text = f"Page ID: {page['id']}, Title: {page['title']}, Body: {page['body']['storage']['value']}"
            embedding_vector = get_free_embedding(page_text)

            # ✅ Insert embedding into Supabase
            response = supabase.table("rag_confluence_embeddings").insert({
                "user_id": user_id,
                "integration_type": "confluence",
                "page_id": page["id"],
                "embedding": embedding_vector,
                "text_data": page_text
            }).execute()

            if "error" in response and response["error"]:
                raise HTTPException(status_code=500, detail=f"Failed to insert into Supabase: {response['error']}")

        return {"message": f"Confluence pages ingested successfully for user {user_id}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)