import google.generativeai as genai
# Removed Pydantic/Langchain imports
from prompts.technical_article_prompt import get_prompt # Ensure this doesn't need format_instructions
import os
import asyncio
import json
from utils.docx_converter import create_docx # MUST accept a dict
from supabase import create_client
from io import BytesIO
import datetime
import magic
from PyPDF2 import PdfReader
import zipfile
import tempfile
# Import Schema types if components is passed as a dict needing conversion, otherwise not strictly needed here
# from google.generativeai.types import Schema, Type
from google.generativeai.types import GenerationConfig # Keep GenerationConfig

# Configure GenAI
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
# Using 1.5 Flash as it generally handles structured output well
model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
print(f"[DEBUG] Initialized GenAI model: {model._model_name}")

# REMOVED: Hardcoded output_schema_genai definition

async def generate_sop_docx(
    KB: str,
    file_path: str,
    event_data: str,
    user_query: str,
    user_id: str,
    job_id: str,
    components: dict # Expecting a dict representing the google.generativeai.types.Schema structure
) -> dict:
    """Generate SOP DOCX using a provided component schema for JSON output."""
    article_dict = None
    file = None # Initialize for finally block

    try:
        # Step 1: Validate Input Schema
        print(f"[DEBUG] Validating provided components schema...")
        if not components or not isinstance(components, dict):
             raise ValueError("[ERROR] Invalid or missing 'components' schema provided. Expected a dictionary.")
        # Optional: Add more specific checks if needed, e.g., presence of 'type', 'properties'
        print(f"[DEBUG] Components schema appears valid (type: dict).")

        # Step 2: Initialize Supabase client
        print(f"[DEBUG] Initializing Supabase client...")
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
        print(f"[DEBUG] Supabase client initialized")

        # Step 3: Define Generation Config using the provided schema
        print(f"[DEBUG] Defining GenerationConfig with provided response_schema")
        try:
            generation_config = GenerationConfig(
                temperature=0,
                response_mime_type="application/json",
                # Directly use the provided dictionary as the schema
                response_schema=components
            )
            print(f"[DEBUG] GenerationConfig created using provided schema.")
        except Exception as e:
            # Catch errors if the provided dict isn't compatible with GenerationConfig
            print(f"[ERROR] Failed to create GenerationConfig with provided components schema: {e}")
            print(f"[DEBUG] Provided components schema was: {components}")
            raise ValueError(f"Invalid components schema structure for GenerationConfig: {e}")


        # Step 4: Validate the PDF file
        print(f"[DEBUG] Validating PDF file: {file_path}")
        if not os.path.exists(file_path): raise ValueError(f"PDF not found: {file_path}")
        if os.path.getsize(file_path) == 0: raise ValueError(f"PDF empty: {file_path}")
        try: # MIME Check
            mime = magic.Magic(mime=True); detected_mime = mime.from_file(file_path)
            if detected_mime != "application/pdf": raise ValueError(f"Invalid MIME: {detected_mime}")
        except Exception as e: print(f"[WARNING] PDF MIME check failed: {e}")
        try: # PDF Read Check
            reader = PdfReader(file_path); print(f"[DEBUG] PDF valid ({len(reader.pages)} pages)")
        except Exception as e: raise ValueError(f"Invalid PDF: {e}")

        # Step 5: Upload the PDF file via GenAI File API
        print(f"[DEBUG] Uploading PDF: {file_path}")
        try:
            file = await asyncio.to_thread(
                genai.upload_file, path=file_path, display_name="SOP_PDF", mime_type="application/pdf"
            )
            file_uri = file.uri
            print(f"[DEBUG] PDF uploaded. URI: {file_uri}, Name: {file.name}")
        except Exception as e:
            print(f"[ERROR] GenAI PDF upload failed: {e}")
            raise ValueError(f"GenAI PDF upload failed: {e}")

        # Step 6: Prepare prompt (ensure get_prompt asks for JSON matching the schema)
        print(f"[DEBUG] Generating prompt...")
        prompt = get_prompt(
            KB=KB, event_text=event_data, user_query=user_query 
        )
        print(f"[DEBUG] Prompt generated.")

        # Step 7: Generate content using GenAI client with schema config
        print(f"[DEBUG] Generating content with JSON schema enforcement...")
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
                generation_config=generation_config # Use config with provided schema
            )
          
            response_text = response.text
            print(f"[DEBUG] Content generation successful. JSON response expected.")

        except Exception as e:
            print(f"[ERROR] Content generation failed: {e}")
            if file: # Attempt cleanup on error
                try: await asyncio.to_thread(genai.delete_file, file.name)
                except Exception as del_e: print(f"[WARNING] Failed to delete file after error: {del_e}")
            raise ValueError(f"Content generation failed: {e}")

        # Step 8: Parse the JSON output
        print(f"[DEBUG] Parsing JSON response...")
        try:
            article_dict = json.loads(response_text)
            if not isinstance(article_dict, dict): raise ValueError("Parsed JSON is not a dictionary.")
            print(f"[DEBUG] Successfully parsed JSON response.")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode JSON response: {e}. Response text: {response_text}")
            raise ValueError(f"Model did not return valid JSON: {e}")
        except Exception as e:
            print(f"[ERROR] Error processing JSON response: {e}")
            raise ValueError(f"Error processing JSON response: {e}")

        # Step 9: Create DOCX file (using the dictionary)
        print(f"[DEBUG] Creating DOCX file from dictionary...")
        try:
            doc_buffer = create_docx(article_dict) 
            doc_bytes = doc_buffer.getvalue()
            print(f"[DEBUG] DOCX created in memory ({len(doc_bytes)} bytes).")
        except Exception as e:
             print(f"[ERROR] Failed to create DOCX from dictionary: {e}")
             raise ValueError(f"Failed to create DOCX file: {e}")

        # Step 10: Validate DOCX file
        print(f"[DEBUG] Validating DOCX file...")
        temp_docx_path = None
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
                temp_docx_path = temp_file.name
                temp_file.write(doc_bytes)
            with zipfile.ZipFile(temp_docx_path, 'r'): pass # Check if valid zip
            mime = magic.Magic(mime=True); detected_mime = mime.from_file(temp_docx_path)
            print(f"[DEBUG] DOCX valid (MIME: {detected_mime}).")
        except Exception as e:
            print(f"[ERROR] DOCX validation failed: {e}")
            raise ValueError(f"Invalid DOCX file generated: {e}")
        finally:
             if temp_docx_path and os.path.exists(temp_docx_path):
                 os.remove(temp_docx_path)

        # Step 11: Generate storage path and filename
        filename = f"sop_{timestamp}.docx"
        storage_path = f"logdata/{user_id}/{job_id}/{filename}"
        print(f"[DEBUG] Storage path: {storage_path}")

        # Step 12: Upload to Supabase storage
        print(f"[DEBUG] Uploading DOCX to Supabase...")
        upload_success = False
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        try: # Attempt 1
            supabase.storage.from_("log_dataa").upload(
                path=storage_path, file=doc_bytes, file_options={"content-type": content_type}
            )
            upload_success = True
        except Exception as e: print(f"[WARNING] Supabase upload failed (attempt 1): {e}")
        if not upload_success: # Attempt 2
            print(f"[DEBUG] Attempting fallback upload...")
            try:
                supabase.storage.from_("log_dataa").upload(path=storage_path, file=doc_bytes)
                upload_success = True
            except Exception as e: print(f"[ERROR] Fallback upload failed (attempt 2): {e}")

        if not upload_success: raise ValueError(f"Supabase upload failed for {storage_path}")
        print(f"[DEBUG] Upload successful.")

        # Step 13: Get public URL
        print(f"[DEBUG] Generating public URL...")
        download_url = supabase.storage.from_("log_dataa").get_public_url(storage_path)
        print(f"[DEBUG] Download URL: {download_url}")

        return {
            "status": "success",
            "document_path": storage_path,
            "download_url": download_url,
            "user_id": user_id,
            "job_id": job_id,
            "timestamp": timestamp
        }

    except ValueError as e:
        print(f"[ERROR] Value error during SOP generation: {e}")
        raise ValueError(f"SOP Generation Error: {e}") from e
    except Exception as e:
        print(f"[ERROR] General unexpected error in SOP generation: {e}")
        raise ValueError(f"Unexpected error generating/storing SOP: {e}") from e
    finally:
        # Final Cleanup: Delete the uploaded GenAI file
        if file and hasattr(file, 'name'):
            print(f"[DEBUG] Final cleanup: Deleting GenAI file {file.name}...")
            try:
                await asyncio.to_thread(genai.delete_file, file.name)
                print(f"[DEBUG] GenAI file deleted.")
            except Exception as e:
                print(f"[WARNING] Failed to delete GenAI file during cleanup: {e}")
        else:
             print(f"[DEBUG] Final cleanup: No GenAI file found to delete.")