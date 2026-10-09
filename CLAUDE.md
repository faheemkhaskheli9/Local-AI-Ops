# Local AI Ops: notes for Claude

This repo holds deterministic tools that save LLM tokens. Read this before working here.

## Using the tools (in any project)

- Before reading a large file (PDF, DOCX, HTML, long text) into context, run `aiops docs totext FILE --max-tokens N` or the `file_to_text` MCP tool.
- For mechanical work (format conversion, counting, filtering, dedupe, timestamps, chapters), call an existing tool instead of doing it by reasoning.
- For simple extraction or classification, try `aiops llm local` (free, cached) before using paid models.
- If you find yourself doing the same mechanical task a second time, suggest adding it here as a tool.

## Adding a tool

1. Put a pure function in the right module (`aiops/<area>/`). Create a new area folder with `__init__.py` if none fits.
2. Make it deterministic: no randomness, no time-dependent output, stable sort orders, explicit tie-breaks.
3. Heavy dependencies are optional: import them inside the function and add them to an extra in `pyproject.toml`.
4. If it calls a model, go through `aiops.core.llm` (temperature 0, seed, cache), or wrap it with `@cached`.
5. Add a test in `tests/` that runs without network, GPU or optional extras.
6. Add a CLI command in `aiops/cli.py`, and an MCP tool in `aiops/mcp_server.py` if Claude should call it.
7. Add a row to the table in `README.md`.

## Conventions

- Python 3.10+, standard library first, type hints.
- Never commit personal data: CVs, configs, databases, keys. See `.gitignore`.
- Run `pytest` before committing.
