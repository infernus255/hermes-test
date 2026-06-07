# Copilot instructions for hermes-test

This repository includes harness-engineered utility scripts that must be used as deterministic skills by Copilot.

Rules for Copilot:

- Use only the provided scripts for state, memory, plan, and Docker updates.
- Do not modify `state.json`, `memory.md`, `docs/HERMES_TELEGRAM_INSTALL_PLAN.md`, or `Dockerfile` by hand unless the change is the direct result of a script execution.
- Avoid freeform inference. The scripts are the source of truth.
- If the task is to capture system state, run:
  - `python3 skills/scripts/skill_state.py`
- If the task is to update plan documentation from state, run:
  - `python3 skills/scripts/skill_plan.py`
- If the task is to add a new memory item, run:
  - `bash skills/scripts/skill_memory.sh "Texto de aprendizaje"`
- If the task is to update Docker package requirements, run:
  - `python3 skills/scripts/skill_docker.py`
- If the task is to validate the harness and commit changes, run:
  - `python3 skills/scripts/skill_commit_push.py "Mensaje de commit"`
- Use `python3 skills/scripts/skill_state.py` to record the current environment in `state.json`.
- The state skill also detects multiple API keys and their configured limits.
- After script execution, verify the generated files and preserve their format.

Preferred deterministic workflow:

1. `python3 skills/scripts/skill_state.py`
2. `python3 skills/scripts/skill_plan.py`
3. `python3 skills/scripts/skill_docker.py`
4. `bash skills/scripts/skill_memory.sh "..."`

The goal is to keep this repo stable and predictable regardless of the AI used.
