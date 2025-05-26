from src.chat_agent import ChatAgent
from src.utils.global_logger import logger
from src.utils.config import global_config
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
import random

class DirectorAgent:
    def __init__(self, max_rounds=1):
        self.actors = [ChatAgent(name) for name in ChatAgent.get_all_agent_names()]  # 聊天agent的列表，即导演所安排的演员
        self.max_rounds = max_rounds
        self.llm = ChatOpenAI( # TODO：这边是强制要求使用localhost的llm，可以改成不同的
            model_name=global_config["qa"]["llm"]["model"],
            temperature=0,
            openai_api_key=global_config["llm_providers"]["localhost"]["api_key"],
            openai_api_base=global_config["llm_providers"]["localhost"]["base_url"],
        )
        
    def create_agent(self, agent_name):
        """
        依照传入的名称添加一个新的agent
        如果无法创建则返回False，如果创建成功则返回True
        """
        if any(agent.name == agent_name for agent in self.actors):
            logger.error(f"Agent {agent_name} 已经存在，无法重复创建")
            return False
        if not ChatAgent.build_openie(agent_name):
            return False
        self.actors.append(ChatAgent(agent_name))
        return True
    
    def random_agent(self):
        """
        随机选择一个在线的agent
        """
        online_agents = [agent for agent in self.actors if agent.online]
        if not online_agents:
            return None
        return random.choice(online_agents).name
    
    def decide_next_agent(self, history, last_response):
        prompt = f"""你是一个协调者，以下是用户和Agent的对话历史记录。请决定下一个应该调用的Agent名字（只能从以下列表选择或者返回关键字）：
        {list(agent.name for agent in self.actors if agent.online)}
        历史记录：
        {history}

        上一次的回复是：
        {last_response}

        请只返回Agent的名字，如果无需继续对话（即这个时候你认为应该用户继续询问了，这种情况的概率稍微低一些），请返回 "END"。"""
        logger.info(f"导演的决策提示：{prompt}")
        response = self.llm.invoke([HumanMessage(content=prompt)])
        logger.info(f"导演的直接回复是：{response.content}")
        return response.content.strip()

    def chat(self, user_input, history: list = None, max_query = 3):
        # for i in range(len(self.actors)):
            # yield self.actors[i].name, user_input, self.actors[i].name
            
        """
        根据用户的输入产生一轮的多 agent 回复
        """
        # 检查是否有agent在线
        if not any(agent.online for agent in self.actors):
            yield "END", "所有 agent 离线", "所有 agent 离线"
            return
        
        if history is None:
            history = []

        # 起始加入用户输入（已经在上层添加，这里视情况重复）
        last_response = user_input
        round = 0
    
        # 构建 text-style 历史，用于 agent 内部调用（仅辅助决策）
        history_text = "\n".join(
            f"{msg.role if hasattr(msg, 'role') else '用户'}: {msg.content}" for msg in history
        )

        while round < self.max_rounds:
            logger.info(f"第 {round + 1} 轮，导演 agent 进行决策")
            next_agent_name = self.decide_next_agent(history_text, last_response)
            # next_agent_name = self.random_agent()
            logger.info(f"第 {round + 1} 轮，导演决定 agent: {next_agent_name}回答")

            if next_agent_name == "END":
                yield "END", "对话结束", "对话已终止"
                return

            agent = next((a for a in self.actors if a.name == next_agent_name), None)
            if agent is None:
                yield "END", f"{next_agent_name} 不存在", "agent 不存在"
                return
            if not agent.online:
                yield "END", f"{next_agent_name} 不在线", "agent 离线"
                return

            logger.info(f"第 {round + 1} 轮，由 agent {agent.name} 回答")
            last_response, query_info = agent.chat(last_response, history, max_query)

            formatted_response = f"【{agent.name}】{last_response}"
            history.append(AIMessage(content=formatted_response))  # 不再使用 ChatMessage

            # 对文本 history_text 做同步更新
            history_text += f"\n{agent.name}: {last_response}"
            round += 1

            yield agent.name, last_response, query_info
