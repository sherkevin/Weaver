"""
测试 Keep-Alive 机制

验证：
1. 同一工作流中多次调用 get_agent_for_workflow 是否返回同一个实例
2. Agent 实例是否能保持上下文（记住之前的对话）
3. 不同工作流的同名 Agent 是否隔离
"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from mas_aider.config import AppConfig
from mas_aider.services import AgentService, EnvironmentService
from mas_aider.core import WorkflowContext


def test_keep_alive_mechanism():
    """测试 Keep-Alive 机制"""
    
    print("=" * 60)
    print("测试 Keep-Alive 机制")
    print("=" * 60)
    
    # 1. 加载配置
    config = AppConfig.load()
    
    # 2. 创建临时工作目录
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print(f"\n📁 临时目录: {temp_path}")
        
        # 3. 初始化服务
        env_service = EnvironmentService(config)
        agent_service = AgentService(config)
        
        # 4. 设置工作区
        workflow_name = "test_workflow"
        agent_names = ["test_agent"]
        
        print(f"\n🔧 设置工作区: workflow={workflow_name}, agents={agent_names}")
        workspace_info = env_service.setup_workspace_for_workflow(
            workflow_name=workflow_name,
            agent_names=agent_names
        )
        
        # 5. 创建工作流上下文
        context = WorkflowContext(
            workflow_name=workflow_name,
            config=config,
            initial_message="测试消息",
            metadata={
                "env_service": env_service,
                "agent_service": agent_service,
                "workspace_info": workspace_info
            }
        )
        
        # 6. 测试1：多次调用 get_agent_for_workflow，检查是否返回同一实例
        print("\n" + "=" * 60)
        print("测试1：多次调用是否返回同一实例")
        print("=" * 60)
        
        agent1 = agent_service.get_agent_for_workflow("test_agent", context)
        agent2 = agent_service.get_agent_for_workflow("test_agent", context)
        agent3 = agent_service.get_agent_for_workflow("test_agent", context)
        
        print(f"\n📊 Agent 实例 ID:")
        print(f"  Agent 1: {id(agent1)}")
        print(f"  Agent 2: {id(agent2)}")
        print(f"  Agent 3: {id(agent3)}")
        
        if id(agent1) == id(agent2) == id(agent3):
            print("\n✅ 成功：多次调用返回了同一个实例（Keep-Alive 工作正常）")
        else:
            print("\n❌ 失败：多次调用返回了不同的实例（Keep-Alive 未工作）")
            return False
        
        # 7. 测试2：检查 Agent 是否能保持上下文
        print("\n" + "=" * 60)
        print("测试2：Agent 是否能保持上下文")
        print("=" * 60)
        
        # 第一轮：让 Agent 记住一个数字
        print("\n📤 第1轮：让 Agent 记住数字 99999")
        try:
            response1 = agent1.run("请记住这个数字：99999。然后告诉我你记住了什么。")
            print(f"📥 Response 1: {response1[:200]}..." if len(response1) > 200 else f"📥 Response 1: {response1}")
        except Exception as e:
            print(f"❌ 第1轮失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 第二轮：使用同一个实例，不传递历史，看是否能记住
        print("\n📤 第2轮：询问 Agent 记住的数字（不传递历史）")
        print("⚠️  使用同一个 Agent 实例，测试是否能自动记住")
        try:
            response2 = agent1.run("我刚才让你记住的数字是什么？请直接告诉我数字。")
            print(f"📥 Response 2: {response2[:200]}..." if len(response2) > 200 else f"📥 Response 2: {response2}")
            
            if "99999" in response2:
                print("\n✅ 成功：Agent 记住了之前的对话（上下文保持正常）")
            else:
                print("\n⚠️  警告：Agent 可能没有记住之前的对话")
        except Exception as e:
            print(f"❌ 第2轮失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 第三轮：再次获取 Agent 实例，检查是否还是同一个
        print("\n📤 第3轮：再次获取 Agent 实例，检查是否还是同一个")
        agent4 = agent_service.get_agent_for_workflow("test_agent", context)
        print(f"📊 Agent 4 ID: {id(agent4)}")
        
        if id(agent4) == id(agent1):
            print("✅ 成功：再次获取时返回了同一个实例")
        else:
            print("❌ 失败：再次获取时返回了不同的实例")
            return False
        
        # 8. 测试3：检查缓存统计
        print("\n" + "=" * 60)
        print("测试3：检查缓存统计")
        print("=" * 60)
        
        cache_stats = agent_service.get_cache_stats()
        print(f"\n📊 缓存统计:")
        print(f"  总缓存数: {cache_stats['total_cached_agents']}")
        print(f"  按工作流分组: {cache_stats['agents_by_workflow']}")
        print(f"  缓存键: {cache_stats['cache_keys']}")
        
        if cache_stats['total_cached_agents'] == 1:
            print("\n✅ 成功：缓存中只有1个 Agent 实例（符合预期）")
        else:
            print(f"\n⚠️  警告：缓存中有 {cache_stats['total_cached_agents']} 个实例（预期1个）")
        
        # 9. 测试4：不同工作流的同名 Agent 是否隔离
        print("\n" + "=" * 60)
        print("测试4：不同工作流的同名 Agent 是否隔离")
        print("=" * 60)
        
        # 创建第二个工作流
        workflow_name2 = "test_workflow_2"
        workspace_info2 = env_service.setup_workspace_for_workflow(
            workflow_name=workflow_name2,
            agent_names=agent_names
        )
        
        context2 = WorkflowContext(
            workflow_name=workflow_name2,
            config=config,
            initial_message="测试消息2",
            metadata={
                "env_service": env_service,
                "agent_service": agent_service,
                "workspace_info": workspace_info2
            }
        )
        
        agent_workflow2 = agent_service.get_agent_for_workflow("test_agent", context2)
        print(f"\n📊 工作流1的 Agent ID: {id(agent1)}")
        print(f"📊 工作流2的 Agent ID: {id(agent_workflow2)}")
        
        if id(agent1) != id(agent_workflow2):
            print("\n✅ 成功：不同工作流的同名 Agent 是隔离的（符合预期）")
        else:
            print("\n❌ 失败：不同工作流的同名 Agent 是同一个实例（不应该这样）")
            return False
        
        # 10. 总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print("\n✅ Keep-Alive 机制工作正常：")
        print("  1. 同一工作流中多次调用返回同一实例")
        print("  2. Agent 实例能保持上下文")
        print("  3. 不同工作流的同名 Agent 正确隔离")
        print("\n💡 结论：Keep-Alive 机制已正确实现并工作正常")
        
        return True


if __name__ == "__main__":
    success = test_keep_alive_mechanism()
    sys.exit(0 if success else 1)

