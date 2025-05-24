from src.memory.memory_manager import MemoryManager
from src.utils.config import global_config
from src.utils.global_logger import logger
import urllib.parse

class Agent:
    # TODO: 增加agent判断是否存在，和从爬虫到记忆库的一站式构造
    def __init__(self, name: str):
        self.name = name        # agent的名字
        print(f"Agent {self.name} 初始化了.")
        self.online = False     # agent的在线状态
        self.avatar_path = global_config["persistence"]["data_root_path"] + "/" + urllib.parse.quote(self.name) + "/avatar.jpg"  # agent的头像路径
    
    def chat(self, query: str):
        """与agent进行对话"""
        response, material = self._memory.get_actor_with_kg(query)
        return response, material
    
    def login(self):
        self._memory = MemoryManager(self.name)  # 根据name初始化agent的记忆库
        self.online = True  # 设置agent为在线状态
        logger.info(f"Agent {self.name} 上线了.")

    def logout(self):
        self._memory = None  # 清空agent的记忆库
        self.online = False
        logger.info(f"Agent {self.name} 下线了.")