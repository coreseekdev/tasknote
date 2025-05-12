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

class TaskBase:
    """Base class for task implementations with shared domain knowledge."""
    
    def __init__(self, file_service: FileService, numbering_service: NumberingService):
        """Initialize TaskBase with common services and configuration.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: The numbering service to use for generating task IDs
        """
        self.file_service = file_service
        self.numbering_service = numbering_service
        
        # 获取任务目录配置
        self.tasks_dir = config.get("tasks.active_dir", "tasks")
        self.archived_dir = config.get("tasks.archived_dir", "archived")


class InlineTaskImpl(TaskBase, InlineTask):
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
        
        # 初始化基类
        TaskBase.__init__(self, file_service, numbering_service)
        InlineTask.__init__(self)  # 如果 InlineTask 有初始化方法
        
        self._edit_session = edit_session
        self.list_item = list_item
        
        # Parse the list item text to extract task ID, link, and text
        parsed_result = parse_task_inline_string(list_item.text)
        self._task_id = parsed_result.get('task_id', None) or "task_id"
        self._task_link = parsed_result.get('link', None)
        self._task_message = parsed_result.get('text', list_item.text)
        
        # 缓存相关的 FileTask
        self._related_file_task_cache = None
    
    @property
    def task_id(self) -> str:
        """Get the task ID."""
        return self._task_id
    
    @property
    def task_message(self) -> str:
        """获取任务消息内容"""
        return self._task_message
        
    def _find_task_file_path(self, task_id: str) -> Optional[str]:
        """查找任务文件路径
        
        检查活动目录和归档目录，返回找到的文件路径或 None
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: 找到的文件路径，如果都不存在则返回 None
        """
        file_name = f"{task_id}.md"
        
        # 首先检查活动目录
        active_task_path = os.path.join(self.tasks_dir, file_name)
        if self.file_service.file_exists(active_task_path):
            return active_task_path
            
        # 然后检查归档目录
        archived_task_path = os.path.join(self.archived_dir, file_name)
        if self.file_service.file_exists(archived_task_path):
            return archived_task_path
            
        # 都不存在则返回 None
        return None

    def convert_task(self) -> FileTask:
        """Convert this inline task to a file task.
        
        如果当前任务已经有关联的 FileTask，则直接返回该 FileTask。
        否则，创建一个新的 FileTask 并将当前任务文本替换为链接形式。
        
        Returns:
            FileTask: 关联的文件任务
            
        Raises:
            NotImplementedError: 如果无法转换任务
        """
        # 1. 如果已有关联的 FileTask，直接返回
        related_task = self.get_related_file_task()
        if related_task:        # 如果返回 None 说明没有关联的 file task
            return related_task
        
        # 2. 创建新的 FileTask
        # 使用当前任务 ID 作为文件名
        file_name = f"{self._task_id}.md"
        # 检查文件是否已存在
        existing_path = self._find_task_file_path(self._task_id)
        if existing_path:
            # 如果文件已经存在，说明其他关联的 task 已经做了准备，此时不需要创建，直接关联即可
            raise NotImplementedError(f"FileTask already exists: {file_name}")
            
        # 文件不存在，创建新路径
        task_path = os.path.join(self.tasks_dir, file_name)
        
        # 创建任务内容
        task_content = FILE_TASK_TEMPLATE.format(
            name=self._task_message,
            description= ""     # 目前的实现中 description 默认为 空
        )
        
        # 不应该写入文件，实际写入的工作由上层 调用 file task 完成
        
        # 3. 替换当前任务文本为链接形式
        # 获取当前任务的文本范围
        start_pos, end_pos = self.list_item.inline_item_text_range
        
        # 创建新的任务文本
        # 注意：inline_item_text_range 不包括 Markdown 列表项的前缀部分（即 "- [ ]"）
        # 因此，我们不需要在新文本中包含复选框，只需要包含任务 ID 和链接
        new_text = f"[{self._task_id}]({file_name}): {self._task_message}"
        
        # 使用编辑会话修改文本
        # 注意：这里可能需要更精确的位置计算，目前只是简单替换
        self._edit_session.replace(start_pos, end_pos, new_text)
        
        # 创建并返回 FileTask 实例
        file_task = FileTaskImpl(self.file_service, self.numbering_service, self._task_id, task_content)
        self._related_file_task_cache = file_task
        
        return file_task

    def get_related_file_task(self) -> Optional['FileTask']:
        """
        返回当前 inline task 关联的 FileTask

        NOTE: 当 Task 使用 link 的形式表示时，链接的 target 就是 FileTask
        
        规则：
        1. 只有形如 filename.md 的 link 才是有效的 filetask link，不能包括任何路径
        2. 需要同时检测活动目录和归档目录，确定文件的具体路径
        
        Returns:
            FileTask: 关联的文件任务
            
        Raises:
            NotImplementedError: 如果链接无效或文件不存在
        """
        # 如果已有缓存，直接返回
        if self._related_file_task_cache is not None:
            return self._related_file_task_cache
            
        # 如果没有链接，返回 None
        if not self._task_link:
            return None
            
        # 从链接中提取文件名
        file_name = os.path.basename(self._task_link)

        # 检查是否包含路径
        if self._task_link != file_name:
            raise NotImplementedError(f"Invalid FileTask link: {self._task_link}. Link cannot contain path.")
        
        # 检查是否是绝对链接或锐点
        if self._task_link.startswith('/') or self._task_link.startswith('#'):
            raise NotImplementedError(f"Invalid FileTask link: {self._task_link}. Link cannot be absolute or anchor.")
        
        # 必须带文件名没有扩展名，添加 .md 扩展名
        if not file_name.endswith('.md'):
            file_name += '.md'

        # 移除扩展名以获取任务 ID , 理论上应该与 当前 task 一致
        task_id = os.path.splitext(file_name)[0]

        if task_id != self._task_id:
            raise NotImplementedError(f"Inconsistent task ID: link points to {task_id}, but current task ID is {self._task_id}")
        
        # 使用辅助方法查找文件路径
        task_path = self._find_task_file_path(task_id)
        if not task_path:
            # 如果没有找到文件，抛出异常
            raise NotImplementedError(f"FileTask not found: {file_name}. The task may have been deleted.")
        
        # 读取任务文件内容
        task_content = self.file_service.read_file(task_path)
        
        # 创建 FileTask 实例并缓存
        self._related_file_task_cache = FileTaskImpl(self.file_service, self.numbering_service, task_id, task_content)
        
        return self._related_file_task_cache

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


class FileTaskImpl(TaskBase, FileTask):
    """Implementation of FileTask interface."""
    
    def __init__(self, file_service: FileService, numbering_service: NumberingService,
                 task_id: str, context: str):
        """Initialize a FileTaskImpl instance.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: The numbering service to use for generating task IDs
            task_id: ID of the task
            context: The content of the task file
        """
        # 初始化基类
        TaskBase.__init__(self, file_service, numbering_service)
        FileTask.__init__(self, file_service, numbering_service, task_id, context)
        
        self._task_id = task_id
        self._context = context
        self._headers_cache = None
    
    @property
    def task_id(self) -> str:
        """Get the task ID."""
        return self._task_id
    
    @property
    def task_message(self) -> str:
        """Get the task single line message.
        
        返回第一个 level 1 的标题文本。如果没有 level 1 标题，则返回空字符串。
        """
        
        # 查找第一个 level 1 的标题
        for header in self.get_headers():
            if header.level == 1:  # level 1 对应 # 标题
                return header.text
        
        # 如果没有 level 1 标题，返回空字符串
        return ""
    
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
    
    def mark_as_done(self) -> bool:
        """Mark the task as done."""
        # 简单实现，仅用于测试
        return True
    
    def mark_as_undone(self) -> bool:
        """Mark the task as not done."""
        # 简单实现，仅用于测试
        return True
    
    def tags(self, new_tags: Optional[List[str]] = None) -> List[str]:
        """Get or replace the list of tags associated with this task."""
        # 简单实现，仅用于测试
        return []

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


class FileTaskService(TaskBase):
    """Task service implementation.
    
    This service manages tasks stored in files.
    
    提供事务支持，可以将多个任务操作合并为一次提交。
    使用方式：
    ```python
    with task_service.transaction("提交消息") as tx:
        task1 = tx.new_task("任务1")
        task2 = tx.new_task("任务2")
        # 所有操作将在 with 块结束时一起提交
    ```
    """
    
    def __init__(self, file_service: FileService, numbering_service: Optional[NumberingService] = None):
        """Initialize a FileTaskService instance.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: Optional numbering service for task IDs
        """
        # 如果未提供编号服务，则创建一个
        if numbering_service is None:
            numbering_service = TaskNumberingService(file_service)
        
        # 初始化基类，它会设置 file_service、numbering_service 和目录配置
        super().__init__(file_service, numbering_service)
        
        # 确保任务目录存在
        if not file_service.file_exists(self.tasks_dir):
            file_service.create_directory(self.tasks_dir)
        
        if not file_service.file_exists(self.archived_dir):
            file_service.create_directory(self.archived_dir)
        
        # 从 numbering service 获取默认前缀
        default_prefix = numbering_service.get_default_prefix()
        task_id = f"{default_prefix}-000"
        
        # 检查根任务文件是否存在
        root_task_path = os.path.join(self.tasks_dir, f"{task_id}.md")
        if file_service.file_exists(root_task_path):
            # 如果存在，读取其内容
            context = file_service.read_file(root_task_path)
        else:
            # 否则使用默认模板
            root_task_name = config.get("tasks.root_task_name", "Root Task")
            context = FILE_TASK_TEMPLATE.format(name=root_task_name, description="")
        
        # 创建根任务实例
        self.root_task = FileTaskImpl(file_service, numbering_service, task_id, context)
    
    def new_task(self, task_msg: str, task_prefix: Optional[str] = None) -> FileTask:
        """Create a new file task.
        
        Args:
            task_msg: Description of the task
            task_prefix: Optional prefix for the task ID
            
        Returns:
            FileTask: The newly created file task
        """
        # 1. 使用根任务实例添加内联任务
        # 使用 new_sub_task 方法添加子任务
        inline_task = self.root_task.new_sub_task(task_msg, task_prefix)
        
        # 如果内联任务创建失败，返回 None
        if inline_task is None:
            return None
        
        # 2. 使用 convert_task 方法将内联任务转换为文件任务
        # 这样可以统一任务创建的逻辑，确保所有任务都通过相同的方式创建
        file_task = inline_task.convert_task()
        
        return file_task

    def transaction(self, commit_message: str = "") -> 'TaskTransaction':
        """创建一个新的任务事务。
        
        Args:
            commit_message: 提交消息
            
        Returns:
            TaskTransaction: 新创建的事务对象
        """
        return TaskTransaction(self, commit_message)
    
    def list_tasks(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """List all tasks managed by this service."""
        raise NotImplementedError("list_tasks not implemented")
    
    def get_task(self, task_id: str) -> Optional[FileTask]:
        """Get a specific task by ID."""
        raise NotImplementedError("get_task not implemented")


class TaskTransaction:
    """任务事务类，用于支持批量操作任务。
    
    该类实现了上下文管理器协议，可以在 with 语句中使用。
    所有在事务中执行的操作将在事务结束时一次性提交。
    
    使用示例：
    ```python
    with task_service.transaction("批量创建任务") as tx:
        task1 = tx.new_task("任务1")
        task2 = tx.new_task("任务2")
        # 所有操作将在 with 块结束时一起提交
    ```
    """
    
    def __init__(self, task_service: FileTaskService, commit_message: str = ""):
        """初始化任务事务。
        
        Args:
            task_service: 任务服务实例
            commit_message: 提交消息
        """
        self.task_service = task_service
        self.commit_message = commit_message
        self.file_transaction = None  # 将在 __enter__ 中初始化
    
    def __enter__(self) -> 'TaskTransaction':
        """进入事务上下文。
        
        创建一个文件服务事务，所有文件操作将在事务中执行。
        
        Returns:
            TaskTransaction: 事务对象自身
        """
        # 创建文件服务事务
        self.file_transaction = self.task_service.file_service.transaction(self.commit_message)
        self.file_transaction.__enter__()
        
        # 替换任务服务中的文件服务，使其使用事务中的文件服务
        self._original_file_service = self.task_service.file_service
        self.task_service.file_service = self.file_transaction
        
        # 同时替换根任务中的文件服务
        self._original_root_task_file_service = self.task_service.root_task.file_service
        self.task_service.root_task.file_service = self.file_transaction
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """退出事务上下文。
        
        如果没有异常发生，提交所有更改；否则回滚更改。
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯
            
        Returns:
            bool: 是否抑制异常
        """
        # 恢复原始文件服务
        self.task_service.file_service = self._original_file_service
        
        # 恢复根任务的文件服务
        self.task_service.root_task.file_service = self._original_root_task_file_service
        
        # 退出文件服务事务
        result = self.file_transaction.__exit__(exc_type, exc_val, exc_tb)
        self.file_transaction = None
        
        return result
    
    def new_task(self, task_msg: str, task_prefix: Optional[str] = None) -> FileTask:
        """在事务中创建新任务。
        
        Args:
            task_msg: 任务描述
            task_prefix: 可选的任务前缀
            
        Returns:
            FileTask: 新创建的文件任务
        """
        return self.task_service.new_task(task_msg, task_prefix)
    
    def archive_task(self, task_id: str) -> bool:
        """Archive a task."""
        raise NotImplementedError("archive_task not implemented")
    
    def delete_archived_task(self, task_id: Optional[str] = None) -> int:
        """Delete archived tasks."""
        raise NotImplementedError("delete_archived_task not implemented")


# Alias for backward compatibility
FileProjectService = FileTaskService
