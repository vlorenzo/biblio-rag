# Prompt Templates

This directory contains external prompt template files that define how the SmartAgent routes, retrieves, and synthesizes responses.

## Template Files

- **`smart_agent_router.txt`** - Router prompt for SmartAgent (decides when to use tools)
- **`smart_agent_synthesis.txt`** - Synthesis prompt for SmartAgent (builds final answer from tool output)
- **`smart_agent_system.txt`** - Fallback system prompt for SmartAgent if router/synthesis are unavailable
- **`smart_agent_finalizer.txt`** - Final output normalizer (enforces user-facing terminology)

## Variable Substitution

Templates support Python-style string formatting with `{variable_name}` placeholders:

- **`smart_agent_router.txt`** uses `{db_schema_description}` - dynamically inserted database schema information
- **`smart_agent_system.txt`** uses `{db_schema_description}` - dynamically inserted database schema information

## Editing Prompts

You can edit these `.txt` files directly without modifying Python code. Changes take effect on the next application restart.

### Example: Changing the Agent Name

To change the agent name from "Amalia" to something else:

1. Edit `smart_agent_router.txt` and replace "Amalia" with your desired name
2. Edit `smart_agent_synthesis.txt` and replace "Amalia" with your desired name
3. Edit `smart_agent_system.txt` and replace "Amalia" with your desired name
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
