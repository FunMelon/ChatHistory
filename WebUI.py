import gradio as gr
from src.memory.memory_manager import MemoryManager
from src.memory.info_extraction import pre_process

memory = MemoryManager()  # 创建MemoryManager实例

def chat_fn(history, message):
    bot_response = memory.get_actor(message)
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": bot_response})
    return history, ""

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=3):  # 左侧聊天区域
            chatbot = gr.Chatbot(label="聊天窗口", type="messages")
            with gr.Row():
                msg = gr.Textbox(placeholder="输入消息...", scale=4)
                send_btn = gr.Button("发送", scale=1)

    send_btn.click(
        fn=chat_fn,
        inputs=[chatbot, msg],
        outputs=[chatbot, msg]
    )

if __name__ == "__main__":
    pre_process() # 读取文本生成OpenIE数据
    memory.import_oie() # 导入OpenIE数据到记忆库
    demo.launch()