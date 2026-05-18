from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os
import sys

# 加载 .env 配置
load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("MODEL", "Qwen3-235B-A22B-Instruct"),
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
)

def print_help():
    print("""
Usage:
  - Enter your code or requirement (multi-line supported), end with a single line containing '.'
  - Type 'clear' to reset history
  - Type 'quit' to exit
  - Type 'help' for this message
""")

def read_multiline_input():
    print("Enter your input (end with a single line '.'):")
    lines = []
    try:
        while True:
            line = input()
            if line.strip() == ".":
                break
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines)

def main():
    print("Welcome! Type 'help' for instructions.\n")
    messages = []

    while True:
        try:
            user_input = read_multiline_input().strip()

            if not user_input:
                print("Input cannot be empty.\n")
                continue

            command = user_input.lower().strip()
            if command == 'quit':
                print("Bye!")
                break
            elif command == 'clear':
                messages.clear()
                print("History cleared.\n")
                continue
            elif command == 'help':
                print_help()
                continue

            messages.append(HumanMessage(content=user_input))

            print("Thinking...", end="", flush=True)
            response = llm.invoke(messages)
            ai_message = response.content
            print("\r" + " " * 20, end="\r", flush=True)

            print(f"Response:\n{ai_message}\n")

            messages.append(AIMessage(content=ai_message))

        except KeyboardInterrupt:
            print("\n\nBye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    main()
