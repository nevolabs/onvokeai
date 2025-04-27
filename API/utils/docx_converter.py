from docx import Document
import datetime
from io import BytesIO
from models.custom_models import CustomTechnicalArticle as TechnicalArticle
import os
from docx import Document
import datetime
from io import BytesIO

def create_docx(article: TechnicalArticle) -> BytesIO:
    """Convert TechnicalArticle model to DOCX document"""
    doc = Document()

    # Title (check if present and non-empty)
    if article.title and article.title.strip():
        doc.add_heading(article.title, level=0)

    # Subtitle (optional)
    if article.subtitle and article.subtitle.strip():
        doc.add_heading(article.subtitle, level=1)

    # Table of Contents (optional)
    if article.table_of_contents and article.table_of_contents.items:
        doc.add_heading(article.table_of_contents.title, level=1)
        for item in article.table_of_contents.items:
            doc.add_paragraph(item, style='List Bullet')

    # Introduction (check if present and has content)
    if article.introduction and article.introduction.content and article.introduction.content.strip():
        doc.add_heading(article.introduction.title or "Introduction", level=1)
        doc.add_paragraph(article.introduction.content)

    # Features (check if present and has features)
    if article.features and article.features.features:
        doc.add_heading(article.features.title, level=1)
        for feature in article.features.features:
            doc.add_heading(feature.title, level=2)
            doc.add_paragraph(feature.description)

    # Paragraphs (optional list)
    if article.paragraphs:
        for paragraph in article.paragraphs:
            if paragraph.content and paragraph.content.strip():
                if paragraph.title and paragraph.title.strip():
                    doc.add_heading(paragraph.title, level=2)
                doc.add_paragraph(paragraph.content)

    # Notes (optional list)
    if article.notes:
        for note in article.notes:
            if note.content and note.content.strip():
                doc.add_heading(note.title or "Note", level=2)
                doc.add_paragraph(note.content, style='Intense Quote')

    # Code Snippets (optional list)
    if article.code_snippets:
        for snippet in article.code_snippets:
            if snippet.code and snippet.code.strip():
                if snippet.title and snippet.title.strip():
                    doc.add_heading(snippet.title, level=2)
                doc.add_paragraph(f"Language: {snippet.language}")
                doc.add_paragraph(snippet.code, style='No Spacing')

    # Images (optional list)
    if article.images:
        for image in article.images:
            if image.url and image.url.strip():
                if image.title and image.title.strip():
                    doc.add_heading(image.title, level=2)
                doc.add_paragraph(f"Image: {image.url} (Alt: {image.alt_text})")

    # Quotes (optional list)
    if article.quotes:
        for quote in article.quotes:
            if quote.content and quote.content.strip():
                if quote.title and quote.title.strip():
                    doc.add_heading(quote.title, level=2)
                doc.add_paragraph(quote.content, style='Quote')
                if quote.author and quote.author.strip():
                    doc.add_paragraph(f"— {quote.author}")

    # Checklists (optional list)
    if article.checklists:
        for checklist in article.checklists:
            if checklist.items:
                doc.add_heading(checklist.title, level=2)
                for item in checklist.items:
                    if item.strip():
                        doc.add_paragraph(item, style='List Bullet')

    # Steps / How-To (check if present and has steps)
    if article.steps and article.steps.steps:
        doc.add_heading(article.steps.title, level=1)
        if article.steps.introduction and article.steps.introduction.strip():
            doc.add_paragraph(article.steps.introduction)
        for i, step in enumerate(article.steps.steps, 1):
            if step.strip():
                doc.add_paragraph(f"Step {i}:", style='List Number')
                doc.add_paragraph(step, style='List Paragraph')

    # FAQ (check if present and has questions)
    if article.faq and article.faq.questions:
        doc.add_heading(article.faq.title, level=1)
        for faq in article.faq.questions:
            if faq.question.strip() and faq.answer.strip():
                doc.add_paragraph(f"Q: {faq.question}", style='List Bullet')
                doc.add_paragraph(f"A: {faq.answer}", style='List Paragraph')

    # Callouts / Tips (optional list)
    if article.callouts:
        for callout in article.callouts:
            if callout.content and callout.content.strip():
                doc.add_heading(callout.title or "Tip", level=2)
                doc.add_paragraph(callout.content, style='Intense Quote')

    # Conclusion (check if present and has content)
    if article.conclusion and article.conclusion.content and article.conclusion.content.strip():
        doc.add_heading(article.conclusion.title or "Conclusion", level=1)
        doc.add_paragraph(article.conclusion.content)

    # References (optional)
    if article.references and article.references.sources:
        doc.add_heading(article.references.title, level=1)
        for source in article.references.sources:
            if source.strip():
                doc.add_paragraph(source, style='List Bullet')

    # Save to bytes buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer