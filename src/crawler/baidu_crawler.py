import sys
import requests
from bs4 import BeautifulSoup


def baike_crawler(key_word):
	# 目标网页URL
	url = f"https://baike.baidu.com/item/{key_word}"
	# 发送HTTP请求
	response = requests.get(url)
	if response.status_code != 200:
		return "未找到相关信息！"
	# 解析HTML内容
	soup = BeautifulSoup(response.text, 'html.parser')
	# print(soup.prettify())
	# 获取主要内容
	content = []
	meta_desc = soup.find('meta', attrs={'name': 'description'})
	return meta_desc.get('content')


def save_json(content, json_file):
	sentence_list = content.split("。")
	if content.endswith("。") is False:
		sentence_list = sentence_list[:-1]
	filtered_list = list(filter(lambda x: len(x) > 0, sentence_list))
	num = len(filtered_list)
	top = 0
	with open(json_file, "w", encoding="utf-8") as f:
		print("[")
		print("[", file=f)
		for sentence in filtered_list:
			top += 1
			sentence_end = ""
			if top < num:
				sentence_end = ","
			print(f"    \"{sentence}。\"{sentence_end}")
			print(f"    \"{sentence}。\"{sentence_end}", file=f)
		print("]")
		print("]", file=f)


def main():
	json_file = "./data/import.json"
	key_word = sys.argv[1]
	print(f"关键词：{key_word}")
	ret = baike_crawler(key_word)
	print("网页信息：")
	save_json(ret, json_file)


if __name__ == "__main__":
	main()
