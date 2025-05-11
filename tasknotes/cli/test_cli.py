"""Test script for the TaskNote CLI."""

import os
import sys
import json

# Set debug mode for testing
os.environ["TASKNOTE_CLI_DEBUG"] = "1"

# Import the main function
from tasknotes.cli.main import main

def test_command(command_line):
    """Test a command by setting sys.argv and calling main()."""
    print(f"\nTesting command: {command_line}")
    # Handle arguments with spaces more carefully
    args = []
    in_quotes = False
    current_arg = ""
    quote_char = None
    
    for char in command_line:
        if char in ['"', "'"] and (not in_quotes or quote_char == char):
            in_quotes = not in_quotes
            if in_quotes:
                quote_char = char
            else:
                quote_char = None
        elif char.isspace() and not in_quotes:
            if current_arg:
                args.append(current_arg)
                current_arg = ""
        else:
            current_arg += char
    
    if current_arg:
        args.append(current_arg)
    
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
