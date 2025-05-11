"""File-based task service implementation for TaskNotes.

This module provides concrete implementations of the Task, InlineTask, FileTask,
and TaskService interfaces defined in the task module.
"""

import os
import time
import re
from typing import Dict, List, Optional, Set, Tuple, Union, Any

from tasknotes.interface.file_service import FileService
from tasknotes.interface.numbering_service import NumberingService
from tasknotes.interface.task import Task, InlineTask, FileTask, TaskService
from tasknotes.core.config import config
from tasknotes.services.numbering_service import TaskNumberingService

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

class FileTaskImpl(Task):
    """Base implementation of Task interface."""
    
    def __init__(self, task_id: str):
        """Initialize a FileTaskImpl instance.
        
        Args:
            task_id: ID of the task
        """
        self._task_id = task_id
    
    @property
    def task_id(self) -> str:
        """Get the task ID."""
        return self._task_id
    
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


class InlineTaskImpl(FileTaskImpl, InlineTask):
    """Implementation of InlineTask interface."""
    
    def __init__(self, file_service: FileService, task_id: str, parent_task: 'FileTaskImpl'):
        """Initialize an InlineTaskImpl instance.
        
        Args:
            file_service: The file service to use for storage operations
            task_id: ID of the task
            parent_task: The parent FileTask that contains this InlineTask
        """
        super().__init__(task_id)
        self.file_service = file_service
        self.parent_task = parent_task
    
    def convert_task(self) -> FileTask:
        """Convert this inline task to a file task."""
        raise NotImplementedError("convert_task not implemented")


class FileTaskImpl(FileTaskImpl, FileTask):
    """Implementation of FileTask interface."""
    
    def __init__(self, file_service: FileService, numbering_service: NumberingService, task_id: str, context: str):
        """Initialize a FileTaskImpl instance.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: The numbering service to use for generating task IDs
            task_id: ID of the task
            context: The markdown content of the task
        """
        super().__init__(task_id)
        self.file_service = file_service
        self.numbering_service = numbering_service
        self.context = context
    
    def new_sub_rtask(self, task_msg: str, task_prefix: Optional[str] = None) -> InlineTask:
        """Create a new inline task as a subtask of this file task.
        
        Args:
            task_msg: Description of the task
            task_prefix: Optional prefix for the task ID
            
        Returns:
            InlineTask: The newly created inline task
        """
        # 获取任务ID
        if task_prefix is None:
            task_prefix = self.numbering_service.get_default_prefix()
            
        task_id = self.numbering_service.get_next_number(task_prefix)
        
        # 修改当前任务文件，在 # Tasks 部分添加新任务
        task_path = os.path.join(self.file_service.base_path, f"{self.task_id}.md")
        content = self.context
        
        # 找到 ## Tasks 部分并添加新任务
        task_section_pattern = r"(## Tasks\s*\n)"
        task_entry = f"- [ ] {task_id}: {task_msg.split('\n')[0] if '\n' in task_msg else task_msg}\n"
        
        if re.search(task_section_pattern, content):
            updated_content = re.sub(task_section_pattern, f"\g<1>{task_entry}", content)
        else:
            # 如果找不到 Tasks 部分，添加一个
            updated_content = content + f"\n## Tasks\n{task_entry}"
        
        # 更新文件
        self.file_service.write_file(task_path, updated_content)
        self.context = updated_content
        
        # 创建并返回 InlineTask 实例
        return InlineTaskImpl(self.file_service, task_id, self)
    
    def tasks(self) -> List[Task]:
        """Get all subtasks of this file task."""
        raise NotImplementedError("tasks not implemented")
    
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
        task_entry = f"- [ ] {task_id}: {task_msg.split('\n')[0] if '\n' in task_msg else task_msg}\n"
        
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
