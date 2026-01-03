# Prompt Templates

This directory contains external prompt template files that define how the chatbot introduces itself and communicates with users.

## Template Files

- **`system_prompt_inline.txt`** - Main system prompt for the RAG engine (used by `PromptBuilder`)
- **`smart_agent_system.txt`** - System prompt for the smart agent (used by `SmartAgent`)
- **`intent_classifier.txt`** - Prompt for intent classification (used by `classify_intent`)

## Variable Substitution

Templates support Python-style string formatting with `{variable_name}` placeholders:

- **`smart_agent_system.txt`** uses `{db_schema_description}` - dynamically inserted database schema information
- **`intent_classifier.txt`** uses `{user_message}` - the user's message to classify

## Editing Prompts

You can edit these `.txt` files directly without modifying Python code. Changes take effect on the next application restart.

### Example: Changing the Agent Name

To change the agent name from "Archivio" to something else:

1. Edit `system_prompt_inline.txt` and replace "Archivio" with your desired name
2. Edit `smart_agent_system.txt` and replace "Amalia" with your desired name  
3. Edit `intent_classifier.txt` and replace "Archivio" with your desired name
4. Restart the application

## Fallback Behavior

If a template file is missing or has errors, the code will:
1. Log a warning
2. Fall back to the hardcoded prompt in the Python source code
3. Continue operating normally

This ensures the application remains functional even if templates are misconfigured.

## Template Loading

Templates are loaded by `backend/rag/prompt/loader.py` which:
- Caches templates in memory for performance
- Supports variable substitution
- Provides helpful error messages if templates are missing
