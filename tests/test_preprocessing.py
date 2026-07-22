"""数据预处理模块单元测试。"""

import pytest
import numpy as np
import pandas as pd


class TestMissingHandler:
    """缺失值处理测试。"""

    def test_mean_fill(self):
        from mathmodel.preprocessing.missing import MissingHandler
        handler = MissingHandler(strategy="mean")

        df = pd.DataFrame({"a": [1, 2, np.nan, 4], "b": [5, np.nan, 7, 8]})
        result = handler.fit_transform(df)

        assert result["a"].isnull().sum() == 0
        assert result["b"].isnull().sum() == 0
        assert abs(result.loc[2, "a"] - 7/3) < 0.01  # mean of [1,2,4]

    def test_median_fill(self):
        from mathmodel.preprocessing.missing import MissingHandler
        handler = MissingHandler(strategy="median")

        df = pd.DataFrame({"a": [1, 5, np.nan, 10]})
        result = handler.fit_transform(df)

        assert result["a"].isnull().sum() == 0
        assert abs(result.loc[2, "a"] - 5.0) < 0.01

    def test_drop(self):
        from mathmodel.preprocessing.missing import MissingHandler
        handler = MissingHandler(strategy="drop")

        df = pd.DataFrame({"a": [1, np.nan, 3], "b": [4, 5, 6]})
        result = handler.fit_transform(df)

        assert len(result) == 2  # 第2行被删除

    def test_report(self):
        from mathmodel.preprocessing.missing import MissingHandler
        handler = MissingHandler()

        df = pd.DataFrame({"a": [1, np.nan, 3], "b": [4, 5, np.nan]})
        report = handler.report(df)

        assert "a" in report
        assert "b" in report


class TestOutlierDetector:
    """异常值检测测试。"""

    def test_iqr_detect(self):
        from mathmodel.preprocessing.outlier import OutlierDetector
        detector = OutlierDetector(method="iqr", threshold=1.5)

        df = pd.DataFrame({"a": [1, 2, 3, 4, 5, 100]})
        mask = detector.detect(df)

        assert mask.sum() == 1  # 100 应该是异常值
        assert mask.iloc[5] == True

    def test_zscore_detect(self):
        from mathmodel.preprocessing.outlier import OutlierDetector
        detector = OutlierDetector(method="zscore", threshold=3.0)

        df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        mask = detector.detect(df)

        assert mask.sum() == 0  # 没有异常值

    def test_remove_outliers(self):
        from mathmodel.preprocessing.outlier import OutlierDetector
        detector = OutlierDetector(method="iqr")

        df = pd.DataFrame({"a": [1, 2, 3, 4, 5, 50]})
        result = detector.remove(df)

        assert len(result) < len(df)
        assert 50 not in result["a"].values


class TestNormalizer:
    """标准化测试。"""

    def test_zscore(self):
        from mathmodel.preprocessing.normalize import Normalizer
        norm = Normalizer(method="zscore")

        df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        result = norm.fit_transform(df)

        assert abs(result["a"].mean()) < 1e-10
        assert abs(result["a"].std() - 1.0) < 0.1

    def test_minmax(self):
        from mathmodel.preprocessing.normalize import Normalizer
        norm = Normalizer(method="minmax", feature_range=(0, 1))

        df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        result = norm.fit_transform(df)

        assert abs(result["a"].min()) < 1e-10
        assert abs(result["a"].max() - 1.0) < 1e-10

    def test_inverse_transform(self):
        from mathmodel.preprocessing.normalize import Normalizer
        norm = Normalizer(method="zscore")

        df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        transformed = norm.fit_transform(df)
        recovered = norm.inverse_transform(transformed)

        assert np.allclose(recovered["a"].values, df["a"].values, atol=1e-8)


class TestFeatureEngineer:
    """特征工程测试。"""

    def test_select_by_correlation(self):
        from mathmodel.preprocessing.feature import FeatureEngineer
        fe = FeatureEngineer()

        df = pd.DataFrame({
            "y": [1, 2, 3, 4, 5],
            "x1": [2, 4, 6, 8, 10],
            "x2": [5, 3, 1, 7, 2],
        })
        result = fe.select_by_correlation(df, target="y", threshold=0.5)

        assert "x1" in result["selected"]
        assert "x2" in result["dropped"]

    def test_one_hot_encode(self):
        from mathmodel.preprocessing.feature import FeatureEngineer
        fe = FeatureEngineer()

        df = pd.DataFrame({"cat": ["a", "b", "a", "c"]})
        result = fe.one_hot_encode(df)

        # drop_first=True，所以 a 被丢弃
        assert "cat_b" in result.columns or "cat_c" in result.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
