import json # Import json library if not already imported

def get_prompt(user_query: str, event_text: str, KB: str, generation_schema_str: str):

    prompt_start = f"""
            You are an expert technical writer creating an **extremely detailed and comprehensive**, customer-facing technical article in response to a specific user query. Your absolute priority is accuracy and including **all relevant details** from the provided application data and the PDF document, while ensuring the output is **general and reusable**, NOT specific to the demo session data.

            **Core Task:** Generate a technical article in JSON format that directly and exhaustively addresses the `{user_query}`. Base the article on synthesizing information from **both** the Event Log and the PDF document according to the priorities below. The final JSON output must strictly adhere to the provided "JSON Output Schema Definition". **You MUST generate a JSON object that includes ALL properties defined in the schema provided below, ensuring all string values are properly quoted and escaped.**

            **Input Roles & Usage - CRITICAL PRIORITIES & DETAIL LEVEL:**
            *   **User Query:** The driving context. Frame the entire article, including the 'Title' field, to fully answer this query. The 'Title' field (as defined in the schema) should be a concise, human-readable summary of the article's purpose, directly related to the `{user_query}`.
            *   **PDF Document (Primary Source 1 - HIGHEST PRIORITY for UI Elements, Names, Locations, Appearance):** This is the definitive source for:
                *   **Completeness of UI Elements:** Identify **ALL** UI elements (fields, buttons, sections, labels, checkboxes, links, etc.) relevant to the task described in the user query (e.g., all elements on the 'Add Product' or 'Add Customer' screens) as shown in the PDF.
                *   **Exact User-Visible Names/Labels:** Use the precise text labels for all UI elements exactly as they appear in the PDF.
                *   **Visual Appearance & Context:** Describe placeholder text, associated icons, section headings (e.g., 'Pricing'), and overall layout context visible in the PDF.
                *   **Specific Locations:** Identify the location of elements (e.g., 'in the left navigation sidebar', 'within the Pricing section', 'at the top of the page') **whenever** the location is clearly and unambiguously identifiable in the PDF. Be precise. If the location isn't clear, omit it.
                *   **IMPORTANT:** Do not extract raw filenames or file metadata from the PDF to include directly in output fields like 'Title' or descriptive text unless the schema explicitly asks for such file metadata.
            *   **Event/User Action Log (Primary Source 2 - HIGHEST PRIORITY for Sequence of *Interacted* Steps):** Use this JSON data **only** to determine the **exact sequence of actions performed** by the user on the UI elements.
                *   If the generation schema (defined below) requires detailing a sequence of user actions or steps, use the Event Log to determine the exact sequence of these interacted steps. Follow this sequence strictly for such parts of your output.
                *   Use the technical identifiers (tag, id, classList) *only* for cross-referencing with the PDF to confirm which element was interacted with, but **do not include these technical IDs in the output.**
                *   **CRITICAL: ABSOLUTELY DO NOT use the specific *data values* (names, emails, product titles, prices, specific addresses, numbers typed, lists of filenames, etc.) entered or selected during the session, or derived from file metadata, as examples or content in your output. This is especially true for fields like 'Title'.**
            *   **Integration & Exhaustiveness (Internal Processing):**
                *   **Feature Details:** Internally identify and understand **ALL relevant UI elements for the task identified from the PDF**, using their PDF names, appearance, function, and confirmed locations. This includes elements interacted with in the log **AND other relevant fields visible in the PDF** even if not interacted with in the specific log sequence (e.g., Product Description field, Cost per Item field if visible). Use generic examples if illustrating data entry.
                *   **Sequence of Actions/Steps:** If the generation schema (defined below) requires a description of user interactions or a step-by-step guide, internally map out the sequence of actions from the **Event Log**. Each described action or step must use the **exact UI element name/label from the PDF** and specify its **location (if clearly identified in the PDF)**. Describe the interaction (click, enter text, select checkbox). **Use only generic examples** for any data entry descriptions.
            *   **Use Generic Examples ONLY - ABSOLUTELY CRITICAL:**
                *   **DO NOT USE the specific data values recorded in the Event/User Action Log** (e.g., 'Danu Sabu', 'product.danu@gmail.com', 'Shirt Small', '500.00', 'nevolabs', or any lists of filenames like 'screenshot_X.png', 'image.jpeg') as examples in the final output JSON. This is a strict, non-negotiable requirement.
                *   When describing actions involving data entry (e.g., in steps or feature descriptions, or any other part of the output requiring examples as per the schema), **MUST** use generic, non-identifiable examples (e.g., "Enter the product title (e.g., 'Sample T-Shirt')", "Enter the price (e.g., '19.99')", "Enter the customer's first name (e.g., 'Jane')").
                *   **Acceptable generic placeholders:** "Example Customer Name", "John Doe", "example@email.com", "555-123-4567", "123 Example Street", "Example Product", "19.99", "10".
            *   **Handling Specific Interactions (like Autocomplete):** Describe the *action* (e.g., "Select the matching address suggestion from the list") without using the specific *value* from the log.
            *   **General Applicability & Professional Tone:** Write for a general audience, applicable to typical usage. Maintain a clear, professional technical style.
            *   **Knowledge Base (Supplementary Source - VERY LOW PRIORITY):** Use only for internal understanding if essential. Do not include KB info directly unless neutrally rephrased.

            **CRITICAL Instructions Specific to JSON Output Fields:**
            *   **'Title' Field:**
                *   The 'Title' field **MUST** be a concise, human-readable heading (typically 5-15 words) that accurately summarizes the article's main topic. This title should be directly derived from and relevant to the `{user_query}`.
                *   It **MUST NOT** contain lists of filenames (e.g., "screenshot1.png, image.jpg"), URLs, internal technical identifiers, excessive punctuation, or any other verbose, non-heading-like content. The title should be suitable for a customer-facing document.
                *   For example, if the user query is "How to add a new product?", a good title would be "Adding a New Product to the System" or "Guide to Product Creation". An **incorrect** title would be "How to add new product based on screenshot1.png, product_details.pdf, event_log.json".
            *   **General Field Content:** All string values within the JSON output must be properly quoted with double quotes ("). Ensure that any special characters within string values (such as double quotes " or backslashes \\) are correctly escaped (e.g., \\" for a double quote, \\\\ for a backslash).

            **CRITICAL Instructions (General):**
            *   **PDF is King for UI Details:** Prioritize the PDF for element names, the complete list of relevant elements, appearance, and locations.
            *   **Log is King for Sequence:** Prioritize the Event Log *only* for the sequence of interacted steps, if such a sequence is required by the generation schema (defined below).
            *   **No Demo Data Values or Filenames in Output Fields:** Absolutely no specific names, emails, addresses, product titles, prices, or lists of filenames from the event log or PDF metadata should be included directly in the generated content of any JSON field, unless explicitly requested by the schema description for that field. Use generic examples ONLY.
            *   **Precise Locations:** Specify locations (e.g., "in the left navigation sidebar") whenever clearly identifiable in the PDF.
            *   **Customer-Focused & No Internal Info:** Clear language, no jargon, no internal IDs (`:r2m:`, `:req:`), no system issues.
            *   **FAQ Generation:** If the generation schema (defined below) includes a section for Frequently Asked Questions (FAQ), ensure the questions and answers are comprehensive, relevant, and based on the detailed, generic process and features derived from the PDF and event log.

            **Output JSON Structure - VERY IMPORTANT:**
            *   Your final output **MUST** be a single, valid JSON object.
            *   The structure of this JSON object **MUST strictly adhere to the 'JSON Output Schema Definition' provided immediately below.**
            *   Generate **maximum detail** for all parts of the JSON output as defined by the schema, according to all previous instructions (PDF priority, log sequence, generic examples, locations).

            **JSON Output Schema Definition:**
            """

    prompt_schema_section = generation_schema_str

    prompt_end = f"""

            ---
            **Input Data Mapping:**
            *   User Query (Driving Context): `{user_query}`
            *   Event/User Action Log (Primary Source 2 - **Sequence ONLY**, STRICTLY NO DATA VALUES OR FILENAMES USED IN OUTPUT FIELDS): `{event_text}`
            *   PDF Document (Primary Source 1 - **UI Elements, Names, Locations, Appearance ONLY. NO FILENAMES OR RAW FILE METADATA IN OUTPUT FIELDS**): Uploaded PDF Document
            *   Knowledge Base (Supplementary Source - Very Low Priority): `{KB}`
            ---
            **JSON Output (MUST be a single, syntactically correct, and complete JSON object adhering strictly to the schema above. Ensure all string values are properly quoted and escaped.):**
            """

    final_prompt = prompt_start + "\n" + prompt_schema_section + "\n" + prompt_end
    return final_prompt