# Project Guidelines

## Package Management

- Use `uv` instead of `pip` for installing and managing Python packages.

## Long-Running Commands

- Always ask the user before running any command with a timeout of more than 1 minute. Do not silently set long timeouts.

## AI API Usage

- Every time an AI API request is made (Gemini, etc.), log and display the cost/token usage so the user knows how much it cost.
- Use `gemini-2.5-flash` as the default Gemini model (update if user specifies differently).
- API keys are stored in `.env` (gitignored).
- **IMPORTANT:** Never change AI model names, API configurations, or other critical parameters without asking the user first. Always confirm before making such changes.

## Logging

- Use Python's `logging` module for all scripts. Write detailed logs to `logs/` directory.
- Log file should include timestamps, module name, and log level.
