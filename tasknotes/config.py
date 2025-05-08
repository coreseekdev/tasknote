"""Configuration management for TaskNotes."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Manages configuration for the TaskNotes application."""
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize configuration with optional custom path."""
        # Default configuration directory is in user's home directory
        self.config_dir = config_path or os.path.join(
            os.path.expanduser("~"), ".tasknotes"
        )
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Configuration file path
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # Tasks directory
        self.tasks_dir = os.path.join(self.config_dir, "tasks")
        
        # Index file for tasks
        self.index_file = os.path.join(self.config_dir, "index.json")
        
        # Load or create configuration
        self._config = self._load_or_create_config()
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load existing configuration or create a new one."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # If the file is corrupted, create a new config
                return self._create_default_config()
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create and save default configuration."""
        default_config = {
            "tasks_dir": self.tasks_dir,
            "editor": os.environ.get("EDITOR", "notepad"),
            "default_status": "open",
            "statuses": ["open", "in-progress", "closed"],
            "git_integration": True,
        }
        
        # Ensure tasks directory exists
        os.makedirs(self.tasks_dir, exist_ok=True)
        
        # Save default configuration
        self.save(default_config)
        
        return default_config
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file."""
        if config:
            self._config = config
            
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save."""
        self._config[key] = value
        self.save()
    
    @property
    def editor(self) -> str:
        """Get the configured editor."""
        return self._config.get("editor", os.environ.get("EDITOR", "notepad"))
    
    @property
    def statuses(self) -> list:
        """Get the list of valid task statuses."""
        return self._config.get("statuses", ["open", "in-progress", "closed"])
    
    @property
    def default_status(self) -> str:
        """Get the default status for new tasks."""
        return self._config.get("default_status", "open")
