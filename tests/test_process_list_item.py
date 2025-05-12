"""Test cases for processing list items in TreeSitterMarkdownService."""

import unittest
from typing import List, Optional, Tuple, Iterator
import re

from tasknotes.core.markdown import TreeSitterMarkdownService, TreeSitterListItem
from tasknotes.interface.markdown_service import ListItem, ListBlock


class TestProcessListItem(unittest.TestCase):
    """Test cases for the processing of list items in markdown."""

    def setUp(self):
        """Set up the test environment."""
        self.markdown_service = TreeSitterMarkdownService()
    
    def _get_list_blocks(self, content: str) -> List[ListBlock]:
        """Helper method to get list blocks from content."""
        # Create a simple document with the content
        document = f"# Test\n\n{content}"
        
        # Parse the document
        _, headers = self.markdown_service.parse(document)
        
        # Get the first header section
        header_sections = list(headers)
        if not header_sections:
            return []
        
        # Get lists from the header section
        return list(header_sections[0].get_lists())

    def test_basic_list_item(self):
        """Test processing a basic list item without task markers."""
        content = "- Basic list item"
        
        list_blocks = self._get_list_blocks(content)
        self.assertEqual(len(list_blocks), 1)
        
        # Check the list item
        list_items = list(list_blocks[0].list_items())
        self.assertEqual(len(list_items), 1)
        
        item = list_items[0]
        self.assertEqual(item.text, "Basic list item")
        self.assertFalse(item.is_task)
        self.assertIsNone(item.is_completed_task)
        self.assertIsNone(item.order)

    def test_ordered_list_item(self):
        """Test processing an ordered list item."""
        content = "1. Ordered list item"
        
        list_blocks = self._get_list_blocks(content)
        self.assertEqual(len(list_blocks), 1)
        
        # Check the list item
        list_items = list(list_blocks[0].list_items())
        self.assertEqual(len(list_items), 1)
        
        item = list_items[0]
        self.assertEqual(item.text, "Ordered list item")
        self.assertFalse(item.is_task)
        self.assertIsNone(item.is_completed_task)
        self.assertEqual(item.order, 1)

    def test_unchecked_task_item(self):
        """Test processing an unchecked task item."""
        content = "- [ ] Unchecked task"
        
        list_blocks = self._get_list_blocks(content)
        list_items = list(list_blocks[0].list_items())
        item = list_items[0]
        
        self.assertEqual(item.text, "Unchecked task")
        self.assertTrue(item.is_task)
        self.assertFalse(item.is_completed_task)

    def test_checked_task_item(self):
        """Test processing a checked task item."""
        content = "- [x] Checked task"
        
        list_blocks = self._get_list_blocks(content)
        list_items = list(list_blocks[0].list_items())
        item = list_items[0]
        
        self.assertEqual(item.text, "Checked task")
        self.assertTrue(item.is_task)
        self.assertTrue(item.is_completed_task)

    def test_task_with_id(self):
        """Test processing a task item with an ID."""
        content = "- [ ] TASK-123: Task with ID"
        
        list_blocks = self._get_list_blocks(content)
        list_items = list(list_blocks[0].list_items())
        item = list_items[0]
        
        self.assertEqual(item.text, "TASK-123: Task with ID")
        self.assertTrue(item.is_task)
        self.assertFalse(item.is_completed_task)
        
        # The ID should be part of the text, not extracted by tree-sitter
        self.assertIn("TASK-123", item.text)

    def test_task_with_backtick_id(self):
        """Test processing a task item with a backtick-formatted ID."""
        content = "- [ ] `TASK-123` Task with backtick ID"
        
        list_blocks = self._get_list_blocks(content)
        list_items = list(list_blocks[0].list_items())
        item = list_items[0]
        
        self.assertEqual(item.text, "`TASK-123` Task with backtick ID")
        self.assertTrue(item.is_task)
        self.assertFalse(item.is_completed_task)

    def test_task_with_link_id(self):
        """Test processing a task item with a link-formatted ID."""
        content = "- [ ] [`TASK-123`](Task-123.md) Task with link ID"
        
        list_blocks = self._get_list_blocks(content)
        list_items = list(list_blocks[0].list_items())
        item = list_items[0]
        
        self.assertEqual(item.text, "[`TASK-123`](Task-123.md) Task with link ID")
        self.assertTrue(item.is_task)
        self.assertFalse(item.is_completed_task)

    def test_task_with_nested_list(self):
        """Test processing a task item with a nested list (tags)."""
        content = """- [ ] TASK-123: Task with nested list
  - tag1
  - tag2
"""
        
        list_blocks = self._get_list_blocks(content)
        list_items = list(list_blocks[0].list_items())
        item = list_items[0]
        
        self.assertEqual(item.text, "TASK-123: Task with nested list")
        self.assertTrue(item.is_task)
        self.assertFalse(item.is_completed_task)
        
        # Check nested lists (tags)
        nested_lists = list(item.get_lists())
        self.assertEqual(len(nested_lists), 1)
        
        nested_items = list(nested_lists[0].list_items())
        self.assertEqual(len(nested_items), 2)
        self.assertEqual(nested_items[0].text, "tag1")
        self.assertEqual(nested_items[1].text, "tag2")

    def test_task_with_complex_nested_structure(self):
        """Test processing a task item with a complex nested structure."""
        content = """- [ ] TASK-123: Complex task
  - priority: high
  - deadline: 2025-05-20
    - note: This is important
    - reminder: 1 day before
"""
        
        list_blocks = self._get_list_blocks(content)
        list_items = list(list_blocks[0].list_items())
        item = list_items[0]
        
        self.assertEqual(item.text, "TASK-123: Complex task")
        
        # Check first level nested items
        nested_lists = list(item.get_lists())
        self.assertEqual(len(nested_lists), 1)
        
        nested_items = list(nested_lists[0].list_items())
        self.assertEqual(len(nested_items), 2)
        self.assertEqual(nested_items[0].text, "priority: high")
        self.assertEqual(nested_items[1].text, "deadline: 2025-05-20")
        
        # Check second level nested items
        second_level_lists = list(nested_items[1].get_lists())
        self.assertEqual(len(second_level_lists), 1)
        
        second_level_items = list(second_level_lists[0].list_items())
        self.assertEqual(len(second_level_items), 2)
        self.assertEqual(second_level_items[0].text, "note: This is important")
        self.assertEqual(second_level_items[1].text, "reminder: 1 day before")

    def test_multiple_tasks_with_different_formats(self):
        """Test processing multiple tasks with different formats."""
        content = """- [ ] Task without ID
- [ ] TASK-001: Task with ID
- [ ] `TASK-002` Task with backtick ID
- [ ] [`TASK-003`](Task-003.md) Task with link ID
"""
        
        list_blocks = self._get_list_blocks(content)
        list_items = list(list_blocks[0].list_items())
        
        self.assertEqual(len(list_items), 4)
        self.assertEqual(list_items[0].text, "Task without ID")
        self.assertEqual(list_items[1].text, "TASK-001: Task with ID")
        self.assertEqual(list_items[2].text, "`TASK-002` Task with backtick ID")
        self.assertEqual(list_items[3].text, "[`TASK-003`](Task-003.md) Task with link ID")

    def test_task_id_extraction(self):
        """Test extracting task IDs from different formats using regex."""
        # This is a helper test to demonstrate how to extract IDs from task text
        
        def extract_task_id(text: str) -> str:
            """Extract task ID from text using regex patterns."""
            # Try TASK-xxx: format (most common)
            prefix_pattern = r'([A-Z]+-\d+):'
            prefix_match = re.search(prefix_pattern, text)
            if prefix_match:
                return prefix_match.group(1)
                
            # Try `TASK-xxx` format
            backtick_pattern = r'`([A-Z]+-\d+)`'
            backtick_match = re.search(backtick_pattern, text)
            if backtick_match:
                return backtick_match.group(1)
            
            # Try [`TASK-xxx`](link) format
            link_pattern = r'\[`([A-Z]+-\d+)`.*?\]\(.*?\)'
            link_match = re.search(link_pattern, text)
            if link_match:
                return link_match.group(1)
            
            return ''
        
        # Test cases
        test_cases = [
            ("Task without ID", ""),
            ("TASK-001: Task with ID", "TASK-001"),
            ("`TASK-002` Task with backtick ID", "TASK-002"),
            ("[`TASK-003`](Task-003.md) Task with link ID", "TASK-003"),
        ]
        
        for text, expected_id in test_cases:
            extracted_id = extract_task_id(text)
            self.assertEqual(extracted_id, expected_id)


if __name__ == '__main__':
    unittest.main()
