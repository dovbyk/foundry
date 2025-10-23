#Communication with external LLM 

import os 
import json
from .schemas import get_schema_for_recipe
import google.generativeai as genai 
import asyncio 
from google.api_core.exceptions import ResourceExhausted

genai.configure(api_key = os.environ["GEMINI_API_KEY"]) 

SYSTEM_PROMPT_TEMPLATE = """
You are an expert data curation assistant. Your task is to generate high-quality, structured data from the user-provided text chunk based on the specified recipe.

You must adhere to the following rules:
1.  Base your output *only* on the information present in the text chunk. Do not add any external knowledge.
2.  Your response MUST be a single, valid JSON object that strictly adheres to the provided JSON schema. Do not add any extra text or explanations.

RECIPE: {recipe_name}
JSON SCHEMA:
{json_schema}
"""

async def generate_data_from_chunk(chunk: str, recipe_name: str, max_retries=3) -> dict | None:
    """
    Generates structured data from a text chunk, now with retry logic
    for rate limit errors.
    """
    
    # --- Create the model and prompt setup ---
    try:
        schema = get_schema_for_recipe(recipe_name)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            recipe_name=recipe_name, 
            json_schema=json.dumps(schema, indent=2)
        )
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt
        )
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        user_prompt = f"Here is the text chunk:\n\n---\n{chunk}\n---"

    except Exception as setup_e:
        print(f"!!! LLM setup error: {setup_e} !!!")
        return None # Failed before even making a call

    # Retry loop
    for attempt in range(max_retries):
        try:
            # Make the async API call
            response = await model.generate_content_async(
                user_prompt,
                generation_config=generation_config
            )

            json_output = response.text
            return json.loads(json_output) 

        except ResourceExhausted as e:
            wait_time = (2 ** attempt) # Exponential backoff: 1s, 2s, 4s
            print(f"--- Rate limit hit (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s... ---")
            await asyncio.sleep(wait_time)
        
        except json.JSONDecodeError as e:
            print(f"!!! LLM generation error: Invalid JSON. {e} !!!")
            return None # Don't retry on bad JSON, just fail this chunk

        except Exception as e:
            print(f"!!! LLM generation error (non-retryable): {e} !!!")
            return None # Fail this chunk

    print(f"!!! LLM generation failed for chunk after {max_retries} retries. !!!")
    return None