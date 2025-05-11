# 命令行接口

基本概念： 

- 任务分两类，一行文字能够说明的，称之为 TASK, 包括多个子任务，可附加 NOTE 的，称之为 Project 。 无论类型是 Project | TASK 其编号均为 TASK-xxx 的形式
- 活跃任务 / Active Task, 记录在 {task_repo}/active 纯文本文件中， 活跃任务是一个栈，默认情况，没有任何参数 close 为关闭（从 active 文件中删除) 最后一个 TASK 

    - 可以通过指定 task 的形式，关闭到特定的 task 
    - 如果 active 为空，则 active 的 task 为 TASK-000


tasknote init [--git]
    初始化 tasknote 文件仓库, 如果给出 --git 则使用 git 后端，即 特定的 git 分支存储任务文件
tasknote add [--to TASK_ID][-y|--yes] <-t/--tag> todo -tag tagName < lkjfsalfdsjajfsakl fdsafsakfldsfjkas fklasjfds | [-f|--file] <file> >
    添加任务到当前活跃的任务。 add 之后的 -/-- 表示初始附加到任务的 tag ， 后续的为任务描述，可以不使用 “”
    - 可选的 TASK_ID 表示 任务添加的 目标 target ， 如果不是 file based task, 则需要提示转换
        - 如果 [y] 则直接转换
    - 由于默认  task 表述只有一行，因此 这个命令不需要多行机制
    - 如果启用  -F 则文件中每一行，作为一个独立的命令
    - -F 启用时， - 表示 stdin 
tasknote note [--task <task_id>][NOTE_FILE_KEY] -m "message"
    记录 task_id 的  note 到  "{task_id}#{NOTE_FILE_KEY}.md"  如果 task_id 为给出，为当前 active 的 project
    - 类似 git, 当 message 有多行时，可以通过多个 -m 或 -F 指定， 如果时 -F 则应读取 指定文件的当前内容，复制到 NOTE 中
    - 如果 没有给出 -m | -F , 则启动默认编辑器。 用户可以通过编辑器删除某个已经存在的 NOTE   
    - 如果没有给出 NOTE_FILE_KEY， 默认为 'notes'。 
tasknote edit {TASK_ID}
    使用系统预制的编辑器编辑 TASK_ID 所在的 文件
    1. 如果 TASK_ID 对应一个 md ，则直接打开那个文件
    2. 如果 没有，则在文件中寻找。 注意需要在所有的 TASK_ID.md 中寻找，因为无法确定任务添加的时间
        - 打开任务所在的 {TASK_ID}.md
        - 优先寻找打开（active) 列表中的文件
    3. 如果时工作在 git 下，优先使用 git 配置的编辑器
    4. 如果没有 git 则关联 os 的， 或要求用户主动配置 
tasknote list -tagName <[TASK_ID，]|active> [--all] 
    列出关联了 tag 即 关联了 tagName 作为 tag 的 Task 
    1. [TASK_ID，] 是列表，如未给出，则在当前 active 的 Project 内寻找，如给出了，则在指定的 TASK | Project 中寻找（过滤）
    2. [active] 是别名，含义是出现在 active 文件中的所有 task ， 包括 TASK-000 。 理论上 TASK-000 应该永远是文件中的第一行
    3. [--all]  查找范围是全部任务记录 
tasknote list {tag_group}
    1. tag_group 为 当前/active project 中预制的 tag groups 
    2. tag_group 中 tag 的列表排序方式不同，显示也不同
        - 有序列表，看板 从左到右，按序号排列
        - 无序列表，从上到下的列表， markdown 格式输出，每个 tag 作为 head
    3. 列出包括上面 tag 的 tasks
tasknote list
    - 列出当前 task 的 所有 (sub)tasks 
    - 需要包括 tags 
    - 如是 file based 需要特别标记（类似 tree-view)
tasknote ar|archive [-y|--yes] {TASK_ID} 
    对 task_id 归档，归档不会改变 关联的笔记文件的位置
    - 实际使用中，建议只归档，不删除
    - 尝试归档没有标记为 done 的任务，会提示
tasknote rm {TASK_ID} [--force] [-y|--yes]
    删除 某个 task 
    1. 如果这个 task 关联了 note 或 存在 inline 的 subtask , 需要 [--force] 才可以删除
        - 已经归档的 task 不需要加 --force 
    2. 如果 task 本身是 inline 的 task  提示后删除（避免编号输入错误）
       - 如果给出了 -y , 则直接删除
    3. 删除会删除 task 本身 和 关联的 note 

tasknote open {TASK_ID}
    开启当前的 task_id 作为活跃的 task 
    - 如果此时，对应的 task_id 为 inline 的， 即在某个 markdown 的 Task 列表中 ，则需要提示用户是否创建
tasknote active [{TASK_ID}]
    - 如果没有给出 task_id, 则为列出当前 active 的 task 
    - 如果给出了，则关闭 task_id 之上的所有 task 
    - 如果不是 active 的 ，则等同 open {task_id}

tasknote close [{TASK_ID}] --all
    关闭 active task 
    - 如果没有给出 TASK_ID , 则关闭最近一层 active task
    - 如果 给出 task_id 则 关闭 task_id 之上所有的 task 
    - 如果 task_id 不是 active 的，则报错
tasknote done [{TASK_ID}]
    标记某个 task 已完成
    1. inline task ， 直接修改文本
    2. file task | project 
        - 增加 tag  DONE 
        - 列表形式记录这个 task 的上级 file task 标记任务完成
    3. 如果当前 task 为 active 的，自动关闭
    4. 如果已经标记为 关闭的 task 又增加了新任务

        1. 如果 task 已经归档，则取消归档（移动）
        2. 删除 file task 中的 tag DONE 
        3. 修改上级的 TASK 列表中的完成标记
    5. 如果当前标记为完成的 TASK  也是上级列表中最后一个 未标记完成 TASK， 自动标记上级 TASK 完成了
        - 实际仅仅创建一个 message , 需要下一次处理消息时，才会真正处理
tasknote tag [--replace] [-g|--group groupName] [-o|--ordered] [{TASK_ID}] -tag tagName -tag tagNameB
    附加 tagName 到指定的 TASK_ID, tagName 可以一次给定多个
    - 如果 TASK_ID 未给出，则为 active task 
    - 如果启用 replace ，则 删除之前关联的 tag 列表
    - 可选的 groupName, 如给出，则变为 设置到 groupName 中  
        - 默认未 unordered 
    - 由于可以 replace ， 因此不提供单独删除的接口
tasknote tag [{TASK_ID}] [-g|--group]
    - task 列出关联的 tag 
    - 如未给出 task_id ，则 是 active task 
    - 列出 tag_group, 和 group 内的 tag ， 需要指明 是否 ordered

需要支持 环境变量给出的调试开关 TASKNOTE_CLI_DEBUG ， 当开启时，不实际执行任务，仅给出命令行的解析结果，使用 JSON 的形式