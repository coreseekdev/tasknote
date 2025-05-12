#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 FileTaskService 类的功能
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from typing import Tuple, List, Optional, Dict, Any

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tasknotes.interface.task import FileTask, FileTaskMut, InlineTask, InlineTaskMut, Task, TaskMut
from tasknotes.interface.file_service import FileService
from tasknotes.interface.edit_session import EditSession
from tasknotes.interface.markdown_service import ListItem, ListBlock, MarkdownService
from tasknotes.interface.numbering_service import NumberingService
from tasknotes.services.file_task_service import FileTaskService, FileTaskImpl, InlineTaskImpl, FILE_TASK_TEMPLATE


class TestFileTaskService(unittest.TestCase):
    """测试 FileTaskService 类的功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 模拟服务
        self.file_service = MagicMock(spec=FileService)
        self.numbering_service = MagicMock(spec=NumberingService)
        self.edit_session = MagicMock(spec=EditSession)
        
        # 设置文件服务的行为
        self.file_service.file_exists.return_value = False
        
        # 设置编号服务的行为
        self.numbering_service.get_default_prefix.return_value = "TASK"
        self.numbering_service.get_next_number.return_value = "TASK-001"
        
        # 创建 FileTaskService 实例
        self.task_service = FileTaskService(self.file_service, self.numbering_service)
        
        # 模拟 root_task.new_sub_task 方法
        self.mock_root_task = MagicMock(spec=FileTaskMut)
        self.task_service.root_task = self.mock_root_task
        
    def tearDown(self):
        """清理测试环境"""
        # 清理模拟对象
        pass
    
    def test_new_task(self):
        """测试 new_task 方法，验证其使用 convert_task 创建新任务"""
        # 准备测试数据
        task_msg = "Test Task"
        task_id = "TASK-001"
        
        # 创建模拟的 InlineTaskMut 实例
        mock_inline_task = MagicMock(spec=InlineTaskMut)
        mock_file_task = MagicMock(spec=FileTaskMut)
        
        # 设置 root_task.new_sub_task 方法返回模拟的 InlineTaskMut
        self.mock_root_task.new_sub_task.return_value = mock_inline_task
        
        # 设置 convert_task 方法返回模拟的 FileTaskMut
        mock_inline_task.convert_task.return_value = mock_file_task
        
        # 调用被测试的方法
        result = self.task_service.new_task(task_msg)
        
        # 验证结果
        self.assertEqual(result, mock_file_task)
        
        # 验证方法调用
        self.mock_root_task.new_sub_task.assert_called_once_with(task_msg, None)
        mock_inline_task.convert_task.assert_called_once()
    
    def test_new_task_with_prefix(self):
        """测试带有前缀的 new_task 方法"""
        # 准备测试数据
        task_msg = "Test Task"
        task_prefix = "PROJ"
        
        # 创建模拟的 InlineTaskMut 实例
        mock_inline_task = MagicMock(spec=InlineTaskMut)
        mock_file_task = MagicMock(spec=FileTaskMut)
        
        # 设置 root_task.new_sub_task 方法返回模拟的 InlineTaskMut
        self.mock_root_task.new_sub_task.return_value = mock_inline_task
        
        # 设置 convert_task 方法返回模拟的 FileTaskMut
        mock_inline_task.convert_task.return_value = mock_file_task
        
        # 调用被测试的方法
        result = self.task_service.new_task(task_msg, task_prefix)
        
        # 验证结果
        self.assertEqual(result, mock_file_task)
        
        # 验证方法调用
        self.mock_root_task.new_sub_task.assert_called_once_with(task_msg, task_prefix)
        mock_inline_task.convert_task.assert_called_once()
    
    def test_new_task_failure(self):
        """测试 new_task 方法在 root_task.new_sub_task 返回 None 时的行为"""
        # 准备测试数据
        task_msg = "Test Task"
        
        # 设置 root_task.new_sub_task 方法返回 None
        self.mock_root_task.new_sub_task.return_value = None
        
        # 调用被测试的方法
        result = self.task_service.new_task(task_msg)
        
        # 验证结果
        self.assertIsNone(result)
        
        # 验证方法调用
        self.mock_root_task.new_sub_task.assert_called_once_with(task_msg, None)


if __name__ == "__main__":
    unittest.main()
