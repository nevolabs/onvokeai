from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from models import SOP
import json

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7)

async def generate_sop_html(pdf_text: str, event_data: dict) -> SOP:
    """Generate SOP JSON documentation using Pydantic parser."""
    try:
        combined_text = pdf_text
        event_text = json.dumps(event_data, indent=2)

        # Define parser
        parser = PydanticOutputParser(pydantic_object=SOP)

        # Define prompt correctly
        prompt = PromptTemplate(
            template="""
            You are an expert in creating structured Standard Operating Procedures (SOPs).
            Generate a JSON output containing a structured SOP with:
            - `main_title`: Main title of the SOP.
            - `sections`: A list of sections, each containing:
              - `title`: Section title.
              - `content`: Explanation.
              - `subsections` (optional): List of subsections.
              - `steps` (optional): Ordered list of steps.
              - `additional_info` (optional): List of extra notes.

            Ensure the output follows this structure strictly.

            Input Data:
            - **Process Description:** {combined_text}
            - **Additional Context:** {event_text}

            Output JSON must follow this schema:
            {format_instructions}
            """,
            input_variables=["combined_text", "event_text", "format_instructions"],
        )

        # Format the prompt with instructions from the parser
        prompt_text = prompt.format(
            combined_text=combined_text,
            event_text=event_text,
            format_instructions=parser.get_format_instructions(),
        )

        # Invoke LLM and parse response
        response = await llm.ainvoke(prompt_text)
        parsed_response = parser.parse(response.content)

        return parsed_response

    except Exception as e:
        raise ValueError(f"Error generating SOP: {str(e)}")
