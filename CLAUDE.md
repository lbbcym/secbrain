# Claude Code Instructions for SecBrain

## After completing any task

1. **Always commit your work.** Stage all relevant changes and create a commit with a clear message following the project's `<type>: <description>` format (feat, fix, docs, style, refactor, test, chore).
2. **Clean up temporary files.** Remove any scratch files, temp outputs, or artifacts created during the session (e.g., `commitmsg.txt`, leftover debug files).
3. **Clean up branches.** If you created a feature branch and the work is merged or complete, delete it. The default workflow is to work directly on `main` unless the user says otherwise.
4. **Do not push** unless the user explicitly asks.

## Platform and environment

- This project is developed on **Windows** but tools like Foundry, nuclei, and shell scripts target **Linux/WSL**.
- Always use `pathlib.Path` for file operations, never `os.path`.
- Use `Path.expanduser()` when resolving paths that contain `~`.
- Use `shutil.which()` to verify tool availability before calling external executables.
- Never hardcode platform-specific paths (`/usr/bin/`, `C:\`, `/mnt/c/`).
- The repo has a `.gitattributes` enforcing LF line endings for scripts and source files. Do not override this.

## Code standards

- Python 3.11+, strict mypy typing, ruff linting (line length 100).
- Use structlog for logging, not print statements.
- Follow existing patterns in the codebase for new code.
- Tests go in `secbrain/tests/`. Run with: `cd secbrain && pytest tests/ -v`
