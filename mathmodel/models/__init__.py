"""模型库 — 优化/微分方程/统计/ML/图论/评价"""

from mathmodel.models.optimization import OptimizationSolver
from mathmodel.models.differential import DiffEqSolver
from mathmodel.models.statistics import StatsSolver
from mathmodel.models.ml import MLSolver
from mathmodel.models.graph import GraphSolver
from mathmodel.models.evaluation import EvaluationSolver

__all__ = [
    "OptimizationSolver", "DiffEqSolver", "StatsSolver",
    "MLSolver", "GraphSolver", "EvaluationSolver",
]
