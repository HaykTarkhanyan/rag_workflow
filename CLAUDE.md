# Project Guidelines

## Package Management

- Use `uv` instead of `pip` for installing and managing Python packages.

## Long-Running Commands

- Always ask the user before running any command with a timeout of more than 1 minute. Do not silently set long timeouts.

## AI API Usage

- Every time an AI API request is made (Gemini, etc.), log and display the cost/token usage so the user knows how much it cost.
- Use `gemini-3-flash-preview` as the default Gemini model.
- API keys are stored in `.env` (gitignored).
- **IMPORTANT:** Never change AI model names, API configurations, or other critical parameters without asking the user first. Always confirm before making such changes.

## Logging

- Use Python's `logging` module for all scripts. Write detailed logs to `logs/` directory.
- Log file should include timestamps, module name, and log level.

## Python Environment

- Always use `.venv/Scripts/python.exe` for running project scripts, never system Python.
- System Python 3.10 has corrupted package metadata and will segfault on torch imports.
- The venv was created with `uv venv .venv --python python3.10`.

## Greeting / Session Start

When the user greets you (hi, hello, hey, etc.) or starts a new session, automatically:
1. Run `git fetch` and report current branch, any remote changes, open PRs
2. Check for other branches and uncommitted changes
3. Show a quick project status (corpus size, ChromaDB collections, pending TODOs from README)
4. Tell a short joke (not necessarily about programming)

## Hooks

The following hooks are configured in settings.json:
- **Pre-commit: No secrets** -- scans staged files for API key patterns, blocks commit if found
- **Post-stop: Memory reminder** -- after completing significant tasks, remind to update memory and _learning/
