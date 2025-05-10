"""Tests for the EditSession class."""

import unittest
import time
import uuid
from tasknotes.core.task_env import connect_edit_service
from tasknotes.core.edit_session_ot import Operation

class TestEditSession(unittest.TestCase):
    def setUp(self):
        self.initial_content = "Hello world!"
        self.session = connect_edit_service("", self.initial_content)

    def test_init_with_custom_session_id(self):
        """Test initialization with a custom session_id."""
        custom_id = "test-session-123"
        session = connect_edit_service("", self.initial_content, session_id=custom_id)
        self.assertEqual(session.session_id, custom_id)

    def test_init_with_default_session_id(self):
        """Test initialization with default UUID session_id."""
        session = connect_edit_service("", self.initial_content)
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
        self.assertEqual(
            self.session.insert(0, "Start: "),
            "Start: Hello world!"
        )

        # Insert in middle
        self.assertEqual(
            self.session.insert(7, "beautiful "),
            "Start: beautiful Hello world!"
        )

        # Insert at end
        self.assertEqual(
            self.session.insert(len(self.session.current_content), "!"),
            "Start: beautiful Hello world!!"
        )

    def test_delete_text(self):
        """Test deleting text at various positions."""
        # Delete from beginning
        self.assertEqual(
            self.session.delete(0, 6),
            "world!"
        )

        # Delete from middle
        content = "Hello beautiful world!"
        session = connect_edit_service("", content)
        self.assertEqual(
            session.delete(6, 15),
            "Hello world!"
        )

        # Delete from end
        self.assertEqual(
            session.delete(5, 12),
            "Hello"
        )

    def test_replace_text(self):
        """Test replacing text at various positions."""
        # Replace at beginning
        self.assertEqual(
            self.session.replace(0, 5, "Hi"),
            "Hi world!"
        )

        # Replace in middle
        content = "Hello beautiful world!"
        session = connect_edit_service("", content)
        self.assertEqual(
            session.replace(6, 15, "amazing"),
            "Hello amazing world!"
        )

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
        session = connect_edit_service("", "")
        self.assertEqual(session.insert(0, "test"), "test")
        self.assertEqual(session.delete(0, 4), "")
        
        # Very long content
        long_content = "a" * 1000000
        session = connect_edit_service("", long_content)
        # Insert at start
        self.assertEqual(
            session.insert(0, "test"),
            "test" + long_content
        )
        # Insert at end
        self.assertEqual(
            session.insert(len(session.current_content), "test"),
            "test" + long_content + "test"
        )
        # Delete from middle
        mid = len(session.current_content) // 2
        result = session.delete(mid, mid + 100000)
        self.assertEqual(len(result), len(session.current_content))
        
        # Special characters
        content = "Hello world!"
        session = connect_edit_service("", content)
        # Insert newlines and tabs
        self.assertEqual(
            session.insert(5, "\n\t"),
            "Hello\n\t world!"
        )
        # Delete across line boundaries
        self.assertEqual(
            session.delete(5, 8),
            "Helloworld!"
        )
        
        # Unicode characters
        content = "Hello 世界！"
        session = connect_edit_service("", content)
        # Insert unicode
        self.assertEqual(
            session.insert(6, "美丽的"),
            "Hello 美丽的世界！"
        )
        # Delete unicode
        self.assertEqual(
            session.delete(6, 9),
            "Hello 世界！"
        )
        
        # Multiple operations at same position
        session = connect_edit_service("", "test")
        # Insert multiple times at same position
        session.insert(0, "1")
        session.insert(0, "2")
        session.insert(0, "3")
        self.assertEqual(session.current_content, "321test")
        # Delete multiple times at same position
        session.delete(0, 1)
        session.delete(0, 1)
        self.assertEqual(session.current_content, "1test")
        
        # Replace with empty and non-empty strings
        session = connect_edit_service("", "Hello world!")
        # Replace with empty (equivalent to delete)
        self.assertEqual(
            session.replace(5, 11, ""),
            "Hello!"
        )
        # Replace with longer text
        self.assertEqual(
            session.replace(0, 5, "Goodbye"),
            "Goodbye!"
        )
        # Replace with same length text
        self.assertEqual(
            session.replace(0, 7, "Welcome"),
            "Welcome!"
        )

    def test_operation_history(self):
        """Test operation history tracking."""
        # Perform a series of operations
        self.session.insert(0, "Start: ")
        self.session.insert(len(self.session.current_content), " End")
        self.session.delete(0, 6)

        history = self.session.get_edit_history()
        self.assertEqual(len(history), 3)  # insert, insert, delete operations
        
        # Verify operations
        # First operation: insert "Start: " at position 0
        self.assertEqual(history[0]["start"], 0)
        self.assertEqual(history[0]["end"], 0)
        self.assertEqual(history[0]["text"], "Start: ")
        
        # Second operation: insert " End" at the end
        self.assertEqual(history[1]["start"], len(self.initial_content) + len("Start: "))
        self.assertEqual(history[1]["end"], len(self.initial_content) + len("Start: "))
        self.assertEqual(history[1]["text"], " End")
        
        # Third operation: delete first 6 characters
        self.assertEqual(history[2]["start"], 0)
        self.assertEqual(history[2]["end"], 6)
        self.assertEqual(history[2]["text"], "")

    def test_timestamps(self):
        """Test timestamp tracking."""
        session = connect_edit_service("", self.initial_content)
        initial_time = session.created_at
        initial_modified = session.last_modified
        
        time.sleep(0.1)
        session.insert(0, "Test")
        
        self.assertEqual(session.created_at, initial_time)
        self.assertTrue(session.last_modified > initial_modified)

if __name__ == '__main__':
    unittest.main()
