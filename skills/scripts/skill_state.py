#!/usr/bin/env python3
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = REPO_ROOT / "state.json"
DOCKER_IMAGE = "hermes-test"
KEY_LIMITS_FILE = REPO_ROOT / "api_key_limits.json"
API_KEY_LIMITS_ENV = "API_KEY_LIMITS"


def run_command(cmd, capture_output=True, check=False):
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, check=check)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def hash_key(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def parse_key_spec(spec):
    parts = spec.split(":", 1)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        return parts[0].strip(), parts[1].strip()
    return None, spec.strip()


def load_env_file(path):
    env = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def parse_key_limits(value):
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    limits = {}
    for item in re.split(r"[;,]", value):
        item = item.strip()
        if not item or ":" not in item:
            continue
        alias, raw_limit = item.split(":", 1)
        alias = alias.strip()
        try:
            limits[alias] = int(raw_limit.strip())
        except ValueError:
            continue
    return limits


def load_key_limit_config():
    limits = {}
    if KEY_LIMITS_FILE.exists():
        try:
            data = json.loads(KEY_LIMITS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "keys" in data:
                data = data["keys"]
            if isinstance(data, dict):
                limits.update(data)
        except json.JSONDecodeError:
            pass
    env_limits = os.getenv(API_KEY_LIMITS_ENV, "").strip()
    if env_limits:
        parsed = parse_key_limits(env_limits)
        limits.update(parsed)
    normalized = {}
    for alias, payload in limits.items():
        if isinstance(payload, dict) and "limit" in payload:
            normalized[alias] = payload
        elif isinstance(payload, (int, float)):
            normalized[alias] = {"limit": int(payload)}
        else:
            normalized[alias] = {"limit": None}
    return normalized


def format_key_limit(alias, key_id, limits):
    if alias and alias in limits:
        entry = limits[alias]
        return entry.get("limit"), entry
    if key_id in limits:
        entry = limits[key_id]
        return entry.get("limit"), entry
    return None, None


def extract_api_keys_data():
    env_values = {}
    env_values.update(os.environ)
    repo_env = REPO_ROOT / "hermes.env"
    if repo_env.exists():
        env_values.update(load_env_file(repo_env))
    home_env = Path.home() / ".hermes" / ".env"
    if home_env.exists():
        env_values.update(load_env_file(home_env))

    key_limits = load_key_limit_config()
    keys = []
    sources = []

    def add_key(provider, raw_value, source):
        if not raw_value:
            return
        if provider.endswith("_KEYS"):
            for chunk in re.split(r"[;,]", raw_value):
                chunk = chunk.strip()
                if not chunk:
                    continue
                alias, key = parse_key_spec(chunk)
                if not key:
                    continue
                key_id = hash_key(key)
                limit, limit_entry = format_key_limit(alias or key_id, key_id, key_limits)
                keys.append({
                    "provider": provider.replace("_KEYS", ""),
                    "alias": alias or f"key-{len(keys)+1}",
                    "key_id": key_id,
                    "limit": limit,
                    "limit_source": limit_entry if limit_entry else None,
                    "source": source,
                    "note": "Carga de múltiples claves API"
                })
        else:
            alias, key = parse_key_spec(raw_value)
            if not key:
                return
            key_id = hash_key(key)
            limit, limit_entry = format_key_limit(alias or key_id, key_id, key_limits)
            keys.append({
                "provider": provider,
                "alias": alias or "primary",
                "key_id": key_id,
                "limit": limit,
                "limit_source": limit_entry if limit_entry else None,
                "source": source,
                "note": "Clave API principal"
            })

    for name in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
        if name in env_values:
            add_key(name.replace("_API_KEY", ""), env_values[name], name)
    for name in ["GEMINI_API_KEYS", "GOOGLE_API_KEYS"]:
        if name in env_values:
            add_key(name.replace("_API_KEYS", ""), env_values[name], name)

    summary = {
        "total_keys": len(keys),
        "providers": sorted(set([key["provider"] for key in keys]))
    }
    return {
        "summary": summary,
        "keys": keys,
        "limits_source": "api_key_limits.json or API_KEY_LIMITS env"
    }


def get_hermes_status():
    result = {
        "installed": False,
        "version": None,
        "provider": None,
        "model_default": None,
        "base_url": None,
        "gateway": None,
    }
    hermes_path = shutil.which("hermes")
    if hermes_path:
        result["installed"] = True
        output = run_command(["hermes", "--version"]) or ""
        if output:
            version_line = output.splitlines()[0].strip()
            result["version"] = version_line
        config_output = run_command(["hermes", "config", "show"]) or ""
    else:
        docker_available = shutil.which("docker") is not None
        if docker_available:
            image_list = run_command(["docker", "images", "-q", DOCKER_IMAGE])
            if image_list:
                result["installed"] = True
                config_output = run_command([
                    "docker", "run", "--rm", "--entrypoint", "/bin/bash", DOCKER_IMAGE,
                    "-lc", 'hermes config show'
                ]) or ""
            else:
                config_output = ""
        else:
            config_output = ""

    if config_output:
        model_match = re.search(r"Model:\s+\{([^}]+)\}", config_output)
        if model_match:
            model_content = model_match.group(1)
            provider_match = re.search(r"'provider': '([^']+)'", model_content)
            default_match = re.search(r"'default': '([^']+)'", model_content)
            base_url_match = re.search(r"'base_url': '([^']+)'", model_content)
            if provider_match:
                result["provider"] = provider_match.group(1)
            if default_match:
                result["model_default"] = default_match.group(1)
            if base_url_match:
                result["base_url"] = base_url_match.group(1)
        if "Telegram:" in config_output:
            if "not configured" in config_output:
                result["gateway"] = "telegram_not_configured"
            else:
                result["gateway"] = "telegram_configured"

    return result


def get_system_state():
    system = {
        "os_name": None,
        "os_version": None,
        "packages_checked": [],
        "required_packages": [
            "curl",
            "git",
            "python3",
            "python3-venv",
            "python3-pip",
            "npm",
            "xz-utils",
            "ca-certificates"
        ]
    }
    if Path("/etc/os-release").exists():
        data = Path("/etc/os-release").read_text().splitlines()
        for line in data:
            if line.startswith("NAME="):
                system["os_name"] = line.split("=", 1)[1].strip().strip('"')
            if line.startswith("VERSION="):
                system["os_version"] = line.split("=", 1)[1].strip().strip('"')
    if shutil.which("lsb_release"):
        distro = run_command(["lsb_release", "-ds"])
        if distro:
            system["os_name"] = distro.strip('"')
    if shutil.which("dpkg-query"):
        for package in system["required_packages"]:
            installed = run_command(["dpkg-query", "-W", "-f=${Status}", package])
            status = "installed" if "install ok installed" in installed else "missing"
            system["packages_checked"].append({"package": package, "status": status})
    return system


def get_git_state():
    git = {
        "branch": None,
        "commit": None,
        "message": None,
        "status": {"modified": 0, "untracked": 0, "ahead": 0, "behind": 0}
    }
    if shutil.which("git"):
        branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        if branch:
            git["branch"] = branch
        commit = run_command(["git", "rev-parse", "HEAD"])
        if commit:
            git["commit"] = commit
        message = run_command(["git", "log", "-1", "--pretty=%B"])
        if message:
            git["message"] = message.strip()
        status_output = run_command(["git", "status", "--short"])
        for line in status_output.splitlines():
            if line.startswith("??"):
                git["status"]["untracked"] += 1
            else:
                git["status"]["modified"] += 1
        branch_status = run_command(["git", "status", "--branch", "--porcelain"]) or ""
        ahead = re.search(r"ahead (\d+)", branch_status)
        behind = re.search(r"behind (\d+)", branch_status)
        if ahead:
            git["status"]["ahead"] = int(ahead.group(1))
        if behind:
            git["status"]["behind"] = int(behind.group(1))
    return git


def get_environment_metadata():
    host_name = os.uname().nodename
    user = os.getenv("USER") or os.getenv("USERNAME") or "unknown"
    path = str(REPO_ROOT)
    in_container = False
    container_id = None
    env_type = "host"

    if Path("/proc/1/cgroup").exists():
        content = Path("/proc/1/cgroup").read_text(errors="ignore")
        if "docker" in content or "kubepods" in content or "containerd" in content:
            in_container = True
            env_type = "container"
            match = re.search(r"[0-9a-f]{64}", content)
            if match:
                container_id = match.group(0)
    env_id = os.getenv("ENVIRONMENT_ID") or os.getenv("HEREMES_ENVIRONMENT_ID")
    if not env_id:
        env_id = f"{host_name}:{env_type}:{os.path.basename(path)}"
        if container_id:
            env_id = f"{env_id}:{container_id[:12]}"

    metadata = {
        "environment_id": env_id,
        "environment_name": os.getenv("ENVIRONMENT_NAME") or host_name,
        "user": user,
        "env_type": env_type,
        "container_id": container_id,
        "path": path,
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }
    return metadata


def load_existing_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def main():
    existing_state = load_existing_state()
    environment = get_environment_metadata()
    env_id = environment["environment_id"]
    env_entry = {
        "environment": environment,
        "hermes": get_hermes_status(),
        "system": get_system_state(),
        "git": get_git_state(),
        "api_keys": extract_api_keys_data()
    }

    state = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "current_environment_id": env_id,
        "environment": environment,
        "environments": existing_state.get("environments", {})
    }
    state["environments"][env_id] = env_entry
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    print(f"Estado guardado en {STATE_FILE}")


if __name__ == "__main__":
    main()
