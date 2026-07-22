"""统计模型求解器。

提供回归分析、时间序列预测、假设检验等统计方法。
"""

import numpy as np
import pandas as pd
from typing import Optional, Literal


class StatsSolver:
    """统计分析求解器。

    Usage::

        ss = StatsSolver()

        # 灰色预测
        result = ss.grey_forecast(data)

        # 线性回归
        result = ss.linear_regression(X, y)

        # 假设检验
        result = ss.t_test(group1, group2)
    """

    # =====================================================================
    # 灰色预测 GM(1,1)
    # =====================================================================

    def grey_forecast(
        self,
        data: list[float] | np.ndarray,
        forecast_steps: int = 1,
    ) -> dict:
        """灰色预测 GM(1,1) 模型。

        适用于小样本（4-10个点）的指数型趋势预测。

        Args:
            data: 原始时序数据（非负）
            forecast_steps: 预测步数

        Returns:
            dict: {
                "forecast": 预测值,
                "fitted": 拟合值 (对原始数据的回代),
                "params": {"a": 发展系数, "b": 灰色作用量},
                "mape": 平均绝对百分比误差,
                "c_ratio": 后验差比值 (越小越好, <0.35 为优),
                "p_value": 小误差概率 (越大越好, >0.95 为优),
            }
        """
        x0 = np.array(data, dtype=float)

        if (x0 <= 0).any():
            # 处理非正数据：加常数平移
            offset = abs(x0.min()) + 1
            x0 = x0 + offset
        else:
            offset = 0

        n = len(x0)

        # Step 1: 1-AGO 累加生成
        x1 = np.cumsum(x0)

        # Step 2: 背景值序列 Z
        z = (x1[:-1] + x1[1:]) / 2.0

        # Step 3: 最小二乘估计 [a, b]^T = (B^T B)^{-1} B^T Y
        B = np.column_stack([-z, np.ones(n - 1)])
        Y = x0[1:]

        params = np.linalg.inv(B.T @ B) @ B.T @ Y
        a, b = params[0], params[1]

        # Step 4: 预测
        def gm_predict(k: int) -> float:
            return (x0[0] - b / a) * np.exp(-a * k) + b / a

        # 拟合值
        fitted_ago = np.array([gm_predict(k) for k in range(n)])
        fitted = np.diff(fitted_ago, prepend=0)
        fitted[0] = x0[0]

        # 预测
        forecast_ago = np.array([gm_predict(k) for k in range(n, n + forecast_steps)])
        forecast = np.diff(forecast_ago, prepend=fitted_ago[-1] if n > 0 else 0)

        if offset > 0:
            fitted = fitted - offset
            forecast = forecast - offset

        # 精度评估
        residual = x0 - fitted
        mape = np.mean(np.abs(residual / (x0 + 1e-10))) * 100

        # 后验差检验
        s1 = np.std(x0, ddof=1)
        s2 = np.std(residual, ddof=1)
        c_ratio = s2 / s1 if s1 > 0 else float("inf")

        # 小误差概率
        mean_resid = np.mean(residual)
        p_count = np.sum(np.abs(residual - mean_resid) < 0.6745 * s1)
        p_value = p_count / n

        return {
            "forecast": forecast.tolist() if forecast_steps > 0 else [],
            "fitted": fitted.tolist(),
            "params": {"a": float(a), "b": float(b)},
            "mape": round(float(mape), 4),
            "c_ratio": round(float(c_ratio), 4),
            "p_value": round(float(p_value), 4),
            "grade": self._gm_grade(c_ratio, p_value),
        }

    @staticmethod
    def _gm_grade(c: float, p: float) -> str:
        """GM(1,1) 精度等级。"""
        if c < 0.35 and p > 0.95:
            return "一级（优）"
        elif c < 0.5 and p > 0.8:
            return "二级（合格）"
        elif c < 0.65 and p > 0.7:
            return "三级（勉强）"
        else:
            return "四级（不合格）"

    # =====================================================================
    # 线性回归
    # =====================================================================

    def linear_regression(
        self,
        X: np.ndarray | pd.DataFrame,
        y: np.ndarray | pd.Series,
        add_intercept: bool = True,
        return_stats: bool = True,
    ) -> dict:
        """线性回归。

        Args:
            X: 自变量矩阵
            y: 因变量
            add_intercept: 是否添加截距项
            return_stats: 是否返回统计检验结果

        Returns:
            dict: {
                "coefficients": 系数,
                "intercept": 截距,
                "predictions": 预测值,
                "r_squared": R²,
                "adj_r_squared": 调整 R²,
                "std_errors": 标准误 (if return_stats),
                "t_values": t 统计量 (if return_stats),
                "p_values": p 值 (if return_stats),
            }
        """
        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, pd.Series):
            y = y.values

        m = X.shape[0]
        X_arr = X.astype(float)
        y_arr = y.astype(float).ravel()

        if add_intercept:
            X_arr = np.column_stack([np.ones(m), X_arr])

        # 正规方程求解
        beta = np.linalg.inv(X_arr.T @ X_arr) @ X_arr.T @ y_arr
        predictions = X_arr @ beta

        # R²
        ss_res = np.sum((y_arr - predictions) ** 2)
        ss_tot = np.sum((y_arr - y_arr.mean()) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # 调整 R²
        k = X_arr.shape[1] - 1  # 自变量个数（不含截距）
        adj_r2 = 1 - (1 - r_squared) * (m - 1) / (m - k - 1) if m > k + 1 else r_squared

        result = {
            "coefficients": beta[1:].tolist() if add_intercept else beta.tolist(),
            "intercept": float(beta[0]) if add_intercept else 0.0,
            "predictions": predictions.tolist(),
            "r_squared": round(float(r_squared), 6),
            "adj_r_squared": round(float(adj_r2), 6),
        }

        if return_stats:
            # 标准误
            sigma2 = ss_res / (m - k - 1) if m > k + 1 else ss_res / m
            cov_matrix = sigma2 * np.linalg.inv(X_arr.T @ X_arr)
            std_errors = np.sqrt(np.diag(cov_matrix))
            t_values = beta / std_errors

            from scipy.stats import t as t_dist
            p_values = 2 * t_dist.sf(np.abs(t_values), m - k - 1)

            result["std_errors"] = std_errors.tolist()
            result["t_values"] = t_values.tolist()
            result["p_values"] = p_values.tolist()

        return result

    # =====================================================================
    # t 检验
    # =====================================================================

    def t_test(
        self,
        group1: list[float] | np.ndarray,
        group2: list[float] | np.ndarray,
        test_type: Literal["two-sided", "greater", "less"] = "two-sided",
        paired: bool = False,
    ) -> dict:
        """t 检验。

        Args:
            group1: 第一组数据
            group2: 第二组数据
            test_type: 检验方向
            paired: 是否配对检验

        Returns:
            dict: {"statistic", "p_value", "significant", "alpha"}
        """
        from scipy import stats

        if paired:
            stat, p_val = stats.ttest_rel(group1, group2)
        else:
            stat, p_val = stats.ttest_ind(group1, group2)

        if test_type == "greater":
            p_val = p_val / 2 if stat > 0 else 1 - p_val / 2
        elif test_type == "less":
            p_val = p_val / 2 if stat < 0 else 1 - p_val / 2

        return {
            "statistic": round(float(stat), 6),
            "p_value": round(float(p_val), 6),
            "significant": p_val < 0.05,
            "alpha": 0.05,
            "conclusion": "显著差异" if p_val < 0.05 else "无显著差异",
        }

    # =====================================================================
    # 相关性分析
    # =====================================================================

    def correlation(
        self,
        x: list[float] | np.ndarray,
        y: list[float] | np.ndarray,
        method: Literal["pearson", "spearman", "kendall"] = "pearson",
    ) -> dict:
        """相关系数计算。

        Returns:
            dict: {"coefficient", "p_value", "significant"}
        """
        from scipy import stats

        x_arr = np.array(x, dtype=float).ravel()
        y_arr = np.array(y, dtype=float).ravel()

        if method == "pearson":
            coef, p_val = stats.pearsonr(x_arr, y_arr)
        elif method == "spearman":
            coef, p_val = stats.spearmanr(x_arr, y_arr)
        else:
            coef, p_val = stats.kendalltau(x_arr, y_arr)

        abs_c = abs(coef)
        if abs_c > 0.8:
            strength = "极强"
        elif abs_c > 0.6:
            strength = "强"
        elif abs_c > 0.4:
            strength = "中等"
        elif abs_c > 0.2:
            strength = "弱"
        else:
            strength = "极弱"

        return {
            "coefficient": round(float(coef), 6),
            "p_value": round(float(p_val), 6),
            "significant": p_val < 0.05,
            "strength": strength,
        }
