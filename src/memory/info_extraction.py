import json
import os
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Event

import tqdm

from src.utils.global_logger import logger
from src.utils.config import global_config
from .ie_process import info_extract_from_str
from src.utils.llm_client import LLMClient
from .open_ie import OpenIE
from .utils.raw_processing import load_raw_data

TEMP_DIR = "./temp"

# 创建一个线程安全的锁，用于保护文件操作和共享数据
file_lock = Lock()
open_ie_doc_lock = Lock()

# 创建一个事件标志，用于控制程序终止
shutdown_event = Event()


def process_single_text(pg_hash, raw_data, llm_client_list):
    """处理单个文本的函数，用于线程池"""
    temp_file_path = f"{TEMP_DIR}/{pg_hash}.json"

    # 使用文件锁检查和读取缓存文件
    with file_lock:
        if os.path.exists(temp_file_path):
            try:
                # 存在对应的提取结果
                logger.info(f"找到缓存的提取结果：{pg_hash}")
                with open(temp_file_path, "r", encoding="utf-8") as f:
                    return json.load(f), None
            except json.JSONDecodeError:
                # 如果JSON文件损坏，删除它并重新处理
                logger.warning(f"缓存文件损坏，重新处理：{pg_hash}")
                os.remove(temp_file_path)

    entity_list, rdf_triple_list = info_extract_from_str(
        llm_client_list[global_config["entity_extract"]["llm"]["provider"]],
        llm_client_list[global_config["rdf_build"]["llm"]["provider"]],
        raw_data,
    )
    if entity_list is None or rdf_triple_list is None:
        return None, pg_hash
    else:
        doc_item = {
            "idx": pg_hash,
            "passage": raw_data,
            "extracted_entities": entity_list,
            "extracted_triples": rdf_triple_list,
        }
        # 保存临时提取结果
        with file_lock:
            try:
                with open(temp_file_path, "w", encoding="utf-8") as f:
                    json.dump(doc_item, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logger.error(f"保存缓存文件失败：{pg_hash}, 错误：{e}")
                # 如果保存失败，确保不会留下损坏的文件
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                # 设置shutdown_event以终止程序
                shutdown_event.set()
                return None, pg_hash
        return doc_item, None


def signal_handler(signum, frame):
    """处理Ctrl+C信号"""
    logger.info("\n接收到中断信号，正在优雅地关闭程序...")
    shutdown_event.set()


def extract_triples(_agent_name: str):
    # 设置信号处理器
    # signal.signal(signal.SIGINT, signal_handler)

    logger.info("--------进行信息提取--------\n")

    logger.info("创建LLM客户端")
    llm_client_list = dict()
    for key in global_config["llm_providers"]:
        llm_client_list[key] = LLMClient(
            global_config["llm_providers"][key]["base_url"],
            global_config["llm_providers"][key]["api_key"],
        )

    logger.info("正在加载原始数据")
    sha256_list, raw_datas = load_raw_data(_agent_name)
    logger.info("原始数据加载完成\n")

    # 创建临时目录
    if not os.path.exists(f"{TEMP_DIR}"):
        os.makedirs(f"{TEMP_DIR}")

    failed_sha256 = []
    open_ie_doc = []

    # 创建线程池，最大线程数为50
    with ThreadPoolExecutor(max_workers=20) as executor:
        # 提交所有任务到线程池
        future_to_hash = {
            executor.submit(
                process_single_text, pg_hash, raw_data, llm_client_list
            ): pg_hash
            for pg_hash, raw_data in zip(sha256_list, raw_datas)
        }

        # 使用tqdm显示进度
        with tqdm.tqdm(total=len(future_to_hash), postfix="正在进行提取：") as pbar:
            # 处理完成的任务
            try:
                for future in as_completed(future_to_hash):
                    if shutdown_event.is_set():
                        # 取消所有未完成的任务
                        for f in future_to_hash:
                            if not f.done():
                                f.cancel()
                        break

                    doc_item, failed_hash = future.result()
                    if failed_hash:
                        failed_sha256.append(failed_hash)
                        logger.error(f"提取失败：{failed_hash}")
                    elif doc_item:
                        with open_ie_doc_lock:
                            open_ie_doc.append(doc_item)
                    pbar.update(1)
            except KeyboardInterrupt:
                # 如果在这里捕获到KeyboardInterrupt，说明signal_handler可能没有正常工作
                logger.info("\n接收到中断信号，正在优雅地关闭程序...")
                shutdown_event.set()
                # 取消所有未完成的任务
                for f in future_to_hash:
                    if not f.done():
                        f.cancel()

    # 保存信息提取结果
    sum_phrase_chars = sum(
        [len(e) for chunk in open_ie_doc for e in chunk["extracted_entities"]]
    )
    sum_phrase_words = sum(
        [len(e.split()) for chunk in open_ie_doc for e in chunk["extracted_entities"]]
    )
    num_phrases = sum([len(chunk["extracted_entities"]) for chunk in open_ie_doc])
    openie_obj = OpenIE(
        open_ie_doc,
        round(sum_phrase_chars / num_phrases, 4),
        round(sum_phrase_words / num_phrases, 4),
    )
    OpenIE.save(openie_obj, _agent_name)

    logger.info("--------信息提取完成--------")
    logger.info(f"提取失败的文段SHA256：{failed_sha256}")
