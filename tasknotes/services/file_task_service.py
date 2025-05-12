"""File-based task service implementation for TaskNotes.

This module provides concrete implementations of the Task, InlineTask, FileTask,
and TaskService interfaces defined in the task module.

Implements the Protocol-based interfaces with a clear separation between read-only
and mutable operations, and supports transaction-based operations.
"""

import os
import time
import re
from tkinter import N
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Iterator, cast

from tasknotes.interface.file_service import FileService
from tasknotes.interface.numbering_service import NumberingService
from tasknotes.interface.task import (
    Task, TaskMut, 
    InlineTask, InlineTaskMut, 
    FileTask, FileTaskMut, 
    TaskService, TaskTransaction as TaskTransactionProtocol
)
from tasknotes.interface.markdown_service import MarkdownService, HeadSection, ListBlock, ListItem, DocumentMeta
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
        
        # 初始化编辑状态相关属性
        self._creation_edit_count = 0  # 创建时的编辑计数
        self._edit_session = None  # 关联的编辑会话

    def find_task_file_path(self, task_file: str) -> Optional[str]:
        """查找任务文件路径
        
        检查活动目录和归档目录，返回找到的文件路径或 None

        Args:
            task_file: 预期的 file task 文件名
            
        Returns:
            str: 找到的文件路径，如果都不存在则返回 None
        """
        # file_name = ta# f"{task_id}.md"
        
        # 首先检查活动目录
        active_task_path = os.path.join(self.tasks_dir, task_file)
        if self.file_service.file_exists(active_task_path):
            return active_task_path
            
        # 然后检查归档目录
        archived_task_path = os.path.join(self.archived_dir, task_file)
        if self.file_service.file_exists(archived_task_path):
            return archived_task_path
            
        # 都不存在则返回 None
        return None

class InlineTaskImpl(TaskBase):
    """Implementation of InlineTask and InlineTaskMut interfaces."""
    
    def __init__(self, file_service: FileService, numbering_service: NumberingService, 
                 edit_session: EditSession, list_item: ListItem):
        """Initialize InlineTaskImpl.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: The numbering service to use for generating task IDs
            edit_session: The edit session for the parent task
            list_item: The list item representing this task
        """
        super().__init__(file_service, numbering_service)
        # 设置编辑会话并记录当前编辑计数
        self._edit_session = None
        self._creation_edit_count = 0
        self._set_edit_session(edit_session)
        self.list_item = list_item
        
        # 解析列表项文本，提取任务ID和消息
        parsed_result = self._parse_list_item_text(list_item.text)
        self._task_id = parsed_result.get('task_id', None) or "task_id"
        self._task_link = parsed_result.get('link', None)
        self._task_message = parsed_result.get('text', list_item.text)

        # list_item 中并没有 [ ] 或 [X] 
        self._is_done = False
        if list_item.is_task:
            # 当 is_task 时， is_completed_task 永不为 None
            self._is_done = list_item.is_completed_task 
        
        # 缓存相关的 FileTask, 对于 "真正的"(task 不是 link 的 ) Inline Task 永远为 None
        self._related_file_task_cache = None
    
    @property
    def task_id(self) -> str:
        """Get the task ID."""
        # task_id 即使在过期状态下也可以访问
        return self._task_id
    
    @property
    def task_message(self) -> str:
        """获取任务消息内容"""
        if self.is_outofdate():
            raise ValueError("Task is out of date, only task_id is accessible")
        return self._task_message
    
    @property
    def edit_status(self) -> TaskEditStatus:
        """获取任务编辑状态"""
        if not self._edit_session:
            return TaskEditStatus.CLEAN
            
        if self._edit_session.edit_count > self._creation_edit_count:
            return TaskEditStatus.OUTOFDATE
            
        return TaskEditStatus.CLEAN
        
    def is_outofdate(self) -> bool:
        """检查任务是否过期"""
        return self.edit_status == TaskEditStatus.OUTOFDATE

    def _set_edit_session(self, edit_session: Optional[EditSession]) -> None:
        """设置关联的编辑会话并记录当前编辑计数"""
        self._edit_session = edit_session
        if edit_session:
            self._creation_edit_count = edit_session.edit_count

    def get_related_file_task(self) -> Optional['FileTask']:
        """
        返回当前内联任务关联的 FileTask，如果存在。
        
        当任务使用链接形式表示时，链接的目标就是 FileTask。
        
        规则：
        1. 如果 list_item.text 包含 markdown 链接，则链接的 target 就是 FileTask 的 ID
        2. 如果 list_item.text 不包含链接，则返回 None
        
        Returns:
            Optional[FileTask]: 关联的文件任务，如果不存在则为 None
            
        Raises:
            NotImplementedError: 如果链接无效或文件不存在
            ValueError: 如果任务已过期
        """
        # 检查任务是否过期
        if self.is_outofdate():
            raise ValueError("Task is out of date, only task_id is accessible")
            
        # 如果已经有缓存，直接返回
        if self._related_file_task_cache:
            return self._related_file_task_cache
            
        # 如果没有链接，返回 None
        if not self._task_link:
            return None
            
        # 查找任务文件, 此处默认 link 中已经存在扩展名 .md
        file_path = self.find_task_file_path(self._task_link)
        
        if not file_path:
            # 如果删除的不完整可能导致这个异常， 后续日志系统接入后，应转为日志
            raise NotImplementedError(f"Task file {self._task_link} not found")
            # return None 
            
        # 读取文件内容
        content = self.file_service.read_file(file_path)
        
        # 检查 链接记录的 task_id 与 当前任务记录的是否一致
        task_id = os.path.basename(self._task_link)
        if task_id != self.task_id:
            # 日志系统接入后，改为记录日志
            raise NotImplementedError(f"Inconsistent task ID: link points to {task_id}, but current task ID is {self._task_id}")
            # return None

        # 创建 FileTask 对象 并 缓存
        self._related_file_task_cache = FileTaskImpl(
            file_service=self.file_service,
            numbering_service=self.numbering_service,
            task_id=self.task_id,
            context=content
        )

        return self._related_file_task_cache

    def as_mutable(self) -> 'InlineTaskMut':
        """获取此任务的可变版本"""
        return cast(InlineTaskMut, self)

    # 以下为 InlineTaskMut 的接口

    def convert_task(self) -> 'FileTask':
        """Convert this inline task to a file task.
        
        如果当前任务已经有关联的 FileTask，则直接返回该 FileTask。
        否则，创建一个新的 FileTask 并将当前任务文本替换为链接形式。
        
        Returns:
            FileTask: 关联的文件任务
            
        Raises:
            NotImplementedError: 如果无法转换任务
            ValueError: 如果任务已过期
        """
        # 检查任务是否过期
        if self.is_outofdate():
            raise ValueError("Cannot convert an out-of-date task")
            
        # 1. 检查是否已经有关联的 FileTask
        related_task = self.get_related_file_task()
        if related_task:
            return related_task
            
        # 2. 如果没有，创建一个新的 FileTask
        # 2.1 检查是否已经存在同名的
        file_path = self.find_task_file_path(task_id)
        if file_path:
            # 2.2 已经存在同名文件, 读取文件内容
            # 此种情况，同一个 task 作为多个 task 的 sub-task , 之前已经转为 file-task 但是未及时更新
            content = self.file_service.read_file(file_path)
        else:
            # 2.2 需要创建新的，默认在 tasks 下，即作为 active task
            file_name = f"{self.task_id}.md"
            file_path = os.path.join(self.tasks_dir, file_name)
        
            # 2.3 使用模板创建文件内容
            content = FILE_TASK_TEMPLATE.format(
                name=self.task_message,
                description=""
            )
        
        # 2.3 不直接写入文件，由上层调用者负责
        # 文件路径保存在 file_task 对象中
        
        # 2.4 创建 FileTask 对象, 并主动设置文件名
        file_task = FileTaskImpl(
            file_service=self.file_service,
            numbering_service=self.numbering_service,
            task_id=task_id,
            context=content
        ).set_filename(file_path)
        
        # 3. 更新当前任务文本，添加链接
        new_text = f"[{task_id}]({task_id}.md): {self.task_message}"
        start_pos, end_pos = self.list_item.inline_item_text_range
        # 编辑操作 会自动调用 apply ，即 更新 edit_coutn
        self._edit_session.replace(start_pos, end_pos, new_text)
        
        # 4. 更新缓存， 其实不必要，此时已经 out of date
        self._task_link = f"{self.task_id}.md"
        self._related_file_task_cache = file_task
        
        return file_task

    def _change_task_marker(self, target_marker:str , new_marker: str) -> bool:
        assert len(new_marker) == len(target_marker)
        # 获取任务文本范围
        text_range_begin, _ = self.list_item.text_range
        inline_begin, _ = self.list_item.inline_item_text_range
        
        # 获取完整的任务文本（包括标记）
        marker_text = self.list_item.text[:inline_begin-text_range_begin]
        
        # 替换标记部分，将 [ ] 替换为 [x]
        if target_marker in marker_text:
            marker_text = marker_text.replace(target_marker, new_marker, 1)
            # 直接替换编辑会话中的内容
            self._edit_session.replace(text_range_begin, inline_begin, marker_text)
            return True
        return False

    def mark_as_done(self) -> bool:
        """将任务标记为已完成。"""

        # 注意： 目前的实现 不考虑 级联标记完成， 不考虑额外修改 file task
        # 如果需要 同步更新，需要发送新的通知。当前版本先保证基本功能可用

        # 检查任务是否过期
        if self.is_outofdate():
            raise ValueError("Cannot modify an out-of-date task")
        
        # 检查当前状态，如果已经是完成状态，不需要修改
        if self._is_done:
            return True
        
        if self._change_task_marker("[ ]", "[X]"):            
            # 更新任务状态
            self._is_done = True
            return True
        
        return False
    
    def mark_as_undone(self) -> bool:
        """将任务标记为未完成。"""
        # 检查任务是否过期
        if self.is_outofdate():
            raise ValueError("Cannot modify an out-of-date task")
        
        # 检查当前状态，如果已经是完成状态，不需要修改
        if self._is_done == False:
            return True
        
        if self._change_task_marker("[X]", "[ ]"):            
            # 更新任务状态
            self._is_done = False
            return True
        
        return False
    
    def delete(self, force: bool = False) -> bool:
        """删除任务。"""
        # 检查任务是否过期
        if self.is_outofdate():
            raise ValueError("Cannot modify an out-of-date task")
        
        # 在当前的处理中，简单的从 文件删除对应的 Task 文本
        # 1. task file 可能出现在多个子列表中，不能立即删除
        # 2. 后续的处理中，考虑先广播一遍删除请求，以便其他 task 可以取消掉
        text_begin, text_end  = self.list_item.text_range
        self._edit_session.replace(text_begin, text_end, "")
        return True

    def modify_task(self, task_msg: str) -> bool:
        """更新任务描述或标题。"""
        # 检查任务是否过期
        if self.is_outofdate():
            raise ValueError("Cannot modify an out-of-date task")

        # 获取任务文本范围
        inline_begin, inline_end = self.list_item.inline_item_text_range
        
        # 构造新的任务文本
        if self._task_link:
            # 如果有链接，保留链接格式
            new_text = f"[{self.task_id}]({self._task_link}): {task_msg}"
        else:
            # 如果没有链接，保留 task_id
            new_text = f"{self.task_id}: {task_msg}"
        
        if new_text != self.list_item.text:
            # 替换内联文本部分，保留标记部分
            self._edit_session.replace(inline_begin, inline_end, new_text)
            return False # 此处的返回值语义不清晰，应该是没有改变，而非改变失败
        
        # 更新任务消息
        self._task_message = task_msg
        
        return True
    
    def get_tags(self) -> List[str]:
        """获取与此任务关联的标签列表。"""
        tags = []
        
        # 检查任务是否过期
        if self.is_outofdate():
            raise ValueError("Cannot modify an out-of-date task")

        # 获取嵌套列表
        nested_lists = list(self.list_item.get_lists())
        if not nested_lists or len(nested_lists) == 0:
            # [不实现] 如果没有嵌套列表，则从任务消息中提取标签
            # 不能将 tag nested 在 task_message 中，这导致修改异常复杂
            # 可以配置选项， tag 是否附加显示在 任务中
            # 如果是看板视图，可以在 task-id 后显示部分 tag 
            return tags   # 即 tag 为空
        
        # 使用第一个嵌套列表中的所有条目作为标签
        first_list = nested_lists[0]
        for tag_item in first_list.list_items():
            # 每个列表项的文本就是一个标签
            tag_text = tag_item.text.strip()
            if tag_text:
                # 移除可能的 '#' 前缀
                if tag_text.startswith('#'):
                    tag_text = tag_text[1:].strip()
                tags.append(tag_text)
        
        return tags
    
    def set_tags(self, tags: List[str]) -> bool:
        """设置与此任务关联的标签列表。"""
        # 检查任务是否过期
        if self.is_outofdate():
            raise ValueError("Cannot modify an out-of-date task")
        
        # 获取当前的 tags
        current_tags = self.get_tags()
        current_tags_set = set(current_tags)
        new_tags_set = set(tags)
        
        # 如果标签没有变化，直接返回
        if current_tags_set == new_tags_set:
            return True

        # 获取嵌套列表
        nested_lists = list(self.list_item.get_lists())
        
        # 获取任务文本范围
        text_range_begin, text_range_end = self.list_item.text_range
        
        # 获取当前行的缩进前缀
        current_content = self._edit_session.current_content
        line_start = current_content.rfind('\n', 0, text_range_begin) + 1
        prefix = current_content[line_start:text_range_begin]
        # 不必 额外加工 preifx ，这个就是 list item - 之前的空格（prefix)
        
        # 子列表的缩进前缀应该比父列表多一级
        sub_list_prefix = prefix + "  "
        
        if not nested_lists or len(nested_lists) == 0:
            # 目前不存在嵌套列表，需要创建一个
            if not tags or len(tags) == 0:
                # 如果没有标签要设置，直接返回
                return True
                
            # 构造标签列表内容
            tag_list_content = "\n"
            for tag in tags:
                tag_list_content += f"{sub_list_prefix}- {tag}\n"
            
            # 在任务文本结束后插入标签列表
            self._edit_session.insert(text_range_end-1, tag_list_content)
            
        else:
            # 已经存在嵌套列表，更新它
            tag_list = nested_lists[0]
            list_range_begin, list_range_end = tag_list.text_range
            
            # 获取标签列表的缩进前缀
            list_line_start = current_content.rfind('\n', 0, list_range_begin) + 1
            list_prefix = current_content[list_line_start:list_range_begin]

            # 构造新的标签列表内容
            new_list_content = ""
            for tag in tags:
                new_list_content += f"{list_prefix}- {tag}\n"
            
            # 如果没有标签，则删除整个列表
            if not tags or len(tags) == 0:
                # 删除列表，包括可能的前导空行
                list_start = current_content.rfind('\n', 0, list_range_begin)
                if list_start != -1:
                    list_range_begin = list_start
                self._edit_session.replace(list_range_begin, list_range_end, "")
            else:
                # 替换整个列表内容，去除最后一个\n以避免多余的空行
                if new_list_content.endswith('\n'):
                    new_list_content = new_list_content[:-1]
                self._edit_session.replace(list_range_begin, list_range_end, new_list_content)
        
        return True


class FileTaskImpl(TaskBase):
    """实现 FileTask 和 FileTaskMut 接口。"""
    
    def __init__(self, file_service: FileService, numbering_service: NumberingService, 
                 task_id: str, context: str, edit_session: Optional[EditSession] = None):
        """Initialize a FileTaskImpl instance.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: The numbering service to use for generating task IDs
            task_id: The ID of this task
            context: The full markdown content of the task file
            edit_session: Optional edit session for the task content
        """
        super().__init__(file_service, numbering_service)

        self._task_id = task_id
        self._context = context
        self._parse_cache = None
        self._is_archived = False
        
        # 文件名，对于新建的文件，不同通过文件系统检测来判断，需要主动设置
        self._task_file = None
        
        # 设置编辑会话并记录当前编辑计数, 如果此时为 None ，会在 get_edit_session 时自动创建
        # 新创建的 edit_session edit_count 默认为 0
        self._edit_session = None
        self._creation_edit_count = 0
        self._set_edit_session(edit_session)
        
        # 检查任务是否已归档
        file_name = f"{task_id}.md"
        archived_path = os.path.join(self.archived_dir, file_name)
        if self.file_service.file_exists(archived_path):
            self._is_archived = True
    
    @property
    def task_id(self) -> str:
        """Get the task ID."""
        # task_id 即使在过期状态下也可以访问
        return self._task_id
    
    @property
    def context(self) -> str:
        """Get the full context of the task."""
        if self.is_outofdate():
            raise ValueError("Task is out of date, only task_id is accessible")
        return self._context
    
    @property
    def task_message(self) -> str:
        """Get the task single line message.
        
        返回第一个 level 1 的标题文本。如果没有 level 1 标题，则返回空字符串。
        """
        if self.is_outofdate():
            raise ValueError("Task is out of date, only task_id is accessible")
            
        # 解析标记文本
        headers = list(self.get_headers())
        
        # 查找第一个 level 1 标题
        for header in headers:
            if header.level == 1:
                return header.title
        
        return ""
    
    @property
    def edit_status(self) -> TaskEditStatus:
        """获取任务编辑状态"""
        if not self._edit_session:
            return TaskEditStatus.CLEAN
            
        if self._edit_session.edit_count > self._creation_edit_count:
            return TaskEditStatus.OUTOFDATE
            
        return TaskEditStatus.CLEAN
        
    def is_outofdate(self) -> bool:
        """检查任务是否过期"""
        return self.edit_status == TaskEditStatus.OUTOFDATE

    def _set_edit_session(self, edit_session: Optional[EditSession]) -> None:
        """设置关联的编辑会话并记录当前编辑计数"""
        self._edit_session = edit_session
        if edit_session:
            self._creation_edit_count = edit_session.edit_count

    def set_filename(self, filename: str) -> 'FileTaskImpl':
        # 主动设置 文件名，避免自动检测
        self._task_file = filename
        return self
    
    def as_mutable(self) -> 'FileTaskMut':
        """获取此文件任务的可变版本"""
        return cast(FileTaskMut, self)
    
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
        
    def get_tasks(self) -> List[Task]:
        """获取此文件任务的所有子任务。
        
        Returns:
            List[Task]: 子任务列表（可以是InlineTask或FileTask）
        """
        tasks = []
        
        # 获取所有任务列表项及其对应的任务ID
        task_items = self._get_tasks()
        
        # 为每个任务创建 InlineTask 实例
        for list_item, task_id in task_items:
            # 创建编辑会话
            edit_session = self.get_edit_session()
            
            # 创建 InlineTask 实例
            inline_task = InlineTaskImpl(
                file_service=self.file_service,
                numbering_service=self.numbering_service,
                edit_session=edit_session,
                list_item=list_item
            )
            
            tasks.append(inline_task)
        
        return tasks
        
    def get_tag_groups(self) -> Dict[str, Dict[str, Any]]:
        """获取此任务中定义的标签组。
        
        Returns:
            Dict[str, Dict[str, Any]]: 标签组字典，其中每个值是一个包含
                'ordered'（bool）和'items'（List[str]）键的字典
        """
        tag_groups = {}
        
        # 查找标签部分
        headers = list(self.get_headers())
        for header in headers:
            if header.title.lower() == "tags":
                # 查找标签组（level 3 标题，即 ### 标题）
                for sub_header in header.children:
                    if sub_header.level == 3:  # level 3 对应 ### 标题
                        group_name = sub_header.title
                        
                        # 检查是否是有序列表
                        is_ordered = False
                        items = []
                        
                        # 查找列表
                        for block in sub_header.blocks:
                            if isinstance(block, ListBlock):
                                is_ordered = block.ordered
                                # 提取列表项文本
                                for item in block.items:
                                    items.append(item.text.strip())
                        
                        # 添加到标签组字典
                        tag_groups[group_name] = {
                            'ordered': is_ordered,
                            'items': items
                        }
        
        return tag_groups
    
    def delete(self, task_id: Optional[str] = None, force: bool = False) -> bool:
        """删除此任务或子任务。
        
        Args:
            task_id: 任务ID（可选）
            force: 强制删除（可选，默认为 False）
            
        Returns:
            bool: 是否删除成功
        """
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
        """获取此任务中定义的标签组。
        
        Returns:
            Dict[str, Dict[str, Any]]: 标签组字典
        """
        return self.get_tag_groups()


class FileTaskService(TaskBase):
    """Implementation of TaskService interface using composition pattern.
    
    This service manages tasks stored in files and provides transaction support.
    
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
            numbering_service: Optional numbering service to use for generating task IDs.
                              If not provided, a TaskNumberingService will be created.
        """
        # 初始化基类
        TaskBase.__init__(self, file_service, numbering_service)
        
        # 如果未提供 numbering_service，创建一个 TaskNumberingService
        if numbering_service is None:
            self.numbering_service = TaskNumberingService(file_service)
        
        # 获取默认前缀
        default_prefix = self.numbering_service.get_default_prefix()
        
        # 构造根任务 ID，格式为 "{default_prefix}-000"
        root_task_id = f"{default_prefix}-000"
        
        # 检查根任务文件是否存在
        tasks_dir = config.get("tasks.active_dir", "tasks")
        root_task_file = os.path.join(tasks_dir, f"{root_task_id}.md")
        
        # 如果根任务文件存在，读取其内容作为 context
        if file_service.file_exists(root_task_file):
            context = file_service.read_file(root_task_file)
        else:
            # 如果根任务文件不存在，使用默认模板作为 context
            context = FILE_TASK_TEMPLATE.format(
                name="Root Task",
                description="This is the root task for the project."
            )
            # 创建目录结构
            file_service.create_directory(tasks_dir)
            archived_dir = config.get("tasks.archived_dir", "archived")
            file_service.create_directory(archived_dir)
            # 写入根任务文件
            file_service.write_file(root_task_file, context)
        
        # 创建根任务实例（使用组合而不是继承）
        self.root_task = FileTaskImpl(file_service, self.numbering_service, root_task_id, context)
    
    def new_task(self, task_msg: str, task_prefix: Optional[str] = None) -> Optional[FileTaskMut]:
        """Create a new file task.
        
        Args:
            task_msg: Description of the task
            task_prefix: Optional prefix for the task ID
            
        Returns:
            Optional[FileTaskMut]: The newly created file task, or None if creation failed
        """
        # 1. 使用根任务实例添加内联任务
        inline_task = self.root_task.new_sub_task(task_msg, task_prefix)
        
        # 如果内联任务创建失败，返回 None
        if inline_task is None:
            return None
            
        # 2. 使用 convert_task 方法将内联任务转换为文件任务
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
