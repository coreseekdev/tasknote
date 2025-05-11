# TaskNote 命令行接口设计

## 基本概念

- **任务类型**：
  - **TASK**：一行文字能够说明的简单任务 ， 也称之为 inline task
  - **Project**：包括多个子任务，可附加 NOTE 的复杂任务, 也称之为 file task 
  - 无论类型是 Project 还是 TASK，其编号均为 TASK-xxx 的形式

- **活跃任务 (Active Task)**：
  - 记录在 `{task_repo}/active` 纯文本文件中
  - 活跃任务是一个栈结构
  - 默认情况下，无参数 `close` 命令会关闭（从 active 文件中删除）最后一个 TASK
  - 可以通过指定 task 的形式，关闭到特定的 task
  - 如果 active 为空，则 active 的 task 为 TASK-000


## 命令参考

### 初始化与配置

```
tasknote init [--git] [--help]
```

初始化 tasknote 文件仓库。

**参数**：
- `--git`：使用 git 后端，即特定的 git 分支存储任务文件
- `--help`：显示帮助信息

### 任务管理

```
tasknote add [--parent TASK_ID] [--yes] [--tag <tagName>...] [--file <file>] <description> [--help]
```

添加任务到当前活跃的任务。

**参数**：
- `--parent TASK_ID`：指定任务添加的父任务（原 `--to`）
- `--yes`, `-y`：如果目标不是 file based task，自动确认转换
- `--tag <tagName>`：初始附加到任务的标签，可多次指定
- `--file <file>`, `-f <file>`：从文件读取任务，每行作为一个独立的任务。使用 `-` 表示从标准输入读取
- `<description>`：任务描述，可以不使用引号
- `--help`：显示帮助信息

**说明**：
- 由于默认 task 表述只有一行，此命令不需要多行机制
- 当指定父任务且不是 file based task 时，需要确认转换

```
tasknote note [--task <task_id>] [--category <category>] [--message <message>...] [--file <file>] [--help]
```

记录任务的笔记内容。

**参数**：
- `--task <task_id>`：指定要添加笔记的任务ID，如果未指定，则使用当前活跃任务
- `--category <category>`：笔记类别（原 NOTE_FILE_KEY），决定保存到的文件名 `{task_id}#{category}.md`，默认为 'notes'
- `--message <message>`, `-m <message>`：笔记内容，可多次指定以添加多行内容
- `--file <file>`, `-f <file>`：从指定文件读取笔记内容
- `--help`：显示帮助信息

**说明**：
- 类似 git，当笔记有多行时，可以通过多个 `-m` 指定
- 如果使用 `--file`，则读取指定文件的内容作为笔记
- 如果没有给出 `-m` 或 `-f`，则启动默认编辑器，用户可以通过编辑器编辑或删除笔记
```
tasknote edit <TASK_ID> [--help]
```

使用系统预制的编辑器编辑指定任务所在的文件。

**参数**：
- `<TASK_ID>`：要编辑的任务ID
- `--help`：显示帮助信息

**说明**：
1. 如果 TASK_ID 对应一个独立的 markdown 文件，则直接打开该文件
2. 如果没有对应文件，则在所有的 TASK_ID.md 文件中寻找该任务，并打开包含该任务的文件
3. 优先在活跃（active）任务列表中寻找
4. 如果在 git 环境下工作，优先使用 git 配置的编辑器，否则使用操作系统默认编辑器或用户配置的编辑器

### 任务列表查看

```
tasknote list [--tag <tagName>] [<TASK_ID>...|active] [--all] [--help]
```

列出符合条件的任务。

**参数**：
- `--tag <tagName>`：按标签过滤任务
- `[<TASK_ID>...]`：指定要查看的任务ID列表，如果未指定，则在当前活跃任务中查找
- `active`：特殊关键字，表示列出所有活跃任务，包括 TASK-000
- `--all`：在所有任务记录中查找，包括已归档的任务
- `--help`：显示帮助信息

```
tasknote list <tag_group> [--help]
```

按标签组显示任务。

**参数**：
- `<tag_group>`：标签组名称，指定要显示的标签组
- `--help`：显示帮助信息

**说明**：
1. 标签组中的标签显示方式取决于组的类型：
   - 有序标签组：以看板形式从左到右显示，按序号排列
   - 无序标签组：以列表形式从上到下显示，每个标签作为标题
2. 显示包含指定标签组中标签的所有任务

```
tasknote list [--help]
```

列出当前活跃任务的所有子任务。

**参数**：
- `--help`：显示帮助信息

**说明**：
- 显示当前任务的所有子任务，包括其标签信息
- 对于基于文件的任务，会以树形结构特别标记
### 任务归档与删除

```
tasknote archive <TASK_ID> [--yes] [--help]
```

将指定任务归档。

**参数**：
- `<TASK_ID>`：要归档的任务ID
- `--yes`, `-y`：自动确认归档未完成的任务
- `--help`：显示帮助信息

**说明**：
- 归档不会改变关联的笔记文件的位置
- 建议使用归档而非删除来管理已完成的任务
- 归档未标记为完成的任务时会显示确认提示

```
tasknote remove <TASK_ID> [--force] [--yes] [--help]
```

删除指定任务。

**参数**：
- `<TASK_ID>`：要删除的任务ID
- `--force`：强制删除，即使任务关联了笔记或存在子任务
- `--yes`, `-y`：自动确认删除，不显示提示
- `--help`：显示帮助信息

**说明**：
1. 如果任务关联了笔记或存在内嵌子任务，需要使用 `--force` 选项才能删除
   - 已经归档的任务不需要指定 `--force`
2. 如果要删除的是内嵌任务（inline task），会显示确认提示以避免编号输入错误
   - 如果指定了 `--yes` 选项，则直接删除不显示提示
3. 删除操作会同时删除任务本身和关联的笔记

### 任务活跃状态管理

```
tasknote open <TASK_ID> [--help]
```

将指定任务设置为活跃状态。

**参数**：
- `<TASK_ID>`：要设置为活跃状态的任务ID
- `--help`：显示帮助信息

**说明**：
- 如果指定的任务是 inline 类型（即存在于某个 markdown 文件的任务列表中），则会提示用户是否创建独立任务

```
tasknote active [<TASK_ID>] [--help]
```

管理活跃任务列表。

**参数**：
- `[<TASK_ID>]`：可选的任务ID
- `--help`：显示帮助信息

**说明**：
- 如果没有指定任务ID，则列出当前所有活跃任务
- 如果指定了任务ID，则关闭该任务之上的所有任务
- 如果指定的任务不在活跃列表中，则等同于 `open <TASK_ID>` 命令

```
tasknote close [<TASK_ID>] [--all] [--help]
```

关闭活跃任务。

**参数**：
- `[<TASK_ID>]`：可选的任务ID
- `--all`：关闭所有活跃任务
- `--help`：显示帮助信息

**说明**：
- 如果没有指定任务ID，则关闭最近添加的活跃任务
- 如果指定了任务ID，则关闭该任务之上的所有任务
- 如果指定的任务不在活跃列表中，则返回错误
```
tasknote done [<TASK_ID>] [--help]
```

标记指定任务为已完成状态。

**参数**：
- `[<TASK_ID>]`：要标记为完成的任务ID，如果未指定，则使用当前活跃任务
- `--help`：显示帮助信息

**说明**：
1. 对于 inline 类型任务（存在于 markdown 文件中的任务列表），直接修改文本标记为完成
2. 对于独立文件任务或项目：
   - 添加 `DONE` 标签
   - 在上级任务的列表中标记该任务为完成
3. 如果当前任务处于活跃状态，则自动关闭该任务
4. 如果已经标记为完成的任务又添加了新的子任务：
   - 如果任务已经归档，则自动取消归档
   - 删除任务中的 `DONE` 标签
   - 修改上级任务列表中的完成标记
5. 如果当前标记为完成的任务是上级任务列表中最后一个未完成的任务，则自动标记上级任务为完成
   - 这个自动标记过程会在下一次处理消息时执行
### 标签管理

```
tasknote tag [<TASK_ID>] [--tag <tagName>...] [--replace] [--group <groupName>] [--ordered] [--help]
```

管理任务的标签。

**参数**：
- `[<TASK_ID>]`：要管理标签的任务ID，如果未指定，则使用当前活跃任务
- `--tag <tagName>`：要添加的标签名称，可多次指定以添加多个标签
- `--replace`：替换模式，删除之前关联的所有标签
- `--group <groupName>`, `-g <groupName>`：指定标签组名称，将标签设置到该组中
- `--ordered`, `-o`：指定标签组为有序排列（默认为无序）
- `--help`：显示帮助信息

**说明**：
- 如果没有指定 `--tag` 参数，则列出任务关联的所有标签
- 如果指定了 `--group` 参数但没有 `--tag` 参数，则列出指定标签组及其包含的标签
- 由于提供了 `--replace` 选项，因此不需要单独的标签删除接口

### 搜索

```
tasknote search <query> [--tag <tag>] [--in <TASK_ID>] [--all] [--help]
```

搜索任务和笔记。

**参数**：
- `<query>`：搜索关键词
- `--tag <tag>`：按标签过滤搜索结果
- `--in <TASK_ID>`：在指定任务及其子任务中搜索
- `--all`：在所有任务中搜索，包括已归档的任务
- `--help`：显示帮助信息

**说明**：
- 默认情况下只在当前活跃任务及其子任务中搜索
- 搜索结果包括任务标题、笔记内容和标签

### 帮助

```
tasknote help [<command>] [--all] [--format <format>] [--help]
```

显示命令的帮助信息。

**参数**：
- `[<command>]`：指定要显示帮助信息的命令
- `--all`：显示所有命令的详细帮助信息
- `--format <format>`：指定输出格式，可选值为 `text`（默认）、`markdown`、`man`
- `--help`：显示帮助命令的帮助信息

**说明**：
- 如果未指定命令，则显示所有可用命令的简要列表
- 指定命令时显示该命令的详细用法和选项
- 可以使用 `tasknote <command> --help` 格式直接获取特定命令的帮助

```
tasknote <command> --help
```

显示指定命令的帮助信息。

**说明**：
- 这是获取命令帮助的快捷方式
- 每个命令都支持 `--help` 选项来显示其用法

### MCP 服务

```
tasknote mcp [--port <port>] [--host <host>] [--auth <auth_token>] [--help]
```

启动 MCP (Machine Communication Protocol) 服务器，允许 LLM 通过 API 访问和操作任务。

**参数**：
- `--port <port>`：服务器端口，默认为 8080
- `--host <host>`：服务器主机，默认为 127.0.0.1
- `--auth <auth_token>`：认证令牌，用于验证 API 请求
- `--help`：显示帮助信息

**说明**：
- 启动后，LLM 可以通过 HTTP API 访问和管理任务
- 支持的 API 端点包括：
  - `GET /tasks`：获取任务列表
  - `GET /tasks/{task_id}`：获取特定任务的详细信息
  - `POST /tasks`：创建新任务
  - `PUT /tasks/{task_id}`：更新任务
  - `GET /tags`：获取所有标签
  - `GET /active`：获取活跃任务
- 所有 API 请求和响应均使用 JSON 格式
- 如果指定了 `--auth` 参数，则所有请求需要在头部包含 `Authorization: Bearer <auth_token>`

## 调试模式

支持通过环境变量 `TASKNOTE_CLI_DEBUG` 开启调试模式。当该环境变量设置为非空值时，命令行工具不会实际执行操作，而是仅输出命令解析结果，以 JSON 格式展示。