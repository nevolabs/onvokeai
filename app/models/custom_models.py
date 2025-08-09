from pydantic import BaseModel, Field
from typing import List, Optional

# --- Existing Component Models ---

class ContentSection(BaseModel):
    title: Optional[str] = Field(None, description="Optional title of the content section (e.g., 'Introduction', 'Conclusion').")
    content: Optional[str] = Field(None, description="Optional detailed textual content for the section.")

class FeatureDetail(BaseModel):
    title: Optional[str] = Field(None, description="Optional name or title of the specific feature.")
    description: Optional[str] = Field(None, description="Optional detailed explanation of the feature, its purpose, and benefits.")

class FeaturesSection(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the section detailing features (e.g., 'Key Product Features').")
    features: List[FeatureDetail] = Field(default_factory=list, description="Optional list describing each key feature in detail.")

class TableOfContents(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the table of contents (e.g., 'Table of Contents').")
    items: List[str] = Field(default_factory=list, description="Optional list of section titles or headings for navigation.")

class Note(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the note.")
    content: Optional[str] = Field(None, description="Optional content of the note, providing additional information or context.")

class CodeSnippet(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the code snippet.")
    language: Optional[str] = Field(None, description="Optional programming language of the code (e.g., 'python', 'javascript').")
    code: Optional[str] = Field(None, description="Optional actual code content.")

class Image(BaseModel):
    title: Optional[str] = Field(None, description="Optional title or caption for the image.")
    url: Optional[str] = Field(None, description="Optional URL or path to the image.")
    alt_text: Optional[str] = Field(None, description="Optional alternative text for accessibility.")

class Quote(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the quote.")
    content: Optional[str] = Field(None, description="Optional quoted text.")
    author: Optional[str] = Field(None, description="Optional author or source of the quote.")

class Checklist(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the checklist (e.g., 'Requirements Checklist').")
    items: List[str] = Field(default_factory=list, description="Optional list of checklist items.")

class StepsSection(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the step-by-step guide (e.g., 'Getting Started: Step-by-Step').")
    introduction: Optional[str] = Field(None, description="Optional introductory text explaining what the guide covers.")
    steps: List[str] = Field(default_factory=list, description="Optional ordered list of detailed steps.")

class FAQItem(BaseModel):
    question: Optional[str] = Field(None, description="Optional likely question a user might ask.")
    answer: Optional[str] = Field(None, description="Optional answer to the question.")

class FAQSection(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the FAQ section (e.g., 'Frequently Asked Questions').")
    questions: List[FAQItem] = Field(default_factory=list, description="Optional list of relevant question-answer pairs.")

class Callout(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the callout or tip.")
    content: Optional[str] = Field(None, description="Optional content of the callout or tip, highlighting important information.")

class References(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the references section (e.g., 'References').")
    sources: List[str] = Field(default_factory=list, description="Optional list of reference sources or citations.")

# --- NEW Component Models ---

class AlertBox(BaseModel):
    style: Optional[str] = Field("Info", description="Style of the alert: Info, Success, Warning, or Danger.")
    content: Optional[str] = Field(None, description="The message text inside the alert box.")

class CallToAction(BaseModel):
    text: Optional[str] = Field(None, description="The button text for the call-to-action (e.g., 'Sign Up Now').")
    href: Optional[str] = Field(None, description="The destination URL for the call-to-action button.")

class DecisionPoint(BaseModel):
    if_condition: Optional[str] = Field(None, description="The condition for the decision, e.g., 'If you are an Admin'.")
    then_steps: List[str] = Field(default_factory=list, description="Steps to follow if the condition is true.")
    else_steps: List[str] = Field(default_factory=list, description="Optional steps to follow if the condition is false.")

class ExpandableSection(BaseModel):
    title: Optional[str] = Field(None, description="The visible title of the expandable section.")
    content: List[str] = Field(default_factory=list, description="The hidden content that is revealed on expansion.")

class ExpectedResult(BaseModel):
    text: Optional[str] = Field(None, description="A description of the expected outcome after a step, e.g., 'A \"Success\" message appears.'")

class GlossaryItem(BaseModel):
    term: Optional[str] = Field(None, description="The key term to be defined.")
    definition: Optional[str] = Field(None, description="The definition of the term.")

class GlossarySection(BaseModel):
    title: Optional[str] = Field("Glossary", description="Title for the glossary section.")
    items: List[GlossaryItem] = Field(default_factory=list, description="List of terms and their definitions.")

class ProcessMapStage(BaseModel):
    stage: Optional[str] = Field(None, description="The name of the stage in the process.")
    details: Optional[str] = Field(None, description="A brief description of what happens in this stage.")

class ProcessMapSection(BaseModel):
    title: Optional[str] = Field("Process Overview", description="Title for the process map section.")
    stages: List[ProcessMapStage] = Field(default_factory=list, description="List of stages in the process.")

class Table(BaseModel):
    title: Optional[str] = Field(None, description="Optional title or caption for the table.")
    headers: List[str] = Field(default_factory=list, description="The header row for the table.")
    rows: List[List[str]] = Field(default_factory=list, description="The data rows, where each row is a list of cell strings.")


# --- Main Technical Article Structure (Updated) ---

class CustomTechnicalArticle(BaseModel):
    # Existing Fields
    title: Optional[str] = Field(None, description="Optional main title of the technical article.")
    subtitle: Optional[str] = Field(None, description="Optional subtitle for the article.")
    table_of_contents: Optional[TableOfContents] = Field(None, description="Optional table of contents.")
    introduction: Optional[ContentSection] = Field(None, description="Optional introduction section.")
    features: Optional[FeaturesSection] = Field(None, description="Optional section detailing features.")
    paragraphs: List[ContentSection] = Field(default_factory=list, description="Optional list of paragraph sections.")
    notes: List[Note] = Field(default_factory=list, description="Optional list of informational notes.")
    code_snippets: List[CodeSnippet] = Field(default_factory=list, description="Optional list of code snippets.")
    images: List[Image] = Field(default_factory=list, description="Optional list of images.")
    quotes: List[Quote] = Field(default_factory=list, description="Optional list of quotes.")
    checklists: List[Checklist] = Field(default_factory=list, description="Optional list of checklists.")
    steps: Optional[StepsSection] = Field(None, description="Optional step-by-step guide.")
    faq: Optional[FAQSection] = Field(None, description="Optional FAQ section.")
    callouts: List[Callout] = Field(default_factory=list, description="Optional list of callouts or tips.")
    
    # NEW Fields
    alert_boxes: List[AlertBox] = Field(default_factory=list, description="Optional list of styled alert boxes.")
    ctas: List[CallToAction] = Field(default_factory=list, description="Optional list of call-to-action buttons.")
    decision_points: List[DecisionPoint] = Field(default_factory=list, description="Optional list of decision points for workflows.")
    expandable_sections: List[ExpandableSection] = Field(default_factory=list, description="Optional list of collapsible sections.")
    expected_results: List[ExpectedResult] = Field(default_factory=list, description="Optional list of expected result descriptions.")
    glossary: Optional[GlossarySection] = Field(None, description="Optional glossary section for defining key terms.")
    process_map: Optional[ProcessMapSection] = Field(None, description="Optional section for visualizing a process.")
    tables: List[Table] = Field(default_factory=list, description="Optional list of data tables.")
    
    # Existing Fields
    conclusion: Optional[ContentSection] = Field(None, description="Optional conclusion section.")
    references: Optional[References] = Field(None, description="Optional references section.")
