"""Markdown parsing utilities using myst-parser."""

from typing import Dict, Any, List, Optional, Tuple
import re

from myst_parser.main import parse_text
from docutils.core import publish_parts
from docutils.nodes import Element


class MarkdownParser:
    """Parse and process markdown content using myst-parser."""
    
    @staticmethod
    def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
        """Extract YAML frontmatter from markdown content."""
        frontmatter: Dict[str, Any] = {}
        body = content
        
        # Check if content starts with YAML frontmatter
        if content.startswith("---"):
            # Find the end of the frontmatter
            end_index = content.find("---", 3)
            if end_index != -1:
                frontmatter_text = content[3:end_index].strip()
                body = content[end_index + 3:].strip()
                
                # Parse frontmatter lines
                for line in frontmatter_text.split("\n"):
                    line = line.strip()
                    if line and ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Handle lists (comma-separated values)
                        if "," in value and key in ["tags", "categories"]:
                            frontmatter[key] = [item.strip() for item in value.split(",")]
                        else:
                            frontmatter[key] = value
        
        return frontmatter, body
    
    @staticmethod
    def parse_markdown(content: str) -> Dict[str, Any]:
        """Parse markdown content and return structured data."""
        # Extract frontmatter and body
        frontmatter, body = MarkdownParser.parse_frontmatter(content)
        
        # Parse markdown body using myst-parser
        try:
            doc = parse_text(body)
            html = publish_parts(
                source=body,
                writer_name="html",
                settings_overrides={"initial_header_level": 1}
            )["html_body"]
        except Exception as e:
            # Fallback to simple parsing if myst-parser fails
            html = f"<p>Error parsing markdown: {str(e)}</p>"
            doc = None
        
        # Extract title from first heading if not in frontmatter
        if "title" not in frontmatter and body:
            title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            if title_match:
                frontmatter["title"] = title_match.group(1).strip()
        
        return {
            "metadata": frontmatter,
            "content": body,
            "html": html,
            "document": doc
        }
    
    @staticmethod
    def extract_tasks(content: str) -> List[Dict[str, Any]]:
        """Extract task items from markdown content."""
        tasks = []
        
        # Look for task list items (- [ ] or - [x])
        task_pattern = r"[-*]\s+\[([ xX])\]\s+(.+)$"
        
        for line in content.split("\n"):
            match = re.search(task_pattern, line.strip())
            if match:
                completed = match.group(1).lower() == "x"
                task_text = match.group(2).strip()
                
                tasks.append({
                    "text": task_text,
                    "completed": completed
                })
        
        return tasks
    
    @staticmethod
    def generate_markdown(
        title: str, 
        content: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate markdown content with frontmatter."""
        metadata = metadata or {}
        content = content or ""
        
        # Add title to metadata if not present
        if "title" not in metadata:
            metadata["title"] = title
        
        # Generate frontmatter
        frontmatter_lines = ["---"]
        for key, value in metadata.items():
            if isinstance(value, list):
                # Handle list values (like tags)
                value_str = ", ".join(value)
                frontmatter_lines.append(f"{key}: {value_str}")
            else:
                frontmatter_lines.append(f"{key}: {value}")
        frontmatter_lines.append("---")
        
        # Generate content with title and body
        content_lines = [
            f"# {title}",
            "",
            content
        ]
        
        return "\n".join(frontmatter_lines + [""] + content_lines)
