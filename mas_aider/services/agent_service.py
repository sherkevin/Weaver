"""
Agent服务 - 负责Agent的创建和管理
"""

from pathlib import Path
from typing import List, Dict, Any

from ..config import AppConfig
from ..agents import AiderAgentFactory
from ..core.workflow_base import Agent, WorkflowContext
from ..diagnostics.logging import get_logger

logger = get_logger()


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

        # ✅ 新增：Agent实例缓存 {cache_key: agent_instance}
        # cache_key格式: "workflow_name:agent_name:workspace_path"
        self._active_agents: Dict[str, Any] = {}

    def get_agent(self, agent_name: str, root_path: Path, workspace_info: Any, workflow_name: str = None) -> Any:
        """
        获取或创建 Agent 实例（核心 Keep-Alive 逻辑）

        Args:
            agent_name: Agent名称
            root_path: Agent工作目录
            workspace_info: 工作区信息
            workflow_name: 工作流名称（可选，用于区分不同工作流的同名Agent）

        Returns:
            Agent实例
        """
        # 生成缓存键：包含工作流标识和Agent标识，确保隔离
        workspace_path = str(workspace_info.collab_dir.parent)
        cache_key = f"{workflow_name or 'default'}:{agent_name}:{workspace_path}"

        # 1. 检查缓存中是否已有该 Agent
        if cache_key in self._active_agents:
            existing_agent = self._active_agents[cache_key]
            # Aider的root是基于fnames模式设置的，而不是传入的root_path
            # 只要缓存键相同且Agent存在，就认为是同一个实例
            logger.debug(f"♻️  Reusing cached agent: {cache_key}")
            return existing_agent

        # 2. 如果没有，则创建新实例
        logger.debug(f"🆕 Creating new agent instance: {cache_key}")

        # 让Agent可以访问整个collab目录下的所有文件
        collab_pattern = str(workspace_info.collab_dir / "**/*")

        agent = self._agent_factory.create_coder(
            root_path=root_path,
            fnames=[collab_pattern],
            agent_name=agent_name
        )

        # 3. 存入缓存
        self._active_agents[cache_key] = agent
        return agent

    def create_agents_for_workflow(
        self,
        context: WorkflowContext,
        workspace_info: Any,  # WorkspaceInfo
        agent_configs: List[Dict[str, Any]]
    ) -> Dict[str, Agent]:
        """
        为工作流创建或复用Agent实例（支持Keep-Alive）

        Args:
            context: 工作流上下文
            workspace_info: 工作区信息
            agent_configs: Agent配置列表 [{"name": "architect", "role": "架构师"}, ...]

        Returns:
            Dict[str, Agent]: Agent名称到实例的映射
        """
        agents = {}

        for agent_config in agent_configs:
            agent_name = agent_config["name"]
            agent_role = agent_config.get("role", agent_name)

            # 获取Agent的工作目录
            agent_root = workspace_info.agent_dirs[agent_name]

            # ✅ 使用 get_agent 获取或复用实例
            agent = self.get_agent(
                agent_name=agent_name,
                root_path=agent_root,
                workspace_info=workspace_info,
                workflow_name=context.workflow_name
            )

            agents[agent_name] = agent

        return agents

    def clear_agents_for_workflow(self, workflow_name: str):
        """
        清理特定工作流的Agent缓存

        Args:
            workflow_name: 工作流名称
        """
        keys_to_remove = [k for k in self._active_agents.keys()
                         if k.startswith(f"{workflow_name}:")]

        for key in keys_to_remove:
            # 清理Agent实例（如果有cleanup方法）
            agent = self._active_agents[key]
            if hasattr(agent, 'cleanup'):
                try:
                    agent.cleanup()
                except Exception as e:
                    logger.warning(f"Failed to cleanup agent {key}: {e}")

            del self._active_agents[key]

        if keys_to_remove:
            logger.info(f"🧹 Cleaned up {len(keys_to_remove)} agents for workflow '{workflow_name}'")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 缓存统计数据
        """
        total_cached = len(self._active_agents)

        # 按工作流分组统计
        workflow_stats = {}
        for cache_key in self._active_agents.keys():
            workflow_name = cache_key.split(':')[0]
            workflow_stats[workflow_name] = workflow_stats.get(workflow_name, 0) + 1

        return {
            "total_cached_agents": total_cached,
            "agents_by_workflow": workflow_stats,
            "cache_keys": list(self._active_agents.keys())
        }

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
