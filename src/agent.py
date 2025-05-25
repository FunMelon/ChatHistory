from src.memory.memory_manager import MemoryManager
from src.utils.config import global_config
from src.utils.global_logger import logger
from src.crawler.wiki_crawler import crawl_data
from src.memory.info_extraction import extract_triples
import urllib.parse
import os
import json


class Agent:
    def __init__(self, name: str):
        self.name = name  # agent的名字
        self.online = False  # agent的在线状态
        self._memory = None  # agent的记忆库
        self.avatar_path = (
            global_config["persistence"]["data_root_path"]
            + "/"
            + urllib.parse.quote(self.name)
            + "/avatar.jpg"
        )  # agent的头像路径

    def chat(self, query: str):
        """与agent进行对话"""
        response, material = self._memory.get_actor_with_kg(query)
        return response, material

    def login(self):
        """
        加载记忆库
        """
        try:
            self._memory = MemoryManager(self.name)  # 根据name初始化agent的记忆库
            try:
                self._memory.import_oie()  # 第一次登录时导入openie数据
            except Exception as e:
                logger.error(f"导入openie数据失败: {e}")
                return False
            self.online = True  # 设置agent为在线状态
            logger.info(f"Agent {self.name} 上线了.")
            return True
        except Exception as e:
            logger.error(f"Agent {self.name} 上线失败: {e}")
            return True

    def logout(self):
        self._memory = None  # 清空agent的记忆库
        self.online = False
        logger.info(f"Agent {self.name} 下线了.")
        return True

    @staticmethod
    def get_all_agent_names():
        path = global_config["persistence"]["data_root_path"]
        agent_dict = {}
        agent_list = []

        try:
            # 遍历指定路径下的所有文件夹
            for item in os.listdir(path):
                item_path = os.path.join(path, item)

                if os.path.isdir(item_path):
                    original_name = item
                    decoded_name = urllib.parse.unquote(original_name)
                    agent_dict[original_name] = decoded_name
                    agent_list.append(decoded_name)

            # 保存到list.json文件
            list_json_path = os.path.join(path, "list.json")
            with open(list_json_path, "w", encoding="utf-8") as f:
                json.dump(agent_dict, f, indent=4, ensure_ascii=False)

            return agent_list

        except Exception as e:
            logger.error(f"获取所有agent名称失败: {e}")
            return []

    @staticmethod
    def build_openie(name: str):
        """
        指定从0开始构造agent的openie.json
        """
        logger.info(f"正在构建agent: {name}")
        # 1.从wikipedia利用关键词爬取数据，存储到import.json中，头像存储到avatar.jpg中
        logger.info(f"正在从维基百科爬取数据: {name}")
        try:
            crawl_data(name)
            logger.info(f"维基百科数据爬取完成: {name}")
        except Exception as e:
            logger.error(f"维基百科数据爬取失败: {e}")
            return False
        # 2.使用openie 从import.json中提取三元组，存储到openie.json中
        logger.info(f"正在从维基百科数据中提取三元组: {name}")
        try:
            extract_triples(name)
            logger.info(f"三元组提取完成: {name}")
        except Exception as e:
            logger.error(f"三元组提取失败: {e}")
            return False

        return True
