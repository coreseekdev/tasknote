#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 ListItem.text_range 的范围，特别是在存在嵌套列表的情况下
"""

import os
import sys
import unittest
from typing import Tuple, List

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tasknotes.core.markdown import TreeSitterMarkdownService
from tasknotes.interface.markdown_service import ListItem, ListBlock


class TestListItemTextRange(unittest.TestCase):
    """测试 ListItem.text_range 的范围"""

    def setUp(self):
        """设置测试环境"""
        self.markdown_service = TreeSitterMarkdownService()

    def _get_list_items(self, markdown_content: str) -> List[ListItem]:
        """从 Markdown 内容中获取所有列表项"""
        meta, headers = self.markdown_service.parse(markdown_content)
        
        # 查找所有列表块
        list_blocks = []
        for header in headers:
            list_blocks.extend(list(header.get_lists()))
        
        # 获取所有列表项
        list_items = []
        for block in list_blocks:
            list_items.extend(list(block.list_items()))
        
        return list_items

    def _print_text_range_info(self, markdown_content: str, list_items: List[ListItem]):
        """打印文本范围信息"""
        print("\n原始 Markdown 内容:")
        for i, line in enumerate(markdown_content.split('\n')):
            print(f"{i}: {line}")
        
        print("\n列表项信息:")
        for i, item in enumerate(list_items):
            start, end = item.text_range
            text = markdown_content[start:end]
            print(f"列表项 {i}:")
            print(f"  文本: '{item.text}'")
            print(f"  范围: ({start}, {end})")
            print(f"  原始文本内容: '{text}'")
            print(f"  是否有嵌套列表: {len(list(item.get_lists())) > 0}")
            print()

    def test_simple_list(self):
        """测试简单列表的文本范围"""
        markdown = """# Test Document

## Tasks

- Item 1
- Item 2
- Item 3
"""
        list_items = self._get_list_items(markdown)
        self._print_text_range_info(markdown, list_items)
        
        # 验证列表项数量
        self.assertEqual(len(list_items), 3)
        
        # 验证每个列表项的文本
        self.assertEqual(list_items[0].text, "Item 1")
        self.assertEqual(list_items[1].text, "Item 2")
        self.assertEqual(list_items[2].text, "Item 3")

    def test_nested_list(self):
        """测试嵌套列表的文本范围"""
        markdown = """# Test Document

## Tasks

- Item 1
  - Nested Item 1.1
  - Nested Item 1.2
- Item 2
- Item 3
  - Nested Item 3.1
"""
        list_items = self._get_list_items(markdown)
        self._print_text_range_info(markdown, list_items)
        
        # 验证列表项数量 (应该包括所有嵌套项)
        self.assertEqual(len(list_items), 6)
        
        # 验证第一个列表项的文本 (不应包括嵌套项)
        self.assertEqual(list_items[0].text, "Item 1")
        
        # 验证第一个列表项是否有嵌套列表
        self.assertTrue(len(list(list_items[0].get_lists())) > 0)

    def test_task_list(self):
        """测试任务列表的文本范围"""
        markdown = """# Test Document

## Tasks

- [ ] Task 1
- [x] Task 2
  - [ ] Nested Task 2.1
  - [x] Nested Task 2.2
- [ ] Task 3
"""
        list_items = self._get_list_items(markdown)
        self._print_text_range_info(markdown, list_items)
        
        # 验证列表项数量
        self.assertEqual(len(list_items), 5)
        
        # 验证任务状态
        self.assertTrue(list_items[0].is_task)
        self.assertFalse(list_items[0].is_completed_task)
        self.assertTrue(list_items[1].is_task)
        self.assertTrue(list_items[1].is_completed_task)

    def test_complex_list(self):
        """测试复杂列表的文本范围，包括任务ID和链接"""
        markdown = """# Test Document

## Tasks

- [ ] TASK-001: Simple task
- [x] [TASK-002](TASK-002.md): Task with link
  - [ ] Nested task under linked task
  - [ ] Another nested task
- [ ] `TASK-003`: Task with code
  - Nested non-task item
    - Deeply nested item
"""
        list_items = self._get_list_items(markdown)
        self._print_text_range_info(markdown, list_items)
        
        # 验证列表项数量
        self.assertEqual(len(list_items), 6)
        
        # 验证任务文本
        self.assertEqual(list_items[0].text, "TASK-001: Simple task")
        self.assertEqual(list_items[1].text, "[TASK-002](TASK-002.md): Task with link")
        self.assertEqual(list_items[2].text, "Nested task under linked task")


if __name__ == "__main__":
    unittest.main()
