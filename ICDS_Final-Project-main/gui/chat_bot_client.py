from ollama import Client

class ChatBotClient:
    def __init__(self, name="bot", model="phi3:mini", host='http://localhost:11434'):
        self.name = name
        self.model = model
        self.client = Client(host=host)
        self.messages = []
        self.system_prompt = "You are a helpful assistant."
        self._init_messages()

    def _init_messages(self):
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def set_personality(self, personality_text):
        """设置机器人的性格"""
        self.system_prompt = f"You are {personality_text}. Respond briefly and friendly."
        self._init_messages()

    def chat(self, user_message):
        self.messages.append({"role": "user", "content": user_message})
        response = self.client.chat(self.model, messages=self.messages)
        reply = response["message"]["content"]
        self.messages.append({"role": "assistant", "content": reply})
        return reply