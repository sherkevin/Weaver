"""
工作流工厂 - 工厂模式 + 注册机制
"""

from typing import Dict, Type
from .workflow_base import BaseWorkflow, WorkflowContext
from .config_workflow import ConfigWorkflow


class WorkflowFactory:
    """
    工作流工厂类 - 工厂模式

    提供工作流的注册和创建机制，支持运行时动态创建不同类型的工作流
    """

    # 工作流注册表
    _registry: Dict[str, Type[BaseWorkflow]] = {}

    @classmethod
    def register(cls, workflow_name: str, workflow_class: Type[BaseWorkflow]) -> None:
        """
        注册工作流类

        Args:
            workflow_name: 工作流类型标识
            workflow_class: 工作流类
        """
        if not issubclass(workflow_class, BaseWorkflow):
            raise TypeError(f"{workflow_class} must inherit from BaseWorkflow")

        cls._registry[workflow_name] = workflow_class
        print(f"✅ Registered workflow: {workflow_name} -> {workflow_class.__name__}")

    @classmethod
    def unregister(cls, workflow_name: str) -> None:
        """
        注销工作流类

        Args:
            workflow_name: 工作流类型标识
        """
        if workflow_name in cls._registry:
            del cls._registry[workflow_name]
            print(f"✅ Unregistered workflow: {workflow_name}")

    @classmethod
    def create(cls, workflow_name: str, context: WorkflowContext, **kwargs) -> BaseWorkflow:
        """
        创建工作流实例

        优先尝试创建ConfigWorkflow（基于配置文件），如果没有配置文件则使用注册的类

        Args:
            workflow_name: 工作流类型
            context: 工作流上下文
            **kwargs: 额外的初始化参数

        Returns:
            BaseWorkflow: 工作流实例

        Raises:
            ValueError: 如果工作流类型未注册且没有配置文件
        """
        # 创建上下文，合并额外参数
        full_context = WorkflowContext(
            workflow_name=workflow_name,
            config=context.config,
            initial_message=context.initial_message,
            shared_files=context.shared_files or [],
            metadata={**context.metadata, **kwargs}
        )

        # 首先尝试创建ConfigWorkflow
        try:
            config_workflow = ConfigWorkflow(full_context)
            print(f"✅ Using config-driven workflow: {workflow_name}")
            return config_workflow
        except (FileNotFoundError, ImportError, ValueError) as e:
            print(f"⚠️  Config workflow not available ({e}), falling back to class-based workflow")

        # 如果ConfigWorkflow不可用，使用传统注册类
        if workflow_name not in cls._registry:
            available_types = list(cls._registry.keys())
            raise ValueError(
                f"Unknown workflow type: {workflow_name}. "
                f"Available types: {available_types}"
            )

        workflow_class = cls._registry[workflow_name]
        return workflow_class(full_context)

    @classmethod
    def get_available_workflows(cls) -> Dict[str, Type[BaseWorkflow]]:
        """
        获取所有可用的工作流

        Returns:
            Dict[str, Type[BaseWorkflow]]: 工作流类型到类的映射
        """
        return cls._registry.copy()

    @classmethod
    def is_registered(cls, workflow_name: str) -> bool:
        """
        检查工作流类型是否已注册

        Args:
            workflow_name: 工作流类型

        Returns:
            bool: 是否已注册
        """
        return workflow_name in cls._registry

    @classmethod
    def get_workflow_class(cls, workflow_name: str) -> Type[BaseWorkflow]:
        """
        获取工作流类

        Args:
            workflow_name: 工作流类型

        Returns:
            Type[BaseWorkflow]: 工作流类

        Raises:
            ValueError: 如果工作流类型未注册
        """
        if workflow_name not in cls._registry:
            raise ValueError(f"Workflow type not registered: {workflow_name}")

        return cls._registry[workflow_name]

    @classmethod
    def get_workflow_initial_message(cls, workflow_name: str) -> str:
        """
        获取工作流的初始消息
        
        Args:
            workflow_name: 工作流类型
            
        Returns:
            str: 初始消息
        """
        try:
            # 尝试从 ConfigWorkflow 获取
            dummy_context = WorkflowContext(
                workflow_name=workflow_name,
                config=None,
                initial_message=""
            )
            config_workflow = ConfigWorkflow(dummy_context)
            config = config_workflow.config
            return config.get("initial_message", f"Start {workflow_name} workflow")
        except:
            # 如果获取失败，返回默认消息
            return f"Start {workflow_name} workflow"
