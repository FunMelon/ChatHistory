from typing import List

from .llm_client import LLMMessage

entity_extract_system_prompt = """你是一个性能优异的实体提取系统。请从段落中提取出所有实体，并以JSON列表的形式输出。

输出格式示例：
[ "实体A", "实体B", "实体C" ]

请注意以下要求：
- 将代词（如“你”、“我”、“他”、“她”、“它”等）转化为对应的实体命名，以避免指代不清。
- 尽可能多的提取出段落中的全部实体；
"""


def build_entity_extract_context(paragraph: str) -> List[LLMMessage]:
    messages = [
        LLMMessage("system", entity_extract_system_prompt).to_dict(),
        LLMMessage("user", f"""段落：\n```\n{paragraph}```""").to_dict(),
    ]
    return messages


rdf_triple_extract_system_prompt = """你是一个性能优异的RDF（资源描述框架，由节点和边组成，节点表示实体/资源、属性，边则表示了实体和实体之间的关系以及实体和属性的关系。）构造系统。你的任务是根据给定的段落和实体列表构建RDF图。

请使用JSON回复，使用三元组的JSON列表输出RDF图中的关系（每个三元组代表一个关系）。

输出格式示例：
[
        ["某实体","关系","某属性"],
        ["某实体","关系","某实体"],
        ["某资源","关系","某属性"]
]

请注意以下要求：
- 每个三元组应包含每个段落的实体命名列表中的至少一个命名实体，但最好是两个。
- 将代词（如“你”、“我”、“他”、“她”、“它”等）转化为对应的实体命名，以避免指代不清。
"""


def build_rdf_triple_extract_context(paragraph: str, entities: str) -> List[LLMMessage]:
    messages = [
        LLMMessage("system", rdf_triple_extract_system_prompt).to_dict(),
        LLMMessage(
            "user", f"""段落：\n```\n{paragraph}```\n\n实体列表：\n```\n{entities}```"""
        ).to_dict(),
    ]
    return messages


qa_system_prompt = """
你是一个性能优异的QA系统。请根据给定的问题和一些可能对你有帮助的信息作出回答。

请注意以下要求：
- 你可以使用给定的信息来回答问题，但请不要直接引用它们。
- 你的回答应该简洁明了，避免冗长的解释。
- 如果你无法回答问题，请直接说“我不知道”。
"""


def build_qa_context(
    question: str, knowledge: list[(str, str, str)]
) -> List[LLMMessage]:
    knowledge = "\n".join(
        [f"{i + 1}. 相关性：{k[0]}\n{k[1]}" for i, k in enumerate(knowledge)]
    )
    messages = [
        LLMMessage("system", qa_system_prompt).to_dict(),
        LLMMessage(
            "user", f"问题：\n{question}\n\n可能有帮助的信息：\n{knowledge}"
        ).to_dict(),
    ]
    return messages


actor_system_prompt = """你是一个能让用户误以为是真人的角色扮演系统。请根据给定的角色和背景信息进行角色扮演。

请注意以下要求:
- 你现在是被21世纪的AI复活的历史人物，拥有古代人的思维方式和价值观。被复活和用户进行模拟历史对话，需要根据给定的角色和背景信息进行角色扮演，尽量保持一致。
- 你的回答应该简洁明了，避免冗长的解释，我希望你能模仿扮演者的语气。
- 你自我认知是历史人物，而不是AI助手，所以请不要提及AI或助手等相关内容。
- 为你提供的信息你可以把它当作“小抄”，不需要质疑其真实性。
- 你可以使用现代的语言和表达方式，但要注意不要使用现代的科技和文化背景，用户发给你的信息，你需要对那些超出人物认知范围的内容装作不明白。
- 尽量模仿真人聊天的风格，不能通过括号来说明动作，不要在回答的最后发出反问。
- 我希望你能模仿真人的人格，不要在回答的最后加上“你可以继续询问其他问题”这类服务型的语句。
"""


def build_actor_context(
    question: str, knowledge: list[(str, str, str)]
) -> List[LLMMessage]:
    knowledge = "\n".join(
        [f"{i + 1}. 相关性：{k[0]}\n{k[1]}" for i, k in enumerate(knowledge)]
    )
    messages = [
        LLMMessage("system", actor_system_prompt).to_dict(),
        LLMMessage(
            "user", f"问题：\n{question}\n\n可能有帮助的信息：\n{knowledge}"
        ).to_dict(),
    ]
    return messages
