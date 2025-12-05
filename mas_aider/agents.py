# agents.py
from pathlib import Path
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

class AiderAgentFactory:
    def __init__(self, model_name="openai/glm-4.6", api_base=None):
        self.model_name = model_name
        if api_base:
            import os
            os.environ["OPENAI_BASE_URL"] = api_base
        self.model = Model(model_name)

    def create_coder(self, root_path: Path, fnames: list[str], agent_name: str) -> Coder:
        """
        创建 Coder，并配置日志记录
        所有agents共享同一个文件，通过绝对路径访问
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

        # 3. 创建 Coder - 使用绝对路径，确保所有操作都在workspace下
        coder = Coder.create(
            main_model=self.model,
            io=io,
            fnames=fnames,  # 现在是绝对路径
            verbose=False,  # 关键：开启详细模式，出错时能看到原因
            # 如果 GLM-4 编辑能力较弱，可以尝试强制使用 'whole' 模式，虽然耗费 token 但更稳
            # edit_format="whole",
        )
        return coder