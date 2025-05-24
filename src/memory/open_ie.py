import json
from typing import Any, Dict, List


from src.utils.config import INVALID_ENTITY, global_config
from .embedding_store import EmbeddingManager
from .kg_manager import KGManager
from src.utils.global_logger import logger
from .utils.hash import hash_deduplicate
import urllib

def _filter_invalid_entities(entities: List[str]) -> List[str]:
    """过滤无效的实体"""
    valid_entities = set()
    for entity in entities:
        if (
            not isinstance(entity, str)
            or entity.strip() == ""
            or entity in INVALID_ENTITY
            or entity in valid_entities
        ):
            # 非字符串/空字符串/在无效实体列表中/重复
            continue
        valid_entities.add(entity)

    return list(valid_entities)


def _filter_invalid_triples(triples: List[List[str]]) -> List[List[str]]:
    """过滤无效的三元组"""
    unique_triples = set()
    valid_triples = []

    for triple in triples:
        if len(triple) != 3 or (
            (not isinstance(triple[0], str) or triple[0].strip() == "")
            or (not isinstance(triple[1], str) or triple[1].strip() == "")
            or (not isinstance(triple[2], str) or triple[2].strip() == "")
        ):
            # 三元组长度不为3，或其中存在空值
            continue

        valid_triple = [str(item) for item in triple]
        if tuple(valid_triple) not in unique_triples:
            unique_triples.add(tuple(valid_triple))
            valid_triples.append(valid_triple)

    return valid_triples


class OpenIE:
    """
    OpenIE规约的数据格式为如下
    {
        "docs": [
            {
                "idx": "文档的唯一标识符（通常是文本的SHA256哈希值）",
                "passage": "文档的原始文本",
                "extracted_entities": ["实体1", "实体2", ...],
                "extracted_triples": [["主语", "谓语", "宾语"], ...]
            },
            ...
        ],
        "avg_ent_chars": "实体平均字符数",
        "avg_ent_words": "实体平均词数"
    }
    """

    def __init__(
        self,
        docs: List[Dict[str, Any]],
        avg_ent_chars,
        avg_ent_words,
    ):
        self.docs = docs
        self.avg_ent_chars = avg_ent_chars
        self.avg_ent_words = avg_ent_words

        for doc in self.docs:
            # 过滤实体列表
            doc["extracted_entities"] = _filter_invalid_entities(
                doc["extracted_entities"]
            )
            # 过滤无效的三元组
            doc["extracted_triples"] = _filter_invalid_triples(doc["extracted_triples"])

    @staticmethod
    def _from_dict(data):
        """从字典中获取OpenIE对象"""
        return OpenIE(
            docs=data["docs"],
            avg_ent_chars=data["avg_ent_chars"],
            avg_ent_words=data["avg_ent_words"],
        )

    def _to_dict(self):
        """转换为字典"""
        return {
            "docs": self.docs,
            "avg_ent_chars": self.avg_ent_chars,
            "avg_ent_words": self.avg_ent_words,
        }

    @staticmethod
    def load(_agent_name: str) -> "OpenIE":
        """从文件中加载OpenIE数据"""
        with open(
            global_config["persistence"]["data_root_path"] + "/" + urllib.parse.quote(_agent_name) + global_config["persistence"]["openie_data_path"], "r", encoding="utf-8"
        ) as f:
            data = json.loads(f.read())

        openie_data = OpenIE._from_dict(data)

        return openie_data

    @staticmethod
    def save(openie_data: "OpenIE", _agent_name: str):
        """保存OpenIE数据到文件"""
        with open(
            global_config["persistence"]["data_root_path"] + "/" + urllib.parse.quote(_agent_name) + global_config["persistence"]["openie_data_path"], "w", encoding="utf-8"
        ) as f:
            f.write(json.dumps(openie_data._to_dict(), ensure_ascii=False, indent=4))

    def extract_entity_dict(self):
        """提取实体列表"""
        ner_output_dict = dict(
            {
                doc_item["idx"]: doc_item["extracted_entities"]
                for doc_item in self.docs
                if len(doc_item["extracted_entities"]) > 0
            }
        )
        return ner_output_dict

    def extract_triple_dict(self):
        """提取三元组列表"""
        triple_output_dict = dict(
            {
                doc_item["idx"]: doc_item["extracted_triples"]
                for doc_item in self.docs
                if len(doc_item["extracted_triples"]) > 0
            }
        )
        return triple_output_dict

    def extract_raw_paragraph_dict(self):
        """提取原始段落"""
        raw_paragraph_dict = dict(
            {doc_item["idx"]: doc_item["passage"] for doc_item in self.docs}
        )
        return raw_paragraph_dict

def handle_import_openie(
    openie_data: OpenIE, embed_manager: EmbeddingManager, kg_manager: KGManager
) -> bool:
    # 从OpenIE数据中提取段落原文与三元组列表
    # 索引的段落原文
    raw_paragraphs = openie_data.extract_raw_paragraph_dict()
    # 索引的实体列表
    entity_list_data = openie_data.extract_entity_dict()
    # 索引的三元组列表
    triple_list_data = openie_data.extract_triple_dict()
    print(
            f"段落数量：{len(raw_paragraphs)}，实体数量：{len(entity_list_data)}，三元组数量：{len(triple_list_data)}"
        )
    if len(raw_paragraphs) != len(entity_list_data) or len(raw_paragraphs) != len(
        triple_list_data
    ):
        logger.error("OpenIE数据存在异常")
        return False
    # 将索引换为对应段落的hash值
    logger.info("正在进行段落去重与重索引")
    raw_paragraphs, triple_list_data = hash_deduplicate(
        raw_paragraphs,
        triple_list_data,
        embed_manager.stored_pg_hashes,
        kg_manager.stored_paragraph_hashes,
    )
    if len(raw_paragraphs) != 0:
        # 获取嵌入并保存
        logger.info(f"段落去重完成，剩余待处理的段落数量：{len(raw_paragraphs)}")
        logger.info("开始Embedding")
        embed_manager.store_new_data_set(raw_paragraphs, triple_list_data)
        # Embedding-Faiss重索引
        logger.info("正在重新构建向量索引")
        embed_manager.rebuild_faiss_index()
        logger.info("向量索引构建完成")
        embed_manager.save_to_file()
        logger.info("Embedding完成")
        # 构建新段落的RAG
        logger.info("开始构建RAG")
        kg_manager.build_kg(triple_list_data, embed_manager)
        kg_manager.save_to_file()
        logger.info("RAG构建完成")
    else:
        logger.info("无新段落需要处理")
    return True