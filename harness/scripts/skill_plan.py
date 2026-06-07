#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

from utils.state_loader import StateLoader

loader = StateLoader()
REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_FILE = REPO_ROOT / "docs" / "HERMES_TELEGRAM_INSTALL_PLAN.md"

STATE_BEGIN = "<!-- STATE-BEGIN -->"
STATE_END = "<!-- STATE-END -->"
AUTORUNNER_BEGIN = "<!-- AUTORUNNER-BEGIN -->"
AUTORUNNER_END = "<!-- AUTORUNNER-END -->"


def load_state():
    state = loader.load_state(force_reload=True)
    if not state:
        raise SystemExit(f"No existe {loader.state_file}. Ejecute harness/scripts/skill_state.py primero.")
    return state


def current_environment(state):
    env_id = state.get("current_environment_id")
    environments = state.get("environments", {})
    if env_id and env_id in environments:
        return environments[env_id]
    return state.get("environment", state)


def format_state(state):
    current = current_environment(state)
    hermes = current.get("hermes", {})
    system = current.get("system", {})
    git = current.get("git", {})
    api_keys = current.get("api_keys", {})
    lines = [
        "## 14. Estado actual y validación",
        "",
        "### Entorno actual",
        f"- Environment ID: {current.get('environment', {}).get('environment_id')}",
        f"- Environment type: {current.get('environment', {}).get('env_type')}",
        "",
        "### Hermes",
        f"- Instalado: {hermes.get('installed')}",
        f"- Versión: {hermes.get('version')}",
        f"- Proveedor: {hermes.get('provider')}",
        f"- Modelo por defecto: {hermes.get('model_default')}",
        f"- Base URL: {hermes.get('base_url')}",
        f"- Gateway Telegram: {hermes.get('gateway')}",
        "",
        "### Sistema operativo",
        f"- Nombre: {system.get('os_name')}",
        f"- Versión: {system.get('os_version')}",
        "- Paquetes verificados:",
    ]
    for package in system.get("packages_checked", []):
        lines.append(f"  - {package['package']}: {package['status']}")
    lines += [
        "",
        "### API keys",
        f"- Total de claves detectadas: {api_keys.get('summary', {}).get('total_keys', 0)}",
        f"- Proveedores: {', '.join(api_keys.get('summary', {}).get('providers', []))}",
    ]
    for key in api_keys.get("keys", []):
        limit = key.get("limit") if key.get("limit") is not None else "unknown"
        lines.append(f"  - {key.get('alias')} ({key.get('provider')}): limit={limit}, source={key.get('source')}")
    lines += [
        "",
        "### Repositorio git",
        f"- Rama: {git.get('branch')}",
        f"- Commit: {git.get('commit')}",
        f"- Mensaje: {git.get('message')}",
        f"- Cambios modificados: {git['status'].get('modified', 0)}",
        f"- Archivos no rastreados: {git['status'].get('untracked', 0)}",
        f"- Ahead: {git['status'].get('ahead', 0)}",
        f"- Behind: {git['status'].get('behind', 0)}",
    ]
    return "\n".join(lines) + "\n"


def format_autorunner(state):
    lines = [
        "## 15. Autorunner para IA de bajo tier",
        "",
        "Sigue estos pasos exactos en el orden dado. No hagas suposiciones adicionales.",
        "",
        "1. Actualiza el estado del proyecto:",
        "   - `python3 harness/scripts/skill_state.py`",
        "",
        "2. Actualiza el plan con el estado actual:",
        "   - `python3 harness/scripts/skill_plan.py`",
        "",
        "3. Si hay un nuevo aprendizaje, agrégalo a la memoria:",
        "   - `bash harness/scripts/skill_memory.sh \"Texto del aprendizaje\"`",
        "",
        "4. Sincroniza Docker con el estado del sistema operativo:",
        "   - `python3 harness/scripts/skill_docker.py`",
        "",
        "5. Reconstruye el contenedor para aplicar los cambios:",
        "   - `docker compose build --progress=plain`",
        "",
        "6. Verifica el contenedor y el gateway:",
        "   - `docker compose up -d`",
        "   - `docker compose logs -f`",
        "",
        "Este autorunner está diseñado para ser seguido literalmente por una IA de bajo tier."
    ]
    return "\n".join(lines) + "\n"


def update_plan_file(state):
    content = PLAN_FILE.read_text()
    state_section = format_state(state)
    autorunner_section = format_autorunner(state)
    if STATE_BEGIN in content and STATE_END in content:
        content = content.split(STATE_BEGIN)[0] + STATE_BEGIN + "\n" + state_section + STATE_END + content.split(STATE_END)[1]
    else:
        content = content.rstrip() + "\n\n" + STATE_BEGIN + "\n" + state_section + STATE_END + "\n\n"
    if AUTORUNNER_BEGIN in content and AUTORUNNER_END in content:
        content = content.split(AUTORUNNER_BEGIN)[0] + AUTORUNNER_BEGIN + "\n" + autorunner_section + AUTORUNNER_END + content.split(AUTORUNNER_END)[1]
    else:
        content = content.rstrip() + "\n\n" + AUTORUNNER_BEGIN + "\n" + autorunner_section + AUTORUNNER_END + "\n"
    PLAN_FILE.write_text(content)
    print(f"Plan actualizado en {PLAN_FILE}")


def main():
    state = load_state()
    update_plan_file(state)


if __name__ == "__main__":
    main()
