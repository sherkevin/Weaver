"""
Agent服务 - 负责Agent的创建和管理
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..config import AppConfig
from ..agents import AiderAgentFactory
from ..core.workflow_base import Agent, WorkflowContext
from ..diagnostics.logging import get_logger
from ..decorators.error_handlers import agent_operation_error_handler

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

        self._agent_factory = AiderAgentFactory(
            model_name=model_name,
            api_base=api_base
        )

        # ✅ 新增：Agent实例缓存 {cache_key: agent_instance}
        # cache_key格式: "workflow_name:agent_name:workspace_path"
        self._active_agents: Dict[str, Any] = {}

    @agent_operation_error_handler
    def get_agent(
        self, 
        agent_name: str, 
        root_path: Path, 
        workspace_info: Any, 
        workflow_name: str = None, 
        agent_type: str = "coder"
    ) -> Any:
        """
        获取或创建 Agent 实例（核心 Keep-Alive 逻辑）

        Args:
            agent_name: Agent名称
            root_path: Agent工作目录
            workspace_info: 工作区信息
            workflow_name: 工作流名称（可选，用于区分不同工作流的同名Agent）
            agent_type: Agent类型，可选值: "coder", "architect", "ask"，默认"coder"

        Returns:
            Agent实例
        """
        cache_key = self._generate_cache_key(agent_name, workspace_info, workflow_name)

        # 1. 检查缓存中是否已有该 Agent
        if cache_key in self._active_agents:
            logger.debug(f"♻️  Reusing cached agent: {cache_key}")
            return self._active_agents[cache_key]

        # 2. 如果没有，则创建新实例
        logger.debug(f"🆕 Creating new agent instance: {cache_key} (type: {agent_type})")

        self._prepare_directories(root_path, workspace_info.collab_dir)
        fnames_list = self._gather_files(root_path, workspace_info.collab_dir)
        
        self._ensure_git_initialized(root_path, agent_name)

        # 3. 创建Agent实例
        # 不再切换CWD，而是依赖AiderAgentFactory正确处理路径
        agent = self._agent_factory.create_coder(
            root_path=root_path,
            fnames=fnames_list,
            agent_name=agent_name,
            type=agent_type
        )

        # 4. 存入缓存
        self._active_agents[cache_key] = agent
        return agent

    def _generate_cache_key(self, agent_name: str, workspace_info: Any, workflow_name: str = None) -> str:
        """生成Agent缓存键"""
        workspace_path = str(workspace_info.collab_dir.parent)
        return f"{workflow_name or 'default'}:{agent_name}:{workspace_path}"

    def _prepare_directories(self, agent_root: Path, collab_dir: Path) -> None:
        """准备必要的目录结构"""
        agent_root.mkdir(parents=True, exist_ok=True)
        collab_dir.mkdir(parents=True, exist_ok=True)

        # collab为空时放置占位，确保被索引
        if not any(collab_dir.iterdir()):
            (collab_dir / ".keep").touch(exist_ok=True)

    def _gather_files(self, agent_root: Path, collab_dir: Path) -> List[str]:
        """
        收集Agent需要感知的文件列表
        包括agent_root下的文件和collab_dir下的文件（通过软链路径）
        """
        # 关键修复：不要将 agent_root 本身加入文件列表，这会让 Aider 认为根目录是可编辑的
        # 也不要将 agent_root/collab 目录本身加入，只加入具体文件
        fnames_list = []

        # 1. 收集agent_root下的文件（排除collab，避免重复或死循环）
        # 注意：rglob("*") 会递归遍历所有子目录，包括软链指向的目录（如果 follow_symlinks=True，默认是 False 但行为取决于 OS）
        # 我们显式排除路径中包含 "collab" 的文件，防止重复添加
        for path in agent_root.rglob("*"):
            if path.is_file():
                try:
                    rel = path.relative_to(agent_root)
                    if "collab" in rel.parts:
                        continue
                    fnames_list.append(str(path))
                except ValueError:
                    continue

        # 2. 收集collab下的文件，但转换为通过软链访问的路径
        # 这里的 collab_dir 是真实的物理路径
        for path in collab_dir.rglob("*"):
            if path.is_file():
                try:
                    relative_path = path.relative_to(collab_dir)
                    
                    symlink_path = agent_root / "collab" / relative_path
                    fnames_list.append(str(symlink_path))
                except ValueError:
                    continue
        
        return fnames_list

    def _ensure_git_initialized(self, root_path: Path, agent_name: str) -> None:
        """确保Git仓库已初始化并配置"""
        if not (root_path / ".git").exists():
            # 使用 git -C 指定目录，避免切换目录
            os.system(f"git -C '{root_path}' init > /dev/null 2>&1")
            os.system(f"git -C '{root_path}' config user.email 'agent@mas-aider.ai'")
            os.system(f"git -C '{root_path}' config user.name '{agent_name}'")
            logger.info(f"🔧 Re-initialized Git repo in {root_path}")

    @agent_operation_error_handler
    def create_agents_for_workflow(
        self,
        context: WorkflowContext,
        workspace_info: Any,
        agent_configs: List[Dict[str, Any]]
    ) -> Dict[str, Agent]:
        """为工作流创建或复用Agent实例"""
        agents = {}
        for agent_config in agent_configs:
            agent_name = agent_config["name"]
            agent_type = agent_config.get("type", "coder")
            agent_root = workspace_info.agent_dirs[agent_name]

            agent = self.get_agent(
                agent_name=agent_name,
                root_path=agent_root,
                workspace_info=workspace_info,
                workflow_name=context.workflow_name,
                agent_type=agent_type
            )
            agents[agent_name] = agent
        return agents

    @agent_operation_error_handler
    def clear_agents_for_workflow(self, workflow_name: str):
        """清理特定工作流的Agent缓存"""
        keys_to_remove = [k for k in self._active_agents.keys()
                         if k.startswith(f"{workflow_name}:")]

        for key in keys_to_remove:
            agent = self._active_agents[key]
            if hasattr(agent, 'cleanup'):
                # 这里我们保留try-catch，因为cleanup失败不应阻止其他清理
                # 但我们可以考虑将其封装到另一个方法中，或者接受这里的例外
                try:
                    agent.cleanup()
                except Exception as e:
                    logger.warning(f"Failed to cleanup agent {key}: {e}")
            del self._active_agents[key]

        if keys_to_remove:
            logger.info(f"🧹 Cleaned up {len(keys_to_remove)} agents for workflow '{workflow_name}'")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_cached = len(self._active_agents)
        workflow_stats = {}
        for cache_key in self._active_agents.keys():
            workflow_name = cache_key.split(':')[0]
            workflow_stats[workflow_name] = workflow_stats.get(workflow_name, 0) + 1

        return {
            "total_cached_agents": total_cached,
            "agents_by_workflow": workflow_stats,
            "cache_keys": list(self._active_agents.keys())
        }

    @agent_operation_error_handler
    def get_agent_for_workflow(self, agent_name: str, context) -> Any:
        """为工作流获取Agent实例"""
        workspace_info = context.metadata.get("workspace_info")
        if not workspace_info:
            raise ValueError("Workspace info not found in context")

        agent_dir = workspace_info.agent_dirs.get(agent_name)
        if not agent_dir:
            raise ValueError(f"Agent directory not found for {agent_name}")

        return self.get_agent(
            agent_name=agent_name,
            root_path=agent_dir,
            workspace_info=workspace_info,
            workflow_name=context.workflow_name,
            agent_type="coder"
        )

    def parse_agent_response(self, response: str) -> Dict[str, Any]:
        """解析Agent响应"""
        # 尝试使用更健壮的方式提取JSON
        starts = [i for i, char in enumerate(response) if char == '{']
        parsed = None
        json_str = ""
        
        for start in reversed(starts):
            try:
                obj, end = json.JSONDecoder().raw_decode(response[start:])
                # 这里我们放宽条件，只要是字典且包含decisions即可，或者甚至不包含decisions也可以？
                # 为了保持一致性，我们优先寻找包含decisions的JSON
                if isinstance(obj, dict) and "decisions" in obj:
                    parsed = obj
                    json_str = response[start:start+end]
                    break
            except json.JSONDecodeError:
                continue
        
        if parsed:
            if "content" not in parsed:
                parsed["content"] = response.replace(json_str, "").strip()
            if not parsed["content"]:
                parsed["content"] = response
            return parsed

        # Fallback: 尝试正则匹配任何JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                if "content" not in parsed:
                    parsed["content"] = response.replace(json_match.group(), "").strip()
                if "decisions" not in parsed:
                    parsed["decisions"] = {}
                return parsed
            except json.JSONDecodeError:
                pass

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
