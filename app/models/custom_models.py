from pydantic import BaseModel, Field
from typing import List, Optional

# Generic section for textual content (used for Introduction, Conclusion, Paragraph)
class ContentSection(BaseModel):
    title: Optional[str] = Field(None, description="Optional title of the content section (e.g., 'Introduction', 'Conclusion').")
    content: Optional[str] = Field(None, description="Optional detailed textual content for the section.")

# Structure for describing a single feature
class FeatureDetail(BaseModel):
    title: Optional[str] = Field(None, description="Optional name or title of the specific feature.")
    description: Optional[str] = Field(None, description="Optional detailed explanation of the feature, its purpose, and benefits.")

# Structure for the features section
class FeaturesSection(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the section detailing features (e.g., 'Key Product Features').")
    features: List[FeatureDetail] = Field(default_factory=list, description="Optional list describing each key feature in detail.")

# Structure for table of contents
class TableOfContents(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the table of contents (e.g., 'Table of Contents').")
    items: List[str] = Field(default_factory=list, description="Optional list of section titles or headings for navigation.")

# Structure for a note
class Note(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the note.")
    content: Optional[str] = Field(None, description="Optional content of the note, providing additional information or context.")

# Structure for a code snippet
class CodeSnippet(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the code snippet.")
    language: Optional[str] = Field(None, description="Optional programming language of the code (e.g., 'python', 'javascript').")
    code: Optional[str] = Field(None, description="Optional actual code content.")

# Structure for an image
class Image(BaseModel):
    title: Optional[str] = Field(None, description="Optional title or caption for the image.")
    url: Optional[str] = Field(None, description="Optional URL or path to the image.")
    alt_text: Optional[str] = Field(None, description="Optional alternative text for accessibility.")

# Structure for a quote
class Quote(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the quote.")
    content: Optional[str] = Field(None, description="Optional quoted text.")
    author: Optional[str] = Field(None, description="Optional author or source of the quote.")

# Structure for a checklist
class Checklist(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the checklist (e.g., 'Requirements Checklist').")
    items: List[str] = Field(default_factory=list, description="Optional list of checklist items.")

# Structure for a step-by-step guide
class StepsSection(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the step-by-step guide (e.g., 'Getting Started: Step-by-Step').")
    introduction: Optional[str] = Field(None, description="Optional introductory text explaining what the guide covers.")
    steps: List[str] = Field(default_factory=list, description="Optional ordered list of detailed steps.")

# Structure for a single FAQ item
class FAQItem(BaseModel):
    question: Optional[str] = Field(None, description="Optional likely question a user might ask.")
    answer: Optional[str] = Field(None, description="Optional answer to the question.")

# Structure for the FAQ section
class FAQSection(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the FAQ section (e.g., 'Frequently Asked Questions').")
    questions: List[FAQItem] = Field(default_factory=list, description="Optional list of relevant question-answer pairs.")

# Structure for a callout or tip
class Callout(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the callout or tip.")
    content: Optional[str] = Field(None, description="Optional content of the callout or tip, highlighting important information.")

# Structure for references
class References(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the references section (e.g., 'References').")
    sources: List[str] = Field(default_factory=list, description="Optional list of reference sources or citations.")

# Main Technical Article structure
class CustomTechnicalArticle(BaseModel):
    title: Optional[str] = Field(None, description="Optional main title of the technical article, reflecting the product/feature.")
    subtitle: Optional[str] = Field(None, description="Optional subtitle for the article.")
    table_of_contents: Optional[TableOfContents] = Field(None, description="Optional table of contents listing sections.")
    introduction: Optional[ContentSection] = Field(None, description="Optional introduction section with general overview and benefits.")
    features: Optional[FeaturesSection] = Field(None, description="Optional section detailing the product's features.")
    paragraphs: List[ContentSection] = Field(default_factory=list, description="Optional list of additional paragraph sections.")
    notes: List[Note] = Field(default_factory=list, description="Optional list of informational notes.")
    code_snippets: List[CodeSnippet] = Field(default_factory=list, description="Optional list of code snippets.")
    images: List[Image] = Field(default_factory=list, description="Optional list of images.")
    quotes: List[Quote] = Field(default_factory=list, description="Optional list of quotes.")
    checklists: List[Checklist] = Field(default_factory=list, description="Optional list of checklists.")
    steps: Optional[StepsSection] = Field(None, description="Optional section providing a detailed step-by-step guide.")
    faq: Optional[FAQSection] = Field(None, description="Optional FAQ section with question-answer pairs.")
    callouts: List[Callout] = Field(default_factory=list, description="Optional list of callouts or tips.")
    conclusion: Optional[ContentSection] = Field(None, description="Optional conclusion section summarizing features and value.")
    references: Optional[References] = Field(None, description="Optional references section with sources.")