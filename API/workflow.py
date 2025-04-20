from langgraph.graph import StateGraph, END
from models.tech_article_models import SOPState
from utils.sop_generator import generate_sop_docx



async def generate_sop_node(state: SOPState) -> SOPState:
    """Node to generate structured SOP JSON."""
    result = await generate_sop_docx(state.KB ,state.file_path, state.event_data ,state.user_query ,state.user_id ,state.job_id)
    return result



def create_workflow():
    graph = StateGraph(SOPState)
    graph.add_node("generate_sop", generate_sop_node)
    graph.set_entry_point("generate_sop")
    graph.add_edge("generate_sop", END)
    return graph.compile()
