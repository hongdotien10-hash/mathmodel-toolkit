"""模型推荐引擎。

整合题型分类结果和数据画像，调用知识库进行模型推荐，
支持多子问题的组合方案生成。
"""

from __future__ import annotations

from typing import Optional

from mathmodel.analyzer.classifier import ProblemClassifier
from mathmodel.analyzer.knowledge_base import ModelKnowledgeBase, get_knowledge_base


class ModelRecommender:
    """模型推荐引擎。

    根据题目特征和数据画像，从知识库中检索并推荐最佳模型。

    Usage::

        recommender = ModelRecommender()
        plan = recommender.recommend(
            sub_problems=[{"id": 1, "title": "...", "type": "预测"}],
            data_profiles={"data": {"shape": (30, 5), ...}},
        )
        for sp in plan["sub_problems"]:
            print(sp["model"], sp["score"], sp["reason"])
    """

    def __init__(self, knowledge_base: Optional[ModelKnowledgeBase] = None):
        """
        Args:
            knowledge_base: 知识库实例，为 None 时使用全局单例
        """
        self.kb = knowledge_base or get_knowledge_base()
        self.classifier = ProblemClassifier(method="rule")

    def recommend(
        self,
        sub_problems: list[dict],
        data_profiles: Optional[dict] = None,
        top_k: int = 5,
        min_confidence: float = 0.3,
    ) -> dict:
        """为多个子问题推荐模型组合方案。

        Args:
            sub_problems: 子问题列表，每项含 id / title / type (或 full_text)
            data_profiles: 数据画像字典
            top_k: 每个子问题返回的前 K 个候选
            min_confidence: 最低置信度阈值

        Returns:
            dict: {
                "plan_id": 方案编号,
                "summary": 方案摘要,
                "confidence": 综合置信度,
                "sub_problems": [{id, title, type, candidates, recommended}],
            }
        """
        if data_profiles is None:
            data_profiles = {}

        sub_results = []

        for sp in sub_problems:
            sub_id = sp.get("id", len(sub_results) + 1)
            title = sp.get("title", "")

            # 如果还没有分类，先分类
            if "type" not in sp or sp["type"] == "综合":
                full_text = sp.get("full_text", title)
                classification = self.classifier.classify(full_text)
                ptype = classification["type"]
            else:
                ptype = sp["type"]

            # 从知识库检索
            candidates = self.kb.query(
                problem_type=ptype,
                data_profiles=data_profiles,
                top_k=top_k,
                min_score=min_confidence,
            )

            # 调整置信度（分类置信度 * 模型得分最高值）
            classification_confidence = sp.get("confidence", 0.5)
            if candidates:
                best_score = candidates[0]["score"]
                adjusted_confidence = classification_confidence * best_score
            else:
                adjusted_confidence = 0.0

            sub_results.append({
                "id": sub_id,
                "title": title[:150],
                "problem_type": ptype,
                "classification_confidence": classification_confidence,
                "candidates": candidates,
                "recommended": candidates[0] if candidates else None,
                "confidence": round(adjusted_confidence, 4),
            })

        # 组装方案
        avg_confidence = (
            sum(s["confidence"] for s in sub_results) / len(sub_results)
            if sub_results
            else 0.0
        )

        plan = {
            "plan_id": 1,
            "summary": " → ".join(
                s["recommended"]["model"] if s["recommended"] else "待定"
                for s in sub_results
            ),
            "confidence": round(avg_confidence, 4),
            "sub_problems": [
                {
                    "id": s["id"],
                    "title": s["title"],
                    "problem_type": s["problem_type"],
                    "model": s["recommended"]["model"] if s["recommended"] else "待人工选择",
                    "score": s["recommended"]["score"] if s["recommended"] else 0,
                    "confidence": s["confidence"],
                    "reason": s["recommended"]["reason"] if s["recommended"] else "",
                    "solver_path": s["recommended"]["solver_path"] if s["recommended"] else "",
                    "alternatives": s["candidates"][1:3] if len(s["candidates"]) > 1 else [],
                }
                for s in sub_results
            ],
        }

        return plan

    def recommend_all(
        self,
        sub_problems: list[dict],
        data_profiles: Optional[dict] = None,
        top_k: int = 5,
        num_plans: int = 3,
    ) -> list[dict]:
        """生成多个备选方案（Top-N 组合）。

        通过为不同子问题选择不同的候选模型，生成多样化的组合方案。

        Args:
            sub_problems: 子问题列表
            data_profiles: 数据画像
            top_k: 检索的候选数
            num_plans: 生成的方案数量

        Returns:
            list[dict]: 方案列表，按综合置信度降序
        """
        if data_profiles is None:
            data_profiles = {}

        # 先为每个子问题获取候选项
        sub_candidates = []
        for sp in sub_problems:
            sub_id = sp.get("id", len(sub_candidates) + 1)
            title = sp.get("title", "")

            if "type" not in sp:
                classification = self.classifier.classify(title)
                ptype = classification["type"]
            else:
                ptype = sp["type"]

            candidates = self.kb.query(
                problem_type=ptype,
                data_profiles=data_profiles,
                top_k=top_k,
            )

            sub_candidates.append({
                "id": sub_id,
                "title": title,
                "problem_type": ptype,
                "candidates": candidates,
            })

        # 生成组合方案
        plans = []
        # 方案1: 全部选最佳
        plan1 = self._build_plan(1, sub_candidates, lambda c: c[0] if c else None)
        plans.append(plan1)

        # 方案2: 交替选择（增加多样性）
        if num_plans >= 2:
            plan2 = self._build_plan(
                2, sub_candidates,
                lambda c: c[1] if len(c) > 1 else (c[0] if c else None),
            )
            plans.append(plan2)

        # 方案3: 全部选第3个（若有）
        if num_plans >= 3:
            plan3 = self._build_plan(
                3, sub_candidates,
                lambda c: c[2] if len(c) > 2 else (c[0] if c else None),
            )
            plans.append(plan3)

        # 按置信度降序
        plans.sort(key=lambda p: p["confidence"], reverse=True)
        return plans

    def _build_plan(self, plan_id: int, sub_candidates: list[dict],
                    selector) -> dict:
        """辅助方法：构建单个方案。"""
        sub_results = []
        for sc in sub_candidates:
            selected = selector(sc["candidates"])
            sub_results.append({
                "id": sc["id"],
                "title": sc["title"],
                "problem_type": sc["problem_type"],
                "model": selected["model"] if selected else "待定",
                "score": selected["score"] if selected else 0,
                "reason": selected["reason"] if selected else "",
                "solver_path": selected["solver_path"] if selected else "",
            })

        avg_conf = (
            sum(s["score"] for s in sub_results) / len(sub_results)
            if sub_results
            else 0.0
        )

        return {
            "plan_id": plan_id,
            "summary": " → ".join(s["model"] for s in sub_results),
            "confidence": round(avg_conf, 4),
            "sub_problems": sub_results,
        }

    def explain_recommendation(self, plan: dict) -> str:
        """解释推荐方案的详细理由。

        Args:
            plan: 推荐方案

        Returns:
            str: 可读的解释文本
        """
        lines = [f"方案 {plan.get('plan_id', '?')}: {plan.get('summary', '')}"]
        lines.append(f"综合置信度: {plan.get('confidence', 0):.1%}")
        lines.append("")

        for sp in plan.get("sub_problems", []):
            lines.append(f"  子问题 {sp['id']}: {sp.get('title', '')[:60]}")
            lines.append(f"    题型: {sp.get('problem_type', '?')}")
            lines.append(f"    推荐模型: {sp.get('model', '?')}")
            lines.append(f"    推荐分数: {sp.get('score', 0):.2f}")
            lines.append(f"    理由: {sp.get('reason', '无')}")
            if sp.get("alternatives"):
                lines.append(f"    备选: {', '.join(a['model'] for a in sp['alternatives'])}")
            lines.append("")

        return "\n".join(lines)
