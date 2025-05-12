"""
Task and Project Interface for TaskNotes.

This module defines the interfaces for managing tasks and projects in TaskNotes.
It provides a unified model where projects are special cases of tasks.

This module uses Protocol for interface definitions, separating read-only and mutable operations.
"""

from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Set, Protocol, runtime_checkable, TypeVar

from tasknotes.interface.file_service import FileService
from tasknotes.interface.numbering_service import NumberingService


# 注意：不要在此处添加 TaskStatus 枚举 

class TaskEditStatus(Enum):
    """任务编辑状态"""
    CLEAN = auto()      # 任务与源文件/编辑会话同步
    OUTOFDATE = auto()  # 任务已过期，需要重新加载


# 只读任务接口
@runtime_checkable
class Task(Protocol):
    """
    只读任务接口。
    
    定义了所有任务类型的共同只读操作。
    """

    @property
    def task_id(self) -> str:
        """获取任务ID"""

        ...

    @property
    def edit_status(self) -> 'TaskEditStatus':
        """获取任务编辑状态"""
        ...

    @property
    def task_message(self) -> str:
        """获取任务单行消息"""

        ...
    
    def get_tags(self) -> List[str]:
        """
        获取与此任务关联的标签列表。
        
        Returns:
            List[str]: 当前标签列表
        """

        ...
    
    def as_mutable(self) -> 'TaskMut':
        """
        获取此任务的可变版本。
        
        Returns:
            TaskMut: 可变任务接口
        """

        ...

# 可变任务接口
@runtime_checkable
class TaskMut(Task, Protocol):
    """
    可变任务接口。
    
    扩展了只读任务接口，添加了修改任务状态的方法。
    """

    def mark_as_done(self) -> bool:
        """
        将任务标记为已完成。
        
        Returns:
            bool: 如果操作成功则为True，否则为False
        """

        ...
    
    def mark_as_undone(self) -> bool:
        """
        将任务标记为未完成。
        
        Returns:
            bool: 如果操作成功则为True，否则为False
        """

        ...
    
    def delete(self, force: bool = False) -> bool:
        """
        删除任务。
        
        Args:
            force: 如果为True，即使有依赖项也强制删除
            
        Returns:
            bool: 如果操作成功则为True，否则为False
        """

        ...
    
    def modify_task(self, task_msg: str) -> bool:
        """
        更新任务描述或标题。
        
        Args:
            task_msg: 任务的新描述或标题
            
        Returns:
            bool: 如果操作成功则为True，否则为False
        """

        ...
    
    def set_tags(self, tags: List[str]) -> bool:
        """
        设置与此任务关联的标签列表。
        
        Args:
            tags: 要关联的新标签列表
            
        Returns:
            bool: 如果操作成功则为True，否则为False
        """

        ...

# 只读内联任务接口
@runtime_checkable
class InlineTask(Task, Protocol):
    """
    只读内联任务接口。
    
    表示为Markdown文件中的单行的任务。这些任务通常是FileTask的一部分，没有自己的文件。
    """

    def get_related_file_task(self) -> Optional['FileTask']:
        """
        返回当前内联任务关联的FileTask，如果存在。
        
        当任务使用链接形式表示时，链接的目标就是FileTask。
        
        Returns:
            Optional[FileTask]: 关联的文件任务，如果不存在则为None
        """

        ...
    
    def as_mutable(self) -> 'InlineTaskMut':
        """
        获取此内联任务的可变版本。
        
        Returns:
            InlineTaskMut: 可变内联任务接口
        """

        ...

# 可变内联任务接口
@runtime_checkable
class InlineTaskMut(InlineTask, TaskMut, Protocol):
    """
    可变内联任务接口。
    
    扩展了只读内联任务接口，添加了修改内联任务的方法。
    """

    def convert_task(self) -> 'FileTask':
        """
        将此内联任务转换为文件任务。
        
        Returns:
            FileTask: 新创建的文件任务
        """

        ...

# 只读文件任务接口
@runtime_checkable
class FileTask(Task, Protocol):
    """
    只读文件任务接口。
    
    表示为Markdown文件的任务。这些任务可以包含内联任务和其他文件任务作为子任务。
    """

    @property
    def context(self) -> str:
        """
        获取任务的完整Markdown内容。
        
        Returns:
            str: 任务的Markdown内容
        """

        ...
    
    def get_tasks(self) -> List[Task]:
        """
        获取此文件任务的所有子任务。
        
        Returns:
            List[Task]: 子任务列表（可以是InlineTask或FileTask）
        """

        ...
    
    def get_tag_groups(self) -> Dict[str, Dict[str, Any]]:
        """
        获取此任务中定义的标签组。
        
        Returns:
            Dict[str, Dict[str, Any]]: 标签组字典，其中每个值是一个包含
                'ordered'（bool）和'items'（List[str]）键的字典
        """

        ...
    
    def as_mutable(self) -> 'FileTaskMut':
        """
        获取此文件任务的可变版本。
        
        Returns:
            FileTaskMut: 可变文件任务接口
        """

        ...

# 可变文件任务接口
@runtime_checkable
class FileTaskMut(FileTask, TaskMut, Protocol):
    """
    可变文件任务接口。
    
    扩展了只读文件任务接口，添加了修改文件任务的方法。
    """

    def __init__(self, file_service: FileService, numbering_service: NumberingService, task_id: str, context: str) -> None:
        """
        初始化FileTaskMut实例。
        
        Args:
            file_service: 用于存储操作的文件服务
            numbering_service: 用于生成任务ID的编号服务
            task_id: 任务的ID
            context: 任务的Markdown内容
        """

        ...
    
    def new_sub_task(self, task_msg: str, task_prefix: Optional[str] = None) -> Optional[InlineTaskMut]:
        """
        创建一个新的内联任务作为此文件任务的子任务。
        
        Args:
            task_msg: 任务描述
            task_prefix: 可选的任务ID前缀
            
        Returns:
            Optional[InlineTaskMut]: 新创建的内联任务，如果创建失败则为None
        """

        ...
    
    def delete(self, task_id: Optional[str] = None, force: bool = False) -> bool:
        """
        删除此任务或子任务。
        
        Args:
            task_id: 要删除的子任务的ID，如果为None则删除此任务
            force: 如果为True，即使有依赖项也强制删除
            
        Returns:
            bool: 如果操作成功则为True，否则为False
        """

        ...
    
    def add_related_task(self, task_id: str) -> 'FileTaskMut':
        """
        将现有任务添加为此任务的相关任务。
        
        Args:
            task_id: 要添加为相关任务的任务ID
            
        Returns:
            FileTaskMut: 相关的文件任务
        """

        ...
    
    def modify_task(self, task_msg: Optional[str] = None) -> bool:
        """
        修改当前任务的标题
        """

        ...

# 任务服务接口
@runtime_checkable
class TaskService(Protocol):
    """
    任务服务接口，管理任务集合。
    
    TaskService作为项目的根任务，提供了额外的项目管理方法。
    支持事务操作，可以将多个任务操作合并为一次提交。
    """

    @property
    def root_task(self) -> FileTaskMut:
        """
        获取根任务。
        
        Returns:
            FileTaskMut: 根任务
        """

        ...
    
    def __init__(self, file_service: FileService, numbering_service: Optional[NumberingService] = None) -> None:
        """
        初始化TaskService实例。
        
        Args:
            file_service: 用于存储操作的文件服务
            numbering_service: 可选的用于生成任务ID的编号服务
        """

        ...
    
    def new_task(self, task_msg: str, task_prefix: Optional[str] = None) -> FileTaskMut:
        """
        创建一个新任务。
        
        Args:
            task_msg: 任务描述
            task_prefix: 可选的任务ID前缀
            
        Returns:
            FileTaskMut: 新创建的文件任务
        """

        ...
    
    def list_tasks(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        列出此服务管理的所有任务。
        
        Args:
            include_archived: 如果为True，则在列表中包含已归档的任务
            
        Returns:
            List[Dict[str, Any]]: 任务信息字典列表，包含：
                - id: 任务ID
                - name: 任务名称
                - description: 任务描述
                - created_at: 创建时间戳
                - archived_at: 归档时间戳（如果未归档则为None）
                - tags: 关联的标签列表
        """

        ...
    
    def get_task(self, task_id: str) -> Optional[FileTaskMut]:
        """
        根据ID获取特定任务。
        
        Args:
            task_id: 要检索的任务的ID
            
        Returns:
            Optional[FileTaskMut]: 任务，如果未找到则为None
            
        Raises:
            ValueError: 如果任务已归档
        """

        ...
    
    def archive_task(self, task_id: str) -> bool:
        """
        归档任务。
        
        Args:
            task_id: 要归档的任务的ID
            
        Returns:
            bool: 如果任务已归档则为True，如果未找到则为False
        """

        ...
    
    def delete_archived_task(self, task_id: Optional[str] = None) -> int:
        """
        删除已归档的任务。
        
        Args:
            task_id: 可选的要删除的特定已归档任务的ID。
                   如果为None，则将删除所有已归档的任务。
            
        Returns:
            int: 删除的任务数量
        """

        ...
    
    def transaction(self, commit_message: str = "") -> 'TaskTransaction':
        """
        创建一个新的任务事务。
        
        Args:
            commit_message: 提交消息
            
        Returns:
            TaskTransaction: 新创建的事务对象
        """

        ...

# 任务事务接口
@runtime_checkable
class TaskTransaction(Protocol):
    """
    任务事务接口，支持批量操作任务。
    
    该接口实现了上下文管理器协议，可以在with语句中使用。
    所有在事务中执行的操作将在事务结束时一次性提交。
    """

    def __enter__(self) -> 'TaskTransaction':
        """
        进入事务上下文。
        
        Returns:
            TaskTransaction: 事务对象自身
        """

        ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        退出事务上下文。
        
        如果没有异常发生，提交所有更改；否则回滚更改。
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯
            
        Returns:
            bool: 是否抑制异常
        """

        ...
    
    def new_task(self, task_msg: str, task_prefix: Optional[str] = None) -> FileTaskMut:
        """
        在事务中创建新任务。
        
        Args:
            task_msg: 任务描述
            task_prefix: 可选的任务ID前缀
            
        Returns:
            FileTaskMut: 新创建的文件任务
        """

        ...
    
    def archive_task(self, task_id: str) -> bool:
        """
        在事务中归档任务。
        
        Args:
            task_id: 要归档的任务的ID
            
        Returns:
            bool: 如果任务已归档则为True，如果未找到则为False
        """

        ...
    
    def delete_archived_task(self, task_id: Optional[str] = None) -> int:
        """
        在事务中删除已归档的任务。
        
        Args:
            task_id: 可选的要删除的特定已归档任务的ID。
                   如果为None，则将删除所有已归档的任务。
            
        Returns:
            int: 删除的任务数量
        """

        ...

# 向后兼容性别名
ProjectService = TaskService