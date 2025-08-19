from io import BytesIO
import datetime

def create_markdown(article_dict: dict, user_id: str, job_id: str):
    """
    Convert a dictionary conforming to the updated SaaS User Documentation schema
    into a Markdown document in memory.
    """
    markdown_lines = []

    # Helper function to add empty line if needed
    def add_empty_line():
        if markdown_lines and markdown_lines[-1] != '':
            markdown_lines.append('')

    # --- Document Structure based on Updated JSON Schema ---

    # Title (string)
    title = article_dict.get('title', '').strip()
    if title:
        markdown_lines.append(f"# {title}")
        add_empty_line()

    # Subtitle (string)
    subtitle = article_dict.get('subtitle', '').strip()
    if subtitle:
        markdown_lines.append(f"## {subtitle}")
        add_empty_line()

    # Introduction (object)
    introduction = article_dict.get('introduction')
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
    features = article_dict.get('features')
    if features and isinstance(features, list):
        markdown_lines.append("## Key Features")
        add_empty_line()
        for feature in features:
            if isinstance(feature, str) and feature.strip():
                markdown_lines.append(f"- {feature.strip()}")
        add_empty_line()

    # Table of Contents (array of objects)
    toc_items = article_dict.get('table_of_contents')
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

    # Notes (array of strings)
    notes = article_dict.get('notes')
    if notes and isinstance(notes, list):
        markdown_lines.append("## Notes")
        add_empty_line()
        for note in notes:
            if isinstance(note, str) and note.strip():
                markdown_lines.append(f"> {note.strip()}")
            add_empty_line()

    # Code Snippets (array of objects)
    code_snippets = article_dict.get('code_snippets')
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

    # Checklists (array of strings)
    checklists = article_dict.get('checklists')
    if checklists and isinstance(checklists, list):
        markdown_lines.append("## Checklist")
        add_empty_line()
        for item in checklists:
            if isinstance(item, str) and item.strip():
                markdown_lines.append(f"- [ ] {item.strip()}")
        add_empty_line()

    # FAQ (array of objects)
    faq_data = article_dict.get('faq')
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

    # Steps (array of objects)
    steps_data = article_dict.get('steps')
    if steps_data and isinstance(steps_data, list):
        markdown_lines.append("## Procedure / Steps")
        add_empty_line()
        for i, step_item in enumerate(steps_data, 1):
            if isinstance(step_item, dict):
                step_text = step_item.get('step', '').strip()
                explanation = step_item.get('explanation', '').strip()
                image_name = step_item.get('screenshotRef', '').strip()

                if step_text:
                    markdown_lines.append(f"**Step {i}:** {step_text}")
                    add_empty_line()

                if explanation:
                    markdown_lines.append(explanation)
                    add_empty_line()

                if image_name:
                    # Construct the full image URL
                    image_path = (f"https://gqvbkzcscjeaghodwxnz.supabase.co/storage/v1/"
                                f"object/public/log_dataa/{user_id}/{job_id}/screenshots/{image_name}")

                    # Determine Alt Text
                    alt_text = explanation if explanation else f"Screenshot for Step {i}"
                    # Sanitize alt_text
                    alt_text = alt_text.replace(']', '').replace('[', '').replace('(', '').replace(')', '')

                    # Append the Markdown for the image
                    markdown_lines.append(f"![{alt_text}]({image_path})")
                    add_empty_line()

    # Callouts (array of strings)
    callouts = article_dict.get('callouts')
    if callouts and isinstance(callouts, list):
        markdown_lines.append("## Tips")
        add_empty_line()
        for callout in callouts:
            if isinstance(callout, str) and callout.strip():
                markdown_lines.append(f"- {callout.strip()}")
        add_empty_line()

    # Alert Boxes (array of objects)
    alert_boxes = article_dict.get('alert_boxes')
    if alert_boxes and isinstance(alert_boxes, list):
        markdown_lines.append("## Alerts")
        add_empty_line()
        for alert in alert_boxes:
            if isinstance(alert, dict):
                style = alert.get('style', 'Info').strip()
                content = alert.get('content', '').strip()
                if content:
                    markdown_lines.append(f"> **{style}:** {content}")
                    add_empty_line()

    # CTAs (array of objects)
    ctas = article_dict.get('ctas')
    if ctas and isinstance(ctas, list):
        markdown_lines.append("## Call to Action")
        add_empty_line()
        for cta in ctas:
            if isinstance(cta, dict):
                text = cta.get('text', '').strip()
                href = cta.get('href', '').strip()
                if text and href:
                    markdown_lines.append(f"[{text}]({href})")
                elif text:
                    markdown_lines.append(f"- {text}")
                add_empty_line()

    # Decision Points (array of objects)
    decision_points = article_dict.get('decision_points')
    if decision_points and isinstance(decision_points, list):
        markdown_lines.append("## Decision Points")
        add_empty_line()
        for dp in decision_points:
            if isinstance(dp, dict):
                if_condition = dp.get('if_condition', '').strip()
                then_steps = dp.get('then_steps', [])
                else_steps = dp.get('else_steps', [])
                if if_condition:
                    markdown_lines.append(f"**If:** {if_condition}")
                    add_empty_line()
                    if then_steps and isinstance(then_steps, list):
                        markdown_lines.append("**Then:**")
                        for step in then_steps:
                            if isinstance(step, str) and step.strip():
                                markdown_lines.append(f"- {step.strip()}")
                        add_empty_line()
                    if else_steps and isinstance(else_steps, list):
                        markdown_lines.append("**Else:**")
                        for step in else_steps:
                            if isinstance(step, str) and step.strip():
                                markdown_lines.append(f"- {step.strip()}")
                        add_empty_line()

    # Expandable Sections (array of objects)
    expandable_sections = article_dict.get('expandable_sections')
    if expandable_sections and isinstance(expandable_sections, list):
        markdown_lines.append("## Expandable Sections")
        add_empty_line()
        for section in expandable_sections:
            if isinstance(section, dict):
                title = section.get('title', '').strip()
                content = section.get('content', [])
                if title and content and isinstance(content, list):
                    markdown_lines.append(f"### {title}")
                    add_empty_line()
                    for line in content:
                        if isinstance(line, str) and line.strip():
                            markdown_lines.append(line.strip())
                        add_empty_line()

    # Expected Results (array of objects)
    expected_results = article_dict.get('expected_results')
    if expected_results and isinstance(expected_results, list):
        markdown_lines.append("## Expected Results")
        add_empty_line()
        for result in expected_results:
            if isinstance(result, dict):
                text = result.get('text', '').strip()
                if text:
                    markdown_lines.append(f"- {text}")
                    add_empty_line()

    # Glossary (array of objects)
    glossary = article_dict.get('glossary')
    if glossary and isinstance(glossary, list):
        markdown_lines.append("## Glossary")
        add_empty_line()
        for term in glossary:
            if isinstance(term, dict):
                term_text = term.get('term', '').strip()
                definition = term.get('definition', '').strip()
                if term_text and definition:
                    markdown_lines.append(f"**{term_text}:** {definition}")
                    add_empty_line()

    # Process Maps (array of objects)
    process_maps = article_dict.get('process_maps')
    if process_maps and isinstance(process_maps, list):
        markdown_lines.append("## Process Map")
        add_empty_line()
        for stage in process_maps:
            if isinstance(stage, dict):
                stage_text = stage.get('stage', '').strip()
                details = stage.get('details', '').strip()
                if stage_text:
                    markdown_lines.append(f"**Stage:** {stage_text}")
                    if details:
                        markdown_lines.append(details)
                    add_empty_line()

    # Tables (array of objects)
    tables = article_dict.get('tables')
    if tables and isinstance(tables, list):
        markdown_lines.append("## Tables")
        add_empty_line()
        for table in tables:
            if isinstance(table, dict):
                headers = table.get('headers', [])
                rows = table.get('rows', [])
                if headers and isinstance(headers, list) and rows and isinstance(rows, list):
                    # Write headers
                    header_row = '| ' + ' | '.join(header.strip() for header in headers if isinstance(header, str)) + ' |'
                    markdown_lines.append(header_row)
                    # Write separator
                    separator = '| ' + ' | '.join(['---' for _ in headers]) + ' |'
                    markdown_lines.append(separator)
                    # Write rows
                    for row in rows:
                        if isinstance(row, list):
                            row_text = '| ' + ' | '.join(cell.strip() for cell in row if isinstance(cell, str)) + ' |'
                            markdown_lines.append(row_text)
                    add_empty_line()

    # Conclusion (object)
    conclusion = article_dict.get('conclusion')
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