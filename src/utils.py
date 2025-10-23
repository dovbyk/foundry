# Divides raw files into chunks using parsers specific to file types.

import io
import ast  
import pandas as pd
from unstructured.partition.auto import partition
from typing import List

def parse_unstructured_file(file_content: bytes, filename: str) -> List[str]:
 
    try:
        # partition handles file type detection internally
        elements = partition(file=io.BytesIO(file_content), file_filename=filename)
        chunks = [str(el) for el in elements]
        print(f"--- Successfully created {len(chunks)} chunks. ---")
        return chunks
        
    except Exception as e:
        print(f"!!! Error parsing [Unstructured] file {filename}: {e} !!!")
        return []

def parse_code_file(file_content: bytes, filename: str) -> List[str]:

    try:
        content_str = file_content.decode('utf-8')
        tree = ast.parse(content_str)
        chunks = []
        
        # Chunk by top-level functions and classes
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # ast.unparse converts the node back to source code
                chunks.append(ast.unparse(node))
            
        # Fallback: If no functions/classes, treat the whole file as one chunk
        if not chunks:
            chunks.append(content_str)
            
        print(f"--- Successfully created {len(chunks)} code chunks. ---")
        return chunks
        
    except Exception as e:
        print(f"!!! Error parsing [Code/AST] file {filename}: {e} !!!")
        # Fallback on pure text chunking if AST fails
        if content_str:
            return [content_str]
        return []

def parse_tabular_file(file_content: bytes, filename: str) -> List[str]:
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            print(f"!!! Unsupported tabular format for: {filename} !!!")
            return []
        
        # Convert each row into a JSON string
        chunks = [row.to_json() for index, row in df.iterrows()]
        
        print(f"--- Successfully created {len(chunks)} row-chunks. ---")
        return chunks
        
    except Exception as e:
        print(f"!!! Error parsing [Tabular/Pandas] file {filename}: {e} !!!")
        return []