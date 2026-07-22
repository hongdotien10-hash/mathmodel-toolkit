"""题型分类器。

基于题目文本和预处理特征，将各子问题归类到以下题型之一：
优化 / 预测 / 评价 / 分类 / 微分方程 / 统计 / 图论 / 综合
"""

from __future__ import annotations

import re
from typing import Optional


# ---- 题型定义 ---------------------------------------------------------------

PROBLEM_TYPES = ["优化", "预测", "评价", "分类", "微分方程", "统计", "图论", "综合"]

# 题型↔关键词映射（关键词越靠前权重越高）
TYPE_KEYWORDS: dict[str, list[str]] = {
    "优化": [
        "优化", "最优", "最大化", "最小化", "极大化", "极小化",
        "目标函数", "约束条件", "线性规划", "非线性规划", "整数规划",
        "动态规划", "多目标", "调度", "分配", "资源", "成本最低",
        "效率最高", "利润最大", "路径最短",
    ],
    "预测": [
        "预测", "预报", "趋势", "未来", "走势", "预期", "推测",
        "估计", "展望", "预判", "时序", "时间序列",
    ],
    "评价": [
        "评价", "评估", "打分", "排名", "排序", "优劣", "等级",
        "绩效", "综合", "指标", "权重", "体系", "考核", "评比",
        "筛选", "选优",
    ],
    "分类": [
        "分类", "识别", "判别", "诊断", "聚类", "归类", "区分",
        "模式识别", "特征提取",
    ],
    "微分方程": [
        "微分方程", "微分", "导数", "变化率", "动力系统", "动力学",
        "传播", "扩散", "传染", "种群", "增长模型", "衰变",
        "流动", "扩散方程",
    ],
    "统计": [
        "回归", "相关", "显著性", "假设检验", "t检验", "卡方",
        "方差分析", "分布", "概率", "置信区间", "抽样",
    ],
    "图论": [
        "路径", "最短路径", "网络", "节点", "边", "连通",
        "遍历", "旅行商", "TSP", "最大流", "最小生成树",
        "拓扑", "路由",
    ],
}

# 编译正则模式（预编译提升性能）
_PATTERNS: dict[str, list[re.Pattern]] = {}
for _ptype, _kws in TYPE_KEYWORDS.items():
    _PATTERNS[_ptype] = [re.compile(re.escape(kw)) for kw in _kws]


class ProblemClassifier:
    """题型分类器。

    支持两种分类模式：
    1. **规则模式**（默认）— 基于关键词匹配，速度快，可解释
    2. **ML 模式**— 基于嵌入向量的分类（需要较大语料训练）

    Usage::

        clf = ProblemClassifier()
        result = clf.classify("请建立模型优化生产调度方案...")
        print(result["type"])    # "优化"
        print(result["scores"])  # {"优化": 0.6, "图论": 0.3, ...}
    """

    def __init__(self, method: str = "rule"):
        """
        Args:
            method: 分类方法，可选 "rule" (规则) 或 "ml" (机器学习)
        """
        self.method = method
        if method == "ml":
            self._init_ml_classifier()

    def classify(self, text: str) -> dict:
        """对输入文本进行题型分类。

        Args:
            text: 题目文本（通常是子问题的描述）

        Returns:
            dict: {"type": 最优题型, "scores": {题型: 分数}, "confidence": 置信度}
        """
        if self.method == "ml":
            return self._classify_ml(text)
        return self._classify_rule(text)

    def classify_all(self, sub_problems: list[dict]) -> list[dict]:
        """对多个子问题批量分类。

        Args:
            sub_problems: 子问题列表，每项至少含 "title" 字段

        Returns:
            list[dict]: 分类结果列表
        """
        results = []
        for sp in sub_problems:
            title = sp.get("title", "")
            # 如果题目有更长的描述文本，也一并纳入
            full_text = sp.get("full_text", title)
            classification = self.classify(full_text)
            results.append({
                "id": sp.get("id", len(results) + 1),
                "title": title[:120],
                "type": classification["type"],
                "type_scores": classification["scores"],
                "confidence": classification["confidence"],
            })
        return results

    # =====================================================================
    # 规则分类
    # =====================================================================

    def _classify_rule(self, text: str) -> dict:
        """基于关键词匹配的题型分类。"""
        scores: dict[str, float] = {}
        text_lower = text.lower()

        for ptype, patterns in _PATTERNS.items():
            score = 0.0
            # 每个关键词贡献分数，越靠前权重越高
            for i, pat in enumerate(patterns):
                matches = pat.findall(text)
                if matches:
                    # 位置权重：前面的关键词权重更高
                    weight = max(0.3, 1.0 - i * 0.05)
                    score += len(matches) * weight
            scores[ptype] = score

        # 归一化
        total = sum(scores.values())
        if total > 0:
            for ptype in scores:
                scores[ptype] = min(1.0, scores[ptype] / total)

        # 找最高分
        if scores:
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]
        else:
            best_type = "综合"
            best_score = 0.0

        # 如果最高分太低，标记为综合
        if best_score < 0.15:
            best_type = "综合"
            best_score = 0.1

        return {
            "type": best_type,
            "scores": {k: round(v, 4) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
            "confidence": round(best_score, 4),
        }

    # =====================================================================
    # ML 分类（基于 TF-IDF + 朴素贝叶斯）
    # =====================================================================

    def _init_ml_classifier(self) -> None:
        """初始化 ML 分类器。"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            from sklearn.pipeline import Pipeline

            self._ml_pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(2, 4),
                    max_features=2000,
                )),
                ("clf", MultinomialNB(alpha=0.1)),
            ])
            self._ml_trained = False
        except ImportError:
            raise ImportError(
                "ML 分类模式需要 scikit-learn >= 1.3.0"
            )

    def _classify_ml(self, text: str) -> dict:
        """基于 ML 模型的题型分类。"""
        if not self._ml_trained:
            # 还没有训练数据时，回退到规则模式
            return self._classify_rule(text)

        try:
            proba = self._ml_pipeline.predict_proba([text])[0]
            classes = self._ml_pipeline.classes_
            scores = {cls: round(float(prob), 4) for cls, prob in zip(classes, proba)}
            best_type = max(scores, key=scores.get)
            return {
                "type": best_type,
                "scores": scores,
                "confidence": round(scores[best_type], 4),
            }
        except Exception:
            return self._classify_rule(text)

    def train_from_examples(self, texts: list[str], labels: list[str]) -> "ProblemClassifier":
        """从标注样例训练 ML 分类器。

        Args:
            texts: 题目文本列表
            labels: 对应的题型标签列表

        Returns:
            self
        """
        if self.method != "ml":
            raise RuntimeError("请先设置 method='ml'")
        try:
            self._ml_pipeline.fit(texts, labels)
            self._ml_trained = True
        except Exception as e:
            raise RuntimeError(f"训练失败: {e}")
        return self

    # =====================================================================
    # 工具方法
    # =====================================================================

    @staticmethod
    def get_data_requirements(problem_type: str) -> dict:
        """获取某个题型典型的数据需求。

        Args:
            problem_type: 题型名称

        Returns:
            dict: 数据要求，如 {"needs_numeric": True, "min_dim": 2}
        """
        requirements = {
            "优化": {
                "needs_numeric": True,
                "needs_constraints": True,
                "min_dim": 2,
                "description": "需要数值型变量和明确的约束条件",
            },
            "预测": {
                "needs_numeric": True,
                "needs_temporal": False,
                "min_samples": 5,
                "description": "需要历史数据，最好有时序结构",
            },
            "评价": {
                "needs_numeric": True,
                "needs_indicators": True,
                "min_dim": 2,
                "description": "需要多方案的指标数据矩阵",
            },
            "分类": {
                "needs_numeric": True,
                "min_samples": 20,
                "description": "需要足够样本，最好有标注",
            },
            "微分方程": {
                "needs_numeric": True,
                "needs_continuous": True,
                "description": "连续变化过程的数学描述",
            },
            "统计": {
                "needs_numeric": True,
                "min_samples": 10,
                "description": "需要样本数据用于推断",
            },
            "图论": {
                "needs_graph": True,
                "description": "需要节点和边的拓扑关系",
            },
        }
        return requirements.get(problem_type, {"description": "通用型问题"})
