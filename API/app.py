import os
from fastapi import FastAPI, HTTPException, Form
from config.config import load_config, set_env
from models.tech_article_models import SOPState
from parsers.json_parser import parse_json
from workflow import create_workflow
from rag.jira_rag import fetch_relevant_jira_issues
from supabase import create_client
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
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/generate_sop/")
async def generate_sop_api(
    user_id: str = Form(...),
    job_id: str = Form(...),
    query: str = Form(...),
    
):
    """API endpoint to generate SOP from stored screenshots and JSON file"""
    temp_files = []
    storage_files_to_delete = []
    screenshot_info = []  # List of (temp_path, original_name) tuples
    component_list = ["title", "introduction","table_of_contents"]
    

    try:
        print(f"[DEBUG] Starting SOP generation for user_id={user_id}, job_id={job_id}, query='{query}'")

        # Initialize Supabase storage client
        storage = supabase.storage.from_('log_dataa')

        # Step 1: Prepare paths
        json_directory = f"{user_id}/{job_id}/json"
        screenshots_directory = f"{user_id}/{job_id}/screenshots"
        print(f"[DEBUG] JSON Directory: {json_directory}")
        print(f"[DEBUG] Screenshot Directory: {screenshots_directory}")

        # Step 2: List files
        try:
            json_files = storage.list(json_directory)
            screenshot_files = storage.list(screenshots_directory)
            print(f"[DEBUG] Found JSON files: {json_files}")
            print(f"[DEBUG] Found screenshot files: {screenshot_files}")
        except Exception as e:
            print(f"[ERROR] Failed to list storage directories: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Storage paths not found: {str(e)}")

        if not json_files and not screenshot_files:
            raise HTTPException(status_code=404, detail="No files found for this user/job combination")

        # Step 3: Process screenshots
        if screenshot_files:
            for file in screenshot_files:
                file_name = file.get('name')
                if file_name and file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    full_path = f"{screenshots_directory}/{file_name}"
                    temp_path = f"temp_{user_id}_{file_name}"
                    try:
                        print(f"[DEBUG] Downloading screenshot from: {full_path}")
                        response = storage.download(full_path)
                        with open(temp_path, "wb") as f:
                            f.write(response)
                        screenshot_info.append((temp_path, file_name))  # Store both path and name
                        storage_files_to_delete.append(full_path)
                        print(f"[DEBUG] Saved screenshot to: {temp_path}")
                    except Exception as e:
                        print(f"[ERROR] Failed to process screenshot {file_name}: {str(e)}")
                        continue

        # Step 4: Process JSON file
        json_path = None
        if json_files:
            for file in json_files:
                file_name = file.get('name')
                if file_name and file_name.lower().endswith('.json'):
                    json_path = f"{json_directory}/{file_name}"
                    storage_files_to_delete.append(json_path)
                    print(f"[DEBUG] JSON file selected: {json_path}")
                    break

        if not screenshot_info:
            raise HTTPException(status_code=404, detail="No valid screenshot files found")
        if not json_path:
            raise HTTPException(status_code=404, detail="No JSON file found in storage")

        # Step 5: Create PDF with original names
        pdf_temp_path = f"temp_{user_id}_generated.pdf"
        try:
            print(f"[DEBUG] Creating PDF at: {pdf_temp_path}")
            create_pdf_from_screenshots(screenshot_info, pdf_temp_path)
            temp_files.append(pdf_temp_path)
            print(f"[DEBUG] PDF created successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to create PDF: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create PDF: {str(e)}")

        # [Rest of the code remains the same until cleanup]
        # Step 6: Download and parse JSON
        json_temp_path = f"temp_{user_id}_sop.json"
        try:
            print(f"[DEBUG] Downloading JSON from: {json_path}")
            json_response = storage.download(json_path)
            with open(json_temp_path, "wb") as f:
                f.write(json_response)
            temp_files.append(json_temp_path)
            print(f"[DEBUG] JSON saved to: {json_temp_path}")

            event_data = await parse_json(json_temp_path)
            print(f"[DEBUG] Parsed event data: {event_data}")

            if not event_data:
                raise HTTPException(status_code=400, detail="No valid event data in JSON file")
            if isinstance(event_data, list) and "error" in event_data[0]:
                raise Exception(event_data[0]["error"])
        except Exception as e:
            print(f"[ERROR] JSON processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"JSON processing failed: {str(e)}")

        # Step 7: Fetch Jira context
        try:
            print(f"[DEBUG] Fetching relevant Jira issues for query: {query}")
            relevant_issues = fetch_relevant_jira_issues(user_id, query, top_k=5)
            jira_context = "\n".join(
                [f"Issue: {issue['issue_id']}\nDetails: {issue['text_data']}" 
                 for issue in relevant_issues]
            ) if relevant_issues else "No relevant Jira issues found."
            print(f"[DEBUG] Fetched Jira context:\n{jira_context}")
        except Exception as e:
            print(f"[WARNING] Error fetching Jira issues: {str(e)}")
            jira_context = f"Error fetching Jira issues: {str(e)}"

        # Step 8: Prepare knowledge base
        knowledge_base = f"""
        ### Jira Issues:
        {jira_context}
        """
        print(f"[DEBUG] Prepared knowledge base.")

        # Step 9: Generate SOP
        try:
            print(f"[DEBUG] Invoking workflow to generate SOP")
            initial_state = SOPState(
                KB=knowledge_base,
                file_path=pdf_temp_path,
                user_id=user_id,
                job_id=job_id,
                event_data=event_data,
                user_query=query,
                components=component_list
            )
            result = await workflow.ainvoke(initial_state)
            print(f"[DEBUG] SOP generation result: {result}")
        except Exception as e:
            print(f"[ERROR] SOP generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"SOP generation failed: {str(e)}")

        # Step 10: Cleanup storage (optional)
        try:
            if storage_files_to_delete:
                print(f"[DEBUG] Cleaning up {len(storage_files_to_delete)} storage files (commented out)")
                # storage.remove(storage_files_to_delete)
        except Exception as e:
            print(f"[WARNING] Storage cleanup failed: {str(e)}")

        return {
            "status": "success",
            "result": result,
            "metadata": {
                "user_id": user_id,
                "job_id": job_id,
                "files_processed": len(screenshot_info) + 1  # +1 for JSON
            }
        }

    except HTTPException as he:
        print(f"[HTTP ERROR] {he.detail}")
        raise he
    except Exception as e:
        print(f"[FATAL ERROR] Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Cleanup temp files
        print(f"[DEBUG] Cleaning up temp files...")
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"[DEBUG] Removed temp file: {temp_file}")
            except Exception as e:
                print(f"[WARNING] Temp file cleanup failed for {temp_file}: {str(e)}")
        for temp_path, _ in screenshot_info:  # Only remove temp_path, not original_name
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"[DEBUG] Removed temp file: {temp_path}")
            except Exception as e:
                print(f"[WARNING] Temp file cleanup failed for {temp_path}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)