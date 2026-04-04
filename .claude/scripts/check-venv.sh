#!/bin/bash
# Pre-Bash hook: warn if running python without .venv
# $TOOL_INPUT is JSON like {"command":"python ...","description":"..."}

# Extract the command field -- use sed instead of grep -P for portability
CMD=$(echo "$TOOL_INPUT" | sed -n 's/.*"command" *: *"\([^"]*\)".*/\1/p' | head -1)

if [ -z "$CMD" ]; then
    exit 0
fi

# Check if command contains python without .venv (handles env vars, cd &&, etc.)
if echo "$CMD" | grep -qE '(^|\s|&&\s*|;\s*)python[3.]?\s' 2>/dev/null; then
    if ! echo "$CMD" | grep -q '.venv' 2>/dev/null; then
        echo "WARNING: Use .venv/Scripts/python.exe instead of system python"
        echo "System Python has corrupted metadata and may segfault."
        exit 1
    fi
fi
exit 0
