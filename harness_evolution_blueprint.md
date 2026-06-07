# Blueprint de Refactorización: Evolución Multi-Entorno y Optimización Quirúrgica de Tokens
> **Instrucciones para el Agente de IA (Copilot / Roo Code):** Lee este documento en su totalidad. Tu objetivo es implementar la infraestructura portable descrita abajo, refactorizar los scripts existentes de la carpeta `harness/scripts/` para eliminar la duplicación de I/O de contexto, e introducir aislamiento de entornos mediante drivers exclusivos.

---

## 1. Nueva Topología de Archivos a Crear
Debes asegurar la creación de los siguientes directorios y módulos relacionales dentro del repositorio:

```text
/workspaces/hermes-test
├── env_drivers/               <-- Carpeta exclusiva de abstracción de hardware/OS
│   ├── __init__.py            <-- Cargador dinámico / Factory pattern
│   ├── base_driver.py         <-- Contrato base (Fallback portátil)
│   ├── codespaces_cloud.py    <-- Parches específicos para GitHub Codespaces (Cloud/DinD)
│   └── local_desktop.py       <-- Parches específicos para entornos locales de desarrollo
├── config/
│   └── api_budget.json        <-- Presupuesto de tokens y control de rate-limiting compartido
├── harness/
│   └── scripts/
│       ├── utils/
│       │   └── state_loader.py <-- Singleton unificado con semáforo/lock para state.json
│       └── skill_env_control.py <-- Orquestador y generador de telemetría incremental
```

## 2. Código Base de la Infraestructura Central

Paso A: Crear harness/scripts/utils/state_loader.py
Este módulo centraliza el acceso a state.json. Resuelve la duplicación de lectura en disco mediante caché en memoria y previene condiciones de carrera concurrentes usando un semáforo atómico.

```python
import os
import json
import time
import shutil
import subprocess
from pathlib import Path

class StateLoader:
    _instance = None
    _cache = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateLoader, cls).__new__(cls)
        return cls._instance

    @property
    def repo_root(self) -> Path:
        override = os.getenv("REPO_ROOT_OVERRIDE")
        if override:
            return Path(override)
        return Path(__file__).resolve().parents[3]

    @property
    def lock_file(self) -> Path:
        return self.repo_root / ".harness_lock"

    @property
    def state_file(self) -> Path:
        return self.repo_root / "state.json"

    def acquire_lock(self, timeout=15):
        """Bloqueo portátil basado en filesystem para evitar colisiones de concurrencia."""
        start_time = time.time()
        while self.lock_file.exists():
            if time.time() - start_time > timeout:
                raise TimeoutError("Harness Lock Timeout: state.json bloqueado por otro proceso activo.")
            time.sleep(0.1)
        self.lock_file.write_text(str(os.getpid()), encoding="utf-8")

    def release_lock(self):
        if self.lock_file.exists():
            self.lock_file.unlink()

    def load_state(self, force_reload=False) -> dict:
        if self._cache and not force_reload:
            return self._cache
        
        if not self.state_file.exists():
            return {}
        
        self.acquire_lock()
        try:
            self._cache = json.loads(self.state_file.read_text(encoding="utf-8"))
            return self._cache
        finally:
            self.release_lock()

    def save_state(self, new_state: dict):
        self.acquire_lock()
        try:
            self.state_file.write_text(json.dumps(new_state, indent=2, ensure_ascii=False), encoding="utf-8")
            self._cache = new_state
        finally:
            self.release_lock()

    def discover_base_system(self) -> dict:
        """Detección de OS portable sin asumir dependencias de lsb_release o linux estático."""
        info = {"os_name": "Unknown", "os_version": "Unknown", "packages_checked": []}
        
        os_release = Path("/etc/os-release")
        if os_release.exists():
            lines = os_release.read_text(encoding="utf-8").splitlines()
            for line in lines:
                if line.startswith("PRETTY_NAME="):
                    info["os_name"] = line.split("=", 1)[1].replace('"', '')
                if line.startswith("VERSION="):
                    info["os_version"] = line.split("=", 1)[1].replace('"', '')
        else:
            info["os_name"] = os.name
            info["os_version"] = subprocess.getoutput("uname -r") if shutil.which("uname") else "Unknown"
            
        return info
```

Paso B: Estructura de la Capa Exclusiva env_drivers/

1. env_drivers/base_driver.py

```python
from pathlib import Path

class BaseDriver:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def get_env_name(self) -> str:
        return "Generic Linux Runtime"

    def get_telemetry_overrides(self) -> dict:
        return {}

    def run_environment_setup(self) -> bool:
        return True
```

2. env_drivers/codespaces_cloud.py

```python
import os
from .base_driver import BaseDriver

class CodespacesCloudDriver(BaseDriver):
    def get_env_name(self) -> str:
        return "GitHub Codespaces Cloud Environment"

    def get_telemetry_overrides(self) -> dict:
        return {
            "docker_mode": "Docker-in-Docker (DinD)",
            "persistence_layer": "Codespace Virtual Volume Shared Socket",
            "proxy_exposed_ports": ["9119"]
        }

    def run_environment_setup(self) -> bool:
        return True
```

3. env_drivers/local_desktop.py

```python
import platform
from .base_driver import BaseDriver

class LocalDesktopDriver(BaseDriver):
    def get_env_name(self) -> str:
        return f"Local Machine ({platform.system()})"

    def get_telemetry_overrides(self) -> dict:
        return {
            "docker_mode": "Native Desktop Daemon / Socket Local",
            "persistence_layer": "Direct Local System Link",
            "arch": platform.machine()
        }
```

4. env_drivers/__init__.py

```python
import os
from pathlib import Path
from .base_driver import BaseDriver
from .codespaces_cloud import CodespacesCloudDriver
from .local_desktop import LocalDesktopDriver

def load_environment_driver(repo_root: Path) -> BaseDriver:
    target = os.getenv("TARGET_ENV")
    if os.getenv("CODESPACES") == "true" or target == "codespaces":
        return CodespacesCloudDriver(repo_root)
    elif target == "local_pc":
        return LocalDesktopDriver(repo_root)
    return BaseDriver(repo_root)
```

## 3. El Controlador Central del Ecosistema: harness/scripts/skill_env_control.py
Este script asume la responsabilidad de mapear el estado y actualizar de forma segura el bloque dinámico <!-- STATE-BEGIN --> dentro del documento centralizado docs/HERMES_TELEGRAM_INSTALL_PLAN.md.

```python
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
            "base_url": "[https://generativelanguage.googleapis.com/v1beta/openai](https://generativelanguage.googleapis.com/v1beta/openai)",
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
```

## 4. Tareas Requeridas para el Asistente de IA (Plan de Ejecución Quirúrgica)

- Creación de Estructuras: Genera los archivos indicados en la sección 1 respetando las rutas exactas.
- Refactorización de Dependencias: Modifica harness/scripts/skill_state.py, harness/scripts/skill_docker.py y harness/scripts/skill_plan.py. Remueve de ellos cualquier función ad-hoc de lectura/escritura cruda sobre state.json. Importa en su lugar StateLoader y consume loader.load_state().
- Validación Incremental en skill_commit_push.py: Configura este script para que use el archivo de semáforo antes de iniciar el flujo de test de empaquetado de Docker y validación final de n8n.
- Política de Token Estricta: Reconfigura el análisis de archivos para que, si estás operando en modo Autopilot, leas el manifiesto de archivos modificados (`git diff --name-only`) en lugar de re-indexar pasivamente todo el repositorio en cada prompt.
