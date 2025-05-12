#!/usr/bin/env python3
"""Debug script to test parse_task_inline_string with test cases."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tasknotes.core.markdown import parse_task_inline_string, is_valid_task_id
from tasknotes.core.markdown import try_parse_code_span, try_parse_link, try_parse_plain_text
from tree_sitter import Language, Parser
import tree_sitter_markdown

def print_node_recursive(node, content, level=0):
    """Print a node and its children with indentation."""
    indent = "  " * level
    node_text = content[node.start_byte:node.end_byte]
    print(f"{indent}{node.type} [{node.start_byte}:{node.end_byte}]: '{node_text}'")
    
    for child in node.children:
        print_node_recursive(child, content, level + 1)

def debug_parse(text):
    """Debug the parsing of a task inline string."""
    print(f"\n=== Testing: '{text}' ===")
    
    # Initialize inline parser
    inline_parser = Parser()
    inline_parser.language = Language(tree_sitter_markdown.inline_language())
    
    # Parse with inline parser
    inline_tree = inline_parser.parse(bytes(text, 'utf8'))
    inline_root = inline_tree.root_node
    
    print("Tree structure:")
    print_node_recursive(inline_root, text)
    
    # Test each helper function
    print("\nTesting helper functions:")
    
    # Test code spans
    for child in inline_root.children:
        if child.type == 'code_span':
            print(f"Code span: '{text[child.start_byte:child.end_byte]}'")
            task_id, link, remaining_text = try_parse_code_span(child, text)
            print(f"  try_parse_code_span result: task_id={task_id}, link={link}, text={remaining_text}")
    
    # Test links
    for child in inline_root.children:
        if child.type == 'inline_link':
            print(f"Link: '{text[child.start_byte:child.end_byte]}'")
            task_id, link, remaining_text = try_parse_link(child, text)
            print(f"  try_parse_link result: task_id={task_id}, link={link}, text={remaining_text}")
    
    # Test plain text
    task_id, remaining_text = try_parse_plain_text(text)
    print(f"try_parse_plain_text result: task_id={task_id}, text={remaining_text}")
    
    # Test full parsing
    result = parse_task_inline_string(text)
    print(f"\nFinal parsing result: {result}")
    
    return result

def main():
    # Test cases from test_parse_task_inline.py
    test_cases = [
        "`TASK-123` task description",
        "`TASK-123`: task description",
        "[`TASK-123`](Task-123.md)task description",
        "[`TASK-123`](Task-123.md):task description",
        "[`TASK-123`:](Task-123.md)task description",
        "[`TASK-123`](Task-123.md): task description",
        "`FEAT-101` new feature"
    ]
    
    for test_case in test_cases:
        debug_parse(test_case)

if __name__ == "__main__":
    main()
