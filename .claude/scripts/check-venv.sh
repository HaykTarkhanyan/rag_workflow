#!/bin/bash
# Pre-Bash hook: warn if running python without .venv
# Checks if the command uses system python instead of .venv

CMD="$1"

# Only check python commands
if echo "$CMD" | grep -qE '^python[3.]* ' 2>/dev/null; then
    if ! echo "$CMD" | grep -q '.venv' 2>/dev/null; then
        echo "WARNING: Use .venv/Scripts/python.exe instead of system python"
        echo "System Python has corrupted metadata and may segfault."
        exit 1
    fi
fi
exit 0
