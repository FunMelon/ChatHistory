import streamlit as st
from src.memory.memory_manager import MemoryManager

memory = MemoryManager("孔子")  # 创建MemoryManager实例

def get_avatar(agent_name):
    return agent_name
    
st.set_page_config(
    page_title="ChatApp",
    page_icon=" ",
    layout="wide",
)

st.title("🏯ChatHistory")

# 给对话增加history属性，将历史对话信息储存下来
if "history" not in st.session_state:
    st.session_state.history = []

# 显示历史信息
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 这里是你的大模型生成的回复
# 需要根据自己的情况进行实现
# 我这里不仅想要显示大模型的回复，还想展示检索信息，所以将检索的内容也一起返回
def get_response_material(query, history):
    return memory.get_actor_with_kg(query)

material = "这里会显示检索的结果"

# user_input接收用户的输入
if user_input := st.chat_input("Chat with history character: "):
    with st.chat_message("user"):
        st.markdown(user_input)

    response, material = get_response_material(user_input, st.session_state.history)

    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("assistant", avatar=get_avatar("孔子.jpg")):
        st.markdown("**孔子**")
        st.markdown(response)
    st.session_state.history.append({"role": "assistant", "content": response})

    if len(st.session_state.history) > 20:
        st.session_state.messages = st.session_state.messages[-20:]

# 左侧栏无论是否有输入都显示
with st.sidebar:
    st.markdown('从记忆库中检索得到:')
    st.text(material)

if __name__ == "__main__":
    # pre_process() # 读取文本生成OpenIE数据，TODO：这里的函数因为用到signal.signal()函数，导致streamlit无法运行
    memory.import_oie() # 导入OpenIE数据到记忆库