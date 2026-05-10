from ollama import Client

# 创建一个全局的 Ollama 客户端（不用每个请求都建）
client = Client(host='http://localhost:11434')
MODEL = "qwen2.5:7b-instruct"

def ask_llm(prompt: str) -> str:
    """发送 prompt 给 phi3:mini，返回回答文本"""
    response = client.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]