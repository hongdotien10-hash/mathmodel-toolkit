"""
统一 LLM 客户端

支持 OpenAI-compatible 和 Anthropic-compatible 两种 API 格式。
默认使用 DeepSeek V4 Pro，自动处理重试和错误。
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from typing import Optional

from api.config import APIConfig, get_default_config, PROVIDERS


class LLMClient:
    """统一的大语言模型调用客户端。

    支持 OpenAI 兼容接口（DeepSeek / OpenAI / 智谱 / 通义千问 等）
    和 Anthropic 原生接口。

    Usage::

        # 使用默认配置（DeepSeek）
        client = LLMClient()

        # 或指定配置
        client = LLMClient(APIConfig(provider="openai", api_key="sk-xxx"))

        # 对话
        reply = client.chat("分析这个数学建模问题...")

        # JSON 结构化输出
        result = client.chat_json("请以JSON格式返回模型推荐...")
    """

    def __init__(self, config: Optional[APIConfig] = None):
        """
        Args:
            config: API 配置，None 时使用全局默认配置
        """
        self.config = config or get_default_config()
        self._provider_info = PROVIDERS.get(self.config.provider, {})

    # ==================================================================
    # 公共接口
    # ==================================================================

    def chat(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """发送对话请求，返回文本回复。

        Args:
            prompt: 用户消息
            system_prompt: 系统提示词
            temperature: 温度参数（None 使用配置默认值）
            max_tokens: 最大输出 token

        Returns:
            str: 模型回复文本
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self._call_with_retry(
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
        )

    def chat_json(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
    ) -> dict:
        """请求 JSON 结构化输出。

        Args:
            prompt: 用户消息（应包含 JSON 格式要求）
            system_prompt: 系统提示词
            temperature: 温度（JSON 输出建议低温度）

        Returns:
            dict: 解析后的 JSON 对象
        """
        json_system = system_prompt or "你是一个数学建模专家，请以 JSON 格式回答。"
        full_prompt = prompt + "\n\n请严格按照 JSON 格式输出，不要包含其他文字。"

        for attempt in range(self.config.max_retries):
            try:
                text = self.chat(full_prompt, system_prompt=json_system,
                                 temperature=temperature)
                # 尝试从回复中提取 JSON
                return self._extract_json(text)
            except (json.JSONDecodeError, ValueError) as e:
                if attempt == self.config.max_retries - 1:
                    raise ValueError(f"JSON 解析失败（已重试 {self.config.max_retries} 次）: {e}")
                time.sleep(1 * (attempt + 1))

        return {}

    # ==================================================================
    # 底层调用
    # ==================================================================

    def _call_with_retry(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """带重试的 API 调用"""
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                return self._call_api(messages, temperature, max_tokens)
            except urllib.error.HTTPError as e:
                last_error = e
                status = e.code
                # 速率限制或服务器错误，等待后重试
                if status in (429, 500, 502, 503):
                    wait = min(2 ** attempt * 2, 30)
                    print(f"  [API] HTTP {status}, 等待 {wait}s 后重试 ({attempt+1}/{self.config.max_retries})")
                    time.sleep(wait)
                    continue
                raise
            except urllib.error.URLError as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    time.sleep(2)
                    continue
                raise

        raise RuntimeError(f"API 调用失败（已重试 {self.config.max_retries} 次）: {last_error}")

    def _call_api(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """实际调用 API"""
        if self.config.provider == "anthropic":
            return self._call_anthropic(messages, temperature, max_tokens)
        else:
            return self._call_openai_compatible(messages, temperature, max_tokens)

    def _call_openai_compatible(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """调用 OpenAI 兼容 API"""
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"

        body = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        data = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        return result["choices"][0]["message"]["content"]

    def _call_anthropic(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """调用 Anthropic API"""
        url = f"{self.config.base_url.rstrip('/')}/messages"

        # 分离 system 消息
        system = ""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                anthropic_messages.append(msg)

        body = {
            "model": self.config.model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            body["system"] = system

        data = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        # Anthropic 返回格式不同
        content = result.get("content", [{}])
        if isinstance(content, list) and len(content) > 0:
            return content[0].get("text", "")
        return str(content)

    # ==================================================================
    # 工具方法
    # ==================================================================

    @staticmethod
    def _extract_json(text: str) -> dict:
        """从文本中提取 JSON 对象"""
        text = text.strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 markdown code block 中的 JSON
        import re
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            return json.loads(match.group(1))

        # 尝试找到第一个 { 和最后一个 }
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])

        raise ValueError(f"无法从回复中提取 JSON: {text[:200]}...")

    # ==================================================================
    # 便捷方法
    # ==================================================================

    def test_connection(self) -> dict:
        """测试 API 连接"""
        try:
            start = time.perf_counter()
            reply = self.chat("请回复 'OK'", system_prompt="", max_tokens=10)
            elapsed = time.perf_counter() - start
            return {
                "ok": True,
                "provider": self.config.provider_name,
                "model": self.config.model,
                "latency": round(elapsed, 2),
                "reply": reply[:50],
            }
        except Exception as e:
            return {
                "ok": False,
                "provider": self.config.provider_name,
                "model": self.config.model,
                "error": str(e),
            }
