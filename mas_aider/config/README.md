# 配置系统文档

多Agent系统支持灵活的配置管理，支持YAML和JSON格式配置文件。

## 📁 文件结构

```
config/
├── app_config.py      # 配置类和加载逻辑
├── config.json        # JSON格式配置文件（推荐）
├── config.yaml        # YAML格式配置文件（可选）
└── README.md          # 本文档
```

## ⚙️ 配置格式

### JSON配置 (config.json)

```json
{
  "_comment": "多Agent系统配置文件",
  "BASE_PATH": "/path/to/project",

  "workspace_path": "${BASE_PATH}/langgraph_workspace",
  "shared_folder_name": "shared",
  "shared_file_name": "math_tools.py",

  "model_name": "openai/glm-4.6",
  "api_base": null,

  "max_turns": 6,
  "verbose_logging": false,
  "initialize_git": true
}
```

### YAML配置 (config.yaml)

```yaml
# 多Agent系统配置文件 - YAML格式
# 支持变量插值: ${VAR_NAME}

# 路径配置
paths:
  project_root: "/path/to/project"
  framework_root: "${paths.project_root}/mas_aider"
  workspace_root: "${paths.project_root}/workspaces"

# 工作环境配置
environment:
  initialize: true
  collab:
    folder_name: collab  # 协作目录名称

# Agent配置
aider:
  model: openai/glm-4.6
  verbose_logging: false

# 工作流配置
workflow:
max_turns: 6
```

## 🔧 配置项说明

### 路径配置 (paths)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `paths.project_root` | string | - | 项目根目录路径 |
| `paths.framework_root` | string | `${paths.project_root}/mas_aider` | 框架根目录路径 |
| `paths.workspace_root` | string | `${paths.project_root}/workspaces` | 工作区根目录路径 |

### 环境配置 (environment)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `environment.initialize` | bool | `true` | 是否初始化Git仓库 |
| `environment.collab.folder_name` | string | `"collab"` | 协作目录名称 |

### Agent配置 (aider)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `aider.model` | string | `"openai/glm-4.6"` | AI模型名称 |
| `aider.verbose_logging` | bool | `false` | 详细日志输出 |

### 工作流配置 (workflow)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `workflow.max_turns` | int | `6` | 最大工作轮次 |

## 🌍 变量插值

配置文件支持变量插值语法：`${VAR_NAME}`

### 路径变量引用

支持在配置中引用已定义的路径：

```yaml
# 定义路径
paths:
  project_root: "/home/user/project"
  framework_root: "${paths.project_root}/mas_aider"  # 引用已定义的路径
  workspace_root: "${paths.project_root}/workspaces"  # 引用已定义的路径
```

### 系统变量

- `${HOME}`: 用户主目录

## 🎯 配置优先级

配置按以下优先级加载（高优先级覆盖低优先级）：

1. **配置文件** (config.json > config.yaml)
2. **环境变量**
3. **默认值**

### 环境变量映射

| 环境变量 | 配置项 |
|----------|--------|
| `OPENAI_API_URL` | `api_base` |
| `MODEL_NAME` | `model_name` |
| `MAX_TURNS` | `max_turns` |
| `VERBOSE_LOGGING` | `verbose_logging` |
| `INIT_GIT` | `initialize_git` |

## 📍 配置文件位置

系统按以下顺序自动查找配置文件：

1. `project_root/config.json`
2. `project_root/mas_aider/config.json`
3. `project_root/config.yaml`
4. `project_root/config.yml`
5. `project_root/mas_aider/config.yaml`
6. `project_root/mas_aider/config.yml`

## 🚀 使用方法

### 自动加载

```python
from mas_aider.config import AppConfig

# 自动查找并加载配置文件
config = AppConfig.load()
```

### 指定配置文件

```python
from pathlib import Path
from mas_aider.config import AppConfig

# 指定特定配置文件
config_path = Path("/path/to/custom/config.json")
config = AppConfig.load()  # 总是从固定的config/config.yaml加载
```

### 仅环境变量

```python
from mas_aider.config import AppConfig

# 仅使用环境变量（向后兼容）
config = AppConfig.from_env()
```

## 🔍 依赖要求

- **JSON格式**: Python标准库支持，无需额外依赖
- **YAML格式**: 需要安装 `PyYAML`

```bash
pip install PyYAML
```

如果没有PyYAML，系统会自动跳过YAML文件并使用JSON配置。

## ⚠️ 注意事项

1. **路径分隔符**: 使用正斜杠 `/`，系统会自动处理不同操作系统的路径差异
2. **布尔值**: JSON中使用 `true`/`false`，YAML中使用 `true`/`false`
3. **空值**: JSON中使用 `null`，YAML中使用 `null` 或省略
4. **编码**: 配置文件应使用UTF-8编码保存

## 🧪 测试配置

运行配置测试：

```bash
cd /path/to/project
python test_config.py
```

或者直接测试：

```python
from mas_aider.config import AppConfig

config = AppConfig.load()
print(f"Model: {config.aider.model}")
print(f"Workspace: {config.paths_workspace_root}")
```
