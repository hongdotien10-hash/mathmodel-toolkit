"""
API 配置管理

默认配置为 DeepSeek V4 Pro，用户只需提供 API Key。
支持从 .env 文件、环境变量或代码参数加载配置。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ================================================================
# 预设提供商配置
# ================================================================

PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek V4 Pro",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-reasoner",
        "models": ["deepseek-reasoner", "deepseek-chat"],
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o3-mini"],
        "api_key_env": "OPENAI_API_KEY",
    },
    "anthropic": {
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-sonnet-5",
        "models": ["claude-sonnet-5", "claude-opus-4-8", "claude-haiku-4-5"],
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "zhipu": {
        "name": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-plus",
        "models": ["glm-4-plus", "glm-4-flash", "glm-4"],
        "api_key_env": "ZHIPU_API_KEY",
    },
    "moonshot": {
        "name": "Moonshot (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "api_key_env": "MOONSHOT_API_KEY",
    },
    "qwen": {
        "name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "models": ["qwen-plus", "qwen-max", "qwen-turbo"],
        "api_key_env": "DASHSCOPE_API_KEY",
    },
    "custom": {
        "name": "自定义兼容接口",
        "base_url": "https://your-api-endpoint.com/v1",
        "default_model": "your-model",
        "models": [],
        "api_key_env": "CUSTOM_API_KEY",
    },
}


# ================================================================
# 配置数据类
# ================================================================

@dataclass
class APIConfig:
    """API 配置。

    优先级：代码参数 > 环境变量 > .env 文件 > 默认值

    Attributes:
        provider: 服务提供商 (deepseek/openai/anthropic/zhipu/moonshot/qwen/custom)
        api_key: API 密钥（留空则自动从环境变量读取）
        base_url: API 端点地址（留空则使用提供商默认值）
        model: 模型名称（留空则使用提供商默认模型）
        max_tokens: 最大输出 token 数
        temperature: 生成温度 (0~2)
        timeout: 请求超时秒数
        max_retries: 最大重试次数
    """

    provider: str = "deepseek"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    max_tokens: int = 4096
    temperature: float = 0.3
    timeout: int = 60
    max_retries: int = 3

    def __post_init__(self):
        """自动从环境变量加载 API Key"""
        # 如果没提供 key，尝试从环境变量读取
        if not self.api_key:
            provider_info = PROVIDERS.get(self.provider, {})
            env_var = provider_info.get("api_key_env", "")
            if env_var:
                self.api_key = os.getenv(env_var, "")

            # 如果 provider-specific env 没设置，尝试通用的
            if not self.api_key:
                self.api_key = os.getenv("LLM_API_KEY", "")

        # 自动设置 base_url 和 model
        if not self.base_url or not self.model:
            provider_info = PROVIDERS.get(self.provider, {})
            if not self.base_url:
                self.base_url = provider_info.get("base_url", "")
            if not self.model:
                self.model = provider_info.get("default_model", "")

        # 尝试从 .env 文件加载
        self._load_dotenv()

    def _load_dotenv(self):
        """从项目 .env 文件加载配置"""
        # 查找 .env 文件
        search_paths = [
            Path.cwd() / ".env",
            Path(__file__).parent.parent / ".env",
            Path.home() / ".mathmodel.env",
        ]
        for env_path in search_paths:
            if env_path.exists():
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key, _, value = line.partition("=")
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                os.environ[key] = value
                except Exception:
                    pass

        # 重新读取环境变量（.env 文件可能已经加载了新值）
        if not self.api_key:
            provider_info = PROVIDERS.get(self.provider, {})
            env_var = provider_info.get("api_key_env", "")
            if env_var:
                self.api_key = os.getenv(env_var, self.api_key)
            if not self.api_key:
                self.api_key = os.getenv("LLM_API_KEY", self.api_key)

    @property
    def provider_name(self) -> str:
        """提供商显示名"""
        return PROVIDERS.get(self.provider, {}).get("name", self.provider)

    @property
    def is_configured(self) -> bool:
        """是否已配置 API Key"""
        return bool(self.api_key) and len(self.api_key) > 10

    @classmethod
    def deepseek(cls, api_key: str = "", model: str = "") -> "APIConfig":
        """快速创建 DeepSeek 配置"""
        return cls(provider="deepseek", api_key=api_key, model=model or "deepseek-chat")

    @classmethod
    def openai(cls, api_key: str = "", model: str = "") -> "APIConfig":
        """快速创建 OpenAI 配置"""
        return cls(provider="openai", api_key=api_key, model=model or "gpt-4o")

    @classmethod
    def anthropic(cls, api_key: str = "", model: str = "") -> "APIConfig":
        """快速创建 Anthropic 配置"""
        return cls(provider="anthropic", api_key=api_key, model=model or "claude-sonnet-5")


# ================================================================
# 全局默认配置
# ================================================================

_default_config: Optional[APIConfig] = None


def get_default_config() -> APIConfig:
    """获取全局 API 配置（单例）"""
    global _default_config
    if _default_config is None:
        _default_config = APIConfig()
    return _default_config


def set_default_config(config: APIConfig):
    """设置全局 API 配置"""
    global _default_config
    _default_config = config
