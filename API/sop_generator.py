from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from models import TechnicalArticle
import json
from pydantic import ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from typing import Dict, Any
import json
from pydantic import ValidationError
from prompts.technical_article_prompt import TechnicalArticlePrompt
# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7)

async def generate_sop_html(KB: str, pdf_text: str, event_data: dict) -> Dict[str, Any]:
    """Generate SOP documentation and return validated JSON dict."""
    try:
        combined_text = pdf_text
        event_text = json.dumps(event_data, indent=2)

        # Define parser with your Pydantic model
        parser = JsonOutputParser(pydantic_object=TechnicalArticle)

        prompt = PromptTemplate(
        template=TechnicalArticlePrompt,
        input_variables=["combined_text", "event_text", "KB", "format_instructions"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

        # Create and run the chain
        chain = prompt | llm | parser
        json_output = await chain.ainvoke({
            "combined_text": combined_text,
            "event_text": event_text,
            "KB": KB
        })

        # Validate the structure by creating the model (but return the dict)
        TechnicalArticle(**json_output)
        return json_output

    except ValidationError as e:
        error_details = []
        for err in e.errors():
            loc = "->".join(str(x) for x in err["loc"])
            error_details.append(f"{loc}: {err['msg']}")
        raise ValueError(f"Validation error:\n" + "\n".join(error_details))
        
    except Exception as e:
        raise ValueError(f"Error generating SOP: {str(e)}")
    
    
    
    
    
    