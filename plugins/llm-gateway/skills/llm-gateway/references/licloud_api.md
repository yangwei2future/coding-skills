# 融合云 AgentOps API 参考文档

## 公司内部支持的模型列表

### OpenAI 协议模型

| 模型名称 | 说明 |
|---------|------|
| `azure-gpt-5_2` | Azure GPT-5.2 标准版 |
| `azure-gpt-5_2-chat` | Azure GPT-5.2 对话版 |

**协议**: OpenAI 标准协议
**Base URL**: `https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1`

### Gemini 协议模型

| 模型名称 | 说明 |
|---------|------|
| `gemini-3-pro-preview` | Gemini 3 Pro 预览版 |
| `gemini-3-flash-preview` | Gemini 3 Flash 预览版 |
| `gemini-3-pro-image-preview` | Gemini 3 Pro 图像预览版 |

**协议**: Gemini 原生协议
**Base URL**: `https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1beta`

### Claude 协议模型

| 模型名称 | 说明 |
|---------|------|
| `aws-claude-sonnet-4-5` | AWS Claude Sonnet 4.5 |
| `google-claude-haiku-4-5` | Google Cloud Claude Haiku 4.5 |

**协议**: Claude 原生协议
**Base URL**: `https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1`

## 三种协议调用格式

### 1. OpenAI 标准协议

**适用模型**: `azure-gpt-5_2`, `azure-gpt-5_2-chat`

**API 端点**:
```
POST https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1/chat/completions
```

**请求头**:
```
Authorization: <JWT Token>
Content-Type: application/json
```

**请求体**:
```json
{
    "model": "azure-gpt-5_2",
    "messages": [
        {
            "role": "system",
            "content": "你是乐于助人的小助理"
        },
        {
            "role": "user",
            "content": "讲一个笑话"
        }
    ],
    "stream": true
}
```

**curl 示例**:
```bash
curl --location 'https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1/chat/completions' \
--header 'Authorization: <你的JWT Token>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "azure-gpt-5_2",
    "messages": [
        {
            "role": "system",
            "content": "你是乐于助人的小助理"
        },
        {
            "role": "user",
            "content": "讲一个笑话"
        }
    ],
    "stream": true
}'
```

### 2. Gemini 原生协议

**适用模型**: `gemini-3-pro-preview`, `gemini-3-flash-preview`, `gemini-3-pro-image-preview`

**API 端点**:
```
POST https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1beta/models/{model}:streamGenerateContent
```

**请求头**:
```
x-goog-api-key: <JWT Token>
Content-Type: application/json
```

**请求体**:
```json
{
    "contents": [
        {
            "parts": [
               {
                "text": "你好"
               }
            ],
            "role": "user"
        },
        {
            "parts": [
                {
                    "text": "Got it. Thanks for the context!"
                }
            ],
            "role": "model"
        },
        {
            "parts": [
                {
                    "text": "解释一下当前的项目"
                }
            ],
            "role": "user"
        }
    ],
    "generationConfig": {
        "temperature": 0,
        "topP": 1,
        "thinkingConfig": {
            "includeThoughts": false,
            "thinkingLevel": "LOW"
        }
    }
}
```

**curl 示例**:
```bash
curl --location 'https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1beta/models/gemini-3-flash-preview:streamGenerateContent' \
--header 'x-goog-api-key: <你的JWT Token>' \
--header 'Content-Type: application/json' \
--data '{
    "contents": [
        {
            "parts": [
               {
                "text": "你好"
               }
            ],
            "role": "user"
        }
    ],
    "generationConfig": {
        "temperature": 0,
        "topP": 1
    }
}'
```

### 3. Claude 原生协议

**适用模型**: `aws-claude-sonnet-4-5`, `google-claude-haiku-4-5`

**API 端点**:
```
POST https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1/messages
```

**请求头**:
```
x-api-key: <JWT Token>
Content-Type: application/json
```

**请求体**:
```json
{
    "max_tokens": 16000,
    "thinking": {
        "type": "enabled",
        "budget_tokens": 10000
    },
    "messages": [
        {
            "role": "user",
            "content": "给我讲个笑话"
        }
    ],
    "stream": true,
    "model": "aws-claude-sonnet-4-5"
}
```

**curl 示例**:
```bash
curl --location 'https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1/messages' \
--header 'x-api-key: <你的JWT Token>' \
--header 'Content-Type: application/json' \
--data '{
    "max_tokens": 16000,
    "thinking": {
        "type": "enabled",
        "budget_tokens": 10000
    },
    "messages": [
        {
            "role": "user",
            "content": "给我讲个笑话"
        }
    ],
    "stream": true,
    "model": "aws-claude-sonnet-4-5"
}'
```

## 获取 API Token

### 接口地址 (Mock)
```
GET https://api.licloud.com/v1/agent-ops/tokens
```

### 请求头
```
Authorization: Bearer <融合云登录 token>
```

### 响应示例
```json
{
  "tokens": [
    {
      "id": "token-123",
      "name": "默认 Token",
      "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "created_at": "2024-01-01T00:00:00Z",
      "expires_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

## 创建工单 (Mock)

如果遇到问题,可以创建工单寻求帮助。

### 接口地址 (Mock)
```
POST https://api.licloud.com/v1/tickets
```

### 请求体
```json
{
  "category": "agentops-model-integration",
  "title": "模型接入问题",
  "description": "问题描述...",
  "priority": "normal"
}
```

### 响应示例
```json
{
  "ticket_id": "TICKET-12345",
  "status": "open",
  "url": "https://ticket.licloud.com/TICKET-12345"
}
```
