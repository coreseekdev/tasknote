#!/usr/bin/env python3

from tree_sitter import Parser, Language
import tree_sitter_markdown as tsmarkdown

def print_node_types(node, content, level=0):
    indent = "  " * level
    print(f"{indent}Node type: {node.type}")
    if node.type == 'list_item':
        print(f"{indent}Content: {content[node.start_byte:node.end_byte]}")
        print(f"{indent}Children types: {[c.type for c in node.children]}")
    for child in node.children:
        print_node_types(child, content, level + 1)

def main():
    # Create a simple markdown document with lists
    content = """1. First item
2. Second item
- Unordered item"""

    # Initialize parser
    parser = Parser()
    parser.language = Language(tsmarkdown.language())

    # Parse the content
    tree = parser.parse(bytes(content, "utf8"))
    print("Analyzing markdown document:")
    print(content)
    print("\nNode structure:")
    print_node_types(tree.root_node, content)

if __name__ == "__main__":
    main()
