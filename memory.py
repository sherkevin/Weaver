import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List

# 引入配置
from config import Config
from langchain_openai import OpenAIEmbeddings # 智谱兼容 OpenAI 接口
from langchain_chroma import Chroma
from langchain_core.documents import Document

class IndustrialMemory:
    def __init__(self, persist_dir="./industrial_memory_data"):
        # 1. 验证配置
        Config.validate()
        
        self.persist_dir = persist_dir
        if not os.path.exists(persist_dir):
            os.makedirs(persist_dir)

        self.executor = ThreadPoolExecutor(max_workers=2)

        # 2. SQL 初始化 (保持不变)
        self.conn = sqlite3.connect(f"{persist_dir}/exact_memory.db", check_same_thread=False)
        self._init_sql()

        # 3. Vector DB 初始化 (!!! 关键修改点 !!!)
        # 使用 Config 中的 Key 和 Base URL
        # 注意：智谱的 Embedding 模型通常叫 "embedding-2" 或 "embedding-3"
        self.embeddings = OpenAIEmbeddings(
            model="embedding-3", 
            openai_api_key=Config.CHAT_API_KEY,
            openai_api_base=Config.CHAT_API_BASE,
            check_embedding_ctx_length=False # 智谱有时候需要关闭这个检查
        )
        
        self.vector_store = Chroma(
            collection_name="semantic_memory",
            embedding_function=self.embeddings,
            persist_directory=f"{persist_dir}/chroma_db"
        )
        print(f"--- [System] 记忆模块已加载 (API: BigModel) ---")

    def _init_sql(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    # ... (get_augmented_prompt 和 save_interaction_async 方法保持不变，逻辑通用) ...
    
    def get_augmented_prompt(self, session_id: str, current_query: str) -> str:
        # (代码同之前，省略以节省篇幅)
        cursor = self.conn.execute(
            "SELECT role, content FROM chat_logs WHERE session_id=? ORDER BY id DESC LIMIT 10", 
            (session_id,)
        )
        recent_rows = cursor.fetchall()[::-1]
        recent_context = "\n".join([f"{row[0]}: {row[1]}" for row in recent_rows])

        vector_docs = self.vector_store.similarity_search(current_query, k=3)
        semantic_context = "\n".join([f"- {d.page_content}" for d in vector_docs])

        keyword_context = ""
        if any(char.isdigit() for char in current_query): 
            cursor = self.conn.execute(
                "SELECT content FROM chat_logs WHERE content LIKE ? AND session_id=? LIMIT 3",
                (f"%{current_query}%", session_id)
            )
            rows = cursor.fetchall()
            if rows:
                keyword_context = "\n".join([f"- {r[0]}" for r in rows])

        final_system_prompt = f"""
你是一个工业级 AI 助手。请基于以下多维度的记忆回答用户。

=== 🧠 长期语义记忆 (类似经验) ===
{semantic_context if semantic_context else "无"}

=== 🔍 精确关键词记录 (特定术语) ===
{keyword_context if keyword_context else "无"}

=== 💬 当前对话场景 (最近上下文) ===
{recent_context if recent_context else "（对话刚开始）"}

请忽略重复信息，基于上述背景回答用户最新的问题：
"""
        return final_system_prompt

    def save_interaction_async(self, session_id: str, user_input: str, ai_output: str):
        # (代码同之前，省略以节省篇幅)
        def _task():
            try:
                with self.conn:
                    self.conn.execute("INSERT INTO chat_logs (session_id, role, content) VALUES (?, ?, ?)",(session_id, "user", user_input))
                    self.conn.execute("INSERT INTO chat_logs (session_id, role, content) VALUES (?, ?, ?)",(session_id, "ai", ai_output))
                
                doc = Document(
                    page_content=f"User问: {user_input}\nAI答: {ai_output}",
                    metadata={"session_id": session_id, "timestamp": str(datetime.now())}
                )
                self.vector_store.add_documents([doc])
            except Exception as e:
                print(f"  [Error] 存档失败: {e}")
        self.executor.submit(_task)

# 单例导出
MEMORY_SYSTEM = IndustrialMemory()