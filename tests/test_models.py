"""模型库单元测试。"""

import pytest
import numpy as np


class TestEvaluationSolver:
    """评价模型测试。"""

    def test_topsis_basic(self):
        from mathmodel.models.evaluation import EvaluationSolver
        solver = EvaluationSolver()

        matrix = np.array([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ], dtype=float)
        weights = [0.3, 0.3, 0.4]

        result = solver.topsis(matrix, weights)

        assert "scores" in result
        assert "rank" in result
        assert len(result["scores"]) == 3
        assert all(0 <= s <= 1 for s in result["scores"])
        # 得分应该降序排列（得分最高的排名第1）
        best_idx = np.argmax(result["scores"])
        assert result["rank"][best_idx] == 1

    def test_ahp_basic(self):
        from mathmodel.models.evaluation import EvaluationSolver
        solver = EvaluationSolver()

        # 3阶一致矩阵
        A = [
            [1, 2, 4],
            [1/2, 1, 2],
            [1/4, 1/2, 1],
        ]
        result = solver.ahp(A)

        assert "weights" in result
        assert len(result["weights"]) == 3
        assert abs(sum(result["weights"]) - 1.0) < 1e-6
        # 完全一致矩阵的 CR 应该接近 0
        assert result["cr"] < 0.01
        assert result["is_consistent"]

    def test_entropy_weight(self):
        from mathmodel.models.evaluation import EvaluationSolver
        solver = EvaluationSolver()

        matrix = np.array([
            [1, 10],
            [2, 9],
            [3, 8],
        ], dtype=float)

        result = solver.entropy_weight(matrix)
        assert len(result["weights"]) == 2
        assert abs(sum(result["weights"]) - 1.0) < 1e-6

    def test_fuzzy_comprehensive(self):
        from mathmodel.models.evaluation import EvaluationSolver
        solver = EvaluationSolver()

        R = np.array([
            [0.2, 0.5, 0.3],
            [0.1, 0.3, 0.6],
            [0.4, 0.4, 0.2],
        ])
        weights = [0.3, 0.4, 0.3]

        result = solver.fuzzy_comprehensive(R, weights)
        assert len(result["result"]) == 3
        assert abs(sum(result["result"]) - 1.0) < 1e-6
        assert 1 <= result["level"] <= 3

    def test_grey_relational(self):
        from mathmodel.models.evaluation import EvaluationSolver
        solver = EvaluationSolver()

        matrix = np.array([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ], dtype=float)

        result = solver.grey_relational(matrix)
        assert len(result["degrees"]) == 3
        assert len(result["rank"]) == 3

    def test_critic(self):
        from mathmodel.models.evaluation import EvaluationSolver
        solver = EvaluationSolver()

        matrix = np.random.rand(10, 4)
        result = solver.critic_weight(matrix)
        assert len(result["weights"]) == 4
        assert abs(sum(result["weights"]) - 1.0) < 1e-6


class TestStatsSolver:
    """统计模型测试。"""

    def test_grey_forecast(self):
        from mathmodel.models.statistics import StatsSolver
        solver = StatsSolver()

        # 指数增长序列
        data = [10, 16, 24, 36, 54]
        result = solver.grey_forecast(data, forecast_steps=2)

        assert len(result["forecast"]) == 2
        assert len(result["fitted"]) == 5
        assert result["p_value"] >= 0
        assert result["c_ratio"] >= 0

    def test_linear_regression(self):
        from mathmodel.models.statistics import StatsSolver
        solver = StatsSolver()

        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([2, 4, 6, 8, 10])

        result = solver.linear_regression(X, y)
        assert abs(result["r_squared"] - 1.0) < 0.01
        assert len(result["predictions"]) == 5

    def test_t_test(self):
        from mathmodel.models.statistics import StatsSolver
        solver = StatsSolver()

        g1 = [1, 2, 3, 4, 5]
        g2 = [6, 7, 8, 9, 10]

        result = solver.t_test(g1, g2)
        assert "p_value" in result
        assert "significant" in result

    def test_correlation(self):
        from mathmodel.models.statistics import StatsSolver
        solver = StatsSolver()

        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]

        result = solver.correlation(x, y, method="pearson")
        assert abs(result["coefficient"] - 1.0) < 0.01


class TestOptimizationSolver:
    """优化模型测试。"""

    def test_linear_program(self):
        from mathmodel.models.optimization import OptimizationSolver
        solver = OptimizationSolver()

        # min -x - 2y  s.t. x + y <= 10, x, y >= 0
        result = solver.linear_program(
            c=[-1, -2],
            A_ub=[[1, 1]],
            b_ub=[10],
            bounds=[(0, None), (0, None)],
        )
        assert result.success
        # 最优解：x=0, y=10
        assert abs(result.x[1] - 10) < 0.01
        assert abs(result.fun + 20) < 0.1

    def test_nonlinear_program(self):
        from mathmodel.models.optimization import OptimizationSolver
        solver = OptimizationSolver()

        def f(x):
            return (x[0] - 1)**2 + (x[1] - 2)**2

        result = solver.nonlinear_program(f, x0=[0, 0])
        assert result.success
        assert abs(result.x[0] - 1) < 0.01
        assert abs(result.x[1] - 2) < 0.01


class TestGraphSolver:
    """图论模型测试。"""

    def test_dijkstra(self):
        from mathmodel.models.graph import GraphSolver
        solver = GraphSolver()

        # 简单三角形图
        adj = [
            [0, 1, 4],
            [1, 0, 2],
            [4, 2, 0],
        ]
        result = solver.dijkstra(adj, source=0, target=2)
        assert result["distance_to_target"] == 3

    def test_min_spanning_tree(self):
        from mathmodel.models.graph import GraphSolver
        solver = GraphSolver()

        adj = [
            [0, 1, 3],
            [1, 0, 2],
            [3, 2, 0],
        ]
        result = solver.min_spanning_tree(adj)
        # MST 总权重应为 1+2=3
        assert abs(result["total_weight"] - 3) < 0.01

    def test_max_flow(self):
        from mathmodel.models.graph import GraphSolver
        solver = GraphSolver()

        capacity = [
            [0, 10, 0, 10],
            [0, 0, 10, 0],
            [0, 0, 0, 10],
            [0, 0, 0, 0],
        ]
        result = solver.max_flow(capacity, source=0, sink=2)
        assert result["max_flow"] == 10


class TestMLSolver:
    """机器学习测试。"""

    def test_pca(self):
        from mathmodel.models.ml import MLSolver
        solver = MLSolver()

        X = np.random.rand(20, 5)
        result = solver.pca(X, n_components=2)

        assert result["transformed"] is not None
        assert len(result["explained_variance_ratio"]) == 2
        assert 0 < result["cumulative_variance"] <= 1

    def test_kmeans(self):
        from mathmodel.models.ml import MLSolver
        solver = MLSolver()

        X = np.vstack([
            np.random.randn(10, 2) + [0, 0],
            np.random.randn(10, 2) + [5, 5],
        ])
        result = solver.kmeans(X, n_clusters=2)

        assert len(result["labels"]) == 20
        assert len(set(result["labels"])) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
