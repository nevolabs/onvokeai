import os
import re
import uuid
import json
from pathlib import Path
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Form
from supabase import create_client, Client

from config.config import load_config, set_env
from models.state_schema import SOPState 
from parsers.json_parser import parse_json
from workflow import create_workflow
from rag.jira_rag import fetch_relevant_jira_issues
from utils.create_pdf import create_pdf_from_screenshots

app = FastAPI()

# Load configuration
config = load_config()
set_env(config)

# Initialize workflow
workflow = create_workflow()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[INFO] Supabase client initialized successfully.")
except Exception as e:
    print(f"[ERROR] Failed to initialize Supabase client: {e}")
    raise RuntimeError(f"Could not initialize Supabase client: {e}")

@app.post("/generate_sop/")
async def generate_sop_api(
    user_id: str = Form(...),
    job_id: str = Form(...),
    query: str = Form(...),
    templates_id: str = Form(...),
):
    """
    API endpoint to generate SOP using a component schema defined
    in a user-specific template (from JSONB).
    """
    temp_files = []
    screenshot_info = []
    full_component_schema: Optional[dict] = None

    try:
        print(f"[DEBUG] Starting SOP generation for user_id={user_id}, job_id={job_id}, template_id='{templates_id}'")

        # --- Fetch Template Components Schema from Supabase ---
        try:
            print(f"[DEBUG] Fetching template components schema for template_id={templates_id}, user_id={user_id}")

            response = supabase.table('templates') \
                             .select('components','name') \
                             .eq('id', templates_id) \
                             .eq('user_id', user_id) \
                             .maybe_single() \
                             .execute()

            print(f"[DEBUG] Supabase template query response data: {response.data}")

            if response.data and 'components' in response.data:
                full_component_schema = response.data['components']
                category_name = response.data.get('name', 'SOP')
            else:
                print(f"[ERROR] No components found for template_id={templates_id}")
                raise HTTPException(status_code=404, detail="Template not found or no components available")

        except HTTPException as he:
            raise he
        except Exception as e:
            print(f"[ERROR] Failed to fetch template schema: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve template schema: {str(e)}")

        # --- File Processing ---
        storage = supabase.storage.from_('log_dataa')
        json_directory = f"{user_id}/{job_id}/json"
        screenshots_directory = f"{user_id}/{job_id}/screenshots"
        print(f"[DEBUG] JSON Directory: {json_directory}")
        print(f"[DEBUG] Screenshot Directory: {screenshots_directory}")

        try:
            json_files = storage.list(json_directory)
            screenshot_files = storage.list(screenshots_directory)
            print(f"[DEBUG] Found JSON files: {len(json_files) if json_files else 0}")
            print(f"[DEBUG] Found screenshot files: {len(screenshot_files) if screenshot_files else 0}")
        except Exception as e:
            print(f"[ERROR] Failed to list storage directories: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Storage paths not found: {str(e)}")

        if not json_files and not screenshot_files:
            raise HTTPException(status_code=404, detail="No JSON or screenshot files found")

        # Process screenshots
        if screenshot_files:
            for file in screenshot_files:
                file_name = file.get('name')
                if file_name and file_name.lower().endswith(('.png', '.jpg', '.jpeg')) and file_name != '.emptyFolderPlaceholder':
                    full_path = f"{screenshots_directory}/{file_name}"
                    safe_local_name = file_name.replace('/', '_').replace('\\', '_')
                    temp_path = f"temp_{user_id}_{job_id}_{safe_local_name}"
                    try:
                        print(f"[DEBUG] Downloading screenshot: {full_path}")
                        response_content = storage.download(full_path)
                        if not isinstance(response_content, bytes):
                            print(f"[ERROR] Failed download: {file_name}")
                            continue
                        with open(temp_path, "wb") as f: 
                            f.write(response_content)
                        screenshot_info.append((temp_path, file_name))
                        print(f"[DEBUG] Saved temp screenshot: {temp_path}")
                        temp_files.append(temp_path)
                    except Exception as e:
                        print(f"[ERROR] Failed processing screenshot {file_name}: {str(e)}")
                        if os.path.exists(temp_path) and temp_path not in temp_files:
                            try: 
                                os.remove(temp_path)
                            except OSError: 
                                pass
                        continue

        # Process JSON file
        json_path = None
        json_file_name_to_process = None
        if json_files:
            for file in json_files:
                file_name = file.get('name')
                if file_name and file_name.lower().endswith('.json') and file_name != '.emptyFolderPlaceholder':
                    json_path = f"{json_directory}/{file_name}"
                    json_file_name_to_process = file_name
                    print(f"[DEBUG] JSON file selected: {json_path}")
                    break

        if not screenshot_info: 
            raise HTTPException(status_code=404, detail="No valid screenshot files found")
        if not json_path: 
            raise HTTPException(status_code=404, detail="No JSON file found in storage")

        # Create PDF
        pdf_temp_path = f"temp_{user_id}_{job_id}_generated.pdf"
        try:
            print(f"[DEBUG] Creating PDF: {pdf_temp_path}")
            if not screenshot_info: 
                raise ValueError("No screenshots for PDF")
            create_pdf_from_screenshots(screenshot_info, pdf_temp_path)
            temp_files.append(pdf_temp_path)
            print(f"[DEBUG] PDF created")
        except Exception as e:
            print(f"[ERROR] Failed to create PDF: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create PDF: {str(e)}")

        # Process JSON data
        try:
            safe_json_filename = re.sub(r'[^\w\-_.]', '_', json_file_name_to_process)
            short_json_filename = safe_json_filename[:50] + Path(safe_json_filename).suffix
            json_temp_path = f"temp_{user_id}_{job_id}_{short_json_filename}"
            
            print(f"[DEBUG] Downloading event JSON: {json_path}")
            json_response = storage.download(json_path)
            if not isinstance(json_response, bytes):
                print(f"[ERROR] Failed download event JSON: {json_file_name_to_process}")
                raise HTTPException(status_code=500, detail="Failed to download event JSON data")
            with open(json_temp_path, "wb") as f: 
                f.write(json_response)
            temp_files.append(json_temp_path)
            print(f"[DEBUG] Saved temp event JSON: {json_temp_path}")
            event_data = await parse_json(json_temp_path)
            print(f"[DEBUG] Parsed event data type: {type(event_data)}")
            if not event_data: 
                raise HTTPException(status_code=400, detail="No valid event data parsed")
            if isinstance(event_data, list) and event_data and isinstance(event_data[0], dict) and "error" in event_data[0]:
                raise Exception(f"Event JSON parsing error: {event_data[0]['error']}")
        except HTTPException as he: 
            raise he
        except Exception as e:
            print(f"[ERROR] Event JSON processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Event JSON processing failed: {str(e)}")

        # --- Fetch Jira Context ---
        jira_context = "Jira context unavailable."
        try:
            print(f"[DEBUG] Fetching Jira issues for query: {query}")
            relevant_issues = fetch_relevant_jira_issues(user_id, query, top_k=5)
            if relevant_issues:
                jira_context = "\n".join([
                    f"Issue: {issue.get('issue_id', 'N/A')}\nDetails: {issue.get('text_data', 'N/A')}" 
                    for issue in relevant_issues
                ])
            else: 
                jira_context = "No relevant Jira issues found."
            print(f"[DEBUG] Fetched Jira context")
        except Exception as e:
            print(f"[WARNING] Error fetching Jira issues: {str(e)}")
            jira_context = f"Error fetching Jira issues: {str(e)}"

        # --- Prepare and Invoke Workflow ---
        knowledge_base = f"### Jira Issues:\n{jira_context}"
        print(f"[DEBUG] Prepared knowledge base")

        result = None
        try:
            print(f"[DEBUG] Invoking workflow with component schema...")
            initial_state = SOPState(
                KB=knowledge_base,
                file_path=pdf_temp_path,
                user_id=user_id,
                job_id=job_id,
                event_data=event_data,
                user_query=query,
                components=full_component_schema,
                category_name=category_name
            )
            result = await workflow.ainvoke(initial_state)
            print(f"[DEBUG] SOP workflow completed")
            print(f"[DEBUG] SOP result type: {type(result)}")

        except Exception as e:
            print(f"[ERROR] SOP workflow failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"SOP generation workflow failed: {str(e)}")

        # --- Return Success Response ---
        return {
            "status": "success",
            "result": result,
            "metadata": {
                "user_id": user_id,
                "job_id": job_id,
                "template_id": templates_id,
                "files_processed": len(screenshot_info) + 1,
                "components_schema_used": full_component_schema
            }
        }

    except HTTPException as he:
        print(f"[HTTP ERROR] Status: {he.status_code}, Detail: {he.detail}")
        raise he
    except Exception as e:
        print(f"[FATAL ERROR] Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        # --- Cleanup Temporary Files ---
        print(f"[DEBUG] Cleaning up {len(temp_files)} temporary files...")
        cleaned_count = 0
        for temp_file in temp_files:
            try:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
                    cleaned_count += 1
            except Exception as e:
                print(f"[WARNING] Temp file cleanup failed for {temp_file}: {str(e)}")
        print(f"[DEBUG] Cleanup finished. Removed {cleaned_count} files.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)