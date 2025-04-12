# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.output_parsers import JsonOutputParser
# from langchain.prompts import PromptTemplate
# from models import TechnicalArticle
# import json
# from pydantic import ValidationError
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.prompts import PromptTemplate
# from typing import Dict, Any,List
# import json
# from pydantic import ValidationError
# from prompts.technical_article_prompt import prompt_template
# import os
# import base64

# # Initialize LLM
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0)

# async def generate_sop_html(KB: str,file_path: str, pdf_text: str, event_data:str , user_query: str) -> Dict[str, Any]:
#     """Generate SOP documentation and return validated JSON dict."""
#     try:
#         combined_text = pdf_text
#         event_text = event_data
        
#         # Save inputs locally for testing
#         os.makedirs("debug_inputs", exist_ok=True)
#         with open("debug_inputs/combined_text.txt", "w", encoding="utf-8") as f:
#             f.write(combined_text)
#         with open("debug_inputs/event_data.json", "w", encoding="utf-8") as f:
#             f.write(event_text)

#         # Define parser with your Pydantic model
#         parser = JsonOutputParser(pydantic_object=TechnicalArticle)

#         prompt = PromptTemplate(
#         template=prompt_template,
#         input_variables=["combined_text", "event_text", "KB", "user_query", "format_instructions"],
#         partial_variables={"format_instructions": parser.get_format_instructions()}
#     )

#         # Create and run the chain
#         chain = prompt | llm | parser
#         json_output = await chain.ainvoke({
#             "combined_text": combined_text,
#             "event_text": event_text,
#             "KB": KB,
#             "user_query": user_query,
#         })

#         # Validate the structure by creating the model (but return the dict)
#         TechnicalArticle(**json_output)
#         return json_output

#     except ValidationError as e:
#         error_details = []
#         for err in e.errors():
#             loc = "->".join(str(x) for x in err["loc"])
#             error_details.append(f"{loc}: {err['msg']}")
#         raise ValueError(f"Validation error:\n" + "\n".join(error_details))
        
#     except Exception as e:
#         raise ValueError(f"Error generating SOP: {str(e)}")
    
    
    
    
    
import google.generativeai as genai
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from models import TechnicalArticle
from pydantic import ValidationError
from prompts.technical_article_prompt import get_prompt
import os
import asyncio

# Configure the GenAI client (ensure GOOGLE_API_KEY is set in your environment)
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro")  # Use an appropriate model that supports file inputs

async def generate_sop_html(KB: str, file_path: str, pdf_text: str, event_data: str, user_query: str):
    """Generate SOP documentation and return validated JSON dict using GenAI client."""
    try:
        # Define the parser with the TechnicalArticle Pydantic model
        parser = JsonOutputParser(pydantic_object=TechnicalArticle)
        format_instructions = parser.get_format_instructions()

        # Save inputs locally for debugging (optional)
        os.makedirs("debug_inputs", exist_ok=True)
        with open("debug_inputs/event_data.json", "w", encoding="utf-8") as f:
            f.write(event_data)
        with open("debug_inputs/user_query.txt", "w", encoding="utf-8") as f:
            f.write(user_query)

        # Upload the PDF file using GenAI File API (synchronous call, run in thread)
        file = await asyncio.to_thread(genai.upload_file, path=file_path, display_name="SOP_PDF", mime_type="application/pdf")
        file_uri = file.uri

        prompt = get_prompt(
            KB=KB,
            event_text=event_data,
            user_query=user_query,
            format_instructions=format_instructions
        )

        # Generate content using GenAI client (synchronous call, run in thread)
        response = await asyncio.to_thread(
            model.generate_content,
            contents=[
                {"role": "user", "parts": [
                    {"text": prompt},
                    {"file_data": {"file_uri": file_uri, "mime_type": "application/pdf"}}
                ]}
            ],
            generation_config={"temperature": 0}
        )

        # Extract the response text
        response_text = response.text  # Assumes response has a 'text' attribute

        # Parse and validate the output
        json_output = parser.parse(response_text)
        TechnicalArticle(**json_output)  # Additional validation
        return json_output

    except ValidationError as e:
        error_details = [f"{'->'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()]
        raise ValueError(f"Validation error:\n" + "\n".join(error_details))
    
    except Exception as e:
        raise ValueError(f"Error generating SOP: {str(e)}")
    
    finally:
        # Clean up: Delete the uploaded file (optional)
        if 'file' in locals():
            await asyncio.to_thread(genai.delete_file, file.name)