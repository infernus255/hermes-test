#!/usr/bin/env python3
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = REPO_ROOT / "state.json"
DOCKERFILE = REPO_ROOT / "Dockerfile"


def load_state():
    if not STATE_FILE.exists():
        raise SystemExit(f"No existe {STATE_FILE}. Ejecute skills/scripts/skill_state.py primero.")
    return json.loads(STATE_FILE.read_text())


def parse_dockerfile_packages(content):
    pattern = re.compile(r"apt-get install -y(.*?)(?:\\n|$)", re.S)
    match = pattern.search(content)
    if not match:
        return []
    package_block = match.group(1)
    package_lines = package_block.replace('\\', ' ').split()
    return [pkg.strip() for pkg in package_lines if pkg.strip()]


def update_dockerfile(content, required_packages):
    current = parse_dockerfile_packages(content)
    missing = [pkg for pkg in required_packages if pkg not in current]
    if not missing:
        return content, []
    updated_lines = []
    for line in content.splitlines():
        if "apt-get install -y" in line:
            prefix = line.split("apt-get install -y", 1)[0] + "apt-get install -y"
            updated_lines.append(prefix + " \\")
            for pkg in sorted(set(current + required_packages)):
                updated_lines.append(f"    {pkg} \\")
        else:
            updated_lines.append(line)
    updated_content = "\n".join(updated_lines) + "\n"
    return updated_content, missing


def main():
    state = load_state()
    required = state.get("system", {}).get("required_packages", [])
    dockerfile_text = DOCKERFILE.read_text()
    updated_text, missing = update_dockerfile(dockerfile_text, required)
    if not missing:
        print(f"Dockerfile ya contiene los paquetes requeridos: {required}")
        return
    DOCKERFILE.write_text(updated_text)
    print(f"Dockerfile actualizado con paquetes adicionales: {missing}")


if __name__ == "__main__":
    main()
