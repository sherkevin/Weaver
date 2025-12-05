from functools import wraps
from typing import TypedDict, Annotated, List, Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 引入配置和记忆单例
from config import Config
from memory import MEMORY_SYSTEM

# ==============================================================================
# 1. 改良版中间件: 支持人设注入 (Persona Middleware)
# ==============================================================================

def with_persona_memory(persona_prompt: str):
    """
    这是一个工厂函数，返回一个装饰器。
    它不仅注入记忆，还注入当前 Agent 的特定人设。
    """
    def decorator(func):
        @wraps(func)
        def wrapper(state):
            messages = state["messages"]
            session_id = state.get("session_id", "default_class")
            
            # 1. 获取上一条消息
            last_msg = messages[-1]
            
            # --- 【核心修复 1】: 类型转换 ---
            # 如果上一条消息是 AI 生成的 (比如来自 Teacher)，那么对于当前的 Student 来说，
            # 这就是一条 "用户输入" (HumanMessage)。
            # 我们必须强转类型，否则 API 会报错 "1214" (因为它看到结尾是 assistant)
            current_input_content = last_msg.content
            if isinstance(last_msg, BaseMessage):
                 # 无论之前是什么类型，这一轮都视为 Human 输入
                current_input_msg = HumanMessage(content=current_input_content)
            else:
                current_input_msg = HumanMessage(content=str(last_msg))

            # 2. 调用 Memory 获取基础记忆上下文
            memory_context = MEMORY_SYSTEM.get_augmented_prompt(session_id, current_input_content)
            
            # --- 【核心修复 2】: 合并 System Message ---
            # 智谱 API 可能不支持多个 SystemMessage，建议合并为一个
            combined_system_prompt = f"""
{memory_context}

=== 当前角色设定 ===
{persona_prompt}
"""

            # 3. 构造复合 Prompt
            # 结构: [System(记忆+人设), Human(对手的话)]
            augmented_messages = [
                SystemMessage(content=combined_system_prompt), 
                current_input_msg 
            ]
            
            # 4. 执行节点
            temp_state = state.copy()
            temp_state["messages"] = augmented_messages
            response_dict = func(temp_state)
            
            # 5. 异步存档
            ai_msg = response_dict["messages"][-1]
            MEMORY_SYSTEM.save_interaction_async(
                session_id, 
                current_input_content, 
                ai_msg.content
            )
            
            return response_dict
        return wrapper
    return decorator


# ==============================================================================
# 2. 定义状态与 LLM
# ==============================================================================

class ClassState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    turn_count: int

# 使用智谱 GLM-4
llm = ChatOpenAI(
    model="glm-4", 
    temperature=0.7, # 稍微调高一点，增加讨论的创造性
    api_key=Config.CHAT_API_KEY,
    base_url=Config.CHAT_API_BASE
)

# ==============================================================================
# 3. 定义 Agent 节点 (Student & Teacher)
# ==============================================================================

# --- 学生 Agent ---
STUDENT_PERSONA = """
你叫小明，是清华大学计算机系的一名研究生。
你非常好奇，对人工智能的未来既充满憧憬又感到困惑。
请用简短、犀利的方式向老师提问或发表观点。
不要长篇大论，每次只抛出一个核心观点或问题。
"""

@with_persona_memory(STUDENT_PERSONA)
def student_node(state: ClassState):
    return {"messages": [llm.invoke(state["messages"])]}


# --- 老师 Agent ---
TEACHER_PERSONA = """
你叫王教授，是一位资深的人工智能专家，图灵奖得主。
你的教学风格循循善诱，喜欢用历史案例和哲学思考来启发学生。
请回答学生的疑问，并指出他思维中的漏洞。

【重要规则】
如果学生表现出深刻的洞察力和总结力而不只是问问题，请在回复的最后加上 " [GRADUATED] " (包含方括号)。
这表示你认为他已经出师了，可以结束今天的课程。
"""

@with_persona_memory(TEACHER_PERSONA)
def teacher_node(state: ClassState):
    response = llm.invoke(state["messages"])
    
    # 增加轮次计数
    current_turn = state.get("turn_count", 0) + 1
    return {
        "messages": [response], 
        "turn_count": current_turn
    }


# ==============================================================================
# 4. 构建图逻辑 (Router)
# ==============================================================================

# ... (Imports 保持不变)

# --- 学生 Agent ---
STUDENT_PERSONA = """
你叫小明，是清华大学计算机系的一名研究生。
你对 AI 的未来充满好奇，但你的思维还不够成熟，容易陷入技术乐观主义或过度的悲观主义。
请针对老师的观点提出具体的追问或反驳。
每次发言控制在 100 字以内，不要长篇大论，要像在聊天一样自然。
"""

@with_persona_memory(STUDENT_PERSONA)
def student_node(state: ClassState):
    return {"messages": [llm.invoke(state["messages"])]}


# --- 老师 Agent ---
TEACHER_PERSONA = """
你叫王教授，是一位严厉但充满智慧的人工智能专家，图灵奖得主。
你的教学风格是苏格拉底式的——你很少直接给出答案，而是通过不断的反问和质疑来逼迫学生思考。

【教学规则】
1. 不要轻易赞同学生：即使学生说得有道理，你也要找出他思维中的漏洞或极端情况进行反驳。
2. 控制节奏：不要急于总结。现在的讨论才刚刚开始，你需要引导学生往更深、更具体的伦理或技术细节去争论。
3. 禁止早期毕业：在前 5 轮交互中，绝对不要认为学生已经出师。
4. 毕业标准：只有当学生能够完美防御你的刁钻提问，并提出超越常人的建设性方案时，你才会在回复最后加上 " [GRADUATED] "。
"""

@with_persona_memory(TEACHER_PERSONA)
def teacher_node(state: ClassState):
    response = llm.invoke(state["messages"])
    current_turn = state.get("turn_count", 0) + 1
    return {
        "messages": [response], 
        "turn_count": current_turn
    }


def router(state: ClassState) -> Literal["student", "__end__"]:
    messages = state["messages"]
    last_msg = messages[-1]
    turn = state.get("turn_count", 0)
    
    # 强制结束
    if turn >= 20:
        print("\n=== 系统提示: 已达到最大交互轮次 (20) ===")
        return END
        
    # 判断出师
    if "[GRADUATED]" in last_msg.content:
        # 增加硬锁：必须聊够 5 轮
        if turn < 5:
            # print(f"  [DEBUG] 老师试图结束，但轮次({turn})不足，强制继续...")
            return "student"
        
        print("\n=== 系统提示: 老师认为学生已出师 ===")
        return END
    
    return "student"


workflow = StateGraph(ClassState)

workflow.add_node("student", student_node)
workflow.add_node("teacher", teacher_node)

# 流程: Start -> Student(发问) -> Teacher(回答) -> 判断是否结束 -> Loop Student
workflow.add_edge(START, "student")
workflow.add_edge("student", "teacher")
workflow.add_conditional_edges(
    "teacher",
    router
)

app = workflow.compile()


# ==============================================================================
# 5. 运行模拟
# ==============================================================================

if __name__ == "__main__":
    Config.validate()
    
    # 这个 Session ID 将承载他们的共同记忆
    # 如果你多次运行，他们会记得“上次课我们聊到了...”
    SESSION_ID = "ai_philosophy_class_2025"
    
    print(f"=== AI 双人教学模拟 (Session: {SESSION_ID}) ===")
    print("角色: 小明 (Student) vs 王教授 (Teacher)")
    print("终止条件: 老师说出 [GRADUATED] 或 20轮交互\n")
    
    # 初始引子：由系统抛出一个话题，激活学生
    initial_input = HumanMessage(content="老师，我在想，如果大模型有了自我意识，人类该怎么办？")
    
    # 注意：LangGraph 的机制是 State 传递
    # 我们把初始话题放入 messages，Student 节点会看到这个 Input 并开始第一轮思考
    try:
        inputs = {
            "messages": [initial_input], 
            "session_id": SESSION_ID,
            "turn_count": 0
        }
        
        # 这里的 stream_mode="updates" 可以让我们实时看到每个 Agent 的输出
        for event in app.stream(inputs, stream_mode="updates"):
            for node_name, value in event.items():
                last_msg = value["messages"][-1]
                content = last_msg.content.replace("[GRADUATED]", "").strip()
                
                role_title = "🧑‍🎓 小明" if node_name == "student" else "👴 王教授"
                color = "\033[94m" if node_name == "student" else "\033[92m" # 蓝/绿
                reset = "\033[0m"
                
                print(f"\n{color}{role_title}:{reset}")
                print(f"{content}")
                
                # 稍微停顿一下，让输出更有节奏感
                import time
                time.sleep(1)
                
    except Exception as e:
        print(f"运行出错: {e}")