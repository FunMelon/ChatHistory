import hashlib
from typing import Dict, List
from src.utils.config import PG_NAMESPACE


def get_sha256(string: str) -> str:
    """获取字符串的SHA256值"""
    sha256 = hashlib.sha256()
    sha256.update(string.encode("utf-8"))
    return sha256.hexdigest()


def hash_deduplicate(
    raw_paragraphs: Dict[str, str],
    triple_list_data: Dict[str, List[List[str]]],
    stored_pg_hashes: set,
    stored_paragraph_hashes: set,
):
    """Hash去重

    Args:
        raw_paragraphs: 索引的段落原文
        triple_list_data: 索引的三元组列表
        stored_pg_hashes: 已存储的段落hash集合
        stored_paragraph_hashes: 已存储的段落hash集合

    Returns:
        new_raw_paragraphs: 去重后的段落
        new_triple_list_data: 去重后的三元组
    """
    # 保存去重后的段落
    new_raw_paragraphs = dict()
    # 保存去重后的三元组
    new_triple_list_data = dict()

    for _, (raw_paragraph, triple_list) in enumerate(
        zip(raw_paragraphs.values(), triple_list_data.values())
    ):
        # 段落hash
        paragraph_hash = get_sha256(raw_paragraph)
        if ((PG_NAMESPACE + "-" + paragraph_hash) in stored_pg_hashes) and (
            paragraph_hash in stored_paragraph_hashes
        ):
            continue
        new_raw_paragraphs[paragraph_hash] = raw_paragraph
        new_triple_list_data[paragraph_hash] = triple_list

    return new_raw_paragraphs, new_triple_list_data
