import os
from llm_helper import ask_llm

def analyze_files(folder="."):
    for file in os.listdir(folder):
        if file.endswith(".py") and file != "analyze_files.py":  # 避免分析自己
            try:
                with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                    content = f.read()
                prompt = f"请分析这个Python文件 {file} 的代码，并总结其功能和可能的改进：\n{content}"
                response = ask_llm(prompt)
                print(f"\n=== 分析 {file} ===\n{response}\n")
            except Exception as e:
                print(f"分析 {file} 时出错: {e}")

if __name__ == "__main__":
    analyze_files()