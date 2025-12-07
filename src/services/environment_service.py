"""
环境服务 - 负责工作区管理和文件系统操作
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

from ..config import AppConfig
from ..decorators.error_handlers import safe_operation
from ..diagnostics.logging import get_logger

logger = get_logger()


@dataclass
class WorkspaceInfo:
    """工作区信息"""
    base_dir: Path
    workflow_dir: Path
    collab_dir: Path
    agent_dirs: Dict[str, Path]  # 动态agent目录

    def get_agent_paths(self) -> Dict[str, Path]:
        """获取所有Agent路径"""
        return self.agent_dirs.copy()


class EnvironmentService:
    """
    环境服务类

    负责：
    - 工作区初始化和清理
    - 文件系统操作
    - Git仓库初始化
    - 软链接创建
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self._workspace_info: WorkspaceInfo = None
        self.logger = logger  # For safe_operation decorator

    def setup_workspace_for_workflow(
        self,
        workflow_name: str,
        agent_names: List[str]
    ) -> WorkspaceInfo:
        """
        为指定工作流设置工作区

        Args:
            workflow_name: 工作流名称
            agent_names: Agent名称列表

        Returns:
            WorkspaceInfo: 工作区信息
        """
        paths = self.config.get_workspace_paths(workflow_name, agent_names)

        # 确保工作流目录存在（持久化，不清理）
        self._ensure_workflow_directory(paths)

        # 创建目录结构
        self._create_directories(paths, agent_names)

        # 初始化Git仓库
        if self.config.environment.initialize:
            self._init_git_repos(paths, agent_names)

        # 创建软链接
        self._create_symlinks(paths, agent_names)

        # collab目录已创建，Agent可以自主创建文件

        # 创建工作区信息
        self._workspace_info = WorkspaceInfo(
            base_dir=paths["workspace"],
            workflow_dir=paths["workflow_dir"],
            collab_dir=paths["collab_dir"],
            agent_dirs={name: paths[f"agent_{name}_dir"] for name in agent_names}
        )

        print(f"✅ Workspace initialized at {paths['workflow_dir']}")
        return self._workspace_info

    def get_workspace_info(self) -> WorkspaceInfo:
        """获取工作区信息"""
        if self._workspace_info is None:
            raise RuntimeError("Workspace not initialized. Call setup_workspace_for_workflow() first.")
        return self._workspace_info

    def get_collab_content(self) -> str:
        """获取collab目录的所有内容"""
        workspace_info = self.get_workspace_info()
        collab_dir = workspace_info.collab_dir
        all_files_content = []

        # 收集collab目录下所有文件的内容
        for file_path in collab_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):  # 跳过隐藏文件
                try:
                    content = file_path.read_text(encoding='utf-8')
                    relative_path = file_path.relative_to(collab_dir)
                    all_files_content.append(f"=== {relative_path} ===\n{content}")
                except Exception as e:
                    relative_path = file_path.relative_to(collab_dir)
                    all_files_content.append(f"=== {relative_path} ===\n[无法读取文件: {e}]")

        return "\n\n".join(all_files_content) if all_files_content else "collab目录为空"

    def _ensure_workflow_directory(self, paths: Dict[str, Path]) -> None:
        """确保工作流目录存在（持久化，不清理现有内容）"""
        workflow_dir = paths["workflow_dir"]
        if not workflow_dir.exists():
            workflow_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created workflow directory: {workflow_dir}")

    def _create_directories(self, paths: Dict[str, Path], agent_names: List[str]) -> None:
        """创建目录结构"""
        directories = [
            paths["collab_dir"],
            *[paths[f"agent_{name}_dir"] for name in agent_names]
        ]

        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                print(f"📁 Created directory: {directory}")
        # collab 目录占位，避免空目录被跳过
        collab_dir = paths["collab_dir"]
        if collab_dir.exists() and not any(collab_dir.iterdir()):
            (collab_dir / ".keep").touch(exist_ok=True)

    def _init_git_repos(self, paths: Dict[str, Path], agent_names: List[str]) -> None:
        """初始化Git仓库"""
        agent_dirs = [paths[f"agent_{name}_dir"] for name in agent_names]

        for agent_dir in agent_dirs:
            if not (agent_dir / ".git").exists():
                self._init_single_git_repo(agent_dir)

    @safe_operation(log_error=True)
    def _init_single_git_repo(self, agent_dir: Path) -> None:
        """初始化单个Git仓库"""
        os.system(f"git init '{agent_dir}' > /dev/null 2>&1")
        # 配置git用户，防止commit失败
        os.system(f"cd '{agent_dir}' && git config user.email 'agent@mas-aider.ai'")
        os.system(f"cd '{agent_dir}' && git config user.name 'MasAider Agent'")
        print(f"🔧 Initialized Git repo: {agent_dir}")

    def _create_symlinks(self, paths: Dict[str, Path], agent_names: List[str]) -> None:
        """创建软链接到collab目录"""
        collab_dir = paths["collab_dir"]
        agent_dirs = [paths[f"agent_{name}_dir"] for name in agent_names]

        for agent_dir in agent_dirs:
            self._create_single_symlink(agent_dir, collab_dir)

    @safe_operation(log_error=True)
    def _create_single_symlink(self, agent_dir: Path, collab_dir: Path) -> None:
        """创建单个软链接"""
        symlink_path = agent_dir / self.config.environment.collab.folder_name
        if symlink_path.exists() or symlink_path.is_symlink():
            if symlink_path.is_dir() and not symlink_path.is_symlink():
                shutil.rmtree(symlink_path)
            else:
                symlink_path.unlink()

        symlink_path.symlink_to(collab_dir.resolve(), target_is_directory=True)
        print(f"🔗 Created symlink: {symlink_path} -> {collab_dir}")

        # 校验软链指向
        if symlink_path.resolve() != collab_dir.resolve():
            print(f"⚠️  Symlink points to wrong target: {symlink_path} -> {symlink_path.resolve()}")

