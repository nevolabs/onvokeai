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
from app.utils.update_status import update_document_status
# Initialize logger for this module
logger = get_logger(__name__)

# Get initialized services from the centralized manager
model = get_genai_model()
MAGIC_AVAILABLE = is_magic_available()

async def generate_sop_docx(
    KB: str,
    file_path: str,
    event_data: str,
    user_query: str,
    user_id: str,
    job_id: str,
    components: dict,
    category_name: str = "",
    contents: str = ""
) -> dict:
    """
    Generates an SOP, stores the Markdown output in a Supabase table.
    Saves model's raw JSON output and generated Markdown locally if SAVE_DEBUG_OUTPUT=true.
    Updates the status column to 'success' or 'failed' based on the outcome.
    """
    
    # Initialize variables
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
            save_debug = False

    # Initialize Supabase client
    logger.info("Initializing Supabase client...")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("[ERROR] SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment.")
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized.")

    try:
        components_schema = components
        # Step 1: Validate Input Schema
        if not components_schema or not isinstance(components_schema, dict):
            raise ValueError("[ERROR] Invalid or missing 'components_schema' from 'generation.json'. Expected a dictionary.")
        logger.info("Components schema from 'generation.json' appears valid.")

        # Step 2: Define Generation Config
        logger.info("Defining GenerationConfig with response_schema from 'generation.json'")
        try:
            generation_config = GenerationConfig(
                temperature=0,
                response_mime_type="application/json",
                response_schema=components_schema
            )
        except Exception as e:
            logger.error(f"Failed to create GenerationConfig with schema: {e}")
            logger.debug(f"Schema used was: {components_schema}")
            raise ValueError(f"Invalid components_schema structure for GenerationConfig: {e}")

        # Step 3: Validate the PDF file
        logger.info(f"Validating PDF file: {file_path}")
        validate_pdf_file(file_path)

        # Step 4: Upload the PDF file via GenAI File API
        logger.info(f"Uploading PDF to GenAI: {file_path}")
        try:
            genai_uploaded_file = await asyncio.to_thread(
                genai.upload_file, path=file_path, display_name=f"SOP_PDF_{job_id}", mime_type="application/pdf"
            )
            file_uri = genai_uploaded_file.uri
            logger.info(f"PDF uploaded to GenAI. URI: {file_uri}")
        except Exception as e:
            logger.error(f"GenAI PDF upload failed: {e}")
            update_document_status(supabase, job_id, "failed")
            raise ValueError(f"GenAI PDF upload failed: {e}")

        # Step 5: Prepare prompt
        logger.info("Generating prompt...")
        schema_json_str = json.dumps(components_schema, indent=2)
        prompt = get_prompt(
            KB=KB,
            event_text=event_data,
            user_query=user_query,
            contents=contents,
            generation_schema_str=schema_json_str 
        )

        # Step 6: Generate content
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
            response_text = response.text
            with open("output.json", "w", encoding="utf-8") as f:
                f.write(response_text)
            logger.info(f"Content generation successful. JSON response received: {response_text[:100]}")
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
            update_document_status(supabase, job_id, "failed")
            raise ValueError(f"Content generation failed: {e}")

        # Step 7: Parse/Validate the JSON output
        logger.info("Validating JSON response structure...")
        try:
            if response_text is None:
                raise ValueError("Model response text is None. Cannot parse.")
            article_dict = json.loads(response_text)
            if not isinstance(article_dict, dict):
                raise ValueError("Parsed JSON is not a dictionary as expected by the top-level schema.")
            logger.info("Successfully parsed and validated JSON response structure.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}. Response text was: {response_text[:500]}...")
            update_document_status(supabase, job_id, "failed")
            raise ValueError(f"Model did not return valid JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing/validating JSON response: {e}")
            update_document_status(supabase, job_id, "failed")
            raise ValueError(f"Error processing/validating JSON response: {e}")

        # Step 8: Generate Markdown
        logger.info("Generating Markdown document from JSON...")
        try:
            markdown_buffer = create_markdown(article_dict, user_id, job_id)
            markdown_content = markdown_buffer.getvalue().decode('utf-8')
            logger.info("Markdown generation successful.")
            logger.debug(f"Generated Markdown content: {markdown_content[:500]}...")
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
            update_document_status(supabase, job_id, "failed")
            raise ValueError(f"Markdown generation failed: {e}")

        # Step 9: Extract title and prepare data for database
        logger.info("Preparing data for database insertion...")
        try:
            sop_title = article_dict.get('docTitle', "SOP")
            if not sop_title:
                logger.warning("'title' not found in generated JSON. Using a default title.")
                sop_title = f"Generated SOP for Job {job_id} - {timestamp}"
            
            db_record = {
                "id": job_id,
                "category": category_name,
                "user_id": user_id,
                "title": sop_title,
                "content": markdown_content,
                "desc": article_dict.get('shortDescription', ''),
                "status": "success"  # Explicitly set status to 'success'
            }
        except Exception as e:
            logger.error(f"Failed to prepare data for database: {e}")
            update_document_status(supabase, job_id, "failed")
            raise ValueError(f"Failed to prepare data for database: {e}")

        # Step 10: Insert/Update data into Supabase table
        logger.info("Inserting/updating document into Supabase table 'generated_docs'...")
        try:
            current_timestamp = datetime.now(timezone.utc).isoformat()
            upsert_data = {
                **db_record,
                "created_at": current_timestamp
            }
            
            logger.info(f"Performing upsert for record with ID {job_id}...")
            insert_response = supabase.table("generated_docs").upsert(
                upsert_data,
                on_conflict="id"
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
                    except:
                        error_message += " Could not parse error response body."
                
                logger.error(error_message)
                update_document_status(supabase, job_id, "failed")
                raise ValueError(f"Failed to save document to Supabase table. {error_message}")

            inserted_doc = insert_response.data[0]
            inserted_doc_id = inserted_doc.get('id', job_id)
            logger.info(f"Document successfully saved to 'generated_docs'. ID: {inserted_doc_id}")

        except Exception as e:
            logger.error(f"Supabase table operation failed: {e}")
            update_document_status(supabase, job_id, "failed")
            raise ValueError(f"Supabase table operation failed: {e}")

        # Step 11: Return success response
        return {
            "status": "success",
            "message": "SOP generated and stored successfully in the database.",
            "document_id": job_id,
            "title": sop_title,
            "user_id": user_id,
            "job_id": job_id,
            "timestamp": timestamp
        }

    except ValueError as e:
        logger.error(f"Value error during SOP generation: {e}")
        update_document_status(supabase, job_id, "failed")
        raise
    except Exception as e:
        logger.error(f"General unexpected error in SOP generation: {e}")
        update_document_status(supabase, job_id, "failed")
        raise
    finally:
        # Step 12: Clean up GenAI uploaded file
        if genai_uploaded_file and hasattr(genai_uploaded_file, 'name'):
            logger.info(f"Final cleanup: Deleting GenAI file {genai_uploaded_file.name}...")
            try:
                await asyncio.to_thread(genai.delete_file, genai_uploaded_file.name)
                logger.info("GenAI file deleted successfully.")
            except Exception as e:
                logger.warning(f"Failed to delete GenAI file '{genai_uploaded_file.name}' during cleanup: {e}")
        else:
            logger.info("Final cleanup: No GenAI input file to delete or already cleaned up.")