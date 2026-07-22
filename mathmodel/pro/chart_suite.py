"""Pro: 专业图表组 — 国赛标准多面板布局"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mathmodel.visualization.styles import despine, get_colors


class ChartSuite:
    """国赛标准多面板图表组"""

    def prediction_suite(self, actual: list, fitted: list, forecast: list,
                         residuals: list = None, intervals: list = None,
                         output_path: str = "") -> str:
        """2×2 预测对比组: (a)趋势 (b)残差 (c)预测区间 (d)指标表"""
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        colors = get_colors(4)
        n_fit, n_fore = len(fitted), len(forecast)

        # (a) Trend
        ax = axes[0, 0]
        ax.plot(range(1, n_fit+1), fitted, color=colors[0], linewidth=2, marker="o",
                markersize=4, markerfacecolor="white", label="Fitted")
        ax.plot(range(n_fit+1, n_fit+n_fore+1), forecast, color=colors[1], linewidth=2,
                linestyle="--", marker="s", markersize=4, markerfacecolor="white", label="Forecast")
        if actual:
            ax.scatter(range(1, len(actual)+1), actual, color=colors[2], s=30, zorder=5,
                       edgecolors="white", label="Actual")
        ax.axvline(x=n_fit+0.5, color="gray", linestyle=":", alpha=0.5)
        ax.set_title("(a) Forecast Trend", fontsize=11, loc="left"); ax.set_xlabel("Period")
        ax.legend(fontsize=7, frameon=False); despine(ax); ax.grid(alpha=0.2, linestyle=":")

        # (b) Residuals
        ax = axes[0, 1]
        if residuals is not None:
            ax.scatter(range(len(residuals)), residuals, c=colors[0], alpha=0.6, s=30, edgecolors="white")
            ax.axhline(0, color="gray", linestyle="--", alpha=0.5)
            r_std = np.std(residuals)
            ax.fill_between(range(len(residuals)), -1.96*r_std, 1.96*r_std, alpha=0.1, color=colors[0])
        ax.set_title("(b) Residuals", fontsize=11, loc="left"); ax.set_xlabel("Index")
        despine(ax); ax.grid(alpha=0.2, linestyle=":")

        # (c) Prediction Intervals
        ax = axes[1, 0]
        if intervals:
            f_x = range(n_fit+1, n_fit+n_fore+1)
            ax.plot(f_x, forecast, color=colors[1], linewidth=2, marker="s", markersize=4, markerfacecolor="white")
            lower = [i["lower"] for i in intervals]
            upper = [i["upper"] for i in intervals]
            ax.fill_between(f_x, lower, upper, alpha=0.15, color=colors[1])
        ax.set_title("(c) Prediction Intervals (95%)", fontsize=11, loc="left"); ax.set_xlabel("Period")
        despine(ax); ax.grid(alpha=0.2, linestyle=":")

        # (d) Metrics Table
        ax = axes[1, 1]
        ax.axis("off")
        mape_val = np.mean(np.abs((np.array(actual)-np.array(fitted))/np.maximum(np.array(actual),1e-10)))*100 if actual else 0
        metrics = [
            ["Metric", "Value"],
            ["MAPE", f"{mape_val:.2f}%"],
            ["Forecast (t+1)", f"{forecast[0]:.2f}" if forecast else "-"],
            ["Forecast (t+2)", f"{forecast[1]:.2f}" if len(forecast)>1 else "-"],
            ["Forecast (t+3)", f"{forecast[2]:.2f}" if len(forecast)>2 else "-"],
            ["Growth Rate", f"{((forecast[-1]/forecast[0])**(1/3)-1)*100:.1f}%" if len(forecast)>=3 else "-"],
        ]
        table = ax.table(cellText=metrics, cellLoc="center", loc="center",
                         colWidths=[0.4, 0.3])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        for i in range(len(metrics)):
            for j in range(2):
                cell = table[i, j]
                cell.set_edgecolor("#cccccc")
                if i == 0:
                    cell.set_facecolor("#f0f0f0")
                    cell.get_text().set_fontweight("bold")
        ax.set_title("(d) Key Metrics", fontsize=11, loc="left")

        fig.tight_layout()
        if output_path:
            from pathlib import Path; Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def evaluation_suite(self, scores: list, labels: list, weights: dict,
                         output_path: str = "") -> str:
        """1×3 评价三联组: (a)得分 (b)权重饼图 (c)排名棒棒糖"""
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        colors = get_colors(len(labels)) if len(labels) <= 10 else get_colors(10)

        # (a) Score bar chart
        ax = axes[0]
        ax.barh(range(len(labels)), [float(s) for s in scores], color=colors[:len(labels)],
                height=0.6, edgecolor="white")
        ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels)
        for i, (s, bar) in enumerate(zip(scores, ax.patches)):
            ax.text(bar.get_width() + max(scores)*0.01, bar.get_y()+bar.get_height()/2,
                    f"{float(s):.3f}", va="center", fontsize=8)
        ax.set_title("(a) Scores", fontsize=11, loc="left"); despine(ax); ax.grid(alpha=0.2, linestyle=":")

        # (b) Weight pie chart
        ax = axes[1]
        w_names = list(weights.keys())[:8]
        w_vals = [float(weights[k]) for k in w_names]
        wedges, texts, autotexts = ax.pie(w_vals, labels=w_names, autopct="%1.1f%%",
                                           colors=colors[:len(w_vals)], startangle=90,
                                           textprops={"fontsize": 7})
        ax.set_title("(b) Weights", fontsize=11, loc="left")

        # (c) Lollipop chart (ranked scores)
        ax = axes[2]
        order = np.argsort([-float(s) for s in scores])
        ordered_scores = [float(scores[i]) for i in order]
        ordered_labels = [labels[i] for i in order]
        ax.stem(range(len(ordered_scores)), ordered_scores, linefmt=colors[0], markerfmt="o", basefmt=" ")
        ax.scatter(range(len(ordered_scores)), ordered_scores, c=colors[:len(ordered_scores)],
                   s=80, zorder=5, edgecolors="white")
        for i, (lbl, s) in enumerate(zip(ordered_labels, ordered_scores)):
            ax.annotate(lbl, (i, s), textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=7)
        ax.set_title("(c) Ranking", fontsize=11, loc="left"); despine(ax); ax.grid(alpha=0.2, axis="y", linestyle=":")

        fig.tight_layout()
        if output_path:
            from pathlib import Path; Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def optimization_suite(self, costs: list, benefits: list, labels: list,
                           selection: list, budget: float, output_path: str = "") -> str:
        """优化三连图: (a)成本柱 (b)收益柱 (c)性价比散点 — 选中项高亮"""
        fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
        colors = get_colors(2)

        n = len(labels)
        sel_mask = [i for i, s in enumerate(selection) if s > 0.5]
        nsel_mask = [i for i in range(n) if i not in sel_mask]
        bar_colors = [colors[0] if selection[i] > 0.5 else "#cccccc" for i in range(n)]

        # (a) Costs
        ax = axes[0]
        ax.bar(range(n), costs, color=bar_colors, width=0.6, edgecolor="white")
        ax.axhline(budget, color="red", linestyle="--", alpha=0.5, label=f"Budget={budget:.0f}")
        ax.set_xticks(range(n)); ax.set_xticklabels(labels, rotation=30 if n > 5 else 0, fontsize=8)
        ax.set_title("(a) Costs", fontsize=11, loc="left"); ax.legend(fontsize=8, frameon=False)
        despine(ax); ax.grid(alpha=0.2, axis="y", linestyle=":")

        # (b) Benefits
        ax = axes[1]
        ax.bar(range(n), benefits, color=bar_colors, width=0.6, edgecolor="white")
        ax.set_xticks(range(n)); ax.set_xticklabels(labels, rotation=30 if n > 5 else 0, fontsize=8)
        ax.set_title("(b) Benefits", fontsize=11, loc="left")
        despine(ax); ax.grid(alpha=0.2, axis="y", linestyle=":")

        # (c) Cost-Benefit scatter
        ax = axes[2]
        ratios = [benefits[i] / max(costs[i], 1e-6) for i in range(n)]
        ax.scatter([costs[i] for i in nsel_mask], [benefits[i] for i in nsel_mask],
                   c="#cccccc", alpha=0.4, s=60, edgecolors="white")
        ax.scatter([costs[i] for i in sel_mask], [benefits[i] for i in sel_mask],
                   c=colors[0], s=100, edgecolors="white", zorder=5)
        for i in sel_mask:
            ax.annotate(labels[i], (costs[i], benefits[i]), textcoords="offset points",
                        xytext=(6, 3), fontsize=8, fontweight="bold")
        ax.axhline(np.mean(benefits), color="gray", linestyle=":", alpha=0.5, label="Avg Benefit")
        ax.axvline(np.mean(costs), color="gray", linestyle=":", alpha=0.5, label="Avg Cost")
        ax.set_xlabel("Cost"); ax.set_ylabel("Benefit")
        ax.set_title("(c) Cost-Benefit Analysis", fontsize=11, loc="left")
        ax.legend(fontsize=7, frameon=False); despine(ax); ax.grid(alpha=0.2, linestyle=":")

        fig.tight_layout()
        if output_path:
            from pathlib import Path; Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return output_path
