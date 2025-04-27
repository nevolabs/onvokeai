import json # Import json library if not already imported

def get_prompt(user_query: str, event_text: str, KB: str ,format_instructions: str ,components: list):
    # Convert the list of components into a user-friendly string for the prompt
    component_list_str = ", ".join([f"'{c}'" for c in components])

    # Ensure format_instructions is a string (e.g., if it was passed as a Pydantic model, convert it)
    # If it's already a JSON string, this is fine. If it's a Python object, serialize it.
    if not isinstance(format_instructions, str):
         # Assuming format_instructions might be a Pydantic model or dict
         # Use schema_json() for Pydantic models or json.dumps for dicts
         # This is an example, adjust based on the actual type of format_instructions
         try:
             # Try Pydantic schema_json() if it's a model type/instance
             if hasattr(format_instructions, 'schema_json'):
                 format_instructions = format_instructions.schema_json(indent=2)
             else: # Fallback to standard json.dumps
                 format_instructions = json.dumps(format_instructions, indent=2)
         except Exception:
             # Fallback if conversion fails - convert to basic string representation
             format_instructions = str(format_instructions)


    # Construct the prompt start using f-string for simple variables
    # Escape the literal braces in the example JSON within the instructions using {{ and }}
    prompt_start = f"""
            You are an expert technical writer creating an **extremely detailed and comprehensive**, customer-facing technical article in response to a specific user query. Your absolute priority is accuracy and including **all relevant details** from the provided application data and the PDF document, while ensuring the output is **general and reusable**, NOT specific to the demo session data.

            **Core Task:** Generate a technical article in JSON format that directly and exhaustively addresses the `{user_query}`. Base the article on synthesizing information from **both** the Event Log and the PDF document according to the priorities below.

            **Input Roles & Usage - CRITICAL PRIORITIES & DETAIL LEVEL:**
            *   **User Query:** The driving context. Frame the entire article to fully answer this query.
            *   **PDF Document (Primary Source 1 - HIGHEST PRIORITY for UI Elements, Names, Locations, Appearance):** This is the definitive source for:
                *   **Completeness of UI Elements:** Identify **ALL** UI elements (fields, buttons, sections, labels, checkboxes, links, etc.) relevant to the task described in the user query (e.g., all elements on the 'Add Product' or 'Add Customer' screens) as shown in the PDF.
                *   **Exact User-Visible Names/Labels:** Use the precise text labels for all UI elements exactly as they appear in the PDF.
                *   **Visual Appearance & Context:** Describe placeholder text, associated icons, section headings (e.g., 'Pricing'), and overall layout context visible in the PDF.
                *   **Specific Locations:** Identify the location of elements (e.g., 'in the left navigation sidebar', 'within the Pricing section', 'at the top of the page') **whenever** the location is clearly and unambiguously identifiable in the PDF. Be precise. If the location isn't clear, omit it.
            *   **Event/User Action Log (Primary Source 2 - HIGHEST PRIORITY for Sequence of *Interacted* Steps):** Use this JSON data **only** to determine the **exact sequence of actions performed** by the user on the UI elements.
                *   Follow this sequence strictly for the `step_by_step_guide` (or equivalent 'steps' component if requested).
                *   Use the technical identifiers (tag, id, classList) *only* for cross-referencing with the PDF to confirm which element was interacted with, but **do not include these technical IDs in the output.**
                *   **CRITICAL: ABSOLUTELY DO NOT use the specific *data values* (names, emails, product titles, prices, specific addresses, numbers typed, etc.) entered or selected during the session as examples in your output.**
            *   **Integration & Exhaustiveness (Internal Processing):**
                *   **Feature Details:** Internally identify and understand **ALL relevant UI elements for the task identified from the PDF**, using their PDF names, appearance, function, and confirmed locations. This includes elements interacted with in the log **AND other relevant fields visible in the PDF** even if not interacted with in the specific log sequence (e.g., Product Description field, Cost per Item field if visible). Use generic examples if illustrating data entry.
                *   **Step-by-Step Guide:** Internally map out the sequence of actions from the **Event Log**. Each step must use the **exact UI element name/label from the PDF** and specify its **location (if clearly identified in the PDF)**. Describe the interaction (click, enter text, select checkbox). **Use only generic examples** for any data entry descriptions.
            *   **Use Generic Examples ONLY - ABSOLUTELY CRITICAL:**
                *   **DO NOT USE the specific data values recorded in the Event/User Action Log** (e.g., 'Danu Sabu', 'product.danu@gmail.com', 'Shirt Small', '500.00', 'nevolabs') as examples in the final output JSON. This is a strict, non-negotiable requirement.
                *   When describing actions involving data entry (e.g., in steps or feature descriptions), **MUST** use generic, non-identifiable examples (e.g., "Enter the product title (e.g., 'Sample T-Shirt')", "Enter the price (e.g., '19.99')", "Enter the customer's first name (e.g., 'Jane')").
                *   **Acceptable generic placeholders:** "Example Customer Name", "John Doe", "example@email.com", "555-123-4567", "123 Example Street", "Example Product", "19.99", "10".
            *   **Handling Specific Interactions (like Autocomplete):** Describe the *action* (e.g., "Select the matching address suggestion from the list") without using the specific *value* from the log.
            *   **General Applicability & Professional Tone:** Write for a general audience, applicable to typical usage. Maintain a clear, professional technical style.
            *   **Knowledge Base (Supplementary Source - VERY LOW PRIORITY):** Use only for internal understanding if essential. Do not include KB info directly unless neutrally rephrased.

            **CRITICAL Instructions:**
            *   **PDF is King for UI Details:** Prioritize the PDF for element names, the complete list of relevant elements, appearance, and locations.
            *   **Log is King for Sequence:** Prioritize the Event Log *only* for the sequence of interacted steps.
            *   **No Demo Data Values:** Absolutely no specific names, emails, addresses, product titles, prices, etc., from the event log in the output. Use generic examples ONLY.
            *   **Precise Locations:** Specify locations (e.g., "in the left navigation sidebar") whenever clearly identifiable in the PDF.
            *   **Customer-Focused & No Internal Info:** Clear language, no jargon, no internal IDs (`:r2m:`, `:req:`), no system issues.
            *   **Appropriate Title & No Source Attribution.**
            *   **Comprehensive & Relevant FAQ (if requested):** Base FAQ on the detailed, generic process and features.

            **Output JSON Structure & Component Filtering - VERY IMPORTANT:**
            *   You are provided with a schema definition below which describes the structure for various possible components (like introduction, features, steps, faq, etc.).
            *   You are also provided with a specific list of requested components: `{component_list_str}` (derived from the `{components}` input variable).
            *   Your final output **MUST** be a JSON object.
            *   This JSON object **MUST ONLY contain the top-level keys (representing components) that are explicitly listed in the requested components list: `{component_list_str}`.**
            *   For each component included in the output, its structure and fields **MUST strictly adhere to the schema defined below**.
            *   **Example:** If `{components}` is `['introduction', 'steps']`, your final JSON output should look something like `{{ "introduction": {{ ... }}, "steps": {{ ... }} }}`, where the content and structure of `introduction` and `steps` follow the schema. Any other components (like 'features', 'faq', 'conclusion') MUST NOT be included in the final JSON output, even if you gathered information for them internally.
            *   Generate **maximum detail** for the requested components according to all previous instructions (PDF priority, log sequence, generic examples, locations).

            **JSON Output Schema Definition:**
            """

    # Append the format_instructions string separately. It's already a string.
    prompt_middle = format_instructions

    # Construct the prompt end using f-string
    prompt_end = f"""

            ---
            **Input Data Mapping:**
            *   User Query (Driving Context): `{user_query}`
            *   Event/User Action Log (Primary Source 2 - **Sequence ONLY**, STRICTLY NO DATA VALUES USED IN OUTPUT): `{event_text}`
            *   PDF Document (Primary Source 1 - **UI Elements, Names, Locations, Appearance**): Uploaded PDF Document
            *   Knowledge Base (Supplementary Source - Very Low Priority): `{KB}`
            *   Requested Output Components: `{component_list_str}`
            ---

            **JSON Output:**
            """

    # Combine the parts into the final prompt string
    final_prompt = prompt_start + "\n" + prompt_middle + "\n" + prompt_end

    return final_prompt