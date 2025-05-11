"""Markdown document parsing service interface.

This module defines the core interfaces for parsing markdown documents,
providing access to structured elements like headers, lists, and metadata.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Iterator, Any, Optional, Tuple, TypeVar, Generic


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


class DocumentMeta(ABC):
    """Represents metadata from a markdown document.
    
    This interface provides access to:
    - YAML frontmatter as key/value pairs
    - The byte range of the metadata section for replacement
    """
    
    @property
    @abstractmethod
    def data(self) -> Dict[str, Any]:
        """Get the metadata as a dictionary of key/value pairs."""
    
    @property
    @abstractmethod
    def text_range(self) -> Tuple[int, int]:
        """Get the start and end positions of the metadata section in bytes."""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the metadata by key.
        
        Args:
            key: The key to look up
            default: Value to return if key is not found
            
        Returns:
            The value associated with the key, or default if not found
        """
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a value in the metadata by key.
        
        Args:
            key: The key to set
            value: The value to set for the key
        """
    
    @abstractmethod
    def apply(self, edit_session: Any) -> str:
        """Apply the metadata changes to the file.
        
        This method writes the modified metadata back to the file using
        the provided EditSession and FileService.
        
        Args:
            edit_session: An EditSession instance for modifying the file content
        """


class MarkdownService(ABC):
    """Service interface for parsing and extracting markdown document structure."""

    @abstractmethod
    def get_meta(self, content: str) -> DocumentMeta:
        """Extract and parse metadata (YAML frontmatter) from markdown content.
        
        Args:
            content: The markdown document text to parse
            
        Returns:
            A DocumentMeta object providing access to the metadata and its position.
            Returns an empty metadata object if no frontmatter is present.
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
    
    @abstractmethod
    def parse(self, content: str) -> Tuple[DocumentMeta, Iterator[HeadSection]]:
        """Parse markdown content and extract both metadata and headers.
        
        This is a convenience method that combines get_meta and get_headers into a single call.
        
        Args:
            content: The markdown document text to parse
            
        Returns:
            A tuple containing:
            - DocumentMeta: The parsed metadata from the document
            - Iterator[HeadSection]: An iterator over all header sections in the document
        """
