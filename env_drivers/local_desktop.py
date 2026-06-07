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
