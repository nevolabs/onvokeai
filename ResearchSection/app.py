import os
from dotenv import load_dotenv
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader
import json
from langchain_openai import ChatOpenAI  
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI


# Load environment variables
load_dotenv()

os.environ["OPENAI_API_KEY"]= os.getenv("OPENAI_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"]=os.getenv("LLAMA_CLOUD_API_KEY")
os.environ["GROQ_API_KEY"]  = os.getenv("GROQ_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Set up LlamaParse
parser = LlamaParse(
    result_type="markdown"  
)



# Set up LangChain OpenAI
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp", 
    temperature=0.7
)

def parse_screenshot(image_path):
    
    try:
        file_extractor = {".png": parser, ".jpg": parser, ".jpeg": parser}  
        documents = SimpleDirectoryReader(input_files=[image_path], file_extractor=file_extractor).load_data()
        print(documents[0].text)
        return documents[0].text if documents else "No text extracted from image."
    except Exception as e:
        print(f"Error parsing {image_path}: {e}")
        return None

def load_event_json(json_path):
    
    try:
        with open(json_path, 'r') as file:
            event_data = json.load(file)
        return event_data
    except Exception as e:
        print(f"Error loading {json_path}: {e}")
        return None

def generate_sop_doc(parsed_data, event_data):
    
    try:
        # Combine parsed data and event data into a prompt
        combined_text = "\n\n".join(parsed_data)
        event_text = json.dumps(event_data, indent=2)
        
        prompt = f"""
            ## Standard Operating Procedure (SOP) HTML Documentation Generator

            You are an expert HTML documentation generator. Your task is to create a professional and adaptable Standard Operating Procedure (SOP) document in HTML format, based on the information provided.

            **Desired Output:** Well-structured, visually appealing HTML code for an SOP. The HTML should be designed for easy customization and readability.

            ---

            **HTML Structure Requirements:**

            1.  **Main Title:** Use `<h1>` for the SOP's main title. (Dynamic - derived from the overall context).
            2.  **Major Sections:** Use `<h2>` for major sections (e.g., Introduction, Scope, Instructions, etc.). Section titles should be dynamically generated based on the content.
            3.  **Sub-sections:** Use `<h3>` within sections for finer detail and improved readability.
            4.  **Explanations:** Use `<p>` for detailed explanations and descriptions.
            5.  **Ordered Steps:** Use `<ol>` for step-by-step instructions, ensuring clear sequential guidance.
            6.  **Additional Information:** Use `<ul>` for supplementary information, notes, or optional details.

            ---

            **Aesthetic and Design Requirements:**

            1.  **Modern CSS Styling:** The HTML must include CSS styling (either inline or, preferably, linked to an external stylesheet placeholder) to achieve a clean, modern, and visually appealing layout. The design should look professional and corporate.

            2.  **Responsive Design:** The HTML must be responsive and adapt to different screen sizes (desktop, tablet, mobile). Consider using viewport meta tags and media queries in the CSS.

            3.  **Color Theme and Typography:** Select a professional color theme and typography suitable for a corporate document. Prioritize readability and visual appeal.

            4.  **Visual Enhancements:** Include placeholders for icons (e.g., `[INSERT ICON HERE]`) within the HTML to improve visual understanding. These are placeholders; do not generate actual icons.

            5.  **Dynamic Sections:** The HTML should be structured to dynamically generate sections based on the provided content.

            6.  **Enhancements for Engagement:** Consider incorporating elements like:
                *   Hover effects (using CSS).
                *   Strategic spacing and typography choices to improve readability.
                *   Expandable sections (using JavaScript/CSS - optional, but desirable).
                *   Collapsible FAQs (using JavaScript/CSS - optional, but desirable).
                *   A dark/light mode switch (using JavaScript/CSS - optional, but desirable).

            7.  **Copy-Paste Friendliness:** Ensure the HTML is structured in a way that allows it to be easily copy-pasted into various documentation systems (e.g., Confluence, SharePoint). This means clean, well-formatted code with no unnecessary dependencies.

            ---

            **Example SOP Outline (Guide - content should be dynamically generated):**

            1.  **Introduction:**
                *   Purpose of the SOP.
                *   Who should use it.

            2.  **Scope:**
                *   Areas covered by the SOP.
                *   Roles and responsibilities.

            3.  **Step-by-Step Instructions:**
                *   (Dynamically Generated based on process description)
                *   Example:

                    ```html
                    <h2>Logging into the System</h2>
                    <p>Follow these steps to securely log in:</p>
                    <ol>
                        <li>Open your browser and go to the login page.</li>
                        <li>Enter your username and password.</li>
                        <li>Click on the "Sign In" button.</li>
                    </ol>
                    ```

            4.  **Compliance and Best Practices:**
                *   Legal or policy-related guidelines.

            5.  **Troubleshooting and Support:**
                *   FAQs or common issues.

            ---

            **Data Inputs:**

            *   **Process Description:** `{combined_text}`
            *   **Additional Context:** `{event_text}`

            ---

            **Instructions:**

            1.  Analyze the `Process Description` and `Additional Context` to understand the process.
            2.  Dynamically create the SOP content (sections, steps, explanations) based on the provided input data.
            3.  Structure the content into valid HTML, following all the requirements outlined above.
            4.  Include CSS styling (either inline or linked to an external stylesheet placeholder) for a modern and professional look.
            5.  Ensure the HTML is well-formatted and easy to copy-paste.

            **Output:** The *complete* HTML code for the SOP. The code *must* be valid HTML and should include styling information (CSS). Be sure to include placeholders where appropriate (e.g., for the stylesheet and images). The output should be directly usable. The goal is a functioning basic SOP that can be further customized with specific content in the placeholders."""
        # Use LangChain's OpenAI to generate SOP documentation
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"Error generating SOP documentation: {e}")
        return ""

def save_html_to_file(html_content, output_file):

    try:
        with open(output_file, 'w') as file:
            file.write(html_content)
        print(f"SOP documentation saved to {output_file}")
    except Exception as e:
        print(f"Error saving HTML file: {e}")

def main():
    # Directory containing screenshots
    screenshot_dir = "Screenshots" 
    event_json_path = "events.json"  

    parsed_data = []

    for filename in os.listdir(screenshot_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            screenshot_path = os.path.join(screenshot_dir, filename)
            
            # Parse the screenshot using LlamaParse
            parsed_text =parse_screenshot(screenshot_path)
            if parsed_text:
                parsed_data.append(parsed_text)

    event_data = load_event_json(event_json_path)

    sop_html = generate_sop_doc(parsed_data, event_data)

    output_file = "output.html"
    save_html_to_file(sop_html, output_file)

if __name__ == "__main__":
    main()