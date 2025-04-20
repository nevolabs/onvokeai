
from docx import Document
from supabase import create_client
import datetime
from io import BytesIO
from models.tech_article_models import TechnicalArticle
import os


def create_docx(article: TechnicalArticle) -> BytesIO:
    """Convert TechnicalArticle model to DOCX document"""
    doc = Document()
    
    # Main Title
    doc.add_heading(article.main_title, level=0)
    
    # Introduction
    doc.add_heading(article.introduction.title, level=1)
    doc.add_paragraph(article.introduction.content)
    
    # Feature Details
    doc.add_heading(article.feature_details.title, level=1)
    for feature in article.feature_details.features:
        doc.add_heading(feature.title, level=2)
        doc.add_paragraph(feature.description)
    
    # Step-by-Step Guide
    doc.add_heading(article.step_by_step_guide.title, level=1)
    if article.step_by_step_guide.introduction:
        doc.add_paragraph(article.step_by_step_guide.introduction)
    for i, step in enumerate(article.step_by_step_guide.steps, 1):
        doc.add_paragraph(f"Step {i}:", style='ListNumber')
        doc.add_paragraph(step)
    
    # Conclusion
    doc.add_heading(article.conclusion.title, level=1)
    doc.add_paragraph(article.conclusion.content)
    
    # FAQ
    doc.add_heading(article.faq.title, level=1)
    for faq in article.faq.questions:
        doc.add_paragraph(f"Q: {faq.question}", style='ListBullet')
        doc.add_paragraph(f"A: {faq.answer}")
    
    # Save to bytes buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer