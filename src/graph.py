#Main graph logic of dataset creation pipeline

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Dict 
import operator
from .utils import parse_and_chunk_file
from .generation import generate_data_from_chunk

class GraphState(TypedDict):
    files_to_process: List[Dict]
    selected_recipe: str 
    parsed_chunks: List[str]
    generated_data: list 
    messages: Annotated[list, operator.add]


async def parse_and_chunk_node(state: GraphState):
    
    all_chunks = []
    files = state.get("files_to_process", [])
    
    print(f"--- Graph: Received {len(files)} files to process. ---")
    
    for file_info in files:
        filename = file_info["filename"]
        file_content = file_info["content"]
        
        chunks = parse_and_chunk_file(file_content, filename) #this util function returns a List 
        all_chunks.extend(chunks) #extend() method takes an iteratble chunks:List, appends all this items to the main list called all_chunks

    total_chunks = len(all_chunks)
    print(f"--- Graph: Total chunks created from all files: {total_chunks} ---")
    
    return {
        "parsed_chunks": all_chunks, 
        "messages": [f"Processed {len(files)} files into {total_chunks} chunks."]
    }

async def generation_node(state: GraphState):
    recipe = state.get("selected_recipe")
    # LangGraph's .map() will inject a single chunk here
    chunk = state.get("current_chunk") 
    generated_object = await generate_data_from_chunk(chunk, recipe)
    
    return {"generated_data": [generated_object] if generated_object else []}



#def accumulate_result_node(state: GraphState):
 #   # The 'generated_data' will be a list of lists. We flatten it.
  #  all_generated_data = [item for sublist in state.get("generated_data", []) for item in sublist]
   # print(f"--- Accumulating {len(all_generated_data)} generated objects. ---")
    #return {"generated_data": all_generated_data, "messages": ["Results accumulated."]}


# This is the main function that creates and runs our graph
async def run_graph(files_to_process: List[Dict], recipe_name: str):

    workflow = StateGraph(GraphState)

    
    workflow.add_node("parse_and_chunk", parse_and_chunk_node)
    workflow.add_node("generation_node", generation_node)
    

    workflow.set_entry_point("parse_and_chunk")
    workflow.add_edge("parse_and_chunk", "generation_node", map = "parsed_chunks" ) #parsed_chunks is a list containing string chunks of all the data.
    workflow.add_edge("generation_node", END)                           #langgraph will add this attribute in the GraphState object for each 'generation_node' function call 

    
    
    app = workflow.compile()

    
    initial_state = {
        "files_to_process": files_to_process,
        "selected_recipe": recipe_name,
        "parsed_chunks": [],
        "generated_data": [],
        "messages": []
    }
    #ainvoke for async execution
    final_state = await app.ainvoke(initial_state) 
    
    #generated_data field contains list of dictionaries, we are flattening it 
    final_state["generated_data"] = [item for sublist in final_state["generated_data"] for item in sublist]

    return final_state
