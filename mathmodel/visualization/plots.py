"""国赛论文图表生成器 — 对标优秀论文标准

所有图表默认: 无标题(标题由论文caption承担)、despine、150dpi、彩色、中文字体
"""

from pathlib import Path
from typing import Optional, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mathmodel.visualization.styles import despine, get_colors


class Plotter:
    """国赛论文图表生成器"""

    def __init__(self, language: str = "zh"):
        self.language = language
        self._figures = []

    def _fig(self, figsize=(6, 4)):
        fig, ax = plt.subplots(figsize=figsize)
        self._figures.append(fig)
        despine(ax)
        return fig, ax

    def _multi_fig(self, rows, cols, figsize=None):
        w, h = figsize or (5*cols, 4*rows)
        fig, axes = plt.subplots(rows, cols, figsize=(w, h))
        self._figures.append(fig)
        for ax in np.atleast_1d(axes).flat:
            despine(ax)
        return fig, axes

    # ==================================================================
    # 柱状图 (国赛最常用)
    # ==================================================================

    def bar(self, x, y, xlabel="", ylabel="", labels=None, horizontal=False,
            color=None, value_format=".2f"):
        """柱状图 — 多彩 + 数值标签"""
        fig, ax = self._fig()
        n = len(y)
        colors = color or get_colors(n)

        if horizontal:
            bars = ax.barh(range(n), y, color=colors[:n], height=0.65, edgecolor="white", linewidth=0.5)
            ax.set_yticks(range(n))
            ax.set_yticklabels(labels or x, fontsize=9)
            for i, (v, bar) in enumerate(zip(y, bars)):
                ax.text(bar.get_width() + max(y)*0.01, bar.get_y() + bar.get_height()/2,
                        f"{v:{value_format}}", va="center", fontsize=8)
        else:
            bars = ax.bar(range(n), y, color=colors[:n], width=0.65, edgecolor="white", linewidth=0.5)
            ax.set_xticks(range(n))
            ax.set_xticklabels(labels or x, fontsize=9, rotation=30 if n > 6 else 0)
            for bar, v in zip(bars, y):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(y)*0.02,
                        f"{v:{value_format}}", ha="center", va="bottom", fontsize=8)

        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.grid(axis="y", alpha=0.2, linestyle=":")
        fig.tight_layout()
        return fig, ax

    def grouped_bar(self, groups, values_dict, xlabel="", ylabel=""):
        """分组柱状图 — 多组对比"""
        n_groups = len(groups)
        n_bars = len(values_dict)
        fig, ax = self._fig(figsize=(max(8, n_groups*1.2), 5))
        colors = get_colors(n_bars)
        width = 0.8 / n_bars
        x = np.arange(n_groups)

        for i, (name, vals) in enumerate(values_dict.items()):
            offset = (i - n_bars/2 + 0.5) * width
            ax.bar(x + offset, vals, width*0.85, label=name, color=colors[i],
                   edgecolor="white", linewidth=0.5)

        ax.set_xticks(x)
        ax.set_xticklabels(groups, fontsize=9, rotation=30 if n_groups > 5 else 0)
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.legend(fontsize=9, frameon=False)
        ax.grid(axis="y", alpha=0.2, linestyle=":")
        fig.tight_layout()
        return fig, ax

    # ==================================================================
    # 折线图 (预测、趋势)
    # ==================================================================

    def line(self, x, y, xlabel="", ylabel="", label="", color=None, markers=True,
             fill_alpha=0.1, linewidth=2.0):
        """折线图 — 带标记点 + 半透明填充"""
        fig, ax = self._fig()
        c = color or get_colors(1)[0]
        marker = "o" if markers and len(y) < 30 else None
        ax.plot(x, y, color=c, linewidth=linewidth, marker=marker, markersize=5,
                markerfacecolor="white", markeredgewidth=1.5, label=label, zorder=3)
        if fill_alpha:
            ax.fill_between(range(len(y)) if isinstance(x, list) else x, y, alpha=fill_alpha,
                            color=c)
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        if label:
            ax.legend(fontsize=9, frameon=False)
        ax.grid(alpha=0.2, linestyle=":")
        fig.tight_layout()
        return fig, ax

    def forecast_plot(self, actual, fitted, forecast, xlabel="", ylabel=""):
        """预测对比图 — 实际值(散点) + 拟合线 + 预测延伸(虚线)"""
        fig, ax = self._fig(figsize=(7, 4.5))
        n_fit = len(fitted)
        n_all = n_fit + len(forecast)
        colors = get_colors(3)

        x_all = list(range(n_all))
        ax.scatter(range(n_fit), actual, color=colors[0], s=50, zorder=5, label="Actual", edgecolors="white")
        ax.plot(range(n_fit), fitted, color=colors[1], linewidth=2, label="Fitted", zorder=3)
        ax.plot(range(n_fit-1, n_all), fitted[-1:] + forecast, color=colors[2],
                linewidth=2, linestyle="--", marker="s", markersize=5,
                markerfacecolor="white", label="Forecast", zorder=3)
        ax.axvline(x=n_fit-0.5, color="gray", linestyle=":", alpha=0.5, linewidth=1)
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.legend(fontsize=9, frameon=False)
        ax.grid(alpha=0.2, linestyle=":")
        fig.tight_layout()
        return fig, ax

    # ==================================================================
    # 散点图 (相关性、分布)
    # ==================================================================

    def scatter(self, x, y, xlabel="", ylabel="", color=None, alpha=0.6,
                fit_line=False, s=30):
        """散点图 — 可选拟合线"""
        fig, ax = self._fig()
        c = color or get_colors(1)[0]
        ax.scatter(x, y, c=c, alpha=alpha, s=s, edgecolors="white", linewidth=0.3, zorder=3)

        if fit_line and len(x) > 2:
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            x_line = np.linspace(min(x), max(x), 100)
            ax.plot(x_line, p(x_line), "--", color="gray", linewidth=1.5, alpha=0.7,
                    label=f"y={z[0]:.3f}x+{z[1]:.3f}")
            ax.legend(fontsize=8, frameon=False)

        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.grid(alpha=0.2, linestyle=":")
        fig.tight_layout()
        return fig, ax

    # ==================================================================
    # 热力图 (相关性矩阵)
    # ==================================================================

    def heatmap(self, matrix, labels, cmap="RdBu_r", vmin=-1, vmax=1, annot=True):
        """相关热力图 — RdBu_r 配色"""
        import numpy as np
        # 干掉 NaN/Inf 防止 imshow 崩溃
        matrix = np.nan_to_num(np.array(matrix), nan=0.0, posinf=1.0, neginf=-1.0)
        n = len(labels)
        fig, ax = self._fig(figsize=(min(n*1.1 + 1, 16), min(n*0.9 + 0.5, 12)))
        im = ax.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(labels, fontsize=8)
        cbar = plt.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
        cbar.ax.tick_params(labelsize=7)

        if annot and n <= 15:  # 超过15×15不标注数字，太密
            for i in range(n):
                for j in range(n):
                    val = float(matrix[i, j])
                    if np.isnan(val) or np.isinf(val):
                        val = 0.0
                    color = "white" if abs(val) > 0.5 else "black"
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7, color=color)

        fig.tight_layout()
        return fig, ax

    # ==================================================================
    # 箱线图
    # ==================================================================

    def boxplot(self, data_dict, xlabel="", ylabel=""):
        """多组箱线图"""
        fig, ax = self._fig(figsize=(len(data_dict)*1.5+1, 4.5))
        colors = get_colors(len(data_dict))
        bp = ax.boxplot(data_dict.values(), patch_artist=True, widths=0.5,
                        medianprops={"color": "black", "linewidth": 1.2})

        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
            patch.set_alpha(0.7)

        ax.set_xticklabels(data_dict.keys(), fontsize=9)
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.grid(axis="y", alpha=0.2, linestyle=":")
        fig.tight_layout()
        return fig, ax

    # ==================================================================
    # 多面板组合图 (国赛高端用法)
    # ==================================================================

    def multi_panel(self, panels: list[dict], rows: int, cols: int,
                    figsize=None, suptitle=None):
        """多面板组合图

        panels: [{"type":"bar","x":...,"y":...,"title":"(a) xxx"}, ...]
        """
        fig, axes = self._multi_fig(rows, cols, figsize)
        flat_axes = np.atleast_1d(axes).flat
        colors = get_colors(10)

        for i, panel in enumerate(panels):
            if i >= len(flat_axes):
                break
            ax = flat_axes[i]
            ptype = panel.get("type", "bar")
            data = panel.get("data", {})
            label = panel.get("label", f"({chr(97+i)})")

            if ptype == "bar":
                x = panel.get("x", [])
                y = panel.get("y", [])
                ax.bar(range(len(y)), y, color=colors[:len(y)], width=0.6,
                       edgecolor="white", linewidth=0.5)
                ax.set_xticks(range(len(y)))
                ax.set_xticklabels(x, fontsize=8, rotation=30 if len(x) > 5 else 0)
            elif ptype == "line":
                x = panel.get("x", range(len(panel.get("y", []))))
                ax.plot(x, panel.get("y", []), color=colors[0], linewidth=2,
                        marker="o", markersize=4, markerfacecolor="white")
            elif ptype == "scatter":
                ax.scatter(panel.get("x", []), panel.get("y", []),
                          c=colors[0], alpha=0.6, s=20, edgecolors="white", linewidth=0.3)
            elif ptype == "heatmap":
                data = panel.get("matrix", [[]])
                im = ax.imshow(data, cmap="RdBu_r", aspect="auto")
                plt.colorbar(im, ax=ax, shrink=0.8)

            ax.set_xlabel(panel.get("xlabel", ""), fontsize=9)
            ax.set_ylabel(panel.get("ylabel", ""), fontsize=9)
            ax.set_title(label, fontsize=10, fontweight="bold", loc="left")
            ax.grid(alpha=0.2, linestyle=":")

        if suptitle:
            fig.suptitle(suptitle, fontsize=12, fontweight="bold", y=1.01)

        fig.tight_layout()
        return fig, axes

    # ==================================================================
    # Save & Cleanup
    # ==================================================================

    def save(self, fig, path, dpi=300):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(path), dpi=dpi, bbox_inches="tight", facecolor="white", edgecolor="none")
        return path

    def close_all(self):
        for fig in self._figures:
            plt.close(fig)
        self._figures.clear()
