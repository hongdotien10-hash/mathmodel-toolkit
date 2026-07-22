"""Pro: 深度灵敏度分析 — Tornado图 + Sobol指数 + 蒙特卡洛"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Callable, Optional
from mathmodel.visualization.styles import despine, get_colors


class DeepSensitivity:
    """深度灵敏度 — OAT→Tornado→Sobol→蒙特卡洛"""

    def tornado(self, model_func: Callable, base_params: list[float],
                param_names: list[str], delta_pct: float = 0.2) -> dict:
        """Tornado图：各参数±delta_pct%扰动，按影响排序"""
        base = model_func(np.array(base_params))
        impacts = []
        for i, (p, name) in enumerate(zip(base_params, param_names)):
            up = np.array(base_params); up[i] = p * (1 + delta_pct)
            dn = np.array(base_params); dn[i] = p * (1 - delta_pct)
            try:
                v_up = model_func(up); v_dn = model_func(dn)
                delta_up = v_up - base; delta_dn = v_dn - base
                impacts.append({"param": name, "base": round(float(base), 6),
                                "delta_up": round(float(delta_up), 6),
                                "delta_dn": round(float(delta_dn), 6),
                                "abs_max": max(abs(delta_up), abs(delta_dn)),
                                "sensitivity": round(float(abs(delta_up - delta_dn)), 6)})
            except Exception:
                impacts.append({"param": name, "error": True})
        impacts.sort(key=lambda x: -x.get("abs_max", 0))
        return {"base_output": round(float(base), 6), "impacts": impacts,
                "most_sensitive": impacts[0]["param"] if impacts else ""}

    def sobol(self, model_func: Callable, bounds: list[tuple], n_samples: int = 1000) -> dict:
        """Sobol一阶/总效应指数（简化Saltelli方法）"""
        k = len(bounds)
        # 2k+2 matrices for Saltelli sampling
        n = n_samples
        A = np.random.uniform(0, 1, (n, k))
        B = np.random.uniform(0, 1, (n, k))
        fA = np.array([model_func(A[i]) for i in range(n)])
        fB = np.array([model_func(B[i]) for i in range(n)])
        S1 = []; ST = []
        for j in range(k):
            AB = A.copy(); AB[:, j] = B[:, j]
            fAB = np.array([model_func(AB[i]) for i in range(n)])
            # First order
            S1.append(float(1.0 / n * np.sum(fB * (fAB - fA)) / max(np.var(np.hstack([fA, fB])), 1e-10)))
            # Total effect
            ST.append(float(0.5 / n * np.sum((fA - fAB)**2) / max(np.var(np.hstack([fA, fB])), 1e-10)))
        return {"S1": [round(float(s), 4) for s in S1], "ST": [round(float(s), 4) for s in ST],
                "important_params": [i for i, s in enumerate(ST) if s > 0.05]}

    def monte_carlo(self, model_func: Callable, base_params: list[float],
                    noise_pct: float = 0.05, n_samples: int = 1000) -> dict:
        """蒙特卡洛：参数加噪声采样→输出分布"""
        outputs = []
        params_arr = np.array(base_params)
        for _ in range(n_samples):
            noise = np.random.normal(0, noise_pct * np.abs(params_arr) + 1e-6)
            perturbed = params_arr + noise
            outputs.append(model_func(np.maximum(perturbed, 0)))
        o = np.array(outputs)
        ci = np.percentile(o, [2.5, 97.5])
        return {"mean": round(float(np.mean(o)), 6), "std": round(float(np.std(o)), 6),
                "cv": round(float(np.std(o) / max(np.mean(o), 1e-10)), 6),
                "ci_95": [round(float(ci[0]), 6), round(float(ci[1]), 6)],
                "min": round(float(o.min()), 6), "max": round(float(o.max()), 6)}

    def plot_tornado(self, impacts: list[dict], title: str = "Parameter Sensitivity (Tornado)",
                     output_path: str = "") -> str:
        """画Tornado图"""
        names = [i["param"] for i in reversed(impacts)]
        up_vals = [i["delta_up"] for i in reversed(impacts)]
        dn_vals = [i["delta_dn"] for i in reversed(impacts)]
        fig, ax = plt.subplots(figsize=(6, max(3, len(names)*0.4)))
        colors = get_colors(2)
        y_pos = range(len(names))
        ax.barh(y_pos, up_vals, height=0.5, color=colors[0], alpha=0.7, label="+ perturbation", edgecolor="white")
        ax.barh(y_pos, dn_vals, height=0.5, color=colors[1], alpha=0.7, label="- perturbation", edgecolor="white")
        ax.set_yticks(y_pos); ax.set_yticklabels(names, fontsize=9)
        ax.axvline(x=0, color="black", linewidth=0.8)
        ax.set_xlabel("Output Change"); ax.legend(fontsize=8, frameon=False)
        ax.grid(axis="x", alpha=0.2, linestyle=":"); despine(ax)
        fig.tight_layout()
        if output_path:
            from pathlib import Path; Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def plot_mc_distribution(self, outputs: list[float], output_path: str = "") -> str:
        """画蒙特卡洛输出分布"""
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.hist(outputs, bins=40, color=get_colors(1)[0], alpha=0.7, edgecolor="white", density=True)
        mean = np.mean(outputs)
        ci_low, ci_hi = np.percentile(outputs, [2.5, 97.5])
        ax.axvline(mean, color="red", linewidth=2, label=f"Mean={mean:.4f}")
        ax.axvline(ci_low, color="gray", linestyle="--", alpha=0.7, label=f"95%CI=[{ci_low:.4f}, {ci_hi:.4f}]")
        ax.axvline(ci_hi, color="gray", linestyle="--", alpha=0.7)
        ax.set_xlabel("Output"); ax.set_ylabel("Density")
        ax.legend(fontsize=8, frameon=False); despine(ax)
        ax.grid(alpha=0.2, linestyle=":"); fig.tight_layout()
        if output_path:
            from pathlib import Path; Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return output_path
