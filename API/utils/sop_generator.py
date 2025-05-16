import google.generativeai as genai
from prompts.technical_article_prompt import get_prompt
import os
import asyncio
import json
from supabase import create_client
from io import BytesIO
import datetime
import magic
from PyPDF2 import PdfReader
import tempfile
from google.generativeai.types import GenerationConfig
from utils.markdownit import create_markdown

# Configure GenAI
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")
print(f"[DEBUG] Initialized GenAI model: {model._model_name}")

async def generate_sop_docx(
    KB: str,
    file_path: str,
    event_data: str,
    user_query: str,
    user_id: str,
    job_id: str,
    components: dict
) -> dict:
    """
    Generate SOP output in both JSON and Markdown formats.
    Saves model's raw output locally if SAVE_DEBUG_OUTPUT=true.
    Uploads both JSON and Markdown versions to Supabase.
    """
    article_dict = None
    genai_uploaded_file = None
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_dir = "debug_output"
    save_debug = os.environ.get("SAVE_DEBUG_OUTPUT", "false").lower() == "true"

    if save_debug:
        print(f"[DEBUG] Debug output saving is ENABLED. Files will be saved to '{debug_dir}'.")
        try:
            os.makedirs(debug_dir, exist_ok=True)
            print(f"[DEBUG] Debug directory '{debug_dir}' ensured.")
        except Exception as e:
            print(f"[WARNING] Could not create debug directory '{debug_dir}': {e}")
            save_debug = False

    try:
        # Step 1: Validate Input Schema
        print(f"[DEBUG] Validating provided components schema...")
        if not components or not isinstance(components, dict):
             raise ValueError("[ERROR] Invalid or missing 'components' schema provided. Expected a dictionary.")
        print(f"[DEBUG] Components schema appears valid (type: dict).")

        # Step 2: Initialize Supabase client
        print(f"[DEBUG] Initializing Supabase client...")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("[ERROR] SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment.")
        supabase = create_client(supabase_url, supabase_key)
        print(f"[DEBUG] Supabase client initialized")

        # Step 3: Define Generation Config using the provided schema
        print(f"[DEBUG] Defining GenerationConfig with provided response_schema")
        try:
            generation_config = GenerationConfig(
                temperature=0,
                response_mime_type="application/json",
                response_schema=components
            )
            print(f"[DEBUG] GenerationConfig created using provided schema.")
        except Exception as e:
            print(f"[ERROR] Failed to create GenerationConfig with provided components schema: {e}")
            print(f"[DEBUG] Provided components schema was: {components}")
            raise ValueError(f"Invalid components schema structure for GenerationConfig: {e}")

        # Step 4: Validate the PDF file
        print(f"[DEBUG] Validating PDF file: {file_path}")
        if not os.path.exists(file_path): raise ValueError(f"PDF not found: {file_path}")
        if os.path.getsize(file_path) == 0: raise ValueError(f"PDF empty: {file_path}")
        try:
            mime = magic.Magic(mime=True); detected_mime = mime.from_file(file_path)
            if detected_mime != "application/pdf": raise ValueError(f"Invalid MIME for PDF: {detected_mime}")
        except Exception as e: print(f"[WARNING] PDF MIME check failed: {e}")
        try:
            reader = PdfReader(file_path); print(f"[DEBUG] PDF valid ({len(reader.pages)} pages)")
        except Exception as e: raise ValueError(f"Invalid PDF: {e}")

        # Step 5: Upload the PDF file via GenAI File API
        print(f"[DEBUG] Uploading PDF: {file_path}")
        try:
            genai_uploaded_file = await asyncio.to_thread(
                genai.upload_file, path=file_path, display_name="SOP_PDF", mime_type="application/pdf"
            )
            file_uri = genai_uploaded_file.uri
            print(f"[DEBUG] PDF uploaded. URI: {file_uri}, Name: {genai_uploaded_file.name}")
        except Exception as e:
            print(f"[ERROR] GenAI PDF upload failed: {e}")
            raise ValueError(f"GenAI PDF upload failed: {e}")

        # Step 6: Prepare prompt
        print(f"[DEBUG] Generating prompt...")
        schema_json_str = json.dumps(components, indent=4)
        prompt = get_prompt(
            KB=KB,
            event_text=event_data,
            user_query=user_query,
            generation_schema_str=schema_json_str
        )
        print(f"[DEBUG] Prompt generated.")

        # Step 7: Generate content using GenAI client with schema config
        print(f"[DEBUG] Generating content with JSON schema enforcement...")
        response_text = None
        try:
            response = await asyncio.to_thread(
                model.generate_content,
                contents=[{
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {"file_data": {"file_uri": file_uri, "mime_type": "application/pdf"}}
                    ]
                }],
                generation_config=generation_config
            )
            response_text = response.text
            print(f"[DEBUG] Content generation successful. JSON response expected.")

            if save_debug:
                try:
                    json_filename_debug = f"job_{job_id}_{timestamp}_model_output.json"
                    json_filepath_debug = os.path.join(debug_dir, json_filename_debug)
                    with open(json_filepath_debug, "w", encoding="utf-8") as f:
                        f.write(response_text)
                    print(f"[DEBUG] Saved raw model output to {json_filepath_debug}")
                except Exception as debug_e:
                    print(f"[WARNING] Failed to save raw model output for debugging: {debug_e}")

        except Exception as e:
            print(f"[ERROR] Content generation failed: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'parts'):
                 print(f"[ERROR_DETAILS] Model response parts: {e.response.parts}")
            if hasattr(e, 'response') and hasattr(e.response, 'candidates') and e.response.candidates:
                 print(f"[ERROR_DETAILS] Model candidate finish reason: {e.response.candidates[0].finish_reason}")
                 if e.response.candidates[0].finish_reason.name == 'OTHER':
                     print(f"[ERROR_INFO] Finish reason 'OTHER' often indicates a schema mismatch or internal model error.")
            raise ValueError(f"Content generation failed: {e}")

        # Step 8: Parse/Validate the JSON output
        print(f"[DEBUG] Validating JSON response structure...")
        try:
            if response_text is None:
                raise ValueError("Model response text is None.")
            article_dict = json.loads(response_text)
            if not isinstance(article_dict, dict):
                raise ValueError("Parsed JSON is not a dictionary as expected by top-level schema.")
            print(f"[DEBUG] Successfully validated JSON response structure.")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode JSON response: {e}. Response text was: {response_text}")
            raise ValueError(f"Model did not return valid JSON: {e}")
        except Exception as e:
            print(f"[ERROR] Error processing/validating JSON response: {e}")
            raise ValueError(f"Error processing/validating JSON response: {e}")

        # Step 9: Generate Markdown from the validated JSON
        print(f"[DEBUG] Generating Markdown document from JSON...")
        try:
            markdown_buffer = create_markdown(article_dict)
            markdown_content = markdown_buffer.getvalue().decode('utf-8')
            print(f"[DEBUG] Markdown generation successful.")
            
            if save_debug:
                try:
                    md_filename_debug = f"job_{job_id}_{timestamp}_output.md"
                    md_filepath_debug = os.path.join(debug_dir, md_filename_debug)
                    with open(md_filepath_debug, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    print(f"[DEBUG] Saved Markdown output to {md_filepath_debug}")
                except Exception as debug_e:
                    print(f"[WARNING] Failed to save Markdown output for debugging: {debug_e}")
                    
        except Exception as e:
            print(f"[ERROR] Markdown generation failed: {e}")
            raise ValueError(f"Markdown generation failed: {e}")

        # Step 10: Prepare both JSON and Markdown for storage
        print(f"[DEBUG] Preparing data for storage...")
        try:
            json_bytes = response_text.encode('utf-8')
            md_bytes = markdown_content.encode('utf-8')
            print(f"[DEBUG] Data prepared for storage (JSON: {len(json_bytes)} bytes, Markdown: {len(md_bytes)} bytes).")
        except Exception as e:
            print(f"[ERROR] Failed to encode data for storage: {e}")
            raise ValueError(f"Failed to encode data for storage: {e}")

        # Step 11: Generate storage paths and filenames
        output_json_filename = f"sop_output_{timestamp}.json"
        output_md_filename = f"sop_output_{timestamp}.md"
        
        json_storage_path = f"logdata/{user_id}/{job_id}/{output_json_filename}"
        md_storage_path = f"logdata/{user_id}/{job_id}/markdown/{output_md_filename}"
        
        print(f"[DEBUG] Storage path for JSON: {json_storage_path}")
        print(f"[DEBUG] Storage path for Markdown: {md_storage_path}")

        # Step 12: Ensure markdown directory exists in Supabase
        print(f"[DEBUG] Ensuring markdown directory exists...")
        try:
            # Supabase doesn't actually have empty directories, so we upload a small file to create the path
            dummy_path = f"logdata/{user_id}/{job_id}/markdown/.keep"
            supabase.storage.from_("log_dataa").upload(
                path=dummy_path,
                file=b"",
                file_options={"content-type": "text/plain"}
            )
            # Then delete it (optional)
            supabase.storage.from_("log_dataa").remove([dummy_path])
            print(f"[DEBUG] Markdown directory structure ensured.")
        except Exception as e:
            print(f"[WARNING] Could not ensure markdown directory structure: {e}")

        # Step 13: Upload both files to Supabase storage
        print(f"[DEBUG] Uploading files to Supabase...")
        content_type_json = "application/json"
        content_type_md = "text/markdown"
        
        # Upload JSON
        json_upload_success = False
        try:
            supabase.storage.from_("log_dataa").upload(
                path=json_storage_path, 
                file=json_bytes, 
                file_options={"content-type": content_type_json}
            )
            json_upload_success = True
        except Exception as e: 
            print(f"[WARNING] Supabase JSON upload failed (attempt 1): {e}")
            try:
                supabase.storage.from_("log_dataa").upload(
                    path=json_storage_path, 
                    file=json_bytes
                )
                json_upload_success = True
            except Exception as e: 
                print(f"[ERROR] Fallback JSON upload failed (attempt 2): {e}")

        # Upload Markdown
        md_upload_success = False
        try:
            supabase.storage.from_("log_dataa").upload(
                path=md_storage_path,
                file=md_bytes,
                file_options={"content-type": content_type_md}
            )
            md_upload_success = True
        except Exception as e:
            print(f"[WARNING] Supabase Markdown upload failed (attempt 1): {e}")
            try:
                supabase.storage.from_("log_dataa").upload(
                    path=md_storage_path,
                    file=md_bytes
                )
                md_upload_success = True
            except Exception as e:
                print(f"[ERROR] Fallback Markdown upload failed (attempt 2): {e}")

        if not json_upload_success or not md_upload_success:
            raise ValueError("File uploads to Supabase failed")

        print(f"[DEBUG] Both JSON and Markdown uploads successful to Supabase.")

        # Step 14: Get public URLs for both files
        print(f"[DEBUG] Generating public URLs...")
        json_download_url = supabase.storage.from_("log_dataa").get_public_url(json_storage_path)
        md_download_url = supabase.storage.from_("log_dataa").get_public_url(md_storage_path)
        
        print(f"[DEBUG] JSON Download URL: {json_download_url}")
        print(f"[DEBUG] Markdown Download URL: {md_download_url}")

        return {
            "status": "success",
            "json_document_path": json_storage_path,
            "markdown_document_path": md_storage_path,
            "json_download_url": json_download_url,
            "markdown_download_url": md_download_url,
            "user_id": user_id,
            "job_id": job_id,
            "timestamp": timestamp
        }

    except ValueError as e:
        print(f"[ERROR] Value error during SOP generation: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] General unexpected error in SOP generation: {e}")
        raise
    finally:
        if genai_uploaded_file and hasattr(genai_uploaded_file, 'name'):
            print(f"[DEBUG] Final cleanup: Deleting GenAI file {genai_uploaded_file.name}...")
            try:
                await asyncio.to_thread(genai.delete_file, genai_uploaded_file.name)
                print(f"[DEBUG] GenAI file deleted.")
            except Exception as e:
                print(f"[WARNING] Failed to delete GenAI file during cleanup: {e}")
        else:
             print(f"[DEBUG] Final cleanup: No GenAI input file found to delete or already cleaned up.")