"""模型库 — 优化/微分方程/统计/ML/图论/评价"""

from mathmodel.models.optimization import OptimizationSolver
from mathmodel.models.statistics import StatsSolver
from mathmodel.models.evaluation import EvaluationSolver
from mathmodel.models.ml import MLSolver

__all__ = ["OptimizationSolver", "StatsSolver", "EvaluationSolver", "MLSolver"]
