#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script showing how Ollama can analyze project code
"""

from ollama import Client

def analyze_project_file(file_path):
    # 创建Ollama客户端
    client = Client(host='http://localhost:11434')
    model = 'qwen2.5:7b-instruct'

    try:
        # 读取项目文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()

        # 构建分析提示
        prompt = f"""请分析以下Python代码文件的内容，总结其主要功能、结构和可能的改进点：

文件名: {file_path}

代码内容:
{code_content}

请提供详细的分析。"""

        # 调用模型
        response = client.chat(model=model, messages=[{'role': 'user', 'content': prompt}])

        # 返回分析结果
        return response['message']['content']

    except FileNotFoundError:
        return f"文件 {file_path} 未找到。"
    except Exception as e:
        return f"分析时出错：{e}"

def demo_project_analysis():
    # 分析当前项目中的chat_server.py文件
    file_to_analyze = 'chat_server.py'  # 相对于gui目录

    print(f"正在分析项目文件: {file_to_analyze}")
    print("=" * 50)

    analysis = analyze_project_file(file_to_analyze)

    print("Ollama分析结果：")
    print(analysis)

if __name__ == "__main__":
    demo_project_analysis()