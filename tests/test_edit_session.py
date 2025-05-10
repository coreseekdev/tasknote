"""Tests for the EditSession class."""

import unittest
import time
import uuid
from tasknotes.core.edit_service import new_edit_service
from tasknotes.interface.edit_session import EditOperation


class TestEditSession(unittest.TestCase):
    def setUp(self):
        self.initial_content = "Hello world!"
        self.session = new_edit_service("", self.initial_content)

    def test_init_with_custom_session_id(self):
        """Test initialization with a custom session_id."""
        custom_id = "test-session-123"
        session = new_edit_service("", self.initial_content, session_id=custom_id)
        self.assertEqual(session.session_id, custom_id)

    def test_init_with_default_session_id(self):
        """Test initialization with default UUID session_id."""
        session = new_edit_service("", self.initial_content)
        # Verify it's a valid UUID
        try:
            uuid.UUID(session.session_id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        self.assertTrue(is_valid_uuid)

    def test_insert_text(self):
        """Test inserting text at various positions."""
        # Insert at beginning
        op = self.session.insert(0, "Start: ")
        self.assertIsInstance(op, EditOperation)
        self.assertEqual(op.text, "Start: ")
        self.assertEqual(op.start, 0)
        self.assertEqual(op.end, 0)
        self.assertEqual(op.length, len("Start: Hello world!"))
        self.assertEqual(self.session.get_content(), "Start: Hello world!")

        # Insert in middle
        op = self.session.insert(7, "beautiful ")
        self.assertIsInstance(op, EditOperation)
        self.assertEqual(op.text, "beautiful ")
        self.assertEqual(op.start, 7)
        self.assertEqual(op.end, 7)
        self.assertEqual(op.length, len("Start: beautiful Hello world!"))
        self.assertEqual(self.session.get_content(), "Start: beautiful Hello world!")

        # Insert at end
        op = self.session.insert(len(self.session.current_content), "!")
        self.assertIsInstance(op, EditOperation)
        self.assertEqual(op.text, "!")
        self.assertEqual(op.start, len("Start: beautiful Hello world!"))
        self.assertEqual(op.end, len("Start: beautiful Hello world!"))
        self.assertEqual(op.length, len("Start: beautiful Hello world!!"))
        self.assertEqual(self.session.get_content(), "Start: beautiful Hello world!!")

    def test_delete_text(self):
        """Test deleting text at various positions."""
        # Delete from beginning
        op = self.session.delete(0, 6)
        self.assertIsInstance(op, EditOperation)
        self.assertEqual(op.text, "")
        self.assertEqual(op.start, 0)
        self.assertEqual(op.end, 6)
        self.assertEqual(op.length, len("world!"))
        self.assertEqual(self.session.get_content(), "world!")

        # Delete from middle
        content = "Hello beautiful world!"
        session = new_edit_service("", content)
        op = session.delete(6, 15)
        self.assertIsInstance(op, EditOperation)
        self.assertEqual(op.text, "")
        self.assertEqual(op.start, 6)
        self.assertEqual(op.end, 15)
        self.assertEqual(op.length, len("Hello world!"))
        self.assertEqual(session.get_content(), "Hello world!")

        # Delete from end
        op = session.delete(5, 12)
        self.assertIsInstance(op, EditOperation)
        self.assertEqual(op.text, "")
        self.assertEqual(op.start, 5)
        self.assertEqual(op.end, 12)
        self.assertEqual(op.length, len("Hello"))
        self.assertEqual(session.get_content(), "Hello")

    def test_replace_text(self):
        """Test replacing text at various positions."""
        # Replace at beginning
        op = self.session.replace(0, 5, "Hi")
        self.assertIsInstance(op, EditOperation)
        self.assertEqual(op.text, "Hi")
        self.assertEqual(op.start, 0)
        self.assertEqual(op.end, 5)
        self.assertEqual(op.length, len("Hi world!"))
        self.assertEqual(self.session.get_content(), "Hi world!")

        # Replace in middle
        content = "Hello beautiful world!"
        session = new_edit_service("", content)
        op = session.replace(6, 15, "amazing")
        self.assertIsInstance(op, EditOperation)
        self.assertEqual(op.text, "amazing")
        self.assertEqual(op.start, 6)
        self.assertEqual(op.end, 15)
        self.assertEqual(op.length, len("Hello amazing world!"))
        self.assertEqual(session.get_content(), "Hello amazing world!")

    def test_invalid_operations(self):
        """Test error handling for invalid operations."""
        # Invalid insert position
        with self.assertRaises(ValueError):
            self.session.insert(-1, "test")
        with self.assertRaises(ValueError):
            self.session.insert(len(self.initial_content) + 1, "test")

        # Invalid delete positions
        with self.assertRaises(ValueError):
            self.session.delete(-1, 5)
        with self.assertRaises(ValueError):
            self.session.delete(5, 3)  # end before start
        with self.assertRaises(ValueError):
            self.session.delete(0, len(self.initial_content) + 1)

        # Invalid replace positions
        with self.assertRaises(ValueError):
            self.session.replace(-1, 5, "test")
        with self.assertRaises(ValueError):
            self.session.replace(5, 3, "test")  # end before start
            
    def test_edge_cases(self):
        """Test edge cases and extreme situations."""
        # Empty content
        session = new_edit_service("", "")
        op = session.insert(0, "test")
        self.assertEqual(session.get_content(), "test")
        self.assertEqual(op.length, 4)
        
        op = session.delete(0, 4)
        self.assertEqual(session.get_content(), "")
        self.assertEqual(op.length, 0)
        
        # Very long content
        long_content = "a" * 1000000
        session = new_edit_service("", long_content)
        # Insert at start
        op = session.insert(0, "test")
        self.assertEqual(session.get_content(), "test" + long_content)
        self.assertEqual(op.length, 4 + 1000000)
        
        # Insert at end
        op = session.insert(len(session.current_content), "test")
        self.assertEqual(session.get_content(), "test" + long_content + "test")
        self.assertEqual(op.length, 4 + 1000000 + 4)
        
        # Delete from middle
        mid = len(session.current_content) // 2
        op = session.delete(mid, mid + 100000)
        self.assertEqual(op.length, len(session.current_content))
        
        # Special characters
        content = "Hello world!"
        session = new_edit_service("", content)
        # Insert newlines and tabs
        op = session.insert(5, "\n\t")
        self.assertEqual(session.get_content(), "Hello\n\t world!")
        self.assertEqual(op.text, "\n\t")
        
        # Delete across line boundaries
        op = session.delete(5, 8)
        self.assertEqual(session.get_content(), "Helloworld!")
        self.assertEqual(op.start, 5)
        self.assertEqual(op.end, 8)
        
        # Unicode characters
        content = "Hello 世界！"
        session = new_edit_service("", content)
        # Insert unicode
        op = session.insert(6, "美丽的")
        self.assertEqual(session.get_content(), "Hello 美丽的世界！")
        self.assertEqual(op.text, "美丽的")
        
        # Delete unicode
        op = session.delete(6, 9)
        self.assertEqual(session.get_content(), "Hello 世界！")
        self.assertEqual(op.start, 6)
        self.assertEqual(op.end, 9)
        
        # Multiple operations at same position
        session = new_edit_service("", "test")
        # Insert multiple times at same position
        session.insert(0, "1")
        session.insert(0, "2")
        session.insert(0, "3")
        self.assertEqual(session.get_content(), "321test")
        
        # Delete multiple times at same position
        session.delete(0, 1)
        session.delete(0, 1)
        self.assertEqual(session.get_content(), "1test")
        
        # Replace with empty and non-empty strings
        session = new_edit_service("", "Hello world!")
        # Replace with empty (equivalent to delete)
        op = session.replace(5, 11, "")
        self.assertEqual(session.get_content(), "Hello!")
        self.assertEqual(op.text, "")
        self.assertEqual(op.start, 5)
        self.assertEqual(op.end, 11)
        
        # Replace with longer text
        op = session.replace(0, 5, "Goodbye")
        self.assertEqual(session.get_content(), "Goodbye!")
        self.assertEqual(op.text, "Goodbye")
        
        # Replace with same length text
        op = session.replace(0, 7, "Welcome")
        self.assertEqual(session.get_content(), "Welcome!")
        self.assertEqual(op.text, "Welcome")

    def test_operation_history(self):
        """Test operation history tracking."""
        # Perform a series of operations
        self.session.insert(0, "Start: ")
        self.session.insert(len(self.session.current_content), " End")
        self.session.delete(0, 6)

        history = self.session.get_edit_history()
        self.assertEqual(len(history), 3)  # insert, insert, delete operations
        
        # Verify operations are EditOperation instances
        for op in history:
            self.assertIsInstance(op, EditOperation)
        
        # First operation: insert "Start: " at position 0
        self.assertEqual(history[0].start, 0)
        self.assertEqual(history[0].end, 0)
        self.assertEqual(history[0].text, "Start: ")
        
        # Second operation: insert " End" at the end
        self.assertEqual(history[1].start, len(self.initial_content) + len("Start: "))
        self.assertEqual(history[1].end, len(self.initial_content) + len("Start: "))
        self.assertEqual(history[1].text, " End")
        
        # Third operation: delete first 6 characters
        self.assertEqual(history[2].start, 0)
        self.assertEqual(history[2].end, 6)
        self.assertEqual(history[2].text, "")

    def test_timestamps(self):
        """Test timestamp tracking."""
        session = new_edit_service("", self.initial_content)
        initial_time = session.created_at
        initial_modified = session.last_modified
        
        time.sleep(0.1)
        session.insert(0, "Test")
        
        self.assertEqual(session.created_at, initial_time)
        self.assertTrue(session.last_modified > initial_modified)

if __name__ == '__main__':
    unittest.main()
