from langgraph.graph import StateGraph, END
from models import SOPState
from sop_generator import generate_sop_html

async def generate_sop_node(state: SOPState) -> SOPState:
    """Node to generate structured SOP JSON."""
    sop_json = await generate_sop_html(state.KB , state.pdf_text, state.event_data)
    state.sop_json = sop_json  
    return state  

def create_workflow():
    graph = StateGraph(SOPState)
    graph.add_node("generate_sop", generate_sop_node)
    graph.set_entry_point("generate_sop")
    graph.add_edge("generate_sop", END)
    return graph.compile()
