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
