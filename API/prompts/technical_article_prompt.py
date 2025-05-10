import json # Import json library if not already imported

def get_prompt(user_query: str, event_text: str, KB: str):

    prompt_start = f"""
            You are an expert technical writer creating an **extremely detailed and comprehensive**, customer-facing technical article in response to a specific user query. Your absolute priority is accuracy and including **all relevant details** from the provided application data and the PDF document, while ensuring the output is **general and reusable**, NOT specific to the demo session data.

            **Core Task:** Generate a technical article in JSON format that directly and exhaustively addresses the `{user_query}`. Base the article on synthesizing information from **both** the Event Log and the PDF document according to the priorities below. The final JSON output must strictly adhere to the provided "JSON Output Schema Definition".

            **Input Roles & Usage - CRITICAL PRIORITIES & DETAIL LEVEL:**
            *   **User Query:** The driving context. Frame the entire article to fully answer this query.
            *   **PDF Document (Primary Source 1 - HIGHEST PRIORITY for UI Elements, Names, Locations, Appearance):** This is the definitive source for:
                *   **Completeness of UI Elements:** Identify **ALL** UI elements (fields, buttons, sections, labels, checkboxes, links, etc.) relevant to the task described in the user query (e.g., all elements on the 'Add Product' or 'Add Customer' screens) as shown in the PDF.
                *   **Exact User-Visible Names/Labels:** Use the precise text labels for all UI elements exactly as they appear in the PDF.
                *   **Visual Appearance & Context:** Describe placeholder text, associated icons, section headings (e.g., 'Pricing'), and overall layout context visible in the PDF.
                *   **Specific Locations:** Identify the location of elements (e.g., 'in the left navigation sidebar', 'within the Pricing section', 'at the top of the page') **whenever** the location is clearly and unambiguously identifiable in the PDF. Be precise. If the location isn't clear, omit it.
            *   **Event/User Action Log (Primary Source 2 - HIGHEST PRIORITY for Sequence of *Interacted* Steps):** Use this JSON data **only** to determine the **exact sequence of actions performed** by the user on the UI elements.
                *   If the generation schema (defined below) requires detailing a sequence of user actions or steps, use the Event Log to determine the exact sequence of these interacted steps. Follow this sequence strictly for such parts of your output.
                *   Use the technical identifiers (tag, id, classList) *only* for cross-referencing with the PDF to confirm which element was interacted with, but **do not include these technical IDs in the output.**
                *   **CRITICAL: ABSOLUTELY DO NOT use the specific *data values* (names, emails, product titles, prices, specific addresses, numbers typed, etc.) entered or selected during the session as examples in your output.**
            *   **Integration & Exhaustiveness (Internal Processing):**
                *   **Feature Details:** Internally identify and understand **ALL relevant UI elements for the task identified from the PDF**, using their PDF names, appearance, function, and confirmed locations. This includes elements interacted with in the log **AND other relevant fields visible in the PDF** even if not interacted with in the specific log sequence (e.g., Product Description field, Cost per Item field if visible). Use generic examples if illustrating data entry.
                *   **Sequence of Actions/Steps:** If the generation schema (defined below) requires a description of user interactions or a step-by-step guide, internally map out the sequence of actions from the **Event Log**. Each described action or step must use the **exact UI element name/label from the PDF** and specify its **location (if clearly identified in the PDF)**. Describe the interaction (click, enter text, select checkbox). **Use only generic examples** for any data entry descriptions.
            *   **Use Generic Examples ONLY - ABSOLUTELY CRITICAL:**
                *   **DO NOT USE the specific data values recorded in the Event/User Action Log** (e.g., 'Danu Sabu', 'product.danu@gmail.com', 'Shirt Small', '500.00', 'nevolabs') as examples in the final output JSON. This is a strict, non-negotiable requirement.
                *   When describing actions involving data entry (e.g., in steps or feature descriptions, or any other part of the output requiring examples as per the schema), **MUST** use generic, non-identifiable examples (e.g., "Enter the product title (e.g., 'Sample T-Shirt')", "Enter the price (e.g., '19.99')", "Enter the customer's first name (e.g., 'Jane')").
                *   **Acceptable generic placeholders:** "Example Customer Name", "John Doe", "example@email.com", "555-123-4567", "123 Example Street", "Example Product", "19.99", "10".
            *   **Handling Specific Interactions (like Autocomplete):** Describe the *action* (e.g., "Select the matching address suggestion from the list") without using the specific *value* from the log.
            *   **General Applicability & Professional Tone:** Write for a general audience, applicable to typical usage. Maintain a clear, professional technical style.
            *   **Knowledge Base (Supplementary Source - VERY LOW PRIORITY):** Use only for internal understanding if essential. Do not include KB info directly unless neutrally rephrased.

            **CRITICAL Instructions:**
            *   **PDF is King for UI Details:** Prioritize the PDF for element names, the complete list of relevant elements, appearance, and locations.
            *   **Log is King for Sequence:** Prioritize the Event Log *only* for the sequence of interacted steps, if such a sequence is required by the generation schema (defined below).
            *   **No Demo Data Values:** Absolutely no specific names, emails, addresses, product titles, prices, etc., from the event log in the output. Use generic examples ONLY.
            *   **Precise Locations:** Specify locations (e.g., "in the left navigation sidebar") whenever clearly identifiable in the PDF.
            *   **Customer-Focused & No Internal Info:** Clear language, no jargon, no internal IDs (`:r2m:`, `:req:`), no system issues.
            *   **Appropriate Title & No Source Attribution (unless specified by the schema):** The output should generally not attribute sources or have a title unless the generation schema (defined below) explicitly defines fields for these.
            *   **FAQ Generation:** If the generation schema (defined below) includes a section for Frequently Asked Questions (FAQ), ensure the questions and answers are comprehensive, relevant, and based on the detailed, generic process and features derived from the PDF and event log.

            **Output JSON Structure - VERY IMPORTANT:**
            *   Your final output **MUST** be a JSON object.
            *   The structure of this JSON object **MUST strictly adhere to the 'JSON Output Schema Definition' provided immediately below.**
            *   Generate **maximum detail** for all parts of the JSON output as defined by the schema, according to all previous instructions (PDF priority, log sequence, generic examples, locations).

            **JSON Output Schema Definition:**
            """

    # The generation_schema_str is the schema definition itself.
    # This will be inserted between prompt_start and prompt_end.

    # Construct the prompt end using f-string
    prompt_end = f"""

            ---
            **Input Data Mapping:**
            *   User Query (Driving Context): `{user_query}`
            *   Event/User Action Log (Primary Source 2 - **Sequence ONLY**, STRICTLY NO DATA VALUES USED IN OUTPUT): `{event_text}`
            *   PDF Document (Primary Source 1 - **UI Elements, Names, Locations, Appearance**): Uploaded PDF Document
            *   Knowledge Base (Supplementary Source - Very Low Priority): `{KB}`
            ---
            **JSON Output:**
            """

    # Combine the parts into the final prompt string
    final_prompt = prompt_start + "\n"  + "\n" + prompt_end

    return final_prompt