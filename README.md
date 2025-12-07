<div align="center">

<img src="pic/logo.png" alt="Weaver Logo" width="600"/>

# 🕷️ Weaver

**Weave workflows, ship code.**

*A powerful, configuration-driven framework for orchestrating multiple AI agents using LangGraph and Aider*

> **The Weaver (编织者)**: Unlike ants that swarm, the spider (Weaver) is solitary, highly intelligent, and excels at building complex structures (Web/Graph). It perfectly embodies LangGraph's form—weaving workflows, transforming code (threads) into software (fabric).

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Aider](https://img.shields.io/badge/Aider-integrated-purple.svg)](https://github.com/paul-gauthier/aider)

[Features](#-key-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Examples](#-examples) • [Contributing](#-contributing)

[English](README.md) | [中文](README_CN.md)

</div>

---

## 📖 Overview

<div align="center">

<img src="pic/framwork.png" alt="LangGraph + Aider Framework" width="600"/>

</div>

**Weaver** is an enterprise-grade framework that enables seamless collaboration between multiple AI agents through declarative YAML configurations. Built on top of LangGraph's powerful graph-based orchestration engine and Aider's code editing capabilities, it allows you to define complex multi-agent workflows without writing a single line of Python code.

### The Weaver Philosophy

Just as a spider weaves its web with precision and intelligence, Weaver helps you craft sophisticated multi-agent workflows. Each agent is like a thread, and together they form a robust fabric of software solutions. The framework's graph-based architecture mirrors the spider's web—complex, interconnected, and beautifully structured.

### Why This Framework?

- 🎯 **Zero-Code Workflow Definition**: Define complex agent collaboration flows using simple YAML files
- 🔄 **Production-Ready**: Built-in error handling, retry mechanisms, and comprehensive logging
- ⚡ **High Performance**: Agent caching and keep-alive sessions for optimal execution speed
- 🔌 **Extensible**: Plugin-based architecture with hot-swappable routers
- 🛡️ **Robust**: Complete state management, execution history, and error recovery

---

## ✨ Key Features

### 🎨 Configuration-Driven Workflows
- **Zero-code workflow definition** via YAML configuration files
- **Complete decoupling** of business logic from framework code
- **Hot-swappable routers** with Convention over Configuration support

### 🔀 LangGraph-Powered Orchestration
- **Graph-based state machines** for complex branching and loops
- **Flexible condition routing** with expressive condition evaluation
- **Complete state tracking** with execution history and recovery support

### 💾 Keep-Alive Session Management
- **Persistent sessions** via `FastAntsSession` to keep agents alive in memory
- **Intelligent agent caching** to avoid redundant initialization
- **Continuous workflow execution** within a single session

### 🔧 Deep Aider Integration
- **Powerful code editing** capabilities through Aider integration
- **Diff-based modifications** for precise file change tracking
- **Automatic Git integration** with version control support

### 📊 Comprehensive Monitoring
- **Unified error handling** with decorator-based retry mechanisms
- **Detailed logging system** with agent responses, state transitions, and errors
- **Execution history tracking** for debugging and auditing

### 🤝 Flexible Collaboration Patterns
- **Multi-agent collaboration** following defined workflows
- **Shared workspace** with isolated workspaces per workflow
- **Built-in collaboration guidelines** ensuring consistent agent output formats

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Git
- OpenAI API Key (or compatible API service)

### Installation

```bash
# Clone the repository
git clone https://github.com/sherkevin/Weaver.git
cd Weaver

# Install dependencies
pip install -r src/requirements.txt
```

### Configuration

1. **Set up environment variables**

Create a `.env` file in the `src/` directory:

```bash
cd src
cat > .env << EOF
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
EOF
```

Or export them directly:

```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_API_BASE="https://api.openai.com/v1"
```

2. **Configure project paths**

Edit `src/config/config.yaml` and update `paths.project_root`:

```yaml
paths:
  project_root: "/your/actual/project/path/Weaver"
  framework_root: "${paths.project_root}/src"
  workspace_root: "${paths.project_root}/workspaces"
```

### Run Your First Workflow

#### Option 1: Command Line (Single Run)

```bash
# List available workflows
python -m src.main --list

# Run a specific workflow
python -m src.main --run hulatang

# Run default workflow
python -m src.main
```

#### Option 2: Python Script (Keep-Alive Session) ⭐ Recommended

Create `run_workflow.py`:

```python
from src.main import FastAntsSession

# Use context manager for automatic cleanup
with FastAntsSession() as session:
    # Run workflow
    result = session.run_workflow("hulatang")
    
    # View session info
    info = session.get_session_info()
    print(f"Session Info: {info}")
    
    # Run multiple workflows in the same session
    # result2 = session.run_workflow("collaboration")
```

Run it:

```bash
python run_workflow.py
```

#### Option 3: Interactive Python

```python
from src.main import FastAntsSession

# Create session
session = FastAntsSession()

# Run workflow
result = session.run_workflow("hulatang")

# Check results
print(f"Success: {result.success}")
print(f"Total Turns: {result.total_turns}")
print(f"Agents Used: {result.agents_used}")

# Cleanup (optional)
session.cleanup_workflow("hulatang")
```

---

## 📁 Project Structure

```
Weaver/
├── src/                          # Source code
│   ├── main.py                   # Main entry point, FastAntsSession
│   ├── config/                   # Configuration management
│   │   ├── config.yaml          # Main config file
│   │   └── app_config.py        # Config loader
│   ├── core/                     # Core components
│   │   ├── workflow_factory.py   # Workflow factory
│   │   ├── workflow_base.py      # Base workflow class
│   │   ├── workflow_state.py    # State definitions
│   │   └── config_workflow.py   # Config-driven workflow
│   ├── engines/                  # Execution engines
│   │   └── langgraph_engine.py  # LangGraph engine
│   ├── services/                 # Service layer
│   │   ├── agent_service.py     # Agent service
│   │   ├── environment_service.py # Environment service
│   │   └── evaluators/          # Condition evaluators
│   ├── workflows/                # Workflow definitions
│   │   ├── hulatang/            # Example: PPT creation workflow
│   │   │   ├── workflow.yaml   # Workflow config
│   │   │   └── router.py       # Custom router (optional)
│   │   └── guide.py            # Collaboration guidelines
│   ├── decorators/               # Decorators
│   ├── diagnostics/             # Logging and diagnostics
│   └── requirements.txt         # Python dependencies
├── workspaces/                   # Workspace directory
│   └── {workflow_name}/         # Isolated workspace per workflow
│       ├── collab/              # Shared deliverables
│       └── {agent_name}/        # Private agent directories
├── aider/                        # Aider integration (local)
└── README.md                     # This file
```

---

## 📝 Workflow Configuration Example

Workflows are defined using YAML files. Here's an example from `src/workflows/hulatang/workflow.yaml`:

```yaml
name: "hulatang"
description: "PPT Creation Workflow: Natural Conversation Collaboration"
initial_message: "Create a promotional PPT about Hulatang"
max_turns: 10

# Agent definitions
agents:
  - name: "client"
    type: "coder"
  - name: "supplier"
    type: "coder"

# State machine definition
states:
  - name: "client_request"
    agent: "client"
    start: true
    prompt: |
      【role】：You are the client (requester).
      【task】：{{initial_message}}
      Please create a requirements document including:
      - PPT theme, number of pages, style requirements
      - Key content, special requirements
      【decisions】:
      {
        "decisions": {
          "request_complete": true  // true: ready to discuss; false: need more info
        }
      }
    transitions:
      - to: "supplier_discuss"
        condition: "request_complete"
  
  - name: "supplier_discuss"
    agent: "supplier"
    prompt: |
      【role】：You are the supplier (developer/designer).
      Client said: {{last_agent_content}}
      Please discuss the PPT design plan and confirm requirements.
      【decisions】:
      {
        "decisions": {
          "design_confirmed": false,  // true: agreement reached
          "ready_to_build": false     // true: ready to start coding
        }
      }
    transitions:
      - to: "client_discuss"
        condition: "NOT (design_confirmed AND ready_to_build)"
      - to: "supplier_create"
        condition: "design_confirmed AND ready_to_build"

  # ... more states

# Global exit conditions
exit_conditions:
  - condition: "max_turns_exceeded"
    action: "force_end"
  - condition: "error_occurred"
    action: "save_and_end"
```

---

## 🎨 Creating Custom Workflows

> 📖 **For detailed workflow engineering guide, see [Workflow Development Guide](docs/WORKFLOW_GUIDE.md)**

### Step 1: Create Workflow Directory

```bash
mkdir -p src/workflows/my_workflow
```

### Step 2: Create `workflow.yaml`

Define your workflow following the example above. Key components:

- **`name`**: Unique workflow identifier
- **`agents`**: List of agents participating in the workflow
- **`states`**: State machine definition with prompts and transitions
- **`exit_conditions`**: Global conditions for workflow termination

### Step 3: (Optional) Create Custom Router

For complex condition evaluation logic, create `router.py`:

```python
from ...core.router_base import BaseRouter

class MyWorkflowRouter(BaseRouter):
    def evaluate_condition(self, condition: str, context: dict) -> bool:
        # Custom condition evaluation logic
        if condition == "custom_check":
            return context.get("some_field") == "expected_value"
        return super().evaluate_condition(condition, context)
```

### Step 4: Run Your Workflow

```python
from src.main import FastAntsSession

with FastAntsSession() as session:
    result = session.run_workflow("my_workflow")
```

---

## 🔧 Configuration Reference

### Main Config (`src/config/config.yaml`)

```yaml
paths:
  project_root: "/path/to/project"  # Must be updated
  workspace_root: "${paths.project_root}/workspaces"

aider:
  model: "openai/glm-4.6"           # AI model name
  api_key: ${oc.env:OPENAI_API_KEY} # From environment variable
  api_base: ${oc.env:OPENAI_API_BASE}

workflow:
  max_turns: 6                       # Default max turns
```

### Environment Variables

- `OPENAI_API_KEY` (required): Your API key
- `OPENAI_API_BASE` (optional): API endpoint (defaults to OpenAI)

---

## 📊 Execution Results

Workflow execution returns a `WorkflowResult` object:

```python
WorkflowResult(
    success: bool,              # Whether execution succeeded
    total_turns: int,           # Total number of turns
    agents_used: List[str],     # List of agents used
    final_content: str,         # Final content (from collab directory)
    metadata: dict              # Execution metadata (history, errors, etc.)
)
```

---

## 🐛 Troubleshooting

### Configuration File Not Found

Ensure `src/config/config.yaml` exists and `paths.project_root` is correctly set.

### API Key Error

Check that `OPENAI_API_KEY` is correctly set in `.env` file or environment variables.

### Workflow Config Not Found

Ensure workflow config file is located at `src/workflows/{workflow_name}/workflow.yaml`.

### Agent Execution Failed

Check log files (usually in project root) for detailed error messages.

---

## 🏗️ Architecture

The framework follows a modular architecture:

```
┌─────────────────────────────────────────┐
│         FastAntsSession                 │
│  (Keep-Alive Session Manager)           │
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

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/sherkevin/Weaver.git
cd Weaver

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r src/requirements.txt

# Run tests (if available)
# pytest tests/
```

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📚 Documentation

- [Workflow Development Guide](docs/WORKFLOW_GUIDE.md) - Complete guide to writing workflow YAML files
- [Workflow Development Guide (中文)](docs/WORKFLOW_GUIDE_CN.md) - 工作流 YAML 编写完整指南
- [Configuration Reference](src/config/README.md)
- [API Documentation](docs/API.md) (Coming soon)

---

## 🗺️ Roadmap

- [ ] Web UI for workflow visualization
- [ ] More built-in workflow templates
- [ ] Enhanced monitoring dashboard
- [ ] Support for more LLM providers
- [ ] Workflow versioning and rollback
- [ ] Distributed execution support

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - Powerful graph-based orchestration
- [Aider](https://github.com/paul-gauthier/aider) - AI pair programming tool
- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

<div align="center">

**Made with ❤️ by the Weaver Team**

[Report Bug](https://github.com/sherkevin/Weaver/issues) • [Request Feature](https://github.com/sherkevin/Weaver/issues) • [Documentation](docs/)

</div>
