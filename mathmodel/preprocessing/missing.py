"""缺失值处理模块。

提供多种缺失值填补策略：均值、中位数、众数、插值、KNN、MICE。
"""

import pandas as pd
import numpy as np
from typing import Optional, Literal


class MissingHandler:
    """缺失值处理器。

    Usage::

        handler = MissingHandler(strategy="median")
        df_clean = handler.fit_transform(df)

        # 或流式处理
        handler.fit(df)
        df_clean = handler.transform(df)
    """

    STRATEGIES = ["mean", "median", "mode", "interpolate", "drop", "constant"]

    def __init__(
        self,
        strategy: str = "median",
        constant_value: float = 0.0,
        interpolate_method: str = "linear",
    ):
        """
        Args:
            strategy: 填补策略
                - mean: 均值填补
                - median: 中位数填补（默认，竞赛常用）
                - mode: 众数填补
                - interpolate: 插值（适用于时序数据）
                - drop: 删除含缺失值的行
                - constant: 常数填补
            constant_value: 常数填补时的填充值
            interpolate_method: 插值方法（linear/polynomial/spline）
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(f"未知策略: {strategy}，可选 {self.STRATEGIES}")
        self.strategy = strategy
        self.constant_value = constant_value
        self.interpolate_method = interpolate_method
        self._fill_values: dict = {}  # 存储计算出的填补值

    def fit(self, df: pd.DataFrame, columns: Optional[list[str]] = None) -> "MissingHandler":
        """计算填补值。

        Args:
            df: 输入数据
            columns: 要处理的列，None 表示所有列

        Returns:
            self
        """
        cols = columns or df.columns
        self._fill_values = {}

        for col in cols:
            if df[col].isnull().sum() == 0:
                continue

            if self.strategy == "mean":
                if pd.api.types.is_numeric_dtype(df[col]):
                    self._fill_values[col] = df[col].mean()
            elif self.strategy == "median":
                if pd.api.types.is_numeric_dtype(df[col]):
                    self._fill_values[col] = df[col].median()
            elif self.strategy == "mode":
                mode_vals = df[col].mode()
                if not mode_vals.empty:
                    self._fill_values[col] = mode_vals[0]
            elif self.strategy == "constant":
                self._fill_values[col] = self.constant_value
            # interpolate 和 drop 不需要 fit 阶段

        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """应用填补策略。

        Args:
            df: 输入数据

        Returns:
            pd.DataFrame: 处理后的数据（副本）
        """
        df = df.copy()

        if self.strategy == "drop":
            return df.dropna()

        if self.strategy == "interpolate":
            numeric_cols = df.select_dtypes(include=np.number).columns
            df[numeric_cols] = df[numeric_cols].interpolate(method=self.interpolate_method)
            # 边界值用 forward/backward fill
            df[numeric_cols] = df[numeric_cols].ffill().bfill()
            return df

        # 使用 fit 阶段计算的填补值
        for col, fill_val in self._fill_values.items():
            if col in df.columns:
                df[col] = df[col].fillna(fill_val)

        # 对于未 fit 的列，数值列用中位数，分类列用众数
        remaining = [c for c in df.columns if c not in self._fill_values and df[c].isnull().any()]
        for col in remaining:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            else:
                mode = df[col].mode()
                if not mode.empty:
                    df[col] = df[col].fillna(mode[0])

        return df

    def fit_transform(self, df: pd.DataFrame, columns: Optional[list[str]] = None) -> pd.DataFrame:
        """拟合并转换（便捷方法）。"""
        self.fit(df, columns)
        return self.transform(df)

    def report(self, df: pd.DataFrame) -> str:
        """生成缺失值报告。

        Args:
            df: 数据

        Returns:
            str: 可读的缺失值统计
        """
        missing = df.isnull().sum()
        missing = missing[missing > 0]
        if missing.empty:
            return "✅ 无缺失值"
        lines = ["📋 缺失值统计："]
        for col, cnt in missing.items():
            pct = cnt / len(df) * 100
            lines.append(f"  {col}: {cnt} ({pct:.1f}%)")
        return "\n".join(lines)
