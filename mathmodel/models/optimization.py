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
            import pulp
            from pulp import LpProblem, LpMinimize, LpVariable, value
        except ImportError:
            raise ImportError("整数规划需要 PuLP: pip install pulp")

        # PuLP 4.x 移除了 pulp.LpStatus 字典，改用 prob.status 枚举名。
        # 这里做版本兼容：旧版取字典，新版直接用求解器给出的状态字符串。
        try:
            from pulp import LpStatus  # PuLP <= 3.x
        except ImportError:
            LpStatus = None

        # PuLP 4.0 起改用 Rust 内核，变量必须经 prob.add_variable() 创建。
        # 用签名探测而不是版本号，避免和发行版号/预发布号纠缠。
        import inspect
        _PULP_USES_ADD_VARIABLE = (
            "add_variable" in dir(LpProblem)
            and "lowBound" in inspect.signature(LpProblem.add_variable).parameters
        )

        n = len(c)
        prob = LpProblem("IP", LpMinimize)

        # PuLP 4.x 不再捆绑求解器，默认求解器为空会报 "No solver available"。
        # 判断依据是 pulp 的默认求解器是否可用（而不是"是否存在任何可用 solver"——
        # HiGHS 虽然可用，但必须显式指定才会被使用）。
        # pulp.LpSolverDefault 在 2.x/3.x 与 4.x 都从顶层导出，位置稳定。
        if getattr(pulp, "LpSolverDefault", None) is None:
            try:
                import highspy  # noqa: F401  —— 仅为触发求解器注册
                prob.solver = pulp.HiGHS(msg=False)
            except ImportError:
                pass

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
                cat_i = "Integer"
            elif binary:
                low, high, cat_i = 0, 1, "Binary"
            else:
                cat_i = cat

            # PuLP 4.0 是 Rust 重写版：LpVariable 不再能用构造器创建，
            # 必须走 prob.add_variable()；且 lowBound/upBound 必须有限。
            # PuLP 2.x/3.x 则相反，只能用 LpVariable 构造器。
            # 这里按版本分流，两边都能跑。
            if _PULP_USES_ADD_VARIABLE:
                # 无上界时给一个足够大的有限值（模型规模远小于此）
                up = high if high is not None else 1e9
                x.append(prob.add_variable(f"x{i}", lowBound=low, upBound=up, cat=cat_i))
            else:
                x.append(LpVariable(f"x{i}", low, high, cat_i))

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

        # 状态判定：不同大版本 API 完全不同
        #   PuLP 2.x/3.x —— prob.status 是整数，LpStatus[status] 是状态名
        #   PuLP 4.x     —— prob.status 属性已移除，改由 solverModel.getModelStatus()
        #                   给出 HighsModelStatus 枚举（kOptimal / kInfeasible …）
        status_name = None
        if _PULP_USES_ADD_VARIABLE:
            try:
                raw = prob.solverModel.getModelStatus()
                status_name = getattr(raw, "name", str(raw))
                # kOptimal -> 归一化成旧版的 "Optimal"，让下游判断逻辑一致
                if status_name.startswith("k"):
                    status_name = status_name[1:]
            except Exception:
                status_name = None
        elif LpStatus is not None:
            status_name = LpStatus[prob.status]

        if status_name is None:
            # 拿不到状态时不做乐观假设：按未收敛处理
            status_name = "Unknown"
            success = False
        else:
            success = status_name == "Optimal"

        return OptimizationResult(
            success=success,
            x=np.array([value(v) for v in x]),
            fun=value(prob.objective) if success else float("inf"),
            message=status_name,
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
