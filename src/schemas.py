#Defines the output schemas for each recipe 

import json

QNA_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {
            "type": "string",
            "description": "A relevant, clear question that a human would ask based on the text."
        },
        "answer": {
            "type": "string",
            "description": "A concise and accurate answer to the question, derived directly from the text."
        }
    },
    "required": ["question", "answer"]
}

SUMMARIZATION_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A brief, highly condensed summary of the key points in the text."
        },
        
        "original_text_preview": {
            "type": "string",
            "description": "The first 50 characters of the original text for reference."
        }
    },
    "required": ["summary", "original_text_preview"]
}

INSTRUCTION_FOLLOWING_SCHEMA = {
    "type": "object",
    "properties": {
        "instruction": {
            "type": "string",
            "description": "A clear, actionable instruction that could be used to train a model."
        },
        "input": {
            "type": "string",
            "description": "The specific input or context for the instruction. Can be empty if not needed."
        },
        "output": {
            "type": "string",
            "description": "The ideal, high-quality response to the instruction and input."
        }
    },
    "required": ["instruction", "output"]
}

CODE_EXPLAINER_SCHEMA = {
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "The full path of the source file within the repository (e.g., 'src/utils/auth.py'). This provides crucial location context."
    },
    "code_chunk": {
      "type": "string",
      "description": "A specific, self-contained block of code, like a function or a class, extracted from the source file."
    },
    "explanation": {
      "type": "string",
      "description": "A detailed, human-readable explanation of what the code_chunk does, its purpose, and its parameters or return values."
    }
  },
  "required": ["file_path", "code_chunk", "explanation"]
}

CODING_AGENT_SCHEMA = {
  "type": "object",
  "properties": {
    "instruction": {
      "type": "string",
      "description": "A high-level, natural language instruction describing the coding task, like 'Implement a function to validate user passwords' or 'Refactor this class to be asynchronous'."
    },
    "input_context": {
      "type": "string",
      "description": "Optional. Relevant existing code, function signatures, or class definitions that the generated code needs to interact with or modify. Can be empty for new code."
    },
    "generated_code": {
      "type": "string",
      "description": "The complete, high-quality code that correctly fulfills the instruction, adhering to best practices."
    }
  },
  "required": ["instruction", "generated_code"]
}

MATH_REASONING_SCHEMA = {
  "type": "object",
  "properties": {
    "problem": {
      "type": "string",
      "description": "The full mathematical problem statement, including any variables or constraints."
    },
    "category": {
      "type": "string",
      "description": "The area of mathematics the problem belongs to (e.g., 'Calculus', 'Linear Algebra', 'Trigonometry')."
    },
    "chain_of_thought": {
      "type": "array",
      "description": "An array of strings, where each string is a distinct, logical step in the reasoning process to solve the problem. Must include mathematical notation in LaTeX format.",
      "items": {
        "type": "string"
      }
    },
    "final_answer": {
      "type": "string",
      "description": "The final, conclusive answer to the problem, clearly stated."
    }
  },
  "required": ["problem", "chain_of_thought", "final_answer"]
}


# A master dictionary to easily look up schemas by recipe name
RECIPE_SCHEMAS = {
    "qna": {
        "name": "Question & Answer Pairs",
        "schema": QNA_SCHEMA,
        "description": "Generates question-answer pairs ideal for chatbots and assistants."
    },
    "summarization": {
        "name": "Summarization",
        "schema": SUMMARIZATION_SCHEMA,
        "description": "Creates a concise summary of the provided text chunk."
    },
    "instruction_following": {
        "name": "Instruction Following",
        "schema": INSTRUCTION_FOLLOWING_SCHEMA,
        "description": "Creates a versatile instruction-based dataset for general purpose models."
    },

    "code_explainer": {
        "name": "Code Explainer",
        "schema": CODE_EXPLAINER_SCHEMA,
        "description": "Generates explanations for source code chunks."
    },

    "coding_agent": {
        "name": "Coding Agent",
        "schema": CODING_AGENT_SCHEMA,
        "description": "Generates instruction-based datasets for training code generation models."
    },

    "math_reasoning": {
        "name": "Math Reasoning",
        "schema": MATH_REASONING_SCHEMA,
        "description": "Generates step-by-step reasoning for solving math problems."
    }
}

def get_schema_for_recipe(recipe_name: str) -> dict:
    recipe = RECIPE_SCHEMAS.get(recipe_name)
    if not recipe:
        raise ValueError(f"Unknown recipe name: {recipe_name}")
    return recipe["schema"]
