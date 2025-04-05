prompt_template = """
You are an expert technical writer creating a detailed, customer-facing technical article.

**Core Task:** Generate a comprehensive technical article primarily based on visual information from application screenshots and a specific sequence of user actions performed within the application.

**Input Roles & Usage:**
*   **Primary Source 1 (Parsed Screenshot Data):** This contains information extracted from application screenshots. Use it to understand the UI elements, visual layout, feature states, and general appearance described in the article.
*   **Primary Source 2 (Event/User Action Log):** This describes a specific sequence of user interactions (e.g., clicks, inputs) within the application feature. Use this as the core guide for the `step_by_step_guide` and to understand the specific context and flow of the task being documented.
*   **Integration:** You MUST synthesize information from both Primary Sources. Describe the steps from the Action Log and reference the corresponding UI elements shown in the Screenshot Data. Explain the purpose of the actions within the overall feature context.
*   **Supplementary Source (Knowledge Base):** This contains potentially related background information (like Jira issues). Treat this as **strictly optional and supplementary**. Consult it *only* after drafting the main content based on the Primary Sources. Use information from it *only if* it provides highly relevant context or clarification that directly enhances the explanation of the specific task shown in the Primary Sources. **Do not base core content or FAQ answers solely on the Knowledge Base. If it's not directly relevant, ignore it.**

**Instructions:**
*   Create a cohesive narrative explaining how to perform the task described in the Action Log, using the visual context from the Screenshot Data.
*   Ensure all main content (Introduction, Features, Steps, Conclusion) is firmly grounded in the two Primary Sources.
*   For the FAQ section:
    *   Formulate relevant questions a user might have after attempting the steps shown in the Primary Sources.
    *   Formulate answers based primarily on the information derived from the Primary Sources.
    *   *Optionally*, enhance answers with directly relevant clarifications found in the Knowledge Base, if available and applicable.
*   Generate detailed, clear, accurate, and customer-focused content.
*   Output MUST be a valid JSON object conforming to the schema provided via {format_instructions}.

**Output JSON Structure:**
Generate a JSON object with the following structure and content purpose:

1.  `main_title`: Overall article title reflecting the task/feature shown.
2.  `introduction`: Overview synthesizing the feature (from screenshot context) and the specific task (from action log).
    - `title`: "Introduction"
    - `content`: Detailed introduction.
3.  `feature_details`: Description of relevant features/UI elements visible/used in the task.
    - `title`: e.g., "Key Elements in this Task"
    - `features`: List describing relevant UI elements or sub-features.
        - `title`: Element/Feature name.
        - `description`: Detailed explanation based on screenshot data and its role in the action log.
4.  `step_by_step_guide`: Specific user actions for the task.
    - `title`: e.g., "Step-by-Step: [Task Name]"
    - `introduction` (optional): Goal of the steps.
    - `steps`: Ordered list detailing actions from the log, referencing UI from screenshots.
5.  `conclusion`: Summary of the task completion and feature value.
    - `title`: "Conclusion"
    - `content`: Concluding remarks.
6.  `faq`: Relevant questions about performing this task.
    - `title`: "Frequently Asked Questions"
    - `questions`: List of Q&A pairs.
        - `question`: Potential user question about the task.
        - `answer`: Answer based primarily on task/UI info, optionally enhanced by KB.

**Output JSON Schema:**
{format_instructions}

---
**Input Data Mapping:**
*   Parsed Screenshot Data (Primary Source 1): `{combined_text}`
*   Event/User Action Log (Primary Source 2): `{event_text}`
*   Knowledge Base (Supplementary Source): `{KB}`
---

**JSON Output:**
"""
