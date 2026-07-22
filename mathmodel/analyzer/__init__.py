"""题目分析 & 智能模型推荐模块。

根据题目文本和附件数据自动完成：
- 题型分类（优化/预测/评价/分类/微分方程/统计/图论/综合）
- 数据画像生成
- 智能模型推荐（基于知识库的打分和排序）
"""

from mathmodel.analyzer.knowledge_base import ModelKnowledgeBase
from mathmodel.analyzer.classifier import ProblemClassifier
from mathmodel.analyzer.recommender import ModelRecommender

__all__ = [
    "ModelKnowledgeBase",
    "ProblemClassifier",
    "ModelRecommender",
]
