# Project Guidelines

## Package Management

- Use `uv` instead of `pip` for installing and managing Python packages.

## Long-Running Commands

- Always ask the user before running any command with a timeout of more than 1 minute. Do not silently set long timeouts.
