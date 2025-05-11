FileTask 

- 记录在 Task-xxx.md 中的 Task ,  file task 可以有 sub-task 。 
- file task 也被称作  Project, 模板如下：
- Task 分 FileTask 和 InlineTask ，后者为一般意义上的 Task ，即 可以用一行文本描述的 Task 

```markdown 
# 项目模板 - 用于创建新项目
PROJECT_TEMPLATE = """# {name}

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
```

    其中，

    - name 为任务名称
    - description 为任务描述，在当前的实现中 为 除非手工编辑，否则为空
    - Tasks 为 sub-task 的列表，采用 markdown unordered task list 形式， 例如 
        "- [ ] task" 不带编号的任务，极少见。除非手工编辑，否则不会构造。 可以使用 TASK-xxx#yyyy 访问 yyyy 为任务的无歧义前缀
        "- [ ]`TASK-xxx`yyyyy" , 可使用 TASK-xxx 访问，也可直接使用 xxx ， 也可以使用上一条的访问方式
        "- [ ][`TASK-xxx`yyyyy](Task-xxx.md)" ， 访问方式同上，但是 表示当前的 task 本是也是 FileTask, 可能有
    - Tags 表示 预制的 Tags Group , 默认有 Milestones Kanban
        - 分组中包括的 Tag 以  ordered 或 unordered list 构造
        - 是否 ordered 与最终的显示结果相关


# 提供的接口

- FileTask(file_service, task_id, context) 构造 FileTask
    - task_id 为 任务编号，不可修改
    - context 为 任务的 markdown 格式的正文
    - file_service 仅用于处理 包括 subtask 也是 FileTask 的情况

- tasks() -> [Task]

    - 返回 当前 Task 关联的 sub task 列表， 可以是 InlineTask | FileTask
    - 不额外提供 getTask ，通过 tasks 查找

- new_task(task_msg, [task_prefix]) -> InlineTask  创建一个新的 Task ,  使用 numbering 服务获得任务编号， task_prefix 为可选的编号前缀
- mark_as_done,  标记当前任务已经完成
    - 对于 InlineTask 为 [ ] -> [X] 
    - 对于 FileTask 为 MetaData 中， 增加 标记为 DONE 的 Tag 
      - 然后需要发送 update_task_status 命令，让 sub task 中有这个 task 的 FileTask 能够更新状态
- mark_as_undone 逻辑类似
    - [X] -> [ ]
- delete(force)
    - 从文件中删除自身, 或 删除文件
- delete(task_id)
    - 删除 TASKID 为  task_id 的 InlineTask , 不能删除 FileTask
    - 包括 Task 本身 和 Task 关联的 tag list
- mark_as_archived(force)
    - 标记当前任务归档
- add_related_task(task_id) -> FileTask
    - 添加已经存在的 task_id 到 当前 task 中， 如果 task_id 为 InlineTask, 给出到所在的 FileTask 的文件名
- convert_task(task_id) 
    - 讲当前 FileTask 中的某个 subtask 转为 FileTask , 此操作不可逆
    - 同时需要发送 convert_task 命令，更新 sub task 中有这个 task 的 FileTask 
- modify_task(task_msg)
    - 更新当前 FileTask 的标题
- modify_task(task_id, task_msg)
    - 更新当前 FileTask 或 某个 subtask 的标题 

- tags() -> [tag]
    - FileTask | InlineTask 关联的 Tag
    - 如果是 FileTask , tag 记录在 meta data 
    - 如果是 InlineTask , 则形如
    
    """
    - [ ] task
        - tagA
        - tagName
    """

    - 注意，InlineTask 的 nested sub list 仅能是 tag , 如果需要附加 note , 需要先转为 FileTask

- tags(new_tags) -> [tag]
    - 替换现有的 tag 列表
    - 为保持 API 的简单，不支持 增加添加

- tag_groups() -> [tag_group]

    - 返回 tag_group 的列表， 为 dict ，形如 key -> { ordered, items: [tag, ]}
    - 为保持 API 简单，不支持按名称获取
    - 默认情况，应返回 Milestones， Kanban 作为 key 的 

## Task 的继承关系 和相关方法

### Task

- 通用抽象基类，无构造函数， 在 task_service 中定义 

- mark_as_done
- mark_as_undone
- delete
- modify_task(task_msg)
- tags() 
- tags(new_tags) 

### InlineTask

- convert_task(task_id)

### FileTask

- FileTask 构造函数
- new_task
- tasks
- delete(task_id)
- mark_as_archived(force)
- add_related_task(task_id)
- modify_task(task_id, task_msg)
- tag_groups()