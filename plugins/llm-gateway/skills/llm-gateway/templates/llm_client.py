"""
LLM Gateway Client Template
This is the production-grade integration template for the LLM Gateway.
AI agents should copy this file to the user's project root when generating integration code.

Supports three protocols:
- OpenAI: azure-gpt-*, baidu-*, bailian-*, kivy-*, volcengine-*
- Claude: aws-claude-*, google-claude-*
- Gemini: gemini-*

SSE Format Compatibility:
- Supports both "data: {json}" (with space) and "data:{json}" (without space)
- All stream methods use line_text[5:].strip() to handle both formats

Required Dependencies:
    pip install requests python-dotenv
"""

import os
import json
import logging
import codecs
from typing import Optional, List, Dict, Any, Generator
from urllib.parse import urlparse, urlunparse

# 依赖检查
try:
    import requests
except ImportError:
    raise ImportError(
        "❌ 缺少依赖: requests\n"
        "💡 请安装: pip install requests python-dotenv"
    )

try:
    from dotenv import load_dotenv
except ImportError:
    raise ImportError(
        "❌ 缺少依赖: python-dotenv\n"
        "💡 请安装: pip install python-dotenv"
    )

# Default Configuration
DEFAULT_GATEWAY_URL = "https://llm-gateway-proxy.inner.chj.cloud/llm-gateway"

# 配置日志 (不使用 basicConfig,避免干扰用户配置)
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class LLMGatewayClient:
    def __init__(self, dotenv_path: Optional[str] = None, auto_load_env: bool = True):
        """
        初始化 LLM Gateway 客户端

        Args:
            dotenv_path: .env 文件路径 (可选)
                        - None: 自动向上搜索，直到遇到项目根目录 (.git 等)
                        - 相对/绝对路径: 使用指定的路径
            auto_load_env: 是否自动加载 .env 文件 (默认 True)
        """
        if auto_load_env:
            if dotenv_path:
                # 用户明确指定了路径
                if os.path.exists(dotenv_path):
                    load_dotenv(dotenv_path, override=True)
                    logger.debug(f"已加载 .env 文件: {dotenv_path}")
                else:
                    logger.warning(f"指定的 .env 文件不存在: {dotenv_path}")
            else:
                # 智能搜索：向上查找 .env，但不跨项目边界
                found_path = self._find_dotenv_in_project()
                if found_path:
                    load_dotenv(found_path, override=True)
                    logger.debug(f"已加载 .env 文件: {found_path}")
                else:
                    logger.warning("未找到 .env 文件，将使用系统环境变量")

        self.api_key = os.getenv("LX_LLM_GATEWAY_API_KEY")
        self.model = os.getenv("LX_LLM_GATEWAY_MODEL")

        # 获取并清洗 Base URL
        raw_url = os.getenv("LX_LLM_GATEWAY_URL", DEFAULT_GATEWAY_URL)
        self.base_url = self._clean_base_url(raw_url)

        if not self.api_key or not self.model:
            missing = []
            if not self.api_key:
                missing.append("LX_LLM_GATEWAY_API_KEY")
            if not self.model:
                missing.append("LX_LLM_GATEWAY_MODEL")

            error_msg = f"❌ 缺少必需的环境变量: {', '.join(missing)}\n"
            error_msg += "\n💡 解决方法:\n"
            error_msg += "1. 在项目根目录创建 .env 文件\n"
            error_msg += "2. 添加以下配置:\n"
            error_msg += "   LX_LLM_GATEWAY_API_KEY=your_api_key\n"
            error_msg += "   LX_LLM_GATEWAY_MODEL=your_model_id\n"
            error_msg += "   LX_LLM_GATEWAY_URL=https://llm-gateway-proxy.inner.chj.cloud/llm-gateway\n"
            error_msg += "   LX_LLM_GATEWAY_CONSUMER=your_app_name\n"
            error_msg += "\n3. 或者明确指定路径: LLMGatewayClient(dotenv_path='/path/to/.env')"
            raise EnvironmentError(error_msg)

        # 自动检测协议类型
        self.protocol = self._detect_protocol(self.model)
        logger.info(f"🔍 检测到协议类型: {self.protocol}")

    def _find_dotenv_in_project(self) -> Optional[str]:
        """
        在项目范围内向上搜索 .env 文件

        搜索策略:
        1. 从当前工作目录开始向上搜索
        2. 遇到项目根标志 (.git, pyproject.toml, setup.py 等) 就停止
        3. 不会跨项目边界搜索

        Returns:
            找到的 .env 文件绝对路径，如果未找到则返回 None
        """
        # 项目根目录标志 (按优先级排序)
        PROJECT_ROOT_MARKERS = [
            '.git',           # Git 仓库
            '.hg',            # Mercurial 仓库
            '.svn',           # SVN 仓库
            'pyproject.toml', # Python 项目配置
            'setup.py',       # Python 包
            'package.json',   # Node.js 项目
            'Cargo.toml',     # Rust 项目
            'go.mod',         # Go 项目
        ]

        current_dir = os.path.abspath(os.getcwd())
        searched_dirs = []

        while True:
            searched_dirs.append(current_dir)

            # 检查当前目录是否有 .env 文件
            dotenv_candidate = os.path.join(current_dir, '.env')
            if os.path.isfile(dotenv_candidate):
                logger.debug(f"找到 .env 文件: {dotenv_candidate}")
                return dotenv_candidate

            # 检查是否到达项目根目录
            is_project_root = any(
                os.path.exists(os.path.join(current_dir, marker))
                for marker in PROJECT_ROOT_MARKERS
            )

            if is_project_root:
                logger.debug(f"到达项目根目录: {current_dir}，停止搜索")
                break

            # 向上一级目录
            parent_dir = os.path.dirname(current_dir)

            # 已到达文件系统根目录
            if parent_dir == current_dir:
                logger.debug("到达文件系统根目录，停止搜索")
                break

            current_dir = parent_dir

        logger.debug(f"未找到 .env 文件，已搜索目录: {searched_dirs}")
        return None

    def _clean_base_url(self, url: str) -> str:
        """
        清洗 Base URL，去除可能误填的 endpoint 后缀。
        确保 URL 形式为: schema://host/path_prefix (无尾部斜杠)
        """
        url = url.strip()
        
        # Parse URL to handle query parameters or fragments safely
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        
        # 常见误填后缀列表 (注意顺序，长后缀优先匹配)
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
                break
        
        if path != original_path:
             logger.warning(f"⚠️ 检测到 URL 包含 Endpoint 后缀，已自动修正 path: {original_path} -> {path}")

        # Reconstruct URL with cleaned path
        clean_url = urlunparse((parsed.scheme, parsed.netloc, path, '', '', ''))
        return clean_url

    def _detect_protocol(self, model: str) -> str:
        """根据模型名称自动检测协议类型"""
        model_lower = model.lower()
        if 'claude' in model_lower:
            return 'claude'
        elif 'gemini' in model_lower:
            return 'gemini'
        else:
            return 'openai'

    def _adapt_messages_for_claude(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """适配 Claude 协议：提取 System Prompt，过滤 Messages"""
        system_prompts = []
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_prompts.append(msg.get("content", ""))
            else:
                filtered_messages.append(msg)
        
        result = {"messages": filtered_messages}
        if system_prompts:
            result["system"] = "\n".join(system_prompts)
        return result

    def _adapt_messages_for_gemini(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """适配 Gemini 协议：合并连续同角色消息，提取 System Instruction"""
        merged_contents = []
        system_prompts = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompts.append(content)
                continue
            
            gemini_role = "model" if role == "assistant" else "user"
            
            # 合并连续的同角色消息
            if merged_contents and merged_contents[-1]["role"] == gemini_role:
                merged_contents[-1]["parts"][0]["text"] += "\n" + content
            else:
                merged_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
        
        # 处理空消息情况（如果只有 system prompt）
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

        result = {"contents": merged_contents}
        
        if system_prompts:
            result["system_instruction"] = {
                "parts": [{"text": "\n".join(system_prompts)}]
            }
            
        return result

    def chat_completion(self, messages: List[Dict[str, str]], timeout: int = 60) -> str:
        """非流式调用"""
        if self.protocol == 'openai':
            return self._chat_openai(messages, timeout, stream=False)
        elif self.protocol == 'claude':
            return self._chat_claude(messages, timeout, stream=False)
        elif self.protocol == 'gemini':
            return self._chat_gemini(messages, timeout, stream=False)

    def chat_completion_stream(self, messages: List[Dict[str, str]], timeout: int = 60) -> Generator[str, None, None]:
        """流式调用"""
        if self.protocol == 'openai':
            yield from self._chat_openai_stream(messages, timeout)
        elif self.protocol == 'claude':
            yield from self._chat_claude_stream(messages, timeout)
        elif self.protocol == 'gemini':
            yield from self._chat_gemini_stream(messages, timeout)

    # ==================== OpenAI 协议 ====================
    def _chat_openai(self, messages: List[Dict[str, str]], timeout: int, stream: bool) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"model": self.model, "messages": messages, "stream": stream}

        try:
            logger.info(f"🚀 请求网关 (OpenAI, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response_data = response.json()
            
            if response.status_code != 200:
                logger.error(f"❌ 网关返回错误 (Status: {response.status_code}): {json.dumps(response_data)}")
                return f"❌ 接口失败: {response_data.get('error', '未知错误')}"

            if "choices" not in response_data:
                logger.error(f"❌ 响应缺少 'choices' 字段。原始响应: {json.dumps(response_data)}")
                return f"❌ 响应格式异常: {json.dumps(response_data)}"
                
            return response_data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"❌ 请求异常: {str(e)}")
            return f"❌ 调用失败: {e}"

    def _chat_openai_stream(self, messages: List[Dict[str, str]], timeout: int) -> Generator[str, None, None]:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"model": self.model, "messages": messages, "stream": True}

        try:
            logger.info(f"🚀 请求网关 (OpenAI Stream, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout, stream=True)

            if response.status_code != 200:
                yield f"❌ 接口失败: {response.text}"
                return

            # 使用增量解码器处理 UTF-8 多字节字符边界问题
            buffer = b""
            decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
            chunk_count = 0

            for chunk in response.iter_content(chunk_size=1):
                if not chunk:
                    continue

                buffer += chunk

                # 当遇到换行符时处理完整的行
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    # 使用增量解码器，自动处理不完整的 UTF-8 字节序列
                    line_text = decoder.decode(line, final=False).strip()

                    if not line_text:
                        continue

                    # 处理 SSE 格式（兼容 "data:" 和 "data: " 两种格式）
                    if line_text.startswith("data:"):
                        # 移除 "data:" 前缀后再 strip，兼容有无空格
                        data_str = line_text[5:].strip()
                        if data_str == "[DONE]":
                            logger.debug(f"收到 [DONE] 标记，共处理 {chunk_count} 个数据块")
                            return
                        try:
                            chunk_data = json.loads(data_str)
                            if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                                choice = chunk_data["choices"][0]
                                delta = choice.get("delta", {})

                                # 提取 content（支持完整内容和增量内容）
                                content = delta.get("content", "")
                                if content:
                                    chunk_count += 1
                                    logger.debug(f"数据块 {chunk_count}: content='{content[:20]}...' (长度: {len(content)})")
                                    yield content

                                # 记录 role（如果存在）
                                role = delta.get("role")
                                if role:
                                    logger.debug(f"数据块 {chunk_count}: role='{role}'")

                                # 检查是否结束
                                finish_reason = choice.get("finish_reason")
                                if finish_reason:
                                    logger.debug(f"流式结束: finish_reason='{finish_reason}'")

                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON 解析失败: {data_str[:100]}... 错误: {e}")
                            continue

        except Exception as e:
            logger.error(f"❌ 流式请求异常: {str(e)}")
            yield f"❌ 调用失败: {e}"

    # ==================== Claude 协议 ====================
    def _chat_claude(self, messages: List[Dict[str, str]], timeout: int, stream: bool) -> str:
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        adapted_data = self._adapt_messages_for_claude(messages)
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "stream": stream,
            **adapted_data
        }

        try:
            logger.info(f"🚀 请求网关 (Claude, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            
            # 优先检查状态码
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
            
            if "content" not in response_data:
                logger.error(f"❌ 响应缺少 'content' 字段。原始响应: {json.dumps(response_data)}")
                return f"❌ 响应格式异常: {json.dumps(response_data)}"
                
            return response_data["content"][0]["text"]

        except Exception as e:
            logger.error(f"❌ 请求异常: {str(e)}")
            return f"❌ 调用失败: {e}"

    def _chat_claude_stream(self, messages: List[Dict[str, str]], timeout: int) -> Generator[str, None, None]:
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        adapted_data = self._adapt_messages_for_claude(messages)
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "stream": True,
            **adapted_data
        }

        try:
            logger.info(f"🚀 请求网关 (Claude Stream, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout, stream=True)

            if response.status_code != 200:
                yield f"❌ 接口失败 (HTTP {response.status_code}): {response.text}"
                return

            # 使用增量解码器处理 UTF-8 多字节字符边界问题
            buffer = b""
            decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')

            for chunk in response.iter_content(chunk_size=1):
                if not chunk:
                    continue

                buffer += chunk

                # 当遇到换行符时处理完整的行
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    # 使用增量解码器，自动处理不完整的 UTF-8 字节序列
                    line_text = decoder.decode(line, final=False).strip()

                    if not line_text:
                        continue

                    # 处理 SSE 格式（兼容 "data:" 和 "data: " 两种格式）
                    if line_text.startswith("data:"):
                        # 移除 "data:" 前缀后再 strip，兼容有无空格
                        data_str = line_text[5:].strip()
                        try:
                            chunk_data = json.loads(data_str)
                            type_ = chunk_data.get("type")

                            if type_ == "content_block_delta":
                                delta = chunk_data.get("delta", {})
                                # 仅处理文本类型的 delta
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

    # ==================== Gemini 协议 ====================
    def _chat_gemini(self, messages: List[Dict[str, str]], timeout: int, stream: bool) -> str:
        # Gemini 使用不同的 URL 格式
        action = "streamGenerateContent" if stream else "generateContent"
        url = f"{self.base_url}/v1beta/models/{self.model}:{action}"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        adapted_data = self._adapt_messages_for_gemini(messages)
        if not adapted_data.get("contents"):
             return "❌ Error: No messages provided."

        payload = {
            "generationConfig": {"temperature": 0.7, "topP": 1},
            **adapted_data
        }

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
            if not candidates or not candidates[0].get("content"):
                 return f"❌ Empty candidates received."
                
            return candidates[0]["content"]["parts"][0]["text"]

        except Exception as e:
            logger.error(f"❌ 请求异常: {str(e)}")
            return f"❌ 调用失败: {e}"

    def _chat_gemini_stream(self, messages: List[Dict[str, str]], timeout: int) -> Generator[str, None, None]:
        url = f"{self.base_url}/v1beta/models/{self.model}:streamGenerateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        adapted_data = self._adapt_messages_for_gemini(messages)
        if not adapted_data.get("contents"):
             return

        payload = {
            "generationConfig": {"temperature": 0.7, "topP": 1},
            **adapted_data
        }

        try:
            logger.info(f"🚀 请求网关 (Gemini Stream, Model: {self.model})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout, stream=True)

            if response.status_code != 200:
                yield f"❌ 接口失败 (HTTP {response.status_code}): {response.text}"
                return

            # 使用增量解码器处理 UTF-8 多字节字符边界问题
            json_decoder = json.JSONDecoder()
            line_buffer = b""
            utf8_decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
            json_buffer = ""

            for chunk in response.iter_content(chunk_size=1):
                if not chunk:
                    continue

                line_buffer += chunk

                # 当遇到换行符时处理完整的行
                while b'\n' in line_buffer:
                    line, line_buffer = line_buffer.split(b'\n', 1)
                    # 使用增量解码器，自动处理不完整的 UTF-8 字节序列
                    line_text = utf8_decoder.decode(line, final=False)

                    if not line_text.strip():
                        continue

                    # 1. 尝试处理标准 SSE 格式（兼容 "data:" 和 "data: " 两种格式）
                    if line_text.startswith("data:"):
                        # 移除 "data:" 前缀后再 strip，兼容有无空格
                        data_str = line_text[5:].strip()
                        if not data_str:
                            continue
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

                    # 2. Fallback: 累积 json_buffer，处理 JSON 数组/对象流
                    json_buffer += line_text

                    while json_buffer:
                        # 去掉前导空白
                        json_buffer = json_buffer.lstrip()
                        if not json_buffer:
                            break

                        # 跳过数组符号和分隔符
                        if json_buffer.startswith(('[', ',', ']')):
                            json_buffer = json_buffer[1:]
                            continue

                        try:
                            # 尝试从 buffer 开头解析一个完整的 JSON 对象
                            obj, idx = json_decoder.raw_decode(json_buffer)

                            # 解析成功，处理数据
                            if "candidates" in obj:
                                # 检查结构是否存在
                                if len(obj["candidates"]) > 0 and "content" in obj["candidates"][0]:
                                    parts = obj["candidates"][0]["content"].get("parts", [])
                                    for part in parts:
                                        if "text" in part:
                                            yield part["text"]

                            # 移除已解析部分，继续处理 buffer 中剩余的数据
                            json_buffer = json_buffer[idx:]

                        except json.JSONDecodeError:
                            # buffer 中的数据还不足以构成一个完整的 JSON 对象
                            # 跳出内层循环，读取更多数据
                            break

        except Exception as e:
            logger.error(f"❌ 流式请求异常: {str(e)}")
            yield f"❌ 调用失败: {e}"

# ==================== Module-Level Wrappers ====================
_default_client: Optional[LLMGatewayClient] = None

def _get_default_client() -> LLMGatewayClient:
    global _default_client
    if _default_client is None:
        _default_client = LLMGatewayClient()
    return _default_client

def chat_completion(messages: List[Dict[str, str]], timeout: int = 60) -> str:
    """
    Module-level wrapper for simple usage.
    Automatically instantiates LLMGatewayClient using environment variables.
    """
    return _get_default_client().chat_completion(messages, timeout)

def chat_completion_stream(messages: List[Dict[str, str]], timeout: int = 60):
    """
    Module-level wrapper for simple usage.
    Automatically instantiates LLMGatewayClient using environment variables.
    """
    yield from _get_default_client().chat_completion_stream(messages, timeout)

if __name__ == "__main__":
    try:
        client = LLMGatewayClient()
        
        # 示例 1: 非流式调用
        print("=== 非流式调用 ===")
        result = client.chat_completion([{"role": "user", "content": "用一句话介绍 Python"}])
        print(result)
        
        # 示例 2: 流式调用
        print("\n=== 流式调用 ===")
        for chunk in client.chat_completion_stream([{"role": "user", "content": "用一句话介绍 Python"}]):
            print(chunk, end="", flush=True)
        print()  # 换行
    except Exception as e:
        print(f"Test failed: {e}")
