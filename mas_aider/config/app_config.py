"""
应用配置管理
"""

from pathlib import Path
from typing import List, Any
from omegaconf import OmegaConf, DictConfig
from ..diagnostics.exceptions import ConfigurationError
from ..decorators.error_handlers import config_load_error_handler
from dotenv import load_dotenv

class AppConfig:
    """配置代理 - 完全配置驱动

    必需配置项：
    - paths.project_root: 项目根目录路径 (str)
    - paths.framework_root: 框架根目录路径 (str)
    - paths.workspace_root: 工作区根目录路径 (str)
    - environment.collab.folder_name: 协作目录名称 (str)
    - aider.model: AI模型名称 (str)
    - workflow.max_turns: 最大工作轮次 (int)

    可选配置项：
    - aider.api_base: 自定义API端点 (str, 可选)
    - aider.verbose_logging: 详细日志输出 (bool, 默认false)
    - environment.initialize: 是否初始化Git仓库 (bool, 默认true)
    """

    def __init__(self, config: DictConfig):
        """初始化配置代理

        Args:
            config: OmegaConf配置对象，包含所有配置项
        """
        self._config = config

    def __getattr__(self, name: str) -> Any:
        """动态属性访问

        支持通过属性访问配置项，例如：
        config.paths.project_root
        config.aider.model

        Args:
            name: 属性名

        Returns:
            配置项的值

        Raises:
            AttributeError: 当配置项不存在时
        """
        try:
            return getattr(self._config, name)
        except AttributeError:
            raise AttributeError(f"Configuration missing required item: '{name}'")

    @property
    def config(self) -> DictConfig:
        """获取完整的配置对象"""
        return self._config

    @classmethod
    @config_load_error_handler
    def load(cls) -> 'AppConfig':
        """
        加载配置 - 使用OmegaConf自动解析所有变量，装饰器处理异常

        Returns:
            AppConfig: 配置实例
        """
        # 0. 确保 .env 文件被加载
        cls._ensure_dotenv_loaded()

        # 1. 获取固定的配置文件路径
        config_path = cls._get_config_path()

        # 2. 验证文件存在（装饰器会处理异常）
        if not config_path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")

        # 3. 使用OmegaConf一键加载并自动解析所有变量（包括环境变量）
        # load_dotenv() 已加载.env文件，${oc.env:VAR_NAME} 会自动解析
        conf: DictConfig = OmegaConf.load(str(config_path))

        # 4. 创建配置代理实例
        return cls(conf)

    @classmethod
    def _ensure_dotenv_loaded(cls) -> None:
        """确保 .env 文件被加载"""
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)
       

    @classmethod
    def _get_config_path(cls) -> Path:
        """获取固定的配置文件路径"""
        return Path(__file__).parent / "config.yaml"

    def get_workspace_paths(self, workflow_name: str, agent_names: List[str]) -> dict[str, Path]:
        """获取工作区相关路径 - 支持动态agent

        Args:
            workflow_name: 工作流名称
            agent_names: Agent名称列表

        Returns:
            Dict[str, Path]: 包含工作区所有路径的字典
        """
        workspace_root = Path(self._config.paths.workspace_root)
        workflow_dir = workspace_root / workflow_name
        collab_dir = workflow_dir / self._config.environment.collab.folder_name

        paths = {
            "workspace": workspace_root,
            "workflow_dir": workflow_dir,
            "collab_dir": collab_dir
        }

        # 动态添加agent路径
        for agent_name in agent_names:
            paths[f"agent_{agent_name}_dir"] = workflow_dir / agent_name

        return paths
