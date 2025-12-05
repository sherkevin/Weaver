"""
多Agent系统主入口 - 重构版

使用依赖注入和工厂模式，解耦合main函数
"""

from pathlib import Path


def main(workflow_name: str):
    """
    主函数 - 简化的应用启动器

    职责：
    1. 配置加载
    2. 服务初始化
    3. 工作流创建和执行
    4. 结果输出

    Args:
        workflow_name: 工作流类型，默认为 "collaboration"
    """
    # 导入架构组件
    from .config import AppConfig
    from .services import EnvironmentService, AgentService
    from .core import WorkflowFactory, WorkflowContext
    from .diagnostics.logging import get_logger

    # 工作流注册由WorkflowFactory.create()方法处理，这里不需要手动注册

    # 1. 加载配置（从YAML + 环境变量）
    config = AppConfig.load()

    # 2. 初始化服务
    env_service = EnvironmentService(config)
    agent_service = AgentService(config)

    # 3. 创建工作流上下文（注意：不再提前设置workspace）
    # 根据工作流类型设置不同的初始消息
    # 获取初始消息（从配置中读取）
    initial_message = WorkflowFactory.get_workflow_initial_message(workflow_name)

    context = WorkflowContext(
        workflow_name=workflow_name,
        config=config,
        initial_message=initial_message,  # ✅ 从配置中获取
        metadata={
            "env_service": env_service,
            "agent_service": agent_service
        }
    )

    # 4. 使用工厂创建工作流
    workflow = WorkflowFactory.create(workflow_name, context)

    # 5. 执行工作流
    logger = get_logger()
    logger.log_execution_start(workflow_name)
    result = workflow.execute()

    # 6. 输出结果
    print_results(result)

    # 注意：现在工作区是持久化的，不再清理


def print_results(result) -> None:
    """输出执行结果"""
    from .diagnostics.logging import get_logger
    logger = get_logger()

    logger.info("="*60)
    logger.info("📊 WORKFLOW EXECUTION RESULTS")
    logger.info("="*60)

    if result.success:
        logger.info("✅ Status: SUCCESS")
        logger.info(f"🔄 Total Turns: {result.total_turns}")
        logger.info(f"🤖 Agents Used: {', '.join(result.agents_used)}")

        if result.final_content.strip():
            logger.info("📄 Final content generated successfully")
        else:
            logger.warning("⚠️ No content generated in shared file")
    else:
        logger.error("❌ Status: FAILED")
        if result.error_message:
            logger.error(f"💥 Error: {result.error_message}")

    # 显示额外元数据
    if result.metadata:
        logger.info("📋 Additional metadata available")

    logger.info("="*60)


def list_available_workflows() -> None:
    """列出所有可用的工作流"""
    from .core import WorkflowFactory
    from .diagnostics.logging import get_logger
    logger = get_logger()

    # 动态导入，避免相对导入问题
    try:
        import importlib.util

        # 导入collaboration_workflow
        spec = importlib.util.spec_from_file_location(
            "collaboration_workflow",
            Path(__file__).parent / "workflows" / "collaboration_workflow.py"
        )
        collaboration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(collaboration_module)
        WorkflowFactory.register("collaboration", collaboration_module.CollaborationWorkflow)
        logger.log_workflow_registered("collaboration")

        # 导入code_review_workflow
        spec = importlib.util.spec_from_file_location(
            "code_review_workflow",
            Path(__file__).parent / "workflows" / "code_review_workflow.py"
        )
        code_review_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(code_review_module)
        WorkflowFactory.register("code_review", code_review_module.CodeReviewWorkflow)
        logger.log_workflow_registered("code_review")

        # 导入testing_workflow
        spec = importlib.util.spec_from_file_location(
            "testing_workflow",
            Path(__file__).parent / "workflows" / "testing_workflow.py"
        )
        testing_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(testing_module)
        WorkflowFactory.register("testing", testing_module.TestingWorkflow)
        logger.log_workflow_registered("testing")

    except Exception as e:
        logger.error(f"Failed to load workflows: {e}")

    logger.info("Available workflows:")
    workflows = WorkflowFactory.get_available_workflows()
    for name, cls in workflows.items():
        logger.info(f"  - {name}: {cls.__name__}")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 当作为脚本运行时，确保可以导入相对模块
    sys.path.insert(0, str(Path(__file__).parent))

    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
        list_available_workflows()
        elif sys.argv[1] == "--run" and len(sys.argv) > 2:
            workflow_name = sys.argv[2]
            main(workflow_name)
        else:
            print("Usage: python -m mas_aider.main [--list | --run <workflow_name>]")
            print("Available workflow types: collaboration, hulatang")
    else:
        main()  # 默认运行 collaboration