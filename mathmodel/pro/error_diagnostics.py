"""Pro: 误差诊断 — 残差分析+QQ图+预测区间+排名稳定性"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mathmodel.visualization.styles import despine, get_colors


class ErrorDiagnostics:
    """误差诊断器"""

    def residual_analysis(self, actual: list[float], fitted: list[float]) -> dict:
        """残差分析：残差vs拟合值 + 残差时序 + QQ图诊断"""
        a, f = np.array(actual), np.array(fitted)
        residuals = a - f
        std_res = residuals / max(np.std(residuals), 1e-10)
        mae = float(np.mean(np.abs(residuals)))
        mse = float(np.mean(residuals**2))
        rmse = float(np.sqrt(mse))
        mape = float(np.mean(np.abs(residuals / np.maximum(np.abs(a), 1e-10))) * 100)
        # Normality test
        from scipy import stats
        shapiro_stat, shapiro_p = 0, 1
        try: shapiro_stat, shapiro_p = stats.shapiro(residuals)
        except: pass
        is_normal = shapiro_p > 0.05
        # Durbin-Watson for autocorrelation
        dw_num = np.sum((residuals[1:] - residuals[:-1])**2)
        dw_denom = np.sum(residuals**2) + 1e-10
        dw = float(dw_num / dw_denom)
        has_autocorr = dw < 1.5 or dw > 2.5
        return {"residuals": [round(float(r), 4) for r in residuals],
                "std_residuals": [round(float(r), 4) for r in std_res],
                "mae": round(mae, 4), "mse": round(mse, 4), "rmse": round(rmse, 4),
                "mape": round(mape, 2), "shapiro_p": round(float(shapiro_p), 4),
                "is_normal": is_normal, "dw": round(dw, 4), "has_autocorr": has_autocorr}

    def prediction_intervals(self, fitted: list[float], forecast: list[float],
                              residuals_std: float, confidence: float = 0.95) -> dict:
        """预测区间（基于残差标准差的 t 分布近似）"""
        from scipy import stats
        n = len(fitted)
        alpha = 1 - confidence
        t_val = stats.t.ppf(1 - alpha/2, max(n-2, 1)) if n > 2 else 1.96
        margin = t_val * residuals_std * np.sqrt(1 + 1/n)
        intervals = []
        for fv in forecast:
            intervals.append({"forecast": round(float(fv), 4),
                              "lower": round(float(fv - margin), 4),
                              "upper": round(float(fv + margin), 4)})
        return {"intervals": intervals, "confidence": confidence, "margin": round(float(margin), 4)}

    def rank_reversal_test(self, matrix: np.ndarray, weights: list[float],
                           impacts: list[int], n_trials: int = 100) -> dict:
        """TOPSIS排名稳定性：随机扰动权重±20%，统计排名变化"""
        from mathmodel.models.evaluation import EvaluationSolver
        ev = EvaluationSolver()
        m = matrix.shape[0]
        rank_counts = np.zeros((m, m))
        w = np.array(weights)
        for _ in range(n_trials):
            perturbed = w * np.random.uniform(0.8, 1.2, len(w))
            perturbed = perturbed / perturbed.sum()
            res = ev.topsis(matrix, weights=perturbed, impacts=impacts)
            rank = np.argsort([-s for s in res["scores"]])  # best first
            for pos, idx in enumerate(rank):
                rank_counts[idx, pos] += 1
        stability = rank_counts / n_trials
        # Diagonal = probability of staying at same rank
        diag = np.diag(stability)
        return {"stability_matrix": [[round(float(v), 3) for v in row] for row in stability],
                "diagonal_stability": [round(float(d), 4) for d in diag],
                "mean_stability": round(float(np.mean(diag)), 4)}

    def plot_residuals(self, actual: list[float], fitted: list[float],
                       output_path: str = "", label_prefix: str = "") -> str:
        """画残差诊断组图：残差vs拟合 + QQ图 + 残差时序"""
        a, f = np.array(actual), np.array(fitted)
        residuals = a - f
        colors = get_colors(3)
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))

        # (a) Residuals vs Fitted
        ax = axes[0]
        ax.scatter(fitted, residuals, c=colors[0], alpha=0.6, s=40, edgecolors="white")
        ax.axhline(0, color="gray", linestyle="--", alpha=0.5)
        ax.set_xlabel("Fitted"); ax.set_ylabel("Residual"); ax.set_title("(a) Residuals vs Fitted", fontsize=10)
        despine(ax); ax.grid(alpha=0.2, linestyle=":")

        # (b) QQ Plot
        ax = axes[1]
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=ax)
        ax.get_lines()[0].set_markerfacecolor(colors[1]); ax.get_lines()[0].set_markeredgecolor("white")
        ax.set_title("(b) Q-Q Plot", fontsize=10)
        despine(ax); ax.grid(alpha=0.2, linestyle=":")

        # (c) Residual Time Series
        ax = axes[2]
        ax.plot(range(len(residuals)), residuals, 'o-', color=colors[2], markersize=5,
                markerfacecolor="white", linewidth=1.5)
        ax.axhline(0, color="gray", linestyle="--", alpha=0.5)
        ax.fill_between(range(len(residuals)), -1.96*np.std(residuals), 1.96*np.std(residuals),
                        alpha=0.1, color=colors[2])
        ax.set_xlabel("Index"); ax.set_ylabel("Residual"); ax.set_title("(c) Residual Sequence", fontsize=10)
        despine(ax); ax.grid(alpha=0.2, linestyle=":")

        fig.tight_layout()
        if output_path:
            from pathlib import Path; Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def plot_prediction_interval(self, fitted: list[float], forecast: list[float],
                                  intervals: list[dict], output_path: str = "") -> str:
        """画预测区间图"""
        n_fit = len(fitted); n_fore = len(forecast)
        all_x = list(range(1, n_fit + n_fore + 1))
        colors = get_colors(2)
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(range(1, n_fit+1), fitted, color=colors[0], linewidth=2, marker="o", markersize=5, markerfacecolor="white", label="Fitted")
        forecast_x = range(n_fit+1, n_fit+n_fore+1)
        ax.plot(forecast_x, forecast, color=colors[1], linewidth=2, linestyle="--", marker="s", markersize=5, markerfacecolor="white", label="Forecast")
        lower = [i["lower"] for i in intervals]
        upper = [i["upper"] for i in intervals]
        ax.fill_between(forecast_x, lower, upper, alpha=0.15, color=colors[1], label=f"{intervals[0].get('confidence',0.95)*100:.0f}% Prediction Interval")
        ax.axvline(x=n_fit+0.5, color="gray", linestyle=":", alpha=0.5)
        ax.set_xlabel("Time"); ax.set_ylabel("Value")
        ax.legend(fontsize=8, frameon=False); despine(ax); ax.grid(alpha=0.2, linestyle=":")
        fig.tight_layout()
        if output_path:
            from pathlib import Path; Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return output_path
