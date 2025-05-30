import time
from typing import Tuple, List, Dict

from src.utils.global_logger import logger
from src.utils import prompt_template
from .embedding_store import EmbeddingManager
from src.utils.llm_client import LLMClient
from .kg_manager import KGManager
from src.utils.config import global_config
from .utils.dyn_topk import dyn_select_top_k


class QAManager:
    def __init__(
        self,
        embed_manager: EmbeddingManager,
        kg_manager: KGManager,
        llm_client_embedding: LLMClient,
        llm_client_filter: LLMClient,
        llm_client_qa: LLMClient,
    ):
        self.embed_manager = embed_manager
        self.kg_manager = kg_manager
        self.llm_client_list = {
            "embedding": llm_client_embedding,
            "filter": llm_client_filter,
            "qa": llm_client_qa,
        }

    def process_query(
        self, question: str
    ) -> Tuple[List[Tuple[str, float, float]], Dict[str, float] | None]:
        """处理查询"""

        # 生成问题的Embedding
        part_start_time = time.perf_counter()
        question_embedding = self.llm_client_list["embedding"].send_embedding_request(
            global_config["embedding"]["model"], question
        )
        part_end_time = time.perf_counter()
        logger.debug(f"Embedding用时：{part_end_time - part_start_time:.5f}s")

        # 根据问题Embedding查询Relation Embedding库
        part_start_time = time.perf_counter()
        relation_search_res = self.embed_manager.relation_embedding_store.search_top_k(
            question_embedding,
            global_config["qa"]["params"]["relation_search_top_k"],
        )
        # 过滤阈值
        # 考虑动态阈值：当存在显著数值差异的结果时，保留显著结果；否则，保留所有结果
        relation_search_res = dyn_select_top_k(relation_search_res)
        if (
            relation_search_res[0][1]
            < global_config["qa"]["params"]["relation_threshold"]
        ):
            # 未找到相关关系
            relation_search_res = []

        part_end_time = time.perf_counter()
        logger.debug(f"关系检索用时：{part_end_time - part_start_time:.5f}s")

        relations = []  # 用于存储提取的三元组

        for res in relation_search_res:
            rel_str = self.embed_manager.relation_embedding_store.store.get(res[0]).str
            logger.info(f"找到相关关系，相似度：{(res[1] * 100):.2f}%  -  {rel_str}")
            # 提取三元组（假设格式始终为形如 ('主体', '关系', '客体') 的字符串）
            try:
                triple = eval(rel_str)
                if isinstance(triple, tuple) and len(triple) == 3:
                    relations.append(triple)
            except Exception as e:
                logger.error(f"⚠️ 三元组解析失败：{rel_str}，错误：{e}")

        # 根据问题Embedding查询Paragraph Embedding库
        part_start_time = time.perf_counter()
        paragraph_search_res = (
            self.embed_manager.paragraphs_embedding_store.search_top_k(
                question_embedding,
                global_config["qa"]["params"]["paragraph_search_top_k"],
            )
        )
        part_end_time = time.perf_counter()
        logger.debug(f"文段检索用时：{part_end_time - part_start_time:.5f}s")

        if len(relation_search_res) != 0:
            logger.info("找到相关关系，将使用RAG进行检索")
            # 使用KG检索
            part_start_time = time.perf_counter()
            result, ppr_node_weights = self.kg_manager.kg_search(
                relation_search_res, paragraph_search_res, self.embed_manager
            )
            part_end_time = time.perf_counter()
            logger.info(f"RAG检索用时：{part_end_time - part_start_time:.5f}s")
        else:
            logger.info("未找到相关关系，将使用文段检索结果")
            result = paragraph_search_res
            ppr_node_weights = None

        result = dyn_select_top_k(result)

        for res in result:
            raw_paragraph = self.embed_manager.paragraphs_embedding_store.store[
                res[0]
            ].str
            print(f"找到相关文段，相关系数：{res[1]:.8f}\n{raw_paragraph}\n\n")

        return result, ppr_node_weights

    def process_query_beautiful(
        self, question: str, max_results: int = 3
    ) -> Tuple[List[Tuple[str, float, float]], Dict[str, float] | None]:
        query_res, _ = self.process_query(question)
        knowledge = [
            (
                self.embed_manager.paragraphs_embedding_store.store[res[0]].str,
                res[1],
            )
            for res in query_res
        ]
        return knowledge[:max_results]

    def answer_question(self, question: str):
        """回答问题"""
        start_time = time.time()  # 计时：总用时计算
        # 处理查询
        query_res, _ = self.process_query(question)

        knowledge = [
            (
                self.embed_manager.paragraphs_embedding_store.store[res[0]].str,
                res[1],
            )
            for res in query_res
        ]
        # 将检索结果和问题发送给LLM，获取答案
        # 构造上下文
        context = prompt_template.build_qa_context(question, knowledge)
        reasoning, content = self.llm_client_list["qa"].send_chat_request(
            global_config["qa"]["llm"]["model"], context
        )
        if reasoning is None:
            print(f"回答：{content}\n")
        else:
            print(f"思考：{reasoning}\n回答：{content}\n")

        logger.info(f"总用时：{time.time() - start_time:.2f}s")

    def actor_question(self, question: str):
        """角色扮演回答问题"""
        start_time = time.time()  # 计时：总用时计算
        # 处理查询
        query_res, _ = self.process_query(question)

        knowledge = [
            (
                self.embed_manager.paragraphs_embedding_store.store[res[0]].str,
                res[1],
            )
            for res in query_res
        ]
        # 将检索结果和问题发送给LLM，获取答案
        # 构造上下文
        context = prompt_template.build_actor_context(question, knowledge)
        reasoning, content = self.llm_client_list["qa"].send_chat_request(
            global_config["qa"]["llm"]["model"], context
        )
        if reasoning is None:
            print(f"回答：{content}\n")
        else:
            print(f"思考：{reasoning}\n回答：{content}\n")

        logger.info(f"总用时：{time.time() - start_time:.2f}s")
        return content, knowledge
