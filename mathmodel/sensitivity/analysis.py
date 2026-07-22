"""灵敏度分析器。

支持 OAT（一次变化法）、Morris、Sobol 方法。
"""

import numpy as np
from typing import Callable, Optional


class SensitivityAnalyzer:
    """灵敏度/鲁棒性分析器。

    Usage::

        sa = SensitivityAnalyzer()

        def model(params):
            x, y = params
            return x**2 + y**3

        result = sa.oat(model, base_params=[1.0, 2.0], deltas=[0.1, 0.1])
    """

    # =====================================================================
    # OAT 一次变化法
    # =====================================================================

    def oat(
        self,
        model_func: Callable[[np.ndarray], float],
        base_params: list[float],
        deltas: Optional[list[float]] = None,
        delta_pct: float = 0.1,
    ) -> dict:
        """OAT (One-At-a-Time) 灵敏度分析。

        每次只改变一个参数，观察输出变化幅度。

        Args:
            model_func: 模型函数 f(params) -> float
            base_params: 基准参数值
            deltas: 各参数的绝对变化量，None 时用 delta_pct * base_param
            delta_pct: 相对变化比例 (默认 10%)

        Returns:
            dict: {
                "base_output": 基准输出,
                "sensitivities": 各参数的灵敏度 [{param_index, delta, output, sensitivity}],
                "ranking": 按灵敏度排序的参数索引,
            }
        """
        base = np.array(base_params, dtype=float)
        base_output = model_func(base)

        if deltas is None:
            deltas = [abs(p * delta_pct) + 1e-6 for p in base]

        sensitivities = []
        for i in range(len(base)):
            params_perturbed = base.copy()
            params_perturbed[i] += deltas[i]
            output_perturbed = model_func(params_perturbed)

            sensitivity = abs(output_perturbed - base_output) / (abs(base_output) + 1e-10)
            sensitivities.append({
                "param_index": i,
                "base_value": float(base[i]),
                "delta": deltas[i],
                "output": float(output_perturbed),
                "output_change": float(output_perturbed - base_output),
                "sensitivity": round(float(sensitivity), 6),
            })

        ranking = sorted(
            range(len(sensitivities)),
            key=lambda i: sensitivities[i]["sensitivity"],
            reverse=True,
        )

        return {
            "base_output": float(base_output),
            "sensitivities": sensitivities,
            "ranking": ranking,
            "most_sensitive": ranking[0] if ranking else None,
        }

    # =====================================================================
    # Morris 方法
    # =====================================================================

    def morris(
        self,
        model_func: Callable[[np.ndarray], float],
        bounds: list[tuple[float, float]],
        n_trajectories: int = 10,
        n_levels: int = 4,
        seed: int = 42,
    ) -> dict:
        """Morris 筛选法。

        Args:
            model_func: 模型函数
            bounds: 各参数的取值范围 [(min, max), ...]
            n_trajectories: 轨迹数量 (推荐 10-50)
            n_levels: 网格水平数
            seed: 随机种子

        Returns:
            dict: {"mu": 均值, "mu_star": 绝对均值, "sigma": 标准差, "ranking": ...}
        """
        rng = np.random.RandomState(seed)
        k = len(bounds)
        delta = n_levels / (2 * (n_levels - 1))

        # 网格点
        grid = np.linspace(0, 1, n_levels)

        mu = np.zeros(k)
        mu_star = np.zeros(k)
        sigma = np.zeros(k)
        elementary_effects = [[] for _ in range(k)]

        for _ in range(n_trajectories):
            # 随机起点
            x = np.array([rng.choice(grid) for _ in range(k)])

            # 随机方向
            D = rng.choice([-1, 1], size=k)
            # 随机排列
            perm = rng.permutation(k)

            prev_y = model_func(self._unscale(x, bounds))

            for i in perm:
                x_new = x.copy()
                x_new[i] += D[i] * delta
                # 边界检查
                x_new[i] = np.clip(x_new[i], 0, 1)

                y_new = model_func(self._unscale(x_new, bounds))
                ee = (y_new - prev_y) / (D[i] * delta)
                elementary_effects[i].append(ee)
                prev_y = y_new
                x = x_new

        for i in range(k):
            ee_arr = np.array(elementary_effects[i])
            mu[i] = np.mean(ee_arr)
            mu_star[i] = np.mean(np.abs(ee_arr))
            sigma[i] = np.std(ee_arr)

        ranking = np.argsort(mu_star)[::-1]

        return {
            "mu": mu.tolist(),
            "mu_star": mu_star.tolist(),
            "sigma": sigma.tolist(),
            "ranking": ranking.tolist(),
            "most_influential": int(ranking[0]),
        }

    # =====================================================================
    # 参数鲁棒性检验
    # =====================================================================

    def robustness_check(
        self,
        model_func: Callable[[np.ndarray], float],
        base_params: list[float],
        noise_std: Optional[list[float]] = None,
        noise_pct: float = 0.05,
        n_samples: int = 1000,
        seed: int = 42,
    ) -> dict:
        """蒙特卡洛鲁棒性检验。

        在参数上叠加随机噪声，检验输出分布的稳定性。

        Args:
            model_func: 模型函数
            base_params: 基准参数
            noise_std: 各参数的噪声标准差，None 时用 noise_pct * param
            noise_pct: 噪声相对标准差
            n_samples: 采样次数
            seed: 随机种子

        Returns:
            dict: {"mean", "std", "cv", "ci_95", "min", "max"}
        """
        rng = np.random.RandomState(seed)
        base = np.array(base_params, dtype=float)

        if noise_std is None:
            noise_std = [abs(p * noise_pct) + 1e-6 for p in base]

        outputs = np.zeros(n_samples)
        for i in range(n_samples):
            perturbed = base + rng.normal(0, noise_std, len(base))
            outputs[i] = model_func(perturbed)

        mean = outputs.mean()
        std = outputs.std()
        cv = std / (abs(mean) + 1e-10)
        ci_95_low = np.percentile(outputs, 2.5)
        ci_95_high = np.percentile(outputs, 97.5)

        return {
            "mean": round(float(mean), 6),
            "std": round(float(std), 6),
            "cv": round(float(cv), 4),
            "ci_95": [round(float(ci_95_low), 6), round(float(ci_95_high), 6)],
            "min": round(float(outputs.min()), 6),
            "max": round(float(outputs.max()), 6),
            "is_robust": cv < 0.1,
        }

    @staticmethod
    def _unscale(x: np.ndarray, bounds: list[tuple[float, float]]) -> np.ndarray:
        """将 [0,1] 归一化的 x 映射回原始范围。"""
        return np.array([
            bounds[i][0] + x[i] * (bounds[i][1] - bounds[i][0])
            for i in range(len(x))
        ])
