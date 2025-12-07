<div align="center">

<img src="pic/logo.png" alt="Weaver Logo" width="600"/>

# 🕷️ Weaver（编织者）

**Weave workflows, ship code.**

*基于 LangGraph 和 Aider 的强大配置驱动多Agent协作编排框架*

> **Weaver**: 不同于蚂蚁的"群聚"，蜘蛛（Weaver）通常是独居、高智商、且善于构建复杂结构（Web/Graph）的猎手。它完美契合 LangGraph 的形态——编织工作流，将代码（线）编织成软件（布）。

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Aider](https://img.shields.io/badge/Aider-integrated-purple.svg)](https://github.com/paul-gauthier/aider)

[特性](#-核心特性) • [快速开始](#-快速开始) • [文档](#-文档) • [示例](#-工作流配置示例) • [贡献](#-贡献)

[English](README.md) | [中文](README_CN.md)

</div>

---

## 📖 项目简介

<div align="center">

<img src="pic/framwork.png" alt="LangGraph + Aider Framework" width="600"/>

</div>

**Weaver** 是一个企业级的多Agent协作编排框架，通过声明式YAML配置实现多个AI Agent之间的无缝协作。基于LangGraph强大的图编排引擎和Aider的代码编辑能力，您无需编写任何Python代码即可定义复杂的多Agent工作流。

### 编织者哲学

正如蜘蛛以其精确和智慧编织蛛网，Weaver 帮助您构建精妙的多Agent工作流。每个Agent就像一根线，它们共同编织成坚固的软件解决方案。框架的图结构架构正如蜘蛛的网——复杂、互联、结构优美。

### 为什么选择这个框架？

- 🎯 **零代码工作流定义**：使用简单的YAML文件定义复杂的Agent协作流程
- 🔄 **生产就绪**：内置错误处理、重试机制和完整的日志系统
- ⚡ **高性能**：Agent缓存和Keep-Alive会话机制，优化执行速度
- 🔌 **可扩展**：基于插件的架构，支持热拔插路由器
- 🛡️ **健壮性**：完整的状态管理、执行历史和错误恢复

---

## ✨ 核心特性

### 🎨 配置驱动的工作流
- 通过YAML配置文件实现**零代码工作流定义**
- **业务逻辑与框架代码完全解耦**
- 支持**热拔插路由器**，遵循约定优于配置原则

### 🔀 LangGraph驱动的编排引擎
- **基于图的状态机**，支持复杂的分支和循环
- **灵活的条件路由**，支持表达式化条件评估
- **完整的状态跟踪**，支持执行历史和恢复

### 💾 Keep-Alive会话管理
- 通过 `FastAntsSession` 实现**持久化会话**，保持Agent在内存中存活
- **智能Agent缓存**，避免重复初始化
- **连续工作流执行**，在同一会话中运行多个工作流

### 🔧 深度集成Aider
- 通过Aider集成实现**强大的代码编辑能力**
- **基于Diff的修改**，精确跟踪文件变更
- **自动Git集成**，支持版本控制

### 📊 全面的监控系统
- **统一的错误处理**，基于装饰器的重试机制
- **详细的日志系统**，记录Agent响应、状态转换和错误
- **执行历史跟踪**，用于调试和审计

### 🤝 灵活的协作模式
- **多Agent协作**，按照定义的工作流执行
- **共享工作空间**，每个工作流有独立的工作空间
- **内置协作规范**，确保Agent输出格式一致

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Git
- OpenAI API Key（或兼容的API服务）

### 安装

```bash
# 克隆仓库
git clone https://github.com/sherkevin/Weaver.git
cd Weaver

# 安装依赖
pip install -r src/requirements.txt
```

### 配置

1. **设置环境变量**

在 `src/` 目录下创建 `.env` 文件：

```bash
cd src
cat > .env << EOF
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
EOF
```

或直接导出环境变量：

```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_API_BASE="https://api.openai.com/v1"
```

2. **配置项目路径**

编辑 `src/config/config.yaml`，更新 `paths.project_root`：

```yaml
paths:
  project_root: "/your/actual/project/path/Weaver"
  framework_root: "${paths.project_root}/src"
  workspace_root: "${paths.project_root}/workspaces"
```

### 运行您的第一个工作流

#### 方式一：命令行（单次运行）

```bash
# 列出可用的工作流
python -m src.main --list

# 运行指定工作流
python -m src.main --run hulatang

# 运行默认工作流
python -m src.main
```

#### 方式二：Python脚本（Keep-Alive会话）⭐ 推荐

创建 `run_workflow.py`：

```python
from src.main import FastAntsSession

# 使用上下文管理器自动清理
with FastAntsSession() as session:
    # 运行工作流
    result = session.run_workflow("hulatang")
    
    # 查看会话信息
    info = session.get_session_info()
    print(f"会话信息: {info}")
    
    # 在同一会话中运行多个工作流
    # result2 = session.run_workflow("collaboration")
```

运行：

```bash
python run_workflow.py
```

#### 方式三：交互式Python

```python
from src.main import FastAntsSession

# 创建会话
session = FastAntsSession()

# 运行工作流
result = session.run_workflow("hulatang")

# 查看结果
print(f"成功: {result.success}")
print(f"总轮次: {result.total_turns}")
print(f"使用的Agent: {result.agents_used}")

# 清理（可选）
session.cleanup_workflow("hulatang")
```

---

## 📁 项目结构

```
Weaver/
├── src/                          # 源代码
│   ├── main.py                   # 主入口，FastAntsSession
│   ├── config/                   # 配置管理
│   │   ├── config.yaml          # 主配置文件
│   │   └── app_config.py        # 配置加载器
│   ├── core/                     # 核心组件
│   │   ├── workflow_factory.py   # 工作流工厂
│   │   ├── workflow_base.py      # 工作流基类
│   │   ├── workflow_state.py    # 状态定义
│   │   └── config_workflow.py   # 配置驱动工作流
│   ├── engines/                  # 执行引擎
│   │   └── langgraph_engine.py  # LangGraph引擎
│   ├── services/                 # 服务层
│   │   ├── agent_service.py     # Agent服务
│   │   ├── environment_service.py # 环境服务
│   │   └── evaluators/          # 条件评估器
│   ├── workflows/                # 工作流定义
│   │   ├── hulatang/            # 示例：PPT制作工作流
│   │   │   ├── workflow.yaml   # 工作流配置
│   │   │   └── router.py       # 自定义路由器（可选）
│   │   └── guide.py            # 协作规范
│   ├── decorators/               # 装饰器
│   ├── diagnostics/             # 日志和诊断
│   └── requirements.txt         # Python依赖
├── workspaces/                   # 工作空间目录
│   └── {workflow_name}/         # 每个工作流的独立工作空间
│       ├── collab/              # 共享交付物
│       └── {agent_name}/        # Agent私有目录
├── aider/                        # Aider集成（本地）
└── README.md                     # 本文档
```

---

## 📝 工作流配置示例

工作流通过YAML文件定义。以下是 `src/workflows/hulatang/workflow.yaml` 的示例：

```yaml
name: "hulatang"
description: "PPT制作工作流：自然对话协作模式"
initial_message: "制作一份关于胡辣汤的宣传PPT"
max_turns: 10

# Agent定义
agents:
  - name: "client"
    type: "coder"
  - name: "supplier"
    type: "coder"

# 状态机定义
states:
  - name: "client_request"
    agent: "client"
    start: true
    prompt: |
      【role】：你是甲方（需求方）。
      【任务目标】：{{initial_message}}
      请提出你的需求，并创建需求文档：
      - 包括：PPT主题、页面数量、风格要求、重点内容、特殊要求
      【decisions字段说明】：
      {
        "decisions": {
          "request_complete": true  // true: 需求描述已完成；false: 还需要继续补充
        }
      }
    transitions:
      - to: "supplier_discuss"
        condition: "request_complete"
  
  - name: "supplier_discuss"
    agent: "supplier"
    prompt: |
      【role】：你是乙方（开发者/设计师）。
      甲方说：{{last_agent_content}}
      请与甲方讨论PPT设计方案，确认需求细节。
      【decisions字段说明】：
      {
        "decisions": {
          "design_confirmed": false,  // true: 双方已达成一致
          "ready_to_build": false     // true: 已具备开发所需的所有信息
        }
      }
    transitions:
      - to: "client_discuss"
        condition: "NOT (design_confirmed AND ready_to_build)"
      - to: "supplier_create"
        condition: "design_confirmed AND ready_to_build"

  # ... 更多状态定义

# 全局退出条件
exit_conditions:
  - condition: "max_turns_exceeded"
    action: "force_end"
  - condition: "error_occurred"
    action: "save_and_end"
```

---

## 🎨 创建自定义工作流

> 📖 **详细的工作流工程指南，请参见 [工作流开发指南](docs/WORKFLOW_GUIDE_CN.md)**

### 步骤1：创建工作流目录

```bash
mkdir -p src/workflows/my_workflow
```

### 步骤2：创建 `workflow.yaml`

按照上面的示例定义您的工作流。关键组件包括：

- **`name`**：唯一的工作流标识符
- **`agents`**：参与工作流的Agent列表
- **`states`**：状态机定义，包含提示和转移条件
- **`exit_conditions`**：工作流终止的全局条件

### 步骤3：（可选）创建自定义路由器

对于复杂的条件评估逻辑，创建 `router.py`：

```python
from ...core.router_base import BaseRouter

class MyWorkflowRouter(BaseRouter):
    def evaluate_condition(self, condition: str, context: dict) -> bool:
        # 自定义条件评估逻辑
        if condition == "custom_check":
            return context.get("some_field") == "expected_value"
        return super().evaluate_condition(condition, context)
```

### 步骤4：运行您的工作流

```python
from src.main import FastAntsSession

with FastAntsSession() as session:
    result = session.run_workflow("my_workflow")
```

---

## 🔧 配置参考

### 主配置 (`src/config/config.yaml`)

```yaml
paths:
  project_root: "/path/to/project"  # 必须更新
  workspace_root: "${paths.project_root}/workspaces"

aider:
  model: "openai/glm-4.6"           # AI模型名称
  api_key: ${oc.env:OPENAI_API_KEY} # 从环境变量读取
  api_base: ${oc.env:OPENAI_API_BASE}

workflow:
  max_turns: 6                       # 默认最大轮次
```

### 环境变量

- `OPENAI_API_KEY`（必需）：您的API密钥
- `OPENAI_API_BASE`（可选）：API端点（默认为OpenAI）

---

## 📊 执行结果

工作流执行返回 `WorkflowResult` 对象：

```python
WorkflowResult(
    success: bool,              # 是否执行成功
    total_turns: int,           # 总轮次数
    agents_used: List[str],     # 使用的Agent列表
    final_content: str,         # 最终内容（从collab目录收集）
    metadata: dict              # 执行元数据（历史、错误等）
)
```

---

## 🐛 故障排查

### 配置文件未找到

确保 `src/config/config.yaml` 存在，并且 `paths.project_root` 设置正确。

### API密钥错误

检查 `.env` 文件或环境变量中的 `OPENAI_API_KEY` 是否正确设置。

### 工作流配置未找到

确保工作流配置文件位于 `src/workflows/{workflow_name}/workflow.yaml`。

### Agent执行失败

查看日志文件（通常在项目根目录）获取详细的错误信息。

---

## 🏗️ 架构

框架采用模块化架构：

```
┌─────────────────────────────────────────┐
│         FastAntsSession                 │
│  (Keep-Alive会话管理器)                  │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────┐
│ Environment │  │   Agent     │
│  Service    │  │  Service    │
└──────┬──────┘  └──────┬──────┘
       │                │
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │ WorkflowFactory│
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │ ConfigWorkflow │
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │ LangGraphEngine│
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │   LangGraph    │
       │  State Graph   │
       └────────────────┘
```

---

## 🤝 贡献

我们欢迎贡献！请查看我们的[贡献指南](CONTRIBUTING.md)了解详情。

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/sherkevin/Weaver.git
cd Weaver

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r src/requirements.txt

# 运行测试（如果有）
# pytest tests/
```

### 贡献指南

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '添加新功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 📚 文档

- [工作流开发指南](docs/WORKFLOW_GUIDE_CN.md) - 编写工作流 YAML 文件的完整指南
- [Workflow Development Guide (English)](docs/WORKFLOW_GUIDE.md) - Complete guide to writing workflow YAML files
- [配置参考](src/config/README.md)
- [API文档](docs/API.md)（即将推出）

---

## 🗺️ 路线图

- [ ] 工作流可视化Web UI
- [ ] 更多内置工作流模板
- [ ] 增强的监控仪表板
- [ ] 支持更多LLM提供商
- [ ] 工作流版本控制和回滚
- [ ] 分布式执行支持

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 强大的基于图的编排引擎
- [Aider](https://github.com/paul-gauthier/aider) - AI配对编程工具
- [LangChain](https://github.com/langchain-ai/langchain) - LLM应用框架

---

## ⭐ Star历史

如果您觉得这个项目有用，请考虑给它一个Star！⭐

---

<div align="center">

[报告Bug](https://github.com/sherkevin/Weaver/issues) • [请求功能](https://github.com/sherkevin/Weaver/issues) • [文档](docs/)

</div>

