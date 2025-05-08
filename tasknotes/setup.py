"""Setup utilities for TaskNotes."""

import os
import subprocess
from typing import Dict, Any, Optional, List, Tuple

from tasknotes.git_integration import GitIntegration
from tasknotes.config import Config


def setup_git_integration() -> bool:
    """Set up the git integration for TaskNotes."""
    return GitIntegration.setup_git_alias()


def setup_environment(config: Optional[Config] = None) -> Dict[str, Any]:
    """Set up the TaskNotes environment and return status information."""
    config = config or Config()
    
    # Ensure config directory exists
    os.makedirs(config.config_dir, exist_ok=True)
    
    # Ensure tasks directory exists
    os.makedirs(config.tasks_dir, exist_ok=True)
    
    # Set up git integration
    git_integration_status = setup_git_integration()
    
    return {
        "config_dir": config.config_dir,
        "tasks_dir": config.tasks_dir,
        "git_integration": git_integration_status
    }


def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are installed."""
    dependencies = {
        "git": False,
        "python": False,
        "myst-parser": False
    }
    
    # Check git
    try:
        subprocess.run(
            ["git", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        dependencies["git"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check python
    try:
        subprocess.run(
            ["python", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        dependencies["python"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check myst-parser
    try:
        import myst_parser
        dependencies["myst-parser"] = True
    except ImportError:
        pass
    
    return dependencies


def setup_command() -> None:
    """Run the setup command."""
    print("Setting up TaskNotes...")
    
    # Check dependencies
    dependencies = check_dependencies()
    all_deps_installed = all(dependencies.values())
    
    if not all_deps_installed:
        print("\nMissing dependencies:")
        for dep, installed in dependencies.items():
            status = "✓ Installed" if installed else "✗ Missing"
            print(f"  {dep}: {status}")
        
        if not dependencies["myst-parser"]:
            print("\nTo install myst-parser, run:")
            print("  pip install myst-parser")
        
        if not dependencies["git"]:
            print("\nGit is required for full functionality.")
            print("Please install Git from https://git-scm.com/downloads")
    
    # Set up environment
    config = Config()
    env_status = setup_environment(config)
    
    print("\nTaskNotes setup complete:")
    print(f"  Config directory: {env_status['config_dir']}")
    print(f"  Tasks directory: {env_status['tasks_dir']}")
    
    git_status = "✓ Configured" if env_status["git_integration"] else "✗ Not configured"
    print(f"  Git integration: {git_status}")
    
    if not env_status["git_integration"]:
        print("\nTo manually set up Git integration, run:")
        print("  git config --global alias.task '!tasknotes'")
    
    print("\nYou can now use TaskNotes with the following commands:")
    print("  tasknotes list")
    print("  git task list  (if git integration is configured)")
