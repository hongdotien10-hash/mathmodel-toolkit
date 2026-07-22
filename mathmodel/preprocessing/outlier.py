"""异常值检测模块。

支持多种检测方法：3σ、IQR、MAD、DBSCAN、孤立森林。
"""

import numpy as np
import pandas as pd
from typing import Optional, Literal


class OutlierDetector:
    """异常值检测器。

    Usage::

        detector = OutlierDetector(method="iqr", threshold=1.5)
        mask = detector.detect(df)       # 返回布尔掩码
        df_clean = detector.remove(df)   # 返回删除异常值后的数据
    """

    METHODS = ["zscore", "iqr", "mad", "isolation_forest", "dbscan"]

    def __init__(
        self,
        method: str = "iqr",
        threshold: float = 1.5,
        columns: Optional[list[str]] = None,
    ):
        """
        Args:
            method: 检测方法
                - zscore: Z-score (|z| > threshold, 默认 3)
                - iqr: 四分位距法 (默认 1.5 IQR)
                - mad: 中位数绝对偏差
                - isolation_forest: 孤立森林
                - dbscan: 基于密度的聚类
            threshold: 阈值参数
                - zscore: 默认 3
                - iqr: 默认 1.5
                - mad: 默认 3.5
            columns: 要检测的列，None 为所有数值列
        """
        if method not in self.METHODS:
            raise ValueError(f"未知方法: {method}，可选 {self.METHODS}")
        self.method = method
        self.threshold = threshold
        self.columns = columns
        self._outlier_mask: Optional[pd.DataFrame] = None

    def detect(self, df: pd.DataFrame) -> pd.Series:
        """检测异常值。

        Args:
            df: 输入数据

        Returns:
            pd.Series: 每行是否为异常值的布尔标记（True=异常）
        """
        cols = self.columns or df.select_dtypes(include=np.number).columns.tolist()
        if not cols:
            return pd.Series(False, index=df.index)

        X = df[cols]

        if self.method == "zscore":
            return self._detect_zscore(X)
        elif self.method == "iqr":
            return self._detect_iqr(X)
        elif self.method == "mad":
            return self._detect_mad(X)
        elif self.method == "isolation_forest":
            return self._detect_iforest(X)
        elif self.method == "dbscan":
            return self._detect_dbscan(X)
        else:
            return pd.Series(False, index=df.index)

    def _detect_zscore(self, X: pd.DataFrame) -> pd.Series:
        """Z-score 法。"""
        z = np.abs((X - X.mean()) / X.std())
        threshold = self.threshold if self.threshold != 1.5 else 3.0
        return z.gt(threshold).any(axis=1)

    def _detect_iqr(self, X: pd.DataFrame) -> pd.Series:
        """IQR 法。"""
        Q1 = X.quantile(0.25)
        Q3 = X.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - self.threshold * IQR
        upper = Q3 + self.threshold * IQR
        return ((X < lower) | (X > upper)).any(axis=1)

    def _detect_mad(self, X: pd.DataFrame) -> pd.Series:
        """MAD (Median Absolute Deviation) 法。"""
        median = X.median()
        mad = np.abs(X - median).median()
        threshold = self.threshold if self.threshold != 1.5 else 3.5
        modified_z = 0.6745 * (X - median) / mad.replace(0, np.nan)
        return np.abs(modified_z).gt(threshold).any(axis=1)

    def _detect_iforest(self, X: pd.DataFrame) -> pd.Series:
        """孤立森林法。"""
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            raise ImportError("需要 scikit-learn: pip install scikit-learn")
        # 填充缺失值
        X_filled = X.fillna(X.median())
        clf = IsolationForest(contamination=0.05, random_state=42)
        pred = clf.fit_predict(X_filled)
        return pd.Series(pred == -1, index=X.index)

    def _detect_dbscan(self, X: pd.DataFrame) -> pd.Series:
        """DBSCAN 法（标记为噪声的样本视为异常）。"""
        try:
            from sklearn.cluster import DBSCAN
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            raise ImportError("需要 scikit-learn: pip install scikit-learn")
        X_filled = X.fillna(X.median())
        X_scaled = StandardScaler().fit_transform(X_filled)
        clf = DBSCAN(eps=2.0, min_samples=5)
        labels = clf.fit_predict(X_scaled)
        return pd.Series(labels == -1, index=X.index)

    def remove(self, df: pd.DataFrame) -> pd.DataFrame:
        """删除检测到的异常值行。

        Args:
            df: 输入数据

        Returns:
            pd.DataFrame: 删除异常值后的数据
        """
        mask = self.detect(df)
        self._outlier_mask = mask
        n_removed = mask.sum()
        if n_removed > 0:
            from mathmodel.utils.helpers import get_logger
            logger = get_logger("preprocessing.outlier")
            logger.info(f"检测到 {n_removed} 个异常值 ({n_removed / len(df) * 100:.1f}%)，已删除")
        return df[~mask].copy()

    def report(self, df: pd.DataFrame) -> str:
        """异常值检测报告。"""
        mask = self.detect(df)
        n_outliers = mask.sum()
        pct = n_outliers / len(df) * 100 if len(df) > 0 else 0
        lines = [
            f"📋 异常值检测报告 [{self.method}]",
            f"  总样本: {len(df)}",
            f"  异常值: {n_outliers} ({pct:.1f}%)",
            f"  正常值: {len(df) - n_outliers} ({100 - pct:.1f}%)",
        ]
        return "\n".join(lines)
