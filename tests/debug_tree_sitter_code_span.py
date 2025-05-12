#!/usr/bin/env python3
"""Debug script to examine tree-sitter's parsing of code spans in markdown."""

from tree_sitter import Language, Parser
import tree_sitter_markdown
import sys

def print_node(node, content, level=0):
    """Print a node and its children with indentation."""
    indent = "  " * level
    node_text = content[node.start_byte:node.end_byte]
    print(f"{indent}{node.type} [{node.start_byte}:{node.end_byte}]: '{node_text}'")
    
    for child in node.children:
        print_node(child, content, level + 1)

def main():
    # Initialize tree-sitter parser
    parser = Parser()
    parser.language = Language(tree_sitter_markdown.language())
    
    # Initialize inline parser
    inline_parser = Parser()
    inline_parser.language = Language(tree_sitter_markdown.inline_language())
    
    # Test content with code spans
    test_cases = [
        "`TASK-123` task description",
        "`TASK-123`: task description",
        "Regular text with `code` inside"
    ]
    
    for i, content in enumerate(test_cases):
        print(f"\n=== Test Case {i+1}: '{content}' ===")
        
        # Parse with main parser
        tree = parser.parse(bytes(content, 'utf8'))
        root_node = tree.root_node
        
        print("Main parser result:")
        print_node(root_node, content)
        
        # Parse with inline parser
        inline_tree = inline_parser.parse(bytes(content, 'utf8'))
        inline_root = inline_tree.root_node
        
        print("\nInline parser result:")
        print_node(inline_root, content)

if __name__ == "__main__":
    main()
