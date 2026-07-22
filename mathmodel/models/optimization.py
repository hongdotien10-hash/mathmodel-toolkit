"""优化模型求解器。

支持线性规划、非线性规划、整数规划、多目标优化。
"""

import numpy as np
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class OptimizationResult:
    """优化结果。"""
    success: bool
    x: np.ndarray       # 最优解
    fun: float          # 目标函数值
    message: str = ""
    nit: int = 0        # 迭代次数
    nfev: int = 0       # 函数评估次数


class OptimizationSolver:
    """通用优化求解器。

    封装 scipy.optimize 和 cvxpy，提供统一的 API。

    Usage::

        solver = OptimizationSolver()

        # 线性规划: min c·x  s.t. A_ub·x <= b_ub, bounds
        result = solver.linear_program(c=[-1, -2], A_ub=[[1, 1]], b_ub=[10])

        # 非线性规划
        def f(x): return (x[0]-1)**2 + (x[1]-2)**2
        result = solver.nonlinear_program(f, x0=[0, 0], bounds=[(-5, 5), (-5, 5)])

        # 整数规划
        result = solver.integer_program(c=[3, 2], A_ub=[[1, 2]], b_ub=[8], bounds=(0, 5))
    """

    # =====================================================================
    # 线性规划
    # =====================================================================

    def linear_program(
        self,
        c: list[float],
        A_ub: Optional[list[list[float]]] = None,
        b_ub: Optional[list[float]] = None,
        A_eq: Optional[list[list[float]]] = None,
        b_eq: Optional[list[float]] = None,
        bounds: Optional[list[tuple[float, float]]] = None,
        method: str = "highs",
    ) -> OptimizationResult:
        """求解线性规划。

        min c·x
        s.t. A_ub·x <= b_ub
             A_eq·x == b_eq
             x ∈ bounds

        Args:
            c: 目标函数系数
            A_ub: 不等式约束矩阵
            b_ub: 不等式约束右端
            A_eq: 等式约束矩阵
            b_eq: 等式约束右端
            bounds: 变量边界 (low, high) 列表
            method: 求解方法（highs/simplex/interior-point）

        Returns:
            OptimizationResult
        """
        from scipy.optimize import linprog

        res = linprog(
            c=c,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method=method,
        )

        return OptimizationResult(
            success=res.success,
            x=res.x if res.success else np.array([]),
            fun=res.fun if res.success else float("inf"),
            message=res.message,
            nit=res.nit,
            nfev=getattr(res, "nfev", 0),
        )

    # =====================================================================
    # 非线性规划
    # =====================================================================

    def nonlinear_program(
        self,
        objective: Callable[[np.ndarray], float],
        x0: list[float],
        bounds: Optional[list[tuple[float, float]]] = None,
        constraints: Optional[list[dict]] = None,
        method: str = "SLSQP",
        options: Optional[dict] = None,
    ) -> OptimizationResult:
        """求解非线性规划。

        min f(x)
        s.t. constraints (scipy 格式)

        Args:
            objective: 目标函数 f(x)，输入为 ndarray，输出为标量
            x0: 初始猜测
            bounds: 变量边界
            constraints: 约束列表，scipy 格式 [{'type':'ineq','fun':g}, ...]
            method: SLSQP / trust-constr / COBYLA
            options: 求解器选项

        Returns:
            OptimizationResult
        """
        from scipy.optimize import minimize

        default_opts = {"maxiter": 1000, "ftol": 1e-8}
        if options:
            default_opts.update(options)

        res = minimize(
            objective,
            x0=np.array(x0, dtype=float),
            method=method,
            bounds=bounds,
            constraints=constraints,
            options=default_opts,
        )

        return OptimizationResult(
            success=res.success,
            x=res.x,
            fun=res.fun,
            message=res.message,
            nit=getattr(res, "nit", 0),
            nfev=getattr(res, "nfev", 0),
        )

    # =====================================================================
    # 整数规划 (0-1 / 整数)
    # =====================================================================

    def integer_program(
        self,
        c: list[float],
        A_ub: Optional[list[list[float]]] = None,
        b_ub: Optional[list[float]] = None,
        A_eq: Optional[list[list[float]]] = None,
        b_eq: Optional[list[float]] = None,
        bounds: tuple[float, float] | list[tuple[float, float]] = (0, None),
        integer_indices: Optional[list[int]] = None,
        binary: bool = False,
    ) -> OptimizationResult:
        """求解整数/0-1 规划。

        使用 PuLP（推荐）或 brute force（小规模）。

        Args:
            c: 目标函数系数
            A_ub: 不等式约束矩阵
            b_ub: 不等式约束右端
            A_eq: 等式约束矩阵
            b_eq: 等式约束右端
            bounds: 变量边界
            integer_indices: 整数变量的索引列表，None 表示全部为整数
            binary: True 表示 0-1 规划

        Returns:
            OptimizationResult
        """
        return self._solve_ip_pulp(
            c, A_ub, b_ub, A_eq, b_eq, bounds, integer_indices, binary
        )

    def _solve_ip_pulp(
        self,
        c, A_ub, b_ub, A_eq, b_eq,
        bounds, integer_indices, binary,
    ) -> OptimizationResult:
        """使用 PuLP 求解整数规划。"""
        try:
            from pulp import LpProblem, LpMinimize, LpVariable, LpStatus, value
        except ImportError:
            raise ImportError("整数规划需要 PuLP: pip install pulp")

        n = len(c)
        prob = LpProblem("IP", LpMinimize)

        # 变量
        if isinstance(bounds, tuple):
            bounds = [bounds] * n

        if binary:
            cat = "Binary"
        else:
            cat = "Integer" if integer_indices is None else "Continuous"

        x = []
        for i in range(n):
            low = bounds[i][0] if bounds[i][0] is not None else 0
            high = bounds[i][1] if bounds[i][1] is not None else None
            if integer_indices and i in integer_indices:
                x.append(LpVariable(f"x{i}", low, high, "Integer"))
            elif binary:
                x.append(LpVariable(f"x{i}", 0, 1, "Binary"))
            else:
                x.append(LpVariable(f"x{i}", low, high, cat))

        # 目标
        prob += sum(c[i] * x[i] for i in range(n))

        # 约束
        if A_ub:
            for i, row in enumerate(A_ub):
                prob += sum(row[j] * x[j] for j in range(n)) <= b_ub[i]
        if A_eq:
            for i, row in enumerate(A_eq):
                prob += sum(row[j] * x[j] for j in range(n)) == b_eq[i]

        prob.solve()

        success = LpStatus[prob.status] == "Optimal"
        return OptimizationResult(
            success=success,
            x=np.array([value(v) for v in x]),
            fun=value(prob.objective) if success else float("inf"),
            message=LpStatus[prob.status],
        )

    # =====================================================================
    # 多目标优化（加权法）
    # =====================================================================

    def weighted_multi_objective(
        self,
        objectives: list[Callable[[np.ndarray], float]],
        weights: list[float],
        x0: list[float],
        bounds: Optional[list[tuple[float, float]]] = None,
    ) -> OptimizationResult:
        """加权法多目标优化。

        min Σ w_i * f_i(x)

        Args:
            objectives: 目标函数列表
            weights: 权重列表
            x0: 初始猜测
            bounds: 变量边界

        Returns:
            OptimizationResult
        """
        total_weight = sum(weights)

        def combined(x: np.ndarray) -> float:
            return sum(w * f(x) / total_weight for w, f in zip(weights, objectives))

        return self.nonlinear_program(combined, x0=x0, bounds=bounds)
