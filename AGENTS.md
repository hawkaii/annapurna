# AGENTS.md

## Build, Lint, and Test Commands
- **Install dependencies:**
  ```bash
  uv venv && uv sync && source .venv/bin/activate
  ```
- **Run the server:**
  ```bash
  cd mcp-bearer-token && python mcp_starter.py
  ```
- **Linting:**
  - No linter configured by default. Use `ruff` or `flake8` for PEP8 compliance if needed.
- **Testing:**
  - No test framework present. To add tests, use `pytest` and run:
    ```bash
    pytest path/to/test_file.py::test_function_name
    ```

## Code Style Guidelines
- **Imports:** Group as stdlib, third-party, then local. One import per line.
- **Formatting:** Follow PEP8. Use 4 spaces for indentation.
- **Types:** Use type hints everywhere (functions, variables, class attributes).
- **Naming:**
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Error Handling:**
  - Use exceptions (e.g., `McpError`) for error reporting.
  - Return JSON-RPC error codes for protocol errors.
- **Environment:**
  - Load secrets from `.env` (see `.env.example`).
- **Async:**
  - Use `async def` for all tool functions and server entrypoints.

_No Cursor or Copilot rules detected._
