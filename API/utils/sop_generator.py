import google.generativeai as genai
from langchain_core.output_parsers import JsonOutputParser
from pydantic import ValidationError
from models.custom_models import CustomTechnicalArticle as TechnicalArticle
from prompts.technical_article_prompt import get_prompt
import os
import asyncio
from utils.docx_converter import create_docx
from supabase import create_client
from io import BytesIO
import datetime
import magic  # For MIME type detection
from PyPDF2 import PdfReader  # For PDF validation
import zipfile  # For DOCX validation
import tempfile  # For temporary file handling

# Configure GenAI
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")
print(f"[DEBUG] Initialized GenAI model: {model._model_name}")

async def generate_sop_docx(
    KB: str, 
    file_path: str, 
    event_data: str, 
    user_query: str,
    user_id: str,
    job_id: str,
    components
) -> dict:
    """Generate SOP documentation as DOCX and store in Supabase with path logdata/userid/jobid/"""
    try:
        # Step 1: Initialize Supabase client
        print(f"[DEBUG] Initializing Supabase client with URL: {os.getenv('SUPABASE_URL')}")
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
        print(f"[DEBUG] Supabase client initialized")

        # Step 2: Define the parser
        print(f"[DEBUG] Setting up JsonOutputParser for TechnicalArticle")
        parser = JsonOutputParser(pydantic_object=TechnicalArticle)
        format_instructions = parser.get_format_instructions()
        print(f"[DEBUG] Format instructions generated: {format_instructions[:100]}...")

        # Step 3: Validate the PDF file
        print(f"[DEBUG] Validating PDF file: {file_path}")
        if not os.path.exists(file_path):
            raise ValueError(f"[ERROR] PDF file not found at: {file_path}")
        
        file_size = os.path.getsize(file_path)
        print(f"[DEBUG] PDF file size: {file_size} bytes")
        if file_size == 0:
            raise ValueError(f"[ERROR] PDF file at {file_path} is empty")

        # Check MIME type using python-magic
        try:
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_file(file_path)
            print(f"[DEBUG] Detected PDF MIME type: {detected_mime}")
            if detected_mime != "application/pdf":
                raise ValueError(f"[ERROR] PDF file is not valid. Detected MIME type: {detected_mime}")
        except Exception as e:
            print(f"[WARNING] PDF MIME type detection failed: {str(e)}")

        # Verify PDF validity using PyPDF2
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            print(f"[DEBUG] PDF is valid with {num_pages} page(s)")
        except Exception as e:
            raise ValueError(f"[ERROR] Invalid PDF file at {file_path}: {str(e)}")

        # Step 4: Upload the PDF file using GenAI File API
        print(f"[DEBUG] Attempting to upload PDF: {file_path} with mime_type=application/pdf")
        try:
            file = await asyncio.to_thread(
                genai.upload_file, 
                path=file_path, 
                display_name="SOP_PDF", 
                mime_type="application/pdf"
            )
            file_uri = file.uri
            print(f"[DEBUG] PDF uploaded successfully. URI: {file_uri}, Name: {file.name}")
        except Exception as e:
            print(f"[ERROR] GenAI PDF upload failed: {str(e)}")
            raise ValueError(f"[ERROR] GenAI PDF upload failed: {str(e)}")

        # Step 5: Prepare prompt
        print(f"[DEBUG] Generating prompt")
        prompt = get_prompt(
            KB=KB,
            event_text=event_data,
            user_query=user_query,
            format_instructions=format_instructions,
            components=components
        )
        print(f"[DEBUG] Prompt generated: {prompt[:200]}...")

        # Step 6: Generate content using GenAI client
        print(f"[DEBUG] Generating content with file URI: {file_uri}")
        try:
            response = await asyncio.to_thread(
                model.generate_content,
                contents=[
                    {
                        "role": "user", 
                        "parts": [
                            {"text": prompt},
                            {"file_data": {"file_uri": file_uri, "mime_type": "application/pdf"}}
                        ]
                    }
                ],
                generation_config={"temperature": 0}
            )
            print(f"[DEBUG] Content generation successful. Response: {response.text[:100]}...")
        except Exception as e:
            print(f"[ERROR] Content generation failed: {str(e)}")
            raise ValueError(f"[ERROR] Content generation failed: {str(e)}")

        # Step 7: Parse and validate the output
        print(f"[DEBUG] Parsing response text")
        json_output = parser.parse(response.text)
        article = TechnicalArticle(**json_output)
        print(f"[DEBUG] Article validated")

        # Step 8: Create DOCX file
        print(f"[DEBUG] Creating DOCX file")
        doc_buffer = create_docx(article)
        doc_bytes = doc_buffer.getvalue()
        print(f"[DEBUG] DOCX file created in memory. Buffer size: {len(doc_bytes)} bytes")

#sopgenerator (relevant section)

        # Validate DOCX file
        print(f"[DEBUG] Validating DOCX file")
        try:
            # Generate timestamp early for debug file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # MOVED THIS LINE UP
            
            # Save DOCX to a temporary file for validation
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
                temp_docx_path = temp_file.name
                temp_file.write(doc_bytes)
            
            # Check if it's a valid ZIP (DOCX is a ZIP archive)
            with zipfile.ZipFile(temp_docx_path, 'r') as zf:
                print(f"[DEBUG] DOCX is a valid ZIP archive")
            
            # Check MIME type
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_file(temp_docx_path)
            print(f"[DEBUG] Detected DOCX MIME type: {detected_mime}")
            
            # Save debug copy with proper timestamp
            debug_filename = f"debug_sop_{timestamp}.docx"
            with open(debug_filename, "wb") as f:
                f.write(doc_bytes)
            print(f"[DEBUG] Saved DOCX copy for inspection at: {debug_filename}")
            
            os.remove(temp_docx_path)
            print(f"[DEBUG] Temporary DOCX file removed")

        # Rest of the code remains the same...
        except Exception as e:
            print(f"[ERROR] DOCX validation failed: {str(e)}")
            raise ValueError(f"[ERROR] Invalid DOCX file: {str(e)}")

        # Step 9: Generate storage path and filename
        filename = f"sop_{timestamp}.docx"
        storage_path = f"logdata/{user_id}/{job_id}/{filename}"
        print(f"[DEBUG] Storage path: {storage_path}")

        # Step 10: Upload to Supabase storage
        print(f"[DEBUG] Uploading DOCX to Supabase at: {storage_path}")
        upload_success = False
        upload_response = None

        # Attempt 1: Upload with explicit content-type
        try:
            upload_response = supabase.storage.from_("log_dataa").upload(
                path=storage_path,
                file=doc_bytes,
                file_options={
                    "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                }
            )
            print(f"[DEBUG] Supabase upload response: {upload_response}")
            upload_success = True
        except Exception as e:
            print(f"[ERROR] Supabase upload failed with content-type: {str(e)}")

        # Attempt 2: Fallback without explicit content-type
        if not upload_success:
            print(f"[DEBUG] Attempting fallback upload without explicit content-type")
            try:
                upload_response = supabase.storage.from_("log_dataa").upload(
                    path=storage_path,
                    file=doc_bytes
                )
                print(f"[DEBUG] Fallback upload response: {upload_response}")
                upload_success = True
            except Exception as e:
                print(f"[ERROR] Fallback upload failed: {str(e)}")

        # Attempt 3: Fallback with generic MIME type
        if not upload_success:
            print(f"[DEBUG] Attempting fallback upload with generic MIME type")
            try:
                upload_response = supabase.storage.from_("log_dataa").upload(
                    path=storage_path,
                    file=doc_bytes,
                    file_options={"content-type": "application/octet-stream"}
                )
                print(f"[DEBUG] Generic MIME type upload response: {upload_response}")
                upload_success = True
            except Exception as e:
                print(f"[ERROR] Generic MIME type upload failed: {str(e)}")

        if not upload_success:
            raise ValueError(f"[ERROR] All Supabase upload attempts failed")

        # Step 11: Get public URL
        print(f"[DEBUG] Generating public URL for: {storage_path}")
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

    except ValidationError as e:
        error_details = [f"{'->'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()]
        print(f"[ERROR] Validation error: {error_details}")
        raise ValueError(f"[ERROR] Validation error: {', '.join(error_details)}")
    
    except Exception as e:
        print(f"[ERROR] General error in SOP generation: {str(e)}")
        raise ValueError(f"[ERROR] Error generating or storing SOP: {str(e)}")
    
    finally:
        # Clean up: Delete the uploaded file
        if 'file' in locals():
            print(f"[DEBUG] Deleting uploaded file: {file.name}")
            try:
                await asyncio.to_thread(genai.delete_file, file.name)
                print(f"[DEBUG] File deleted successfully")
            except Exception as e:
                print(f"[WARNING] Failed to delete uploaded file: {str(e)}")