import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from dotenv import load_dotenv
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from typing import Dict, Any
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Set environment variables
os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_CLOUD_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Initialize FastAPI app
app = FastAPI()

# Initialize LlamaParse
parser = LlamaParse(result_type="markdown")

# Initialize LangChain model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7)

# Define LangGraph state using Pydantic for type safety
class SOPState(BaseModel):
    pdf_text: str = ""
    event_data: Dict[str, Any] = {}
    sop_html: str = ""

    class Config:
        arbitrary_types_allowed = True

# Workflow nodes
def parse_pdf_node(state: SOPState) -> SOPState:
    """Extract text from a PDF file using LlamaParse."""
    try:
        if not state.pdf_text:  # Only parse if not already set
            raise ValueError("PDF file path not provided in state")
        return state  # PDF parsing happens in the API endpoint
    except Exception as e:
        state.pdf_text = f"Error parsing PDF: {str(e)}"
        return state

def parse_json_node(state: SOPState) -> SOPState:
    """Load event JSON data."""
    try:
        if not state.event_data:  # Only parse if not already set
            raise ValueError("Event JSON data not provided in state")
        return state  # JSON parsing happens in the API endpoint
    except Exception as e:
        state.event_data = {"error": f"Error loading JSON: {str(e)}"}
        return state

def generate_sop_node(state: SOPState) -> SOPState:
    """Generate SOP HTML documentation."""
    try:
        combined_text = state.pdf_text
        event_text = json.dumps(state.event_data, indent=2)

        prompt = f"""
            ## Standard Operating Procedure (SOP) HTML Documentation Generator

            You are an expert HTML documentation generator. Your task is to create a professional and adaptable Standard Operating Procedure (SOP) document in HTML format, based on the information provided.

            **Desired Output:** Well-structured, visually appealing HTML code for an SOP. The HTML should be designed for easy customization and readability.

            ---

            **HTML Structure Requirements:**

            1.  **Main Title:** Use `<h1>` for the SOP's main title. (Dynamic - derived from the overall context).
            2.  **Major Sections:** Use `<h2>` for major sections (e.g., Introduction, Scope, Instructions, etc.). Section titles should be dynamically generated based on the content.
            3.  **Sub-sections:** Use `<h3>` within sections for finer detail and improved readability.
            4.  **Explanations:** Use `<p>` for detailed explanations and descriptions.
            5.  **Ordered Steps:** Use `<ol>` for step-by-step instructions, ensuring clear sequential guidance.
            6.  **Additional Information:** Use `<ul>` for supplementary information, notes, or optional details.

            ---

            **Aesthetic and Design Requirements:**

            1.  **Modern CSS Styling:** The HTML must include CSS styling (either inline or linked to an external stylesheet placeholder) to achieve a clean, modern, and visually appealing layout. The design should look professional and corporate.
            2.  **Responsive Design:** The HTML must be responsive and adapt to different screen sizes (desktop, tablet, mobile). Consider using viewport meta tags and media queries in the CSS.
            3.  **Color Theme and Typography:** Select a professional color theme and typography suitable for a corporate document. Prioritize readability and visual appeal.
            4.  **Visual Enhancements:** Include placeholders for icons (e.g., `[INSERT ICON HERE]`) within the HTML to improve visual understanding.
            5.  **Dynamic Sections:** The HTML should be structured to dynamically generate sections based on the provided content.

            ---

            **Data Inputs:**

            *   **Process Description:** `{combined_text}`
            *   **Additional Context:** `{event_text}`

            ---

            **Instructions:**

            1.  Analyze the `Process Description` and `Additional Context` to understand the process.
            2.  Dynamically create the SOP content (sections, steps, explanations) based on the provided input data.
            3.  Structure the content into valid HTML, following all the requirements outlined above.
            4.  Include CSS styling (either inline or linked to an external stylesheet placeholder) for a modern and professional look.
            5.  Ensure the HTML is well-formatted and easy to copy-paste.

            **Output:** The *complete* HTML code for the SOP. The code *must* be valid HTML and should include styling information (CSS)."""
        
        response = llm.invoke(prompt)
        state.sop_html = response.content.strip()
        return state
    except Exception as e:
        state.sop_html = f"Error generating SOP: {str(e)}"
        return state

# Define LangGraph workflow
graph = StateGraph(SOPState)
graph.add_node("parse_pdf", parse_pdf_node)
graph.add_node("parse_json", parse_json_node)
graph.add_node("generate_sop", generate_sop_node)

# Define edges
graph.add_edge("parse_pdf", "parse_json")
graph.add_edge("parse_json", "generate_sop")
graph.add_edge("generate_sop", END)

# Set entry point
graph.set_entry_point("parse_pdf")

# Compile the workflow
workflow = graph.compile()

def parse_pdf_with_llama(file_path: str) -> str:
    """Extract text from a PDF file using LlamaParse."""
    try:
        documents = SimpleDirectoryReader(input_files=[file_path], file_extractor={".pdf": parser}).load_data()
        return documents[0].text if documents else "No text extracted from PDF."
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

@app.post("/generate_sop/")
async def generate_sop_api(pdf_file: UploadFile = File(...), event_file: UploadFile = File(...)):
    """API endpoint to generate SOP from PDF and event JSON."""
    # Validate file types
    if not pdf_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid PDF file format")
    if not event_file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid JSON file format")

    # Save uploaded files temporarily
    pdf_path = f"temp_{pdf_file.filename}"
    event_path = f"temp_{event_file.filename}"

    try:
        # Write PDF file
        with open(pdf_path, "wb") as f:
            f.write(await pdf_file.read())
        
        # Write JSON file
        with open(event_path, "wb") as f:
            f.write(await event_file.read())

        # Parse PDF
        pdf_text = parse_pdf_with_llama(pdf_path)
        if "Error" in pdf_text:
            raise Exception(pdf_text)

        # Parse JSON
        with open(event_path, "r") as f:
            event_data = json.load(f)

        # Initialize state
        initial_state = SOPState(pdf_text=pdf_text, event_data=event_data)

        # Run the workflow
        result = workflow.invoke(initial_state)

        return {"sop_html": result.sop_html}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
    
    finally:
        # Clean up temporary files
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(event_path):
            os.remove(event_path)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)