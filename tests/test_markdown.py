import pytest
import os
from typing import Iterator, Optional
from unittest.mock import MagicMock, patch

from tasknotes.core.markdown import create_markdown_service
from tasknotes.interface.markdown_service import HeadSection, ListBlock, ListItem
from tasknotes.interface.edit_session import EditOperation
from tasknotes.interface.file_service import FileService

def test_frontmatter_parsing():
    service = create_markdown_service()
    content = """---
title: Test Document
tags:
  - test
  - markdown
priority: 1
---
# Content
Some content here
"""
    meta = service.get_meta(content)
    frontmatter = meta.data
    assert frontmatter["title"] == "Test Document"
    assert frontmatter["tags"] == ["test", "markdown"]
    assert frontmatter["priority"] == 1
    
    # Test get method
    assert meta.get("title") == "Test Document"
    assert meta.get("nonexistent") is None
    assert meta.get("nonexistent", "default") == "default"
    
    # Test text_range
    start, end = meta.text_range
    assert start == 0
    assert end == content.index("# Content")  # Should end at the closing --- marker

def test_headers_parsing():
    service = create_markdown_service()
    content = """# Top Level
Some content
## Second Level
More content
### Third Level
Final content
"""
    headers = list(service.get_headers(content))
    assert len(headers) == 3
    assert headers[0].text == "Top Level"
    assert headers[0].head_level == 1
    assert headers[1].text == "Second Level"
    assert headers[1].head_level == 2
    assert headers[2].text == "Third Level"
    assert headers[2].head_level == 3
    
    # Test text ranges
    for header in headers:
        start, end = header.text_range
        assert start >= 0
        assert end > start
        assert content[start:end].strip().startswith('#')

def test_lists_under_header():
    service = create_markdown_service()
    content = """# Shopping List
1. Apples
2. Bananas
   - Organic only
   - [ ] Check ripeness
   - [x] Compare prices

# Other Section
- Not included
"""
    headers = list(service.get_headers(content))
    shopping_header = next(h for h in headers if h.text == "Shopping List")
    lists = list(shopping_header.get_lists())
    
    assert len(lists) == 1  # One main list with nested items
    main_list = lists[0]
    assert main_list.ordered == True
    
    items = list(main_list.list_items())
    assert len(items) == 2  # Two top-level items
    
    # First item
    assert items[0].text == "Apples"
    assert items[0].order == 1
    assert not items[0].is_task
    
    # Second item with nested list
    assert items[1].text == "Bananas"
    assert items[1].order == 2
    assert not items[1].is_task
    
    # Check nested items
    nested_lists = list(items[1].get_lists())
    assert len(nested_lists) == 1
    nested_list = nested_lists[0]
    assert not nested_list.ordered
    
    nested_items = list(nested_list.list_items())
    assert len(nested_items) == 3
    
    # Check nested item properties
    assert nested_items[0].text == "Organic only"
    assert not nested_items[0].is_task
    
    assert nested_items[1].text == "Check ripeness"
    assert nested_items[1].is_task
    assert not nested_items[1].is_completed_task
    
    assert nested_items[2].text == "Compare prices"
    assert nested_items[2].is_task
    assert nested_items[2].is_completed_task

def test_empty_document():
    service = create_markdown_service()
    content = ""
    
    meta = service.get_meta(content)
    assert meta.data == {}
    assert meta.get("any_key") is None
    start, end = meta.text_range
    assert start == 0
    assert end == 0
    assert len(list(service.get_headers(content))) == 0
    
def test_document_without_frontmatter():
    service = create_markdown_service()
    content = """# Just a header
Some content without frontmatter
"""
    
    meta = service.get_meta(content)
    assert meta.data == {}
    start, end = meta.text_range
    assert start == 0
    assert end == 0

def test_no_matching_header():
    service = create_markdown_service()
    content = """# Existing Header
- Some list item
"""
    headers = list(service.get_headers(content))
    assert len(headers) == 1
    assert headers[0].text == "Existing Header"
    assert len(list(headers[0].get_lists())) == 1

def test_multiple_lists_under_header():
    service = create_markdown_service()
    content = """# Shopping List
- Fruits
- Vegetables

Some text in between

1. Meat
2. Fish

More text

- [ ] Snacks
- [x] Drinks
"""
    headers = list(service.get_headers(content))
    shopping_header = next(h for h in headers if h.text == "Shopping List")
    lists = list(shopping_header.get_lists())
    
    assert len(lists) == 3  # Three separate lists
    
    # First list (unordered)
    assert not lists[0].ordered
    items = list(lists[0].list_items())
    assert len(items) == 2
    assert items[0].text == "Fruits"
    assert items[1].text == "Vegetables"
    
    # Second list (ordered)
    assert lists[1].ordered
    items = list(lists[1].list_items())
    assert len(items) == 2
    assert items[0].text == "Meat"
    assert items[0].order == 1
    assert items[1].text == "Fish"
    assert items[1].order == 2
    
    # Third list (task list)
    assert not lists[2].ordered
    items = list(lists[2].list_items())
    assert len(items) == 2
    assert items[0].text == "Snacks"
    assert items[0].is_task
    assert not items[0].is_completed_task
    assert items[1].text == "Drinks"
    assert items[1].is_task
    assert items[1].is_completed_task

def test_nested_lists():
    service = create_markdown_service()
    content = """# Project Tasks
- Backend
  - Database setup
    1. Create schema
    2. Add indexes
  - API development
    - [ ] Auth endpoints
    - [x] User endpoints
- Frontend
  1. Setup React
  2. Components
     - [ ] Header
     - [ ] Footer
     - Navigation
       - [x] Menu
       - [ ] Breadcrumbs
"""
    headers = list(service.get_headers(content))
    tasks_header = next(h for h in headers if h.text == "Project Tasks")
    lists = list(tasks_header.get_lists())
    
    assert len(lists) == 1  # One main list
    main_list = lists[0]
    assert not main_list.ordered
    
    main_items = list(main_list.list_items())
    assert len(main_items) == 2  # Backend and Frontend
    
    # Backend section
    backend = main_items[0]
    assert backend.text == "Backend"
    backend_lists = list(backend.get_lists())
    assert len(backend_lists) == 1
    
    backend_items = list(backend_lists[0].list_items())
    assert len(backend_items) == 2  # Database setup and API development
    
    # Database setup section
    db_setup = backend_items[0]
    assert db_setup.text == "Database setup"
    db_lists = list(db_setup.get_lists())
    assert len(db_lists) == 1
    assert db_lists[0].ordered
    
    db_items = list(db_lists[0].list_items())
    assert len(db_items) == 2
    assert db_items[0].text == "Create schema"
    assert db_items[0].order == 1
    assert db_items[1].text == "Add indexes"
    assert db_items[1].order == 2
    
    # API development section
    api_dev = backend_items[1]
    assert api_dev.text == "API development"
    api_lists = list(api_dev.get_lists())
    assert len(api_lists) == 1
    
    api_items = list(api_lists[0].list_items())
    assert len(api_items) == 2
    assert api_items[0].text == "Auth endpoints"
    assert api_items[0].is_task
    assert not api_items[0].is_completed_task
    assert api_items[1].text == "User endpoints"
    assert api_items[1].is_task
    assert api_items[1].is_completed_task
    
    # Frontend section
    frontend = main_items[1]
    assert frontend.text == "Frontend"
    frontend_lists = list(frontend.get_lists())
    assert len(frontend_lists) == 1
    assert frontend_lists[0].ordered
    
    frontend_items = list(frontend_lists[0].list_items())
    assert len(frontend_items) == 2
    assert frontend_items[0].text == "Setup React"
    assert frontend_items[0].order == 1
    
    # Components section
    components = frontend_items[1]
    assert components.text == "Components"
    assert components.order == 2
    comp_lists = list(components.get_lists())
    assert len(comp_lists) == 1
    
    comp_items = list(comp_lists[0].list_items())
    assert len(comp_items) == 3
    assert comp_items[0].text == "Header"
    assert comp_items[0].is_task
    assert not comp_items[0].is_completed_task
    assert comp_items[1].text == "Footer"
    assert comp_items[1].is_task
    assert not comp_items[1].is_completed_task
    
    # Navigation section
    nav = comp_items[2]
    assert nav.text == "Navigation"
    nav_lists = list(nav.get_lists())
    assert len(nav_lists) == 1
    
    nav_items = list(nav_lists[0].list_items())
    assert len(nav_items) == 2
    assert nav_items[0].text == "Menu"
    assert nav_items[0].is_task
    assert nav_items[0].is_completed_task
    assert nav_items[1].text == "Breadcrumbs"
    assert nav_items[1].is_task
    assert not nav_items[1].is_completed_task


def test_parse_method():
    """Test the parse method that extracts both metadata and headers in a single call."""
    service = create_markdown_service()
    content = """---
title: Test Document
tags:
  - test
  - markdown
priority: 1
---
# Top Level
Some content
## Second Level
More content
- List item 1
- List item 2
  - Nested item

### Third Level
Final content
"""
    
    # Call the parse method
    meta, headers_iterator = service.parse(content)
    headers = list(headers_iterator)
    
    # Verify metadata
    assert meta.data["title"] == "Test Document"
    assert meta.data["tags"] == ["test", "markdown"]
    assert meta.data["priority"] == 1
    
    # Verify headers
    assert len(headers) == 3
    assert headers[0].text == "Top Level"
    assert headers[0].head_level == 1
    assert headers[1].text == "Second Level"
    assert headers[1].head_level == 2
    assert headers[2].text == "Third Level"
    assert headers[2].head_level == 3
    
    # Verify lists under second header
    second_header = headers[1]
    lists = list(second_header.get_lists())
    assert len(lists) == 1
    
    list_items = list(lists[0].list_items())
    assert len(list_items) == 2
    assert list_items[0].text == "List item 1"
    assert list_items[1].text == "List item 2"
    
    # Verify nested list
    nested_lists = list(list_items[1].get_lists())
    assert len(nested_lists) == 1
    nested_items = list(nested_lists[0].list_items())
    assert len(nested_items) == 1
    assert nested_items[0].text == "Nested item"


def test_parse_without_frontmatter():
    """Test the parse method with a document that has no frontmatter."""
    service = create_markdown_service()
    content = """# Just a header
Some content without frontmatter

## Second header
- List item
"""
    
    # Call the parse method
    meta, headers_iterator = service.parse(content)
    headers = list(headers_iterator)
    
    # Verify empty metadata
    assert meta.data == {}
    start, end = meta.text_range
    assert start == 0
    assert end == 0
    
    # Verify headers
    assert len(headers) == 2
    assert headers[0].text == "Just a header"
    assert headers[0].head_level == 1
    assert headers[1].text == "Second header"
    assert headers[1].head_level == 2
    
    # Verify list under second header
    second_header = headers[1]
    lists = list(second_header.get_lists())
    assert len(lists) == 1
    list_items = list(lists[0].list_items())
    assert len(list_items) == 1
    assert list_items[0].text == "List item"


def test_parse_empty_document():
    """Test the parse method with an empty document."""
    service = create_markdown_service()
    content = ""
    
    # Call the parse method
    meta, headers_iterator = service.parse(content)
    headers = list(headers_iterator)
    
    # Verify empty metadata
    assert meta.data == {}
    start, end = meta.text_range
    assert start == 0
    assert end == 0
    
    # Verify no headers
    assert len(headers) == 0


def test_parse_with_empty_tasks_section():
    """Test the parse method with a document that has a Tasks section but no tasks list."""
    service = create_markdown_service()
    content = """# Test Document
        
## Tasks

This section should contain tasks.

## Notes

Some notes here.
"""
    
    # Call the parse method
    meta, headers_iterator = service.parse(content)
    headers = list(headers_iterator)
    
    # Verify empty metadata
    assert meta.data == {}
    start, end = meta.text_range
    assert start == 0
    assert end == 0
    
    # Verify headers
    assert len(headers) == 3  # Should have 3 headers: Test Document, Tasks, Notes
    assert headers[0].text == "Test Document"
    assert headers[0].head_level == 1
    assert headers[1].text == "Tasks"
    assert headers[1].head_level == 2
    assert headers[2].text == "Notes"
    assert headers[2].head_level == 2
    
    # Verify Tasks section has no lists
    tasks_header = headers[1]
    lists = list(tasks_header.get_lists())
    assert len(lists) == 0  # Should have no lists under Tasks section
    
    # Verify header text ranges
    # Main header
    main_start, main_end = headers[0].text_range
    assert main_start >= 0
    assert main_end > main_start
    assert content[main_start:main_end].strip().startswith('# Test Document')
    
    # Get all text ranges first
    tasks_start, tasks_end = headers[1].text_range
    notes_start, notes_end = headers[2].text_range
    
    # Tasks header
    assert tasks_start > main_start
    assert tasks_end > tasks_start
    # Tasks section should start with ## Tasks and end before ## Notes
    assert content[tasks_start:tasks_start+10].strip().startswith('## Tasks')
    assert tasks_end == notes_start  # Tasks section should end exactly where Notes section begins
    
    # Notes header
    assert notes_start > tasks_start
    assert notes_end > notes_start
    assert content[notes_start:notes_start+10].strip().startswith('## Notes')
    assert notes_end == len(content)  # Last header's end should be the end of the document


def test_document_meta_set_and_apply():
    """Test the set and apply methods of DocumentMeta."""
    service = create_markdown_service()
    
    # Test with existing frontmatter
    content = """---
title: Original Title
tags:
  - original
  - tags
---
# Content
Some content here
"""
    
    # Create mock EditSession
    mock_edit_session = MagicMock()
    mock_edit_session.replace.return_value = EditOperation(text="new yaml", start=0, end=len(content), length=len(content))
    mock_edit_session.insert.return_value = EditOperation(text="new yaml", start=0, end=0, length=len(content) + 10)
    mock_edit_session.get_content.return_value = "updated content"
    
    # Create mock FileService
    mock_file_service = MagicMock(spec=FileService)
    
    # Get metadata and modify it
    meta = service.get_meta(content)
    
    # Test the set method
    meta.set("title", "Updated Title")
    meta.set("priority", 1)
    meta.set("tags", ["updated", "metadata"])
    
    # Verify the changes in the data
    assert meta.get("title") == "Updated Title"
    assert meta.get("priority") == 1
    assert meta.get("tags") == ["updated", "metadata"]
    
    # Test apply method with existing frontmatter
    file_path = "/path/to/file.md"
    result = meta.apply(mock_edit_session)
    
    # Verify that replace was called since we had existing frontmatter
    start, end = meta.text_range
    mock_edit_session.replace.assert_called_once()
    
    # Verify that the method returns the updated content
    assert result == "updated content"
    
    # Verify that the file service was NOT called (apply no longer writes to file)
    mock_file_service.write_file.assert_not_called()
    
    # Reset mocks for the next test
    mock_edit_session.reset_mock()
    mock_file_service.reset_mock()
    
    # Test with no frontmatter
    content_no_meta = """# Content
Some content here
"""
    
    meta_empty = service.get_meta(content_no_meta)
    meta_empty.set("title", "New Title")
    meta_empty.set("author", "Test Author")
    
    # Apply changes
    result = meta_empty.apply(mock_edit_session)
    
    # Verify that insert was called since we had no existing frontmatter
    mock_edit_session.insert.assert_called_once()
    
    # Verify that the method returns the updated content
    assert result == "updated content"
    
    # Verify that the file service was NOT called (apply no longer writes to file)
    mock_file_service.write_file.assert_not_called()
