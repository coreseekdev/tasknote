"""测试 new_sub_task 方法的功能。

这个测试程序主要用于验证 FileTaskImpl.new_sub_task 方法在各种情况下的行为是否正确。
测试场景包括：
1. 没有 Task 标题
2. 存在 Task 标题但没有列表
3. 已经存在列表
4. 已经存在的列表包括嵌套列表
"""

import os
import sys
import logging
import unittest
from typing import List, Tuple, Optional, Dict, Any

# 配置日志
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from tasknotes.interface.markdown_service import MarkdownService, HeadSection, ListBlock, DocumentMeta
from tasknotes.interface.edit_session import EditSession
from tasknotes.interface.numbering_service import NumberingService
from tasknotes.interface.file_service import FileService
from tasknotes.interface.task import FileTask, InlineTask, Task
from tasknotes.core.edit_session_ot import EditSessionOT
from tasknotes.core.markdown import create_markdown_service
from tasknotes.services.file_task_service import FileTaskImpl, InlineTaskImpl


class MockFileService(FileService):
    """模拟文件服务，用于测试"""
    
    def __init__(self):
        self.files = {}
        self.in_transaction = False
    
    def read_file(self, path: str) -> str:
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]
    
    def write_file(self, path: str, content: str) -> None:
        self.files[path] = content
    
    def file_exists(self, path: str) -> bool:
        return path in self.files
    
    def delete_file(self, path: str) -> None:
        if path in self.files:
            del self.files[path]
    
    def list_files(self, directory: str = "", pattern: str = "*") -> List[str]:
        return [f for f in self.files.keys() if f.startswith(directory)]
    
    def create_directory(self, directory: str) -> None:
        pass
    
    def get_modified_time(self, path: str) -> float:
        return 0.0
    
    def rename(self, old_path: str, new_path: str) -> None:
        if old_path not in self.files:
            raise FileNotFoundError(f"File not found: {old_path}")
        if new_path in self.files:
            raise FileExistsError(f"File already exists: {new_path}")
        self.files[new_path] = self.files[old_path]
        del self.files[old_path]
    
    def begin_transaction(self) -> None:
        self.in_transaction = True
    
    def commit_transaction(self, message: str = "") -> None:
        self.in_transaction = False
    
    def abort_transaction(self) -> None:
        self.in_transaction = False


class MockNumberingService(NumberingService):
    """模拟编号服务，用于测试"""
    
    def __init__(self, initial_counters=None):
        self.counters = initial_counters or {"TASK": 0}
        self.default_prefix = "TASK"
        
    def set_counter(self, prefix: str, value: int) -> None:
        """设置特定前缀的计数器值（仅用于测试）
        
        Args:
            prefix: 要设置的前缀
            value: 计数器值
        """
        self.counters[prefix] = value
    
    def get_next_number(self, prefix: Optional[str] = None) -> str:
        if prefix is None:
            prefix = self.default_prefix
        if prefix not in self.counters:
            self.counters[prefix] = 0
        self.counters[prefix] += 1
        return f"{prefix}-{self.counters[prefix]:03d}"
    
    def get_current_number(self, prefix: Optional[str] = None) -> int:
        if prefix is None:
            prefix = self.default_prefix
        if prefix not in self.counters:
            self.counters[prefix] = 0
        return self.counters[prefix]
    
    def get_default_prefix(self) -> str:
        return self.default_prefix
    
    def set_default_prefix(self, prefix: str) -> None:
        self.default_prefix = prefix
    
    def get_all_prefixes(self) -> Dict[str, int]:
        return self.counters.copy()
    
    def reset_prefix(self, prefix: str, value: int = 0) -> None:
        self.counters[prefix] = value


class MockFileTaskImpl(FileTaskImpl):
    """模拟 FileTaskImpl 类，实现所有抽象方法"""
    
    def __init__(self, file_service: FileService, numbering_service: NumberingService, task_id: str, context: str):
        """初始化 MockFileTaskImpl 实例
        
        Args:
            file_service: 文件服务
            numbering_service: 编号服务
            task_id: 任务ID
            context: 任务内容
        """
        # 不调用父类的 __init__ 方法，而是直接初始化必要的属性
        self.file_service = file_service
        self.numbering_service = numbering_service
        self._task_id = task_id
        self._context = context
        self._context_updated_count = 0
        self._parse_cache = None
        self._markdown_service = None
    
    @property
    def task_id(self) -> str:
        """获取任务ID"""
        return self._task_id
    
    @property
    def task_message(self) -> str:
        """获取任务ID"""
        return self._task_id

    def mark_as_done(self) -> bool:
        """将任务标记为已完成"""
        return True
    
    def mark_as_undone(self) -> bool:
        """将任务标记为未完成"""
        return True
    
    def delete(self, task_id: Optional[str] = None, force: bool = False) -> bool:
        """删除任务或子任务"""
        return True
    
    def modify_task(self, task_id: Optional[str] = None, task_msg: Optional[str] = None) -> bool:
        """修改任务或子任务"""
        return True
    
    def tags(self, new_tags: Optional[List[str]] = None) -> List[str]:
        """获取或替换任务标签"""
        return []
    
    def tasks(self) -> List[Task]:
        """获取所有子任务"""
        return []
    
    def mark_as_archived(self, force: bool = False) -> bool:
        """将任务标记为已归档"""
        return True
    
    def add_related_task(self, task_id: str) -> 'FileTask':
        """添加相关任务"""
        return self
    
    def convert_task(self, task_id: str) -> 'FileTask':
        """将子任务转换为文件任务"""
        return self
    
    def tag_groups(self) -> Dict[str, Dict[str, Any]]:
        """获取标签组"""
        return {}


class TestNewSubTask(unittest.TestCase):
    """测试 new_sub_task 方法"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建模拟服务
        self.file_service = MockFileService()
        self.numbering_service = MockNumberingService()
        self.markdown_service = create_markdown_service()
    
    def test_no_task_section(self):
        """测试没有 Task 标题的情况"""
        # 准备测试数据
        content = """# Test Document
        
## Introduction
This is a test document.

## Conclusion
This is the conclusion.
"""
        
        # 创建 MockFileTaskImpl 实例
        task = MockFileTaskImpl(self.file_service, self.numbering_service, "TASK-000", content)
        
        # 调用 new_sub_task 方法
        sub_task = task.new_sub_task("Test task without section")
        
        # 验证结果
        updated_content = task.context
        logger.debug(f"更新后的内容:\n{updated_content}")
        
        # 验证是否创建了新的 Tasks 部分
        self.assertIn("## Tasks", updated_content)
        self.assertIn("- [ ] TASK-001: Test task without section", updated_content)
        
        # 验证格式是否正确（没有过多的换行符）
        sections = updated_content.split("##")
        tasks_section = [s for s in sections if "Tasks" in s.split("\n")[0]][0]
        
        # 确保 Tasks 部分的格式正确
        lines = tasks_section.strip().split("\n")
        self.assertEqual(lines[0], "Tasks")
        self.assertEqual(lines[1], "- [ ] TASK-001: Test task without section")
        
        # 验证返回的 InlineTask 是否正确
        self.assertEqual(sub_task.task_id, "TASK-001")
    
    def test_task_section_no_list(self):
        """测试存在 Task 标题但没有列表的情况"""
        # 准备测试数据
        content = """# Test Document
        
## Tasks

This section should contain tasks.

## Notes

Some notes here.

"""
        
        # 创建 MockFileTaskImpl 实例
        task = MockFileTaskImpl(self.file_service, self.numbering_service, "TASK-000", content)
        
        # 调用 new_sub_task 方法
        sub_task = task.new_sub_task("Test task with empty section")
        
        # 验证结果
        updated_content = task.context
        logger.debug(f"更新后的内容:\n{updated_content}")
        
        # 验证是否添加了新任务
        self.assertIn("## Tasks", updated_content)
        self.assertIn("- [ ] TASK-001: Test task with empty section", updated_content)
        
        # 修复 header text_range 后，任务现在正确地被添加到 Tasks 部分内
        tasks_section_pos = updated_content.find("## Tasks")
        notes_section_pos = updated_content.find("## Notes")
        task_pos = updated_content.find("- [ ] TASK-001: Test task with empty section")
        
        # 验证任务在 Tasks 部分之后，但在 Notes 部分之前
        self.assertGreater(task_pos, tasks_section_pos)
        self.assertLess(task_pos, notes_section_pos)
        
        # 验证返回的 InlineTask 是否正确
        self.assertEqual(sub_task.task_id, "TASK-001")
    
    def test_existing_list(self):
        """测试已经存在列表的情况"""
        # 准备测试数据
        content = """# Test Document
        
## Tasks
- [ ] TASK-001: First task
- [ ] TASK-002: Second task

## Notes
Some notes here.
"""
        
        # 创建 MockFileTaskImpl 实例
        self.numbering_service.set_counter("TASK", 2)  # 设置计数器值，下一个值将是 TASK-003
        task = MockFileTaskImpl(self.file_service, self.numbering_service, "TASK-000", content)
        
        # 调用 new_sub_task 方法
        sub_task = task.new_sub_task("Third task")
        
        # 验证结果
        updated_content = task.context
        logger.debug(f"更新后的内容:\n{updated_content}")
        
        # 验证是否在列表末尾添加了新任务
        self.assertIn("- [ ] TASK-003: Third task", updated_content)
        
        # 验证任务顺序
        lines = updated_content.split("\n")
        task_001_line = next((i for i, line in enumerate(lines) if "TASK-001" in line), -1)
        task_002_line = next((i for i, line in enumerate(lines) if "TASK-002" in line), -1)
        task_003_line = next((i for i, line in enumerate(lines) if "TASK-003" in line), -1)
        
        self.assertGreater(task_002_line, task_001_line)
        self.assertGreater(task_003_line, task_002_line)
        
        # 验证返回的 InlineTask 是否正确
        self.assertEqual(sub_task.task_id, "TASK-003")
    
    def test_nested_list(self):
        """测试已经存在的列表包括嵌套列表的情况"""
        # 准备测试数据
        content = """# Test Document with Nested List
        
## Tasks
- [ ] TASK-001: First task
  - tag1
  - tag2
- [ ] TASK-002: Second task
  - priority: high
  - deadline: 2025-05-20

## Notes
Some notes here.
"""
        
        # 创建 MockFileTaskImpl 实例
        task = MockFileTaskImpl(self.file_service, self.numbering_service, "TASK-000", content)
        
        # 调用 new_sub_task 方法
        sub_task = task.new_sub_task("Third task")
        
        # 验证结果
        updated_content = task.context
        logger.debug(f"更新后的内容:\n{updated_content}")
        
        # 验证是否在列表末尾添加了新任务
        self.assertIn("- [ ] TASK-001: Third task", updated_content)
        
        # 验证任务顺序和嵌套结构
        lines = updated_content.split("\n")
        task_001_first_line = next((i for i, line in enumerate(lines) if "TASK-001" in line and "First task" in line), -1)
        task_002_line = next((i for i, line in enumerate(lines) if "TASK-002" in line), -1)
        task_001_third_line = next((i for i, line in enumerate(lines) if "TASK-001" in line and "Third task" in line), -1)
        deadline_line = next((i for i, line in enumerate(lines) if "deadline" in line), -1)
        
        # 验证任务顺序：TASK-001 -> TASK-002 -> deadline -> TASK-001 (Third task)
        self.assertGreater(task_002_line, task_001_first_line)
        self.assertGreater(deadline_line, task_002_line)
        self.assertGreater(task_001_third_line, deadline_line)
        
        # 验证新任务不是嵌套在其他任务中的
        # 检查缩进级别
        task_001_third_indent = len(lines[task_001_third_line]) - len(lines[task_001_third_line].lstrip())
        task_002_indent = len(lines[task_002_line]) - len(lines[task_002_line].lstrip())
        deadline_indent = len(lines[deadline_line]) - len(lines[deadline_line].lstrip())
        
        # 新任务应该与主任务有相同的缩进级别，而不是与嵌套项相同
        self.assertEqual(task_001_third_indent, task_002_indent)
        self.assertNotEqual(task_001_third_indent, deadline_indent)
        
        # 验证返回的 InlineTask 是否正确
        self.assertEqual(sub_task.task_id, "TASK-001")


if __name__ == "__main__":
    unittest.main()
