"""
Gateway Client Module
Provides a unified interface for calling the LLM Gateway across different protocols (OpenAI, Claude, Gemini).
Shared by call_gateway.py and diagnose_connection.py.
"""

import os
import json
import logging
import requests
from typing import Optional, List, Dict, Any, Generator

# Default Configuration
DEFAULT_GATEWAY_URL = "https://llm-gateway-proxy.inner.chj.cloud/llm-gateway"

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

from urllib.parse import urlparse, urlunparse

class GatewayClient:
    def __init__(self, api_key: str, model: str, base_url: str = DEFAULT_GATEWAY_URL):
        self.api_key = api_key
        self.model = model
        self.base_url = self._clean_base_url(base_url)
        self.protocol = self._detect_protocol(self.model)

    def _clean_base_url(self, url: str) -> str:
        """
        Cleans the Base URL by removing common endpoint suffixes.
        Ensures URL format: schema://host/path_prefix (no trailing slash)
        """
        url = url.strip()
        
        # Parse URL to handle query parameters or fragments safely
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        
        suffixes_to_remove = [
            '/v1/chat/completions',
            '/v1/messages',
            '/v1beta/models', 
            '/v1'
        ]
        
        original_path = path
        for suffix in suffixes_to_remove:
            if path.endswith(suffix):
                path = path[:-len(suffix)].rstrip('/')
                # If we stripped something, we stop checking other suffixes
                break
                
        if path != original_path:
             logger.warning(f"⚠️ 检测到 URL 包含 Endpoint 后缀，已自动修正 path: {original_path} -> {path}")

        # Reconstruct URL with cleaned path, keeping scheme/netloc
        # We discard query/params/fragment as they usually don't belong in a base_url
        clean_url = urlunparse((parsed.scheme, parsed.netloc, path, '', '', ''))
        return clean_url

    def _detect_protocol(self, model: str) -> str:
        """Detects protocol based on model name."""
        model_lower = model.lower()
        if 'claude' in model_lower:
            return 'claude'
        elif 'gemini' in model_lower:
            return 'gemini'
        else:
            return 'openai'

    def chat_completion(self, messages: List[Dict[str, str]], timeout: int = 60, **kwargs) -> str:
        """Non-streaming call."""
        if self.protocol == 'openai':
            return self._chat_openai(messages, timeout, stream=False, **kwargs)
        elif self.protocol == 'claude':
            return self._chat_claude(messages, timeout, stream=False, **kwargs)
        elif self.protocol == 'gemini':
            return self._chat_gemini(messages, timeout, stream=False, **kwargs)
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol}")

    def chat_completion_stream(self, messages: List[Dict[str, str]], timeout: int = 60, **kwargs) -> Generator[str, None, None]:
        """Streaming call."""
        if self.protocol == 'openai':
            yield from self._chat_openai_stream(messages, timeout, **kwargs)
        elif self.protocol == 'claude':
            yield from self._chat_claude_stream(messages, timeout, **kwargs)
        elif self.protocol == 'gemini':
            yield from self._chat_gemini_stream(messages, timeout, **kwargs)
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol}")

    # ==================== OpenAI Protocol ====================
    def _chat_openai(self, messages: List[Dict[str, str]], timeout: int, stream: bool, **kwargs) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"model": self.model, "messages": messages, "stream": stream}
        
        # Merge extra args
        if kwargs:
            payload.update(kwargs)

        try:
            logger.info(f"🚀 请求网关 (OpenAI, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response_data = response.json()
            
            if response.status_code != 200:
                logger.error(f"❌ 网关返回错误 (Status: {response.status_code}): {json.dumps(response_data)}")
                return f"❌ 接口失败: {response_data.get('error', '未知错误')}"

            if "choices" not in response_data or not response_data["choices"]:
                logger.error(f"❌ 响应缺少 'choices' 字段。原始响应: {json.dumps(response_data)}")
                return f"❌ 响应格式异常: {json.dumps(response_data)}"
                
            return response_data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"❌ 请求异常: {str(e)}")
            return f"❌ 调用失败: {e}"

    def _chat_openai_stream(self, messages: List[Dict[str, str]], timeout: int, **kwargs) -> Generator[str, None, None]:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"model": self.model, "messages": messages, "stream": True}
        
        if kwargs:
            payload.update(kwargs)

        try:
            logger.info(f"🚀 请求网关 (OpenAI Stream, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout, stream=True)
            
            if response.status_code != 200:
                yield f"❌ 接口失败: {response.text}"
                return

            for line in response.iter_lines():
                if not line: continue
                line_text = line.decode('utf-8').strip()
                
                if line_text.startswith("data:"):
                    data_str = line_text[5:].strip()
                    if data_str == "[DONE]": break
                    try:
                        chunk_data = json.loads(data_str)
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"❌ 流式请求异常: {str(e)}")
            yield f"❌ 调用失败: {e}"

    # ==================== Claude Protocol ====================
    def _chat_claude(self, messages: List[Dict[str, str]], timeout: int, stream: bool, **kwargs) -> str:
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Separate system prompts from messages
        system_prompts = []
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_prompts.append(msg.get("content", ""))
            else:
                filtered_messages.append(msg)

        payload = {
            "model": self.model,
            "max_tokens": 4096, # Default, can be overridden by kwargs
            "messages": filtered_messages,
            "stream": stream
        }
        
        if system_prompts:
            payload["system"] = "\n".join(system_prompts)
        
        if kwargs:
            payload.update(kwargs)

        try:
            logger.info(f"🚀 请求网关 (Claude, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            
            # Check status code first before parsing JSON to avoid crashes on 502/504
            if response.status_code != 200:
                try:
                    err_json = response.json()
                    err_msg = err_json.get('error', {}).get('message', '未知错误')
                    logger.error(f"❌ 网关返回错误 (Status: {response.status_code}): {json.dumps(err_json)}")
                    return f"❌ 接口失败: {err_msg}"
                except:
                    logger.error(f"❌ 网关返回错误 (Status: {response.status_code}): {response.text}")
                    return f"❌ 接口失败 (HTTP {response.status_code}): {response.text[:200]}"

            response_data = response.json()

            if "content" not in response_data or not response_data["content"]:
                logger.error(f"❌ 响应缺少 'content' 字段。原始响应: {json.dumps(response_data)}")
                return f"❌ 响应格式异常: {json.dumps(response_data)}"
                
            return response_data["content"][0]["text"]

        except Exception as e:
            logger.error(f"❌ 请求异常: {str(e)}")
            return f"❌ 调用失败: {e}"

    def _chat_claude_stream(self, messages: List[Dict[str, str]], timeout: int, **kwargs) -> Generator[str, None, None]:
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Separate system prompts from messages
        system_prompts = []
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_prompts.append(msg.get("content", ""))
            else:
                filtered_messages.append(msg)

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": filtered_messages,
            "stream": True
        }
        
        if system_prompts:
            payload["system"] = "\n".join(system_prompts)
        
        if kwargs:
            payload.update(kwargs)

        try:
            logger.info(f"🚀 请求网关 (Claude Stream, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout, stream=True)
            
            if response.status_code != 200:
                yield f"❌ 接口失败 (HTTP {response.status_code}): {response.text}"
                return

            for line in response.iter_lines():
                if not line: continue
                line_text = line.decode('utf-8').strip()
                if line_text.startswith("data:"):
                    data_str = line_text[5:].strip()
                    try:
                        chunk_data = json.loads(data_str)
                        type_ = chunk_data.get("type")
                        
                        if type_ == "content_block_delta":
                            delta = chunk_data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                content = delta.get("text", "")
                                if content:
                                    yield content
                        elif type_ == "error":
                            error_details = chunk_data.get("error", {})
                            yield f"❌ Stream Error: {error_details.get('message', 'Unknown')}"

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"❌ 流式请求异常: {str(e)}")
            yield f"❌ 调用失败: {e}"

    # ==================== Gemini Protocol ====================
    def _chat_gemini(self, messages: List[Dict[str, str]], timeout: int, stream: bool, **kwargs) -> str:
        action = "streamGenerateContent" if stream else "generateContent"
        url = f"{self.base_url}/v1beta/models/{self.model}:{action}"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Merge messages (User/Model strict alternation)
        merged_contents = []
        system_prompts = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompts.append(content)
                continue
            
            gemini_role = "model" if role == "assistant" else "user"
            
            # If the last message has the same role, append content
            if merged_contents and merged_contents[-1]["role"] == gemini_role:
                merged_contents[-1]["parts"][0]["text"] += "\n" + content
            else:
                merged_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
        
        if not merged_contents:
            if system_prompts:
                 # Only system prompts, treat as user message
                 merged_contents.append({
                     "role": "user",
                     "parts": [{"text": "\n".join(system_prompts)}]
                 })
                 system_prompts = []
            else:
                 return "❌ Error: No messages provided."

        # Ensure the conversation starts with a user message
        if merged_contents and merged_contents[0]["role"] == "model":
            merged_contents.insert(0, {
                "role": "user",
                "parts": [{"text": "..."}] # Placeholder to satisfy protocol
            })

        payload = {
            "contents": merged_contents,
            "generationConfig": {"temperature": 0.7, "topP": 1}
        }
        
        # Use native system_instruction if available (assuming v1beta supports it)
        # Otherwise prepend to first user message
        if system_prompts:
            payload["system_instruction"] = {
                "parts": [{"text": "\n".join(system_prompts)}]
            }

        if kwargs:
             payload.update(kwargs)

        try:
            logger.info(f"🚀 请求网关 (Gemini, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            
            if response.status_code != 200:
                 try:
                     err_json = response.json()
                     err_msg = err_json.get('error', {}).get('message', '未知错误')
                     logger.error(f"❌ 网关返回错误 (Status: {response.status_code}): {json.dumps(err_json)}")
                     return f"❌ 接口失败: {err_msg}"
                 except:
                     logger.error(f"❌ 网关返回错误 (Status: {response.status_code}): {response.text}")
                     return f"❌ 接口失败 (HTTP {response.status_code}): {response.text[:200]}"

            response_data = response.json()

            if "candidates" not in response_data:
                logger.error(f"❌ 响应缺少 'candidates' 字段。原始响应: {json.dumps(response_data)}")
                return f"❌ 响应格式异常: {json.dumps(response_data)}"
            
            candidates = response_data["candidates"]
            if not candidates:
                 return f"❌ 接收到的 candidates 为空。"
                 
            # Safety check for content
            first_candidate = candidates[0]
            if "content" not in first_candidate:
                finish_reason = first_candidate.get("finishReason", "UNKNOWN")
                return f"❌ 内容被拦截 (Reason: {finish_reason})"

            return first_candidate["content"]["parts"][0]["text"]

        except Exception as e:
            logger.error(f"❌ 请求异常: {str(e)}")
            return f"❌ 调用失败: {e}"

    def _chat_gemini_stream(self, messages: List[Dict[str, str]], timeout: int, **kwargs) -> Generator[str, None, None]:
        url = f"{self.base_url}/v1beta/models/{self.model}:streamGenerateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        merged_contents = []
        system_prompts = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_prompts.append(content)
                continue
            
            gemini_role = "model" if role == "assistant" else "user"
            
            if merged_contents and merged_contents[-1]["role"] == gemini_role:
                merged_contents[-1]["parts"][0]["text"] += "\n" + content
            else:
                merged_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
        
        if not merged_contents and system_prompts:
             merged_contents.append({
                 "role": "user",
                 "parts": [{"text": "\n".join(system_prompts)}]
             })
             system_prompts = []
        
        # Ensure the conversation starts with a user message
        if merged_contents and merged_contents[0]["role"] == "model":
            merged_contents.insert(0, {
                "role": "user",
                "parts": [{"text": "..."}] # Placeholder to satisfy protocol
            })

        payload = {
            "contents": merged_contents,
            "generationConfig": {"temperature": 0.7, "topP": 1}
        }
        
        if system_prompts:
            payload["system_instruction"] = {
                "parts": [{"text": "\n".join(system_prompts)}]
            }
        
        if kwargs:
            payload.update(kwargs)

        try:
            logger.info(f"🚀 请求网关 (Gemini Stream, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout, stream=True)
            
            if response.status_code != 200:
                yield f"❌ 接口失败 (HTTP {response.status_code}): {response.text}"
                return

            decoder = json.JSONDecoder()
            buffer = ""

            for line in response.iter_lines():
                if not line:
                    continue
                
                line_text = line.decode('utf-8')
                
                # 1. 尝试处理标准 SSE 格式 (data: {...})
                if line_text.startswith("data:"):
                    data_str = line_text[5:].strip()
                    if not data_str: continue
                    try:
                        obj = json.loads(data_str)
                        if "candidates" in obj and len(obj["candidates"]) > 0:
                            content_obj = obj["candidates"][0].get("content", {})
                            parts = content_obj.get("parts", [])
                            for part in parts:
                                if "text" in part:
                                    yield part["text"]
                    except json.JSONDecodeError:
                        pass
                    continue

                # 2. Fallback: 累积 buffer，处理 JSON 数组/对象流
                buffer += line_text
                
                while buffer:
                    buffer = buffer.lstrip()
                    if not buffer:
                        break
                    
                    if buffer.startswith(('[', ',', ']')):
                        buffer = buffer[1:]
                        continue
                    
                    try:
                        obj, idx = decoder.raw_decode(buffer)
                        
                        if "candidates" in obj:
                            if len(obj["candidates"]) > 0 and "content" in obj["candidates"][0]:
                                parts = obj["candidates"][0]["content"].get("parts", [])
                                for part in parts:
                                    if "text" in part:
                                        yield part["text"]
                        
                        buffer = buffer[idx:]
                        
                    except json.JSONDecodeError:
                        break

        except Exception as e:
            logger.error(f"❌ 流式请求异常: {str(e)}")
            yield f"❌ 调用失败: {e}"
