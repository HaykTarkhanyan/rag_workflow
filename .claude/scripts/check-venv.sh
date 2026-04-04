#!/bin/bash
# Pre-Bash hook: warn if running python without .venv
# $TOOL_INPUT is JSON like {"command":"python ...","description":"..."}

# Extract the command field from JSON input
CMD=$(echo "$TOOL_INPUT" | grep -oP '"command"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"$//')

if [ -z "$CMD" ]; then
    exit 0
fi

# Only check if command starts with python (not .venv/Scripts/python)
if echo "$CMD" | grep -qE '^python[3.]?(\s|$)' 2>/dev/null; then
    if ! echo "$CMD" | grep -q '.venv' 2>/dev/null; then
        echo "WARNING: Use .venv/Scripts/python.exe instead of system python"
        echo "System Python has corrupted metadata and may segfault."
        exit 1
    fi
fi
exit 0
