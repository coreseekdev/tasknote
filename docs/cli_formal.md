# TaskNote CLI 形式化参数解析规范

本文档提供了 TaskNote 命令行工具的参数解析规范，用于指导代码生成。每个命令的参数解析规则以形式化方式描述。

## 通用规则

1. **命令格式**：`tasknote <command> [options] [arguments]`
2. **帮助选项**：所有命令都支持 `--help` 选项
3. **参数类型**：
   - **必选参数**：使用 `<param>` 表示
   - **可选参数**：使用 `[param]` 表示
   - **可重复参数**：使用 `...` 后缀表示
   - **互斥参数**：使用 `|` 分隔表示
4. **默认行为**：
   - 未指定任务ID时，默认使用当前活跃任务
   - 命令可以通过 `<command> --help` 获取帮助

## 命令参数规范

### init

```
命令：init
选项：
  --git          布尔值，使用git后端存储任务
  --help         布尔值，显示帮助信息
```

### add

```
命令：add
参数：
  description    字符串，任务描述，必选
选项：
  --parent       字符串，父任务ID，可选
  --yes, -y      布尔值，自动确认转换，可选
  --tag, -t     字符串，任务标签，可重复
  --file, -f     字符串，输入文件路径，可选
  --help         布尔值，显示帮助信息
行为：
  - 如果 --file 为 "-"，则从标准输入读取
  - 如果指定了 --parent 且目标不是file based task，需要确认转换
```

### note

```
命令：note
选项：
  --task         字符串，任务ID，可选，默认为当前活跃任务
  --category, -c 字符串，笔记类别，可选，默认为'notes'
  --message, -m  字符串，笔记内容，可重复
  --file, -f     字符串，输入文件路径，可选
  --help         布尔值，显示帮助信息
行为：
  - 如果未指定 --message 和 --file，则启动编辑器
  - 笔记保存路径为 {task_id}#{category}.md
```

### edit

```
命令：edit
参数：
  TASK_ID        字符串，任务ID，必选
选项：
  --help         布尔值，显示帮助信息
```

### list

```
命令：list
参数：
  [TASK_ID...]   字符串数组，任务ID列表，可选
  [tag_group]    字符串，标签组名称，可选
选项：
  --tag, -t     字符串，按标签过滤，可选
  --all          布尔值，包括已归档任务，可选
  --help         布尔值，显示帮助信息
特殊参数：
  active         关键字，列出所有活跃任务
行为：
  - 无参数时列出当前活跃任务的子任务
  - 指定tag_group时按标签组显示任务
  - 指定TASK_ID时在指定任务中查找
```

### archive

```
命令：archive
参数：
  TASK_ID        字符串，任务ID，必选
选项：
  --yes, -y      布尔值，自动确认归档未完成任务，可选
  --help         布尔值，显示帮助信息
```

### remove

```
命令：remove
参数：
  TASK_ID        字符串，任务ID，必选
选项：
  --force        布尔值，强制删除有关联内容的任务，可选
  --yes, -y      布尔值，自动确认删除，可选
  --help         布尔值，显示帮助信息
行为：
  - 已归档任务不需要 --force 选项
  - 删除inline task时需要确认，除非指定 --yes
```

### open

```
命令：open
参数：
  TASK_ID        字符串，任务ID，必选
选项：
  --help         布尔值，显示帮助信息
行为：
  - 如果是inline task，会提示是否创建独立任务
```

### active

```
命令：active
参数：
  [TASK_ID]      字符串，任务ID，可选
选项：
  --help         布尔值，显示帮助信息
行为：
  - 无参数时列出所有活跃任务
  - 有参数时关闭该任务之上的所有任务
  - 如果指定任务不在活跃列表中，等同于open命令
```

### close

```
命令：close
参数：
  [TASK_ID]      字符串，任务ID，可选
选项：
  --all          布尔值，关闭所有活跃任务，可选
  --help         布尔值，显示帮助信息
行为：
  - 无参数时关闭最近添加的活跃任务
  - 有参数时关闭该任务之上的所有任务
  - 如果指定任务不在活跃列表中，返回错误
```

### done

```
命令：done
参数：
  [TASK_ID]      字符串，任务ID，可选，默认为当前活跃任务
选项：
  --help         布尔值，显示帮助信息
行为：
  - 对inline task直接修改文本
  - 对file task添加DONE标签
  - 如果任务处于活跃状态，自动关闭
```

### tag

```
命令：tag
参数：
  [TASK_ID]      字符串，任务ID，可选，默认为当前活跃任务
选项：
  --tag, -t     字符串，标签名称，可重复
  --replace      布尔值，替换现有标签，可选
  --group, -g    字符串，标签组名称，可选
  --ordered, -o  布尔值，有序标签组，可选，默认为无序
  --help         布尔值，显示帮助信息
行为：
  - 无--tag参数时列出任务的标签
  - 有--group无--tag时列出标签组信息
```

### search

```
命令：search
参数：
  query          字符串，搜索关键词，必选
选项：
  --tag, -t     字符串，按标签过滤，可选
  --in           字符串，指定搜索范围的任务ID，可选
  --all          布尔值，包括已归档任务，可选
  --help         布尔值，显示帮助信息
行为：
  - 默认只在当前活跃任务及其子任务中搜索
```

### help

```
命令：help
参数：
  [command]      字符串，命令名称，可选
选项：
  --all          布尔值，显示所有命令的详细信息，可选
  --format       字符串，输出格式，可选值：text|markdown|man，默认为text
  --help         布尔值，显示帮助信息
行为：
  - 无参数时显示所有命令的简要列表
```

### mcp

```
命令：mcp
选项：
  --port         整数，服务器端口，可选，默认为8080
  --host         字符串，服务器主机，可选，默认为127.0.0.1
  --auth         字符串，认证令牌，可选
  --help         布尔值，显示帮助信息
```

## 环境变量

```
TASKNOTE_CLI_DEBUG  非空值时启用调试模式，输出JSON格式的命令解析结果
```
