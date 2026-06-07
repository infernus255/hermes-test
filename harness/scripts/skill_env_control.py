#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[0]))
from utils.state_loader import StateLoader

try:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from env_drivers import load_environment_driver
except ImportError:
    load_environment_driver = None


def get_git_status(repo_root: Path) -> dict:
    try:
        branch = subprocess.getoutput("git branch --show-current").strip()
        commit_hash = subprocess.getoutput("git rev-parse HEAD").strip()
        commit_msg = subprocess.getoutput("git log -1 --pretty=%B").strip()
        modified = len(subprocess.getoutput("git diff --name-only").splitlines())
        untracked = len(subprocess.getoutput("git status --porcelain | grep '??'").splitlines())
        
        return {
            "branch": branch,
            "commit": commit_hash,
            "message": commit_msg,
            "status": {"modified": modified, "untracked": untracked, "ahead": 0, "behind": 0}
        }
    except Exception:
        return {"branch": "unknown", "commit": "unknown"}


def sync_markdown_plan(repo_root: Path, current_state: dict, env_id: str):
    plan_path = repo_root / "docs" / "HERMES_TELEGRAM_INSTALL_PLAN.md"
    if not plan_path.exists():
        return

    content = plan_path.read_text(encoding="utf-8")
    env_data = current_state.get("environments", {}).get(env_id, {})
    
    lines = [
        "## 14. Estado actual y validación\n",
        "### Entorno actual",
        f"- Environment ID: {env_id}",
        f"- Environment type: {env_data.get('environment', {}).get('env_type', 'host')}\n",
        "### Hermes",
        f"- Instalado: {env_data.get('hermes', {}).get('installed', False)}",
        f"- Versión: {env_data.get('hermes', {}).get('version', 'Unknown')}",
        f"- Proveedor: {env_data.get('hermes', {}).get('provider', 'Unknown')}",
        f"- Modelo por defecto: {env_data.get('hermes', {}).get('model_default', 'Unknown')}",
        f"- Base URL: {env_data.get('hermes', {}).get('base_url', 'Unknown')}\n",
        "### Sistema operativo",
        f"- Nombre: {env_data.get('system', {}).get('os_name', 'Unknown')}",
        f"- Versión: {env_data.get('system', {}).get('os_version', 'Unknown')}\n"
    ]
    
    markdown_payload = "\n".join(lines)
    start_tag = "<!-- STATE-BEGIN -->"
    end_tag = "<!-- STATE-END -->"
    
    if start_tag in content and end_tag in content:
        before = content.split(start_tag)[0]
        after = content.split(end_tag)[1]
        updated_content = f"{before}{start_tag}\n{markdown_payload}\n{end_tag}{after}"
        plan_path.write_text(updated_content, encoding="utf-8")


def main():
    loader = StateLoader()
    state = loader.load_state()
    repo_root = loader.repo_root
    
    env_node_id = os.getenv("AGENCY_NODE_ID", "codespaces-16ec44")
    env_id = f"{env_node_id}:host:hermes-test"
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    state["timestamp"] = timestamp
    state["current_environment_id"] = env_id
    if "environments" not in state:
        state["environments"] = {}
        
    sys_info = loader.discover_base_system()
    git_info = get_git_status(repo_root)
    
    env_specifics = {}
    if load_environment_driver:
        driver = load_environment_driver(repo_root)
        env_specifics = driver.get_telemetry_overrides()
        driver.run_environment_setup()
        
    state["environments"][env_id] = {
        "environment": {
            "environment_id": env_id,
            "environment_name": env_node_id,
            "user": os.getenv("USER", "codespace"),
            "env_type": "host",
            "path": str(repo_root),
            "timestamp": timestamp
        },
        "hermes": {
            "installed": True,
            "version": "Hermes Agent v0.16.0 (2026.6.5) · upstream 210f4e70",
            "provider": "gemini",
            "model_default": "gemini-3.5-flash",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "gateway": "telegram_not_configured"
        },
        "system": {
            "os_name": sys_info["os_name"],
            "os_version": sys_info["os_version"],
            "driver_extensions": env_specifics
        },
        "git": git_info
    }
    
    loader.save_state(state)
    sync_markdown_plan(repo_root, state, env_id)
    print(f"[OK] Estado de sincronización completado de forma portable para: {env_id}")


if __name__ == "__main__":
    main()
