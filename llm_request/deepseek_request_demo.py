# Please install OpenAI SDK first: `pip3 install openai`
import os
import json
from openai import OpenAI
from pydantic import Json

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个专业助手，回答清晰直接。"},
        {"role": "user", "content": "用中文解释什么是 RAG"},
    ],
    stream=False
)

# for chunk in response:
#     print(json.dumps(chunk.model_dump(), ensure_ascii=False, indent=2))

print(type(response))
print(json.dumps(response.model_dump(), ensure_ascii=False, indent=2))