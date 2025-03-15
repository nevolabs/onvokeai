import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from config import load_config, set_env
from models import SOPState
from parsers import parse_pdf, parse_json
from workflow import create_workflow
from rag_fetch import fetch_relevant_jira_issues

app = FastAPI()

# ✅ Load configuration
config = load_config()
set_env(config)

# ✅ Initialize workflow
workflow = create_workflow()

@app.post("/generate_sop/")
async def generate_sop_api(
    user_id: str = Form(...),
    query: str = Form(...),  
    pdf_file: UploadFile = File(...),
    event_file: UploadFile = File(...)
):
    """API endpoint to generate SOP from PDF and event JSON."""
    if not pdf_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid PDF file format")
    if not event_file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid JSON file format")

    pdf_path = f"temp_{pdf_file.filename}"
    json_path = f"temp_{event_file.filename}"

    try:
        # ✅ Step 1: Write uploaded files
        with open(pdf_path, "wb") as f:
            f.write(await pdf_file.read())
        with open(json_path, "wb") as f:
            f.write(await event_file.read())

        # ✅ Step 2: Parse the files
        pdf_text = await parse_pdf(pdf_path)
        if "Error" in pdf_text:
            raise Exception(pdf_text)
        
        event_data = await parse_json(json_path)
        if isinstance(event_data, list) and "error" in event_data[0]:
            raise Exception(event_data[0]["error"])

        # ✅ Step 3: Fetch relevant Jira issues
        relevant_issues = fetch_relevant_jira_issues(user_id, query, top_k=5)
        jira_context = "\n".join(
            [f"Issue: {issue['issue_id']}\nDetails: {issue['text_data']}" for issue in relevant_issues]
        ) if relevant_issues else "No relevant Jira issues found."

        # ✅ Step 4: Combine all into a Knowledge Base (KB)
        knowledge_base = f"""
        ### Jira Issues:
        {jira_context}
        """

        # ✅ Step 5: Initialize SOPState with the Knowledge Base
        initial_state = SOPState(KB=knowledge_base, pdf_text=pdf_text, event_data=event_data)

        # ✅ Step 6: Run workflow and ensure result is SOPState
        result = await workflow.ainvoke(initial_state)

        # ✅ Step 7: Convert result if needed
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
