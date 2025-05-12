"""Test cases for the parse_task_inline_string function."""

import unittest
from tasknotes.core.markdown import parse_task_inline_string

class TestParseTaskInline(unittest.TestCase):
    """Test cases for parsing task inline text."""

    def test_simple_task(self):
        """Test parsing a simple task without ID or link."""
        result = parse_task_inline_string("task")
        self.assertIsNone(result['task_id'])
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "task")

    def test_task_with_id(self):
        """Test parsing a task with ID."""
        result = parse_task_inline_string("TASK-123: task description")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "task description")

    def test_task_with_code_id(self):
        """Test parsing a task with code-formatted ID."""
        result = parse_task_inline_string("`TASK-123` task description")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "task description")

    def test_task_with_code_id_and_colon(self):
        """Test parsing a task with code-formatted ID and colon."""
        result = parse_task_inline_string("`TASK-123`: task description")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "task description")

    def test_task_with_link(self):
        """Test parsing a task with link."""
        result = parse_task_inline_string("[TASK-123](Task-123.md)task description")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertEqual(result['link'], "Task-123.md")
        self.assertEqual(result['text'], "task description")

    def test_task_with_link_and_colon(self):
        """Test parsing a task with link and colon."""
        result = parse_task_inline_string("[TASK-123](Task-123.md): task description")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertEqual(result['link'], "Task-123.md")
        self.assertEqual(result['text'], "task description")

    def test_task_with_link_and_colon_in_link_text(self):
        """Test parsing a task with link and colon in link text."""
        result = parse_task_inline_string("[TASK-123:](Task-123.md)task description")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertEqual(result['link'], "Task-123.md")
        self.assertEqual(result['text'], "task description")

    def test_task_with_code_in_link(self):
        """Test parsing a task with code-formatted ID in link."""
        result = parse_task_inline_string("[`TASK-123`](Task-123.md)task description")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertEqual(result['link'], "Task-123.md")
        self.assertEqual(result['text'], "task description")

    def test_task_with_code_in_link_and_colon_in_link(self):
        """Test parsing a task with code-formatted ID and colon in link."""
        result = parse_task_inline_string("[`TASK-123`:](Task-123.md)task description")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertEqual(result['link'], "Task-123.md")
        self.assertEqual(result['text'], "task description")

    def test_task_with_code_in_link_and_colon_after_link(self):
        """Test parsing a task with code-formatted ID in link and colon after link."""
        result = parse_task_inline_string("[`TASK-123`](Task-123.md):task description")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertEqual(result['link'], "Task-123.md")
        self.assertEqual(result['text'], "task description")

    def test_task_with_code_in_link_and_colon_with_space(self):
        """Test parsing a task with code-formatted ID in link and colon with space."""
        result = parse_task_inline_string("[`TASK-123`](Task-123.md): task description")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertEqual(result['link'], "Task-123.md")
        self.assertEqual(result['text'], "task description")

    def test_task_with_complex_id(self):
        """Test parsing a task with complex ID."""
        result = parse_task_inline_string("TASK-ABC-123: task description")
        self.assertEqual(result['task_id'], "TASK-ABC-123")
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "task description")

    def test_task_with_no_description(self):
        """Test parsing a task with ID but no description."""
        result = parse_task_inline_string("TASK-123:")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "")

    def test_task_with_link_but_no_description(self):
        """Test parsing a task with link but no description."""
        result = parse_task_inline_string("[TASK-123](Task-123.md)")
        self.assertEqual(result['task_id'], "TASK-123")
        self.assertEqual(result['link'], "Task-123.md")
        self.assertEqual(result['text'], "")
        
    # Tests with different prefixes
    
    def test_task_with_proj_prefix(self):
        """Test parsing a task with PROJ prefix."""
        result = parse_task_inline_string("PROJ-456: project task")
        self.assertEqual(result['task_id'], "PROJ-456")
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "project task")
    
    def test_task_with_bug_prefix(self):
        """Test parsing a task with BUG prefix."""
        result = parse_task_inline_string("BUG-789: critical bug")
        self.assertEqual(result['task_id'], "BUG-789")
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "critical bug")
    
    def test_task_with_feat_prefix_in_code(self):
        """Test parsing a task with FEAT prefix in code format."""
        result = parse_task_inline_string("`FEAT-101` new feature")
        self.assertEqual(result['task_id'], "FEAT-101")
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "new feature")
    
    def test_task_with_doc_prefix_in_link(self):
        """Test parsing a task with DOC prefix in link."""
        result = parse_task_inline_string("[DOC-202](documentation.md): update docs")
        self.assertEqual(result['task_id'], "DOC-202")
        self.assertEqual(result['link'], "documentation.md")
        self.assertEqual(result['text'], "update docs")
    
    def test_task_with_custom_prefix_and_complex_id(self):
        """Test parsing a task with custom prefix and complex ID."""
        result = parse_task_inline_string("CUSTOM-A1B2C3: complex task")
        self.assertEqual(result['task_id'], "CUSTOM-A1B2C3")
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "complex task")
    
    def test_invalid_id_without_dash(self):
        """Test parsing a task with invalid ID format (no dash)."""
        result = parse_task_inline_string("TASK123: invalid format")
        self.assertIsNone(result['task_id'])
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "TASK123: invalid format")
    
    def test_invalid_id_without_digits(self):
        """Test parsing a task with invalid ID format (no digits)."""
        result = parse_task_inline_string("TASK-ABC: invalid format")
        self.assertIsNone(result['task_id'])
        self.assertIsNone(result['link'])
        self.assertEqual(result['text'], "TASK-ABC: invalid format")


if __name__ == '__main__':
    unittest.main()
