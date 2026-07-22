"""特征工程模块。

提供特征选择、降维、构造等操作。
"""

import numpy as np
import pandas as pd
from typing import Optional


class FeatureEngineer:
    """特征工程处理器。

    支持 PCA 降维、相关性筛选、多项式特征构造等。

    Usage::

        fe = FeatureEngineer()
        df_new = fe.reduce_dimension(df, method="pca", n_components=3)
        selected = fe.select_by_correlation(df, target="y", threshold=0.3)
    """

    def reduce_dimension(
        self,
        df: pd.DataFrame,
        method: str = "pca",
        n_components: int = 2,
        columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """降维。

        Args:
            df: 输入数据
            method: 降维方法 (pca, tsne)
            n_components: 目标维度
            columns: 要处理的列

        Returns:
            pd.DataFrame: 降维后的数据
        """
        cols = columns or df.select_dtypes(include=np.number).columns.tolist()
        X = df[cols].fillna(df[cols].median())

        try:
            from sklearn.preprocessing import StandardScaler
            X_scaled = StandardScaler().fit_transform(X)
        except ImportError:
            X_scaled = (X - X.mean()) / X.std()

        if method == "pca":
            from sklearn.decomposition import PCA
            model = PCA(n_components=n_components, random_state=42)
            transformed = model.fit_transform(X_scaled)
            result = pd.DataFrame(
                transformed,
                columns=[f"PC{i+1}" for i in range(n_components)],
                index=df.index,
            )
            return result

        elif method == "tsne":
            from sklearn.manifold import TSNE
            model = TSNE(n_components=n_components, random_state=42)
            transformed = model.fit_transform(X_scaled)
            result = pd.DataFrame(
                transformed,
                columns=[f"tSNE{i+1}" for i in range(n_components)],
                index=df.index,
            )
            return result

        raise ValueError(f"未知降维方法: {method}")

    def select_by_correlation(
        self,
        df: pd.DataFrame,
        target: str,
        threshold: float = 0.3,
        method: str = "pearson",
    ) -> dict:
        """基于相关性筛选特征。

        Args:
            df: 输入数据
            target: 目标列名
            threshold: 相关性阈值
            method: pearson / spearman

        Returns:
            dict: {"selected": [...], "scores": {...}, "dropped": [...]}
        """
        if target not in df.columns:
            raise ValueError(f"目标列 '{target}' 不存在")

        numeric_cols = df.select_dtypes(include=np.number).columns
        features = [c for c in numeric_cols if c != target]

        scores = {}
        for col in features:
            corr = df[target].corr(df[col], method=method)
            scores[col] = abs(corr)

        selected = [c for c, s in scores.items() if s >= threshold]
        dropped = [c for c, s in scores.items() if s < threshold]

        return {
            "selected": selected,
            "scores": {k: round(v, 4) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
            "dropped": dropped,
        }

    @staticmethod
    def add_polynomial_features(
        df: pd.DataFrame,
        columns: Optional[list[str]] = None,
        degree: int = 2,
    ) -> pd.DataFrame:
        """添加多项式特征。

        Args:
            df: 输入数据
            columns: 要处理的列
            degree: 多项式阶数

        Returns:
            pd.DataFrame: 包含原始列和新特征的 DataFrame
        """
        cols = columns or df.select_dtypes(include=np.number).columns.tolist()[:5]

        try:
            from sklearn.preprocessing import PolynomialFeatures
            pf = PolynomialFeatures(degree=degree, include_bias=False)
            transformed = pf.fit_transform(df[cols].fillna(0))
            new_names = pf.get_feature_names_out(cols)
            new_df = pd.DataFrame(transformed, columns=new_names, index=df.index)
            return pd.concat([df, new_df.iloc[:, len(cols):]], axis=1)
        except ImportError:
            pass

        # 手动实现简单版
        df = df.copy()
        for i, c1 in enumerate(cols):
            for c2 in cols[i:]:
                if degree >= 2:
                    name = f"{c1}×{c2}" if c1 != c2 else f"{c1}²"
                    df[name] = df[c1] * df[c2]
        return df

    @staticmethod
    def one_hot_encode(
        df: pd.DataFrame,
        columns: Optional[list[str]] = None,
        drop_first: bool = True,
    ) -> pd.DataFrame:
        """独热编码。

        Args:
            df: 输入数据
            columns: 要编码的列，None 为所有分类列
            drop_first: 是否丢弃第一列（避免多重共线性）

        Returns:
            pd.DataFrame: 编码后的数据
        """
        cols = columns or df.select_dtypes(include="object").columns.tolist()
        return pd.get_dummies(df, columns=cols, drop_first=drop_first)

    @staticmethod
    def binning(
        df: pd.DataFrame,
        column: str,
        bins: int = 5,
        labels: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """等距/等频分箱。

        Args:
            df: 输入数据
            column: 要分箱的列
            bins: 箱数
            labels: 标签列表

        Returns:
            pd.DataFrame: 含新列的数据
        """
        df = df.copy()
        df[f"{column}_binned"] = pd.cut(df[column], bins=bins, labels=labels)
        return df
