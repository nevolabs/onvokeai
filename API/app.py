import os
from fastapi import FastAPI, HTTPException, Form
from config.config import load_config, set_env
from models.tech_article_models import SOPState
from parsers.json_parser import  parse_json
from workflow import create_workflow
from rag.jira_rag import fetch_relevant_jira_issues
from supabase import create_client
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image

app = FastAPI()

# ✅ Load configuration
config = load_config()
set_env(config)

# ✅ Initialize workflow
workflow = create_workflow()

# ✅ Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_pdf_from_screenshots(screenshot_paths: List[str], output_path: str):
    """Convert an array of screenshot images into a single PDF."""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    for screenshot_path in screenshot_paths:
        img = Image.open(screenshot_path)
        img_width, img_height = img.size
        
        scale = min(width/img_width, height/img_height)
        scaled_width = img_width * scale
        scaled_height = img_height * scale
        
        x = (width - scaled_width) / 2
        y = (height - scaled_height) / 2
        
        c.drawImage(screenshot_path, x, y, scaled_width, scaled_height)
        c.showPage()
    
    c.save()
    
    
@app.post("/generate_sop/")
async def generate_sop_api(
    user_id: str = Form(...),
    job_id: str = Form(...),
    query: str = Form(...),
):
    """API endpoint to generate SOP from stored screenshots and JSON file"""
    temp_files = []
    storage_files_to_delete = []
    screenshot_temp_paths = []
    
    try:
        # Initialize Supabase storage client
        storage = supabase.storage.from_('log_dataa')  # Note: consistent bucket name
        
        # Step 1: Verify and prepare paths
        json_directory = f"{user_id}/{job_id}/json"
        screenshots_directory = f"{user_id}/{job_id}/screenshots"
        
        # Step 2: Check if directories exist
        try:
            json_files = storage.list(json_directory)
            screenshot_files = storage.list(screenshots_directory)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Storage paths not found: {str(e)}"
            )

        if not json_files and not screenshot_files:
            raise HTTPException(
                status_code=404,
                detail="No files found for this user/job combination"
            )

        # Step 3: Process screenshots
        if screenshot_files:
            for file in screenshot_files:
                if file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    full_path = f"{screenshots_directory}/{file.name}"
                    temp_path = f"temp_{user_id}_{file.name}"
                    
                    try:
                        # Download screenshot
                        response = storage.download(full_path)
                        with open(temp_path, "wb") as f:
                            f.write(response)
                        screenshot_temp_paths.append(temp_path)
                        storage_files_to_delete.append(full_path)
                    except Exception as e:
                        print(f"Failed to process {file.name}: {str(e)}")
                        continue

        # Step 4: Process JSON file
        json_path = None
        if json_files:
            for file in json_files:
                if file.name.lower().endswith('.json'):
                    json_path = f"{json_directory}/{file.name}"
                    storage_files_to_delete.append(json_path)
                    break

        if not screenshot_temp_paths:
            raise HTTPException(
                status_code=404,
                detail="No valid screenshot files found"
            )
        if not json_path:
            raise HTTPException(
                status_code=404,
                detail="No JSON file found in storage"
            )

        # Step 5: Create PDF from screenshots
        pdf_temp_path = f"temp_{user_id}_generated.pdf"
        try:
            create_pdf_from_screenshots(screenshot_temp_paths, pdf_temp_path)
            temp_files.append(pdf_temp_path)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create PDF: {str(e)}"
            )

        # Step 6: Download and parse JSON
        json_temp_path = f"temp_{user_id}_sop.json"
        try:
            json_response = storage.download(json_path)
            with open(json_temp_path, "wb") as f:
                f.write(json_response)
            temp_files.append(json_temp_path)
            
            event_data = await parse_json(json_temp_path)
            if not event_data:
                raise HTTPException(
                    status_code=400,
                    detail="No valid event data in JSON file"
                )
            if isinstance(event_data, list) and "error" in event_data[0]:
                raise Exception(event_data[0]["error"])
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"JSON processing failed: {str(e)}"
            )

        # Step 7: Fetch Jira context
        try:
            relevant_issues = fetch_relevant_jira_issues(user_id, query, top_k=5)
            jira_context = "\n".join(
                [f"Issue: {issue['issue_id']}\nDetails: {issue['text_data']}" 
                 for issue in relevant_issues]
            ) if relevant_issues else "No relevant Jira issues found."
        except Exception as e:
            jira_context = f"Error fetching Jira issues: {str(e)}"

        # Step 8: Prepare knowledge base
        knowledge_base = f"""
        ### Jira Issues:
        {jira_context}
        """

        # Step 9: Generate SOP
        try:
            initial_state = SOPState(
                KB=knowledge_base,
                file_path=pdf_temp_path,
                user_id=user_id,
                job_id=job_id,
                event_data=event_data,
                user_query=query
            )
            result = await workflow.ainvoke(initial_state)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"SOP generation failed: {str(e)}"
            )

        # Step 10: Cleanup (only if everything succeeded)
        try:
            if storage_files_to_delete:
                pass
                # storage.remove(storage_files_to_delete)
        except Exception as e:
            print(f"Warning: Storage cleanup failed: {str(e)}")

        return {
            "status": "success",
            "result": result,
            "metadata": {
                "user_id": user_id,
                "job_id": job_id,
                "files_processed": len(screenshot_temp_paths) + 1  # +1 for JSON
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
    finally:
        # Always clean up temp files
        for temp_file in temp_files + screenshot_temp_paths:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Temp file cleanup failed for {temp_file}: {str(e)}")