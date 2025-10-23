from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Dict 
import operator
import asyncio 

from .utils import (
    parse_unstructured_file, 
    parse_code_file, 
    parse_tabular_file
)
from .generation import generate_data_from_chunk

class GraphState(TypedDict):
    files_to_process: List[Dict]
    selected_recipe: str 
    parsed_chunks: List[str]
    generated_data: list # Will hold list-of-lists, then a flat list
    rejected_data: Annotated[list, operator.add] # For failed QC items
    messages: Annotated[list, operator.add]

async def parsing_node(state: GraphState):

    all_chunks = []
    files = state.get("files_to_process", [])
    print(f"--- Graph: Received {len(files)} files to process. ---")

    for file_info in files:
        filename = file_info["filename"].lower()
        content = file_info["content"]
        chunks = []

        if filename.endswith(('.pdf', '.docx', '.txt', '.md')):
            chunks = parse_unstructured_file(content, filename)
        elif filename.endswith(('.py', '.js', '.ts', '.java')):
            chunks = parse_code_file(content, filename)
        elif filename.endswith(('.csv', '.xlsx', '.xls')):
            chunks = parse_tabular_file(content, filename)
        else:
            print(f"--- Skipping unsupported file type: {filename} ---")

        all_chunks.extend(chunks)

    total_chunks = len(all_chunks)
    print(f"--- Graph: Total chunks from all files: {total_chunks} ---")
    
    return {
        "parsed_chunks": all_chunks, 
        "messages": [f"Processed {len(files)} files into {total_chunks} chunks."]
    }

async def generation_node(state: GraphState):
    recipe = state.get("selected_recipe")
    chunk = state.get("current_chunk") 
    
    generated_object = await generate_data_from_chunk(chunk, recipe)
    
    # We return a list *containing* the object or an empty list
    # This is necessary for the aggregation step
    return {"generated_data": [generated_object] if generated_object else []}

async def aggregate_node(state: GraphState):

    # state["generated_data"] will be a list of lists, e.g., [[{}], [], [{}]]
    all_results = [
        item 
        for sublist in state.get("generated_data", []) 
        for item in sublist 
        if item is not None # Filter out None values from failed generations
    ]
    print(f"--- Graph: Aggregated {len(all_results)} valid generated objects. ---")
    return {"generated_data": all_results}

def is_high_quality(item: dict, recipe: str) -> bool:
    try:
        if recipe == "qna":
            question = item.get("question", "")
            answer = item.get("answer", "")
            if len(question) < 10 or len(answer) < 10:
                return False # Too short
            if "placeholder" in answer.lower() or "?" not in question:
                return False # Low-quality content
        
        elif recipe == "code_explainer":
            explanation = item.get("explanation", "")
            if len(explanation) < 30: # Explanation must be substantial
                return False

        # Add more rules for other recipes...
        
        return True 
    
    except Exception as e:
        print(f"--- QC check failed with exception: {e} ---")
        return False 

async def quality_control_node(state: GraphState):

    data_to_check = state.get("generated_data", [])
    recipe = state.get("selected_recipe")
    
    good_data = []
    bad_data = []

    for item in data_to_check:
        if is_high_quality(item, recipe):
            good_data.append(item)
        else:
            bad_data.append(item)
            
    print(f"--- Graph: QC complete. {len(good_data)} passed, {len(bad_data)} failed. ---")
    
    return {
        "generated_data": good_data,
        "rejected_data": bad_data,
        "messages": [f"QC complete. {len(good_data)} items passed."]
    }

async def run_graph(files_to_process: List[Dict], recipe_name: str):

    workflow = StateGraph(GraphState)

    workflow.add_node("parsing_node", parsing_node)
    workflow.add_node("generation_node", generation_node)
    workflow.add_node("aggregate_node", aggregate_node)
    workflow.add_node("quality_control_node", quality_control_node)

    workflow.set_entry_point("parsing_node")
    
    workflow.add_edge("parsing_node", "generation_node", map="parsed_chunks")
    # 2. Run generation on all chunks in parallel
    # 3. Aggregate all parallel results into one list
    workflow.add_edge("generation_node", "aggregate_node")
    # 4. Run QC on the aggregated list
    workflow.add_edge("aggregate_node", "quality_control_node")
    # 5. End
    workflow.add_edge("quality_control_node", END)
    
    app = workflow.compile()
    
    initial_state = {
        "files_to_process": files_to_process,
        "selected_recipe": recipe_name,
        "parsed_chunks": [],
        "generated_data": [],
        "rejected_data": [],
        "messages": []
    }
    
    # Asynchronously run the graph
    final_state = await app.ainvoke(initial_state) 
    
    return final_state