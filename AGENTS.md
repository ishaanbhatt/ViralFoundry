# Agent Instructions

## Git Workflow

- Before making code changes, inspect the current git branch, status, and remotes so the working tree state and publish target are clear.
- For each change made to this project, commit the relevant files with a clear message.
- After each successful commit, push the commit to the configured GitHub remote.
- If no GitHub remote is configured, do not guess the destination. Tell the user that the commit is local and ask for the intended GitHub remote URL before pushing.
- Do not revert or overwrite user changes unless the user explicitly asks for that.
