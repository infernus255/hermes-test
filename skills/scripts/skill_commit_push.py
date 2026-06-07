#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = REPO_ROOT / "state.json"
VALIDATION_FILES = [
    "state.json",
    "memory.md",
    "README.md",
    "docs/HERMES_TELEGRAM_INSTALL_PLAN.md",
    "docs/copilot-instructions.md",
    "skills/README.md",
    "skills/docs/COPILOT_SKILL.md",
    "docs/N8N.md",
    "Dockerfile",
    "docker-compose.yml",
    "docker-entrypoint.sh",
    "hermes-install.sh",
]


def run(cmd, check=True, capture_output=True):
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=True)


def validate_file(path):
    file_path = REPO_ROOT / path
    if not file_path.exists():
        return False, f"Falta el archivo requerido: {path}"
    if file_path.stat().st_size == 0:
        return False, f"El archivo {path} está vacío"
    return True, None


def load_state():
    if not STATE_FILE.exists():
        return None, "No se encontró state.json. Ejecuta skills/scripts/skill_state.py primero."
    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f), None


def current_state_entry(state):
    env_id = state.get("current_environment_id")
    environments = state.get("environments", {})
    if env_id and env_id in environments:
        return environments[env_id]
    return state.get("environment", state)


def validate_os(state):
    current = current_state_entry(state)
    system = current.get("system", {})
    if not system.get("os_name"):
        return False, "No se detectó el nombre del sistema operativo en state.json"
    missing = [pkg["package"] for pkg in system.get("packages_checked", []) if pkg["status"] != "installed"]
    if missing:
        return False, f"Paquetes faltantes o no instalados: {', '.join(missing)}"
    return True, None


def validate_hermes(state):
    current = current_state_entry(state)
    hermes = current.get("hermes", {})
    if not hermes.get("installed"):
        return False, "Hermes no está instalado según state.json"
    if not hermes.get("provider") or not hermes.get("model_default") or not hermes.get("base_url"):
        return False, "La configuración de Hermes no está completa en state.json"
    if shutil.which("hermes"):
        try:
            result = run(["hermes", "config", "show"], check=False)
            if result.returncode != 0:
                return False, "El binario Hermes existe pero no se pudo ejecutar 'hermes config show'"
        except Exception as exc:
            return False, f"Error al ejecutar Hermes: {exc}"
    return True, None


def validate_copilot_docs():
    docs = [
        ("docs/copilot-instructions.md", ["Use only the provided scripts", "skill_state.py", "skill_plan.py", "skill_docker.py"]),
        ("skills/docs/COPILOT_SKILL.md", ["deterministic", "state.json", "skill_memory.sh", "skill_state.py", "skill_docker.py"]),
    ]
    for path, phrases in docs:
        file_path = REPO_ROOT / path
        if not file_path.exists():
            return False, f"Falta la documentación de Copilot: {path}"
        content = file_path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in content:
                return False, f"El archivo {path} no menciona '{phrase}', debe incluir reglas de uso deterministas"
    return True, None


def validate_n8n():
    if not (REPO_ROOT / "docs" / "N8N.md").exists():
        return False, "Falta la documentación de n8n: docs/N8N.md"
    if not shutil.which("n8n"):
        return False, "n8n no está instalado o no está en el PATH"
    if shutil.which("pgrep"):
        proc = run(["pgrep", "-f", "n8n"], check=False)
        if proc.returncode != 0:
            return False, "n8n no parece estar levantado en el sistema"
    return True, None


def validate_api_keys(state):
    current = current_state_entry(state)
    api_keys = current.get("api_keys", {}).get("keys", [])
    if not api_keys:
        return False, "No se detectaron claves API en state.json. Ejecuta skills/scripts/skill_state.py con las claves definidas."
    missing = [key for key in api_keys if key.get("limit") is None]
    if missing:
        aliases = [key.get("alias") or key.get("key_id", "unknown") for key in missing]
        return False, f"Faltan límites para las claves API: {', '.join(aliases)}"
    return True, None


def validate_docker():
    dockerfile = REPO_ROOT / "Dockerfile"
    if not dockerfile.exists():
        return False, "Falta Dockerfile"
    if not shutil.which("docker"):
        return False, "docker no está instalado en el PATH"
    try:
        result = run(["docker", "compose", "config"], check=False)
        if result.returncode != 0:
            return False, "docker compose config falló, revisa docker-compose.yml"
    except Exception as exc:
        return False, f"Error al ejecutar docker compose config: {exc}"
    return True, None


def git_add_commit_push(message):
    run(["git", "add", "."])
    run(["git", "commit", "-m", message])
    run(["git", "push"])


def main():
    state, err = load_state()
    if err:
        print(err)
        sys.exit(1)

    print("Validando archivos de documentación...")
    errors = []
    for path in VALIDATION_FILES:
        ok, msg = validate_file(path)
        if not ok:
            errors.append(msg)

    print("Validando estado del sistema operativo...")
    ok, msg = validate_os(state)
    if not ok:
        errors.append(msg)

    print("Validando Hermes...")
    ok, msg = validate_hermes(state)
    if not ok:
        errors.append(msg)

    print("Validando documentación de Copilot...")
    ok, msg = validate_copilot_docs()
    if not ok:
        errors.append(msg)

    print("Validando claves API y límites...")
    ok, msg = validate_api_keys(state)
    if not ok:
        errors.append(msg)

    print("Validando n8n...")
    ok, msg = validate_n8n()
    if not ok:
        errors.append(msg)

    print("Validando Docker...")
    ok, msg = validate_docker()
    if not ok:
        errors.append(msg)

    if errors:
        print("\nValidación fallida con los siguientes errores:")
        for item in errors:
            print(f"- {item}")
        sys.exit(1)

    commit_message = "Auto commit: validate state/docs/hermes/copilot/n8n/docker and push"
    if len(sys.argv) > 1:
        commit_message = " ".join(sys.argv[1:])

    print("Todas las validaciones pasaron. Commit y push en progreso...")
    git_add_commit_push(commit_message)
    print("Commit y push completados.")


if __name__ == "__main__":
    main()
