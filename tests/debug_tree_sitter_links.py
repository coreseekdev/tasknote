#!/usr/bin/env python3
"""Debug script to examine tree-sitter's parsing of markdown links in list items."""

from tree_sitter import Language, Parser
import tree_sitter_markdown
import sys

def print_node(node, content, level=0):
    """Print a node and its children with indentation."""
    indent = "  " * level
    node_text = content[node.start_byte:node.end_byte]
    print(f"{indent}{node.type}: '{node_text}'")
    
    for child in node.children:
        print_node(child, content, level + 1)

def main():
    # Initialize tree-sitter parser
    parser = Parser()
    parser.language = Language(tree_sitter_markdown.language())
    
    # Test content with different link formats in list items
    content = """- [ ] [TASK-001: First task](TASK-001.md)
- [x] [`TASK-002: Second task`](TASK-002.md)
- Regular item with [link](some-link.md)
- [TASK-003: No checkbox](TASK-003.md)"""
    
    # Parse the content
    tree = parser.parse(bytes(content, 'utf8'))
    root_node = tree.root_node
    
    # Print the entire tree
    print("Full Tree Structure:")
    print_node(root_node, content)
    
    # Focus on list items
    print("\nList Items:")
    for node in root_node.children:
        if node.type == 'list':
            for item in node.children:
                if item.type == 'list_item':
                    print("\nList Item:")
                    print_node(item, content, 1)

if __name__ == "__main__":
    main()
