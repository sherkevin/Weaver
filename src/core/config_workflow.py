"""
配置驱动的工作流 - 基于YAML配置的工作流实现
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml


from ..core.workflow_base import BaseWorkflow, WorkflowContext, WorkflowResult
from ..engines.langgraph_engine import LangGraphEngine
from ..services.evaluators.condition_evaluator import UnifiedConditionEvaluator
from ..diagnostics.logging import get_logger
import importlib


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
        self.logger = get_logger()

    @property
    def workflow_name(self) -> str:
        """工作流类型"""
        return self.config.get("name", "config_workflow")

    def get_agent_configs(self) -> List[Dict[str, Any]]:
        """获取Agent配置"""
        agents = self.config.get("agents", [])
        return [{"name": agent["name"], "type": agent.get("type", "coder")} for agent in agents]

    def execute(self) -> WorkflowResult:
        """
        执行配置驱动的工作流

        使用LangGraph引擎执行，支持workflow router热拔插
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

            # 4. 加载workflow router（Convention over Configuration）
            workflow_router = self._load_workflow_router()
            
            # 5. 创建统一条件评估器（注入router）
            condition_evaluator = UnifiedConditionEvaluator(
                max_turns=self.config.get("max_turns", 10),
                workflow_router=workflow_router
            )

            # 6. 初始化LangGraph引擎
            self.engine = LangGraphEngine(
                self.config, 
                agent_service, 
                env_service,
                condition_evaluator
            )

            # 7. 执行工作流
            initial_state = {
                "workflow_name": self.workflow_name,
                "workspace_info": workspace_info
            }

            result = self.engine.execute(self.context, initial_state)

            # 8. 构建标准结果格式
            return WorkflowResult(
                success=result.get("success", False),
                final_content=result.get("final_content", ""),
                total_turns=result.get("total_turns", 0),
                agents_used=result.get("agents_used", []),
                metadata=result.get("metadata", {})
            )

        except Exception as e:
            self.logger.error(f"❌ Workflow execution failed: {e}", exc_info=True)
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
        # 从项目根目录查找 (src目录)
        project_root = Path(__file__).parent.parent

        # 可能的配置文件位置（优先workflow package）
        possible_paths = [
            # 新格式：workflow package内的workflow.yaml
            project_root / "workflows" / self.context.workflow_name / "workflow.yaml",
            project_root / "workflows" / self.context.workflow_name / "workflow.yml",
            # 兼容旧格式
            project_root / "config" / f"{self.context.workflow_name}.yaml",
            project_root / "config" / f"{self.context.workflow_name}.yml",
            project_root / "workflows" / f"{self.context.workflow_name}.yaml",
            project_root / "workflows" / f"{self.context.workflow_name}.yml",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None
    
    def _load_workflow_router(self) -> Optional[Any]:
        """
        自动发现并加载workflow router（Convention over Configuration）
        
        约定：
        - Router位置：workflows/{workflow_name}/router.py
        - Router类名：{WorkflowName}Router（驼峰式）
        
        Returns:
            Router实例或None（如果workflow没有自定义router）
        """
        workflow_name = self.context.workflow_name
        
        try:
            # 尝试导入 workflows.{workflow_name}.router
            module_path = f"workflows.{workflow_name}.router"
            module = importlib.import_module(module_path)
            
            # 约定：Router类名 = Pascal case of workflow_name + "Router"
            # 例如：hulatang -> HulatangRouter
            #      code_review -> CodeReviewRouter
            class_name = ''.join(word.capitalize() for word in workflow_name.split('_')) + "Router"
            
            router_class = getattr(module, class_name)
            router = router_class()
            
            self.logger.info(f"✅ Loaded workflow router: {class_name}")
            self.logger.info(f"   Available conditions: {router.list_conditions()}")
            
            return router
            
        except (ImportError, AttributeError) as e:
            # 没有router是正常的（简单workflow不需要）
            self.logger.debug(f"No router found for '{workflow_name}': {e}")
            return None
        except Exception as e:
            # 其他错误应该报警
            self.logger.warning(f"⚠️  Failed to load router for '{workflow_name}': {e}")
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
            if "name" not in agent:
                raise ValueError("Each agent must have 'name' field")
            
            # 验证type字段（如果提供）
            agent_type = agent.get("type", "coder")
            valid_types = ["coder", "architect", "ask"]
            if agent_type not in valid_types:
                raise ValueError(f"Invalid agent type '{agent_type}'. Valid types: {valid_types}")

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
