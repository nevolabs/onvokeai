import google.generativeai as genai
from app.prompts.technical_article_prompt import get_prompt
import os
import asyncio
import json
from supabase import create_client, Client
from io import BytesIO
from datetime import datetime, timezone
import mimetypes
from PyPDF2 import PdfReader
from google.generativeai.types import GenerationConfig
from app.services.file_services.markdownit import create_markdown
from app.services.file_services.pdf_validator import validate_pdf_file
from app.core.initializers import get_genai_model, get_supabase_client, get_file_mime_type, is_magic_available
from app.config.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Get initialized services from the centralized manager
model = get_genai_model()
MAGIC_AVAILABLE = is_magic_available()

# Note: get_file_mime_type is now imported from centralizers
# No need to redefine it here - using the centralized version

async def generate_sop_docx(
    KB: str,
    file_path: str,
    event_data: str,
    user_query: str,
    user_id: str,
    job_id: str,
    components: dict, # This is now loaded from generation.json
    category_name: str = "",
    contents: str = ""
) -> dict:
    """
    Generates an SOP, stores the Markdown output in a Supabase table.
    Saves model's raw JSON output and generated Markdown locally if SAVE_DEBUG_OUTPUT=true.
    """
    
    # Load the generation schema (components) from the JSON file
    # This schema is used for GenAI response structuring and title extraction
    article_dict = None
    genai_uploaded_file = None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_dir = "debug_output"
    save_debug = os.environ.get("SAVE_DEBUG_OUTPUT", "false").lower() == "true"

    if save_debug:
        logger.info(f"Debug output saving is ENABLED. Files will be saved to '{debug_dir}'.")
        try:
            os.makedirs(debug_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create debug directory '{debug_dir}': {e}")
            save_debug = False # Disable if directory creation fails

    try:
        components_schema = components
        # Step 1: Validate Input Schema (already loaded as components_schema)
        if not components_schema or not isinstance(components_schema, dict):
             raise ValueError("[ERROR] Invalid or missing 'components_schema' from 'generation.json'. Expected a dictionary.")
        logger.info("Components schema from 'generation.json' appears valid.")

        # Step 2: Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("[ERROR] SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment.")
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized.")

        # Step 3: Define Generation Config using the loaded schema
        logger.info("Defining GenerationConfig with response_schema from 'generation.json'")
        try:
            generation_config = GenerationConfig(
                temperature=0, # For deterministic output
                response_mime_type="application/json",
                response_schema=components_schema
            )
        except Exception as e:
            logger.error(f"Failed to create GenerationConfig with schema: {e}")
            logger.debug(f"Schema used was: {components_schema}")
            raise ValueError(f"Invalid components_schema structure for GenerationConfig: {e}")

        # Step 4: Validate the PDF file
        logger.info(f"Validating PDF file: {file_path}")
        validate_pdf_file(file_path)

        # Step 5: Upload the PDF file via GenAI File API
        logger.info(f"Uploading PDF to GenAI: {file_path}")
        try:
            # Use asyncio.to_thread for blocking I/O in async function
            genai_uploaded_file = await asyncio.to_thread(
                genai.upload_file, path=file_path, display_name=f"SOP_PDF_{job_id}", mime_type="application/pdf"
            )
            file_uri = genai_uploaded_file.uri
            logger.info(f"PDF uploaded to GenAI. URI: {file_uri}")
        except Exception as e:
            logger.error(f"GenAI PDF upload failed: {e}")
            raise ValueError(f"GenAI PDF upload failed: {e}")

        # Step 6: Prepare prompt
        logger.info("Generating prompt...")
        schema_json_str = json.dumps(components_schema, indent=2) # Use 2 spaces for less verbose debug output
        prompt = get_prompt(
            KB=KB,
            event_text=event_data,
            user_query=user_query,
            contents=contents,
            generation_schema_str=schema_json_str 
        )
        
        # prompt = "created a technical article based on the following PDF file. The article should be structured according to the provided JSON schema. The PDF file is attached as a file input. Please ensure that the generated content adheres to the schema and is relevant to the content of the PDF."
        # logger.debug(f"Generated prompt: {prompt[:500]}...")  # Optionally log part of the prompt

        # Step 7: Generate content using GenAI client with schema config
        logger.info("Generating content with JSON schema enforcement...")
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
                logger.debug(f"Generated content: {response_text[:500]}...")  # Optionally log
                
            logger.info(f"Content generation successful. JSON response received: {response_text[:100]}")  # Log first 100 chars of response for debugging
            if not response_text:
                raise ValueError("Model response text is empty. Cannot parse.")
            if save_debug:
                try:
                    json_filename_debug = f"job_{job_id}_{timestamp}_model_output.json"
                    json_filepath_debug = os.path.join(debug_dir, json_filename_debug)
                    with open(json_filepath_debug, "w", encoding="utf-8") as f:
                        f.write(response_text)
                    logger.info(f"Saved raw model JSON output to {json_filepath_debug}")
                except Exception as debug_e:
                    logger.warning(f"Failed to save raw model output for debugging: {debug_e}")

        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            # Log more details if available from the GenAI exception
            if hasattr(e, 'response') and e.response:
                 if hasattr(e.response, 'parts'): logger.debug(f"Model response parts: {e.response.parts}")
                 if hasattr(e.response, 'candidates') and e.response.candidates:
                     logger.debug(f"Model candidate finish reason: {e.response.candidates[0].finish_reason}")
                     if e.response.candidates[0].finish_reason.name == 'OTHER':
                         logger.warning("Finish reason 'OTHER' often indicates a schema mismatch or internal model error. Check 'generation.json' against model output capabilities.")
            raise ValueError(f"Content generation failed: {e}")

        # Step 8: Parse/Validate the JSON output
        logger.info("Validating JSON response structure...")
        try:
            if response_text is None:
                raise ValueError("Model response text is None. Cannot parse.")
            article_dict = json.loads(response_text)
            if not isinstance(article_dict, dict): # Top level of schema should be an object
                raise ValueError("Parsed JSON is not a dictionary as expected by the top-level schema.")
            logger.info("Successfully parsed and validated JSON response structure.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}. Response text was: {response_text[:500]}...")
            raise ValueError(f"Model did not return valid JSON: {e}")
        except Exception as e: # Catch other validation errors
            logger.error(f"Error processing/validating JSON response: {e}")
            raise ValueError(f"Error processing/validating JSON response: {e}")

        # Step 9: Generate Markdown from the validated JSON
        logger.info("Generating Markdown document from JSON...")
        try:
            # create_markdown function is expected to take the dictionary and return a BytesIO buffer
            markdown_buffer = create_markdown(article_dict,user_id ,job_id) 
            markdown_content = markdown_buffer.getvalue().decode('utf-8')
            logger.info("Markdown generation successful.")
            
            if save_debug:
                try:
                    md_filename_debug = f"job_{job_id}_{timestamp}_output.md"
                    md_filepath_debug = os.path.join(debug_dir, md_filename_debug)
                    with open(md_filepath_debug, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    logger.info(f"Saved Markdown output to {md_filepath_debug}")
                except Exception as debug_e:
                    logger.warning(f"Failed to save Markdown output for debugging: {debug_e}")
                    
        except Exception as e:
            logger.error(f"Markdown generation failed: {e}")
            raise ValueError(f"Markdown generation failed: {e}")

        # Step 10: Extract title and prepare data for database
        logger.info("Preparing data for database insertion...")
        try:
            # Extract title from the article_dict.
            # This assumes 'title' is a key in the root of the JSON structure defined in 'generation.json'.
            # Adjust `article_dict.get('title')` if the title is nested, e.g., `article_dict.get('metadata', {}).get('title')`.
            sop_title = article_dict.get('docTitle',"SOP") 
            if not sop_title:
                logger.warning("'title' not found in generated JSON. Using a default title.")
                sop_title = f"Generated SOP for Job {job_id} - {timestamp}"
            
            # Data to be inserted into the 'generated_docs' table
            # Fields: user_id, title, content, category, desc (created_at and id are auto-managed by Supabase)
            logger.debug(f"Markdown content preview: {markdown_content[:100]}...")
            db_record = {
                "id": job_id,  # Use job_id as the primary key
                "category": category_name,
                "user_id": user_id,
                "title": sop_title,
                "content": markdown_content, # Storing the full markdown text
                "desc": article_dict.get('shortDescription', ''),
            }

        except Exception as e:
            logger.error(f"Failed to prepare data for database: {e}")
            raise ValueError(f"Failed to prepare data for database: {e}")

        # Step 11: Insert/Update data into Supabase table 'generated_docs' with upsert functionality
        logger.info("Inserting/updating document into Supabase table 'generated_docs'...")
        try:
            # Add current timestamp for created_at field
            current_timestamp = datetime.now(timezone.utc).isoformat()
            
            # Use Supabase upsert functionality instead of manual check-then-update
            # This is atomic and handles race conditions better
            upsert_data = {
                **db_record,
                "created_at": current_timestamp  # Update created_at on both insert and update
            }
            
            logger.info(f"Performing upsert for record with ID {job_id}...")
            insert_response = supabase.table("generated_docs").upsert(
                upsert_data,
                on_conflict="id"  # Specify the conflict column
            ).execute()

            if not insert_response.data or len(insert_response.data) == 0:
                error_message = "Unknown error during Supabase operation."
                if hasattr(insert_response, 'error') and insert_response.error:
                    error_message = f"Supabase error: {insert_response.error.message if hasattr(insert_response.error, 'message') else insert_response.error}"
                elif hasattr(insert_response, 'status_code') and insert_response.status_code not in [200, 201]:
                     error_message = f"Supabase operation failed with status {insert_response.status_code}."
                     try:
                         error_details = insert_response.json()
                         error_message += f" Details: {error_details}"
                     except: # if .json() fails
                         error_message += " Could not parse error response body."
                
                logger.error(error_message)
                raise ValueError(f"Failed to save document to Supabase table. {error_message}")

            inserted_doc = insert_response.data[0]
            inserted_doc_id = inserted_doc.get('id', job_id) # Use job_id as fallback
            logger.info(f"Document successfully saved to 'generated_docs'. ID: {inserted_doc_id}")

        except Exception as e:
            logger.error(f"Supabase table operation failed: {e}")
            # Avoid logging full db_record.content if it's very large in production logs
            logger.debug(f"Failed to save record (title: {db_record.get('title')}, user_id: {db_record.get('user_id')})")
            raise ValueError(f"Supabase table operation failed: {e}")

        # Step 12: Return success response
        return {
            "status": "success",
            "message": "SOP generated and stored successfully in the database.",
            "document_id": job_id,  # Always return job_id as document_id for consistency
            "title": sop_title,
            "user_id": user_id,
            "job_id": job_id, # Still useful to return job_id for context
            "timestamp": timestamp # Generation timestamp
        }

    except ValueError as e: # Catch specific, anticipated errors
        logger.error(f"Value error during SOP generation: {e}")
        # Potentially re-raise with more context or a custom exception type
        raise
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"General unexpected error in SOP generation: {e}")
        # Log traceback for unexpected errors if possible in a real logging setup
        # import traceback
        # logger.debug(traceback.format_exc())
        raise
    finally:
        # Step 13: Clean up GenAI uploaded file
        if genai_uploaded_file and hasattr(genai_uploaded_file, 'name'):
            logger.info(f"Final cleanup: Deleting GenAI file {genai_uploaded_file.name}...")
            try:
                await asyncio.to_thread(genai.delete_file, genai_uploaded_file.name)
                logger.info("GenAI file deleted successfully.")
            except Exception as e:
                logger.warning(f"Failed to delete GenAI file '{genai_uploaded_file.name}' during cleanup: {e}")
        else:
             logger.info("Final cleanup: No GenAI input file to delete or already cleaned up.")