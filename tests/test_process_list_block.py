"""Test cases for the _process_list_block method in TreeSitterMarkdownService."""

import unittest
from typing import List, Optional, Tuple, Iterator

from tasknotes.core.markdown import TreeSitterMarkdownService, TreeSitterListItem, TreeSitterListBlock
from tasknotes.interface.markdown_service import ListItem, ListBlock


class TestProcessListBlock(unittest.TestCase):
    """Test cases for processing list blocks in markdown."""

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

    def test_unordered_list_block(self):
        """Test processing an unordered list block."""
        content = """- Item 1
- Item 2
- Item 3"""
        
        list_blocks = self._get_list_blocks(content)
        self.assertEqual(len(list_blocks), 1)
        
        block = list_blocks[0]
        self.assertFalse(block.is_ordered)
        
        items = list(block.list_items())
        self.assertEqual(len(items), 3)
        for i, item in enumerate(items, 1):
            self.assertEqual(item.text, f"Item {i}")
            self.assertIsNone(item.order)

    def test_ordered_list_block(self):
        """Test processing an ordered list block."""
        content = """1. First item
2. Second item
3. Third item"""
        
        list_blocks = self._get_list_blocks(content)
        self.assertEqual(len(list_blocks), 1)
        
        block = list_blocks[0]
        self.assertTrue(block.is_ordered)
        
        items = list(block.list_items())
        self.assertEqual(len(items), 3)
        for i, item in enumerate(items, 1):
            self.assertEqual(item.text, f"{['First', 'Second', 'Third'][i-1]} item")
            self.assertEqual(item.order, i)

    def test_mixed_list_block(self):
        """Test processing a list block with mixed ordered and unordered items."""
        content = """1. First ordered item
2. Second ordered item
- Unordered item 1
- Unordered item 2
3. Third ordered item"""
        
        list_blocks = self._get_list_blocks(content)
        self.assertEqual(len(list_blocks), 2)
        
        # First block should be ordered
        ordered_block = list_blocks[0]
        self.assertTrue(ordered_block.is_ordered)
        ordered_items = list(ordered_block.list_items())
        self.assertEqual(len(ordered_items), 2)
        self.assertEqual(ordered_items[0].text, "First ordered item")
        self.assertEqual(ordered_items[1].text, "Second ordered item")
        
        # Second block should be unordered
        unordered_block = list_blocks[1]
        self.assertFalse(unordered_block.is_ordered)
        unordered_items = list(unordered_block.list_items())
        self.assertEqual(len(unordered_items), 3)  # Including the last ordered item
        self.assertEqual(unordered_items[0].text, "Unordered item 1")
        self.assertEqual(unordered_items[1].text, "Unordered item 2")
        self.assertEqual(unordered_items[2].text, "Third ordered item")

    def test_nested_list_blocks(self):
        """Test processing nested list blocks."""
        content = """1. First level ordered
   - Second level unordered 1
   - Second level unordered 2
     1. Third level ordered 1
     2. Third level ordered 2
2. Back to first level
   1. Second level ordered 1
   2. Second level ordered 2"""
        
        list_blocks = self._get_list_blocks(content)
        self.assertEqual(len(list_blocks), 1)
        
        # First level should be ordered
        block = list_blocks[0]
        self.assertTrue(block.is_ordered)
        
        items = list(block.list_items())
        self.assertEqual(len(items), 2)
        
        # Check first item and its nested lists
        first_item = items[0]
        self.assertEqual(first_item.text, "First level ordered")
        
        nested_lists = list(first_item.get_lists())
        self.assertEqual(len(nested_lists), 1)
        
        # Second level should be unordered
        second_level = nested_lists[0]
        self.assertFalse(second_level.is_ordered)
        
        second_items = list(second_level.list_items())
        self.assertEqual(len(second_items), 2)
        
        # Check third level ordered list
        second_item = second_items[1]  # The one with the nested list
        third_level_lists = list(second_item.get_lists())
        self.assertEqual(len(third_level_lists), 1)
        
        third_level = third_level_lists[0]
        self.assertTrue(third_level.is_ordered)
        
        third_items = list(third_level.list_items())
        self.assertEqual(len(third_items), 2)
        self.assertEqual(third_items[0].order, 1)
        self.assertEqual(third_items[1].order, 2)

    def test_task_list_block(self):
        """Test processing a task list block."""
        content = """- [ ] Task 1
- [x] Task 2
- [ ] Task 3"""
        
        list_blocks = self._get_list_blocks(content)
        self.assertEqual(len(list_blocks), 1)
        
        block = list_blocks[0]
        self.assertFalse(block.is_ordered)
        
        items = list(block.list_items())
        self.assertEqual(len(items), 3)
        
        # Check task status
        self.assertTrue(items[0].is_task)
        self.assertFalse(items[0].is_completed_task)
        
        self.assertTrue(items[1].is_task)
        self.assertTrue(items[1].is_completed_task)
        
        self.assertTrue(items[2].is_task)
        self.assertFalse(items[2].is_completed_task)

    def test_empty_list_block(self):
        """Test processing an empty list block."""
        content = """- """
        
        list_blocks = self._get_list_blocks(content)
        self.assertEqual(len(list_blocks), 0)

    def test_list_block_with_empty_items(self):
        """Test processing a list block with empty items."""
        content = """1. First item
2. 
3. Third item"""
        
        list_blocks = self._get_list_blocks(content)
        self.assertEqual(len(list_blocks), 1)
        
        block = list_blocks[0]
        self.assertTrue(block.is_ordered)
        
        items = list(block.list_items())
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].text, "First item")
        self.assertEqual(items[1].text, "")
        self.assertEqual(items[2].text, "Third item")


if __name__ == '__main__':
    unittest.main()
