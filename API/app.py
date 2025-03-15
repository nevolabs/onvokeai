import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from config import load_config, set_env
from models import SOPState
from parsers import parse_pdf, parse_json
from workflow import create_workflow

app = FastAPI()

# Load configuration
config = load_config()
set_env(config)

# Initialize workflow
workflow = create_workflow()

@app.post("/generate_sop/")
async def generate_sop_api(pdf_file: UploadFile = File(...), event_file: UploadFile = File(...)):
    """API endpoint to generate SOP from PDF and event JSON."""
    if not pdf_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid PDF file format")
    if not event_file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid JSON file format")

    pdf_path = f"temp_{pdf_file.filename}"
    json_path = f"temp_{event_file.filename}"

    try:
        # Write uploaded files
        with open(pdf_path, "wb") as f:
            f.write(await pdf_file.read())
        with open(json_path, "wb") as f:
            f.write(await event_file.read())

        # Parse files in the API
        pdf_text = await parse_pdf(pdf_path)
        if "Error" in pdf_text:
            raise Exception(pdf_text)
        
        event_data = await parse_json(json_path)
        if isinstance(event_data, list) and "error" in event_data[0]:
            raise Exception(event_data[0]["error"])

        # Initialize state with parsed data
        initial_state = SOPState(pdf_text=pdf_text, event_data=event_data)

        # Run workflow and ensure result is SOPState
        result = await workflow.ainvoke(initial_state)

        # Check if result is a dict (AddableValuesDict) and convert to SOPState if needed
        if isinstance(result, dict):
            result = SOPState(**result)

        return {"sop_json": result.sop_json}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
    
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(json_path):
            os.remove(json_path)

    
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

