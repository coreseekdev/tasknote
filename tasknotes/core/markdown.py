"""Markdown parsing utilities using markdown-it-py."""

from typing import Dict, Any, List, Optional, Tuple, Union, cast
import re

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from markdown_it.token import Token
from markdown_it.renderer import RendererHTML


class MarkdownParser:
    """Parse and process markdown content using markdown-it-py."""
    
    # Create a markdown parser instance with default options
    _md = MarkdownIt("commonmark").enable("table")
    
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
        
        # Parse markdown body using markdown-it-py
        try:
            # Parse the markdown to tokens
            tokens = MarkdownParser._md.parse(body)
            
            # Create a syntax tree from the tokens
            tree = SyntaxTreeNode(tokens)
            
            # Render to HTML
            html = MarkdownParser._md.render(body)
        except Exception as e:
            # Fallback to simple parsing if markdown-it-py fails
            html = f"<p>Error parsing markdown: {str(e)}</p>"
            tree = None
            tokens = []
        
        # Extract title from first heading if not in frontmatter
        if "title" not in frontmatter and body:
            title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            if title_match:
                frontmatter["title"] = title_match.group(1).strip()
            elif tokens:
                # Try to find the first heading in tokens
                for token in tokens:
                    if token.type == "heading_open" and token.tag == "h1":
                        # Get the content from the next token
                        if len(tokens) > token.map[0] + 1:
                            content_token = tokens[token.map[0] + 1]
                            if content_token.type == "inline" and content_token.content:
                                frontmatter["title"] = content_token.content
                                break
        
        return {
            "metadata": frontmatter,
            "content": body,
            "html": html,
            "tree": tree,
            "tokens": tokens
        }
    
    @staticmethod
    def extract_tasks(content: str) -> List[Dict[str, Any]]:
        """Extract task items from markdown content."""
        tasks = []
        
        # Parse the markdown
        tokens = MarkdownParser._md.parse(content)
        
        # Look for task list items in the tokens
        for i, token in enumerate(tokens):
            if token.type == "list_item_open":
                # Check if this is a task list item
                if i + 1 < len(tokens) and tokens[i+1].type == "paragraph_open":
                    if i + 2 < len(tokens) and tokens[i+2].type == "inline":
                        inline_content = tokens[i+2].content
                        # Check for task list syntax: [ ] or [x]
                        match = re.match(r'^\[([ xX])\]\s+(.+)$', inline_content)
                        if match:
                            completed = match.group(1).lower() == "x"
                            task_text = match.group(2).strip()
                            
                            tasks.append({
                                "text": task_text,
                                "completed": completed,
                                "token_index": i
                            })
        
        # If no tasks found using tokens, fall back to regex
        if not tasks:
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
    def find_node_by_path(tree: SyntaxTreeNode, path: List[int]) -> Optional[SyntaxTreeNode]:
        """Find a node in the syntax tree by path.
        
        Args:
            tree: The syntax tree to search in
            path: List of indices to follow from the root
            
        Returns:
            Optional[SyntaxTreeNode]: The found node or None
        """
        if not path:
            return tree
            
        current = tree
        for index in path:
            if current.children and 0 <= index < len(current.children):
                current = current.children[index]
            else:
                return None
                
        return current
    
    @staticmethod
    def find_heading(tree: SyntaxTreeNode, level: int = 1, text: Optional[str] = None) -> Optional[SyntaxTreeNode]:
        """Find a heading in the syntax tree.
        
        Args:
            tree: The syntax tree to search in
            level: The heading level to find (1-6)
            text: Optional text to match in the heading
            
        Returns:
            Optional[SyntaxTreeNode]: The found heading node or None
        """
        def _find_heading_recursive(node: SyntaxTreeNode) -> Optional[SyntaxTreeNode]:
            if node.type == "heading_open" and node.tag == f"h{level}":
                # Check if this is the heading we're looking for
                if text is None:
                    return node
                    
                # Check if the heading text matches
                if node.children and len(node.children) > 0:
                    content_node = node.children[0]
                    if content_node.type == "inline" and content_node.content == text:
                        return node
            
            # Recursively search in children
            if node.children:
                for child in node.children:
                    result = _find_heading_recursive(child)
                    if result:
                        return result
                        
            return None
            
        return _find_heading_recursive(tree)
    
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
