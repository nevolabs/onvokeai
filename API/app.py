import os
import re
import uuid
import json
from pathlib import Path
from typing import Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from supabase import create_client, Client
import pandas as pd
import PyPDF2
from docx import Document
from io import BytesIO

# Assuming these local modules exist in your project structure
from config.config import load_config, set_env
from models.state_schema import SOPState
from parsers.json_parser import parse_json
from workflow import create_workflow
from utils.create_pdf import create_pdf_from_screenshots
from utils.pdf_converter import convert_to_pdf
from utils.docx_converter import convert_to_docx

from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = [
    "https://dashboard.onvoke.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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

# Placeholder for the Jira fetch function to avoid NameError if uncommented
# def fetch_relevant_jira_issues(user_id, query, top_k=5):
#     # This would contain your actual Jira fetching logic
#     return []

def read_excel_file(file_content: bytes) -> str:
    """Read content from an Excel file."""
    try:
        excel_file = BytesIO(file_content)
        df = pd.read_excel(excel_file, engine='openpyxl')
        # Convert all sheets to text (simplified representation)
        return df.to_string()
    except Exception as e:
        print(f"[ERROR] Failed to read Excel file: {str(e)}")
        return ""

def read_pdf_file(file_content: bytes) -> str:
    """Read content from a PDF file."""
    try:
        pdf_file = BytesIO(file_content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"[ERROR] Failed to read PDF file: {str(e)}")
        return ""

def read_docx_file(file_content: bytes) -> str:
    """Read content from a DOCX file."""
    try:
        docx_file = BytesIO(file_content)
        doc = Document(docx_file)
        text = "\n".join([para.text for para in doc.paragraphs if para.text])
        return text
    except Exception as e:
        print(f"[ERROR] Failed to read DOCX file: {str(e)}")
        return ""

@app.post("/generate_sop/")
async def generate_sop_api(
    file: Optional[UploadFile] = File(None), 
    user_id: str = Form(...),
    job_id: str = Form(...),
    query: str = Form(...),
    templates_id: str = Form(...),
):
    """
    API endpoint to generate SOP using a component schema defined
    in a user-specific or public template.
    """
    temp_files = []
    screenshot_info = []
    full_component_schema: Optional[dict] = None
    category_name: str = 'SOP'
    
    uploaded_file_content = ""
    if file:
        contents = await file.read()
        file_extension = Path(file.filename).suffix.lower()
        if file_extension in ['.xlsx', '.xls']:
            uploaded_file_content = read_excel_file(contents)
        elif file_extension == '.pdf':
            uploaded_file_content = read_pdf_file(contents)
        elif file_extension == '.docx':
            uploaded_file_content = read_docx_file(contents)
        else:
            uploaded_file_content = contents.decode('utf-8', errors='ignore')

    try:
        print(f"[DEBUG] Starting SOP generation for user_id={user_id}, job_id={job_id}, template_id='{templates_id}'")

        # --- EXTENDED LOGIC: Fetch Template from private or public table ---
        try:
            print(f"[DEBUG] 1. Attempting to fetch from user's private 'templates' table for template_id={templates_id}")
            response = supabase.table('templates') \
                               .select('components, name') \
                               .eq('id', templates_id) \
                               .eq('user_id', user_id) \
                               .maybe_single() \
                               .execute()

            if response.data and 'components' in response.data:
                print("[INFO] Found template in user's private table.")
                full_component_schema = response.data['components']
                category_name = response.data.get('name', 'SOP')
            else:
                # --- If not found, check the public templates table ---
                print(f"[INFO] Template not found in private table. Checking 'publictemplates' table.")
                public_response = supabase.table('publictemplates') \
                                          .select('components, name') \
                                          .eq('id', templates_id) \
                                          .maybe_single() \
                                          .execute()
                
                if public_response.data and 'components' in public_response.data:
                    print("[INFO] Found template in public table.")
                    full_component_schema = public_response.data['components']
                    category_name = public_response.data.get('name', 'SOP')
                else:
                    # --- If not found in either table, raise an error ---
                    print(f"[ERROR] No components found for template_id={templates_id} in private or public tables.")
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
            for screenshot_file in screenshot_files:
                file_name = screenshot_file.get('name')
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
            for json_file_obj in json_files:
                file_name = json_file_obj.get('name')
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

        jira_context = ""
        # try:
        #     print(f"[DEBUG] Fetching Jira issues for query: {query}")
        #     relevant_issues = fetch_relevant_jira_issues(user_id, query, top_k=5)
        #     if relevant_issues:
        #         jira_context = "\n".join([
        #             f"Issue: {issue.get('issue_id', 'N/A')}\nDetails: {issue.get('text_data', 'N/A')}" 
        #             for issue in relevant_issues
        #         ])
        #     else: 
        #         jira_context = "No relevant Jira issues found."
        #     print(f"[DEBUG] Fetched Jira context")
        # except Exception as e:
        #     print(f"[WARNING] Error fetching Jira issues: {str(e)}")
        #     jira_context = f"Error fetching Jira issues: {str(e)}"

        # --- Prepare and Invoke Workflow ---
        knowledge_base = f"### Jira Issues:\n{jira_context}\n"
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
                category_name=category_name,
                contents=uploaded_file_content
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
                "files_processed": len(screenshot_info) + (1 if file else 0),
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

@app.post("/download/")
def convert_markdown(markdown_text: str = Form(...), 
                     format: str = Form(...), 
                     filename: str = None):
    try:
        if format == "pdf":
            content = convert_to_pdf(markdown_text)
            default_filename = "document.pdf"
            media_type = "application/pdf"
        elif format == "docx":
            content = convert_to_docx(markdown_text)
            default_filename = "document.docx"
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Please use 'pdf' or 'docx'.")
        
        filename = filename or default_filename
        # Wrap content in BytesIO for streaming
        file_stream = BytesIO(content)
        
        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True, workers=4, log_level="info")
