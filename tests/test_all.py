"""Core solver tests — 验证所有求解器可正常实例化和运行"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest


class TestEvaluationSolver:
    """评价类求解器测试"""

    def test_import(self):
        from mathmodel.models import EvaluationSolver
        ev = EvaluationSolver()
        assert ev is not None

    def test_entropy_weight(self):
        from mathmodel.models import EvaluationSolver
        ev = EvaluationSolver()
        m = np.array([[100, 0.5, 30], [80, 0.8, 50], [60, 0.3, 20]])
        r = ev.entropy_weight(m)
        assert "weights" in r
        assert len(r["weights"]) == 3
        assert all(0 <= w <= 1 for w in r["weights"])

    def test_topsis(self):
        from mathmodel.models import EvaluationSolver
        ev = EvaluationSolver()
        m = np.array([[100, 0.5, 30], [80, 0.8, 50], [60, 0.3, 20]])
        r = ev.topsis(m, weights=[0.4, 0.3, 0.3], impacts=[1, 1, -1])
        assert "scores" in r and "rank" in r
        assert len(r["scores"]) == 3
        assert len(r["rank"]) == 3

    def test_ahp(self):
        from mathmodel.models import EvaluationSolver
        ev = EvaluationSolver()
        mat = np.array([[1, 3, 5], [1/3, 1, 2], [1/5, 1/2, 1]])
        r = ev.ahp(mat)
        assert "cr" in r and "weights" in r
        assert r["cr"] < 0.1  # consistent

    def test_grey_relational(self):
        from mathmodel.models import EvaluationSolver
        ev = EvaluationSolver()
        r = ev.grey_relational(np.array([[10, 5, 3], [8, 7, 4], [6, 9, 5]]))
        assert "degrees" in r
        assert len(r["degrees"]) == 3


class TestStatsSolver:
    """统计/预测类求解器测试"""

    def test_import(self):
        from mathmodel.models import StatsSolver
        ss = StatsSolver()
        assert ss is not None

    def test_grey_forecast(self):
        from mathmodel.models import StatsSolver
        ss = StatsSolver()
        data = [12, 15, 19, 24, 30, 38, 47, 57]
        r = ss.grey_forecast(data, forecast_steps=3)
        assert "forecast" in r
        assert len(r["forecast"]) == 3
        assert "mape" in r and "grade" in r
        assert r["mape"] < 20  # decent fit


class TestOptimizationSolver:
    """优化类求解器测试"""

    def test_import(self):
        from mathmodel.models import OptimizationSolver
        opt = OptimizationSolver()
        assert opt is not None

    def test_integer_program(self):
        from mathmodel.models import OptimizationSolver
        opt = OptimizationSolver()
        r = opt.integer_program(
            c=[-3, -5], A_ub=[[2, 4]], b_ub=[10],
            bounds=(0, 5), binary=False,
        )
        assert r.success
        assert -15 <= r.fun <= 0


class TestMLSolver:
    """机器学习求解器测试"""

    def test_import(self):
        from mathmodel.models import MLSolver
        mls = MLSolver()
        assert mls is not None

    def test_kmeans(self):
        from mathmodel.models import MLSolver
        mls = MLSolver()
        X = np.random.RandomState(42).rand(30, 4)
        r = mls.kmeans(X, n_clusters=3)
        assert "labels" in r and "silhouette_score" in r
        assert len(r["labels"]) == 30

    def test_pca(self):
        from mathmodel.models import MLSolver
        mls = MLSolver()
        X = np.random.RandomState(42).rand(30, 5)
        r = mls.pca(X, n_components=2)
        assert "transformed" in r and "cumulative_variance" in r
        assert len(r["transformed"]) == 30

    def test_random_forest(self):
        from mathmodel.models import MLSolver
        mls = MLSolver()
        X = np.random.RandomState(42).rand(50, 3)
        y = X[:, 0] * 2 + X[:, 1] * 0.5 + np.random.randn(50) * 0.1
        r = mls.random_forest_regression(X, y, n_estimators=20)
        assert "r_squared" in r and r["r_squared"] > 0

    def test_svm_classify(self):
        from mathmodel.models import MLSolver
        mls = MLSolver()
        X = np.random.RandomState(42).rand(40, 4)
        y = (X[:, 0] + X[:, 1] > 1).astype(int)
        r = mls.svm_classify(X, y)
        assert "accuracy" in r and r["accuracy"] > 0.5


class TestDiffEqSolver:
    """微分方程求解器测试"""

    def test_import(self):
        from mathmodel.models import DiffEqSolver
        des = DiffEqSolver()
        assert des is not None

    def test_solve_ode(self):
        from mathmodel.models import DiffEqSolver
        des = DiffEqSolver()

        def dydt(t, y):
            return [-0.5 * y[0]]

        r = des.solve_ode(dydt, y0=[10], t_span=[0, 10])
        assert r is not None and isinstance(r, dict)
        assert "t" in r and "y" in r
        assert r["success"] is True
        assert r["y"][-1][0] < r["y"][0][0]  # decay

    def test_sir_model(self):
        from mathmodel.models import DiffEqSolver
        des = DiffEqSolver()
        r = des.sir_model(population=10000, beta=0.3, gamma=0.1, days=100)
        assert "S" in r and "I" in r and "R" in r
        assert len(r["I"]) > 0

    def test_logistic(self):
        from mathmodel.models import DiffEqSolver
        des = DiffEqSolver()
        # Use realistic logistic growth data (S-curve)
        t_data = list(range(20))
        y_data = [1000 / (1 + 9 * np.exp(-0.4 * t)) + np.random.randn() * 2 for t in t_data]
        r = des.logistic_model(t_data, y_data, forecast_steps=5)
        assert "forecast" in r or "K" in r
        assert isinstance(r, dict)


class TestGraphSolver:
    """图论求解器测试"""

    def test_import(self):
        from mathmodel.models import GraphSolver
        gs = GraphSolver()
        assert gs is not None

    def test_dijkstra(self):
        from mathmodel.models import GraphSolver
        gs = GraphSolver()
        adj = [[0, 4, 2], [4, 0, 1], [2, 1, 0]]
        r = gs.dijkstra(adj, source=0, target=2)
        assert "distance_to_target" in r and "path_to_target" in r
        assert r["distance_to_target"] == 2

    def test_floyd(self):
        from mathmodel.models import GraphSolver
        gs = GraphSolver()
        adj = [[0, 4, 2], [4, 0, 1], [2, 1, 0]]
        r = gs.floyd(adj)
        assert "distance_matrix" in r
        assert len(r["distance_matrix"]) == 3

    def test_max_flow(self):
        from mathmodel.models import GraphSolver
        gs = GraphSolver()
        cap = [[0, 16, 13, 0], [0, 0, 10, 12], [0, 4, 0, 14], [0, 0, 0, 0]]
        r = gs.max_flow(cap, source=0, sink=3)
        assert "max_flow" in r
        assert r["max_flow"] > 0


class TestPreprocessing:
    """预处理模块测试"""

    def test_missing_handler(self):
        from mathmodel.preprocessing import MissingHandler
        df = pd.DataFrame({"A": [1, 2, None, 4, 100], "B": [10, None, 30, 40, 50]})
        mh = MissingHandler(strategy="median")
        result = mh.fit_transform(df)
        assert result.isnull().sum().sum() == 0

    def test_outlier_detector(self):
        from mathmodel.preprocessing import OutlierDetector
        df = pd.DataFrame({"A": [1, 2, 3, 4, 100]})
        od = OutlierDetector(method="iqr")
        mask = od.detect(df)
        assert mask.sum() >= 0

    def test_normalizer(self):
        from mathmodel.preprocessing import Normalizer
        df = pd.DataFrame({"A": [1, 2, 3, 4, 5], "B": [10, 20, 30, 40, 50]})
        norm = Normalizer(method="zscore")
        result = norm.fit_transform(df)
        assert abs(result["A"].mean()) < 0.01  # zscore mean ~= 0


class TestClassifier:
    """题型分类器测试"""

    def test_classify_evaluation(self):
        from mathmodel.analyzer.classifier import ProblemClassifier
        clf = ProblemClassifier()
        r = clf.classify("请对5个城市的经济发展水平进行综合评价排名")
        assert r["type"] in ("评价", "综合")

    def test_classify_prediction(self):
        from mathmodel.analyzer.classifier import ProblemClassifier
        clf = ProblemClassifier()
        r = clf.classify("请建立模型预测未来3年的GDP增长率")
        assert r["type"] in ("预测", "综合")

    def test_classify_optimization(self):
        from mathmodel.analyzer.classifier import ProblemClassifier
        clf = ProblemClassifier()
        r = clf.classify("在预算约束下最大化利润")
        assert r["type"] in ("优化", "评价", "综合")


class TestProModules:
    """Pro 模块测试"""

    def test_model_contest_local(self):
        from mathmodel.pro import ModelContest
        mc = ModelContest()  # no API key
        assert mc.use_ai is False

    def test_deep_sensitivity_tornado(self):
        from mathmodel.pro import DeepSensitivity
        ds = DeepSensitivity()

        def f(x):
            return float(sum(x))

        r = ds.tornado(f, [1, 2, 3, 4, 5], ["A", "B", "C", "D", "E"])
        assert "most_sensitive" in r and r["most_sensitive"] != ""

    def test_error_diagnostics(self):
        from mathmodel.pro import ErrorDiagnostics
        ed = ErrorDiagnostics()
        actual = [12, 15, 19, 24, 30, 38, 47, 57]
        fitted = [12.5, 15.8, 18.9, 23.5, 30.2, 37.5, 46.8, 58.0]
        r = ed.residual_analysis(actual, fitted)
        assert "mape" in r and "dw" in r
        assert r["mape"] < 20

    def test_chart_suite(self):
        from mathmodel.pro import ChartSuite
        cs = ChartSuite()
        import io
        actual = [12, 15, 19, 24, 30, 38, 47, 57]
        fitted = [12.5, 15.8, 18.9, 23.5, 30.2, 37.5, 46.8, 58.0]
        forecast = [71.4, 88.8, 110.5]
        path = cs.prediction_suite(actual, fitted, forecast)
        assert path == "" or path.endswith(".png")

    def test_result_narrator_fallback(self):
        from mathmodel.pro.result_writer import ResultNarrator
        rn = ResultNarrator(api_key="")
        sp = {"id": 1, "type": "评价", "model": "TOPSIS"}
        result = {"scores": [0.6, 0.3, 0.5], "labels": ["A", "B", "C"]}
        text = rn._fallback_narrative(sp, result)
        assert len(text) > 0
        assert "A" in text or "0.6000" in text


class TestRichProgress:
    """Rich 进度模块测试"""

    def test_import(self):
        from mathmodel.pipeline.rich_progress import (
            PhaseTracker, print_header, print_section, print_result_summary,
        )
        assert PhaseTracker is not None

    def test_tracker_no_crash(self):
        from mathmodel.pipeline.rich_progress import PhaseTracker
        tracker = PhaseTracker(title="test")
        tracker.start_phase("Test Phase", 10)
        tracker.update(5)
        tracker.complete_phase("done")
        tracker.finish()  # should not raise
