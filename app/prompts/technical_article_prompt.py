import json # Import json library if not already imported

def get_prompt(user_query: str, event_text: str, KB: str,contents:str, generation_schema_str: str):
   

    prompt_start = f"""
            You are an expert technical writer creating an **extremely detailed and comprehensive**, customer-facing technical article in response to a specific user query. Your absolute priority is accuracy and including **all relevant details** from the provided application data and the PDF document, while ensuring the output is **general and reusable**, NOT specific to the demo session data.

            **Core Task:** Generate a technical article in JSON format that directly and exhaustively addresses the **User Query** :`{user_query}`. Base the article on synthesizing information from **both** the Event Log and the PDF document according to the priorities below. The final JSON output must strictly adhere to the provided "JSON Output Schema Definition". **You MUST generate a JSON object that includes ALL properties defined in the comprehensive schema provided below (including sections like "Title", "Subtitle", "Introduction", "Features", "Table of Contents", "Paragraph", "Note", "Code Snippet", "Quote", "Checklist", "FAQ", "Steps / How-To", "Callout / Tip", "Conclusion", and "References"). Ensure all string values are properly quoted and escaped.**

            **Input Roles & Usage - CRITICAL PRIORITIES & DETAIL LEVEL:**
            *   **User Query:** The driving context. Frame the entire article, including the 'Title' field, to fully answer this query. The 'Title' field (as defined in the schema) should be a concise, human-readable summary of the article's purpose, directly related to the User Query.
            *   **PDF Document (Primary Source 1 - HIGHEST PRIORITY for UI Elements, Names, Locations, Appearance, and Image References):** This is the definitive source for:
                *   **Completeness of UI Elements:** Identify **ALL** UI elements (fields, buttons, sections, labels, checkboxes, links, etc.) relevant to the task described in the user query as shown in the PDF.
                *   **Exact User-Visible Names/Labels:** Use the precise text labels for all UI elements exactly as they appear in the PDF.
                *   **Visual Appearance & Context:** Describe placeholder text, associated icons, section headings, and overall layout context visible in the PDF.
                *   **Specific Locations:** Identify the location of elements (e.g., 'in the left navigation sidebar', 'within the Pricing section') **whenever** clearly identifiable in the PDF.
                *   **Image References:**
                    *   For the `"Steps / How-To"` section, if a step has an associated image in the PDF, populate the `screenshotRef` field within that step's item with the **image filename** (e.g., "figure1.png", "step2_image.jpg") as identifiable from the PDF (e.g., from a caption or by its content).
                    *   For other sections in the schema that have a top-level `screenshot` field (e.g., `Introduction.screenshot`, `Features.screenshot`), if a general, relevant image for that entire section is clearly identifiable in the PDF, populate this `screenshot` field with the corresponding **image filename**. If no such general image exists for a section, this optional field can be omitted or be an empty string if the schema requires the key.
                *   **IMPORTANT:** Do not extract raw filenames or file metadata from the PDF to include directly in output fields like 'Title' or descriptive text unless the schema explicitly asks for such file metadata (like for `screenshotRef` or `screenshot` fields).
            *   **Event/User Action Log (Primary Source 2 - HIGHEST PRIORITY for Sequence of *Interacted* Steps for the "Steps / How-To" section):** Use this JSON data **only** to determine the **exact sequence of actions performed** by the user on the UI elements.
                *   The `"Steps / How-To"` section in the output JSON should be derived from this log. Follow this sequence strictly.
                *   Use the technical identifiers (tag, id, classList) *only* for cross-referencing with the PDF to confirm which element was interacted with, but **do not include these technical IDs in the output.**
                *   **CRITICAL: ABSOLUTELY DO NOT use the specific *data values* (names, emails, product titles, prices, specific addresses, numbers typed, lists of filenames, etc.) entered or selected during the session, or derived from file metadata, as examples or content in your output. This is especially true for fields like 'Title'.**
            *   **Integration & Exhaustiveness (Internal Processing):**
                *   **Feature Details & Other Sections:** Internally identify and understand **ALL relevant UI elements and information from the PDF** to populate all sections of the schema (e.g., "Features", "Introduction", "Note", "Callout / Tip", etc.). Use generic examples if illustrating data entry.
                *   **Sequence of Actions/Steps (for "Steps / How-To"):** Internally map out the sequence of actions from the **Event Log**. Each described action or step must use the **exact UI element name/label from the PDF** and specify its **location (if clearly identified in the PDF)**. Describe the interaction (click, enter text, select checkbox). **Use only generic examples** for any data entry descriptions.
            *   **Use Generic Examples ONLY - ABSOLUTELY CRITICAL:** (This section remains excellent, no changes needed)
                *   **DO NOT USE the specific data values recorded in the Event/User Action Log...**
                *   **When describing actions involving data entry... MUST use generic, non-identifiable examples...**
                *   **Acceptable generic placeholders...**
            *   **Handling Specific Interactions (like Autocomplete):** (Good as is)
            *   **General Applicability & Professional Tone:** (Good as is)
            *   **Knowledge Base (Supplementary Source - VERY LOW PRIORITY):** (Good as is)

            **CRITICAL Instructions Specific to JSON Output Fields:**
            *   **'Title' Field:** (Good as is)
            *   **General Field Content:** (Good as is)

            **CRITICAL Instructions (General):**
            *   **PDF is King for UI Details & Image References:** Prioritize the PDF for element names, the complete list of relevant elements, appearance, locations, and identifying image filenames for `screenshotRef` and `screenshot` fields.
            *   **Log is King for Sequence (for "Steps / How-To"):** Prioritize the Event Log *only* for the sequence of interacted steps for the `"Steps / How-To"` section.
            *   **No Demo Data Values or Filenames in Output Fields (except for designated screenshot fields):** (Good as is, with slight clarification)
            *   **Precise Locations:** (Good as is)
            *   **Customer-Focused & No Internal Info:** (Good as is)
            *   **FAQ Generation:** (Good as is)

            **Output JSON Structure - VERY IMPORTANT:**
            *   Your final output **MUST** be a single, valid JSON object.
            *   The structure of this JSON object **MUST strictly adhere to the 'JSON Output Schema Definition' (the comprehensive one including all sections like "Table of Contents", "Code Snippet", etc.) provided immediately below.**
            *   Generate **maximum detail** for all parts of the JSON output as defined by the schema, according to all previous instructions. If information for an optional field or an entire optional section cannot be reasonably derived from the inputs, it can be omitted if the schema allows, or represented by an empty string/array as appropriate for its type if the key must be present. (However, strive for completeness).

            **JSON Output Schema Definition:**
            """

    prompt_schema_section = generation_schema_str # This MUST be the string of your FULL DETAILED SCHEMA

    prompt_end = f"""

            ---
            **Input Data Mapping:**
            *   User Query (Driving Context): `{user_query}`
            *   Event/User Action Log (Primary Source 2 - **Sequence ONLY for "Steps / How-To"**, STRICTLY NO DATA VALUES OR FILENAMES USED IN OUTPUT FIELDS): `{event_text}`
            *   PDF Document (Primary Source 1 - **UI Elements, Names, Locations, Appearance, Image Filenames ONLY. NO OTHER FILENAMES OR RAW FILE METADATA IN OUTPUT FIELDS**): Uploaded PDF Document
            *   Knowledge Base (Supplementary Source - Very Low Priority): `{KB}`
            *   Contents (Raw Text Content): `{contents}` ** (This is the raw text content of the PDF, which can be used to derive additional context or information, but should not be used to populate specific fields in the JSON output unless it directly relates to the user query or is relevant to the article's content.)
            ---
            **JSON Output (MUST be a single, syntactically correct, and complete JSON object adhering strictly to the comprehensive schema above. Ensure all string values are properly quoted and escaped.):**
            """

    final_prompt = prompt_start + "\n" + prompt_schema_section + "\n" + prompt_end
    return final_prompt