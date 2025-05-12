#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 InlineTaskImpl.convert_task 方法
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from typing import Tuple, List, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tasknotes.interface.task import FileTask, InlineTask
from tasknotes.interface.file_service import FileService
from tasknotes.interface.edit_session import EditSession
from tasknotes.core.edit_session_ot import EditSessionOT
from tasknotes.interface.markdown_service import ListItem, ListBlock, MarkdownService
from tasknotes.core.markdown import TreeSitterMarkdownService, TreeSitterListItem, create_markdown_service
from tasknotes.interface.numbering_service import NumberingService
from tasknotes.services.file_task_service import InlineTaskImpl, FileTaskImpl, FILE_TASK_TEMPLATE


def get_list_item_from_markdown(markdown_text: str, item_index: int = 0) -> ListItem:
    """从 Markdown 文本中获取列表项
    
    Args:
        markdown_text: Markdown 文本
        item_index: 要获取的列表项索引，默认为第一个
        
    Returns:
        ListItem: 解析得到的列表项
        
    Raises:
        IndexError: 如果指定索引的列表项不存在
    """
    # 创建 Markdown 服务实例
    markdown_service = create_markdown_service()
    
    # 解析 Markdown 文本
    meta, headers = markdown_service.parse(markdown_text)
    
    # 获取所有列表块
    list_blocks = []
    for header in headers:
        list_blocks.extend(list(header.get_lists()))
    
    if not list_blocks:
        raise IndexError(f"No list blocks found in markdown text: {markdown_text}")
    
    # 获取所有列表项
    list_items = []
    for block in list_blocks:
        list_items.extend(list(block.list_items()))
    
    if not list_items:
        raise IndexError(f"No list items found in markdown text: {markdown_text}")
    
    # 返回指定索引的列表项
    if item_index >= len(list_items):
        raise IndexError(f"List item index {item_index} out of range (0-{len(list_items)-1})")
    
    return list_items[item_index]


class TestConvertTask(unittest.TestCase):
    """测试 InlineTaskImpl.convert_task 方法"""
    
    def setUp(self):
        """设置测试环境"""
        # 模拟服务
        self.file_service = MagicMock(spec=FileService)
        self.numbering_service = MagicMock(spec=NumberingService)
        
        # 设置文件服务的行为
        self.file_service.file_exists.return_value = False
        
        # 设置编号服务的行为
        self.numbering_service.get_default_prefix.return_value = "TASK"
        
        # 使用真实的 EditSessionOT 实现，并将其包装为一个 spy 对象
        # 这样我们可以记录调用参数，同时也能获取真实的编辑结果
        self.original_edit_sessions = {}  # 用于存储原始的 EditSession 实例
        
    def test_convert_task_simple(self):
        """测试简单任务的转换"""
        # 创建一个简单的 Markdown 文本
        markdown_text = """# Test Document

## Tasks

- [ ] Simple task
"""
        
        # 从 Markdown 文本中获取列表项
        list_item = get_list_item_from_markdown(markdown_text)
        
        # 创建真实的 EditSessionOT 实例
        original_edit_session = EditSessionOT(markdown_text)
        
        # 使用 MagicMock 包装真实的 EditSessionOT，以记录调用参数
        edit_session = MagicMock(spec=EditSession)
        edit_session.replace.side_effect = original_edit_session.replace
        
        # 保存原始的 EditSession 实例以便后续验证
        self.original_edit_sessions["simple"] = original_edit_session
        
        # 创建 InlineTaskImpl 实例
        task_id = "TASK-001"
        inline_task = InlineTaskImpl(
            self.file_service, 
            self.numbering_service,
            edit_session,
            list_item
        )
        
        # 手动设置任务 ID
        inline_task._task_id = task_id
        
        # 调用 convert_task 方法
        file_task = inline_task.convert_task()
        
        # 验证结果
        self.assertIsNotNone(file_task)
        self.assertIsInstance(file_task, FileTaskImpl)
        self.assertEqual(file_task.task_id, task_id)
        
        # 验证文件服务调用 - 不应该写入文件，实际写入的工作由上层调用 file task 完成
        self.file_service.write_file.assert_not_called()
        
        # 验证编辑会话调用
        edit_session.replace.assert_called_once()
        call_args = edit_session.replace.call_args[0]
        
        # 1. 验证替换的文本内容
        self.assertEqual(call_args[2], f"[{task_id}]({task_id}.md): Simple task")
        
        # 2. 验证替换的范围是内联范围
        start_pos, end_pos = call_args[0], call_args[1]
        inline_start, inline_end = list_item.inline_item_text_range
        self.assertEqual(start_pos, inline_start)
        self.assertEqual(end_pos, inline_end)
        
        # 3. 验证修改后的完整文本
        modified_text = self.original_edit_sessions["simple"].get_content()
        
        # 验证修改后的文本包含链接形式的任务
        expected_task_line = f"- [ ] [{task_id}]({task_id}.md): Simple task"
        self.assertIn(expected_task_line, modified_text)
        
        # 4. 直接对比完整的修改后文本
        expected_full_text = f"""# Test Document

## Tasks

- [ ] [{task_id}]({task_id}.md): Simple task
"""
        self.assertEqual(modified_text, expected_full_text)  # new_text
        
    def test_convert_task_with_nested_lists(self):
        """测试带有嵌套列表的任务转换"""
        # 创建一个带有嵌套列表的 Markdown 文本
        markdown_text = """# Test Document

## Tasks

- [x] Task with nested lists
  - Nested item 1
  - Nested item 2
    - Deeply nested item
"""
        
        # 从 Markdown 文本中获取列表项
        list_item = get_list_item_from_markdown(markdown_text)
        
        # 创建真实的 EditSessionOT 实例
        original_edit_session = EditSessionOT(markdown_text)
        
        # 使用 MagicMock 包装真实的 EditSessionOT，以记录调用参数
        edit_session = MagicMock(spec=EditSession)
        edit_session.replace.side_effect = original_edit_session.replace
        
        # 保存原始的 EditSession 实例以便后续验证
        self.original_edit_sessions["nested"] = original_edit_session
        
        # 创建 InlineTaskImpl 实例
        task_id = "TASK-002"
        inline_task = InlineTaskImpl(
            self.file_service, 
            self.numbering_service,
            edit_session,
            list_item
        )
        
        # 手动设置任务 ID
        inline_task._task_id = task_id
        
        # 调用 convert_task 方法
        file_task = inline_task.convert_task()
        
        # 验证结果
        self.assertIsNotNone(file_task)
        self.assertIsInstance(file_task, FileTaskImpl)
        self.assertEqual(file_task.task_id, task_id)
        
        # 验证文件服务调用 - 不应该写入文件，实际写入的工作由上层调用 file task 完成
        self.file_service.write_file.assert_not_called()
        
        # 验证编辑会话调用 - 关键是只替换内联部分，不影响嵌套列表
        edit_session.replace.assert_called_once()
        call_args = edit_session.replace.call_args[0]
        
        # 1. 验证替换的文本内容
        self.assertEqual(call_args[2], f"[{task_id}]({task_id}.md): Task with nested lists")
        
        # 2. 验证替换的范围是内联范围，而不是完整范围
        start_pos, end_pos = call_args[0], call_args[1]
        inline_start, inline_end = list_item.inline_item_text_range
        self.assertEqual(start_pos, inline_start)
        self.assertEqual(end_pos, inline_end)
        
        # 3. 验证替换的范围小于完整范围（当有嵌套列表时）
        full_start, full_end = list_item.text_range
        if len(list(list_item.get_lists())) > 0:  # 如果有嵌套列表
            self.assertLess(end_pos, full_end, "替换范围应小于完整范围，以保留嵌套列表")
        
        # 4. 验证修改后的完整文本
        modified_text = self.original_edit_sessions["nested"].get_content()
        
        # 验证修改后的文本包含链接形式的任务
        expected_task_line = f"- [x] [{task_id}]({task_id}.md): Task with nested lists"
        self.assertIn(expected_task_line, modified_text)
        
        # 验证嵌套列表项仍然存在
        self.assertIn("- Nested item 1", modified_text)
        self.assertIn("- Nested item 2", modified_text)
        self.assertIn("- Deeply nested item", modified_text)
        
        # 5. 直接对比完整的修改后文本
        expected_full_text = f"""# Test Document

## Tasks

- [x] [{task_id}]({task_id}.md): Task with nested lists
  - Nested item 1
  - Nested item 2
    - Deeply nested item
"""
        self.assertEqual(modified_text, expected_full_text)  # new_text
        
    def test_convert_task_with_existing_link(self):
        """测试已有链接的任务转换"""
        # 创建一个带有链接的 Markdown 文本
        task_id = "TASK-003"
        markdown_text = f"""# Test Document

## Tasks

- [ ] [{task_id}]({task_id}.md): Task with link
"""
        
        # 从 Markdown 文本中获取列表项
        list_item = get_list_item_from_markdown(markdown_text)
        
        # 创建真实的 EditSessionOT 实例
        original_edit_session = EditSessionOT(markdown_text)
        
        # 使用 MagicMock 包装真实的 EditSessionOT，以记录调用参数
        edit_session = MagicMock(spec=EditSession)
        edit_session.replace.side_effect = original_edit_session.replace
        
        # 保存原始的 EditSession 实例以便后续验证
        self.original_edit_sessions["existing_link"] = original_edit_session
        
        # 模拟文件存在
        self.file_service.file_exists.return_value = True
        self.file_service.read_file.return_value = "Existing task content"
        
        # 创建 InlineTaskImpl 实例
        inline_task = InlineTaskImpl(
            self.file_service, 
            self.numbering_service,
            edit_session,
            list_item
        )
        
        # 注意：不需要手动设置 task_id 和 task_link，因为 InlineTaskImpl 构造函数会从列表项文本中提取这些信息
        
        # 调用 convert_task 方法
        file_task = inline_task.convert_task()
        
        # 验证结果
        self.assertIsNotNone(file_task)
        self.assertIsInstance(file_task, FileTaskImpl)
        self.assertEqual(file_task.task_id, task_id)
        
        # 验证没有创建新文件
        self.file_service.write_file.assert_not_called()
        
        # 验证不调用编辑会话的替换方法，因为任务已经有链接
        edit_session.replace.assert_not_called()
        
        # 验证文本没有变化
        modified_text = self.original_edit_sessions["existing_link"].get_content()
        self.assertEqual(modified_text, markdown_text)
        
        # 直接对比完整的文本，确保没有任何变化
        expected_full_text = f"""# Test Document

## Tasks

- [ ] [{task_id}]({task_id}.md): Task with link
"""
        self.assertEqual(modified_text, expected_full_text)
        
    def test_convert_task_with_multiline_content(self):
        """测试多行内容的任务转换"""
        # 注意：Markdown 列表项中的换行在解析时会被处理为空格
        # 所以我们使用一个长文本来模拟多行内容
        markdown_text = """# Test Document

## Tasks

- [ ] Task with a very long description that would typically be displayed across multiple lines in a text editor
"""
        
        # 从 Markdown 文本中获取列表项
        list_item = get_list_item_from_markdown(markdown_text)
        
        # 创建真实的 EditSessionOT 实例
        original_edit_session = EditSessionOT(markdown_text)
        
        # 使用 MagicMock 包装真实的 EditSessionOT，以记录调用参数
        edit_session = MagicMock(spec=EditSession)
        edit_session.replace.side_effect = original_edit_session.replace
        
        # 保存原始的 EditSession 实例以便后续验证
        self.original_edit_sessions["multiline"] = original_edit_session
        
        # 创建 InlineTaskImpl 实例
        task_id = "TASK-004"
        inline_task = InlineTaskImpl(
            self.file_service, 
            self.numbering_service,
            edit_session,
            list_item
        )
        
        # 手动设置任务 ID
        inline_task._task_id = task_id
        
        # 调用 convert_task 方法
        file_task = inline_task.convert_task()
        
        # 验证结果
        self.assertIsNotNone(file_task)
        self.assertIsInstance(file_task, FileTaskImpl)
        
        # 验证文件服务调用 - 不应该写入文件，实际写入的工作由上层调用 file task 完成
        self.file_service.write_file.assert_not_called()
        
        # 验证编辑会话调用
        edit_session.replace.assert_called_once()
        call_args = edit_session.replace.call_args[0]
        
        # 1. 验证替换的文本内容
        expected_text = "Task with a very long description that would typically be displayed across multiple lines in a text editor"
        self.assertEqual(call_args[2], f"[{task_id}]({task_id}.md): {expected_text}")
        
        # 2. 验证替换的范围是内联范围
        start_pos, end_pos = call_args[0], call_args[1]
        inline_start, inline_end = list_item.inline_item_text_range
        self.assertEqual(start_pos, inline_start)
        self.assertEqual(end_pos, inline_end)
        
        # 3. 验证修改后的完整文本
        modified_text = self.original_edit_sessions["multiline"].get_content()
        
        # 验证修改后的文本包含链接形式的任务
        expected_task_line = f"- [ ] [{task_id}]({task_id}.md): {expected_text}"
        self.assertIn(expected_task_line, modified_text)
        
        # 4. 直接对比完整的修改后文本
        expected_full_text = f"""# Test Document

## Tasks

- [ ] [{task_id}]({task_id}.md): {expected_text}
"""
        self.assertEqual(modified_text, expected_full_text)  # new_text


if __name__ == "__main__":
    unittest.main()
