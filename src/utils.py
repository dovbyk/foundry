# foundry/utils.py
import io
from unstructured.partition.auto import partition

def parse_and_chunk_file(file_content: bytes, filename: str) -> list[str]:
    
    print(f"--- Parsing and chunking file: {filename} ---")
    
    try:
        
        elements = partition(file=io.BytesIO(file_content), file_filename=filename)
        chunks = [str(el) for el in elements]
        print(f"--- Successfully created {len(chunks)} chunks. ---")
        return chunks
        
    except Exception as e:
        print(f"!!! Error parsing file {filename}: {e} !!!")
        return []
