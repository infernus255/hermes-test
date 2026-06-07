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
