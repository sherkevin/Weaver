"""
Agent服务 - 负责Agent的创建和管理
"""

from pathlib import Path
from typing import List, Dict, Any

from ..config import AppConfig
from ..agents import AiderAgentFactory
from ..core.workflow_base import Agent, WorkflowContext


class AgentService:
    """
    Agent服务类

    负责：
    - Agent实例的创建和管理
    - Agent配置的统一管理
    - 工作流上下文到Agent的映射
    """

    def __init__(self, config: AppConfig):
        self.config = config

        # 立即解析配置值，避免 OmegaConf 插值状态问题
        model_name = config.aider.model
        api_base = config.aider.api_base

        # 输出配置信息用于调试
        # from ..diagnostics.logging import get_logger
        # logger = get_logger()
        # logger.info("🔧 AgentService 配置信息:")
        # logger.info(f"   model_name: {model_name}")
        # logger.info(f"   api_base: {api_base}")
        # logger.info(f"   verbose_logging: {config.aider.verbose_logging}")
        # logger.info(f"   max_turns: {config.workflow.max_turns}")
        # logger.info(f"   project_root: {config.paths.project_root}")
        # logger.info(f"   framework_root: {config.paths.framework_root}")
        # logger.info(f"   workspace_root: {config.paths.workspace_root}")
        # logger.info(f"   collab_folder_name: {config.environment.collab.folder_name}")
        # logger.info(f"   initialize_git: {config.environment.initialize}")
        # logger.info(f"   aider_api_key: {config.aider.api_key}")

        self._agent_factory = AiderAgentFactory(
            model_name=model_name,
            api_base=api_base
        )

    def create_agents_for_workflow(
        self,
        context: WorkflowContext,
        workspace_info: Any,  # WorkspaceInfo
        agent_configs: List[Dict[str, Any]]
    ) -> Dict[str, Agent]:
        """
        为工作流创建Agent实例

        Args:
            context: 工作流上下文
            workspace_info: 工作区信息
            agent_configs: Agent配置列表 [{"name": "architect", "role": "架构师"}, ...]

        Returns:
            Dict[str, Agent]: Agent名称到实例的映射
        """
        agents = {}

        # 根据配置动态创建Agent
        for agent_config in agent_configs:
            agent_name = agent_config["name"]
            agent_role = agent_config.get("role", agent_name)

        # 让Agent可以访问整个collab目录下的所有文件
        # 使用通配符让Agent可以自由创建和编辑collab目录下的任何文件
        collab_pattern = str(workspace_info.collab_dir / "**/*")

        agent = self._agent_factory.create_coder(
            root_path=workspace_info.agent_dirs[agent_name],
            fnames=[collab_pattern],  # 可以使用collab目录下的所有文件
            agent_name=agent_role
        )

        agents[agent_name] = agent

        return agents

    def get_agent_for_workflow(self, agent_name: str, context) -> Any:
        """
        为工作流获取Agent实例

        Args:
            agent_name: Agent名称
            context: 工作流上下文

        Returns:
            Agent实例
        """
        # 从上下文中获取workspace信息
        workspace_info = context.metadata.get("workspace_info")
        if not workspace_info:
            raise ValueError("Workspace info not found in context")

        # 根据agent_name创建相应的Agent
        # 这里需要根据配置文件中的agent定义来创建
        # 暂时使用简单映射，后续可以从配置中读取

        # 删除错误的映射表
        # agent_mappings = {
        #     "architect": "agent_a",
        #     "developer": "agent_b",
        #     "reviewer": "agent_a",
        #     "fixer": "agent_b",
        #     "tester": "agent_a"
        # }

        # 直接使用 agent_name 作为 key
        agent_dir = workspace_info.agent_dirs.get(agent_name)

        if not agent_dir:
            raise ValueError(f"Agent directory not found for {agent_name}")

        # 让Agent可以访问整个collab目录下的所有文件
        collab_pattern = str(workspace_info.collab_dir / "**/*")

        # 创建Agent实例
        agent = self._agent_factory.create_coder(
            root_path=agent_dir,
            fnames=[collab_pattern],  # 可以使用collab目录下的所有文件
            agent_name=agent_name  # 使用传入的agent_name作为显示名称
        )

        return agent

    def parse_agent_response(self, response: str) -> Dict[str, Any]:
        """
        解析Agent响应，支持JSON格式的decisions字段

        Args:
            response: Agent原始响应

        Returns:
            Dict[str, Any]: 解析后的响应，包含content和decisions
        """
        import json
        import re

        # 尝试提取JSON部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                # 确保包含content和decisions字段
                if "content" not in parsed:
                    parsed["content"] = response.replace(json_match.group(), "").strip()
                if "decisions" not in parsed:
                    parsed["decisions"] = {}
                return parsed
            except json.JSONDecodeError:
                pass

        # 如果不是JSON格式，返回纯文本响应
        return {
            "content": response,
            "decisions": {}
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """获取Agent服务信息"""
        return {
            "factory_config": {
                "model_name": self.config.aider.model,
                "api_base": self.config.api_base
            }
        }
