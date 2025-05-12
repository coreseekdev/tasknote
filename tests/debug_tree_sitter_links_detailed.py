#!/usr/bin/env python3
"""Debug script to examine tree-sitter's parsing of markdown links in list items with more detail."""

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

def analyze_list_item_structure(item_node, content, level=0):
    """Analyze the structure of a list item node, focusing on nested lists and inline nodes."""
    indent = "  " * level
    item_text = content[item_node.start_byte:item_node.end_byte].strip()
    print(f"{indent}List Item: '{item_text}'")
    
    # Analyze direct children
    print(f"{indent}Direct children:")
    for child in item_node.children:
        child_text = content[child.start_byte:child.end_byte].strip()
        print(f"{indent}  {child.type} [{child.start_byte}:{child.end_byte}]: '{child_text}'")
        
        # Analyze paragraph children (looking for inline nodes)
        if child.type == 'paragraph':
            print(f"{indent}  Paragraph children:")
            for para_child in child.children:
                para_child_text = content[para_child.start_byte:para_child.end_byte].strip()
                print(f"{indent}    {para_child.type} [{para_child.start_byte}:{para_child.end_byte}]: '{para_child_text}'")
                
                # If this is an inline node, examine its structure
                if para_child.type == 'inline':
                    print(f"{indent}    Inline children:")
                    for inline_child in para_child.children:
                        inline_child_text = content[inline_child.start_byte:inline_child.end_byte]
                        print(f"{indent}      {inline_child.type} [{inline_child.start_byte}:{inline_child.end_byte}]: '{inline_child_text}'")
        
        # Look for nested lists
        elif child.type == 'list':
            print(f"{indent}  Found nested list:")
            analyze_list(child, content, level + 2)

def analyze_list(list_node, content, level=0):
    """Analyze the structure of a list node and its items."""
    indent = "  " * level
    list_text = content[list_node.start_byte:list_node.end_byte].strip()
    print(f"{indent}List: '{list_text[:50]}...' (truncated)")
    
    # Analyze list items
    for child in list_node.children:
        if child.type == 'list_item':
            analyze_list_item_structure(child, content, level + 1)

def main():
    # Initialize tree-sitter parser
    parser = Parser()
    parser.language = Language(tree_sitter_markdown.language())
    
    # Test content with different link formats in list items, including nested lists
    content = """- [ ] [TASK-001: First task](TASK-001.md)
  - Nested item under first task
  - Another nested item
- [x] [`TASK-002: Second task`](TASK-002.md)
  1. Nested ordered item with [link](nested-link.md)
  2. Second nested ordered item
- Regular item with [link](some-link.md)
  - Nested item with [another link](another-link.md)
    - Deeply nested item
- [TASK-003: No checkbox](TASK-003.md)"""
    
    # Parse the content
    tree = parser.parse(bytes(content, 'utf8'))
    root_node = tree.root_node
    
    # Analyze the document structure
    print("\nAnalyzing Document Structure:")
    print("==========================")
    
    # First print the overall tree structure
    print("\nOverall Tree Structure:")
    print_node(root_node, content, 0)
    
    # Then focus on lists and their items
    print("\nDetailed List Structure Analysis:")
    print("===============================")
    
    for node in root_node.children:
        if node.type == 'section':
            for section_child in node.children:
                if section_child.type == 'list':
                    analyze_list(section_child, content)
    
    # Specific focus on items with both links and nested lists
    print("\nItems with Both Links and Nested Lists:")
    print("====================================")
    
    found_complex_items = False
    for node in root_node.children:
        if node.type == 'section':
            for section_child in node.children:
                if section_child.type == 'list':
                    for item in section_child.children:
                        if item.type == 'list_item':
                            # Check if this item has both a paragraph with inline and a nested list
                            has_paragraph_with_inline = False
                            has_nested_list = False
                            
                            for child in item.children:
                                if child.type == 'paragraph':
                                    for para_child in child.children:
                                        if para_child.type == 'inline':
                                            has_paragraph_with_inline = True
                                elif child.type == 'list':
                                    has_nested_list = True
                            
                            if has_paragraph_with_inline and has_nested_list:
                                found_complex_items = True
                                item_text = content[item.start_byte:item.end_byte].strip().split('\n')[0] + '...'
                                print(f"\nFound item with both link and nested list: '{item_text}'")
                                analyze_list_item_structure(item, content)
    
    if not found_complex_items:
        print("No items found with both links and nested lists.")
        
    print("\nAnalysis Complete")

if __name__ == "__main__":
    main()
