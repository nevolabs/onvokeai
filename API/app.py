import os
from fastapi import FastAPI, HTTPException, Form
from config import load_config, set_env
from models import SOPState
from parsers import parse_pdf, parse_json
from workflow import create_workflow
from rag_fetch import fetch_relevant_jira_issues
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
    query: str = Form(...),
):
    """API endpoint to generate SOP from stored screenshots and JSON file, then delete them."""
    temp_files = []
    storage_files_to_delete = []
    screenshot_temp_paths = []
    
    try:
        # Step 1: Fetch file list from user's directory in Supabase storage
        json_directory = f"{user_id}/json"
        screenshots_directory = f"{user_id}/screenshots"
        
        # List files in both directories
        json_files = supabase.storage.from_('log_data').list(json_directory)
        screenshot_files = supabase.storage.from_('log_data').list(screenshots_directory)
        
        if not json_files and not screenshot_files:
            raise HTTPException(status_code=404, detail="No files found for user")

        # Step 2: Process screenshots
        if screenshot_files:
            for file in screenshot_files:
                if file['name'].lower().endswith(('.png', '.jpg', '.jpeg')):
                    full_path = f"{screenshots_directory}/{file['name']}"
                    temp_path = f"temp_{user_id}_{file['name']}"
                    
                    # Download screenshot
                    response = supabase.storage.from_('log_data').download(full_path)
                    with open(temp_path, "wb") as f:
                        f.write(response)
                    
                    screenshot_temp_paths.append(temp_path)
                    storage_files_to_delete.append(full_path)

        # Step 3: Process JSON file
        json_path = None
        if json_files:
            for file in json_files:
                if file['name'].lower().endswith('.json'):
                    json_path = f"{json_directory}/{file['name']}"
                    storage_files_to_delete.append(json_path)
                    break  # Assuming there's only one JSON file

        if not screenshot_temp_paths:
            raise HTTPException(status_code=404, detail="No screenshot files found in storage")
        if not json_path:
            raise HTTPException(status_code=404, detail="No JSON file found in storage")

        # Step 4: Create PDF from screenshots
        pdf_temp_path = f"temp_{user_id}_generated.pdf"
        create_pdf_from_screenshots(screenshot_temp_paths, pdf_temp_path)
        temp_files.append(pdf_temp_path)

        # Step 5: Download JSON file
        json_temp_path = f"temp_{user_id}_sop.json"
        json_response = supabase.storage.from_('log_data').download(json_path)
        with open(json_temp_path, "wb") as f:
            f.write(json_response)
        temp_files.append(json_temp_path)

        # Rest of your processing logic remains the same...
        pdf_text = await parse_pdf(pdf_temp_path)
        if "Error" in pdf_text:
            raise Exception(pdf_text)
        
        event_data = await parse_json(json_temp_path)
        if isinstance(event_data, list) and "error" in event_data[0]:
            raise Exception(event_data[0]["error"])

        # Fetch relevant Jira issues
        relevant_issues = fetch_relevant_jira_issues(user_id, query, top_k=5)
        jira_context = "\n".join(
            [f"Issue: {issue['issue_id']}\nDetails: {issue['text_data']}" for issue in relevant_issues]
        ) if relevant_issues else "No relevant Jira issues found."

        # Combine all into a Knowledge Base (KB)
        knowledge_base = f"""
        ### Jira Issues:
        {jira_context}
        """

        # Initialize SOPState with the Knowledge Base
        initial_state = SOPState(KB=knowledge_base, pdf_text=pdf_text, event_data=event_data , user_query=query)

        # Run workflow
        result = await workflow.ainvoke(initial_state)

        # Convert result if needed
        if isinstance(result, dict):
            result = SOPState(**result)

        # Delete files from Supabase storage after successful processing
        # We'll delete the entire user directory since we want to clean up everything
        try:
            print(f"Deleting files from storage: {storage_files_to_delete}")
            # supabase.storage.from_('log_data').remove(storage_files_to_delete)
        except Exception as e:
            print(f"Warning: Error deleting files from storage: {str(e)}")

        return {"sop_json": result.sop_json}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
    
    finally:
        # Clean up all temporary files
        for temp_file in temp_files + screenshot_temp_paths:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Error deleting temporary file {temp_file}: {str(e)}")
                
                
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)