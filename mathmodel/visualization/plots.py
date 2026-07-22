"""标准图表生成器。

提供竞赛论文常用的图表类型：折线图、柱状图、散点图、
箱线图、饼图、误差棒图等。
"""

from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd

from mathmodel.visualization.styles import set_style


class Plotter:
    """标准图表生成器。

    所有方法均返回 (fig, ax) 元组，并支持直接保存为 PDF/SVG/PNG。

    Usage::

        plotter = Plotter(language="zh")
        fig, ax = plotter.line(x, y, xlabel="时间", ylabel="值", title="趋势图")
        plotter.save(fig, "output/trend.pdf")
    """

    def __init__(self, language: str = "zh", palette: str = "default"):
        set_style(language, palette)
        self.language = language
        self.palette = palette
        self._figures: list = []

    def _fig(self, figsize: tuple = (8, 5)):
        """创建 figure 并注册。"""
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=figsize)
        self._figures.append(fig)
        return fig, ax

    # =====================================================================
    # 折线图
    # =====================================================================

    def line(
        self,
        x: Union[list, np.ndarray],
        y: Union[list, np.ndarray, dict],
        xlabel: str = "",
        ylabel: str = "",
        title: str = "",
        labels: Optional[list[str]] = None,
        markers: bool = True,
    ):
        """折线图。

        Args:
            x: x 轴数据
            y: y 轴数据，若为 dict 则每个 key 画一条线
            labels: 图例标签
            markers: 是否显示数据点标记
        """
        fig, ax = self._fig()

        if isinstance(y, dict):
            for i, (name, values) in enumerate(y.items()):
                marker = "o" if markers else None
                ax.plot(x, values, marker=marker, linewidth=1.5, label=name)
        else:
            ax.plot(x, y, marker="o" if markers else None, linewidth=1.5,
                    label=labels[0] if labels else None)

        self._decorate(ax, xlabel, ylabel, title)
        if labels or isinstance(y, dict):
            ax.legend()
        return fig, ax

    # =====================================================================
    # 柱状图
    # =====================================================================

    def bar(
        self,
        x: Union[list, np.ndarray],
        y: Union[list, np.ndarray],
        xlabel: str = "",
        ylabel: str = "",
        title: str = "",
        labels: Optional[list[str]] = None,
        horizontal: bool = False,
    ):
        """柱状图。"""
        fig, ax = self._fig()

        if horizontal:
            ax.barh(x, y)
        else:
            ax.bar(x, y)

        # 数值标签
        for i, v in enumerate(y):
            if horizontal:
                ax.text(v, i, f" {v:.2f}", va="center", fontsize=8)
            else:
                ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)

        if labels:
            if horizontal:
                ax.set_yticks(range(len(labels)))
                ax.set_yticklabels(labels)
            else:
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=30)

        self._decorate(ax, xlabel, ylabel, title)
        return fig, ax

    # =====================================================================
    # 散点图
    # =====================================================================

    def scatter(
        self,
        x: Union[list, np.ndarray],
        y: Union[list, np.ndarray],
        xlabel: str = "",
        ylabel: str = "",
        title: str = "",
        color: Optional[Union[list, np.ndarray]] = None,
        alpha: float = 0.7,
        trend_line: bool = False,
    ):
        """散点图（可选趋势线）。"""
        fig, ax = self._fig()

        sc = ax.scatter(x, y, c=color, alpha=alpha, s=30, cmap="viridis")
        if color is not None:
            fig.colorbar(sc, ax=ax)

        if trend_line:
            x_arr = np.array(x, dtype=float)
            y_arr = np.array(y, dtype=float)
            coeffs = np.polyfit(x_arr, y_arr, 1)
            x_line = np.linspace(x_arr.min(), x_arr.max(), 100)
            ax.plot(x_line, np.polyval(coeffs, x_line), "r--", linewidth=1, label="趋势线")
            ax.legend()

        self._decorate(ax, xlabel, ylabel, title)
        return fig, ax

    # =====================================================================
    # 箱线图
    # =====================================================================

    def boxplot(
        self,
        data: Union[list[np.ndarray], dict],
        xlabel: str = "",
        ylabel: str = "",
        title: str = "",
        labels: Optional[list[str]] = None,
    ):
        """箱线图。"""
        fig, ax = self._fig()

        if isinstance(data, dict):
            labels = list(data.keys())
            data = list(data.values())

        bp = ax.boxplot(data, labels=labels, patch_artist=True)
        for patch in bp["boxes"]:
            patch.set_alpha(0.6)

        self._decorate(ax, xlabel, ylabel, title)
        return fig, ax

    # =====================================================================
    # 饼图
    # =====================================================================

    def pie(
        self,
        values: Union[list, np.ndarray],
        labels: Optional[list[str]] = None,
        title: str = "",
        pct_threshold: float = 3.0,
    ):
        """饼图。"""
        fig, ax = self._fig(figsize=(7, 7))

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct=lambda p: f"{p:.1f}%" if p > pct_threshold else "",
            startangle=90,
        )
        ax.set_title(title, fontsize=12, fontweight="bold")

        return fig, ax

    # =====================================================================
    # 误差棒图
    # =====================================================================

    def errorbar(
        self,
        x: Union[list, np.ndarray],
        y: Union[list, np.ndarray],
        yerr: Union[list, np.ndarray],
        xlabel: str = "",
        ylabel: str = "",
        title: str = "",
    ):
        """误差棒图。"""
        fig, ax = self._fig()
        ax.errorbar(x, y, yerr=yerr, fmt="o-", capsize=5, capthick=1.5, linewidth=1.5)
        self._decorate(ax, xlabel, ylabel, title)
        return fig, ax

    # =====================================================================
    # 多子图
    # =====================================================================

    def subplots_grid(
        self,
        nrows: int = 1,
        ncols: int = 2,
        figsize: tuple = (12, 5),
    ):
        """创建多子图网格。"""
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
        self._figures.append(fig)
        return fig, axes

    # =====================================================================
    # 保存 & 清理
    # =====================================================================

    def save(self, fig, path: str | Path, dpi: int = 300) -> Path:
        """保存图表为文件。"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(path), dpi=dpi, bbox_inches="tight")
        return path

    def save_all(self, output_dir: str | Path) -> list[Path]:
        """保存所有图表。"""
        out = Path(output_dir)
        paths = []
        for i, fig in enumerate(self._figures):
            p = out / f"figure_{i+1:03d}.pdf"
            paths.append(self.save(fig, p))
        return paths

    def close_all(self) -> None:
        """关闭所有图表。"""
        import matplotlib.pyplot as plt
        for _ in self._figures:
            plt.close()
        self._figures.clear()

    # =====================================================================
    # 装饰
    # =====================================================================

    def _decorate(self, ax, xlabel: str, ylabel: str, title: str) -> None:
        """统一装饰 axes。"""
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title, fontsize=12, fontweight="bold")
        ax.tick_params(direction="in")
