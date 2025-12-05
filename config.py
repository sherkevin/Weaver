import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    """
    统一配置管理类
    """
    # 智谱 Chat/Embedding 配置
    CHAT_API_KEY = os.getenv("CHAT_API_KEY")
    CHAT_API_BASE = os.getenv("CHAT_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
    
    # 智谱 Code 配置 (如果需要专用代码模型)
    CODE_API_KEY = os.getenv("CODE_API_KEY")
    CODE_API_BASE = os.getenv("CODE_API_BASE")
    
    # 其他配置
    HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")

    @classmethod
    def validate(cls):
        if not cls.CHAT_API_KEY:
            print("❌ 错误: 未找到 CHAT_API_KEY，请检查 .env 文件")
            sys.exit(1)

# 自动设置 HuggingFace 镜像环境变量 (如果使用本地模型下载)
os.environ["HF_ENDPOINT"] = Config.HF_ENDPOINT