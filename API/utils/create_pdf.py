

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
from typing import List
import os 

# Function to create PDF with original names (define this in utils/create_pdf.py or here)
def create_pdf_from_screenshots(screenshot_info, output_path):
    """Create a PDF from screenshots, including original names as captions."""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    for temp_path, original_name in screenshot_info:
        try:
            img = Image.open(temp_path)
            img_width, img_height = img.size
            # Scale image to fit page, leaving space for caption
            scale = min((width - 40) / img_width, (height - 60) / img_height)
            scaled_width = img_width * scale
            scaled_height = img_height * scale
            x = (width - scaled_width) / 2  # Center horizontally
            y = (height - scaled_height) / 2  # Center vertically
            c.drawImage(temp_path, x, y, scaled_width, scaled_height)
            # Add caption below image
            c.drawString(x, y - 20, f"page_name: {original_name}")
            c.showPage()
        except Exception as e:
            print(f"[ERROR] Failed to add screenshot {original_name} to PDF: {str(e)}")
    c.save()
