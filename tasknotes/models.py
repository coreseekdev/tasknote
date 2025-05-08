"""Data models for TaskNotes."""

import datetime
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class Task:
    """Represents a task in the system."""
    
    title: str
    status: str = "open"
    description: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    updated_at: Optional[datetime.datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create a Task instance from a dictionary."""
        # Handle datetime conversion
        created_at = datetime.datetime.fromisoformat(data["created_at"])
        updated_at = datetime.datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        
        return cls(
            id=data["id"],
            title=data["title"],
            status=data["status"],
            description=data.get("description"),
            created_at=created_at,
            updated_at=updated_at,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
    
    def update(self, **kwargs: Any) -> None:
        """Update task properties and set updated_at timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.datetime.now()
