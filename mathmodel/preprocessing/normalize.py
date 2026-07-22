"""数据标准化/归一化模块。

支持 Z-score、Min-Max、Robust、MaxAbs 等多种方法。
"""

import numpy as np
import pandas as pd
from typing import Optional


class Normalizer:
    """数据标准化/归一化器。

    Usage::

        norm = Normalizer(method="zscore")
        df_norm = norm.fit_transform(df)
    """

    METHODS = ["zscore", "minmax", "robust", "maxabs", "log", "yeo_johnson"]

    def __init__(
        self,
        method: str = "zscore",
        columns: Optional[list[str]] = None,
        feature_range: tuple[float, float] = (0, 1),
    ):
        """
        Args:
            method: 归一化方法
                - zscore: Z-score 标准化 (mean=0, std=1)
                - minmax: Min-Max 归一化
                - robust: Robust 标准化（用中位数和 IQR）
                - maxabs: 除以最大绝对值
                - log: log(1+x) 变换
                - yeo_johnson: Yeo-Johnson 幂变换
            columns: 要处理的列，None 为所有数值列
            feature_range: Min-Max 的目标范围
        """
        if method not in self.METHODS:
            raise ValueError(f"未知方法: {method}，可选 {self.METHODS}")
        self.method = method
        self.columns = columns
        self.feature_range = feature_range
        self._params: dict = {}  # 存储拟合参数

    def fit(self, df: pd.DataFrame) -> "Normalizer":
        """计算归一化参数。"""
        cols = self.columns or df.select_dtypes(include=np.number).columns.tolist()
        self._params = {"columns": cols}

        for col in cols:
            if self.method == "zscore":
                self._params[col] = {
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                }
            elif self.method == "minmax":
                self._params[col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                }
            elif self.method == "robust":
                q = df[col].quantile([0.25, 0.5, 0.75])
                self._params[col] = {
                    "median": float(q.iloc[1]),
                    "iqr": float(q.iloc[2] - q.iloc[0]),
                }
            elif self.method == "maxabs":
                self._params[col] = {"max_abs": float(np.abs(df[col]).max())}
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """应用归一化变换。"""
        df = df.copy()
        cols = self._params.get("columns", [])

        if self.method == "log":
            from mathmodel.utils.helpers import get_logger
            logger = get_logger("preprocessing.normalize")
            for col in cols:
                if col in df.columns:
                    min_val = df[col].min()
                    # log 变换要求正值
                    offset = max(0, 1 - min_val)
                    df[col] = np.log(df[col] + offset + 1)
            return df

        if self.method == "yeo_johnson":
            try:
                from sklearn.preprocessing import PowerTransformer
                pt = PowerTransformer(method="yeo-johnson", standardize=True)
                X = df[cols].fillna(df[cols].median()).values
                df[cols] = pt.fit_transform(X)
                return df
            except ImportError:
                from mathmodel.utils.helpers import get_logger
                get_logger("preprocessing.normalize").warning(
                    "需要 scikit-learn 进行 Yeo-Johnson 变换，回退到 Z-score"
                )

        for col in cols:
            if col not in df.columns:
                continue
            params = self._params.get(col, {})
            if not params:
                continue

            if self.method == "zscore":
                std = params["std"]
                if std and std > 0:
                    df[col] = (df[col] - params["mean"]) / std
                else:
                    df[col] = df[col] - params["mean"]

            elif self.method == "minmax":
                rng = params["max"] - params["min"]
                if rng and rng > 0:
                    a, b = self.feature_range
                    df[col] = a + (df[col] - params["min"]) * (b - a) / rng

            elif self.method == "robust":
                iqr = params["iqr"]
                if iqr and iqr > 0:
                    df[col] = (df[col] - params["median"]) / iqr
                else:
                    df[col] = df[col] - params["median"]

            elif self.method == "maxabs":
                m = params["max_abs"]
                if m and m > 0:
                    df[col] = df[col] / m

        return df

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """拟合并转换。"""
        self.fit(df)
        return self.transform(df)

    def inverse_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """逆向还原（仅在 fit 后可用）。"""
        df = df.copy()
        cols = self._params.get("columns", [])

        for col in cols:
            if col not in df.columns:
                continue
            params = self._params.get(col, {})
            if not params:
                continue

            if self.method == "zscore":
                df[col] = df[col] * params.get("std", 1) + params.get("mean", 0)
            elif self.method == "minmax":
                a, b = self.feature_range
                rng = params["max"] - params["min"]
                df[col] = params["min"] + (df[col] - a) * rng / (b - a)
            elif self.method == "robust":
                df[col] = df[col] * params.get("iqr", 1) + params.get("median", 0)
            elif self.method == "maxabs":
                df[col] = df[col] * params.get("max_abs", 1)

        return df
