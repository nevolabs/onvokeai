import os
import re
from pathlib import Path
from typing import Optional
import asyncio
import concurrent.futures
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.models.state_schema import SOPState
from app.utils.json_parser import parse_json
from app.workflow import create_workflow
from app.services.rag_services.rag import fetch_relevant_issues
from app.services.file_services.create_pdf import create_pdf_from_screenshots
from app.services.file_services.pdf_converter import convert_to_pdf
from app.services.file_services.docx_converter import convert_to_docx
from app.services.file_services.file_readers import read_excel_file, read_pdf_file, read_docx_file
from app.core.database import get_supabase_client
from app.config.logging import get_logger
from app.utils.download_screenshot import download_screenshot
from app.utils.update_status import update_document_status

from langchain_google_genai import ChatGoogleGenerativeAI

# Initialize logger
logger = get_logger(__name__)

# Create router
router = APIRouter()

# Initialize workflow
workflow = create_workflow()

@router.post("/generate")
async def generate_sop_api(
    file: Optional[UploadFile] = File(None),
    user_id: str = Form(...),
    job_id: str = Form(...),
    query: str = Form(...),
    templates_id: str = Form(...),
    integration_type: str = Form(...),
):
    """
    API endpoint to generate SOP using a component schema defined
    in a user-specific template (from JSONB).
    Updates the status in the generated_docs table.
    """
    temp_files = []
    screenshot_info = []
    full_component_schema: Optional[dict] = None
    contents = b""
    if file is not None:
        contents = await file.read()
    supabase = get_supabase_client()

    try:
        logger.debug(f"Starting SOP generation for user_id={user_id}, job_id={job_id}, template_id='{templates_id}', integration_type='{integration_type}'")

        # --- Initialize Record with 'pending' Status ---
        logger.info(f"Initializing generated_docs record with status='pending' for job_id={job_id}")
        try:
            supabase.table("generated_docs").upsert(
                {"id": job_id, "user_id": user_id, "status": "pending"},
                on_conflict="id"
            ).execute()
            logger.info(f"Initialized generated_docs record for job_id={job_id}")
        except Exception as e:
            logger.error(f"Failed to initialize generated_docs record: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize document record: {str(e)}")

        # --- Fetch Template Components Schema from Supabase ---
        try:
            logger.debug(f"Fetching template components schema for template_id={templates_id}, user_id={user_id}")
            response = supabase.table('templates') \
                             .select('components','name') \
                             .eq('id', templates_id) \
                             .eq('user_id', user_id) \
                             .maybe_single() \
                             .execute()

            logger.debug(f"Supabase template query response: {response}")
            logger.debug(f"Supabase template query response data: {getattr(response, 'data', None)}")

            if response and hasattr(response, 'data') and response.data and 'components' in response.data:
                full_component_schema = response.data['components']
                category_name = response.data.get('name', 'SOP')
            else:
                logger.info(f"Template not found in private table. Checking 'publictemplates' table.")
                public_response = supabase.table('publictemplates') \
                                        .select('components, name') \
                                        .eq('id', templates_id) \
                                        .maybe_single() \
                                        .execute()
                
                logger.debug(f"Supabase public template query response: {public_response}")
                logger.debug(f"Supabase public template query response data: {getattr(public_response, 'data', None)}")
                
                if public_response and hasattr(public_response, 'data') and public_response.data and 'components' in public_response.data:
                    full_component_schema = public_response.data['components']
                    category_name = public_response.data.get('name', 'SOP')
                    logger.info(f"Template found in publictemplates table for template_id={templates_id}")
                else:
                    logger.error(f"No components found for template_id={templates_id} in both private and public tables")
                    update_document_status(supabase, job_id, "failed")
                    raise HTTPException(status_code=404, detail="Template not found or no components available")

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to fetch template schema: {str(e)}")
            update_document_status(supabase, job_id, "failed")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve template schema: {str(e)}")

        # --- File Processing ---
        storage = supabase.storage.from_('log_dataa')
        json_directory = f"{user_id}/{job_id}/json"
        screenshots_directory = f"{user_id}/{job_id}/screenshots"
        logger.debug(f"JSON Directory: {json_directory}")
        logger.debug(f"Screenshot Directory: {screenshots_directory}")

        try:
            json_files = storage.list(json_directory)
            screenshot_files = storage.list(screenshots_directory)
            logger.debug(f"Found JSON files: {len(json_files) if json_files else 0}")
            logger.debug(f"Found screenshot files: {len(screenshot_files) if screenshot_files else 0}")
        except Exception as e:
            logger.error(f"Failed to list storage directories: {str(e)}")
            update_document_status(supabase, job_id, "failed")
            raise HTTPException(status_code=404, detail=f"Storage paths not found: {str(e)}")

        if not json_files and not screenshot_files:
            update_document_status(supabase, job_id, "failed")
            raise HTTPException(status_code=404, detail="No JSON or screenshot files found")

        # Process uploaded file content based on file type
        if file is not None:
            file_extension = Path(file.filename).suffix.lower()
            if file_extension in ['.xlsx', '.xls']:
                uploaded_file_content = read_excel_file(contents)
            elif file_extension == '.pdf':
                uploaded_file_content = read_pdf_file(contents)
            elif file_extension == '.docx':
                uploaded_file_content = read_docx_file(contents)
        else:
            uploaded_file_content = ""

        # Process screenshots in parallel
        if screenshot_files:
            logger.info(f"Starting parallel download of {len(screenshot_files)} screenshots...")
            download_tasks = []
            for file in screenshot_files:
                file_name = file.get('name')
                if file_name and file_name.lower().endswith(('.png', '.jpg', '.jpeg')) and file_name != '.emptyFolderPlaceholder':
                    full_path = f"{screenshots_directory}/{file_name}"
                    safe_local_name = file_name.replace('/', '_').replace('\\', '_')
                    temp_path = f"temp_{user_id}_{job_id}_{safe_local_name}"
                    task = download_screenshot(storage, full_path, temp_path, file_name)
                    download_tasks.append(task)
            
            max_concurrent_downloads = 10
            semaphore = asyncio.Semaphore(max_concurrent_downloads)
            
            async def bounded_download(task):
                async with semaphore:
                    return await task
            
            logger.debug(f"Processing {len(download_tasks)} screenshot downloads with max concurrency of {max_concurrent_downloads}")
            results = await asyncio.gather(*[bounded_download(task) for task in download_tasks], return_exceptions=True)
            
            successful_downloads = 0
            for result in results:
                if isinstance(result, tuple) and result is not None:
                    temp_path, file_name = result
                    screenshot_info.append((temp_path, file_name))
                    temp_files.append(temp_path)
                    successful_downloads += 1
                elif isinstance(result, Exception):
                    logger.error(f"Download task failed with exception: {str(result)}")
            
            logger.info(f"Completed parallel downloads: {successful_downloads}/{len(download_tasks)} successful")

        # Process JSON file
        json_path = None
        json_file_name_to_process = None
        if json_files:
            for file in json_files:
                file_name = file.get('name')
                if file_name and file_name.lower().endswith('.json') and file_name != '.emptyFolderPlaceholder':
                    json_path = f"{json_directory}/{file_name}"
                    json_file_name_to_process = file_name
                    logger.debug(f"JSON file selected: {json_path}")
                    break

        if not screenshot_info: 
            update_document_status(supabase, job_id, "failed")
            raise HTTPException(status_code=404, detail="No valid screenshot files found")
        if not json_path: 
            update_document_status(supabase, job_id, "failed")
            raise HTTPException(status_code=404, detail="No JSON file found in storage")

        # Create PDF
        pdf_temp_path = f"temp_{user_id}_{job_id}_generated.pdf"
        try:
            logger.debug(f"Creating PDF: {pdf_temp_path}")
            if not screenshot_info: 
                raise ValueError("No screenshots for PDF")
            create_pdf_from_screenshots(screenshot_info, pdf_temp_path)
            temp_files.append(pdf_temp_path)
            logger.debug("PDF created")
        except Exception as e:
            logger.error(f"Failed to create PDF: {str(e)}")
            update_document_status(supabase, job_id, "failed")
            raise HTTPException(status_code=500, detail=f"Failed to create PDF: {str(e)}")

        # Process JSON data
        try:
            safe_json_filename = re.sub(r'[^\w\-_.]', '_', json_file_name_to_process)
            short_json_filename = safe_json_filename[:50] + Path(safe_json_filename).suffix
            json_temp_path = f"temp_{user_id}_{job_id}_{short_json_filename}"
            
            logger.debug(f"Downloading event JSON: {json_path}")
            json_response = storage.download(json_path)
            if not isinstance(json_response, bytes):
                logger.error(f"Failed download event JSON: {json_file_name_to_process}")
                update_document_status(supabase, job_id, "failed")
                raise HTTPException(status_code=500, detail="Failed to download event JSON data")
            with open(json_temp_path, "wb") as f: 
                f.write(json_response)
            temp_files.append(json_temp_path)
            logger.debug(f"Saved temp event JSON: {json_temp_path}")
            event_data = await parse_json(json_temp_path)
            logger.debug(f"Parsed event data type: {type(event_data)}")
            if not event_data: 
                update_document_status(supabase, job_id, "failed")
                raise HTTPException(status_code=400, detail="No valid event data parsed")
            if isinstance(event_data, list) and event_data and isinstance(event_data[0], dict) and "error" in event_data[0]:
                update_document_status(supabase, job_id, "failed")
                raise Exception(f"Event JSON parsing error: {event_data[0]['error']}")
        except HTTPException as he: 
            raise he
        except Exception as e:
            logger.error(f"Event JSON processing failed: {str(e)}")
            update_document_status(supabase, job_id, "failed")
            raise HTTPException(status_code=500, detail=f"Event JSON processing failed: {str(e)}")

        # --- Fetch RAG Context ---
        rag_context = f"{integration_type.capitalize()} context unavailable."
        try:
            logger.debug(f"Fetching relevant issues for query: {query}, integration_type: {integration_type}")
            if integration_type:
                relevant_issues = fetch_relevant_issues(user_id, query, integration_type, top_k=5)
                if relevant_issues:
                    rag_context = "\n".join([
                        f"{integration_type.capitalize()} Item: {issue.get('issue_id', 'N/A')}\nDetails: {issue.get('text_data', 'N/A')}" 
                        for issue in relevant_issues
                    ])
                else: 
                    rag_context = f"No relevant {integration_type} items found."
            logger.debug("Fetched RAG context")
        except Exception as e:
            logger.warning(f"Error fetching {integration_type} issues: {str(e)}")
            rag_context = f"Error fetching {integration_type} issues: {str(e)}"

        # --- Prepare and Invoke Workflow ---
        knowledge_base = f"### Relevant {integration_type.capitalize()} Content:\n{rag_context}\n"
        logger.debug("Prepared knowledge base")

        result = None
        try:
            logger.debug("Invoking workflow with component schema...")
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
            logger.debug("SOP workflow completed")
            logger.debug(f"SOP result type: {type(result)}")

            # --- Verify Status After Workflow ---
            # Since generate_sop_docx updates status to 'success', verify it
            response = supabase.table('generated_docs').select('status').eq('id', job_id).single().execute()
            if response.data and response.data.get('status') != 'success':
                logger.warning(f"Workflow completed but status is {response.data.get('status')} for job_id={job_id}")
                update_document_status(supabase, job_id, "success")

        except Exception as e:
            logger.error(f"SOP workflow failed: {str(e)}")
            update_document_status(supabase, job_id, "failed")
            raise HTTPException(status_code=500, detail=f"SOP generation workflow failed: {str(e)}")

        # --- Return Success Response ---
        return {
            "status": "success",
            "result": result,
            "metadata": {
                "user_id": user_id,
                "job_id": job_id,
                "template_id": templates_id,
                "integration_type": integration_type,
                "files_processed": len(screenshot_info) + 1,
                "components_schema_used": full_component_schema
            }
        }

    except HTTPException as he:
        logger.error(f"HTTP Error - Status: {he.status_code}, Detail: {he.detail}")
        update_document_status(supabase, job_id, "failed")
        raise he
    except Exception as e:
        logger.error(f"Fatal unexpected error: {str(e)}")
        update_document_status(supabase, job_id, "failed")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        # --- Cleanup Temporary Files ---
        logger.debug(f"Cleaning up {len(temp_files)} temporary files...")
        cleaned_count = 0
        for temp_file in temp_files:
            try:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Temp file cleanup failed for {temp_file}: {str(e)}")
        logger.debug(f"Cleanup finished. Removed {cleaned_count} files.")
        
@router.post("/rephrase")
async def rephrase_markdown(
    query: str = Form(...),
    markdown_text: str = Form(...),
    text_to_update: str = Form(...),
    job_id: Optional[str] = Form(None)
):
    """
    API endpoint to rephrase a specific section of a markdown string using Google Gemini via LangChain,
    based on the user query, returning only the updated section and job_id.
    """
    try:
        logger.debug(f"Rephrasing markdown section for job_id={job_id if job_id else 'None'}")

        # Validate inputs
        if not markdown_text or not text_to_update or not query:
            raise HTTPException(status_code=400, detail="Query, markdown text, and section to update are required")
        
        # Check if text_to_update exists in markdown_text
        if text_to_update not in markdown_text:
            raise HTTPException(status_code=400, detail="Specified section not found in the markdown text")

        # Initialize Google Gemini model
        try:
            gemini_model = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",  # Updated to a valid model name
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google Gemini model: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Model initialization failed: {str(e)}")

        # Create LangChain prompt
        prompt = rephrase_prompt_template.format(
            query=query,
            markdown_text=markdown_text,
            text_to_update=text_to_update
        )

        # Invoke Google Gemini model
        try:
            response = gemini_model.invoke(prompt)
            rephrased_section = response.content if hasattr(response, 'content') else str(response)
            logger.debug(f"Rephrasing successful for job_id={job_id if job_id else 'None'}")
        except Exception as e:
            logger.error(f"Failed to rephrase with Gemini: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Rephrasing failed: {str(e)}")

        # Log the rephrase action if job_id is provided
        if job_id:
            logger.info(f"Section rephrased for job_id={job_id}, original section: {text_to_update[:50]}...")

        return {
            "rephrased_section": rephrased_section,
            "job_id": job_id
        }

    except HTTPException as he:
        logger.error(f"HTTP Error - Status: {he.status_code}, Detail: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in rephrase: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")



@router.post("/download")
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


