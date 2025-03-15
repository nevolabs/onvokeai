from pydantic import BaseModel
from typing import List, Dict, Any

# class SOPState(BaseModel):
#     pdf_text: str = ""
#     event_data: List[Dict[str, Any]] = []  # Changed from Dict to List[Dict]
#     sop_html: str = ""

#     class Config:
#         arbitrary_types_allowed = True


from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Base class for SOP structure
class SOPSection(BaseModel):
    title: str
    content: str
    subsections: Optional[List['SOPSection']] = None  # Recursive for subsections
    steps: Optional[List[str]] = None  # Ordered steps
    additional_info: Optional[List[str]] = None  # Unordered supplementary info

# Update SOPSection to allow recursive references
SOPSection.model_rebuild()

# Main SOP structure
class SOP(BaseModel):
    main_title: str
    sections: List[SOPSection]

# State class for LangGraph
class SOPState(BaseModel):
    KB: str = ""
    pdf_text: str = ""
    event_data: List[Dict[str, Any]] = []  # Assuming event_data is a list of dicts from your JSON
    sop_json: Optional[SOP] = None  # Store the generated SOP as a Pydantic model

    class Config:
        arbitrary_types_allowed = True