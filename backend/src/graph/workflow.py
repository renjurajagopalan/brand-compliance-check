'''
This module defines the DAG: Directed Acyclic Graph that performs the video audit compliance
The nodes are connected using stategraph from LangGraph

START -> index_vido_node -> audit_content_node -> END

'''
from langgraph.graph import StateGraph, END

from backend.src.graph.state import VideoAuditState
from backend.src.graph.nodes import (
    index_video_node,
    audit_content_node
)

def create_graph():
    '''
    Defines and compiles the LangGraph workflow

    '''
    # Initialize the graph
    workflow = StateGraph(VideoAuditState)

    # Add the nodes
    workflow.add_node("indexer",index_video_node)
    workflow.add_node("auditor",audit_content_node)

    # Define the entry point
    workflow.set_entry_point("indexer")

    # Define the edges
    workflow.add_edge("indexer", "auditor")
    workflow.add_edge("auditor",END)

    # compile the graph
    app = workflow.compile()
    return app

# expose the runnable app
app = create_graph()