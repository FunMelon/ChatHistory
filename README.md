# 🏯ChatHistory
一个专注于历史模拟对话的智能体
## 🕹️使用方法
### 安装依赖
下载并进入目录内
```
conda create -n ChatHistory python=3.11
conda activate ChatHistory
pip install -r requirements.txt
```
quick_algo库并没有包含在requirement中，请在文件夹找到对应的程序自行编译安装。
### 关于agent黑名单
在入口函数中找到enable_blacklist可以启用和关闭黑名单机制（默认启用），需要在根目录下面补充blacklist黑名单和warning.jpg警告图片（自备）
### 启用控制台回答
```sh
python main.py
```
### 启用gradio的WebUI（已废弃）
```sh
python WebUI.py
```
### 启用streamlit的WebUI（推荐）
```
streamlit run sl_UI.py
```
## 🎯开发目标
1. 实现agent通过记忆机制进行交互
    - [x] 从指定文件中读取和构建记忆;
    - [x] 从记忆库进行检索记忆;
    - [x] 构造一个聊天控制台;
    - [ ] 构造合适的prompt，测试选择合适的模型;
    - [x] 协同LLM工作实现检索问答;
    - [x] 从百科网页爬取历史人物介绍;
    - [x] 增加了日志文件功能
    - [x] 增加了agent黑名单
2. 实现多agent协作工作流
    - [x] 实现不同角色信息的分离存储;
    - [x] 实现多agent协同聊天机制;
3. 实现WebUI界面
    - [x] 实现WebUI界面的简易对话;
    - [x] 实现WebUI界面的智能体角色的构建和激活;
4. 进一步优化
    - [ ] 采用流式输出;
    - [ ] 实现聊天记录的实时存入记忆库;
    - [ ] 换用数据库软件来存储记忆库;
## 🗂文件记忆库存储
不同的agent的记忆库会以agent的名字转ASCII来进行命名，初始文件只有爬取的import.json文件和对应的头像文件avatar.jpg，为一个由人物资料的句子构成的json数组，经过openie处理得到openie.json文件，然后会被记忆库处理得到embedding和rag。此外data目录下还有一个list.json来保存现在有多少个agent。
## ❤️致谢
- [MaiMBot-LPMM-Demo](https://github.com/MaiM-with-u/MaiMBot-LPMM)：本项目使用的记忆体机制
- [HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG): 本项目参考的RAG管理机制