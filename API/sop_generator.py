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

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7)

async def generate_sop_html(KB: str, pdf_text: str, event_data: dict) -> Dict[str, Any]:
    """Generate SOP documentation and return validated JSON dict."""
    try:
        combined_text = pdf_text
        event_text = json.dumps(event_data, indent=2)

        # Define parser with your Pydantic model
        parser = JsonOutputParser(pydantic_object=TechnicalArticle)

        # Define prompt template
        prompt = PromptTemplate(
        template="""
        You are an expert technical writer specializing in creating detailed, customer-facing articles about SaaS products.
        Generate a JSON output containing a structured Technical Article based on the provided data.

        **Your Goal:** Create a comprehensive and highly detailed technical article explaining a SaaS product's features and usage. This document is for customers, so clarity, accuracy, and thoroughness are paramount. Do NOT hallucinate; use only the provided data sources.

        **Input Data:**
        - **Product/Feature Description (JSON/Text):** {combined_text}  (Use for Introduction, Features, Steps)
        - **Context/Use Case Data:** {event_text} (Use for Introduction, context in Features/Steps, Conclusion)
        - **Knowledge Base:** {KB} (Use STRICTLY for generating answers in the FAQ section. May also inform other sections if relevant facts are present.)

        **Output JSON Structure:**
        Generate a JSON object that strictly adheres to the following structure:
        1.  `main_title`: Overall title for the technical article.
        2.  `introduction`:
            - `title`: "Introduction"
            - `content`: Generalized overview based on input data. Include product details, primary use case, and how it benefits users.
        3.  `feature_details`:
            - `title`: e.g., "Key Features"
            - `features`: A list, where each item describes ONE feature:
                - `title`: Name of the feature.
                - `description`: DETAILED explanation of the feature, drawing heavily from `{combined_text}`. Explain what it does and why it's useful.
        4.  `step_by_step_guide`:
            - `title`: e.g., "Step-by-Step Guide: Using [Feature Name]"
            - `introduction` (optional): Brief text explaining the goal of the steps.
            - `steps`: An ordered list of DETAILED steps. Primary source is `{combined_text}` (if it contains procedural info), for precise actions, UI elements to click/interact with, expected outcomes, and minor visual details. Make each step explicit and easy to follow.
        5.  `conclusion`:
            - `title`: "Conclusion"
            - `content`: Summarize the key features discussed and reiterate their value and usefulness for the customer based on the provided context and descriptions.
        6.  `faq`:
            - `title`: "Frequently Asked Questions"
            - `questions`: A list of relevant questions a user might have after reading the article. Formulate questions based on the content and the likely user journey.
                - `question`: The user's potential question.
                - `answer`: The answer, derived EXCLUSIVELY from the `{KB}` (Knowledge Base). If the KB doesn't cover a potential question, do not include that question-answer pair.

        Ensure maximum detail in all content fields. The final output MUST be a valid JSON object conforming to the schema below.

        Output JSON Schema:
        {format_instructions}

        JSON Output:
        """,
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