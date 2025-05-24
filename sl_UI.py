import streamlit as st
from src.agent import Agent
from src.utils.global_logger import logger
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx

enable_blacklist = True  # 是否开启agent黑名单
# 黑名单
BLACKLIST = set()
if enable_blacklist:
    logger.info("正在加载黑名单...")
    with open("./blacklist.txt", "r", encoding="utf-8") as file:
        for line in file:
            # 使用strip()方法去掉行末的换行符等额外字符
            element = line.strip()
            # 把处理后的元素添加到列表中
            BLACKLIST.add(element)
    logger.info("黑名单加载完成")

st.set_page_config(
    page_title="ChatHistory：穿越历史人物对话",
    page_icon="🏯",
    layout="wide",
)

def get_remote_ip() -> str:
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None

        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return None
    except Exception as e:
        return None

    return session_info.request.remote_ip

user_ip = get_remote_ip()
logger.info(f"用户IP: {user_ip}正在访问")

st.title("🏯ChatHistory")

# dialog 方式创建 Agent, FIXME: 将这个dialog设置为不可关闭状态，因为现在实在是不会所以只能没骨气地求用户了
@st.dialog(title="🥺请完成后再关闭当前页面", width="large")
def create_agent_dialog(name):
    if enable_blacklist and name in BLACKLIST:
        logger.warning(f"Agent创建行为，严重警告！用户 {user_ip} 尝试创建黑名单中的 Agent: {name}")
        st.image("warn.jpg")  # 展示图片
        st.error("你想干什么？！")
        st.error("你的IP {}，已经被记录".format(user_ip))
        st.session_state.interactable = True
        return
    st.markdown(f"🧟`{name}`正在转世中...")
    success = Agent.build_openie(name)
    if success:
        new_agent = Agent(name)
        st.session_state.agent_list.append(new_agent)
        st.session_state[f"agent_{new_agent.name}"] = False
        st.success(f"Agent {name} 创建成功！")
        logger.info(f"Agent创建行为，用户 {user_ip} 创建了 Agent: {name}")
    else:
        st.error(f"无法创建 Agent {name}")
        logger.error(f"Agent创建行为，用户 {user_ip} 创建 Agent: {name} 失败")
    st.session_state.interactable = True
    # st.rerun()  # 自动关闭弹窗并刷新界面，FIXME:这行代码有bug，rerun会导致登录的列表被清空

@st.dialog(title="🥺请登录完成后再关闭当前页面", width="large")
def agent_login_dialog(agent):
    st.markdown(f"🧙`{agent.name}`正在登录中...")
    success = agent.login()
    if success:
        st.success(f"Agent {agent.name} 创建成功！")
        logger.info(f"Agent登录行为，用户 {user_ip} 登录了 Agent: {agent.name}")
    else:
        print("登录失败")
        logger.error(f"Agent登录行为，用户 {user_ip} 登录 Agent: {agent.name} 失败")
        st.error(f"Agent {agent.name} 登录失败")
    st.session_state.interactable = True
    # st.rerun()
    
# 初始化对话历史
if "history" not in st.session_state:
    st.session_state.history = []

# 初始化 agent 列表
if "agent_list" not in st.session_state:
    st.session_state.agent_list = [Agent(name) for name in Agent.get_all_agent_names()]

# 控制用户交互状态
if "interactable" not in st.session_state:
    st.session_state.interactable = True

# 初始化每个 agent 的 checkbox 状态
for agent in st.session_state.agent_list:
    checkbox_key = f"agent_{agent.name}"
    if checkbox_key not in st.session_state:
        st.session_state[checkbox_key] = False

# 更新 agent 在线状态
def update_agent_status():
    for agent in st.session_state.agent_list:
        key = f"agent_{agent.name}"
        desired_status = st.session_state.get(key, False)
        if desired_status and not agent.online:
            # 登录要求用户不能操作
            st.session_state.interactable = False
            agent_login_dialog(agent)
        elif not desired_status and agent.online:
            agent.logout()

update_agent_status()

# 显示历史消息（包括头像）- 修复后的版本
for message in st.session_state.history:
    with st.chat_message(message["role"], avatar=message.get("avatar", None)):
        st.markdown(message["content"])

material = "这里会显示检索的结果"

# 处理用户输入
if user_input := st.chat_input(placeholder="和历史上的人物对话: ", disabled= not st.session_state.get("interactable", True)):
    st.session_state.interactable = False

    # 用户输入消息
    logger.info(f"用户聊天内容，用户 {user_ip} 输入消息: {user_input}")
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.history.append({
    "role": "user",
        "content": user_input,
        "avatar": None  # 可选：你可以加用户自定义头像路径
    })

    # agent 响应
    for agent in st.session_state.agent_list:
        if agent.online:
            response, material = agent.chat(user_input)
            logger.info(f"Agent聊天内容，用户 {user_ip} 收到 Agent: {agent.name} 的消息: {response}")
            with st.chat_message("assistant", avatar=agent.avatar_path):
                st.markdown(f"**{agent.name}**")
                st.markdown(response)
            st.session_state.history.append({
                "role": "assistant",
                "content": f"**{agent.name}**: {response}",
                "avatar": agent.avatar_path
            })

    # 限制历史消息数量
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[-20:]

    st.session_state.interactable = True

# Sidebar
with st.sidebar:
    with st.sidebar:
        with st.expander("➕ 添加 Agent"):
            if not st.session_state.get("interactable", True):
                st.warning("请稍候...")
            else:
                new_agent_name = st.text_input("请输入新 Agent 的名字", key="new_agent_name")
                if st.button("确认创建"):
                    if new_agent_name.strip():
                        st.session_state.interactable = False
                        create_agent_dialog(new_agent_name)
                    else:
                        st.warning("请先输入 Agent 的名字")

    with st.expander("🤖在线agent"):
        if not st.session_state.get("interactable", True):
            st.warning("请稍候...")
        else:
            for agent in st.session_state.agent_list:
                key = f"agent_{agent.name}"
                st.checkbox(label=agent.name, key=key)

    with st.expander("🔍️记忆库检索结果"):
        st.text(material)

    with st.expander("⚙️个人信息配置"):
        st.text("这里是个人信息配置的内容（待施工）")

if not st.session_state.get("interactable", True):
    st.info("⚙️ 后台正在处理，请耐心等待...")
