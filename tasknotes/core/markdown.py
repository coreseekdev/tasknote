"""Tree-sitter based implementation of the markdown service interfaces.

This module provides concrete implementations of the markdown service interfaces
using the tree-sitter parser for markdown document analysis.
"""

from typing import Dict, List, Iterator, Any, Optional, Tuple
import yaml
import re
from dataclasses import dataclass
from tree_sitter import Language, Parser

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
                block = self._service._process_list_block(current, self._content, 0)
                if block:
                    self._lists.append(block)
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
        
        # Check if this is an ordered list item
        raw_text = content[node.start_byte:node.end_byte]
        ordered_match = re.match(r'^\s*(\d+)\.', raw_text)
        if ordered_match:
            order = int(ordered_match.group(1))
        
        # Process item content
        for child in node.children:
            if child.type == 'task_list_marker_checked':
                is_task = True
                is_completed = True
            elif child.type == 'task_list_marker_unchecked':
                is_task = True
                is_completed = False
            elif child.type == 'paragraph':
                text = content[child.start_byte:child.end_byte].strip()
        
        # Remove list markers from text
        text = re.sub(r'^\s*\d+\.\s+|^\s*[-*]\s+', '', text)
        
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
                nested_block = self._process_list_block(child, content, level + 1)
                if nested_block:
                    item.add_nested_list(nested_block)
        
        return item
    
    def _process_list_block(self, node, content: str, level: int) -> Optional[TreeSitterListBlock]:
        """Process a list node and its items.
        
        Args:
            node: The tree-sitter node representing the list.
            content: The full markdown content.
            level: The nesting level of the list.
            
        Returns:
            A TreeSitterListBlock object, or None if the node is not a valid list.
        """
        items = []
        
        # Determine if this is an ordered list
        first_item = next((c for c in node.children if c.type == 'list_item'), None)
        if not first_item:
            return None
            
        raw_text = content[first_item.start_byte:first_item.end_byte]
        is_ordered = bool(re.match(r'^\s*\d+\.', raw_text))
        
        # Process all items
        for child in node.children:
            if child.type == 'list_item':
                item = self._process_list_item(child, content, level)
                if item:
                    items.append(item)
        
        if not items:
            return None
            
        # Create list block
        return TreeSitterListBlock(
            _items=items,
            _level=level,
            _start_pos=node.start_byte,
            _end_pos=node.end_byte,
            _ordered=is_ordered
        )
    
    def get_meta(self, content: str) -> DocumentMeta:
        """Extract metadata (YAML frontmatter) from the markdown content."""
        tree = self.parser.parse(bytes(content, 'utf8'))
        root_node = tree.root_node
        
        # Find frontmatter section
        for child in root_node.children:
            if child.type == 'minus_metadata':
                yaml_text = content[child.start_byte:child.end_byte]
                start_pos = child.start_byte
                end_pos = child.end_byte
                
                try:
                    # PyYAML can handle documents with --- markers directly
                    for doc in yaml.safe_load_all(yaml_text):
                        if doc and isinstance(doc, dict):
                            return TreeSitterDocumentMeta(
                                _data=doc,
                                _start_pos=start_pos,
                                _end_pos=end_pos
                            )
                except yaml.YAMLError:
                    pass
                    
        # Return empty metadata if no frontmatter found
        return TreeSitterDocumentMeta(
            _data={},
            _start_pos=0,
            _end_pos=0
        )
    
    def get_headers(self, content: str) -> Iterator[HeadSection]:
        """Extract all headers from the markdown content.
        
        This method only extracts the headers and doesn't process lists or other content.
        Lists are processed lazily when HeadSection.get_lists() is called.
        
        Args:
            content: The markdown content to parse.
            
        Returns:
            An iterator of HeadSection objects.
        """
        tree = self.parser.parse(bytes(content, 'utf8'))
        
        # Find all header nodes
        def find_headers(node):
            if node.type == 'atx_heading':
                header = self._process_header_node(node, content)
                if header:
                    yield header
            
            # Continue with children
            for child in node.children:
                yield from find_headers(child)
        
        yield from find_headers(tree.root_node)
    
    def _process_header_node(self, node, content: str) -> Optional[TreeSitterHeadSection]:
        """Process a header node and extract its text and level.
        
        Args:
            node: The tree-sitter node representing the header.
            content: The full markdown content.
            
        Returns:
            A TreeSitterHeadSection object, or None if the node is not a valid header.
        """
        if node.type != 'atx_heading':
            return None
            
        # Get header level (number of #)
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
        
        if not level:
            return None
            
        # Find the end of the section by looking for the next header
        end_pos = len(content)
        current = node
        while current:
            current = current.next_sibling
            if current and current.type == 'atx_heading':
                end_pos = current.start_byte
                break
            
        # Create header section with node reference
        return TreeSitterHeadSection(
            _text=text,
            _level=level,
            _start_pos=node.start_byte,
            _end_pos=end_pos,
            _node=node,
            _content=content,
            _service=self
        )


def create_markdown_service() -> MarkdownService:
    """Create a new instance of the markdown service.
    
    Returns:
        A concrete implementation of the MarkdownService interface.
    """
    return TreeSitterMarkdownService()
