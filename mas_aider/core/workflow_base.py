"""
工作流基类 - 模板方法模式
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Protocol, Optional
from pathlib import Path
from dataclasses import dataclass

from langchain_core.messages import BaseMessage


class Agent(Protocol):
    """Agent协议接口"""
    def run(self, prompt: str) -> str:
        """执行任务"""
        ...


@dataclass
class WorkflowContext:
    """工作流上下文"""
    workflow_name: str
    config: Any  # AppConfig
    initial_message: str = "Start project"
    shared_files: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.shared_files is None:
            self.shared_files = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    success: bool
    final_content: str
    total_turns: int
    agents_used: List[str]
    metadata: Dict[str, Any]
    error_message: Optional[str] = None


class BaseWorkflow(ABC):
    """
    工作流基类 - 模板方法模式

    定义工作流执行的框架，具体实现由子类提供
    """

    def __init__(self, context: WorkflowContext):
        self.context = context
        self.agents: List[Agent] = []
        self._graph = None

    @property
    @abstractmethod
    def workflow_name(self) -> str:
        """工作流类型标识"""
        pass

    @abstractmethod
    def get_agent_configs(self) -> List[Dict[str, Any]]:
        """
        获取Agent配置 - 由子类实现

        Returns:
            List[Dict[str, Any]]: Agent配置列表
            例如: [{"name": "architect", "role": "架构师"}, {"name": "developer", "role": "开发者"}]
        """
        pass

    @abstractmethod
    def build_graph(self) -> Any:
        """
        构建工作流图 - 由子类实现

        Returns:
            Any: 工作流图实例 (StateGraph)
        """
        pass

    @abstractmethod
    def get_initial_state(self) -> Dict[str, Any]:
        """
        获取初始状态 - 由子类实现

        Returns:
            Dict[str, Any]: 初始状态字典
        """
        pass

    def execute(self) -> WorkflowResult:
        """
        执行工作流 - 模板方法

        这是一个模板方法，定义了工作流执行的整体框架。
        具体步骤由子类实现。
        """
        try:
            # 1. 获取Agent配置
            agent_configs = self.get_agent_configs()
            agent_names = [config["name"] for config in agent_configs]

            # 2. 设置工作环境
            env_service = self.context.metadata.get("env_service")
            workspace_info = env_service.setup_workspace_for_workflow(
                self.context.workflow_name,
                agent_names
            )

            # 3. 创建Agent
            agent_service = self.context.metadata.get("agent_service")
            agents_dict = agent_service.create_agents_for_workflow(
                self.context,
                workspace_info,
                agent_configs
            )

            # 按照配置顺序排列agents
            self.agents = [agents_dict[config["name"]] for config in agent_configs]

            # 4. 构建和执行工作流图
            self._graph = self.build_graph()
            result = self._run_workflow()

            return WorkflowResult(
                success=True,
                final_content=result.get("final_content", ""),
                total_turns=result.get("total_turns", 0),
                agents_used=[config["role"] for config in agent_configs],
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

    @abstractmethod
    def _run_workflow(self) -> Dict[str, Any]:
        """
        运行工作流的具体逻辑 - 由子类实现

        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    def _get_shared_file_path(self) -> str:
        """获取共享文件路径"""
        # 注意：现在需要在execute方法中获取workspace_info后才能调用此方法
        # 这里返回一个占位符，实际使用时需要从workspace_info获取
        env_service = self.context.metadata.get("env_service")
        if env_service:
            workspace_info = env_service.get_workspace_info()
            return str(workspace_info.shared_file)
        return ""

    def _log(self, message: str) -> None:
        """日志记录"""
        if self.context.config.aider.verbose_logging:
            print(f"[{self.workflow_name}] {message}")
