import requests
from bs4 import BeautifulSoup
import urllib.parse
from opencc import OpenCC
import json
import re

def trad_to_simp(text):
    """
    将繁体中文句子转换为简体中文
    
    参数:
        text (str): 需要转换的繁体中文句子
    
    返回:
        str: 转换后的简体中文句子
    """
    try:
        # 使用 OpenCC 进行繁简转换
        # 't2s' 表示繁体到简体的转换
        cc = OpenCC('t2s')
        simplified_text = cc.convert(text)
        return simplified_text
    except Exception as e:
        # 处理可能的异常
        print(f"转换过程中出现错误: {e}")
        return None

def remove_references(text):
    # 去除形如 [1]、[注 1] 等脚注标记
    return re.sub(r'\[[^\[\]]*?\]', '', text)

def wikipedia_search_and_save(keyword): 
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://zh.wikipedia.org/wiki/{encoded_keyword}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"请求失败，状态码：{response.status_code}")
            return

        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        content_div = soup.find("div", id="mw-content-text")
        if not content_div:
            print("未能找到词条内容。")
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
            print("未能提取到有效段落内容。")
            return

        filename = f"{keyword}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(content_list, f, ensure_ascii=False, indent=2)

        print(f"维基百科内容已成功保存到 {filename}。")

    except requests.RequestException as e:
        print("网络请求出错：", e)
    except Exception as e:
        print("发生错误：", e)

if __name__ == "__main__":
    keyword = "杨玉环"  # 示例关键词
    wikipedia_search_and_save(keyword)