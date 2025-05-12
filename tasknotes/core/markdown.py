"""Tree-sitter based implementation of the markdown service interfaces.

This module provides concrete implementations of the markdown service interfaces
using the tree-sitter parser for markdown document analysis.
"""

from typing import Dict, List, Iterator, Any, Optional, Tuple
import yaml
from dataclasses import dataclass
from tree_sitter import Language, Parser

from tasknotes.interface.file_service import FileService
from tasknotes.interface.edit_session import EditSession, EditOperation

from tasknotes.interface.markdown_service import (
    MarkdownService,
    HeadSection,
    ListBlock,
    ListItem,
    DocumentMeta
)

@dataclass
class TreeSitterListItem(ListItem):
    """Tree-sitter implementation of a markdown list item."""
    _text: str
    _level: int
    _start_pos: int
    _end_pos: int
    _is_task: bool = False
    _is_completed: Optional[bool] = None
    _order: Optional[int] = None
    
    def __post_init__(self):
        self._nested_lists: List[ListBlock] = []
    
    @property
    def text(self) -> str:
        return self._text
    
    @property
    def text_range(self) -> Tuple[int, int]:
        return (self._start_pos, self._end_pos)
    
    @property
    def is_task(self) -> bool:
        return self._is_task
    
    @property
    def is_completed_task(self) -> Optional[bool]:
        return self._is_completed if self._is_task else None
    
    @property
    def order(self) -> Optional[int]:
        return self._order
    
    def get_lists(self) -> Iterator[ListBlock]:
        return iter(self._nested_lists)
    
    def add_nested_list(self, block: ListBlock) -> None:
        """Add a nested list block under this item."""
        self._nested_lists.append(block)

@dataclass
class TreeSitterListBlock(ListBlock):
    """Tree-sitter implementation of a markdown list block."""
    _items: List[TreeSitterListItem]
    _level: int
    _start_pos: int
    _end_pos: int
    _ordered: bool
    
    @property
    def ordered(self) -> bool:
        return self._ordered

    @property
    def is_ordered(self) -> bool:
        return self._ordered
    
    @property
    def text_range(self) -> Tuple[int, int]:
        return (self._start_pos, self._end_pos)
    
    def list_items(self) -> Iterator[ListItem]:
        return iter(self._items)
    
    def add_item(self, item: TreeSitterListItem) -> None:
        """Add an item to this list block."""
        self._items.append(item)

@dataclass
class TreeSitterHeadSection(HeadSection):
    """Tree-sitter implementation of a markdown header section."""
    _text: str
    _level: int
    _start_pos: int
    _end_pos: int
    _node: Any  # The tree-sitter node
    _content: str  # The full markdown content
    _service: Any  # Reference to the markdown service
    _lists_processed: bool = False
    
    def __post_init__(self):
        self._lists: List[ListBlock] = []
    
    @property
    def text(self) -> str:
        return self._text
    
    @property
    def head_level(self) -> int:
        return self._level
    
    @property
    def text_range(self) -> Tuple[int, int]:
        return (self._start_pos, self._end_pos)
    
    def get_lists(self) -> Iterator[ListBlock]:
        # Lazy loading of lists
        if not self._lists_processed:
            self._process_lists()
        return iter(self._lists)
    
    def _process_lists(self) -> None:
        """Process all lists under this header."""
        # Find the section range
        section_end = self._end_pos
        
        # Process all nodes in the section
        current = self._node.next_sibling
        while current and current.start_byte < section_end:
            if current.type == 'list':
                blocks = self._service._process_list_block(current, self._content, 0)
                # Extend the lists with all blocks returned
                self._lists.extend(blocks)
            current = current.next_sibling
        
        self._lists_processed = True
    
    def add_list(self, block: ListBlock) -> None:
        """Add a list block under this header."""
        self._lists.append(block)

@dataclass
class TreeSitterDocumentMeta(DocumentMeta):
    """Tree-sitter implementation of markdown document metadata."""
    _data: Dict[str, Any]
    _start_pos: int
    _end_pos: int
    
    @property
    def data(self) -> Dict[str, Any]:
        return self._data
    
    @property
    def text_range(self) -> Tuple[int, int]:
        return (self._start_pos, self._end_pos)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the metadata by key.
        
        Args:
            key: The key to set
            value: The value to set for the key
        """
        self._data[key] = value
    
    def apply(self, edit_session: EditSession) -> str:
        """Apply the metadata changes to the file.
        
        This method writes the modified metadata back to the file using
        the provided EditSession and FileService.
        
        Args:
            edit_session: An EditSession instance for modifying the file content
            file_service: A FileService instance for saving the file
            path: The path to the file to update
        """
        # Convert metadata to YAML format
        yaml_text = "---\n" + yaml.safe_dump(self._data, default_flow_style=False) + "---\n"
        
        # If there's existing metadata, replace it; otherwise insert at the beginning
        if self._start_pos < self._end_pos:
            # Replace existing metadata
            op = edit_session.replace(self._start_pos, self._end_pos, yaml_text)
        else:
            # Insert at the beginning of the file
            op = edit_session.insert(0, yaml_text)
        
        # 返回更新后的内容，让调用者决定是否保存
        return edit_session.get_content()


class TreeSitterMarkdownService(MarkdownService):
    """Tree-sitter based implementation of the markdown service."""
    
    def __init__(self):
        # Initialize tree-sitter parser using installed package
        import tree_sitter_markdown as tsmarkdown
        
        # Create the parser with the markdown language
        self.parser = Parser()
        self.parser.language = Language(tsmarkdown.language())
        
    def _process_list_item(self, node, content: str, level: int) -> Optional[TreeSitterListItem]:
        """Process a list item node and its nested content.
        
        Args:
            node: The tree-sitter node representing the list item.
            content: The full markdown content.
            level: The nesting level of the list item.
            
        Returns:
            A TreeSitterListItem object, or None if the node is not a valid list item.
        """
        text = ""
        is_task = False
        is_completed = None
        order = None
        
        # Check for list markers
        for child in node.children:
            if child.type == 'list_marker_dot':
                # For ordered lists, extract the number before the dot
                marker_text = content[child.start_byte:child.end_byte]
                try:
                    # Extract just the number part
                    number_str = ''.join(c for c in marker_text if c.isdigit())
                    if number_str:
                        order = int(number_str)
                except ValueError:
                    pass
        
        # Process item content
        paragraph_text = ""
        for child in node.children:
            if child.type == 'task_list_marker_checked':
                is_task = True
                is_completed = True
            elif child.type == 'task_list_marker_unchecked':
                is_task = True
                is_completed = False
            elif child.type == 'paragraph':
                # Only include text from the paragraph node
                paragraph_text = content[child.start_byte:child.end_byte].strip()
                text = paragraph_text
        
        
        # Create list item
        item = TreeSitterListItem(
            _text=text,
            _level=level,
            _start_pos=node.start_byte,
            _end_pos=node.end_byte,
            _is_task=is_task,
            _is_completed=is_completed,
            _order=order
        )
        
        # Process nested lists
        for child in node.children:
            if child.type == 'list':
                nested_blocks = self._process_list_block(child, content, level + 1)
                # Add each block in the list to the item's nested lists
                for block in nested_blocks:
                    item.add_nested_list(block)
        
        return item
    
    def _process_list_block(self, node, content: str, level: int) -> List[TreeSitterListBlock]:
        """Process a list node and its items.
        
        Args:
            node: The tree-sitter node representing the list.
            content: The full markdown content.
            level: The nesting level of the list.
            
        Returns:
            A TreeSitterListBlock object, or None if the node is not a valid list.
        """
        
        # Determine if this is an ordered list by checking the first list_item's marker
        first_item = next((c for c in node.children if c.type == 'list_item'), None)
        if not first_item:
            return []

        # Check for list marker types
        is_ordered = any(c.type == 'list_marker_dot' for c in first_item.children)
        
        # Process all items
        current_items = []
        current_is_ordered = is_ordered
        blocks = []

        for child in node.children:
            if child.type == 'list_item':
                # Check if this item has a dot marker (ordered list)
                item_is_ordered = any(c.type == 'list_marker_dot' for c in child.children)
                
                # If order type changes, create a new block
                if item_is_ordered != current_is_ordered and current_items:
                    blocks.append(TreeSitterListBlock(
                        _items=current_items,
                        _level=level,
                        _start_pos=current_items[0]._start_pos,
                        _end_pos=current_items[-1]._end_pos,
                        _ordered=current_is_ordered
                    ))
                    current_items = []
                    current_is_ordered = item_is_ordered
                
                item = self._process_list_item(child, content, level)
                if item:
                    current_items.append(item)
        
        # Create final block if there are remaining items
        if current_items:
            blocks.append(TreeSitterListBlock(
                _items=current_items,
                _level=level,
                _start_pos=current_items[0]._start_pos,
                _end_pos=current_items[-1]._end_pos,
                _ordered=current_is_ordered
            ))
        
        # Always return the list of blocks, even if empty
        return blocks
    
    def get_meta(self, content: str) -> DocumentMeta:
        """Extract metadata (YAML frontmatter) from the markdown content.
        
        This method reuses the parse method to ensure consistent behavior.
        """
        meta, _ = self.parse(content)
        return meta
    
    def get_headers(self, content: str) -> Iterator[HeadSection]:
        """Extract all headers from the markdown content.
        
        This method only extracts the headers and doesn't process lists or other content.
        """
        _, headers = self.parse(content)
        return headers
    
    def parse(self, content: str) -> Tuple[DocumentMeta, Iterator[HeadSection]]:
        """Parse markdown content and extract both metadata and headers.
        
        This method efficiently extracts both metadata and headers in a single parse operation,
        avoiding the need to parse the markdown content twice.
        
        Args:
            content: The markdown document text to parse
            
        Returns:
            A tuple containing:
            - DocumentMeta: The parsed metadata from the document
            - Iterator[HeadSection]: An iterator over all header sections in the document
        """
        # Parse the content once
        tree = self.parser.parse(bytes(content, 'utf8'))
        root_node = tree.root_node
        
        # Extract metadata
        meta = TreeSitterDocumentMeta(_data={}, _start_pos=0, _end_pos=0)
        for child in root_node.children:
            if child.type == 'minus_metadata':
                yaml_text = content[child.start_byte:child.end_byte]
                start_pos = child.start_byte
                end_pos = child.end_byte
                
                try:
                    # PyYAML can handle documents with --- markers directly
                    for doc in yaml.safe_load_all(yaml_text):
                        if doc and isinstance(doc, dict):
                            meta = TreeSitterDocumentMeta(
                                _data=doc,
                                _start_pos=start_pos,
                                _end_pos=end_pos
                            )
                            break
                except yaml.YAMLError:
                    pass
        
        # Extract headers
        # First collect all header nodes
        header_nodes = []
        
        def collect_headers(node):
            if node.type == 'atx_heading':
                header_nodes.append(node)
        
            # Continue with children
            for child in node.children:
                collect_headers(child)
        
        collect_headers(root_node)
        
        # Sort header nodes by their position in the document
        header_nodes.sort(key=lambda node: node.start_byte)
        
        # Process headers in order
        headers_list = []
        for i, node in enumerate(header_nodes):
            # If this is not the last header, set its end position to the start of the next header
            next_pos = header_nodes[i+1].start_byte if i < len(header_nodes) - 1 else len(content)
        
            # Get header level and text
            level = 0
            text = ""
            for child in node.children:
                if child.type == 'atx_h1_marker':
                    level = 1
                elif child.type == 'atx_h2_marker':
                    level = 2
                elif child.type == 'atx_h3_marker':
                    level = 3
                elif child.type == 'atx_h4_marker':
                    level = 4
                elif child.type == 'atx_h5_marker':
                    level = 5
                elif child.type == 'atx_h6_marker':
                    level = 6
                elif child.type == 'inline':
                    text = content[child.start_byte:child.end_byte].strip()
        
            if level:
                # Create header section with node reference
                header = TreeSitterHeadSection(
                    _text=text,
                    _level=level,
                    _start_pos=node.start_byte,
                    _end_pos=next_pos,
                    _node=node,
                    _content=content,
                    _service=self
                )
                headers_list.append(header)
    
        # Return headers as an iterator
        headers = iter(headers_list)
        
        return meta, headers
    
    # _process_header_node 方法已被移除，因为其功能已被整合到 parse 方法中


def create_markdown_service() -> MarkdownService:
    """Create a new instance of the markdown service.
    
    Returns:
        A concrete implementation of the MarkdownService interface.
    """
    return TreeSitterMarkdownService()
