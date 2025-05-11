"""测试任务列表追加功能。

这个测试程序主要用于验证通过 Markdown 接口追加任务的逻辑是否正确。
使用 ListItem 的 text_range 属性获取列表项范围，避免字符串解析。
"""

import os
import sys
import logging
import unittest
from typing import List, Tuple, Optional

# 配置日志
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from tasknotes.interface.markdown_service import MarkdownService, HeadSection, ListBlock, DocumentMeta
from tasknotes.interface.edit_session import EditSession
from tasknotes.core.edit_session_ot import EditSessionOT
from tasknotes.core.markdown import create_markdown_service


class TaskAppender:
    """用于测试任务列表追加功能的类"""
    
    def __init__(self, task_id: str):
        """初始化 TaskAppender 实例
        
        Args:
            task_id: 任务ID
        """
        self._task_id = task_id
        self._context = ""
        self._markdown_service = None
        self._parse_cache = None
    
    @property
    def context(self) -> str:
        """获取任务内容"""
        return self._context
    
    @context.setter
    def context(self, value: str):
        """设置任务内容"""
        if self._context != value:
            self._context = value
            self._parse_cache = None
    
    def get_markdown_service(self) -> MarkdownService:
        """获取 Markdown 服务实例"""
        if self._markdown_service is None:
            self._markdown_service = create_markdown_service()
        return self._markdown_service
    
    def parse_markdown(self) -> Tuple[DocumentMeta, List[HeadSection]]:
        """解析当前内容，并缓存结果"""
        if self._parse_cache is None:
            self._parse_cache = self.get_markdown_service().parse(self._context)
        return self._parse_cache
    
    def get_headers(self) -> List[HeadSection]:
        """获取标题列表"""
        _, headers = self.parse_markdown()
        return headers
    
    def _find_task_section(self, task_section_name: str) -> Optional[HeadSection]:
        """查找任务部分
        
        Args:
            task_section_name: 任务部分的标题名称
            
        Returns:
            Optional[HeadSection]: 找到的任务部分，如果没有找到则返回 None
        """
        for header in self.get_headers():
            if header.text == task_section_name and header.head_level == 2:  # ## Tasks
                return header
        return None
    
    def _append_task_to_list(self, task_id: str, task_msg: str, task_section_name: str, edit_session: EditSession) -> bool:
        """将任务添加到指定任务部分的列表中
        
        Args:
            task_id: 任务ID
            task_msg: 任务描述
            task_section_name: 任务部分的标题名称
            edit_session: 编辑会话
            
        Returns:
            bool: 是否成功添加任务
        """
        logger.debug(f"开始添加任务: {task_id} - {task_msg}")
        logger.debug(f"任务部分名称: {task_section_name}")
        
        # 查找任务部分
        task_section = self._find_task_section(task_section_name)
        if not task_section:
            # 没有找到任务部分，在文档末尾添加新部分
            current_content = edit_session.get_content()
            insert_pos = len(current_content)
            logger.debug(f"没有找到任务部分，在末尾添加新部分，位置: {insert_pos}")
            
            task_entry = f"- [ ] {task_id}: {task_msg}\n"
            new_section = f"\n## {task_section_name}\n{task_entry}"
            logger.debug(f"新部分内容:\n{new_section}")
            
            edit_session.insert(insert_pos, new_section)
            logger.debug(f"插入后内容:\n{edit_session.get_content()}")
            return True
        
        # 获取任务列表
        lists = list(task_section.get_lists())
        
        if lists:
            # 有列表，找到最后一个列表项
            task_list = lists[0]  # 假设只有一个列表
            list_items = list(task_list.list_items())
            
            if list_items:
                # 有列表项，在最后一个列表项的行尾插入
                last_item = list_items[-1]
                _, last_item_end = last_item.text_range
                
                # 获取当前内容
                current_content = edit_session.get_content()
                
                # 使用 last_item_end 作为插入位置
                # 这样可以正确处理嵌套列表的情况
                insert_pos = last_item_end -1
                
                # 在列表项结束位置插入新任务
                task_entry = f"- [ ] {task_id}: {task_msg}\n"
                logger.debug(f"在列表项结束位置 {insert_pos} 插入: {task_entry}")
                edit_session.insert(insert_pos, task_entry)
            else:
                # 列表存在但没有列表项，在列表开始处插入
                list_start, _ = task_list.text_range
                task_entry = f"- [ ] {task_id}: {task_msg}\n"
                logger.debug(f"在列表开始处 {list_start} 添加新任务: {task_entry}")
                edit_session.insert(list_start, task_entry)
        else:
            # 没有列表，在任务部分的标题后创建新列表
            section_start, _ = task_section.text_range
            current_content = edit_session.get_content()
            
            # 找到标题行结束位置
            header_line_end = current_content.find('\n', section_start)
            if header_line_end == -1:
                header_line_end = len(current_content)
            
            # 在标题行结束位置插入新任务
            task_entry = f"\n- [ ] {task_id}: {task_msg}\n"
            logger.debug(f"在标题行结束位置 {header_line_end} 添加新任务: {task_entry}")
            edit_session.insert(header_line_end, task_entry)
        
        logger.debug(f"插入后内容:\n{edit_session.get_content()}")
        return True


class TestTaskAppend(unittest.TestCase):
    """测试任务列表追加功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建 Markdown 服务
        self.markdown_service = create_markdown_service()
    
    def test_append_to_existing_list(self):
        """测试向已有列表追加任务"""
        # 准备测试数据
        content = """# Test Task
        
## Tasks
- [ ] TASK-001: First task
- [ ] TASK-002: Second task

## Notes
Some notes here.
"""
        
        # 创建 TaskAppender 实例
        task = TaskAppender("TASK-000")
        task.context = content
        task._markdown_service = self.markdown_service
        
        # 创建 EditSession
        edit_session = EditSessionOT(content)
        
        # 调用 _append_task_to_list 方法
        result = task._append_task_to_list("TASK-003", "Third task", "Tasks", edit_session)
        
        # 验证结果
        self.assertTrue(result)
        updated_content = edit_session.get_content()
        self.assertIn("TASK-003: Third task", updated_content)
        
        # 输出更新后的内容
        logger.debug(f"更新后的内容:\n{updated_content}")
    
    def test_append_to_empty_section(self):
        """测试向空的任务部分追加任务"""
        # 准备测试数据
        content = """# Test Task
        
## Tasks

## Notes
Some notes here.
"""
        
        # 创建 TaskAppender 实例
        task = TaskAppender("TASK-000")
        task.context = content
        task._markdown_service = self.markdown_service
        
        # 创建 EditSession
        edit_session = EditSessionOT(content)
        
        # 调用 _append_task_to_list 方法
        result = task._append_task_to_list("TASK-001", "First task", "Tasks", edit_session)
        
        # 验证结果
        self.assertTrue(result)
        updated_content = edit_session.get_content()
        self.assertIn("TASK-001: First task", updated_content)
        
        # 输出更新后的内容
        logger.debug(f"更新后的内容:\n{updated_content}")
    
    def test_create_new_section(self):
        """测试创建新的任务部分"""
        # 准备测试数据
        content = """# Test Task
        
## Notes
Some notes here.
"""
        
        # 创建 TaskAppender 实例
        task = TaskAppender("TASK-000")
        task.context = content
        task._markdown_service = self.markdown_service
        
        # 创建 EditSession
        edit_session = EditSessionOT(content)
        
        # 调用 _append_task_to_list 方法
        result = task._append_task_to_list("TASK-001", "First task", "Tasks", edit_session)
        
        # 验证结果
        self.assertTrue(result)
        updated_content = edit_session.get_content()
        self.assertIn("## Tasks", updated_content)
        self.assertIn("TASK-001: First task", updated_content)
        
        # 输出更新后的内容
        logger.debug(f"更新后的内容:\n{updated_content}")


    def test_append_to_nested_list(self):
        """测试向带有嵌套列表的任务列表追加任务"""
        # 准备测试数据 - 包含嵌套列表的任务
        content = """# Test Task with Nested List
        
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
        
        # 创建 TaskAppender 实例
        task = TaskAppender("TASK-000")
        task.context = content
        task._markdown_service = self.markdown_service
        
        # 创建 EditSession
        edit_session = EditSessionOT(content)
        
        # 调用 _append_task_to_list 方法
        result = task._append_task_to_list("TASK-003", "Third task", "Tasks", edit_session)
        
        # 验证结果
        self.assertTrue(result)
        updated_content = edit_session.get_content()
        self.assertIn("TASK-003: Third task", updated_content)
        
        # 确保新任务被添加在最后一个任务项之后，而不是嵌套在其中
        task_lines = updated_content.split('\n')
        task_003_line = next((i for i, line in enumerate(task_lines) if "TASK-003" in line), -1)
        task_002_line = next((i for i, line in enumerate(task_lines) if "TASK-002" in line), -1)
        deadline_line = next((i for i, line in enumerate(task_lines) if "deadline" in line), -1)
        
        # 验证任务顺序：TASK-002 -> deadline -> TASK-003
        self.assertGreater(task_003_line, deadline_line)
        self.assertGreater(deadline_line, task_002_line)
        
        # 输出更新后的内容
        logger.debug(f"更新后的内容:\n{updated_content}")


if __name__ == "__main__":
    unittest.main()