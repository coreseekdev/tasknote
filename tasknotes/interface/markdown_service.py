"""Markdown document parsing service interface.

This module defines the core interfaces for parsing markdown documents,
providing access to structured elements like headers, lists, and frontmatter.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Iterator, Any, Optional, Tuple


class ListItem(ABC):
    """Represents a single item in a markdown list.
    
    A list item can be:
    - A regular unordered item (bullet point)
    - A numbered item with an order
    - A task item that may be completed
    - A parent item containing nested lists
    """
    
    @property
    @abstractmethod
    def text(self) -> str:
        """The text content of the list item, excluding markers and nesting."""
    
    @property
    def text_range(self) -> Tuple[int, int]:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_task(self) -> bool:
        """Whether this item represents a task (checkbox item)."""
    
    @property
    @abstractmethod
    def is_completed_task(self) -> Optional[bool]:
        """The completion status if this is a task item, None otherwise."""
    
    @property
    @abstractmethod
    def order(self) -> Optional[int]:
        """The item number if this is part of an ordered list, None otherwise."""
    
    @abstractmethod
    def get_lists(self) -> Iterator['ListBlock']:
        """Get any nested lists contained under this item."""

class ListBlock(ABC):
    """Represents a block of related list items at the same nesting level.
    
    A list block maintains the following properties:
    - Whether it is an ordered (numbered) or unordered list
    - The items contained in the list
    - The nesting level within the document structure
    """
    @property
    @abstractmethod
    def ordered(self) -> bool:
        """Whether this is an ordered (numbered) list block."""

    @property
    def text_range(self) -> Tuple[int, int]:
        raise NotImplementedError
    
    @abstractmethod
    def list_items(self) -> Iterator[ListItem]:
        """Get all items in this list block."""

class HeadSection(ABC):
    """Represents a markdown header section with its associated content.
    
    A header section includes:
    - The header text and level (h1-h6)
    - The range of text it encompasses
    - Any list blocks directly under this header
    """
    @property
    def text(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def head_level(self) -> int:
        """The header level (1-6)."""
    
    @property
    @abstractmethod
    def text_range(self) -> Tuple[int, int]:
        """The start and end positions of this section in the source text."""
    
    @abstractmethod
    def get_lists(self) -> Iterator[ListBlock]:
        """Get all list blocks directly under this header section."""


class MarkdownService(ABC):
    """Service interface for parsing and extracting markdown document structure."""

    @abstractmethod
    def get_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract and parse YAML frontmatter from markdown content.
        
        Args:
            content: The markdown document text to parse
            
        Returns:
            A dictionary containing the parsed YAML frontmatter data.
            Returns an empty dict if no frontmatter is present.
        """
    
    @abstractmethod
    def get_headers(self, content: str) -> Iterator[HeadSection]:
        """Extract all headers and their sections from markdown content.
        
        Args:
            content: The markdown document text to parse
            
        Returns:
            An iterator over HeadSection objects, each representing a header
            and its associated content section.
        """
