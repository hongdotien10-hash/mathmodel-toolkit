"""评价模型求解器。

提供竞赛常用的综合评价方法：
AHP、TOPSIS、熵权法、模糊综合评价、灰色关联分析、CRITIC、VIKOR。
"""

import numpy as np
import pandas as pd
from typing import Optional


class EvaluationSolver:
    """综合评价求解器。

    支持多种评价方法，输出论文可用的结果。

    Usage::

        evaluator = EvaluationSolver()

        # TOPSIS
        scores = evaluator.topsis(matrix, weights)

        # AHP
        weights, cr = evaluator.ahp(pairwise_matrix)

        # 熵权法
        weights = evaluator.entropy_weight(matrix)
    """

    # =====================================================================
    # TOPSIS 优劣解距离法
    # =====================================================================

    def topsis(
        self,
        matrix: np.ndarray | pd.DataFrame,
        weights: Optional[list[float]] = None,
        impacts: Optional[list[int]] = None,
        normalize: bool = True,
    ) -> dict:
        """TOPSIS 优劣解距离法。

        Args:
            matrix: 决策矩阵 (m 方案 × n 指标)，数值型
            weights: 指标权重，None 时为等权
            impacts: 指标方向，1=正向（越大越好），-1=负向（越小越好），None 时全部为正
            normalize: 是否归一化

        Returns:
            dict: {
                "scores": 得分数组 (0~1, 越大越优),
                "rank": 排名 (1-based),
                "d_plus": 到正理想解距离,
                "d_minus": 到负理想解距离,
                "ideal_best": 正理想解,
                "ideal_worst": 负理想解,
            }
        """
        if isinstance(matrix, pd.DataFrame):
            matrix = matrix.values

        m, n = matrix.shape

        if weights is None:
            weights = np.ones(n) / n
        else:
            weights = np.array(weights, dtype=float)
            weights = weights / weights.sum()

        if impacts is None:
            impacts = [1] * n

        # Step 1: 归一化
        if normalize:
            norm = np.sqrt((matrix ** 2).sum(axis=0))
            norm[norm == 0] = 1  # 避免除零
            normalized = matrix / norm
        else:
            normalized = matrix.copy()

        # Step 2: 加权
        weighted = normalized * weights

        # Step 3: 确定正负理想解
        ideal_best = np.zeros(n)
        ideal_worst = np.zeros(n)

        for j in range(n):
            col = weighted[:, j]
            if impacts[j] > 0:  # 正向指标
                ideal_best[j] = col.max()
                ideal_worst[j] = col.min()
            else:  # 负向指标
                ideal_best[j] = col.min()
                ideal_worst[j] = col.max()

        # Step 4: 计算距离
        d_plus = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
        d_minus = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

        # Step 5: 计算相对贴近度
        denom = d_plus + d_minus
        denom[denom == 0] = 1e-10
        scores = d_minus / denom

        rank = scores.argsort()[::-1].argsort() + 1

        return {
            "scores": scores,
            "rank": rank,
            "d_plus": d_plus,
            "d_minus": d_minus,
            "ideal_best": ideal_best,
            "ideal_worst": ideal_worst,
        }

    # =====================================================================
    # AHP 层次分析法
    # =====================================================================

    def ahp(
        self,
        pairwise_matrix: np.ndarray | list[list[float]],
    ) -> dict:
        """层次分析法 (AHP)。

        Args:
            pairwise_matrix: n×n 成对比较矩阵（Saaty 1-9 标度）

        Returns:
            dict: {
                "weights": 权重向量,
                "lambda_max": 最大特征值,
                "ci": 一致性指标,
                "cr": 一致性比率,
                "is_consistent": 是否通过一致性检验 (CR < 0.1),
            }
        """
        A = np.array(pairwise_matrix, dtype=float)
        n = A.shape[0]

        # 特征值法求权重
        eigenvalues, eigenvectors = np.linalg.eig(A)
        max_idx = np.argmax(np.abs(eigenvalues))
        lambda_max = float(np.real(eigenvalues[max_idx]))

        # 权重 = 最大特征值对应的特征向量（归一化）
        w = np.abs(np.real(eigenvectors[:, max_idx]))
        weights = w / w.sum()

        # 一致性检验
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0

        # 随机一致性指标 RI（Saaty 表）
        ri_table = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24,
                    7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
        ri = ri_table.get(n, 1.5)

        cr = ci / ri if ri > 0 else 0

        return {
            "weights": weights,
            "lambda_max": lambda_max,
            "ci": round(ci, 6),
            "cr": round(cr, 6),
            "is_consistent": cr < 0.1,
        }

    # =====================================================================
    # 熵权法
    # =====================================================================

    def entropy_weight(
        self,
        matrix: np.ndarray | pd.DataFrame,
        normalize: bool = True,
    ) -> dict:
        """熵权法 — 基于信息熵的客观赋权。

        Args:
            matrix: 决策矩阵 (m 方案 × n 指标)
            normalize: 是否先归一化

        Returns:
            dict: {"weights": 权重, "entropy": 各指标熵值, "d": 信息效用值}
        """
        if isinstance(matrix, pd.DataFrame):
            matrix = matrix.values

        m, n = matrix.shape

        # 归一化（Min-Max，正向指标）
        if normalize:
            normalized = np.zeros_like(matrix, dtype=float)
            for j in range(n):
                col = matrix[:, j]
                col_min, col_max = col.min(), col.max()
                if col_max > col_min:
                    normalized[:, j] = (col - col_min) / (col_max - col_min)
                else:
                    normalized[:, j] = 0.5
        else:
            normalized = matrix.copy()

        # 平移避免 log(0)
        normalized += 1e-10

        # 计算比重 p_ij
        p = normalized / normalized.sum(axis=0, keepdims=True)

        # 计算熵值 e_j = -k * Σ p_ij * ln(p_ij)
        k = 1.0 / np.log(m) if m > 1 else 1.0
        entropy = -k * (p * np.log(p)).sum(axis=0)

        # 信息效用值
        d = 1 - entropy
        weights = d / d.sum() if d.sum() > 0 else np.ones(n) / n

        return {
            "weights": weights,
            "entropy": entropy,
            "d": d,
        }

    # =====================================================================
    # 模糊综合评价
    # =====================================================================

    def fuzzy_comprehensive(
        self,
        membership_matrix: np.ndarray,
        weights: list[float],
        operator: str = "weighted_avg",
    ) -> dict:
        """模糊综合评价。

        Args:
            membership_matrix: 隶属度矩阵 (m 指标 × k 评价等级)
            weights: 指标权重
            operator: 合成算子类型
                - "weighted_avg": 加权平均型 M(·,+)
                - "max_min": 主因素决定型 M(∧,∨)
                - "max_product": 主因素突出型 M(·,∨)

        Returns:
            dict: {"result": 综合评价向量, "level": 最大隶属度等级}
        """
        R = np.array(membership_matrix, dtype=float)
        W = np.array(weights, dtype=float).reshape(1, -1)

        if operator == "max_min":
            # M(∧, ∨) — 取小取大
            k, n = R.shape
            B = np.zeros(n)
            for j in range(n):
                B[j] = np.max(np.minimum(W, R[:, j]))
        elif operator == "max_product":
            # M(·, ∨) — 乘取大
            B = np.max(W.T * R, axis=0)
        else:
            # M(·, +) — 加权平均（默认）
            B = (W @ R).flatten()

        # 归一化
        B = B / B.sum() if B.sum() > 0 else B

        level = int(np.argmax(B)) + 1

        return {
            "result": B,
            "level": level,
            "level_names": {i + 1: f"等级{i + 1}" for i in range(len(B))},
        }

    # =====================================================================
    # 灰色关联分析
    # =====================================================================

    def grey_relational(
        self,
        matrix: np.ndarray | pd.DataFrame,
        reference: Optional[list[float]] = None,
        rho: float = 0.5,
    ) -> dict:
        """灰色关联分析。

        Args:
            matrix: 比较序列矩阵 (m 个序列 × n 个指标)
            reference: 参考序列（理想值），None 时取各指标最优值
            rho: 分辨系数 (0~1)，默认 0.5

        Returns:
            dict: {"degrees": 关联度, "rank": 排名}
        """
        if isinstance(matrix, pd.DataFrame):
            matrix = matrix.values

        m, n = matrix.shape

        # 参考序列
        if reference is None:
            reference = matrix.max(axis=0)

        ref = np.array(reference, dtype=float).reshape(1, -1)

        # 初值化
        normalized = matrix / matrix[0, :] if m > 0 else matrix

        # 差值矩阵
        diff = np.abs(normalized - ref)

        # 关联系数
        min_diff = diff.min()
        max_diff = diff.max()
        xi = (min_diff + rho * max_diff) / (diff + rho * max_diff)

        # 关联度（各指标关联系数的均值）
        degrees = xi.mean(axis=1)
        rank = degrees.argsort()[::-1].argsort() + 1

        return {
            "degrees": degrees,
            "rank": rank,
        }

    # =====================================================================
    # CRITIC 权重法
    # =====================================================================

    def critic_weight(self, matrix: np.ndarray | pd.DataFrame) -> dict:
        """CRITIC 客观赋权法。

        综合考虑各指标的对比强度（标准差）和冲突性（相关性）。

        Args:
            matrix: 决策矩阵

        Returns:
            dict: {"weights": 权重, "std": 标准差, "conflict": 冲突性}
        """
        if isinstance(matrix, pd.DataFrame):
            matrix = matrix.values

        m, n = matrix.shape

        # 标准化
        norm = (matrix - matrix.mean(axis=0)) / (matrix.std(axis=0, ddof=1) + 1e-10)

        # 对比强度（标准差）
        std = np.std(norm, axis=0, ddof=1)

        # 冲突性
        corr = np.corrcoef(norm, rowvar=False)
        conflict = np.sum(1 - np.abs(corr), axis=0)

        # 信息量
        info = std * conflict
        weights = info / info.sum() if info.sum() > 0 else np.ones(n) / n

        return {
            "weights": weights,
            "std": std,
            "conflict": conflict,
            "info": info,
        }
