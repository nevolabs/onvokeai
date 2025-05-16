from io import BytesIO
import datetime

def create_markdown(article_dict: dict):
    """
    Convert a dictionary conforming to the SaaS User Documentation schema
    into a Markdown document in memory.
    """
    markdown_lines = []

    # Helper function to add empty line if needed
    def add_empty_line():
        if markdown_lines and markdown_lines[-1] != '':
            markdown_lines.append('')

    # --- Document Structure based on JSON Schema ---

    # Title (string)
    title = article_dict.get('Title', '').strip()
    if title:
        markdown_lines.append(f"# {title}")
        add_empty_line()

    # Subtitle (string)
    subtitle = article_dict.get('Subtitle', '').strip()
    if subtitle:
        markdown_lines.append(f"## {subtitle}")
        add_empty_line()

    # Introduction (object)
    introduction = article_dict.get('Introduction')
    if introduction and isinstance(introduction, dict):
        markdown_lines.append("## Introduction")
        add_empty_line()

        # Introduction Paragraphs (array of strings)
        intro_paragraphs = introduction.get('paragraphs')
        if intro_paragraphs and isinstance(intro_paragraphs, list):
            for para in intro_paragraphs:
                if isinstance(para, str) and para.strip():
                    markdown_lines.append(para.strip())
                    add_empty_line()

        # Introduction Prerequisites (array of strings)
        prerequisites = introduction.get('prerequisites')
        if prerequisites and isinstance(prerequisites, list):
            markdown_lines.append("### Prerequisites")
            add_empty_line()
            for prereq in prerequisites:
                if isinstance(prereq, str) and prereq.strip():
                    markdown_lines.append(f"- {prereq.strip()}")
            add_empty_line()

        # Introduction Outcomes (array of strings)
        outcomes = introduction.get('outcomes')
        if outcomes and isinstance(outcomes, list):
            markdown_lines.append("### Learning Outcomes")
            add_empty_line()
            for outcome in outcomes:
                if isinstance(outcome, str) and outcome.strip():
                    markdown_lines.append(f"- {outcome.strip()}")
            add_empty_line()

    # Features (array of strings)
    features = article_dict.get('Features')
    if features and isinstance(features, list):
        markdown_lines.append("## Key Features")
        add_empty_line()
        for feature in features:
            if isinstance(feature, str) and feature.strip():
                markdown_lines.append(f"- {feature.strip()}")
        add_empty_line()

    # Table of Contents (array of objects)
    toc_items = article_dict.get('tableOfContents')
    if toc_items and isinstance(toc_items, list):
        markdown_lines.append("## Table of Contents")
        add_empty_line()
        for item in toc_items:
            if isinstance(item, dict):
                text = item.get('text', '').strip()
                if text:
                    markdown_lines.append(f"- {text}")
        add_empty_line()

    # Paragraphs (array of strings)
    paragraphs = article_dict.get('paragraphs')
    if paragraphs and isinstance(paragraphs, list):
        for para in paragraphs:
            if isinstance(para, str) and para.strip():
                markdown_lines.append(para.strip())
                add_empty_line()

    # Steps (array of objects)
    steps_data = article_dict.get('Steps / How-To')
    if steps_data and isinstance(steps_data, list):
        markdown_lines.append("## Procedure / Steps")
        add_empty_line()
        for i, step_item in enumerate(steps_data, 1):
            if isinstance(step_item, dict):
                step_text = step_item.get('step', '').strip()
                explanation = step_item.get('explanation', '').strip()
                screenshot_ref = step_item.get('screenshotRef', '').strip()

                if step_text:
                    markdown_lines.append(f"**Step {i}:** {step_text}")
                    add_empty_line()

                if explanation:
                    markdown_lines.append(explanation)
                    add_empty_line()

                if screenshot_ref:
                    markdown_lines.append(f"*(See: {screenshot_ref})*")
                    add_empty_line()

    # FAQ (array of objects)
    faq_data = article_dict.get('FAQ')
    if faq_data and isinstance(faq_data, list):
        markdown_lines.append("## Frequently Asked Questions (FAQ)")
        add_empty_line()
        for faq_item in faq_data:
            if isinstance(faq_item, dict):
                question = faq_item.get('question', '').strip()
                answer = faq_item.get('answer', '').strip()
                if question and answer:
                    markdown_lines.append(f"**Q:** {question}")
                    markdown_lines.append(f"**A:** {answer}")
                    add_empty_line()

    # Code Snippets (array of objects)
    code_snippets = article_dict.get('codeSnippets')
    if code_snippets and isinstance(code_snippets, list):
        markdown_lines.append("## Code Snippets")
        add_empty_line()
        for snippet in code_snippets:
            if isinstance(snippet, dict):
                content = snippet.get('content', '').strip()
                language = snippet.get('language', 'plaintext').strip()
                caption = snippet.get('caption', '').strip()

                if content:
                    if caption:
                        markdown_lines.append(f"### {caption}")
                        add_empty_line()
                    markdown_lines.append(f"*Language: {language}*")
                    add_empty_line()
                    markdown_lines.append(f"```{language}")
                    markdown_lines.append(content)
                    markdown_lines.append("```")
                    add_empty_line()

    # Notes (array of strings)
    notes = article_dict.get('notes')
    if notes and isinstance(notes, list):
        markdown_lines.append("## Notes")
        add_empty_line()
        for note in notes:
            if isinstance(note, str) and note.strip():
                markdown_lines.append(f"> {note.strip()}")
                add_empty_line()

    # Tips (array of strings)
    tips = article_dict.get('tips')
    if tips and isinstance(tips, list):
        markdown_lines.append("## Tips")
        add_empty_line()
        for tip in tips:
            if isinstance(tip, str) and tip.strip():
                markdown_lines.append(f"- {tip.strip()}")
        add_empty_line()

    # Quotes (array of objects)
    quotes = article_dict.get('quotes')
    if quotes and isinstance(quotes, list):
        markdown_lines.append("## Quotes")
        add_empty_line()
        for quote in quotes:
            if isinstance(quote, dict):
                text = quote.get('text', '').strip()
                attribution = quote.get('attribution', '').strip()
                if text:
                    markdown_lines.append(f"> {text}")
                    if attribution:
                        markdown_lines.append(f"> — {attribution}")
                    add_empty_line()

    # Checklist (array of strings)
    checklist = article_dict.get('checklist')
    if checklist and isinstance(checklist, list):
        markdown_lines.append("## Checklist")
        add_empty_line()
        for item in checklist:
            if isinstance(item, str) and item.strip():
                markdown_lines.append(f"- [ ] {item.strip()}")
        add_empty_line()

    # Conclusion (object)
    conclusion = article_dict.get('Conclusion')
    if conclusion and isinstance(conclusion, dict):
        markdown_lines.append("## Conclusion")
        add_empty_line()

        conc_paragraphs = conclusion.get('paragraphs')
        if conc_paragraphs and isinstance(conc_paragraphs, list):
            for para in conc_paragraphs:
                if isinstance(para, str) and para.strip():
                    markdown_lines.append(para.strip())
                    add_empty_line()

        next_steps = conclusion.get('nextSteps')
        if next_steps and isinstance(next_steps, list):
            markdown_lines.append("### Next Steps")
            add_empty_line()
            for step in next_steps:
                if isinstance(step, str) and step.strip():
                    markdown_lines.append(f"- {step.strip()}")
            add_empty_line()

    # References (array of objects)
    references = article_dict.get('references')
    if references and isinstance(references, list):
        markdown_lines.append("## References")
        add_empty_line()
        for ref in references:
            if isinstance(ref, dict):
                text = ref.get('text', '').strip()
                href = ref.get('href', '').strip()
                annotation = ref.get('annotation', '').strip()

                if text and href:
                    ref_text = f"- [{text}]({href})"
                    if annotation:
                        ref_text += f" ({annotation})"
                    markdown_lines.append(ref_text)
                elif text:
                    markdown_lines.append(f"- {text}")
        add_empty_line()

    # --- Save Document to Buffer ---
    markdown_content = '\n'.join(markdown_lines)
    buffer = BytesIO(markdown_content.encode('utf-8'))
    buffer.seek(0)
    return buffer