#!/usr/bin/env python3
"""Debug script to explore tree-sitter inline language parsing."""

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
    # Initialize main markdown parser
    md_parser = Parser()
    md_parser.language = Language(tree_sitter_markdown.language())
    
    # Initialize inline parser
    inline_parser = Parser()
    inline_parser.language = Language(tree_sitter_markdown.inline_language())
    
    # Test content with different link formats
    content = """- [ ] [TASK-001: First task](TASK-001.md)
- [x] [`TASK-002: Second task`](TASK-002.md)
- Regular item with [link](some-link.md)
- [TASK-003: No checkbox](TASK-003.md)"""
    
    # Parse the content with main parser
    tree = md_parser.parse(bytes(content, 'utf8'))
    root_node = tree.root_node
    
    # Find inline nodes and parse them with inline parser
    for node in root_node.children:
        if node.type == 'section':
            for section_child in node.children:
                if section_child.type == 'list':
                    for item in section_child.children:
                        if item.type == 'list_item':
                            # Find paragraph
                            paragraph = None
                            for child in item.children:
                                if child.type == 'paragraph':
                                    paragraph = child
                                    break
                            
                            if paragraph:
                                # Find inline node
                                for child in paragraph.children:
                                    if child.type == 'inline':
                                        inline_node = child
                                        inline_text = content[inline_node.start_byte:inline_node.end_byte]
                                        print(f"\nFound inline node: '{inline_text}'")
                                        
                                        # Parse with inline parser
                                        inline_tree = inline_parser.parse(bytes(inline_text, 'utf8'))
                                        inline_root = inline_tree.root_node
                                        
                                        print("Inline parsed structure:")
                                        print_node(inline_root, inline_text)
                                        
                                        # Try to extract link
                                        link_text = None
                                        link_url = None
                                        
                                        # Look for link nodes
                                        for inline_child in inline_root.children:
                                            if inline_child.type == 'link':
                                                print("\nFound link node:")
                                                print_node(inline_child, inline_text, 1)
                                                
                                                # Extract link text and destination
                                                for link_child in inline_child.children:
                                                    if link_child.type == 'link_text':
                                                        link_text = inline_text[link_child.start_byte:link_child.end_byte]
                                                    elif link_child.type == 'link_destination':
                                                        link_url = inline_text[link_child.start_byte:link_child.end_byte]
                                        
                                        if link_text is not None:
                                            print(f"Extracted link text: '{link_text}'")
                                        if link_url is not None:
                                            print(f"Extracted link URL: '{link_url}'")

if __name__ == "__main__":
    main()
