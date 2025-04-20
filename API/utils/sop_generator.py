import google.generativeai as genai
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from models.tech_article_models import TechnicalArticle
from pydantic import ValidationError
from prompts.technical_article_prompt import get_prompt
import os
import asyncio
from utils.docx_converter import create_docx
from supabase import create_client
from io import BytesIO
import datetime

# Configure GenAI
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro")

async def generate_sop_docx(
    KB: str, 
    file_path: str, 
    event_data: str, 
    user_query: str,
    user_id: str,
    job_id: str
) -> dict:
    """Generate SOP documentation as DOCX and store in Supabase with path logdata/userid/jobid/"""
    try:
        # Initialize Supabase client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
        
        # Define the parser with the TechnicalArticle Pydantic model
        parser = JsonOutputParser(pydantic_object=TechnicalArticle)
        format_instructions = parser.get_format_instructions()

        # Upload the PDF file using GenAI File API
        file = await asyncio.to_thread(
            genai.upload_file, 
            path=file_path, 
            display_name="SOP_PDF", 
            mime_type="application/pdf"
        )
        file_uri = file.uri

        prompt = get_prompt(
            KB=KB,
            event_text=event_data,
            user_query=user_query,
            format_instructions=format_instructions
        )

        # Generate content using GenAI client
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

        # Parse and validate the output
        json_output = parser.parse(response.text)
        article = TechnicalArticle(**json_output)  # Additional validation
        
        # Create DOCX file
        doc_buffer = create_docx(article)
        
        # Generate storage path and filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sop_{timestamp}.docx"
        storage_path = f"logdata/{user_id}/{job_id}/{filename}"
        
        # Upload to Supabase storage
        upload_response = supabase.storage.from_("log_data").upload(
            path=storage_path,
            file=doc_buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # Get public URL
        download_url = supabase.storage.from_("log_data").get_public_url(storage_path)
        
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
        raise ValueError(f"Validation error:\n" + "\n".join(error_details))
    
    except Exception as e:
        raise ValueError(f"Error generating or storing SOP: {str(e)}")
    
    finally:
        # Clean up: Delete the uploaded file
        if 'file' in locals():
            await asyncio.to_thread(genai.delete_file, file.name)