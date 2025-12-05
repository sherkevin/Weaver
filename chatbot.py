from functools import wraps
from typing import TypedDict, Annotated, List

# 引入配置
from config import Config
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 从 memory.py 导入实例化好的系统
from memory import MEMORY_SYSTEM

# ==============================================================================
# 模块 2: 中间件装饰器 (Middleware)
# ==============================================================================

def with_industrial_memory(func):
    @wraps(func)
    def wrapper(state):
        messages = state["messages"]
        session_id = state.get("session_id", "default_session")
        last_user_msg = messages[-1]
        
        # 调用 Memory 获取增强 Prompt
        system_prompt_content = MEMORY_SYSTEM.get_augmented_prompt(session_id, last_user_msg.content)
        
        # 注入增强的 System Prompt
        augmented_messages = [
            SystemMessage(content=system_prompt_content),
            last_user_msg
        ]
        
        # 执行业务节点
        temp_state = state.copy()
        temp_state["messages"] = augmented_messages
        response_dict = func(temp_state)
        
        # 触发后台存档
        ai_msg = response_dict["messages"][-1]
        MEMORY_SYSTEM.save_interaction_async(
            session_id, 
            last_user_msg.content, 
            ai_msg.content
        )
        
        return response_dict
    return wrapper


# ==============================================================================
# 模块 3: 用户工作流 (Workflow)
# ==============================================================================

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str

# !!! 关键修改点 !!!
# 初始化 LLM，使用 Config 中的配置
# model="glm-4" 是智谱当前的主力模型
llm = ChatOpenAI(
    model="glm-4", 
    temperature=0.3,
    api_key=Config.CHAT_API_KEY,
    base_url=Config.CHAT_API_BASE
)

@with_industrial_memory 
def chatbot_node(state: ChatState):
    return {"messages": [llm.invoke(state["messages"])]}

# 构建图
workflow = StateGraph(ChatState)
workflow.add_node("bot", chatbot_node)
workflow.add_edge(START, "bot")
workflow.add_edge("bot", END)

app = workflow.compile()


# ==============================================================================
# 模块 4: 运行演示
# ==============================================================================

if __name__ == "__main__":
    # 验证配置是否生效
    Config.validate()
    
    SESSION_ID = "machine_maintenance_team_001"
    
    print(f"\n=== 工业级记忆 Bot (Powered by GLM-4) ===")
    print(f"当前 Session: {SESSION_ID}")
    print("输入 'exit' 退出。\n")

    while True:
        user_in = input("User: ")
        if user_in.lower() in ["exit", "quit"]:
            break
            
        try:
            result = app.invoke({
                "messages": [HumanMessage(content=user_in)],
                "session_id": SESSION_ID
            })
            print(f"Bot:  {result['messages'][-1].content}")
            print("-" * 50)
        except Exception as e:
            print(f"❌ 调用出错: {e}")
            print("请检查网络连接或 API Key 是否正确。")