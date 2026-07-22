"""
API 接口模块 — 接入大语言模型增强数学建模分析

默认使用 DeepSeek V4 Pro，用户只需设置 API Key 即可使用。
支持所有兼容 OpenAI/Anthropic 接口的服务。

使用方式::

    from api import AIAnalyzer

    analyzer = AIAnalyzer()  # 自动读取 .env 中的 DEEPSEEK_API_KEY

    # 或显式指定
    analyzer = AIAnalyzer(api_key="sk-xxx", provider="deepseek")

    # AI 分析题目
    result = analyzer.analyze_problem("请建立综合评价模型...")

    # AI 推荐模型
    rec = analyzer.recommend_models(problem_text, data_summary)
"""

from api.client import LLMClient
from api.config import APIConfig, get_default_config
from api.analyzer import AIAnalyzer

__all__ = [
    "LLMClient",
    "APIConfig",
    "get_default_config",
    "AIAnalyzer",
]
