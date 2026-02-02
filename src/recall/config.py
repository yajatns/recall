"""Configuration management for recall."""

from pathlib import Path
from typing import Any, Optional

import yaml

DEFAULT_CONFIG = {
    "model": "gpt-4o-mini",
    "db_path": "~/.recall/recall.db",
    "search_limit": 10,
    "editor": None,  # Uses $EDITOR or system default
}


class Config:
    """Manages recall configuration stored in ~/.recall/config.yaml."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path.home() / ".recall" / "config.yaml"
        self.config_path = config_path
        self._config = self._load()

    def _load(self) -> dict:
        """Load config from file, merging with defaults."""
        config = DEFAULT_CONFIG.copy()
        if self.config_path.exists():
            with open(self.config_path) as f:
                file_config = yaml.safe_load(f) or {}
                config.update(file_config)
        return config

    def _save(self):
        """Save config to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False)

    def get(self, key: str) -> Any:
        """Get a config value."""
        return self._config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any):
        """Set a config value and save."""
        # Convert string values to appropriate types
        if key == "search_limit":
            value = int(value)
        elif key == "db_path":
            value = str(value)

        self._config[key] = value
        self._save()

    def all(self) -> dict:
        """Get all config values."""
        return self._config.copy()

    @property
    def db_path(self) -> Path:
        """Get the database path, expanding ~ if present."""
        path = self.get("db_path")
        return Path(path).expanduser()

    @property
    def model(self) -> str:
        """Get the default model."""
        return self.get("model")

    @property
    def search_limit(self) -> int:
        """Get the default search limit."""
        return self.get("search_limit")

    @property
    def editor(self) -> Optional[str]:
        """Get the preferred editor."""
        return self.get("editor")


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
