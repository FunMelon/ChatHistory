import os
import toml
import argparse

PG_NAMESPACE = "paragraph"
ENT_NAMESPACE = "entity"
REL_NAMESPACE = "relation"

RAG_GRAPH_NAMESPACE = "rag-graph"
RAG_ENT_CNT_NAMESPACE = "rag-ent-cnt"
RAG_PG_HASH_NAMESPACE = "rag-pg-hash"

# 无效实体
INVALID_ENTITY = [
    "",
    "你",
    "他",
    "她",
    "它",
    "我们",
    "你们",
    "他们",
    "她们",
    "它们",
]


def _load_config(config, config_file_path):
    """读取TOML格式的配置文件"""
    if not os.path.exists(config_file_path):
        return
    with open(config_file_path, "r", encoding="utf-8") as f:
        file_config = toml.load(f)

    if "llm_providers" in file_config:
        for provider in file_config["llm_providers"]:
            if provider["name"] not in config["llm_providers"]:
                config["llm_providers"][provider["name"]] = dict()
            config["llm_providers"][provider["name"]]["base_url"] = provider["base_url"]
            config["llm_providers"][provider["name"]]["api_key"] = provider["api_key"]

    if "entity_extract" in file_config:
        config["entity_extract"] = file_config["entity_extract"]

    if "rdf_build" in file_config:
        config["rdf_build"] = file_config["rdf_build"]

    if "embedding" in file_config:
        config["embedding"] = file_config["embedding"]

    if "rag" in file_config:
        config["rag"] = file_config["rag"]

    if "qa" in file_config:
        config["qa"] = file_config["qa"]

    if "director" in file_config:
        config["director"] = file_config["director"]
        
    if "persistence" in file_config:
        config["persistence"] = file_config["persistence"]

    print("Configurations loaded from file: ", config_file_path)
    print(config)


parser = argparse.ArgumentParser(description="Configurations for the pipeline")
parser.add_argument(
    "--config_path",
    type=str,
    default="config.toml",
    help="Path to the configuration file",
)

global_config = dict(
    {
        "llm_providers": {
            "localhost": {
                "base_url": "http://localhost:8000",
                "api_key": "",
            }
        },
        "entity_extract": {
            "llm": {
                "provider": "localhost",
                "model": "entity-extract",
            }
        },
        "rdf_build": {
            "llm": {
                "provider": "localhost",
                "model": "rdf-build",
            }
        },
        "embedding": {
            "provider": "localhost",
            "model": "embed",
            "dimension": 1024,
        },
        "rag": {
            "params": {
                "synonym_search_top_k": 10,
                "synonym_threshold": 0.75,
            }
        },
        "qa": {
            "params": {
                "relation_search_top_k": 10,
                "relation_threshold": 0.75,
                "paragraph_search_top_k": 10,
                "paragraph_node_weight": 0.05,
                "ent_filter_top_k": 10,
                "ppr_damping": 0.8,
                "res_top_k": 10,
            },
            "llm": {
                "provider": "localhost",
                "model": "qa",
            },
        },
        "director": {
            "params": {
                "relation_search_top_k": 10,
                "relation_threshold": 0.75,
                "paragraph_search_top_k": 10,
                "paragraph_node_weight": 0.05,
                "ent_filter_top_k": 10,
                "ppr_damping": 0.8,
                "res_top_k": 10,
            },
            "llm": {
                "provider": "localhost",
                "model": "director",
            },
        },
        "persistence": {
            "data_root_path": "data",
            "raw_data_path": "data/raw.json",
            "openie_data_path": "data/openie.json",
            "embedding_data_dir": "data/embedding",
            "rag_data_dir": "data/rag",
        },
    }
)

_load_config(global_config, parser.parse_args().config_path)
