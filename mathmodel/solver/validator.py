"""求解结果验证器。

验证数值结果的合理性：非负性、边界、约束满足、量纲等。
"""

import numpy as np
from typing import Optional


class ResultValidator:
    """求解结果验证器。

    Usage::

        validator = ResultValidator()
        is_valid, msg = validator.check(result)
    """

    def check(self, result: dict, constraints: Optional[dict] = None) -> tuple[bool, list[str]]:
        """验证求解结果。

        Args:
            result: 求解结果字典
            constraints: 约束条件 {"min": 0, "max": 1, "non_negative": True}

        Returns:
            (is_valid, warnings): 是否通过，以及警告信息列表
        """
        warnings = []

        # 检查是否有值
        if "scores" in result:
            scores = np.array(result["scores"])
            if np.any(np.isnan(scores)):
                warnings.append("❌ 结果包含 NaN 值")
            if np.any(np.isinf(scores)):
                warnings.append("❌ 结果包含 Inf 值")

        # 检查非负约束
        if constraints and constraints.get("non_negative"):
            for key in ["scores", "forecast", "predictions"]:
                if key in result:
                    vals = np.array(result[key])
                    if np.any(vals < 0):
                        warnings.append(f"⚠️ {key} 包含负值（不满足非负约束）")

        # 检查权重和为1
        if "weights" in result:
            w = np.array(result["weights"])
            if abs(w.sum() - 1.0) > 0.01:
                warnings.append(f"⚠️ 权重和 = {w.sum():.4f}，不等于 1")

        # 检查概率范围
        for key in ["scores", "accuracy"]:
            if key in result:
                vals = np.atleast_1d(result[key])
                if np.any(vals < 0) or np.any(vals > 1.1):
                    warnings.append(f"⚠️ {key} 超出 [0,1] 范围")

        is_valid = not any("❌" in w for w in warnings)
        return is_valid, warnings

    def check_optimization(
        self,
        solution: np.ndarray,
        constraints: dict,
    ) -> tuple[bool, list[str]]:
        """验证优化解是否满足约束。

        Args:
            solution: 解向量
            constraints: {"A_ub": ..., "b_ub": ..., "A_eq": ..., "b_eq": ..., "bounds": ...}

        Returns:
            (is_feasible, violations): 是否可行及违规项
        """
        violations = []
        x = np.array(solution)

        # 不等式约束检查
        if "A_ub" in constraints and "b_ub" in constraints:
            A_ub = np.array(constraints["A_ub"])
            b_ub = np.array(constraints["b_ub"])
            slack = b_ub - A_ub @ x
            for i, s in enumerate(slack):
                if s < -0.01:
                    violations.append(f"违反不等式约束 {i}: slack={s:.4f}")

        # 等式约束检查
        if "A_eq" in constraints and "b_eq" in constraints:
            A_eq = np.array(constraints["A_eq"])
            b_eq = np.array(constraints["b_eq"])
            residual = A_eq @ x - b_eq
            for i, r in enumerate(residual):
                if abs(r) > 0.01:
                    violations.append(f"违反等式约束 {i}: residual={r:.4f}")

        # 边界检查
        if "bounds" in constraints:
            bounds = constraints["bounds"]
            for i, (low, high) in enumerate(bounds):
                if low is not None and x[i] < low - 0.01:
                    violations.append(f"x[{i}]={x[i]:.4f} < lower={low}")
                if high is not None and x[i] > high + 0.01:
                    violations.append(f"x[{i}]={x[i]:.4f} > upper={high}")

        is_feasible = len(violations) == 0
        return is_feasible, violations
