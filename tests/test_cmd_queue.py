#!/usr/bin/env python
"""Test script for the command queue system with StringIO content display."""

import os
import sys
import io

# Set debug mode for testing
os.environ["TASKNOTE_CLI_DEBUG"] = "1"

from tasknotes.cmds.base_cmd import BaseCmd, CmdResult, create_string_input
from tasknotes.cmds.cmd_service import CmdService
from tasknotes.cmds.cmd_factory import cmd_factory
from tasknotes.cmds.cmd_init import InitCmd
from tasknotes.core.task_env import TaskNoteEnv

# Register commands
cmd_factory.register_cmd("init", InitCmd)

def test_command_with_string_input():
    """Test a command with StringIO input."""
    print("\nTesting command with StringIO input:")
    
    # Create a TaskNoteEnv for the current directory
    cwd = os.getcwd()
    task_env = TaskNoteEnv(cwd)
    
    # Create a command service
    cmd_service = CmdService(task_env)
    
    # Create a StringIO input with multi-line content
    content = "This is line 1\nThis is line 2\nThis is line 3"
    string_input = create_string_input(content)
    
    # Create a command with the StringIO input
    cmd = InitCmd("init", {"git": True}, stdin=string_input)
    
    # Print the command as JSON
    print(cmd)
    print("-" * 40)

def test_command_with_message_list():
    """Test a command with a list of messages."""
    print("\nTesting command with message list:")
    
    # Create a TaskNoteEnv for the current directory
    cwd = os.getcwd()
    task_env = TaskNoteEnv(cwd)
    
    # Create a command service
    cmd_service = CmdService(task_env)
    
    # Create a list of messages
    messages = [
        "First message",
        "Second message",
        "Third message with special chars: \n\t\"'[]{}",
    ]
    
    # Create a StringIO input from the messages
    string_input = create_string_input(messages)
    
    # Create a command with the StringIO input
    cmd = InitCmd("init", {"git": False, "messages": messages}, stdin=string_input)
    
    # Print the command as JSON
    print(cmd)
    print("-" * 40)

if __name__ == "__main__":
    test_command_with_string_input()
    test_command_with_message_list()
