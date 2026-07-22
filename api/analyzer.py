"""
AI 增强分析器

使用大语言模型进行：
- 题目理解与子问题拆分
- 更精准的题型分类
- 模型推荐与方案生成
- 论文摘要和章节撰写

所有方法都有本地回退：API 不可用时自动使用基于规则的本地方法。
"""

from __future__ import annotations

import json
from typing import Optional

from api.client import LLMClient
from api.config import APIConfig, get_default_config


class AIAnalyzer:
    """AI 增强的数学建模分析器。

    使用 LLM 增强题目分析、模型推荐和论文撰写。
    API 不可用时自动回退到本地规则引擎。

    Usage::

        analyzer = AIAnalyzer()  # 自动使用 DeepSeek

        # 指定配置
        analyzer = AIAnalyzer(APIConfig.deepseek("sk-xxx"))

        # 分析题目
        result = analyzer.analyze_problem("请建立综合评价模型...")
        print(result["type"])        # "评价"
        print(result["confidence"])  # 0.95

        # 推荐模型
        rec = analyzer.recommend_models(
            problem="建立优化模型选择配送中心...",
            data_summary="5个备选地点，含成本和覆盖人口",
        )
    """

    # ==================================================================
    # 提示词模板
    # ==================================================================

    SYSTEM_PROMPT = """你是一位资深的数学建模竞赛专家，精通 CUMCM（国赛）和 MCM/ICM（美赛）。

你的任务是：
1. 分析题目，识别子问题的题型（优化/预测/评价/分类/微分方程/统计/图论）
2. 为每个子问题推荐最合适的数学模型
3. 撰写高质量的论文摘要和章节

请始终提供具体的、可验证的推荐，并说明推荐理由。
回答请使用中文，模型名称使用中文。"""

    ANALYZE_PROMPT = """请分析以下数学建模题目，识别所有子问题并对每个子问题进行题型分类。

题目内容：
{problem}

请以 JSON 格式返回（不要包含其他文字）：
{{
    "sub_problems": [
        {{
            "id": 1,
            "title": "子问题简述",
            "type": "优化/预测/评价/分类/微分方程/统计/图论/综合",
            "confidence": 0.95,
            "keywords": ["关键词1", "关键词2"],
            "reason": "分类理由"
        }}
    ],
    "overall_theme": "题目整体主题",
    "difficulty": "easy/medium/hard",
    "estimated_models": ["需要的模型类型"]
}}"""

    RECOMMEND_PROMPT = """请为以下数学建模子问题推荐最合适的数学模型。

子问题：{problem}
题型：{problem_type}
数据情况：{data_summary}

请考虑：
- 数据特征（样本量、维度、类型）
- 模型的可解释性（竞赛论文要求）
- 模型在数学建模竞赛中的使用频率和成熟度

请以 JSON 格式返回 Top-3 推荐（不要包含其他文字）：
{{
    "recommendations": [
        {{
            "rank": 1,
            "model": "模型名称（中文优先）",
            "score": 0.95,
            "reason": "详细推荐理由",
            "pros": ["优点1", "优点2"],
            "cons": ["缺点1"],
            "python_lib": "Python库名"
        }}
    ],
    "best_choice": "最推荐的模型",
    "alternative_approach": "备选方案"
}}"""

    PAPER_ABSTRACT_PROMPT = """请为以下数学建模论文撰写摘要。

题目：{problem}
使用模型：{models}
主要结果：{results}

要求：
1. 200-300字
2. 包含问题背景、建模方法、主要结论
3. 包含具体的数值结果
4. 语言简洁、专业

请直接输出摘要文本，不需要 JSON 格式。"""

    # ==================================================================
    # 初始化
    # ==================================================================

    def __init__(self, config: Optional[APIConfig] = None):
        """
        Args:
            config: API 配置，None 时自动读取环境变量默认 DeepSeek
        """
        self.config = config or get_default_config()
        self._client: Optional[LLMClient] = None
        self._api_available: Optional[bool] = None

    @property
    def client(self) -> LLMClient:
        """懒初始化 LLM 客户端"""
        if self._client is None:
            self._client = LLMClient(self.config)
        return self._client

    @property
    def api_available(self) -> bool:
        """检查 API 是否可用"""
        if self._api_available is None:
            if not self.config.is_configured:
                self._api_available = False
            else:
                try:
                    result = self.client.test_connection()
                    self._api_available = result.get("ok", False)
                except Exception:
                    self._api_available = False
        return self._api_available

    # ==================================================================
    # 题目分析
    # ==================================================================

    def analyze_problem(self, problem_text: str) -> dict:
        """AI 分析题目，识别子问题和题型。

        Args:
            problem_text: 完整的题目文本

        Returns:
            dict: {
                "sub_problems": [...],
                "overall_theme": "...",
                "difficulty": "...",
                "source": "ai" | "rule"
            }
        """
        if self.api_available:
            try:
                prompt = self.ANALYZE_PROMPT.format(problem=problem_text[:4000])
                result = self.client.chat_json(prompt, system_prompt=self.SYSTEM_PROMPT)
                result["source"] = "ai"
                return result
            except Exception as e:
                print(f"  [AI] API 调用失败，回退到规则引擎: {e}")

        # 本地回退
        return self._analyze_local(problem_text)

    def _analyze_local(self, problem_text: str) -> dict:
        """本地规则引擎分析（API 不可用时的回退）"""
        from mathmodel.analyzer import ProblemClassifier
        from mathmodel.parser import ProblemSplitter

        splitter = ProblemSplitter()
        classifier = ProblemClassifier()

        sub_raw = splitter.split(problem_text)
        sub_problems = []

        for sp in sub_raw:
            clf = classifier.classify(sp.get("content", sp.get("title", "")))
            sub_problems.append({
                "id": sp.get("id", len(sub_problems) + 1),
                "title": sp.get("title", "")[:150],
                "type": clf["type"],
                "confidence": clf["confidence"],
                "keywords": [clf["type"]],
                "reason": f"规则匹配: {clf.get('scores', {})}",
            })

        return {
            "sub_problems": sub_problems,
            "overall_theme": "综合数学建模问题",
            "difficulty": "medium",
            "source": "rule",
        }

    # ==================================================================
    # 模型推荐
    # ==================================================================

    def recommend_models(
        self,
        problem: str,
        problem_type: str = "",
        data_summary: str = "",
        top_k: int = 3,
    ) -> dict:
        """AI 推荐的模型。

        Args:
            problem: 子问题描述
            problem_type: 已知的题型（可选）
            data_summary: 数据情况描述
            top_k: 返回前 K 个推荐

        Returns:
            dict: 推荐结果
        """
        if self.api_available:
            try:
                ptype = problem_type or "未知"
                dsum = data_summary or "未知"
                prompt = self.RECOMMEND_PROMPT.format(
                    problem=problem[:2000],
                    problem_type=ptype,
                    data_summary=dsum,
                )
                result = self.client.chat_json(prompt, system_prompt=self.SYSTEM_PROMPT)
                result["source"] = "ai"
                return result
            except Exception as e:
                print(f"  [AI] 推荐失败，回退到知识库: {e}")

        # 本地回退：使用知识库
        return self._recommend_local(problem, problem_type, data_summary, top_k)

    def _recommend_local(
        self,
        problem: str,
        problem_type: str,
        data_summary: str,
        top_k: int,
    ) -> dict:
        """本地知识库推荐"""
        from mathmodel.analyzer import ProblemClassifier, ModelKnowledgeBase

        classifier = ProblemClassifier()
        kb = ModelKnowledgeBase()

        if not problem_type:
            clf = classifier.classify(problem)
            problem_type = clf["type"]

        candidates = kb.query(problem_type=problem_type, top_k=top_k)

        return {
            "recommendations": [
                {
                    "rank": i + 1,
                    "model": c["model"],
                    "score": c["score"],
                    "reason": c["reason"],
                    "python_lib": c.get("solver_path", ""),
                }
                for i, c in enumerate(candidates)
            ],
            "best_choice": candidates[0]["model"] if candidates else "待定",
            "source": "rule",
        }

    # ==================================================================
    # 批量分析（全流程）
    # ==================================================================

    def full_analysis(
        self,
        problem_text: str,
        data_summary: str = "",
    ) -> dict:
        """完整的 AI 分析流程：题目分析 + 模型推荐。

        Args:
            problem_text: 完整题目文本
            data_summary: 数据附件简述

        Returns:
            dict: {
                "problem_analysis": {...},
                "model_recommendations": [...],
                "source": "ai" | "rule"
            }
        """
        analysis = self.analyze_problem(problem_text)

        recommendations = []
        for sp in analysis.get("sub_problems", []):
            rec = self.recommend_models(
                problem=sp.get("title", ""),
                problem_type=sp.get("type", ""),
                data_summary=data_summary,
            )
            recommendations.append({
                "sub_problem_id": sp["id"],
                "sub_problem_type": sp["type"],
                "recommendations": rec.get("recommendations", []),
                "best_choice": rec.get("best_choice", ""),
            })

        return {
            "problem_analysis": analysis,
            "model_recommendations": recommendations,
            "source": analysis.get("source", "rule"),
        }

    # ==================================================================
    # 论文辅助
    # ==================================================================

    def generate_abstract(
        self,
        problem: str,
        models: str,
        results: str,
    ) -> str:
        """AI 生成论文摘要。

        Args:
            problem: 题目简述
            models: 使用的模型列表
            results: 主要结果

        Returns:
            str: 摘要文本
        """
        if self.api_available:
            try:
                prompt = self.PAPER_ABSTRACT_PROMPT.format(
                    problem=problem[:1000],
                    models=models,
                    results=results[:500],
                )
                return self.client.chat(prompt, system_prompt=self.SYSTEM_PROMPT)
            except Exception:
                pass

        # 本地回退
        return f"本文针对{problem[:50]}...，综合运用{models}等方法进行建模求解。{results}"

    def polish_text(self, text: str, style: str = "academic") -> str:
        """AI 润色文本。

        Args:
            text: 原始文本
            style: 风格 (academic/concise/english)

        Returns:
            str: 润色后的文本
        """
        if not self.api_available:
            return text

        prompts = {
            "academic": "请将以下文字润色为学术论文风格，保持原意不变",
            "concise": "请将以下文字精简，去除冗余",
            "english": "请将以下中文翻译为英文科技论文风格",
        }

        try:
            return self.client.chat(
                f"{prompts.get(style, prompts['academic'])}：\n\n{text}",
                system_prompt="你是学术写作助手。只输出润色后的文字，不要解释。",
                temperature=0.3,
            )
        except Exception:
            return text


# ================================================================
# 便捷函数
# ================================================================

def create_analyzer(
    api_key: str = "",
    provider: str = "deepseek",
    model: str = "",
) -> AIAnalyzer:
    """快速创建 AI 分析器。

    Args:
        api_key: API 密钥（留空则从环境变量读取）
        provider: 提供商 (deepseek/openai/anthropic/...)
        model: 模型名称（留空则自动选择）

    Returns:
        AIAnalyzer 实例
    """
    config = APIConfig(provider=provider, api_key=api_key, model=model)
    return AIAnalyzer(config)
