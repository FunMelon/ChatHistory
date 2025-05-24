import streamlit as st
from src.agent import Agent

# 设置聊天人的头像
def get_avatar_path(agent_name):
    return agent_name

st.set_page_config(
    page_title="ChatHistory",
    page_icon="🏯",
    layout="wide",
)

st.title("🏯ChatHistory")

# 给对话增加history属性，将历史对话信息储存下来
if "history" not in st.session_state:
    st.session_state.history = []
if "agent_list" not in st.session_state:
    st.session_state.agent_list = [Agent("释迦牟尼"), Agent("孔子")]

# 显示历史信息
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

material = "这里会显示检索的结果"
# user_input接收用户的输入
if user_input := st.chat_input("Chat with history character: "):
    with st.chat_message("user"):
        st.markdown(user_input)

    response, material = user_input, "这里是检索的结果"  # agent.chat(user_input)

    st.session_state.history.append({"role": "user", "content": user_input})
    agent1 = st.session_state.agent_list[0]
    with st.chat_message("assistant", avatar=agent1.avatar_path):
        st.markdown("**{}**".format(agent1.name))
        st.markdown(response)
    agent2 = st.session_state.agent_list[1]
    with st.chat_message("assistant", avatar=agent2.avatar_path):
        st.markdown("**{}**".format(agent2.name))
        st.markdown(response)
        
    st.session_state.history.append({"role": "assistant", "content": response})

    if len(st.session_state.history) > 20:
        st.session_state.messages = st.session_state.messages[-20:]


with st.sidebar:
    # 在线agent列表部分
    with st.expander("🤖在线agent"):
        for agent in st.session_state.agent_list:
            st.checkbox(label=agent.name, key=f"agent_{agent.name}")
        # TODO: 添加增加新agent的button
    
    # 检索内容部分
    with st.expander("🔍️记忆库检索结果"):
        st.text(material)
    
    # TODO: 个人信息配置部分
    with st.expander("👤个人信息配置"):
        st.text("这里是个人信息配置的内容")

if __name__ == "__main__":
    pass
    # 初始化agent_list并存储在st.session_state中
    # if "agent_list" not in st.session_state:
    # st.session_state.agent_list = [Agent("孔子")]
    # 触发页面刷新
    # st.rerun()