# agents.py
from pathlib import Path
from aider.coders import Coder, ArchitectCoder, AskCoder
from aider.models import Model
from aider.io import InputOutput

class AiderAgentFactory:
    def __init__(self, model_name="openai/glm-4.6", api_base=None):
        self.model_name = model_name
        import os
        if api_base:
            os.environ["OPENAI_BASE_URL"] = api_base

        # 创建Model实例
        self.model = Model(model_name)

        # 修改Aider的默认request_timeout从600秒增加到1800秒（30分钟）
        # 这样可以确保长回复任务有足够的时间完成
        import aider.models
        aider.models.request_timeout = 1800

    # Agent类型映射表，用于选择不同的Coder实现
    CODER_TYPES = {
        "coder": Coder,
        "architect": ArchitectCoder,
        "ask": AskCoder,
    }

    def create_coder(
        self, 
        root_path: Path, 
        fnames: list[str], 
        agent_name: str,
        type: str = "coder",
        **kwargs
    ) -> Coder:
        """
        创建 Coder，并配置日志记录
        所有agents共享同一个文件，通过绝对路径访问
        
        Args:
            root_path: Agent工作目录
            fnames: 可访问的文件列表
            agent_name: Agent名称
            type: Agent类型，可选值: "coder", "architect", "ask"
            **kwargs: 其他参数
        """
        # 1. 显式定义聊天记录文件路径
        # 这样你就能在 agent_a/.aider.chat.history.md 中看到记录了
        history_file = root_path / f".aider.chat.history.md"

        # 2. 配置 IO
        io = InputOutput(
            yes=True,                       # 自动确认
            chat_history_file=history_file, # 关键：指定历史记录文件
            input_history_file=root_path / ".aider.input.history",
        )

        # 3. 根据type获取对应的 Coder 类
        CoderClass = self.CODER_TYPES.get(type, Coder)

        # 4. 创建 Coder - 使用绝对路径，确保所有操作都在workspace下
        coder = CoderClass.create(
            main_model=self.model,
            io=io,
            fnames=fnames,  # 现在是绝对路径
            verbose=False,  # 关键：开启详细模式，出错时能看到原因
            **kwargs        # 透传其他参数，如 edit_format="whole"
        )
        return coder