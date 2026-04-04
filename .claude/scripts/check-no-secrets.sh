#!/bin/bash
# Pre-commit hook: check for API keys in staged files
# Returns non-zero exit code if secrets found

STAGED=$(git diff --cached --name-only 2>/dev/null)
if [ -z "$STAGED" ]; then
    exit 0
fi

FOUND=0
for file in $STAGED; do
    if [ -f "$file" ]; then
        # Check for common API key patterns
        if grep -qE '(AIza[0-9A-Za-z_-]{35}|sk-[a-zA-Z0-9]{48}|GEMINI_API_KEY\s*=\s*[A-Za-z0-9])' "$file" 2>/dev/null; then
            echo "WARNING: Possible API key found in $file"
            FOUND=1
        fi
    fi
done

if [ $FOUND -eq 1 ]; then
    echo "BLOCKED: Remove API keys before committing. Use .env (gitignored) for secrets."
    exit 1
fi
exit 0
