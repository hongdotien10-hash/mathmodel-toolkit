"""模型库模块。

提供数学建模竞赛的六大类标准模型：
- optimization: 优化模型（线性/非线性/整数/多目标）
- differential: 微分方程（ODE/PDE 求解与拟合）
- statistics: 统计模型（回归/时序/假设检验）
- ml: 机器学习（聚类/分类/降维）
- graph: 图论与网络（最短路径/最大流/TSP）
- evaluation: 评价模型（AHP/TOPSIS/熵权/模糊综合评价）
"""

from mathmodel.models.optimization import OptimizationSolver
from mathmodel.models.differential import DiffEqSolver
from mathmodel.models.statistics import StatsSolver
from mathmodel.models.ml import MLSolver
from mathmodel.models.graph import GraphSolver
from mathmodel.models.evaluation import EvaluationSolver

__all__ = [
    "OptimizationSolver",
    "DiffEqSolver",
    "StatsSolver",
    "MLSolver",
    "GraphSolver",
    "EvaluationSolver",
]
