import streamlit as st
from src.agent import Agent

st.set_page_config(
    page_title="ChatHistory：穿越历史人物对话",
    page_icon="🏯",
    layout="wide",
)

st.title("🏯ChatHistory")

# 给对话增加history属性，将历史对话信息储存下来
if "history" not in st.session_state:
    st.session_state.history = []

# 初始化agent_list并存储在st.session_state中
if "agent_list" not in st.session_state:
    st.session_state.agent_list = [Agent(name) for name in Agent.get_all_agent_names()]

# 设置用户是否可以进行交互
if "interactable" not in st.session_state:
    st.session_state.interactable = True

# 初始化每个agent的checkbox状态
for agent in st.session_state.agent_list:
    checkbox_key = f"agent_{agent.name}"
    if checkbox_key not in st.session_state:
        st.session_state[checkbox_key] = False

# 处理checkbox状态变化并更新online状态
def update_agent_status():
    for agent in st.session_state.agent_list:
        key = f"agent_{agent.name}"
        desired_status = st.session_state.get(key, False)
        if desired_status and not agent.online:
            agent.login()
        elif not desired_status and agent.online:
            agent.logout()

# 执行状态更新
update_agent_status()

# 显示历史信息
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

material = "这里会显示检索的结果"

# 用户输入处理
if not st.session_state.get("interactable", True):
    st.warning("请稍候...")
else:
    if user_input := st.chat_input("Chat with history character: "):
        st.session_state.interactable = False

        # 显示用户输入
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.history.append({"role": "user", "content": user_input})

        # 显示所有在线 agent 的响应
        for agent in st.session_state.agent_list:
            if agent.online:
                response, material = agent.chat(user_input)
                with st.chat_message("assistant", avatar=agent.avatar_path):
                    st.markdown(f"**{agent.name}**")
                    st.markdown(response)
                st.session_state.history.append({"role": "assistant", "content": f"**{agent.name}**: {response}"})

        # 保持最多20条历史记录
        if len(st.session_state.history) > 20:
            st.session_state.history = st.session_state.history[-20:]

        st.session_state.interactable = True

# Sidebar
with st.sidebar:
    with st.expander("➕ 添加 Agent"):
        if not st.session_state.get("interactable", True):
            st.warning("请稍候...")
        else:
            new_agent_name = st.text_input("请输入新 Agent 的名字", key="new_agent_name")
            if st.button("确认创建"):
                st.session_state.interactable = False
                if Agent.build_openie(new_agent_name):
                    new_agent = Agent(new_agent_name)
                    st.session_state.agent_list.append(new_agent)
                    st.session_state[f"agent_{new_agent.name}"] = False
                    st.success(f"Agent {new_agent_name} 创建成功！")
                else:
                    st.warning("无法创建 Agent {}".format(new_agent_name))
                st.session_state.interactable = True

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
