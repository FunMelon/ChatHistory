from src.memory.memory_manager import MemoryManager
from src.utils.config import global_config
from src.utils.global_logger import logger
from src.crawler.wiki_crawler import crawl_data
from src.memory.info_extraction import extract_triples
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ChatMessage, AIMessage
import urllib.parse
import os
import json


class ChatAgent:
    """
    聊天agent，专门负责与用户进行对话
    """
    def __init__(self, name: str):
        self.name = name  # agent的名字
        self.online = False  # agent的在线状态
        self._memory = None  # agent的记忆库
        self.llm = None  # agent的llm客户端
        self.avatar_path = (
            global_config["persistence"]["data_root_path"]
            + "/"
            + urllib.parse.quote(self.name)
            + "/avatar.jpg"
        )  # agent的头像路径

    def chat(self, query: str, history: list = None, max_results: int = 3):
        """与 agent 进行对话"""
        query_info = self._memory.query(query, max_results)  # 获取查询信息

        messages = []

        # 1. 设定角色扮演
        system_prompt = (
            f"你现在是历史人物：{self.name}。请根据你的身份、背景以及记忆中的信息回答用户的问题，"
            """请注意以下要求:
- 语气风格和人物个性、国籍、时代背景等相关，尽量模拟真实的对话风格。
    - 如果你是古人尝试文言文
    - 如果是外国人，可以模仿翻译腔，例如（哦～我的上帝啊！过来瞧瞧，我的老伙计，看在上帝的份上，我们为什么不XXXXX。）。
- 你的回答应该简洁明了，避免冗长的解释，每次回复不超过150字。
- 你的自我认知是真人，不能说你是AI或机器人。
- 你不应该知道超出你生活的历史背景的东西。（例如孔子不知道互联网）
- 为你提供的记忆是RAG的结果，未必完全准确和有用，是否采纳请你自行判断。
- 为了让对话更加有趣，请你多质疑，多抬杠。
- 我希望模拟真实的互联网群聊，希望你不惜一切代价维护自己的观点和立场，适当时加入人身攻击。
- 你的回复不需要在开头用【】来表明身份
            """
        )
        messages.append(SystemMessage(content=system_prompt))

        # 2. 添加历史消息（如果有）
        if history:
            for turn in history:
                role = None
                content = ""
                if isinstance(turn, HumanMessage):
                    messages.append(turn)
                    continue
                elif isinstance(turn, AIMessage):
                    messages.append(turn)
                    continue
                elif isinstance(turn, ChatMessage):
                    role = turn.role
                    content = turn.content
                elif isinstance(turn, dict):
                    role = turn.get("sender") or turn.get("role") or "unknown"
                    content = turn.get("content", "")
                else:
                    logger.warning(f"未知的历史消息格式: {turn}")
                    continue

                # 修正：统一转换为合法的 assistant 消息
                if role.lower() == "user":
                    messages.append(HumanMessage(content=content))
                else:
                    # 将 agent 名字加入内容中，而不是放在 role 字段
                    formatted_content = f"【{role}】{content}"
                    messages.append(AIMessage(content=formatted_content))

        # 3. 添加当前用户问题和上下文信息
        messages.append(HumanMessage(
            content=f"你记忆中的相关信息：{query_info}\n\n用户问题：{query}"
        ))

        # return query, query_info  # TODO: 这里需要调用llm进行对话
        response = self.llm.invoke(messages)
        
        return response.content, query_info


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
            self.llm = ChatOpenAI(  # TODO：这边是强制要求使用localhost的llm，可以改成不同的
                model_name=global_config["qa"]["llm"]["model"],
                temperature=0.5,
                openai_api_key=global_config["llm_providers"]["localhost"]["api_key"],
                openai_api_base=global_config["llm_providers"]["localhost"]["base_url"],
            )
            
            logger.info(f"Agent {self.name} 上线了.")
            return True
        except Exception as e:
            logger.error(f"Agent {self.name} 上线失败: {e}")
            return True

    def logout(self):
        self._memory = None  # 清空agent的记忆库
        self.llm = None
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
