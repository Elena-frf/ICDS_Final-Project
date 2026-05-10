#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script for calling qwen2.5:7b-instruct model using Ollama
"""

from ollama import Client

def demo_qwen():
    # 创建Ollama客户端，连接到本地服务
    client = Client(host='http://localhost:11434')

    # 定义模型名称
    model = 'qwen2.5:7b-instruct'

    # 准备消息
    messages = [
        {'role': 'user', 'content': '请介绍一下你自己，并解释什么是大语言模型。'}
    ]

    try:
        # 调用chat方法
        response = client.chat(model=model, messages=messages)

        # 打印响应
        print("模型响应：")
        print(response['message']['content'])

    except Exception as e:
        print(f"调用模型时出错：{e}")
        print("请确保Ollama服务正在运行，并且模型已下载。")

if __name__ == "__main__":
    demo_qwen()