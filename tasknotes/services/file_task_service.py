"""File-based task service implementation for TaskNotes.

This module provides concrete implementations of the Task, InlineTask, FileTask,
and TaskService interfaces defined in the task module.
"""

import os
import time
import re
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Iterator

from tasknotes.interface.file_service import FileService
from tasknotes.interface.numbering_service import NumberingService
from tasknotes.interface.task import Task, InlineTask, FileTask, TaskService
from tasknotes.interface.markdown_service import MarkdownService, HeadSection, ListBlock, ListItem,DocumentMeta
from tasknotes.interface.edit_session import EditSession, EditOperation
from tasknotes.core.config import config
from tasknotes.services.numbering_service import TaskNumberingService
from tasknotes.core.markdown import create_markdown_service
from tasknotes.core.edit_session_ot import EditSessionOT

# 任务模板 - 用于创建新任务
FILE_TASK_TEMPLATE = """# {name}

{description}

## Tasks

## Notes

## Tags

### Milestones 

### Kanban

1. TODO
2. DOING
3. DONE

"""

class InlineTaskImpl(InlineTask):
    """Implementation of InlineTask interface."""
    
    def __init__(self, file_service: FileService, numbering_service: NumberingService,
                 edit_session: EditSession, list_item: 'ListItem'):
        """Initialize an InlineTaskImpl instance.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: The numbering service to use for generating task IDs
            edit_session: The edit session to use for modifying the task
            list_item: The ListItem object representing this task in the markdown
        """
        from tasknotes.core.markdown import parse_task_inline_string
        
        self.file_service = file_service
        self.numbering_service = numbering_service
        self._edit_session = edit_session
        self.list_item = list_item
        
        # Parse the list item text to extract task ID, link, and text
        parsed_result = parse_task_inline_string(list_item.text)
        self._task_id = parsed_result.get('task_id', None) or "task_id"
        self._task_link = parsed_result.get('link', None)
        self._task_message = parsed_result.get('text', list_item.text)
    
    @property
    def task_id(self) -> str:
        """Get the task ID."""
        return self._task_id
    
    @property
    def task_message(self) -> str:
        """获取任务消息内容"""
        return self._task_message

    def convert_task(self) -> FileTask:
        """Convert this inline task to a file task."""
        raise NotImplementedError("convert_task not implemented")

    def get_related_file_task(self) -> Optional['FileTask']:
        """
        返回当前 inline task 关联的 FileTask ，如果存在

        NOTE: 当 Task 使用 link 的形式表示时，链接的 target 就是 FileTask
        """
        pass

    def mark_as_done(self) -> bool:
        """Mark the task as done."""
        raise NotImplementedError("mark_as_done not implemented")
    
    def mark_as_undone(self) -> bool:
        """Mark the task as not done."""
        raise NotImplementedError("mark_as_undone not implemented")
    
    def delete(self, force: bool = False) -> bool:
        """Delete the task."""
        raise NotImplementedError("delete not implemented")
    
    def modify_task(self, task_msg: str) -> bool:
        """Update the task description or title."""
        raise NotImplementedError("modify_task not implemented")
    
    def tags(self, new_tags: Optional[List[str]] = None) -> List[str]:
        """Get or replace the list of tags associated with this task."""
        raise NotImplementedError("tags not implemented")


class FileTaskImpl(FileTask):
    """Implementation of FileTask interface."""
    
    def __init__(self, file_service: FileService, numbering_service: NumberingService, task_id: str, context: str):
        """Initialize a FileTaskImpl instance.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: The numbering service to use for generating task IDs
            task_id: ID of the task
            context: The markdown content of the task
        """
        self._task_id = task_id
        self.file_service = file_service
        self.numbering_service = numbering_service
        self._context = context
        self._context_updated_count = 0
        self._parse_cache = None
    
    @property
    def context(self) -> str:
        """Get the markdown content of the task.
        
        Returns:
            str: The markdown content
        """
        return self._context
    
    @context.setter
    def context(self, value: str) -> None:
        """Set the markdown content of the task.
        
        Only updates if the content has changed, and invalidates the parse cache if needed.
        
        Args:
            value: The new markdown content
        """
        if self._context != value:
            self._context = value
            self._context_updated_count += 1
            self._parse_cache = None  # 内容变化时清除缓存
    
    def get_markdown_service(self) -> MarkdownService:
        """Get or create a markdown service instance.
        
        Returns:
            MarkdownService: An instance of the markdown service
        """

        # 有必要为每个 FileTask 都构造一个 markdown_service， 因为其本质为 parser 。
        # 基于 tree-sitter 增量的本质决定了，不能复用 parser.
        if self._markdown_service is None:
            self._markdown_service = create_markdown_service()
        return self._markdown_service
    
    def parse_markdown(self) -> Tuple[DocumentMeta, Iterator[HeadSection]]:
        """Parse current context with caching.
        
        Returns:
            Tuple: The parsed metadata and headers
        """
        # 使用当前上下文，并利用缓存
        if self._parse_cache is None:
            # 解析并缓存结果
            markdown_service = self.get_markdown_service()
            self._parse_cache = markdown_service.parse(self._context)
        
        return self._parse_cache
    
    def get_meta(self) -> DocumentMeta:
        """Get metadata from current context.
        
        Returns:
            DocumentMeta: The parsed metadata
        """
        meta, _ = self.parse_markdown()
        return meta
    
    def get_headers(self) -> Iterator[HeadSection]:
        """Get headers from current context.
        
        Returns:
            Iterator[HeadSection]: The parsed headers
        """
        _, headers = self.parse_markdown()
        return headers
        
    def get_edit_session(self) -> EditSession:
        """Get or create an edit session for this task.
        
        Returns:
            EditSession: An edit session for modifying the task content
        """
        if not hasattr(self, '_edit_session') or self._edit_session is None:
            self._edit_session = EditSessionOT(self._context)
        return self._edit_session
        
    def _find_or_create_task_list(self, head_section: HeadSection) -> Tuple[bool, ListBlock]:
        """Find an existing task list or create a new one under the given header section.
        
        Args:
            head_section: The header section to search in
            
        Returns:
            Tuple[bool, ListBlock]: A tuple containing:
                - bool: True if a list was found, False if a new one was created
                - ListBlock: The found or created list block
        """
        # 检查是否已有任务列表
        lists = list(head_section.get_lists())
        if lists:
            # 返回第一个列表（通常只有一个）
            return True, lists[0]
        
        # 没有找到列表，需要创建一个新的（这部分会在调用方处理）
        return False, None
    
    def _append_task_to_list(self, task_id: str, task_msg: str, task_section_name: str, edit_session: EditSession) -> bool:
        """Append a new task to the task list in the markdown content using edit session.
        
        Args:
            task_id: The ID of the new task
            task_msg: The description of the new task
            task_section_name: The name of the task section header
            edit_session: The edit session to use for modifications
            
        Returns:
            bool: True if content was modified, False otherwise
        """
        # 确保任务消息只有一行
        assert '\n' not in task_msg, "Task message must be a single line"
        
        # 使用当前上下文解析内容
        headers = self.get_headers()
        
        # 查找任务部分
        task_section = None
        for header in headers:
            if header.text == task_section_name and header.head_level == 2:  # ## Tasks
                task_section = header
                break
        
        # 准备新任务条目
        task_entry = f"- [ ] {task_id}: {task_msg}\n"
        
        if task_section:
            # 找到了任务部分，使用 _find_or_create_task_list 获取任务列表
            found, task_list = self._find_or_create_task_list(task_section)
            
            if found:
                # 有列表，找到最后一个列表项
                list_items = list(task_list.list_items())
                
                if list_items:
                    # 有列表项，在最后一个列表项的行尾插入
                    last_item = list_items[-1]
                    _, last_item_end = last_item.text_range
                    
                    # 获取当前内容
                    # current_content = edit_session.get_content()
                    
                    # 使用 last_item_end 作为插入位置
                    # 这样可以正确处理嵌套列表的情况
                    insert_pos = last_item_end - 1
                    
                    # 在列表项结束位置插入新任务
                    edit_session.insert(insert_pos, task_entry)
                else:
                    # 列表存在但没有列表项，在列表开始处插入
                    list_start, _ = task_list.text_range
                    edit_session.insert(list_start, task_entry)
            else:
                # 没有列表，在任务部分的标题后创建新列表
                # 使用 task_section 的 text_range 属性获取标题的范围
                _, section_end = task_section.text_range
                
                # 有内容，在部分结束处插入新任务
                edit_session.insert(section_end-1, task_entry)
        else:
            # 没有找到任务部分，添加新部分
            current_content = edit_session.get_content()
            edit_session.insert(len(current_content), f"\n## {task_section_name}\n{task_entry}\n")
        
        return True
    
    def _get_tasks(self) -> List[ListItem]:
        """获取所有任务列表项及其对应的任务ID
        
        Returns:
            List[Tuple[ListItem, str]]: 列表项和任务ID的元组列表
                任务ID可能为空字符串，表示该任务没有明确的ID
        """
        # 获取任务部分名称（支持国际化）
        task_section_name = config.get("tasks.section_name", "Tasks")
        
        # 使用当前上下文解析内容
        headers = self.get_headers()
        
        # 查找任务部分
        task_section = None
        for header in headers:
            if header.text == task_section_name and header.head_level == 2:  # ## Tasks
                task_section = header
                break
        
        if not task_section:
            return []
        
        # 查找任务列表
        task_list_blocks = list(task_section.get_lists())
        if not task_list_blocks:
            return []
        
        result = []
        # 处理所有列表块中的任务项
        for list_block in task_list_blocks:
            for list_item in list_block.list_items():
                # TODO: 只处理任务类型的列表项, 在当前的实现中
                if list_item.is_task:
                    result.append(list_item)
        
        return result

    def new_sub_task(self, task_msg: str, task_prefix: Optional[str] = None) -> Optional[InlineTask]:
        """Create a new inline task as a subtask of this file task.
        
        Args:
            task_msg: Description of the task (must be a single line)
            task_prefix: Optional prefix for the task ID
            
        Returns:
            InlineTask: The newly created inline task
        """
        # 确保任务消息只有一行
        if '\n' in task_msg:
            task_msg = task_msg.split('\n')[0]
        
        # 获取任务ID
        if task_prefix is None:
            task_prefix = self.numbering_service.get_default_prefix()
        task_id = self.numbering_service.get_next_number(task_prefix)
        
        # 获取任务部分名称（支持国际化）
        task_section_name = config.get("tasks.section_name", "Tasks")
        
        # 获取编辑会话
        edit_session = self.get_edit_session()
        
        # 使用改进的 _append_task_to_list 方法添加任务
        # 该方法使用 ListItem 的 text_range 属性，避免字符串解析
        content_modified = self._append_task_to_list(task_id, task_msg, task_section_name, edit_session)
        
        # 如果内容被修改，更新上下文并保存
        if content_modified:
            # 获取更新后的内容
            updated_content = edit_session.get_content()
            
            # 更新上下文（使用setter，会自动处理缓存）
            self.context = updated_content
            
            # 重新解析，并获取 task 列表
            task_items = self._get_tasks()

            # 查找刚刚添加的任务
            for list_item in task_items:
                # 创建 InlineTask 实例
                inline_task = InlineTaskImpl(
                    self.file_service,
                    self.numbering_service,
                    self.get_edit_session(),
                    list_item
                )
                
                # 检查 task_id 是否匹配
                if inline_task.task_id == task_id:
                    return inline_task
        
        # 如果没有找到对应的列表项，创建失败
        return None
        
    def tasks(self) -> List[InlineTask]:
        """Get all subtasks of this file task.
        
        Returns:
            List[InlineTask]: List of inline tasks in this file task
        """
        task_items = self._get_tasks()
        
        result = []
        for list_item, task_id in task_items:
            # 创建InlineTask实例
            inline_task = InlineTaskImpl(
                    self.file_service,
                    self.numbering_service,
                    self.get_edit_session(),
                    list_item
            )
            result.append(inline_task)
        
        return result
    
    def delete(self, task_id: Optional[str] = None, force: bool = False) -> bool:
        """Delete this task or a subtask."""
        raise NotImplementedError("delete not implemented")
    
    def mark_as_archived(self, force: bool = False) -> bool:
        """Mark this task as archived."""
        raise NotImplementedError("mark_as_archived not implemented")
    
    def add_related_task(self, task_id: str) -> 'FileTask':
        """Add an existing task as a related task to this task."""
        raise NotImplementedError("add_related_task not implemented")
    
    def modify_task(self, task_id: Optional[str] = None, task_msg: Optional[str] = None) -> bool:
        """Update this task or a subtask."""
        raise NotImplementedError("modify_task not implemented")
    
    def tag_groups(self) -> Dict[str, Dict[str, Any]]:
        """Get the tag groups defined in this task."""
        raise NotImplementedError("tag_groups not implemented")


class FileTaskService(FileTaskImpl, TaskService):
    """Implementation of TaskService interface that uses FileService for storage."""
    
    def __init__(self, file_service: FileService, numbering_service: Optional[NumberingService] = None):
        """Initialize a FileTaskService instance.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: Optional numbering service for task IDs
        """
        # 获取任务目录配置
        self.tasks_dir = config.get("tasks.active_dir", "tasks")
        self.archived_dir = config.get("tasks.archived_dir", "archived")
        
        # 确保任务目录存在
        if not file_service.file_exists(self.tasks_dir):
            file_service.create_directory(self.tasks_dir)
        
        if not file_service.file_exists(self.archived_dir):
            file_service.create_directory(self.archived_dir)
        
        # 如果未提供编号服务，则创建一个
        if numbering_service is None:
            numbering_service = TaskNumberingService(file_service)
        
        # 从numbering service获取默认前缀
        default_prefix = numbering_service.get_default_prefix()
        task_id = f"{default_prefix}-000"
        
        # 检查根任务文件是否存在
        root_task_path = os.path.join(self.tasks_dir, f"{task_id}.md")
        if file_service.file_exists(root_task_path):
            # 如果存在，读取其内容
            context = file_service.read_file(root_task_path)
        else:
            # 否则使用默认模板
            context = FILE_TASK_TEMPLATE.format(name="Root Task", description="")
        
        # 初始化基类
        super().__init__(file_service, numbering_service, task_id, context)
    
    def new_task(self, task_msg: str, task_prefix: Optional[str] = None) -> FileTask:
        """Create a new file task.
        
        This implementation overrides the standard FileTask.new_task method to return
        a FileTask instead of an InlineTask.
        
        Args:
            task_msg: Description of the task
            task_prefix: Optional prefix for the task ID
            
        Returns:
            FileTask: The newly created file task
        """
        # 1. 获取任务ID
        if task_prefix is None:
            task_prefix = self.numbering_service.get_default_prefix()
            
        task_id = self.numbering_service.get_next_number(task_prefix)
        
        # 2. 直接使用 self 作为根任务实例添加内联任务
        # 使用 new_sub_task 方法添加子任务
        inline_task = self.new_sub_task(task_msg, task_prefix)
        
        # 如果内联任务创建失败，返回 None
        if inline_task is None:
            return None
        
        # 3. 创建任务内容
        task_content = FILE_TASK_TEMPLATE.format(
            name=task_msg.split('\n')[0] if '\n' in task_msg else task_msg,
            description=task_msg if '\n' in task_msg else ""
        )
        
        # 4. 使用文件服务创建新任务文件
        task_path = os.path.join(self.tasks_dir, f"{task_id}.md")
        
        # 创建新任务文件
        self.file_service.write_file(task_path, task_content)
        
        # 5. 创建并返回新的 FileTask 实例
        return FileTaskImpl(self.file_service, self.numbering_service, task_id, task_content)

    def list_tasks(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """List all tasks managed by this service."""
        raise NotImplementedError("list_tasks not implemented")
    
    def get_task(self, task_id: str) -> Optional[FileTask]:
        """Get a specific task by ID."""
        raise NotImplementedError("get_task not implemented")
    
    def archive_task(self, task_id: str) -> bool:
        """Archive a task."""
        raise NotImplementedError("archive_task not implemented")
    
    def delete_archived_task(self, task_id: Optional[str] = None) -> int:
        """Delete archived tasks."""
        raise NotImplementedError("delete_archived_task not implemented")


# Alias for backward compatibility
FileProjectService = FileTaskService
