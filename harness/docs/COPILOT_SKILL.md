# Hermes Copilot Skill Documentation

These scripts are designed as deterministic Copilot skills for maintaining project state, learning, plan updates, and Docker synchronization.

## Available skills

- `harness/scripts/skill_memory.sh`
  - Appends a timestamped learning entry to `memory.md`.
  - No state inference; only writes the provided text.

- `harness/scripts/skill_state.py`
  - Gathers actual system and repo status.
  - Writes `state.json` from current machine state.
  - Records environment-specific state so this repo can learn from each environment independently.
  - Detects multiple API keys and tracks their configured limits.
  - Does not guess configuration; it reads Hermes, OS, and git directly.

- `harness/scripts/skill_plan.py`
  - Reads `state.json` and updates `docs/HERMES_TELEGRAM_INSTALL_PLAN.md`.
  - Inserts the current state section and a low-tier autorunner block.
  - Keeps the install plan reproducible and aligned with the current environment.

- `harness/scripts/skill_docker.py`
  - Reads `state.json` and synchronizes `Dockerfile` package installation with required packages.
  - Ensures the Docker build is consistent with the detected system state.
- `python3 harness/scripts/skill_commit_push.py "Mensaje de commit"`
  - Validates OS, docs, Hermes, Copilot, n8n, and Docker.
  - Commits and pushes only when all checks pass.
## Harness engineering principles

- Use scripts as deterministic tools.
- Avoid making ad hoc file edits when these scripts are available.
- Prefer concrete command execution over speculative AI changes.
- Maintain reproducibility across different Copilot sessions.

## Example usage

- To refresh project status:
  - `python3 harness/scripts/skill_state.py`
- To refresh the install plan:
  - `python3 harness/scripts/skill_plan.py`
- To add a learning entry:
  - `bash harness/scripts/skill_memory.sh "Detected missing npm package in environment"`
- To sync Docker with required packages:
  - `python3 harness/scripts/skill_docker.py`
