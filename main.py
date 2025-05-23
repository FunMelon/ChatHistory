import sys

from src.memory.memory_manager import MemoryManager
from src.memory.info_extraction import pre_process
from src.utils.global_logger import logger

def process_instruction(
    inst: str,
    memoryManager: MemoryManager,
):
    match inst:
        case "import oie":
            logger.info("正在导入OpenIE数据到记忆库")
            memoryManager.import_oie()
        case "query":
            logger.info("进入查询模式")
            while True:
                print("请在此处输入问题，输入exit退出：", end="")
                sys.stdout.flush()
                question = input().strip()
                if question == "exit":
                    break
                if question == "":
                    continue
                res = memoryManager.query(question)
                print("找到查询结果*****************************************************************")
                print(res)
                print("****************************************************************************")
        case "qa":
            logger.info("进入QA模式")
            while True:
                print("请在此处输入问题，输入exit退出：", end="")
                sys.stdout.flush()
                question = input().strip()
                if question == "exit":
                    break
                if question == "":
                    continue
                memoryManager.get_qa(question)
        case "play":
            logger.info("进入角色扮演模式")
            while True:
                print("请在此处输入问题，输入exit退出：", end="")
                sys.stdout.flush()
                question = input().strip()
                if question == "exit":
                    break
                if question == "":
                    continue
                memoryManager.get_actor(question)
        case _:
            print(f"无效指令：{inst}")

def cmd():
    memory = MemoryManager("苏格拉底")  # 创建MemoryManager实例
    pre_process("苏格拉底") # 读取文本生成OpenIE数据
    memory.import_oie() # 导入OpenIE数据到记忆库
    # print(memory.query("苏格拉底和哲学？"))  # 回答问题
    while True:
        print("🏯ChatHistory> ", end="")
        sys.stdout.flush()
        instructions = input().strip()
        # 指令解析，允许多指令同时输入，以“|”分隔
        instruction = [inst.strip() for inst in instructions.lower().split("|")]
        for inst in instruction:
            if inst == "":
                continue
            elif inst == "help":
                print(
                    "可用指令：\n"
                    "1. import oie - 导入OpenIE数据到记忆库\n"
                    "2. query - 进入查询模式\n"
                    "3. qa - 进入QA模式\n"
                    "4. play - 进入角色扮演模式\n"
                    "5. exit - 退出控制台\n"
                )
            elif inst == "exit":
                print("退出控制台")
                exit(0)
            elif (
                process_instruction(
                    inst, memory
                )
                is False
            ):
                print("指令流程出现错误，请检查")
                exit(0)

if __name__ == "__main__":
    cmd()