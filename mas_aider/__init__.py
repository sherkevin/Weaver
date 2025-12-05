"""
多Agent系统 - 重构版

基于设计模式的模块化架构：
- 策略模式：不同工作流作为可插拔策略
- 工厂模式：创建工作流和Agent实例
- 模板方法：工作流执行框架
- 依赖注入：服务层解耦
"""

# 导入主要组件供外部使用
from .config import AppConfig
from .core import WorkflowFactory, WorkflowContext, WorkflowResult
from .services import EnvironmentService, AgentService

__version__ = "2.0.0"
__author__ = "AI Assistant"
