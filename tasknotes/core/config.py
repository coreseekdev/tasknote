import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """
    Configuration manager for TaskNotes.
    Stores configuration in ~/.tasknote.yml and supports environment variable overrides.
    """
    
    DEFAULT_CONFIG = {
        "local": {
            "task_dir": ".tasknote"
        },
        "git": {
            "branch_name": "tasknote",
            "user_name": "TaskNotes User",
            "user_email": "user@tasknotes"
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the Config object.
        
        Args:
            config_path: Optional custom path for the config file.
                         If not provided, defaults to ~/.tasknote.yml
        """
        self._config_path = config_path or Path.home() / ".tasknote.yml"
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load config from file or return defaults if file doesn't exist"""
        config = self.DEFAULT_CONFIG.copy()
        
        if self._config_path.exists():
            with open(self._config_path, 'r') as f:
                file_config = yaml.safe_load(f) or {}
                config.update(file_config)
        
        # Apply environment variable overrides
        if "TASKNOTE_GIT_BRANCH" in os.environ:
            config["git"]["branch_name"] = os.environ["TASKNOTE_GIT_BRANCH"]
        if "TASKNOTE_GIT_USER" in os.environ:
            config["git"]["user_name"] = os.environ["TASKNOTE_GIT_USER"]
        if "TASKNOTE_GIT_EMAIL" in os.environ:
            config["git"]["user_email"] = os.environ["TASKNOTE_GIT_EMAIL"]
        if "TASKNOTE_LOCAL_DIR" in os.environ:
            config["local"]["task_dir"] = os.environ["TASKNOTE_LOCAL_DIR"]
            
        return config
    
    def save(self):
        """Save current config to file"""
        with open(self._config_path, 'w') as f:
            yaml.safe_dump(self._config, f)
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get config value by dot notation key (e.g. 'git.branch_name')"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, save: bool = False):
        """Set config value by dot notation key"""
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        
        if save:
            self.save()

# Global config instance
config = Config()
