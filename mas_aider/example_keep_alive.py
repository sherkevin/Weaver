#!/usr/bin/env python3
"""
MasAider Keep-Alive 使用示例

演示如何使用 MasAiderSession 保持 Agent 存活状态，实现连续工作流执行
"""

from mas_aider.main import MasAiderSession
import time


def example_keep_alive_usage():
    """
    基础使用示例：连续运行多个工作流，Agent保持存活
    """
    print("🚀 MasAider Keep-Alive 示例")
    print("=" * 50)

    # 1. 创建持久化会话（Agent开始存活）
    session = MasAiderSession(auto_cleanup=True)

    try:
        # 2. 第一次运行工作流
        print("\n📋 第一次执行：hulatang 工作流")
        result1 = session.run_workflow("hulatang")

        # Agent现在还活着！它们保持着对话历史和上下文
        print(f"✅ 工作流完成，结果: {getattr(result1, 'success', 'unknown')}")

        # 3. 短暂等待（模拟用户思考或外部处理）
        print("\n⏳ 模拟外部处理...")
        time.sleep(1)

        # 4. 第二次运行工作流（复用之前的Agent实例）
        print("\n📋 第二次执行：collaboration 工作流")
        result2 = session.run_workflow("collaboration")

        print(f"✅ 工作流完成，结果: {getattr(result2, 'success', 'unknown')}")

        # 5. 查看会话统计信息
        print("\n📊 会话统计:")
        info = session.get_session_info()
        print(f"  会话运行时间: {info['session_uptime']:.1f}秒")
        print(f"  缓存的Agent数量: {info['cached_agents']['total_cached_agents']}")
        print(f"  活跃工作流: {info['active_workflows']}")

    finally:
        # 会话结束时自动清理（如果auto_cleanup=True）
        print("\n🧹 会话结束，自动清理完成")


def example_context_manager():
    """
    上下文管理器使用示例
    """
    print("\n🔄 上下文管理器示例")
    print("=" * 30)

    with MasAiderSession() as session:
        print("📋 在上下文管理器中运行工作流")
        session.run_workflow("hulatang")
        print("✅ 工作流执行完毕")

    print("🧹 离开上下文，自动清理完成")


def example_manual_cleanup():
    """
    手动清理示例
    """
    print("\n🔧 手动清理示例")
    print("=" * 25)

    session = MasAiderSession(auto_cleanup=False)  # 禁用自动清理

    session.run_workflow("hulatang")
    session.run_workflow("collaboration")

    print("📊 清理前统计:")
    info = session.get_session_info()
    print(f"  活跃工作流: {info['active_workflows']}")
    print(f"  缓存Agent: {info['cached_agents']['total_cached_agents']}")

    # 手动清理特定工作流
    session.cleanup_workflow("hulatang")
    print("🧹 清理了 hulatang 工作流")

    # 查看清理后的状态
    info_after = session.get_session_info()
    print(f"  清理后活跃工作流: {info_after['active_workflows']}")
    print(f"  清理后缓存Agent: {info_after['cached_agents']['total_cached_agents']}")


def example_custom_config():
    """
    自定义配置文件示例
    """
    print("\n⚙️  自定义配置示例")
    print("=" * 20)

    session = MasAiderSession()

    # 使用自定义配置文件运行工作流
    custom_config = "/path/to/custom/workflow.yaml"
    print(f"📋 使用自定义配置: {custom_config}")

    # 注意：这只是示例，实际需要有效的配置文件路径
    # session.run_workflow("custom_workflow", custom_config_path=custom_config)


if __name__ == "__main__":
    print("MasAider Keep-Alive 使用示例")
    print("=" * 40)

    # 运行所有示例
    example_keep_alive_usage()
    example_context_manager()
    example_manual_cleanup()
    # example_custom_config()  # 需要有效配置文件

    print("\n🎉 所有示例运行完成！")
    print("\n💡 关键要点：")
    print("  • MasAiderSession 保持Agent存活")
    print("  • 同一个Agent实例可多次复用")
    print("  • 支持自动和手动清理")
    print("  • 上下文管理器确保资源释放")
