"""
配置驱动的工作流 - 基于YAML配置的工作流实现
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml


from ..core.workflow_base import BaseWorkflow, WorkflowContext, WorkflowResult
from ..services.engines.state_machine_engine import StateMachineEngine


class ConfigWorkflow(BaseWorkflow):
    """
    配置驱动的工作流

    通过YAML配置文件定义工作流逻辑，完全解耦业务代码和框架代码
    """

    def __init__(self, context: WorkflowContext, config_path: Optional[str] = None):
        """
        初始化配置工作流

        Args:
            context: 工作流上下文
            config_path: 配置文件路径，如果为None则自动查找
        """
        super().__init__(context)
        self.config_path = config_path
        self.config = self._load_config()
        self.engine = None

    @property
    def workflow_name(self) -> str:
        """工作流类型"""
        return self.config.get("name", "config_workflow")

    def get_agent_configs(self) -> List[Dict[str, Any]]:
        """获取Agent配置"""
        agents = self.config.get("agents", [])
        return [{"name": agent["name"], "role": agent["role"]} for agent in agents]

    def execute(self) -> WorkflowResult:
        """
        执行配置驱动的工作流

        重写父类的execute方法，使用状态机引擎执行
        """
        try:
            # 1. 获取Agent配置并创建agents
            agent_configs = self.get_agent_configs()
            agent_names = [config["name"] for config in agent_configs]

            # 2. 设置工作环境
            env_service = self.context.metadata.get("env_service")
            workspace_info = env_service.setup_workspace_for_workflow(
                self.workflow_name,
                agent_names
            )
            self.context.metadata["workspace_info"] = workspace_info

            # 3. 创建Agent服务
            agent_service = self.context.metadata.get("agent_service")

            # 4. 初始化状态机引擎
            self.engine = StateMachineEngine(self.config, agent_service, env_service)

            # 5. 执行工作流
            initial_state = {
                "workflow_name": self.workflow_name,
                "workspace_info": workspace_info
            }

            result = self.engine.execute(self.context, initial_state)

            # 6. 构建标准结果格式
            return WorkflowResult(
                success=result.get("success", False),
                final_content=result.get("final_content", ""),
                total_turns=result.get("total_turns", 0),
                agents_used=result.get("agents_used", []),
                metadata=result.get("metadata", {})
            )

        except Exception as e:
            return WorkflowResult(
                success=False,
                final_content="",
                total_turns=0,
                agents_used=[],
                metadata={},
                error_message=str(e)
            )

    def build_graph(self):
        """配置工作流不需要构建图，由状态机引擎处理"""
        return None

    def get_initial_state(self):
        """配置工作流不需要初始状态，由状态机引擎处理"""
        return {}

    def _run_workflow(self):
        """配置工作流不需要_run_workflow，由状态机引擎处理"""
        return {}

    def _load_config(self) -> Dict[str, Any]:
        """
        加载工作流配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        # 如果指定了配置文件路径
        if self.config_path:
            config_path = Path(self.config_path)
        else:
            # 自动查找配置文件
            config_path = self._find_config_file()

        if not config_path or not config_path.exists():
            raise FileNotFoundError(f"Workflow config file not found: {config_path}")

        # 加载YAML配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        # 验证配置
        self._validate_config(config)

        return config

    def _find_config_file(self) -> Optional[Path]:
        """查找配置文件"""
        # 从项目根目录查找 (mas_aider目录)
        project_root = Path(__file__).parent.parent

        # 可能的配置文件位置
        possible_paths = [
            project_root / "config" / f"{self.context.workflow_name}.yaml",
            project_root / "config" / f"{self.context.workflow_name}.yml",
            project_root / "workflows" / f"{self.context.workflow_name}.yaml",
            project_root / "workflows" / f"{self.context.workflow_name}.yml",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _validate_config(self, config: Dict[str, Any]):
        """验证配置文件的正确性"""
        required_fields = ["name", "agents", "states"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field in config: {field}")

        # 验证agents
        agents = config.get("agents", [])
        if not agents:
            raise ValueError("At least one agent must be defined")

        for agent in agents:
            if "name" not in agent or "role" not in agent:
                raise ValueError("Each agent must have 'name' and 'role' fields")

        # 验证states
        states = config.get("states", [])
        if not states:
            raise ValueError("At least one state must be defined")

        for state in states:
            if "name" not in state or "agent" not in state:
                raise ValueError("Each state must have 'name' and 'agent' fields")

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "name": self.config.get("name"),
            "description": self.config.get("description"),
            "agent_count": len(self.config.get("agents", [])),
            "state_count": len(self.config.get("states", [])),
            "exit_conditions": len(self.config.get("exit_conditions", []))
        }
