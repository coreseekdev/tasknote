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
    # Initialize inline parser
    inline_parser = Parser()
    inline_parser.language = Language(tree_sitter_markdown.inline_language())
    
    # Test content with code spans
    test_cases = [
        "`TASK-123` task description",
        "`TASK-123`: task description",
        "[`TASK-123`](link.md) description"
    ]
    
    for i, content in enumerate(test_cases):
        print(f"\n=== Test Case {i+1}: '{content}' ===")
        
        # Parse with inline parser
        inline_tree = inline_parser.parse(bytes(content, 'utf8'))
        inline_root = inline_tree.root_node
        
        print("Inline parser result:")
        print_node(inline_root, content)
        
        # Print all children of code_span nodes
        print("\nCode span children:")
        for node in inline_root.children:
            if node.type == 'code_span':
                print(f"Code span: '{content[node.start_byte:node.end_byte]}'")
                for child in node.children:
                    print(f"  Child {child.type}: '{content[child.start_byte:child.end_byte]}'")
            elif node.type == 'link':
                print(f"Link: '{content[node.start_byte:node.end_byte]}'")
                for child in node.children:
                    print(f"  Child {child.type}: '{content[child.start_byte:child.end_byte]}'")
                    if child.type == 'link_text':
                        for subchild in child.children:
                            print(f"    Subchild {subchild.type}: '{content[subchild.start_byte:subchild.end_byte]}'")

if __name__ == "__main__":
    main()
