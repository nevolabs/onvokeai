from langchain.prompts import PromptTemplate

rephrase_prompt_template = PromptTemplate(
    input_variables=["query", "markdown_text", "text_to_update"],
    template="""
    You are provided with a full markdown document, a specific section to update, and a user query describing how to rephrase that section. Your task is to rephrase only the specified section according to the user query while maintaining the original markdown format and structure. Do not modify any other parts of the document. Return only the rephrased section in markdown format, without any additional explanations or content.

    **User Query**: {query}
    **Full Markdown Document (for reference)**: 
    {markdown_text}
    **Section to Update**: 
    {text_to_update}

    **Output**: Only the rephrased section in markdown format.
    """
)