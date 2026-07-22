"""机器学习模型求解器。

提供聚类、分类、降维等竞赛常用 ML 方法。
"""

import numpy as np
import pandas as pd
from typing import Optional, Literal


class MLSolver:
    """机器学习求解器。

    Usage::

        mls = MLSolver()

        # K-means 聚类
        result = mls.kmeans(X, n_clusters=3)

        # PCA 降维
        result = mls.pca(X, n_components=2)
    """

    def kmeans(
        self,
        X: np.ndarray | pd.DataFrame,
        n_clusters: int = 3,
        random_state: int = 42,
    ) -> dict:
        """K-means 聚类。

        Returns:
            dict: {"labels", "centers", "inertia", "silhouette_score"}
        """
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        if isinstance(X, pd.DataFrame):
            X = X.values
        X = np.array(X, dtype=float)

        model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        labels = model.fit_predict(X)

        sil = silhouette_score(X, labels) if n_clusters > 1 else 0

        return {
            "labels": labels.tolist(),
            "centers": model.cluster_centers_.tolist(),
            "inertia": float(model.inertia_),
            "silhouette_score": round(float(sil), 4),
        }

    def dbscan(
        self,
        X: np.ndarray | pd.DataFrame,
        eps: float = 0.5,
        min_samples: int = 5,
    ) -> dict:
        """DBSCAN 密度聚类。"""
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler

        if isinstance(X, pd.DataFrame):
            X = X.values
        X = StandardScaler().fit_transform(X)

        model = DBSCAN(eps=eps, min_samples=min_samples)
        labels = model.fit_predict(X)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = int((labels == -1).sum())

        return {
            "labels": labels.tolist(),
            "n_clusters": n_clusters,
            "n_noise": n_noise,
        }

    def hierarchical(
        self,
        X: np.ndarray | pd.DataFrame,
        n_clusters: int = 3,
        method: str = "ward",
    ) -> dict:
        """层次聚类。"""
        from sklearn.cluster import AgglomerativeClustering

        if isinstance(X, pd.DataFrame):
            X = X.values

        model = AgglomerativeClustering(n_clusters=n_clusters, linkage=method)
        labels = model.fit_predict(X)

        return {"labels": labels.tolist(), "n_clusters": n_clusters}

    def pca(
        self,
        X: np.ndarray | pd.DataFrame,
        n_components: int = 2,
    ) -> dict:
        """PCA 主成分分析。

        Returns:
            dict: {"transformed", "components", "explained_variance_ratio", "cumulative_variance"}
        """
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler

        if isinstance(X, pd.DataFrame):
            X = X.values
        X_scaled = StandardScaler().fit_transform(X)

        model = PCA(n_components=n_components)
        transformed = model.fit_transform(X_scaled)

        return {
            "transformed": transformed.tolist(),
            "components": model.components_.tolist(),
            "explained_variance_ratio": model.explained_variance_ratio_.tolist(),
            "cumulative_variance": float(np.cumsum(model.explained_variance_ratio_)[-1]),
        }

    def random_forest_regression(
        self,
        X: np.ndarray | pd.DataFrame,
        y: np.ndarray | pd.Series,
        n_estimators: int = 100,
        **kwargs,
    ) -> dict:
        """随机森林回归。"""
        from sklearn.ensemble import RandomForestRegressor

        if isinstance(X, pd.DataFrame):
            feature_names = X.columns.tolist()
            X = X.values
        else:
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        if isinstance(y, pd.Series):
            y = y.values

        model = RandomForestRegressor(n_estimators=n_estimators, random_state=42, **kwargs)
        model.fit(X, y)
        predictions = model.predict(X)

        r2 = 1 - np.sum((y - predictions) ** 2) / np.sum((y - y.mean()) ** 2)

        importances = sorted(
            zip(feature_names, model.feature_importances_),
            key=lambda x: -x[1],
        )

        return {
            "predictions": predictions.tolist(),
            "r_squared": round(float(r2), 6),
            "feature_importance": [(name, round(float(imp), 4)) for name, imp in importances],
        }

    def svm_classify(
        self,
        X: np.ndarray | pd.DataFrame,
        y: np.ndarray | pd.Series,
        kernel: str = "rbf",
    ) -> dict:
        """SVM 分类器。"""
        from sklearn.svm import SVC
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import accuracy_score

        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, pd.Series):
            y = y.values

        X_scaled = StandardScaler().fit_transform(X)
        model = SVC(kernel=kernel, random_state=42)
        model.fit(X_scaled, y)
        pred = model.predict(X_scaled)
        acc = accuracy_score(y, pred)

        return {
            "predictions": pred.tolist(),
            "accuracy": round(float(acc), 4),
            "n_support_": [int(s) for s in model.n_support_],
        }
