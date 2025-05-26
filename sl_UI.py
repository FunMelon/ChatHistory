import streamlit as st
from langchain.schema import HumanMessage, ChatMessage, SystemMessage
from src.utils.global_logger import logger
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx
from src.director_agent import DirectorAgent

# 黑名单相关设置
enable_blacklist = True
BLACKLIST = set()
if enable_blacklist:
    logger.info("正在加载黑名单...")
    with open("./blacklist.txt", "r", encoding="utf-8") as file:
        for line in file:
            BLACKLIST.add(line.strip())
    logger.info("黑名单加载完成")

# Streamlit 页面设置
st.set_page_config(
    page_title="ChatHistory：穿越历史人物对话",
    page_icon="🏯",
    layout="wide",
)

# 获取用户 IP
def get_remote_ip() -> str:
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None
        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return None
        return session_info.request.remote_ip
    except Exception:
        return None

user_ip = get_remote_ip()
logger.info(f"用户IP: {user_ip} 正在访问")

st.title("🏯ChatHistory")

# 初始化状态变量
if "history" not in st.session_state:
    st.session_state.history = []

# 清理旧格式的历史记录（去除 AIMessage）
st.session_state.history = [
    msg for msg in st.session_state.history
    if isinstance(msg, (HumanMessage, ChatMessage))
]

if "director" not in st.session_state:
    st.session_state.director = DirectorAgent()

if "interactable" not in st.session_state:
    st.session_state.interactable = True

# Agent 登录与创建逻辑
@st.dialog(title="🥺请完成后再关闭当前页面", width="large")
def create_agent_dialog(name):
    if enable_blacklist and name in BLACKLIST:
        logger.warning(f"用户 {user_ip} 尝试创建黑名单 Agent: {name}")
        st.image("warn.jpg")
        st.error("你想干什么？！")
        st.error(f"你的IP {user_ip}，已经被记录")
        st.session_state.interactable = True
        return

    st.markdown(f"🧟`{name}`正在转世中...")
    success = st.session_state.director.create_agent(name)
    if success:
        st.session_state[f"agent_{name}"] = False
        st.success(f"Agent {name} 创建成功！")
        logger.info(f"用户 {user_ip} 创建了 Agent: {name}")
    else:
        st.error(f"无法创建 Agent {name}")
        logger.error(f"用户 {user_ip} 创建 Agent: {name} 失败")
    st.session_state.interactable = True

@st.dialog(title="🥺请登录完成后再关闭当前页面", width="large")
def agent_login_dialog(agent):
    st.markdown(f"🧙`{agent.name}`正在登录中...")
    success = agent.login()
    if success:
        st.success(f"Agent {agent.name} 登录成功！")
        logger.info(f"用户 {user_ip} 登录了 Agent: {agent.name}")
    else:
        st.error(f"Agent {agent.name} 登录失败")
        logger.error(f"用户 {user_ip} 登录 Agent: {agent.name} 失败")
    st.session_state.interactable = True

# 初始化每个 agent 的 checkbox 状态
for agent in st.session_state.director.actors:
    key = f"agent_{agent.name}"
    if key not in st.session_state:
        st.session_state[key] = False

def update_agent_status():
    for agent in st.session_state.director.actors:
        key = f"agent_{agent.name}"
        desired_status = st.session_state.get(key, False)
        if desired_status and not agent.online:
            st.session_state.interactable = False
            agent_login_dialog(agent)
        elif not desired_status and agent.online:
            agent.logout()

update_agent_status()

for message in st.session_state.history:
    if isinstance(message, HumanMessage):
        role = "user"
        avatar = None
    elif isinstance(message, ChatMessage):
        role = message.role
        avatar = None
        for agent in st.session_state.director.actors:
            if agent.name == role:
                avatar = getattr(agent, "avatar_path", None)
                break
    else:
        continue

    with st.chat_message(role, avatar=avatar):
        st.markdown(message.content)

material = ["这里会显示数据库检索的结果"]

if user_input := st.chat_input(
    placeholder="chat with history: ",
    disabled=not st.session_state.get("interactable", True),
):
    st.session_state.interactable = False

    logger.info(f"用户聊天内容：用户 {user_ip} 输入消息: {user_input}")
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.history.append(HumanMessage(content=user_input))

    try:
        for agent_name, response, query_info in st.session_state.director.chat(
            user_input,
            history=st.session_state.history,
            max_round=st.session_state.get("max_round", 3),
            max_query=st.session_state.get("max_query", 3)
        ):
            if agent_name == "END":
                st.session_state.interactable = True
                st.success("该您了")
                break

            agent = next((a for a in st.session_state.director.actors if a.name == agent_name), None)
            if agent is None:
                st.error(f"Agent {agent_name} 不存在")
                break

            with st.chat_message(agent.name, avatar=agent.avatar_path):
                st.markdown(f"**{agent.name}**")
                st.markdown(response)

            if query_info:
                material.append(query_info)

            st.session_state.history.append(
                ChatMessage(role=agent.name, content=response)
            )

    except Exception as e:
        logger.error(f"导演 agent 处理失败: {e}")
        st.error("对话过程中发生错误，请稍后再试。")

    max_history = st.session_state.get("max_history", 0)
    st.session_state.history = st.session_state.history[-max_history:]  # 控制历史长度
    print(f"当前历史消息数量: {len(st.session_state.history)}")
    for item in st.session_state.history:
        print(item)
    st.session_state.interactable = True

# Sidebar 设置
with st.sidebar:
    with st.expander("➕ 添加 Agent"):
        if not st.session_state.interactable:
            st.warning("请稍候...")
        else:
            new_agent_name = st.text_input("请输入新 Agent 的名字", key="new_agent_name")
            if st.button("确认创建"):
                if new_agent_name.strip():
                    st.session_state.interactable = False
                    create_agent_dialog(new_agent_name)
                else:
                    st.warning("请先输入 Agent 的名字")

    with st.expander("🤖 在线 agent"):
        if not st.session_state.interactable:
            st.warning("请稍候...")
        else:
            for agent in st.session_state.director.actors:
                st.checkbox(label=agent.name, key=f"agent_{agent.name}")

    with st.expander("🔍️ 记忆库检索结果"):
        for i, item in enumerate(material):
            st.markdown(f"{'初始检索' if i == 0 else f'{i}轮检索结果'}: {item}")

    with st.expander("⚙️ 聊天系统配置"):
        st.session_state["max_round"] = st.slider("Agent 之间交流最大轮数", 1, 10, 3)
        st.session_state["max_query"] = st.slider("记忆库检索保留的最大条数", 0, 10, 3)
        st.session_state["max_history"] = st.slider("聊天历史保留条数", 1, 20, 10)

# Loading 状态提示
if not st.session_state.get("interactable", True):
    st.info("⚙️ 后台正在处理，请耐心等待...")
