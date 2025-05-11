"""Test script for the TaskNote CLI."""

import os
import sys
import json

# Set debug mode for testing
os.environ["TASKNOTE_CLI_DEBUG"] = "1"

import sys
import shlex

# Import the main function
from tasknotes.cli.main import main

def test_command(command_line):
    """Test a command by setting sys.argv and calling main().
    
    Args:
        command_line: A command line string to parse and execute
    """
    print(f"\nTesting command: {command_line}")
    
    # Use shlex.split to handle shell-like argument parsing
    # This correctly handles quotes, escapes, etc.
    args = shlex.split(command_line)
    
    sys.argv = ["tasknote"] + args
    main()
    print("-" * 40)

if __name__ == "__main__":
    # Test various commands
    try:
        # Basic commands
        test_command("init --git")
        test_command("add --parent TASK-001 --tag important --tag urgent 'Implement CLI parsing'")
        test_command("note --task TASK-001 --category meeting -m 'First point' -m 'Second point'")
        test_command("edit TASK-001")
        
        # List commands
        test_command("list --tag important")
        test_command("list active")
        
        # Task management commands
        test_command("archive TASK-001 --yes")
        test_command("remove TASK-001 --force --yes")
        test_command("open TASK-001")
        test_command("active")
        test_command("active TASK-001")
        test_command("close")
        test_command("close TASK-001")
        test_command("done TASK-001")
        
        # Tag commands
        test_command("tag TASK-001 --tag important --tag urgent --replace")
        test_command("tag TASK-001 --group status --ordered")
        
        # Search and help commands
        test_command("search 'important task' --tag urgent --all")
        test_command("help add")
        
        # MCP command
        test_command("mcp --port 8888 --host 0.0.0.0 --auth secret-token")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
