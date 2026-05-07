from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage,AIMessage
import sys
llm= ChatOpenAI(
    model="Qwen3-235B-A22B-Instruct",
    api_key="gpustack_2ac06a646549b075_97f1450f7574246ed84360d61c10f10a",
    base_url="http://10.22.2.31:38080/v1"
)
def print_help():
    print("""
📌 使用说明：
  • 输入你的代码或需求（可多行），以单独一行输入 '.' 结束输入
  • 输入 'clear' 清空对话历史
  • 输入 'quit' 退出程序
  • 输入 'help' 查看帮助
""")

def read_multiline_input():
    print("📝 请输入你的代码或需求（结束请输入单独一行 '.'）：")
    lines = []
    try:
        while True:
            line = input()
            if line.strip() == ".":
                break
            lines.append(line)
    except EOFError:  # 用户按下 Ctrl+D (Linux/Mac) 或 Ctrl+Z+Enter (Windows)
        pass
    return "\n".join(lines)

def main():
    print("🚀 欢迎使用代码优化助手！输入 'help' 查看帮助。\n")
    messages = []

    while True:
        try:
            user_input = read_multiline_input().strip()

            if not user_input:
                print("⚠️ 输入不能为空，请重新输入。\n")
                continue

            command = user_input.lower().strip()
            if command == 'quit':
                print("👋 再见！")
                break
            elif command == 'clear':
                messages.clear()
                print("🗑️ 对话已清空。\n")
                continue
            elif command == 'help':
                print_help()
                continue

            # 添加用户消息
            messages.append(HumanMessage(content=user_input))

            # 调用模型
            print("🧠 正在思考...", end="", flush=True)
            response = llm.invoke(messages)
            ai_message = response.content
            print(" " * 20, end="\r", flush=True)  # 清除“正在思考”

            # 打印 AI 回复
            print(f"✅ 优化建议：\n{ai_message}\n")

            # 保存 AI 回复到历史
            messages.append(AIMessage(content=ai_message))

        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断。")
            break
        except Exception as e:
            print(f"❌ 调用 LLM 时出错：{e}\n")

if __name__ == "__main__":
    main()