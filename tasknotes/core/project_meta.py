from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from tasknotes.interface.edit_session import EditSession
from tasknotes.interface.file_service import FileService
from tasknotes.interface.markdown_service import DocumentMeta


@dataclass
class ProjectMeta:
    """Class to represent project metadata.
    
    This class encapsulates the project metadata, including both the
    metadata stored in the markdown frontmatter and the metadata
    extracted from the markdown content (id, name, description).
    """
    _id: str
    _name: str
    _description: str
    _doc_meta: DocumentMeta
    
    @property
    def id(self) -> str:
        """Get the project ID.
        
        Returns:
            str: The project ID
        """
        return self._id
    
    @property
    def name(self) -> str:
        """Get the project name.
        
        Returns:
            str: The project name
        """
        return self._name
    
    @property
    def description(self) -> str:
        """Get the project description.
        
        Returns:
            str: The project description
        """
        return self._description
    
    @description.setter
    def description(self, value: str) -> None:
        """Set the project description.
        
        Args:
            value: The new description
        """
        self._description = value
    
    @property
    def doc_meta(self) -> DocumentMeta:
        """Get the document metadata.
        
        Returns:
            DocumentMeta: The document metadata
        """
        return self._doc_meta
    
    def get_meta(self, key: str, default: Any = None) -> Any:
        """Get a value from the document metadata.
        
        Args:
            key: The key to get
            default: The default value to return if the key is not found
            
        Returns:
            Any: The value for the key, or the default if not found
        """
        return self._doc_meta.get(key, default)
    
    def set_meta(self, key: str, value: Any) -> None:
        """Set a value in the document metadata.
        
        Args:
            key: The key to set
            value: The value to set
        """
        self._doc_meta.set(key, value)
    
    @property
    def created_at(self) -> Optional[float]:
        """Get the creation timestamp.
        
        Returns:
            float or None: The creation timestamp, or None if not set
        """
        return self._doc_meta.get("created_at")
    
    @property
    def archived_at(self) -> Optional[float]:
        """Get the archive timestamp.
        
        Returns:
            float or None: The archive timestamp, or None if not set
        """
        return self._doc_meta.get("archived_at")
    
    @property
    def tags(self) -> list:
        """Get the project tags.
        
        Returns:
            list: The project tags, or an empty list if not set
        """
        return self._doc_meta.get("tags", [])
    
    @tags.setter
    def tags(self, value: list) -> None:
        """Set the project tags.
        
        Args:
            value: The new tags
        """
        self._doc_meta.set("tags", value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the project metadata to a dictionary.
        
        Returns:
            Dict[str, Any]: The project metadata as a dictionary
        """
        # Start with the document metadata
        result = dict(self._doc_meta.data)
        
        # Add the project-specific fields
        result["id"] = self._id
        result["name"] = self._name
        result["description"] = self._description
        
        return result
    
    def apply(self, edit_session: EditSession, file_service: FileService, path: str) -> str:
        """Apply the metadata changes to the file.
        
        This method delegates to the document metadata's apply method.
        
        Args:
            edit_session: An EditSession instance for modifying the file content
            file_service: A FileService instance
            path: The path to the file to update
            
        Returns:
            str: The updated content
        """
        return self._doc_meta.apply(edit_session, file_service, path)
