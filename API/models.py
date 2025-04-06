from pydantic import BaseModel
from typing import List, Dict, Any



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


        
from pydantic import BaseModel, Field
from typing import List, Optional

# Basic section with title and content (for Introduction, Conclusion)
class ContentSection(BaseModel):
    title: str = Field(..., description="Title of the content section (e.g., 'Introduction', 'Conclusion')")
    content: str = Field(..., description="Detailed textual content for the section.")

# Structure for describing a single feature
class FeatureDetail(BaseModel):
    title: str = Field(..., description="Name or title of the specific feature.")
    description: str = Field(..., description="Detailed explanation of the feature, its purpose, and benefits. Use provided data sources extensively.")

# Structure for the main features section
class FeatureDetailsSection(BaseModel):
    title: str = Field(..., description="Title for the section detailing features (e.g., 'Key Product Features')")
    features: List[FeatureDetail] = Field(..., description="A list describing each key feature in detail.")

# Structure for the step-by-step guide
class GuideSection(BaseModel):
    title: str = Field(..., description="Title for the step-by-step guide (e.g., 'Getting Started: Step-by-Step')")
    introduction: Optional[str] = Field(None, description="Optional introductory text explaining what the guide covers.")
    steps: List[str] = Field(..., description="Ordered list of detailed steps. Must incorporate details from JSON data and visual cues from screenshots.")

# Structure for a single FAQ item
class FAQItem(BaseModel):
    question: str = Field(..., description="A likely question a user might ask.")
    answer: str = Field(..., description="The answer to the question, sourced strictly from the Knowledge Base.")

# Structure for the FAQ section
class FAQSection(BaseModel):
    title: str = Field(..., description="Title for the FAQ section (e.g., 'Frequently Asked Questions')")
    questions: List[FAQItem] = Field(..., description="A list of relevant question-answer pairs.")

# Main Technical Article structure
class TechnicalArticle(BaseModel):
    main_title: str = Field(..., description="Overall title of the technical article, reflecting the product/feature.")
    introduction: ContentSection = Field(..., description="Introduction section: General overview, product details, use case, and user benefits.")
    feature_details: FeatureDetailsSection = Field(..., description="Section detailing the product's features.")
    step_by_step_guide: GuideSection = Field(..., description="Section providing a detailed step-by-step guide.")
    conclusion: ContentSection = Field(..., description="Conclusion section: Summarizing features and their value to the customer.")
    faq: FAQSection = Field(..., description="FAQ section with questions derived from content and user journey, answers from KB.")
    
    
# State class for LangGraph
class SOPState(BaseModel):
    KB: str = ""
    pdf_text: str = ""
    user_query: str = ""
    event_data:str = ""  # Accept both list and raw string
    sop_json: Optional[TechnicalArticle] = None  # Store the generated SOP as a Pydantic model

    class Config:
        arbitrary_types_allowed = True
        
        
        