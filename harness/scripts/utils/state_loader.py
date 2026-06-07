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
