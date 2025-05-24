from src.utils.config import PG_NAMESPACE, global_config
from .embedding_store import EmbeddingManager
from .kg_manager import KGManager
from src.utils.llm_client import LLMClient
from .open_ie import OpenIE, handle_import_openie
from .qa_manager import QAManager
from src.utils.global_logger import logger

class MemoryManager:
    def __init__(self, _agent_name):
        self._agent_name = _agent_name
        try:
            from lib import quick_algo
            print("quick_algo库已加载")
        except ImportError:
            print("未找到quick_algo库，无法使用quick_algo算法")
            print("请安装quick_algo库 - 在lib.quick_algo中，执行命令：python setup.py build_ext --inplace")
        
        # 1.初始化LLM客户端
        logger.info("为agent {} 创建LLM客户端".format(self._agent_name))
        llm_client_list = dict()
        for key in global_config["llm_providers"]:
            llm_client_list[key] = LLMClient(
                global_config["llm_providers"][key]["base_url"],
                global_config["llm_providers"][key]["api_key"],
            )
            print(llm_client_list[key])

        # 2.初始化Embedding库（指定agent名字的嵌入库）
        self._embed_manager = EmbeddingManager(
            llm_client_list[global_config["embedding"]["provider"]],
            self._agent_name,
        )
        logger.info("正在从文件加载agent {} 的Embedding库".format(self._agent_name))
        try:
            self._embed_manager.load_from_file()
        except Exception as e:
            logger.error("从文件加载{} 的 Embedding库时发生错误：{}".format(self._agent_name, e))
        logger.info("{} 的 Embedding库加载完成.".format(self._agent_name))
        # 3.初始化KG（指定agent名字的KG库）
        self._kg_manager = KGManager(self._agent_name)
        logger.info("正在从文件加载 {} 的KG".format(self._agent_name))
        try:
            self._kg_manager.load_from_file()
        except Exception as e:
            logger.error("从文件加载 {} 的KG时发生错误：{}".format(self._agent_name, e))
        logger.info("{} KG加载完成".format(self._agent_name))

        logger.info(f"KG节点数量：{len(self._kg_manager.graph.get_node_list())}")
        logger.info(f"KG边数量：{len(self._kg_manager.graph.get_edge_list())}")

        # 数据比对：Embedding库与KG的段落hash集合
        for pg_hash in self._kg_manager.stored_paragraph_hashes:
            key = PG_NAMESPACE + "-" + pg_hash
            if key not in self._embed_manager.stored_pg_hashes:
                logger.warning(f"KG中存在Embedding库中不存在的段落：{key}")

        # 问答系统（用于知识库）TODO: 未来考虑注释掉，仅仅作为知识库使用
        self._qa_manager = QAManager(
            self._embed_manager,
            self._kg_manager,
            llm_client_list[global_config["embedding"]["provider"]],
            llm_client_list[global_config["qa"]["llm"]["provider"]],
            llm_client_list[global_config["qa"]["llm"]["provider"]],
        )


    def import_oie(self):
        logger.info("正在导入OpenIE数据文件")
        try:
            openie_data = OpenIE.load(self._agent_name)
        except Exception as e:
            logger.error("导入OpenIE数据文件时发生错误：{}".format(e))
            return False
        if handle_import_openie(openie_data, self._embed_manager, self._kg_manager) is False:
            logger.error("处理OpenIE数据时发生错误")
            return False
    
    def query(self, question):
        """处理查询"""
        return self._qa_manager.process_query_beautiful(question)
    
    def get_qa(self, question):
        """处理问答查询"""
        return self._qa_manager.answer_question(question)
    
    def get_actor(self, question):
        """处理角色扮演查询"""
        ans, _ = self._qa_manager.actor_question(question)
        return ans;
    
    def get_actor_with_kg(self, question):
        """处理角色扮演查询，同时保留KG信息"""
        return self._qa_manager.actor_question(question)