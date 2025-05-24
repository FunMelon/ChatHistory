import requests
from bs4 import BeautifulSoup
import urllib.parse
from opencc import OpenCC
import json
import re
import os
from src.utils.global_logger import logger
from src.utils.config import global_config

def trad_to_simp(text):
    """繁体转简体"""
    try:
        cc = OpenCC('t2s')
        return cc.convert(text)
    except Exception as e:
        logger.error(f"转换错误: {e}")
        return None

def remove_references(text):
    """去除脚注标记如 [1]、[注 1] 等"""
    return re.sub(r'\[[^\[\]]*?\]', '', text)

def download_avatar(image_url, save_path):
    """下载人物头像"""
    try:
        img_response = requests.get(image_url, stream=True)
        if img_response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in img_response.iter_content(1024):
                    f.write(chunk)
            logger.info(f"人物头像已保存到 {save_path}")
        else:
            logger.error("图片下载失败，状态码：", img_response.status_code)
    except Exception as e:
        logger.error("下载图片出错：%s", e)

def wikipedia_search_and_save(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://zh.wikipedia.org/wiki/{encoded_keyword}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"请求失败，状态码：{response.status_code}")
            return

        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        # 获取段落内容
        content_div = soup.find("div", id="mw-content-text")
        if not content_div:
            logger.error("未能找到词条内容。")
            return

        paragraphs = content_div.find_all("p")
        content_list = []
        for para in paragraphs:
            text = para.get_text(strip=True)
            if text:
                text = trad_to_simp(text)
                text = remove_references(text)
                content_list.append(text)

        if not content_list:
            logger.error("未能提取到有效段落内容。")
            return

        # 尝试提取人物头像（信息框中的第一张图）
        infobox = soup.find("table", class_="infobox")
        image_url = None
        if infobox:
            img = infobox.find("img")
            if img and img.get("src"):
                image_url = "https:" + img["src"]

        # 保存文本内容
        dir_path = global_config["persistence"]["data_root_path"] + "/" + urllib.parse.quote(keyword)
        os.makedirs(dir_path, exist_ok=True)
        filename = os.path.join(dir_path + global_config["persistence"]["raw_data_path"])
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(content_list, f, ensure_ascii=False, indent=2)
        logger.info(f"维基百科内容已保存到 {filename}")

        # 下载人物头像
        if image_url:
            image_ext = os.path.splitext(image_url)[1]
            image_filename = os.path.join(dir_path + f"/avatar{image_ext}")
            download_avatar(image_url, image_filename)
        else:
            logger.error(f"未找到{keyword}的头像。")

    except requests.RequestException as e:
        logger.error("网络请求出错：%s", e)
    except Exception as e:
        logger.error("发生错误：%s", e)

def crawl_data(keyword):
    """爬取数据"""
    wikipedia_search_and_save(keyword)

if __name__ == "__main__":
    keyword = "牛顿"  # 示例关键词
    wikipedia_search_and_save(keyword)
