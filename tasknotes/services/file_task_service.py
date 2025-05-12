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
            task_id: ID of the task
            task_msg: Description of the task
            parent_task: The parent FileTask that contains this InlineTask
            list_item: The ListItem object representing this task in the markdown
        """
        self._task_id = "task_id"
        self.file_service = file_service
        self.numbering_service = numbering_service
        self._edit_session = edit_session
        self.list_item = list_item
    
    @property
    def task_id(self) -> str:
        """Get the task ID."""
        return self._task_id
    
    @property
    def task_message(self) -> str:
        """获取任务ID"""
        return self._task_id

    def convert_task(self) -> FileTask:
        """Convert this inline task to a file task."""
        raise NotImplementedError("convert_task not implemented")
        
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
                    result.append((list_item, task_id))
        
        return result

    def _parse_task_id(self, text: str) -> str:
        """从任务文本中解析任务ID
        
        支持以下格式:
        - "task" (无ID，返回空字符串)
        - "`TASK-xxx`yyyyy" (返回 "TASK-xxx")
        - "[`TASK-xxx`yyyyy](Task-xxx.md)" (返回 "TASK-xxx")
        - "TASK-xxx: yyyyy" (返回 "TASK-xxx")
        
        Args:
            text: 任务文本
        
        Returns:
            str: 解析出的任务ID，如果没有ID则返回空字符串
        """
        # 尝试匹配 TASK-xxx: 格式 (最常见的格式)
        prefix_pattern = r'([A-Z]+-\d+):'
        prefix_match = re.search(prefix_pattern, text)
        if prefix_match:
            return prefix_match.group(1)
            
        # 尝试匹配 `TASK-xxx` 格式
        backtick_pattern = r'`([A-Z]+-\d+)`'
        backtick_match = re.search(backtick_pattern, text)
        if backtick_match:
            return backtick_match.group(1)
        
        # 尝试匹配 [`TASK-xxx`](Task-xxx.md) 格式
        link_pattern = r'\[`([A-Z]+-\d+)`.*?\]\(.*?\)'
        link_match = re.search(link_pattern, text)
        if link_match:
            return link_match.group(1)
        
        # 没有找到任务ID
        return ''

    def _extract_task_msg(self, text: str, task_id: str) -> str:
        """从任务文本中提取任务消息
        
        Args:
            text: 任务文本
            task_id: 任务ID
        
        Returns:
            str: 提取出的任务消息
        """
        if not task_id:
            # 没有任务ID，整个文本都是任务消息
            return text.strip()
        
        # 移除任务ID及其格式化部分
        # 处理 `TASK-xxx` 格式
        msg = re.sub(r'`' + re.escape(task_id) + r'`\s*', '', text)
        # 处理 [`TASK-xxx`](link) 格式
        msg = re.sub(r'\[`' + re.escape(task_id) + r'`.*?\]\(.*?\)\s*', '', msg)
        # 处理 TASK-xxx: 格式
        msg = re.sub(re.escape(task_id) + r':\s*', '', msg)
        
        return msg.strip()

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
            print("------", task_items, task_id)

            # 查找刚刚添加的任务
            for list_item, item_task_id in task_items:
                if item_task_id == task_id:
                    # 创建并返回 InlineTask 实例，包含对应的 ListItem
                    return InlineTaskImpl(
                        self.file_service,
                        self.numbering_service,
                        self.get_edit_session(),
                        list_item
                    )
        
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
            # 从列表项中提取任务消息
            task_msg = self._extract_task_msg(list_item.text, task_id)
            
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
    
    def convert_task(self, task_id: str) -> 'FileTask':
        """Convert a subtask to a file task."""
        raise NotImplementedError("convert_task not implemented")
    
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
        # 1. 调用 FileTaskImpl 的 new_sub_task 方法创建一个 InlineTask
        # 首先，我们需要在根任务(TASK-000)中添加一个内联任务
        
        # 获取任务ID
        if task_prefix is None:
            task_prefix = self.numbering_service.get_default_prefix()
            
        task_id = self.numbering_service.get_next_number(task_prefix)
        
        # 修改根任务文件，在 # Tasks 部分添加新任务
        root_task_path = os.path.join(self.tasks_dir, f"{self.task_id}.md")
        root_content = self.file_service.read_file(root_task_path)
        
        # 找到 ## Tasks 部分并添加新任务
        task_section_pattern = r"(## Tasks\s*\n)"
        # 使用r前缀创建原始字符串，避免反斜杠问题
        newline = "\n"
        task_entry = f"- [ ] {task_id}: {task_msg.split(newline)[0] if newline in task_msg else task_msg}{newline}"
        
        if re.search(task_section_pattern, root_content):
            updated_content = re.sub(task_section_pattern, f"\g<1>{task_entry}", root_content)
        else:
            # 如果找不到 Tasks 部分，添加一个
            updated_content = root_content + f"\n## Tasks\n{task_entry}"
        
        # 2. 创建 InlineTask 实例
        inline_task = InlineTaskImpl(self.file_service, task_id, self)
        
        # 3. 调用 convert_task 将 InlineTask 转换为 FileTask
        # 由于我们需要自己实现转换逻辑，我们将直接创建文件任务
        
        # 创建任务内容
        task_content = FILE_TASK_TEMPLATE.format(
            name=task_msg.split('\n')[0] if '\n' in task_msg else task_msg,
            description=task_msg if '\n' in task_msg else ""
        )
        
        # 4. 使用文件服务创建新任务文件
        task_path = os.path.join(self.tasks_dir, f"{task_id}.md")
        
        # 使用事务更新两个文件
        try:
            # 开始事务
            self.file_service.begin_transaction()
            
            # 更新根任务文件
            self.file_service.write_file(root_task_path, updated_content)
            
            # 创建新任务文件
            self.file_service.write_file(task_path, task_content)
            
            # 提交事务
            self.file_service.commit_transaction()
        except Exception as e:
            # 回滚事务
            self.file_service.rollback_transaction()
            raise e
        
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
