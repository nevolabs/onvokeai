# def get_prompt(user_query: str, event_text: str, KB: str ,format_instructions: str):
#     return f"""
#             You are an expert technical writer creating an **extremely detailed and comprehensive**, customer-facing technical article in response to a specific user query. Your absolute priority is accuracy and including **all relevant details** from the provided application data and the PDF document, while ensuring the output is **general and reusable**, NOT specific to the demo session data.

#             **Core Task:** Generate a technical article in JSON format that directly and exhaustively addresses the `{user_query}`. Base the article **primarily** on the **Event/User Action Log (JSON data)** for the definitive sequence and exact technical element references, and the **PDF Document** for visual context, user-visible labels, element appearance, and location confirmation.

#             **Input Roles & Usage - CRITICAL PRIORITIES & DETAIL LEVEL:**
#             *   **User Query:** The driving context. Frame the entire article to fully answer this query.
#             *   **Event/User Action Log (Primary Source 1 - HIGHEST PRIORITY for sequence & technical details):** This JSON data records user interactions. Use this as the definitive source for the **complete sequence of steps** and the technical identifiers (tag, id, classList) of **ALL** UI elements interacted with. **CRITICAL: Use the sequence of events and interacted element *types* (buttons, inputs, links, etc.) from this log, but ABSOLUTELY DO NOT use the specific *data values* (names, emails, product titles, prices, specific addresses, numbers typed, etc.) entered or selected during the session as examples in your output.**
#             *   **PDF Document (Primary Source 2 - HIGHEST PRIORITY for user-visible names, context, appearance & location):** Use this as the definitive source for the **user-visible text/labels** of UI elements, visual appearance (including placeholder text, section headings like 'Pricing'), and location confirmation (only if unambiguous).
#             *   **Integration & Exhaustiveness:** Synthesize **ALL** relevant information from both Primary Sources.
#                 *   Describe **every step** from the Action Log sequence relevant to the user query.
#                 *   Use the **exact user-visible names/labels** from the PDF Document for all UI elements mentioned.
#                 *   Ensure *every distinct UI element* interacted with in the Event Log (relevant to the query) has a corresponding entry in `feature_details`, described using its label from the PDF and its function/appearance.
#                 *   Describe the visual appearance and function of each element, referencing PDF context.
#                 *   Reference **all relevant UI sections and contextual elements** visible in the PDF.
#                 *   Specify locations **only** when confirmed by the PDF.
#                 *   **The goal is maximum detail on the *process* and *UI elements*, using ONLY generic examples for any user-entered data.**
#             *   **Use Generic Examples ONLY - ABSOLUTELY CRITICAL:**
#                 *   **DO NOT USE the specific data values recorded in the Event/User Action Log (e.g., 'Danu Sabu', 'product.danu@gmail.com', 'Shirt Small', '500.00', 'nevolabs', 'Kripa, Puthoor') as examples in the final output JSON.** This is a strict, non-negotiable requirement.
#                 *   When describing actions that involve entering data (like typing in a field) within the `step_by_step_guide` or `feature_details`, you **MUST** use generic, non-identifiable, placeholder examples suitable for a general audience.
#                 *   **Examples of acceptable generic placeholders:**
#                     *   Names: "Example Customer Name", "John Doe"
#                     *   Emails: "example@email.com", "customer@yourdomain.com"
#                     *   Phone Numbers: "555-123-4567" (or describe generally)
#                     *   Addresses: "123 Example Street, Anytown, ST 12345" or describe the field entry generally like "Enter the street address", "Enter the city".
#                     *   Product Titles: "Example Product", "T-Shirt", "Sample Item"
#                     *   Prices/Numbers: "19.99", "25.00", "10", or describe like "Enter the desired price", "Enter the weight value".
#                 *   **Apply this rule rigorously throughout the entire generated JSON, especially in the `step_by_step_guide`.**
#             *   **Handling Specific Interactions (like Autocomplete):**
#                 *   If the event log shows specific interaction patterns like selecting an item from a dropdown or an autocomplete suggestion list after typing, describe this *action* in the `step_by_step_guide` (e.g., "Type the beginning of the address", "Select the matching address suggestion from the list that appears").
#                 *   **However, still use generic placeholders** for the actual data *typed* or the *example value selected* in the description. **Do not use the specific value from the log** (e.g., avoid "Select the suggested address 'Kripa, Puthoor, Kerala, India'"). Instead say something like "Select the appropriate suggested address from the list".
#             *   **General Applicability:** Ensure the article is written for a general audience and applicable to typical Shopify usage, not tied to the specifics of the demo session.
#             *   **Professional Tone:** Maintain a clear, concise, and professional technical writing style.
#             *   **Knowledge Base (Supplementary Source - VERY LOW PRIORITY):** Use **only** for internal understanding if essential. **DO NOT** include KB info directly unless absolutely necessary and neutrally rephrased.

#             **CRITICAL Instructions:**
#             *   **Customer-Focused & No Internal/Demo Info:** Write clearly for end-users. **NO internal jargon, NO system issues, NO non-user-facing IDs (like :r2m:, :req:), and ABSOLUTELY NO specific demo data (names, emails, addresses, product details, typed values) from the event log.**
#             *   **Exact Naming Convention:** Use **PRECISE user-visible names/labels** from the **PDF Document**.
#             *   **Location Specificity (Strict Confidence):** Specify locations **ONLY** when **highly confident** based on the PDF Document.
#             *   **Appropriate Title:** Create a professional, descriptive `main_title`.
#             *   **No Source Attribution:** Do not mention "Event Log" or "PDF Document" in the output.
#             *   **Comprehensive & Relevant FAQ:** Base FAQ **primarily** on the *generic process* described in the article. Ensure questions are relevant to the steps and elements discussed.

#             **Output JSON Structure:**
#             Generate a JSON object with the following structure. Populate fields with **maximum detail** according to the critical instructions, ensuring **no relevant element, label, placeholder text, or step is missed, and using ONLY generic examples for data entry steps.**

#             1.  `main_title`: Professional, descriptive title addressing the user query topic.
#             2.  `introduction`: Comprehensive overview synthesizing context, directly addressing the user query.
#                 - `title`: "Introduction"
#                 - `content`: Detailed introduction setting the stage fully.
#             3.  `feature_details`: Exhaustive description of **all** relevant features/UI elements using exact user-visible names/labels.
#                 - `title`: e.g., "Key Elements and Sections Involved"
#                 - `features`: Comprehensive list describing **all relevant UI elements/features interacted with in the event log or clearly visible and relevant in the PDF**.
#                     - `title`: Exact user-visible element/feature name/label (e.g., "Title Input Field (Product)", "Pricing Section", "Add customer Button", "Apartment, suite, etc. Input Field").
#                     - `description`: Detailed explanation of its appearance (including placeholder text, associated labels/icons), function, location (if confirmed), and role in the task, referencing visual context accurately. Use generic examples if illustrating data entry.
#             4.  `step_by_step_guide`: **Complete sequence** of specific actions using exact user-visible names/labels and confirmed locations.
#                 - `title`: e.g., "Detailed Step-by-Step Guide: [Task Name]"
#                 - `introduction` (optional): Briefly state the goal of the steps.
#                 - `steps`: Ordered list detailing **every single necessary action** (from Action Log sequence), using exact UI element names/labels (from PDF). **CRITICAL: When describing data input steps (e.g., "Enter the product title..."), use ONLY the generic placeholder examples mandated above (e.g., "Enter the product title (e.g., 'Sample T-Shirt')"). DO NOT use the specific values from the event log.** Follow the guidance for handling specific interactions like autocomplete generically.
#             5.  `conclusion`: Summary reinforcing the solution/answer, acknowledging the steps covered.
#                 - `title`: "Conclusion"
#                 - `content`: Concluding remarks.
#             6.  `faq`: Relevant follow-up questions covering potential nuances derived from the detailed, generic steps and elements.
#                 - `title`: "Frequently Asked Questions"
#                 - `questions`: List of Q&A pairs.
#                     - `question`: Potential follow-up question based on the article's detailed content.
#                     - `answer`: Answer based primarily on the detailed (but generic) process presented in the article.

#             **Output JSON Schema:**
#             {format_instructions}

#             ---
#             **Input Data Mapping:**
#             *   User Query (Driving Context): `{user_query}`
#             *   Event/User Action Log (Primary Source 1 - Sequence/Technical Details, **STRICTLY NO DATA VALUES USED IN OUTPUT**): `{event_text}`
#             *   PDF Document (Primary Source 2 - User-Visible Names/Labels, Context, Appearance, Location): Uploaded PDF Document
#             *   Knowledge Base (Supplementary Source - Very Low Priority): `{KB}`
#             ---

#             **JSON Output:**
#             """


def get_prompt(user_query: str, event_text: str, KB: str ,format_instructions: str):
    return f"""
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
                *   Follow this sequence strictly for the `step_by_step_guide`.
                *   Use the technical identifiers (tag, id, classList) *only* for cross-referencing with the PDF to confirm which element was interacted with, but **do not include these technical IDs in the output.**
                *   **CRITICAL: ABSOLUTELY DO NOT use the specific *data values* (names, emails, product titles, prices, specific addresses, numbers typed, etc.) entered or selected during the session as examples in your output.**
            *   **Integration & Exhaustiveness:**
                *   **Feature Details:** Must describe **ALL relevant UI elements for the task identified from the PDF**, using their PDF names, appearance, function, and confirmed locations. This includes elements interacted with in the log **AND other relevant fields visible in the PDF** even if not interacted with in the specific log sequence (e.g., Product Description field, Cost per Item field if visible).
                *   **Step-by-Step Guide:** Must follow the sequence of actions from the **Event Log**. Each step must use the **exact UI element name/label from the PDF** and specify its **location (if clearly identified in the PDF)**. Describe the interaction (click, enter text, select checkbox). **Use only generic examples** for any data entry descriptions.
            *   **Use Generic Examples ONLY - ABSOLUTELY CRITICAL:**
                *   **DO NOT USE the specific data values recorded in the Event/User Action Log** (e.g., 'Danu Sabu', 'product.danu@gmail.com', 'Shirt Small', '500.00', 'nevolabs') as examples in the final output JSON. This is a strict, non-negotiable requirement.
                *   When describing actions involving data entry in the `step_by_step_guide` or `feature_details`, **MUST** use generic, non-identifiable examples (e.g., "Enter the product title (e.g., 'Sample T-Shirt')", "Enter the price (e.g., '19.99')", "Enter the customer's first name (e.g., 'Jane')").
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
            *   **Comprehensive & Relevant FAQ based on the generic process.**

            **Output JSON Structure:**
            Generate a JSON object with the following structure. Populate fields with **maximum detail** according to the critical instructions, ensuring **all relevant elements from the PDF are described**, the **step sequence matches the log**, **locations from the PDF are used**, and **only generic examples** are provided.

            1.  `main_title`: Professional, descriptive title.
            2.  `introduction`: Comprehensive overview.
                - `title`: "Introduction"
                - `content`: Detailed introduction.
            3.  `feature_details`: Exhaustive description of **ALL** relevant UI elements for the task (identified from the PDF).
                - `title`: e.g., "Key Elements and Sections Involved"
                - `features`: Comprehensive list.
                    - `title`: Exact user-visible element/feature name/label (from PDF).
                    - `description`: Detailed explanation of appearance (placeholder text, icons), function, location (from PDF, if clear), and role in the task. Include **all relevant fields** (e.g., Product Description, Cost per Item) visible in the PDF for the task, even if not in the event log. Use generic examples if illustrating data entry.
            4.  `step_by_step_guide`: **Sequence of actions from Event Log**, using exact names/locations from PDF.
                - `title`: e.g., "Detailed Step-by-Step Guide: [Task Name]"
                - `introduction` (optional): ...
                - `steps`: Ordered list detailing **every necessary action performed in the Event Log sequence**. Use exact UI element names/labels (from PDF) and **specify location if clear in PDF** (e.g., "Click 'Products' in the left navigation sidebar"). **CRITICAL: Use ONLY generic examples for data input descriptions (e.g., "Enter the product title (e.g., 'Sample Item') in the 'Title' field at the top of the page").** Handle interactions like autocomplete generically.
            5.  `conclusion`: Summary.
                - `title`: "Conclusion"
                - `content`: Concluding remarks.
            6.  `faq`: Relevant follow-up questions based on the detailed, generic process and features.
                - `title`: "Frequently Asked Questions"
                - `questions`: List of Q&A pairs.

            **Output JSON Schema:**
            {format_instructions}

            ---
            **Input Data Mapping:**
            *   User Query (Driving Context): `{user_query}`
            *   Event/User Action Log (Primary Source 2 - **Sequence ONLY**, STRICTLY NO DATA VALUES USED IN OUTPUT): `{event_text}`
            *   PDF Document (Primary Source 1 - **UI Elements, Names, Locations, Appearance**): Uploaded PDF Document
            *   Knowledge Base (Supplementary Source - Very Low Priority): `{KB}`
            ---

            **JSON Output:**
            """