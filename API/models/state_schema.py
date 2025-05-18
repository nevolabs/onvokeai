# File: models.py  
from pydantic import BaseModel, Field
from typing import List, Optional , Dict

# State class for LangGraph
class SOPState(BaseModel):
    KB: str = ""
    file_path: str = ""
    user_query: str = ""
    event_data:str = ""  # Accept both list and raw string
    user_id: str = ""
    job_id: str = ""
    components: Optional[Dict] = None 
    category_name: str = ""

    class Config:
        arbitrary_types_allowed = True
        
        
        