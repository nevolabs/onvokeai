import google.generativeai as genai
from prompts.technical_article_prompt import get_prompt # Assuming this is a custom module
import os
import asyncio
import json
from supabase import create_client, Client
from io import BytesIO
import datetime
import magic
from PyPDF2 import PdfReader # Corrected import name
from google.generativeai.types import GenerationConfig
from utils.markdownit import create_markdown # Assuming this is a custom module
import random
# Configure GenAI
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash-lite")
print(f"[INFO] Initialized GenAI model: {model._model_name}")

async def generate_sop_docx(
    KB: str,
    file_path: str,
    event_data: str,
    user_query: str,
    user_id: str,
    job_id: str,
    components: dict, # This is now loaded from generation.json
    category_name: str = ""
) -> dict:
    """
    Generates an SOP, stores the Markdown output in a Supabase table.
    Saves model's raw JSON output and generated Markdown locally if SAVE_DEBUG_OUTPUT=true.
    """
    
    # Load the generation schema (components) from the JSON file
    # This schema is used for GenAI response structuring and title extraction
    article_dict = None
    genai_uploaded_file = None
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_dir = "debug_output"
    save_debug = os.environ.get("SAVE_DEBUG_OUTPUT", "false").lower() == "true"

    if save_debug:
        print(f"[INFO] Debug output saving is ENABLED. Files will be saved to '{debug_dir}'.")
        try:
            os.makedirs(debug_dir, exist_ok=True)
        except Exception as e:
            print(f"[WARNING] Could not create debug directory '{debug_dir}': {e}")
            save_debug = False # Disable if directory creation fails

    try:
        components_schema = components
        # Step 1: Validate Input Schema (already loaded as components_schema)
        if not components_schema or not isinstance(components_schema, dict):
             raise ValueError("[ERROR] Invalid or missing 'components_schema' from 'generation.json'. Expected a dictionary.")
        print(f"[INFO] Components schema from 'generation.json' appears valid.")

        # Step 2: Initialize Supabase client
        print(f"[INFO] Initializing Supabase client...")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("[ERROR] SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment.")
        supabase: Client = create_client(supabase_url, supabase_key)
        print(f"[INFO] Supabase client initialized.")

        # Step 3: Define Generation Config using the loaded schema
        print(f"[INFO] Defining GenerationConfig with response_schema from 'generation.json'")
        try:
            generation_config = GenerationConfig(
                temperature=0, # For deterministic output
                response_mime_type="application/json",
                response_schema=components_schema
            )
        except Exception as e:
            print(f"[ERROR] Failed to create GenerationConfig with schema: {e}")
            print(f"[DEBUG] Schema used was: {components_schema}")
            raise ValueError(f"Invalid components_schema structure for GenerationConfig: {e}")

        # Step 4: Validate the PDF file
        print(f"[INFO] Validating PDF file: {file_path}")
        if not os.path.exists(file_path): raise ValueError(f"PDF not found: {file_path}")
        if os.path.getsize(file_path) == 0: raise ValueError(f"PDF empty: {file_path}")
        try:
            mime = magic.Magic(mime=True); detected_mime = mime.from_file(file_path)
            if detected_mime != "application/pdf": raise ValueError(f"Invalid MIME for PDF: {detected_mime}")
        except Exception as e: print(f"[WARNING] PDF MIME check failed (continuing): {e}") # Non-fatal warning
        try:
            reader = PdfReader(file_path); print(f"[INFO] PDF valid ({len(reader.pages)} pages)")
        except Exception as e: raise ValueError(f"Invalid PDF: {e}")

        # Step 5: Upload the PDF file via GenAI File API
        print(f"[INFO] Uploading PDF to GenAI: {file_path}")
        try:
            # Use asyncio.to_thread for blocking I/O in async function
            genai_uploaded_file = await asyncio.to_thread(
                genai.upload_file, path=file_path, display_name=f"SOP_PDF_{job_id}", mime_type="application/pdf"
            )
            file_uri = genai_uploaded_file.uri
            print(f"[INFO] PDF uploaded to GenAI. URI: {file_uri}")
        except Exception as e:
            print(f"[ERROR] GenAI PDF upload failed: {e}")
            raise ValueError(f"GenAI PDF upload failed: {e}")

        # Step 6: Prepare prompt
        print(f"[INFO] Generating prompt...")
        schema_json_str = json.dumps(components_schema, indent=2) # Use 2 spaces for less verbose debug output
        prompt = get_prompt(
            KB=KB,
            event_text=event_data,
            user_query=user_query,
            generation_schema_str=schema_json_str # Pass the schema string to the prompt function
        )
        
        # prompt = "created a technical article based on the following PDF file. The article should be structured according to the provided JSON schema. The PDF file is attached as a file input. Please ensure that the generated content adheres to the schema and is relevant to the content of the PDF."
        # print(f"[DEBUG] Generated prompt: {prompt[:500]}...") # Optionally log part of the prompt

        # Step 7: Generate content using GenAI client with schema config
        print(f"[INFO] Generating content with JSON schema enforcement...")
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
            response_text = response.text # Expecting JSON string
            with open("output.json", "w", encoding="utf-8") as f:
                f.write(response_text)
                print(f"[INFO] Generated content: {response_text[:500]}...") # Optionally log
                
            print(f"[INFO] Content generation successful. JSON response received.",response_text[:100]) # Log first 100 chars of response for debugging
            if not response_text:
                raise ValueError("Model response text is empty. Cannot parse.")
            if save_debug:
                try:
                    json_filename_debug = f"job_{job_id}_{timestamp}_model_output.json"
                    json_filepath_debug = os.path.join(debug_dir, json_filename_debug)
                    with open(json_filepath_debug, "w", encoding="utf-8") as f:
                        f.write(response_text)
                    print(f"[INFO] Saved raw model JSON output to {json_filepath_debug}")
                except Exception as debug_e:
                    print(f"[WARNING] Failed to save raw model output for debugging: {debug_e}")

        except Exception as e:
            print(f"[ERROR] Content generation failed: {e}")
            # Log more details if available from the GenAI exception
            if hasattr(e, 'response') and e.response:
                 if hasattr(e.response, 'parts'): print(f"[ERROR_DETAILS] Model response parts: {e.response.parts}")
                 if hasattr(e.response, 'candidates') and e.response.candidates:
                     print(f"[ERROR_DETAILS] Model candidate finish reason: {e.response.candidates[0].finish_reason}")
                     if e.response.candidates[0].finish_reason.name == 'OTHER':
                         print(f"[ERROR_INFO] Finish reason 'OTHER' often indicates a schema mismatch or internal model error. Check 'generation.json' against model output capabilities.")
            raise ValueError(f"Content generation failed: {e}")

        # Step 8: Parse/Validate the JSON output
        print(f"[INFO] Validating JSON response structure...")
        try:
            if response_text is None:
                raise ValueError("Model response text is None. Cannot parse.")
            article_dict = json.loads(response_text)
            if not isinstance(article_dict, dict): # Top level of schema should be an object
                raise ValueError("Parsed JSON is not a dictionary as expected by the top-level schema.")
            print(f"[INFO] Successfully parsed and validated JSON response structure.")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to decode JSON response: {e}. Response text was: {response_text[:500]}...")
            raise ValueError(f"Model did not return valid JSON: {e}")
        except Exception as e: # Catch other validation errors
            print(f"[ERROR] Error processing/validating JSON response: {e}")
            raise ValueError(f"Error processing/validating JSON response: {e}")

        # Step 9: Generate Markdown from the validated JSON
        print(f"[INFO] Generating Markdown document from JSON...")
        try:
            # create_markdown function is expected to take the dictionary and return a BytesIO buffer
            markdown_buffer = create_markdown(article_dict,user_id ,job_id) 
            markdown_content = markdown_buffer.getvalue().decode('utf-8')
            print(f"[INFO] Markdown generation successful.")
            
            if save_debug:
                try:
                    md_filename_debug = f"job_{job_id}_{timestamp}_output.md"
                    md_filepath_debug = os.path.join(debug_dir, md_filename_debug)
                    with open(md_filepath_debug, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    print(f"[INFO] Saved Markdown output to {md_filepath_debug}")
                except Exception as debug_e:
                    print(f"[WARNING] Failed to save Markdown output for debugging: {debug_e}")
                    
        except Exception as e:
            print(f"[ERROR] Markdown generation failed: {e}")
            raise ValueError(f"Markdown generation failed: {e}")

        # Step 10: Extract title and prepare data for database
        print(f"[INFO] Preparing data for database insertion...")
        try:
            # Extract title from the article_dict.
            # This assumes 'title' is a key in the root of the JSON structure defined in 'generation.json'.
            # Adjust `article_dict.get('title')` if the title is nested, e.g., `article_dict.get('metadata', {}).get('title')`.
            sop_title = article_dict.get('docTitle',"SOP") 
            if not sop_title:
                print(f"[WARNING] 'title' not found in generated JSON. Using a default title.")
                sop_title = f"Generated SOP for Job {job_id} - {timestamp}"
            
            # Data to be inserted into the 'generated_docs' table
            # Fields: user_id, title, content (created_at and id are auto-managed by Supabase)
            print(f"markdown_content[:100]...") # Log first 100 chars of content for debugging
            print(markdown_content[:100])
            db_record = {
                "id":random.randint(1, 10000000), # Random ID for testing, replace with None for auto-increment
                "category": category_name,
                "user_id": user_id,
                "title": sop_title,
                "content": markdown_content, # Storing the full markdown text
                "desc": article_dict.get('shortDescription', ''),
            }
            # print(f"[DEBUG] Record to insert: {{user_id: {user_id}, title: '{sop_title}', content_length: {len(markdown_content)}}}")

        except Exception as e:
            print(f"[ERROR] Failed to prepare data for database: {e}")
            raise ValueError(f"Failed to prepare data for database: {e}")

        # Step 11: Insert data into Supabase table 'generated_docs'
        print(f"[INFO] Inserting document into Supabase table 'generated_docs'...")
        try:
            insert_response = supabase.table("generated_docs").insert(db_record).execute()

            if not insert_response.data or len(insert_response.data) == 0:
                error_message = "Unknown error during Supabase insert."
                if hasattr(insert_response, 'error') and insert_response.error:
                    error_message = f"Supabase insert error: {insert_response.error.message if hasattr(insert_response.error, 'message') else insert_response.error}"
                elif hasattr(insert_response, 'status_code') and insert_response.status_code not in [200, 201]:
                     error_message = f"Supabase insert failed with status {insert_response.status_code}."
                     try:
                         error_details = insert_response.json()
                         error_message += f" Details: {error_details}"
                     except: # if .json() fails
                         error_message += " Could not parse error response body."
                
                print(f"[ERROR] {error_message}")
                # print(f"[DEBUG] Supabase insert response object: {insert_response}")
                raise ValueError(f"Failed to insert document into Supabase table. {error_message}")

            inserted_doc = insert_response.data[0]
            inserted_doc_id = inserted_doc.get('id') # Supabase returns the inserted record(s) with 'id'
            print(f"[INFO] Document successfully inserted into 'generated_docs'. ID: {inserted_doc_id}")

        except Exception as e:
            print(f"[ERROR] Supabase table insertion failed: {e}")
            # Avoid logging full db_record.content if it's very large in production logs
            print(f"[DEBUG] Failed to insert record (title: {db_record.get('title')}, user_id: {db_record.get('user_id')})")
            raise ValueError(f"Supabase table insertion failed: {e}")

        # Step 12: Return success response
        return {
            "status": "success",
            "message": "SOP generated and stored successfully in the database.",
            "document_id": inserted_doc_id, # The ID from 'generated_docs' table
            "title": sop_title,
            "user_id": user_id,
            "job_id": job_id, # Still useful to return job_id for context
            "timestamp": timestamp # Generation timestamp
        }

    except ValueError as e: # Catch specific, anticipated errors
        print(f"[ERROR] Value error during SOP generation: {e}")
        # Potentially re-raise with more context or a custom exception type
        raise
    except Exception as e: # Catch any other unexpected errors
        print(f"[ERROR] General unexpected error in SOP generation: {e}")
        # Log traceback for unexpected errors if possible in a real logging setup
        # import traceback
        # print(traceback.format_exc())
        raise
    finally:
        # Step 13: Clean up GenAI uploaded file
        if genai_uploaded_file and hasattr(genai_uploaded_file, 'name'):
            print(f"[INFO] Final cleanup: Deleting GenAI file {genai_uploaded_file.name}...")
            try:
                await asyncio.to_thread(genai.delete_file, genai_uploaded_file.name)
                print(f"[INFO] GenAI file deleted successfully.")
            except Exception as e:
                print(f"[WARNING] Failed to delete GenAI file '{genai_uploaded_file.name}' during cleanup: {e}")
        else:
             print(f"[INFO] Final cleanup: No GenAI input file to delete or already cleaned up.")