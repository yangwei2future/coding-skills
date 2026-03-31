# 不同框架的模型接入模式

本文档提供不同 LLM 框架接入公司内部模型的最佳实践。

## LangChain

### 使用 ChatOpenAI

```python
from langchain_openai import ChatOpenAI
import os

model = ChatOpenAI(
    model="openai/gpt-4o-mini",  # 使用公司内部模型名称
    api_key=os.getenv("AGENTOPS_API_KEY"),
    base_url=os.getenv("AGENTOPS_API_BASE")  # https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1
)

# 使用
response = model.invoke("Hello, world!")
print(response.content)
```

**关键点**:
- ✅ 使用 `base_url` 参数(不是 `api_base`)
- ✅ URL 不包含 `/chat/completions`(会自动添加)
- ✅ 使用公司内部模型名称格式

## LiteLLM

### 直接使用 LiteLLM

```python
from litellm import completion
import os

response = completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    api_key=os.getenv("AGENTOPS_API_KEY"),
    base_url=os.getenv("AGENTOPS_API_BASE")
)

print(response.choices[0].message.content)
```

**关键点**:
- ✅ 直接传递 `api_key` 和 `base_url` 参数(推荐)
- ⚠️ 不要仅依赖环境变量自动解析

### LiteLLM with ADK

```python
from adk.models import LiteLlm
import os

model = LiteLlm(
    model="openai/gpt-4o-mini",
    api_key=os.getenv("AGENTOPS_API_KEY"),
    base_url=os.getenv("AGENTOPS_API_BASE")
)

# 在 ADK Agent 中使用
agent = LlmAgent(
    model=model,
    name="my_agent",
    instruction="You are a helpful assistant"
)
```

## OpenAI SDK

### Python OpenAI SDK

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("AGENTOPS_API_KEY"),
    base_url=os.getenv("AGENTOPS_API_BASE")
)

response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.choices[0].message.content)
```

### Node.js OpenAI SDK

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: process.env.AGENTOPS_API_KEY,
  baseURL: process.env.AGENTOPS_API_BASE
});

const response = await client.chat.completions.create({
  model: 'openai/gpt-4o-mini',
  messages: [{ role: 'user', content: 'Hello' }]
});

console.log(response.choices[0].message.content);
```

## Anthropic SDK

对于使用 Anthropic SDK 的项目,需要切换到 OpenAI 兼容接口:

```python
# 原代码
from anthropic import Anthropic
client = Anthropic(api_key="sk-ant-...")

# 修改为使用 OpenAI SDK 调用公司模型
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("AGENTOPS_API_KEY"),
    base_url=os.getenv("AGENTOPS_API_BASE")
)

# 使用 anthropic/ 前缀的模型
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## 自定义 HTTP 调用

如果项目没有使用任何框架,可以使用 requests 库:

```python
import requests
import os

def call_model(messages, model="openai/gpt-4o-mini"):
    api_base = os.getenv("AGENTOPS_API_BASE")
    api_key = os.getenv("AGENTOPS_API_KEY")

    url = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": messages
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()

# 使用
result = call_model([{"role": "user", "content": "Hello"}])
print(result["choices"][0]["message"]["content"])
```

## 常见配置陷阱

### ❌ 错误: URL 路径重复

```python
# ❌ 错误
base_url = "https://llm-gateway.com/v1/chat/completions"
# 结果: https://llm-gateway.com/v1/chat/completions/chat/completions
```

### ✅ 正确: 只包含基础 URL

```python
# ✅ 正确
base_url = "https://llm-gateway.com/v1"
# 结果: https://llm-gateway.com/v1/chat/completions
```

### ❌ 错误: 依赖环境变量自动解析

```python
# ❌ 不推荐(可能失败)
os.environ["OPENAI_API_KEY"] = key
os.environ["OPENAI_API_BASE"] = base_url
model = ChatOpenAI(model="...")  # 可能无法正确使用自定义 Gateway
```

### ✅ 正确: 直接传递参数

```python
# ✅ 推荐
model = ChatOpenAI(
    model="...",
    api_key=key,
    base_url=base_url
)
```

## 环境变量配置

### .env 文件示例

```bash
# 公司内部模型配置
AGENTOPS_API_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...  # JWT Token (很长)
AGENTOPS_API_BASE=https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1
AGENTOPS_MODEL=openai/gpt-4o-mini
```

### 加载环境变量

```python
from dotenv import load_dotenv

# ⚠️ 重要: 使用 override=True 确保覆盖已有环境变量
load_dotenv(override=True)
```

**为什么需要 override=True?**
- Shell 环境中可能有旧的 API key
- `load_dotenv()` 默认不覆盖已存在的环境变量
- 使用 `override=True` 强制使用 .env 文件中的新值

## 验证配置

配置完成后,添加调试输出验证:

```python
import os

api_key = os.getenv("AGENTOPS_API_KEY", "")
api_base = os.getenv("AGENTOPS_API_BASE", "")

print(f"API Key length: {len(api_key)}")  # JWT Token 应该很长(>100)
print(f"API Base: {api_base}")
print(f"API Key ends with: ...{api_key[-20:]}")
```
