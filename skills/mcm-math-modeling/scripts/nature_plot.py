r"""
nature_plot.py — Nature 风格 matplotlib 绘图模板（美赛论文插图专用）

用法（在任意绘图脚本中）：
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from nature_plot import apply_nature_style, new_figure, save_figure, NPG_COLORS

    apply_nature_style()                       # 一键应用 Nature 风格
    fig, ax = new_figure(size="single")        # single/onehalf/double
    ax.plot(x, y, color=NPG_COLORS[0], label="Model")
    ax.set_xlabel("Time (day)")
    ax.set_ylabel("Population")
    ax.legend(frameon=False)
    save_figure(fig, "fig1")                   # 输出 fig1.pdf + fig1.png

直接运行本文件可生成一组示例图（输出到 ./nature_demo/）。
"""

import os
from pathlib import Path
import warnings
from collections.abc import Sequence
from typing import Optional, Union

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import matplotlib.patches as mpatches

# scipy 是可选依赖，没有时回退到简单实现
try:
    from scipy import stats
    from scipy.interpolate import UnivariateSpline
    HAS_SCIPY = True
except Exception:
    HAS_SCIPY = False

# ---------------------------------------------------------------------------
# 配色
# ---------------------------------------------------------------------------

# NPG (Nature Publishing Group) 主配色，按推荐使用顺序
NPG_COLORS = [
    "#E64B35",  # 红
    "#4DBBD5",  # 蓝
    "#00A087",  # 绿
    "#F39B7F",  # 橙
    "#3C5488",  # 深蓝
    "#8491B4",  # 灰蓝
    "#91D1C2",  # 青
    "#B09C85",  # 棕
]

# Okabe-Ito 色盲友好配色（备选）
OKABE_ITO = [
    "#E69F00", "#56B4E9", "#009E73", "#F0E442",
    "#0072B2", "#D55E00", "#CC79A7", "#999999",
]

NEAR_BLACK = "#1A1A1A"   # 文字/坐标轴用近黑

# 图幅尺寸（宽×高, mm）—— 对应 Nature 栏宽
FIG_SIZES = {
    "single":  (89, 62),     # 单栏
    "onehalf": (140, 92),    # 1.5 栏（美赛主结果图推荐）
    "double":  (183, 120),   # 全宽（多面板组合图推荐）
}

MM_PER_INCH = 25.4


# ---------------------------------------------------------------------------
# 样式
# ---------------------------------------------------------------------------

def apply_nature_style():
    """一键应用 Nature 出版风格 rcParams。"""
    plt.rcParams.update({
        # 字体
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 9,
        "mathtext.fontset": "stixsans",
        # 坐标轴
        "axes.linewidth": 0.9,
        "axes.edgecolor": NEAR_BLACK,
        "axes.labelcolor": NEAR_BLACK,
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        # 刻度：朝外，Nature 标志性细节
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "xtick.major.width": 0.9,
        "ytick.major.width": 0.9,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "xtick.color": NEAR_BLACK,
        "ytick.color": NEAR_BLACK,
        # 图例：无边框
        "legend.frameon": False,
        "legend.fontsize": 8.5,
        # 线条
        "lines.linewidth": 1.8,
        "lines.markersize": 5,
        # 文本
        "text.color": NEAR_BLACK,
        # 导出
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42,      # TrueType 嵌入，PDF 文字可编辑
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def new_figure(size="onehalf", nrows=1, ncols=1, sharex=False, sharey=False,
               extra_height=1.0):
    """按 Nature 栏宽创建图。extra_height 是相对基础高度的倍数。"""
    w_mm, h_mm = FIG_SIZES[size]
    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(w_mm / MM_PER_INCH, (h_mm * extra_height) / MM_PER_INCH),
        sharex=sharex, sharey=sharey,
        constrained_layout=True,
    )
    return fig, axes


def panel_label(ax, label, x=-0.18, y=1.05):
    """在子图左上角添加 (a)(b)(c) 面板标签，加粗。"""
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=11, fontweight="bold", va="bottom", ha="left",
            color=NEAR_BLACK)


def save_figure(fig, name, outdir="."):
    """同时导出矢量 PDF 与 300dpi PNG。name 不含扩展名。"""
    os.makedirs(outdir, exist_ok=True)
    pdf_path = os.path.join(outdir, name + ".pdf")
    png_path = os.path.join(outdir, name + ".png")
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print(f"saved: {pdf_path}\nsaved: {png_path}")
    return pdf_path, png_path


def despine(ax, keep=("left", "bottom")):
    """移除多余脊柱。默认已去 top/right，可进一步清理。"""
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)


# ---------------------------------------------------------------------------
# 通用辅助
# ---------------------------------------------------------------------------

def plot_with_band(ax, x, y_mean, y_std, color, label=None, n_sigma=1.96):
    """均值曲线 + 半透明置信带（Nature 常见呈现方式）。"""
    ax.plot(x, y_mean, color=color, lw=1.8, label=label)
    ax.fill_between(x, y_mean - n_sigma * y_std, y_mean + n_sigma * y_std,
                    color=color, alpha=0.2, linewidth=0)


def _cycle_colors(n, palette=NPG_COLORS):
    """循环取色，返回 n 个颜色。"""
    return [palette[i % len(palette)] for i in range(n)]


def _nice_ticks(ax, axis="x", n=5):
    """简化版自动 nice ticks，避免 matplotlib 默认过密。"""
    if axis == "x":
        lo, hi = ax.get_xlim()
        ax.set_xticks(np.linspace(lo, hi, n))
    else:
        lo, hi = ax.get_ylim()
        ax.set_yticks(np.linspace(lo, hi, n))


def add_significance_bracket(ax, x1, x2, y, pval, h=0.02, fs=7.5):
    """在柱状/箱线图上添加显著性桥。"""
    stars = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "n.s."
    dh = (ax.get_ylim()[1] - ax.get_ylim()[0]) * h
    ax.plot([x1, x1, x2, x2], [y, y + dh, y + dh, y], color=NEAR_BLACK, lw=0.8)
    ax.text((x1 + x2) / 2, y + dh * 1.15, stars, ha="center", va="bottom", fontsize=fs)


# ---------------------------------------------------------------------------
# 1) 单/分组/堆叠柱状图
# ---------------------------------------------------------------------------

def bar_chart(ax, categories, values, color=None, horizontal=False,
              annotate=True, ylabel="", xlabel=""):
    """简洁柱状图。适合类别对比。"""
    color = color or NPG_COLORS[0]
    n = len(categories)
    if horizontal:
        bars = ax.barh(np.arange(n), values, color=color, height=0.6)
        ax.set_yticks(np.arange(n))
        ax.set_yticklabels(categories)
        ax.set_xlabel(ylabel or "Value")
    else:
        bars = ax.bar(np.arange(n), values, color=color, width=0.6)
        ax.set_xticks(np.arange(n))
        ax.set_xticklabels(categories, rotation=30, ha="right")
        ax.set_ylabel(ylabel or "Value")
    ax.set_xlabel(xlabel)
    if annotate:
        for bar, val in zip(bars, values):
            if horizontal:
                ax.text(val + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                        f"{val:.2g}", va="center", ha="left", fontsize=8)
            else:
                ax.text(bar.get_x() + bar.get_width() / 2, val + max(values) * 0.01,
                        f"{val:.2g}", ha="center", va="bottom", fontsize=8)


def grouped_bar(ax, categories, groups, values, colors=None,
                ylabel="Value", xlabel=""):
    """分组柱状图。values: shape (n_groups, n_categories)。"""
    values = np.asarray(values)
    ng, nc = values.shape
    x = np.arange(nc)
    width = 0.8 / ng
    colors = colors or _cycle_colors(ng)
    for i, (g, row) in enumerate(zip(groups, values)):
        ax.bar(x + (i - (ng - 1) / 2) * width, row, width,
               label=g, color=colors[i], edgecolor="white", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.legend()


def stacked_bar(ax, categories, groups, values, colors=None,
                 ylabel="Value", xlabel=""):
    """堆叠柱状图。values: shape (n_groups, n_categories)。"""
    values = np.asarray(values, dtype=float)
    ng, nc = values.shape
    x = np.arange(nc)
    colors = colors or _cycle_colors(ng)
    bottom = np.zeros(nc)
    for i, (g, row) in enumerate(zip(groups, values)):
        ax.bar(x, row, bottom=bottom, label=g, color=colors[i],
               width=0.6, edgecolor="white", linewidth=0.5)
        bottom += row
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.legend(reverse=True)


# ---------------------------------------------------------------------------
# 2) 箱线 + strip / 小提琴
# ---------------------------------------------------------------------------

def box_strip_plot(ax, data, labels, colors=None, ylabel="Value",
                   show_mean=True):
    """箱线图叠加散点（显示每个数据点）。n<10 时强烈建议用此图而非纯均值柱。"""
    data = [np.asarray(d) for d in data]
    n = len(data)
    colors = colors or _cycle_colors(n)
    positions = np.arange(1, n + 1)
    bp = ax.boxplot(data, positions=positions, widths=0.35, patch_artist=True,
                    showmeans=show_mean, showfliers=False,
                    meanprops=dict(marker="D", markerfacecolor=NEAR_BLACK,
                                   markeredgecolor=NEAR_BLACK, markersize=5))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)
        patch.set_edgecolor(color)
        patch.set_linewidth(1.2)
    for whisker in bp["whiskers"]:
        whisker.set(color=NEAR_BLACK, linewidth=0.9)
    for cap in bp["caps"]:
        cap.set(color=NEAR_BLACK, linewidth=0.9)
    for median in bp["medians"]:
        median.set(color=NEAR_BLACK, linewidth=1.5)
    rng = np.random.default_rng(0)
    for i, (d, c) in enumerate(zip(data, colors)):
        jitter = rng.normal(0, 0.04, size=len(d))
        ax.scatter(positions[i] + jitter, d, s=16, c=c, zorder=3,
                   edgecolors="white", linewidth=0.4, alpha=0.9)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel(ylabel)


def violin_plot(ax, data, labels, colors=None, ylabel="Value",
                show_box=False):
    """小提琴图，可选叠加箱线。适合展示分布形态。"""
    n = len(data)
    colors = colors or _cycle_colors(n)
    positions = np.arange(1, n + 1)
    parts = ax.violinplot(data, positions=positions, widths=0.7,
                          showmeans=False, showmedians=False, showextrema=False)
    for pc, color in zip(parts["bodies"], colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.4)
        pc.set_edgecolor(color)
        pc.set_linewidth(1.2)
    if show_box:
        bp = ax.boxplot(data, positions=positions, widths=0.15, showcaps=False,
                        showfliers=False, medianprops=dict(color=NEAR_BLACK, lw=1.5))
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel(ylabel)


def paired_raincloud(ax, before, after, group_labels=("Before", "After"),
                     ylabel="Value"):
    """配对前后对比的云雨图：半边小提琴 + 箱线 + 抖动点 + 连线。"""
    before = np.asarray(before)
    after = np.asarray(after)
    positions = [1, 2]
    data = [before, after]
    colors = [NPG_COLORS[1], NPG_COLORS[0]]
    # 半边小提琴
    for pos, d, c in zip(positions, data, colors):
        parts = ax.violinplot(d, positions=[pos], widths=0.35, showextrema=False)
        for pc in parts["bodies"]:
            pc.set_facecolor(c)
            pc.set_alpha(0.35)
            # 切成半边：只保留一侧
            paths = pc.get_paths()
            for path in paths:
                vertices = path.vertices
                vertices[:, 0] = pos + (vertices[:, 0] - pos) * 0.5
    # 箱线
    bp = ax.boxplot(data, positions=positions, widths=0.12, showcaps=False,
                    showfliers=False, medianprops=dict(color=NEAR_BLACK, lw=1.5))
    for patch, c in zip(bp["boxes"], colors):
        patch.set_color(c)
    # 抖动点 + 配对连线
    rng = np.random.default_rng(2)
    offsets = [-0.12, 0.12]
    for i, (d, off, c) in enumerate(zip(data, offsets, colors)):
        x = np.full(len(d), positions[i]) + rng.normal(off, 0.015, size=len(d))
        ax.scatter(x, d, s=18, c=c, zorder=4, edgecolors="white", linewidth=0.4)
    # 连线
    for b, a in zip(before, after):
        ax.plot(positions, [b, a], color=NEAR_BLACK, lw=0.3, alpha=0.25, zorder=1)
    ax.set_xticks(positions)
    ax.set_xticklabels(group_labels)
    ax.set_ylabel(ylabel)
    ax.set_xlim(0.4, 2.6)


# ---------------------------------------------------------------------------
# 3) 直方图 + KDE
# ---------------------------------------------------------------------------

def hist_kde(ax, x, bins=20, color=None, xlabel="Value", ylabel="Density",
             rug=False):
    """带核密度估计的直方图。"""
    color = color or NPG_COLORS[0]
    ax.hist(x, bins=bins, density=True, color=color, alpha=0.35,
            edgecolor="white", linewidth=0.5)
    if HAS_SCIPY and len(x) > 3:
        kde = stats.gaussian_kde(x)
        xs = np.linspace(x.min(), x.max(), 200)
        ax.plot(xs, kde(xs), color=color, lw=1.8)
        ax.fill_between(xs, kde(xs), color=color, alpha=0.15)
    ax.axvline(np.median(x), color=NEAR_BLACK, lw=1.2, ls="--")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if rug:
        ax.scatter(x, np.full_like(x, -0.01 * ax.get_ylim()[1]),
                   s=10, color=color, alpha=0.5, clip_on=False)


def density_ridge(axs, data, labels, color=None):
    """山脊图（joyplot）：展示多组分布。data 为 list of arrays。
    注意：axs 应为一维子图数组，每个子图放一组分布，需外部安排好垂直堆叠。"""
    colors = color or _cycle_colors(len(data))
    offset = 0
    for ax, d, lab, c in zip(axs, data, labels, colors):
        if HAS_SCIPY:
            kde = stats.gaussian_kde(d)
            xs = np.linspace(d.min(), d.max(), 200)
            ys = kde(xs) + offset
            ax.fill_between(xs, offset, ys, color=c, alpha=0.35)
            ax.plot(xs, ys, color=c, lw=1.5)
        else:
            counts, edges = np.histogram(d, bins=20, density=True)
            xs = (edges[:-1] + edges[1:]) / 2
            ys = counts + offset
            ax.fill_between(xs, offset, ys, color=c, alpha=0.35)
        ax.text(d.min(), offset + (max(ys) - offset) * 0.5, lab,
                va="center", fontsize=8, color=c, fontweight="bold")
        ax.set_ylim(offset, offset + max(ys) * 1.3)
        ax.set_yticks([])
        despine(ax, keep=("bottom",))
    axs[-1].set_xlabel("Value")


# ---------------------------------------------------------------------------
# 4) 散点 + 回归
# ---------------------------------------------------------------------------

def scatter_with_fit(ax, x, y, xlabel="x", ylabel="y", color=None,
                     annotate_stats=True):
    """散点 + 线性拟合 + 置信带 + R²/p 标注。"""
    x = np.asarray(x)
    y = np.asarray(y)
    color = color or NPG_COLORS[1]
    ax.scatter(x, y, s=25, color=color, alpha=0.7, edgecolors="white", linewidth=0.5)
    if HAS_SCIPY:
        slope, intercept, r, p, se = stats.linregress(x, y)
        xs = np.linspace(x.min(), x.max(), 100)
        pred = slope * xs + intercept
        ax.plot(xs, pred, color=NPG_COLORS[0], lw=1.8,
                label=f"Fit: $y={slope:.2g}x{intercept:+.2g}$")
        # 简易置信带
        xmean = x.mean()
        ssx = ((x - xmean) ** 2).sum()
        n = len(x)
        sy = np.sqrt(((y - (slope * x + intercept)) ** 2).sum() / (n - 2))
        try:
            tval = stats.t.ppf(0.975, n - 2)
        except Exception:
            tval = 2.0
        band = se * np.sqrt(1 + 1 / n + (xs - xmean) ** 2 / ssx) * tval
        ax.fill_between(xs, pred - band, pred + band, color=NPG_COLORS[0], alpha=0.15)
        if annotate_stats:
            ax.text(0.05, 0.95, f"$R^2={r ** 2:.3f}$\n$p={p:.3f}$",
                    transform=ax.transAxes, va="top", fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor=NEAR_BLACK, linewidth=0.5, alpha=0.9))
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc="lower right")


# ---------------------------------------------------------------------------
# 5) 相关矩阵 / 混淆矩阵 / 热图
# ---------------------------------------------------------------------------

def correlation_heatmap(ax, corr, labels, cmap="RdBu_r", vmin=-1, vmax=1,
                        annotate=True):
    """相关矩阵热图。corr 为 square numpy array。"""
    im = ax.imshow(corr, cmap=cmap, vmin=vmin, vmax=vmax, aspect="equal")
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    if annotate:
        for i in range(len(labels)):
            for j in range(len(labels)):
                val = corr[i, j]
                txt_color = "white" if abs(val) > 0.6 else NEAR_BLACK
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=7.5, color=txt_color)
    return im


def confusion_matrix(ax, cm, labels, cmap="Blues", annotate=True):
    """混淆矩阵或一般分类计数矩阵。"""
    im = ax.imshow(cm, cmap=cmap, aspect="equal")
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    if annotate:
        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(j, i, f"{cm[i, j]:.0f}", ha="center", va="center",
                        fontsize=8, color="white" if cm[i, j] > cm.max() / 2 else NEAR_BLACK)
    cb = plt.colorbar(im, ax=ax, shrink=0.8)
    cb.outline.set_visible(False)
    return im


# ---------------------------------------------------------------------------
# 6) 雷达图（多指标评估，适合多模型/多方案对比）
# ---------------------------------------------------------------------------

def radar_chart(ax, categories, values, labels=None, colors=None,
                fill_alpha=0.18):
    """雷达/蜘蛛图。values shape (n_series, n_categories)。"""
    values = np.asarray(values)
    n = len(categories)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    colors = colors or _cycle_colors(values.shape[0])
    for row, lab, c in zip(values, labels or [f"S{i}" for i in range(len(values))], colors):
        row = np.concatenate([row, row[:1]])
        ax.plot(angles, row, color=c, lw=1.5, label=lab, marker="o", markersize=4)
        ax.fill(angles, row, color=c, alpha=fill_alpha)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))


# ---------------------------------------------------------------------------
# 7) 堆叠面积 / 桑基风格堆叠条
# ---------------------------------------------------------------------------

def stacked_area(ax, x, y_stack, labels, colors=None, xlabel="x",
                 ylabel="Value"):
    """堆叠面积图。y_stack shape (n_series, n_x)。"""
    y_stack = np.asarray(y_stack, dtype=float)
    colors = colors or _cycle_colors(y_stack.shape[0])
    ax.stackplot(x, *y_stack, labels=labels, colors=colors, alpha=0.8,
                 edgecolor="white", linewidth=0.5)
    ax.set_xlim(x.min(), x.max())
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(reverse=True, loc="upper left")


def sankey_style_flow(ax, sources, targets, values, label_map=None):
    """简化桑基风格流图：用左右条形 + 曲带表示 source→target 的流。
    sources/targets 为整数索引，values 为流量。适合展示状态转移/分配。"""
    left_nodes = sorted(set(sources))
    right_nodes = sorted(set(targets))
    left_pos = {n: i for i, n in enumerate(left_nodes)}
    right_pos = {n: i for i, n in enumerate(right_nodes)}
    left_counts = np.bincount(sources, weights=values)
    right_counts = np.bincount(targets, weights=values)
    # 归一化高度
    def norm(arr):
        s = arr.sum()
        return arr / s if s else arr
    lc = norm(left_counts)
    rc = norm(right_counts)
    y_left = np.cumsum(np.r_[0, lc])[:-1] + lc / 2
    y_right = np.cumsum(np.r_[0, rc])[:-1] + rc / 2
    # 画左右柱
    ax.barh(y_left, np.ones(len(left_nodes)) * 0.2, height=lc * 0.9,
            left=np.zeros(len(left_nodes)), color=NPG_COLORS[0], alpha=0.8)
    ax.barh(y_right, np.ones(len(right_nodes)) * 0.2, height=rc * 0.9,
            left=np.ones(len(right_nodes)), color=NPG_COLORS[1], alpha=0.8)
    # 流带（简化为透明度带）
    for s, t, v in zip(sources, targets, values):
        ax.fill_betweenx([y_left[left_pos[s]] - lc[s] * 0.4,
                           y_left[left_pos[s]] + lc[s] * 0.4],
                         0.2, 0.8, color=NPG_COLORS[0], alpha=0.1)
    ax.set_xlim(-0.2, 1.4)
    ax.set_ylim(-0.1, 1.1)
    ax.axis("off")
    ax.text(0.1, 1.05, "Source", ha="center", fontsize=9, fontweight="bold")
    ax.text(0.9, 1.05, "Target", ha="center", fontsize=9, fontweight="bold")


# ---------------------------------------------------------------------------
# 8) 相图 / 向量场
# ---------------------------------------------------------------------------

def phase_portrait(ax, fun, xlim=(-2, 2), ylim=(-2, 2), n=20,
                   xlabel="x", ylabel="y"):
    """二维动力系统相图：向量场 + 零斜线。fun(X, Y) -> (U, V)。"""
    x = np.linspace(*xlim, n)
    y = np.linspace(*ylim, n)
    X, Y = np.meshgrid(x, y)
    U, V = fun(X, Y)
    mag = np.sqrt(U ** 2 + V ** 2)
    ax.streamplot(X, Y, U, V, color=mag, cmap="viridis", density=1.2,
                  linewidth=0.8, arrowsize=1)
    ax.contour(X, Y, U, levels=[0], colors=NPG_COLORS[0], linewidths=1.2)
    ax.contour(X, Y, V, levels=[0], colors=NPG_COLORS[1], linewidths=1.2)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def quiver_field(ax, X, Y, U, V, xlabel="x", ylabel="y",
                 color=None):
    """箭头场。"""
    color = color or NPG_COLORS[0]
    ax.quiver(X, Y, U, V, color=color, scale=15, width=0.004)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


# ---------------------------------------------------------------------------
# 9) 3D 曲面 / 等高线（响应面）
# ---------------------------------------------------------------------------

def contour_surface(ax, x, y, Z, kind="contour", cmap="viridis",
                    xlabel="x", ylabel="y", zlabel="z"):
    """响应面。kind='contour'（推荐）或 'filled'。"""
    if kind == "contour":
        cs = ax.contour(x, y, Z, levels=10, colors=NEAR_BLACK, linewidths=0.8)
        ax.clabel(cs, inline=True, fontsize=7)
    elif kind == "filled":
        pc = ax.contourf(x, y, Z, levels=20, cmap=cmap)
        cb = plt.colorbar(pc, ax=ax, shrink=0.8)
        cb.set_label(zlabel)
        cb.outline.set_visible(False)
    else:
        raise ValueError("kind must be 'contour' or 'filled'")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def surface_3d(fig, x, y, Z, cmap="viridis", xlabel="x", ylabel="y", zlabel="z"):
    """3D 曲面图（慎用，Nature 以 2D 为主）。"""
    from mpl_toolkits.mplot3d import Axes3D
    X, Y = np.meshgrid(x, y)
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(X, Y, Z, cmap=cmap, edgecolor="none", alpha=0.9)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)
    fig.colorbar(surf, ax=ax, shrink=0.5)
    return ax


# ---------------------------------------------------------------------------
# 10) 时间线 / Gantt
# ---------------------------------------------------------------------------

def timeline(ax, tasks, starts, durations, colors=None, xlabel="Time"):
    """水平时间线/Gantt 图。tasks 为字符串列表，starts/durations 为数值数组。"""
    colors = colors or _cycle_colors(len(tasks))
    y = np.arange(len(tasks))
    ax.barh(y, durations, left=starts, color=colors, height=0.6,
            edgecolor="white", linewidth=0.5)
    for i, (s, d, task) in enumerate(zip(starts, durations, tasks)):
        ax.text(s + d / 2, i, task, ha="center", va="center",
                fontsize=7.5, color="white" if d > 0 else NEAR_BLACK)
    ax.set_yticks(y)
    ax.set_yticklabels(tasks)
    ax.set_xlabel(xlabel)
    ax.invert_yaxis()


# ---------------------------------------------------------------------------
# 11) 龙卷风 / 敏感性
# ---------------------------------------------------------------------------

def tornado_plot(ax, params, effects, base=0.0):
    """敏感性蜘蛛图（tornado plot）：横向条形按影响从大到小排序。"""
    order = np.argsort(np.abs(effects))
    params = [params[i] for i in order]
    effects = np.asarray(effects)[order]
    colors = [NPG_COLORS[0] if e > 0 else NPG_COLORS[1] for e in effects]
    ax.barh(params, effects, color=colors, height=0.6, edgecolor="none")
    ax.axvline(base, color=NEAR_BLACK, lw=0.9, ls="--")
    ax.set_xlabel("Change in output (%)")


# ---------------------------------------------------------------------------
# 12) 排序条形家族：棒棒糖 / 正负发散 / 点图
# ---------------------------------------------------------------------------

def lollipop_chart(ax, categories, values, color=None, horizontal=True,
                   xlabel="Value", ylabel="Value"):
    """棒棒糖图：细杆 + 端点圆点，比柱状轻，适合排名/单序列。"""
    color = color or NPG_COLORS[0]
    values = np.asarray(values, dtype=float)
    n = len(categories)
    if horizontal:
        y = np.arange(n)
        ax.hlines(y, 0, values, color=color, lw=1.4)
        ax.scatter(values, y, s=42, color=color, zorder=3,
                   edgecolors="white", linewidth=0.6)
        ax.set_yticks(y); ax.set_yticklabels(categories)
        ax.set_xlabel(xlabel); ax.margins(x=0.10)
    else:
        x = np.arange(n)
        ax.vlines(x, 0, values, color=color, lw=1.4)
        ax.scatter(x, values, s=42, color=color, zorder=3,
                   edgecolors="white", linewidth=0.6)
        ax.set_xticks(x); ax.set_xticklabels(categories, rotation=30, ha="right")
        ax.set_ylabel(ylabel); ax.margins(y=0.10)


def diverging_bar(ax, categories, values, pos_color=None, neg_color=None,
                  xlabel="Value"):
    """正负发散横向柱状图：正负两色，含数值标注。适合增减量对比。"""
    pos_color = pos_color or NPG_COLORS[0]
    neg_color = neg_color or NPG_COLORS[1]
    values = np.asarray(values, dtype=float)
    colors = [pos_color if v >= 0 else neg_color for v in values]
    y = np.arange(len(categories))
    ax.barh(y, values, color=colors, height=0.62)
    ax.axvline(0, color=NEAR_BLACK, lw=0.9)
    lo, hi = min(values.min(), 0), max(values.max(), 0)
    pad = (hi - lo) * 0.02 if hi > lo else 1.0
    for yi, v in zip(y, values):
        ax.text(v + (pad if v >= 0 else -pad), yi, f"{v:+.1f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=7.5)
    ax.set_yticks(y); ax.set_yticklabels(categories); ax.set_xlabel(xlabel)
    ax.margins(x=0.14)


def dot_plot(ax, categories, values, color=None, xlabel="Value"):
    """点图（Cleveland dot plot）：按值排序，适合多国/多方案指标对比。"""
    color = color or NPG_COLORS[4]
    order = np.argsort(values)
    cats = [categories[i] for i in order]
    vals = np.asarray(values, dtype=float)[order]
    y = np.arange(len(cats))
    ax.hlines(y, 0, vals, color="#CCCCCC", lw=0.8, zorder=1)
    ax.scatter(vals, y, s=58, color=color, zorder=3,
               edgecolors="white", linewidth=0.6)
    for yi, v in zip(y, vals):
        ax.text(v, yi, f" {v:.3g}", va="center", ha="left", fontsize=7.5)
    ax.set_yticks(y); ax.set_yticklabels(cats); ax.set_xlabel(xlabel)
    ax.margins(x=0.14)


# ---------------------------------------------------------------------------
# 13) 构成 / 占比：环形图 / 华夫图 / 百分比堆叠
# ---------------------------------------------------------------------------

def donut_chart(ax, sizes, labels, colors=None, center_text=None):
    """环形图（占比）。Nature 语境下慎用，类别 <=5 且在无更好选择时使用。"""
    colors = colors or _cycle_colors(len(sizes))
    wedges, _ = ax.pie(sizes, colors=colors, startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.2))
    total = float(np.sum(sizes))
    for w, s in zip(wedges, sizes):
        ang = np.deg2rad((w.theta2 + w.theta1) / 2)
        ax.text(np.cos(ang) * 0.79, np.sin(ang) * 0.79, f"{s/total*100:.0f}%",
                ha="center", va="center", fontsize=8)
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5))
    ax.set(aspect="equal")
    if center_text:
        ax.text(0, 0, center_text, ha="center", va="center",
                fontsize=10, fontweight="bold")


def waffle_chart(ax, values, labels, colors=None, rows=10, cols=10):
    """华夫图：用方格数量表示占比，比饼图更易读。"""
    values = np.asarray(values, dtype=float)
    total = values.sum()
    colors = colors or _cycle_colors(len(values))
    n_cells = rows * cols
    counts = np.round(values / total * n_cells).astype(int)
    diff = n_cells - int(counts.sum())
    if diff != 0:
        counts[int(np.argmax(values))] += diff
    cum = np.cumsum(counts)
    idx = 0
    for r in range(rows):
        for c in range(cols):
            cat = int(np.searchsorted(cum, idx, side="right"))
            cat = min(cat, len(values) - 1)
            ax.add_patch(mpatches.Rectangle((c, rows - 1 - r), 1, 1,
                         facecolor=colors[cat], edgecolor="white", linewidth=0.8))
            idx += 1
    ax.set_xlim(0, cols); ax.set_ylim(0, rows); ax.set_aspect("equal")
    ax.axis("off")
    handles = [mpatches.Patch(facecolor=colors[i],
               label=f"{labels[i]} ({values[i]/total*100:.0f}%)")
               for i in range(len(values))]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5))


def stacked_bar_100(ax, categories, groups, values, colors=None,
                    ylabel="Share (%)"):
    """百分比堆叠柱状图。values: shape (n_groups, n_categories)。"""
    values = np.asarray(values, dtype=float)
    share = values / (values.sum(axis=0, keepdims=True) + 1e-12) * 100
    ng, nc = share.shape
    x = np.arange(nc)
    colors = colors or _cycle_colors(ng)
    bottom = np.zeros(nc)
    for i, g in enumerate(groups):
        ax.bar(x, share[i], bottom=bottom, color=colors[i], label=g, width=0.62,
               edgecolor="white", linewidth=0.5)
        bottom += share[i]
    ax.set_xticks(x); ax.set_xticklabels(categories, rotation=30, ha="right")
    ax.set_ylabel(ylabel); ax.set_ylim(0, 100)
    ax.legend(reverse=True, loc="upper left", bbox_to_anchor=(1.0, 1.0))


def waterfall_chart(ax, labels, deltas, start=0.0, pos_color=None,
                    neg_color=None, ylabel="Value"):
    """瀑布图：逐步累积的增减分解。适合贡献度/敏感性拆解。"""
    pos_color = pos_color or NPG_COLORS[2]
    neg_color = neg_color or NPG_COLORS[0]
    deltas = np.asarray(deltas, dtype=float)
    bottoms = []; running = []
    cum = start
    for d in deltas:
        bottoms.append(cum); cum += d; running.append(cum)
    x = np.arange(len(labels))
    for xi, bo, h in zip(x, bottoms, deltas):
        ax.bar(xi, h, bottom=bo, color=pos_color if h >= 0 else neg_color,
               width=0.62)
    ax.plot(x, running, color=NEAR_BLACK, lw=0.8, ls=":", marker="o", markersize=3)
    ax.axhline(0, color="#AAAAAA", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel(ylabel)


# ---------------------------------------------------------------------------
# 14) 分布诊断：ECDF / QQ / 残差
# ---------------------------------------------------------------------------

def _norm_ppf(p):
    """标准正态分位数（Acklam 近似），无需 scipy。"""
    p = np.asarray(p, dtype=float)
    a1, a2, a3, a4, a5, a6 = (-3.969683028665376e+01, 2.209460984245205e+02,
                              -2.759285104469687e+02, 1.383577518672690e+02,
                              -3.066479806614716e+01, 2.506628277459239e+00)
    b1, b2, b3, b4, b5 = (-5.447609879822406e+01, 1.615858368580409e+02,
                          -1.556989798598866e+02, 6.680131188771972e+01,
                          -1.328068155288572e+01)
    c1, c2, c3, c4, c5, c6 = (-7.784894002430293e-03, -3.223964580411365e-01,
                              -2.400758277161838e+00, -2.549732539343734e+00,
                              4.374664141464968e+00, 2.938163982698783e+00)
    d1, d2, d3, d4 = (7.784695709041462e-03, 3.224671290700398e-01,
                      2.445134137142996e+00, 3.754408661907416e+00)
    plow, phigh = 0.02425, 1 - 0.02425
    out = np.zeros_like(p)
    lo = p < plow; hi = p > phigh; mid = ~(lo | hi)
    q = np.sqrt(-2 * np.log(p[lo]))
    out[lo] = (((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6) / ((((d1*q+d2)*q+d3)*q+d4)*q+1)
    q = p[mid] - 0.5; r = q * q
    out[mid] = ((((((a1*r+a2)*r+a3)*r+a4)*r+a5)*r+a6)*q /
                (((((b1*r+b2)*r+b3)*r+b4)*r+b5)*r+1))
    q = np.sqrt(-2 * np.log(1 - p[hi]))
    out[hi] = -(((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6) / ((((d1*q+d2)*q+d3)*q+d4)*q+1)
    return out


def ecdf_plot(ax, samples, labels=None, colors=None, xlabel="Value"):
    """经验累积分布（ECDF）。比直方图更适合比较多个分布。"""
    if not isinstance(samples, (list, tuple)):
        samples = [samples]
    labels = labels or [f"S{i}" for i in range(len(samples))]
    colors = colors or _cycle_colors(len(samples))
    for s, lab, c in zip(samples, labels, colors):
        s = np.sort(np.asarray(s, dtype=float))
        y = np.arange(1, len(s) + 1) / len(s)
        ax.step(s, y, where="post", color=c, lw=1.6, label=lab)
    ax.set_xlabel(xlabel); ax.set_ylabel("Cumulative probability")
    ax.set_ylim(0, 1)
    if len(samples) > 1:
        ax.legend(loc="lower right")


def qq_plot(ax, data, color=None):
    """正态 QQ 图：检验残差/数据正态性。"""
    color = color or NPG_COLORS[4]
    data = np.sort(np.asarray(data, dtype=float)); n = len(data)
    p = (np.arange(1, n + 1) - 0.5) / n
    theo = _norm_ppf(p)
    samp = (data - data.mean()) / (data.std(ddof=1) + 1e-12)
    ax.scatter(theo, samp, s=16, color=color, alpha=0.8,
               edgecolors="white", linewidth=0.4)
    lim = [min(theo.min(), samp.min()), max(theo.max(), samp.max())]
    ax.plot(lim, lim, color=NPG_COLORS[0], lw=1.4, ls="--")
    ax.set_xlabel("Theoretical quantiles"); ax.set_ylabel("Sample quantiles")


def residual_plot(ax, fitted, residuals, color=None, xlabel="Fitted",
                  ylabel="Residual"):
    """残差图：诊断回归/模型系统偏差。"""
    color = color or NPG_COLORS[1]
    ax.axhline(0, color=NEAR_BLACK, lw=0.9, ls="--")
    ax.scatter(fitted, residuals, s=18, color=color, alpha=0.75,
               edgecolors="white", linewidth=0.4)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)


# ---------------------------------------------------------------------------
# 15) 分类性能：ROC / PR
# ---------------------------------------------------------------------------

def _auc(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    return float(np.sum(np.diff(x) * (y[1:] + y[:-1]) / 2))


def roc_curve(ax, y_true, scores, color=None, label=None):
    """ROC 曲线 + AUC。y_true 为 0/1，scores 为连续打分。"""
    color = color or NPG_COLORS[0]
    y_true = np.asarray(y_true, int); scores = np.asarray(scores, float)
    order = np.argsort(-scores); yt = y_true[order]
    P = yt.sum(); N = len(yt) - P
    tpr = np.cumsum(yt) / (P if P else 1)
    fpr = np.cumsum(1 - yt) / (N if N else 1)
    tpr = np.r_[0, tpr, 1]; fpr = np.r_[0, fpr, 1]
    auc = _auc(fpr, tpr)
    ax.plot(fpr, tpr, color=color, lw=1.8, label=f"{label or 'ROC'} (AUC={auc:.3f})")
    ax.plot([0, 1], [0, 1], color="#AAAAAA", lw=0.9, ls="--")
    ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
    ax.legend(loc="lower right")
    return auc


def pr_curve(ax, y_true, scores, color=None, label=None):
    """精确率-召回率曲线 + 平均精确率（类别不平衡时比 ROC 更合适）。"""
    color = color or NPG_COLORS[2]
    y_true = np.asarray(y_true, int); scores = np.asarray(scores, float)
    order = np.argsort(-scores); yt = y_true[order]
    P = yt.sum() if yt.sum() else 1
    tps = np.cumsum(yt)
    prec = tps / np.arange(1, len(yt) + 1)
    rec = tps / P
    ap = _auc(rec, prec)
    ax.plot(rec, prec, color=color, lw=1.8, label=f"{label or 'PR'} (AP={ap:.3f})")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
    ax.legend(loc="lower left")
    return ap


# ---------------------------------------------------------------------------
# 16) 建模过程：收敛曲线 / 特征重要性 / 森林图
# ---------------------------------------------------------------------------

def learning_curve(ax, epochs, train, val, xlabel="Epoch", ylabel="Loss",
                   logy=False):
    """训练/验证收敛曲线。"""
    ax.plot(epochs, train, color=NPG_COLORS[1], lw=1.8, label="Train")
    ax.plot(epochs, val, color=NPG_COLORS[0], lw=1.8, label="Validation")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.legend(loc="best")
    if logy:
        ax.set_yscale("log")


def feature_importance(ax, names, importances, color=None, xlabel="Importance",
                       top=None):
    """特征重要性横向条形图（按重要性升序）。"""
    color = color or NPG_COLORS[4]
    names = list(names); imp = np.asarray(importances, dtype=float)
    order = np.argsort(imp)
    if top:
        order = order[-top:]
    names = [names[i] for i in order]; imp = imp[order]
    y = np.arange(len(names))
    ax.barh(y, imp, color=color, height=0.66)
    ax.set_yticks(y); ax.set_yticklabels(names); ax.set_xlabel(xlabel)


def forest_plot(ax, labels, estimates, lo, hi, ref=0.0, xlabel="Effect size",
                color=None):
    """森林图：效应量 + 置信区间。适合多参数敏感性/回归系数总览。"""
    color = color or NPG_COLORS[4]
    labels = list(labels)
    est = np.asarray(estimates, float); lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    y = np.arange(len(est))
    ax.errorbar(est, y, xerr=[est - lo, hi - est], fmt="o", color=NEAR_BLACK,
                ecolor=color, elinewidth=1.4, capsize=2.5, markersize=5)
    ax.axvline(ref, color="#AAAAAA", lw=0.9, ls="--")
    ax.set_yticks(y); ax.set_yticklabels(labels); ax.set_xlabel(xlabel)


# ---------------------------------------------------------------------------
# 17) 预测不确定性：扇形区间 / 预测-实际
# ---------------------------------------------------------------------------

def fan_chart(ax, x, bands, xlabel="Time", ylabel="Value", color=None):
    """扇形预测图。bands: list[(lo, hi)] 由宽到窄（外->内）。"""
    color = color or NPG_COLORS[0]
    x = np.asarray(x, float)
    alphas = np.linspace(0.12, 0.32, len(bands))
    for (lo, hi), al in zip(bands, alphas):
        ax.fill_between(x, lo, hi, color=color, alpha=al, linewidth=0)
    mid = (np.asarray(bands[-1][0], float) + np.asarray(bands[-1][1], float)) / 2
    ax.plot(x, mid, color=color, lw=1.8)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)


def pred_vs_actual(ax, actual, pred, xlabel="Actual", ylabel="Predicted",
                   color=None):
    """预测 vs 实际散点 + 1:1 参考线。模型验证首选图。"""
    color = color or NPG_COLORS[1]
    actual = np.asarray(actual, float); pred = np.asarray(pred, float)
    ax.scatter(actual, pred, s=22, color=color, alpha=0.75,
               edgecolors="white", linewidth=0.4)
    lim = [min(actual.min(), pred.min()), max(actual.max(), pred.max())]
    ax.plot(lim, lim, color=NPG_COLORS[0], lw=1.4, ls="--")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)


# ---------------------------------------------------------------------------
# 18) 高维关系：气泡 / 2D 密度 / 散点矩阵 / 网络 / 平行坐标
# ---------------------------------------------------------------------------

def bubble_chart(ax, x, y, size, colorvals=None, cmap="viridis",
                 xlabel="x", ylabel="y", cbar_label=""):
    """气泡图：位置 + 大小 + 颜色三通道编码。"""
    x = np.asarray(x, float); y = np.asarray(y, float)
    size = np.asarray(size, float)
    rng = size.max() - size.min()
    s = 80 + 500 * (size - size.min()) / (rng + 1e-12)
    if colorvals is not None:
        sc = ax.scatter(x, y, s=s, c=np.asarray(colorvals, float), cmap=cmap,
                        alpha=0.8, edgecolors="white", linewidth=0.5)
        cb = ax.figure.colorbar(sc, ax=ax, shrink=0.8)
        cb.set_label(cbar_label); cb.outline.set_visible(False)
    else:
        ax.scatter(x, y, s=s, color=NPG_COLORS[1], alpha=0.7,
                   edgecolors="white", linewidth=0.5)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)


def density_2d(ax, x, y, bins=40, cmap="viridis", kind="hexbin",
               xlabel="x", ylabel="y"):
    """二维密度（hexbin/直方）。大样本散点重叠时的替代。"""
    if kind == "hexbin":
        hb = ax.hexbin(x, y, gridsize=bins, cmap=cmap, mincnt=1)
    else:
        h, xe, ye, hb = ax.hist2d(x, y, bins=bins, cmap=cmap)
    cb = ax.figure.colorbar(hb, ax=ax, shrink=0.8)
    cb.set_label("Count"); cb.outline.set_visible(False)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)


def pairplot(data, names=None, color_by=None, palette=None, figsize=None):
    """散点矩阵（pairplot）。data: (n_samples, n_vars)。返回 fig。"""
    data = np.asarray(data, dtype=float)
    n = data.shape[1]
    names = names or [f"x{i}" for i in range(n)]
    fig, axes = plt.subplots(n, n, figsize=figsize or (2.0 * n, 2.0 * n),
                             constrained_layout=True)
    axes = np.atleast_2d(axes)
    cats = None; cmap = None
    if color_by is not None:
        color_by = np.asarray(color_by)
        cats = np.unique(color_by)
        palette = palette or _cycle_colors(len(cats))
        cmap = {c: palette[i] for i, c in enumerate(cats)}
    for i in range(n):
        for j in range(n):
            ax = axes[i, j]
            if i == j:
                ax.hist(data[:, j], bins=15, color=NPG_COLORS[4], alpha=0.6,
                        edgecolor="white", linewidth=0.4)
            elif color_by is not None:
                for c in cats:
                    m = color_by == c
                    ax.scatter(data[m, j], data[m, i], s=8, color=cmap[c],
                               alpha=0.7, linewidth=0)
            else:
                ax.scatter(data[:, j], data[:, i], s=8, color=NPG_COLORS[1],
                           alpha=0.6, linewidth=0)
            if i == n - 1:
                ax.set_xlabel(names[j])
            if j == 0:
                ax.set_ylabel(names[i])
    return fig


def network_graph(ax, edges, node_labels=None, node_color=None):
    """网络/关系图（环形布局）。edges: [(i, j)] 或 [(i, j, weight)]。"""
    edges = [(e[0], e[1], (e[2] if len(e) > 2 else 1.0)) for e in edges]
    nodes = sorted(set([a for a, b, w in edges] + [b for a, b, w in edges]))
    N = len(nodes)
    ang = np.linspace(0, 2 * np.pi, N, endpoint=False)
    pos = {n: (float(np.cos(a)), float(np.sin(a))) for n, a in zip(nodes, ang)}
    maxw = max(w for _, _, w in edges) if edges else 1.0
    for a, b, w in edges:
        x1, y1 = pos[a]; x2, y2 = pos[b]
        ax.plot([x1, x2], [y1, y2], color="#B0B0B0",
                lw=0.5 + 2.0 * w / maxw, alpha=0.6, zorder=1)
    xs = [pos[n][0] for n in nodes]; ys = [pos[n][1] for n in nodes]
    ax.scatter(xs, ys, s=120, color=node_color or NPG_COLORS[4], zorder=2,
               edgecolors="white", linewidth=0.8)
    for n in nodes:
        lab = node_labels.get(n, str(n)) if isinstance(node_labels, dict) else str(n)
        ax.text(pos[n][0], pos[n][1], lab, ha="center", va="center",
                fontsize=7, color="white", zorder=3)
    ax.set_aspect("equal"); ax.axis("off")


def parallel_coordinates(ax, data, names, target=None, cmap="coolwarm"):
    """平行坐标图（多变量概览）。维度 <=8 时可读。"""
    data = np.asarray(data, dtype=float)
    n = data.shape[1]
    dmin = data.min(0); dmax = data.max(0)
    norm = (data - dmin) / (dmax - dmin + 1e-12)
    x = np.arange(n)
    if target is not None:
        t = np.asarray(target, float)
        tn = (t - t.min()) / (t.max() - t.min() + 1e-12)
        cmap_obj = plt.get_cmap(cmap)
        colors = [cmap_obj(v) for v in tn]
    else:
        colors = [NPG_COLORS[4]] * len(data)
    for row, c in zip(norm, colors):
        ax.plot(x, row, color=c, lw=1.0, alpha=0.7)
    for xi in x:
        ax.axvline(xi, color="#DDDDDD", lw=0.8, zorder=0)
    ax.set_xticks(x); ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_yticks([]); ax.set_xlim(-0.2, n - 0.8)


# ---------------------------------------------------------------------------
# 19) 矩阵：通用标注热图 / 聚类热图 / 树状图
# ---------------------------------------------------------------------------

def heatmap_annotated(ax, M, row_labels, col_labels, cmap="viridis",
                      fmt="{:.2f}", annotate=True, cbar_label=""):
    """通用带数值标注热图。M: (n_rows, n_cols)。"""
    M = np.asarray(M, dtype=float)
    im = ax.imshow(M, cmap=cmap, aspect="auto")
    ax.set_xticks(np.arange(M.shape[1])); ax.set_xticklabels(col_labels, rotation=45, ha="right")
    ax.set_yticks(np.arange(M.shape[0])); ax.set_yticklabels(row_labels)
    if annotate:
        thr = (M.max() + M.min()) / 2
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                ax.text(j, i, fmt.format(M[i, j]), ha="center", va="center",
                        fontsize=7, color="white" if M[i, j] < thr else NEAR_BLACK)
    cb = ax.figure.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label(cbar_label); cb.outline.set_visible(False)
    return im


def clustermap(ax, M, row_labels=None, col_labels=None, cmap="RdBu_r",
               method="average"):
    """聚类热图（行列重排）。scipy 可选，缺失时按均值简单排序。"""
    M = np.asarray(M, dtype=float)
    rlab = row_labels or [str(i) for i in range(M.shape[0])]
    clab = col_labels or [str(i) for i in range(M.shape[1])]
    try:
        from scipy.cluster.hierarchy import linkage, leaves_list
        from scipy.spatial.distance import pdist
        ro = leaves_list(linkage(pdist(M), method=method))
        co = leaves_list(linkage(pdist(M.T), method=method))
    except Exception:
        ro = np.argsort(M.mean(1)); co = np.argsort(M.mean(0))
    Mo = M[np.ix_(ro, co)]
    vmax = np.abs(Mo).max()
    im = ax.imshow(Mo, cmap=cmap, vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_yticks(np.arange(len(ro))); ax.set_yticklabels([rlab[i] for i in ro])
    ax.set_xticks(np.arange(len(co))); ax.set_xticklabels([clab[i] for i in co],
                                                          rotation=45, ha="right")
    cb = ax.figure.colorbar(im, ax=ax, shrink=0.8); cb.outline.set_visible(False)
    return im


def dendrogram_plot(ax, data, labels=None, method="average"):
    """层次聚类树状图（需 scipy）。"""
    from scipy.cluster.hierarchy import linkage, dendrogram
    from scipy.spatial.distance import pdist
    Z = linkage(pdist(np.asarray(data, dtype=float)), method=method)
    dendrogram(Z, labels=labels, ax=ax, color_threshold=0,
               above_threshold_color=NEAR_BLACK)
    for coll in ax.collections:
        coll.set_linewidth(1.0)
    ax.set_ylabel("Distance"); despine(ax, keep=("left",))


# ---------------------------------------------------------------------------
# 20) 其他：斜率图 / 哑铃图 / 小倍数 / 极坐标柱
# ---------------------------------------------------------------------------

def slope_chart(ax, labels, y1, y2, group1="Before", group2="After",
                colors=None):
    """斜率图：两时点排名/数值变化的连线。适合前后对比。"""
    labels = list(labels)
    y1 = np.asarray(y1, float); y2 = np.asarray(y2, float)
    colors = colors or [NPG_COLORS[0] if b < a else NPG_COLORS[2]
                        for a, b in zip(y1, y2)]
    for i, (a, b, c) in enumerate(zip(y1, y2, colors)):
        ax.plot([0, 1], [a, b], color=c, lw=1.6, marker="o", markersize=4)
        ax.text(-0.02, a, labels[i], ha="right", va="center", fontsize=8)
        ax.text(1.02, b, labels[i], ha="left", va="center", fontsize=8)
    ax.set_xlim(-0.35, 1.35); ax.set_xticks([0, 1])
    ax.set_xticklabels([group1, group2])
    despine(ax, keep=("left",))


def dumbbell_plot(ax, labels, a_vals, b_vals, a_label="A", b_label="B"):
    """哑铃图：两方案同指标的成对对比。"""
    labels = list(labels)
    a = np.asarray(a_vals, float); b = np.asarray(b_vals, float)
    y = np.arange(len(labels))
    for yi, ai, bi in zip(y, a, b):
        ax.plot([ai, bi], [yi, yi], color="#CCCCCC", lw=2.2, zorder=1)
    ax.scatter(a, y, s=55, color=NPG_COLORS[1], zorder=3, label=a_label,
               edgecolors="white", linewidth=0.6)
    ax.scatter(b, y, s=55, color=NPG_COLORS[0], zorder=3, label=b_label,
               edgecolors="white", linewidth=0.6)
    ax.set_yticks(y); ax.set_yticklabels(labels); ax.legend(loc="best")


def small_multiples(fig_axes, series_list, titles, xlabel="x", ylabel="y",
                    colors=None):
    """小倍数网格。fig_axes 为扁平子图数组，series_list 为 [(x, y), ...]。"""
    colors = colors or _cycle_colors(len(series_list))
    for ax, s, title, c in zip(fig_axes, series_list, titles, colors):
        ax.plot(s[0], s[1], color=c, lw=1.5)
        ax.set_title(title, fontsize=8.5, color=NEAR_BLACK)
        ax.set_xlabel(xlabel, fontsize=8); ax.set_ylabel(ylabel, fontsize=8)


def polar_bar(ax, categories, values, color=None):
    """极坐标柱状图（环形）。类别 <=8 时使用。"""
    color = color or NPG_COLORS[2]
    n = len(categories)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ax.bar(ang, values, width=2 * np.pi / n * 0.85, color=color, alpha=0.85,
           edgecolor="white", linewidth=0.6)
    ax.set_xticks(ang); ax.set_xticklabels(categories)
    ax.set_theta_offset(np.pi / 2); ax.set_theta_direction(-1)


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------

def _demo():
    apply_nature_style()
    outdir = "nature_demo"
    rng = np.random.default_rng(7)

    # 1) 模型 vs 数据
    t = np.linspace(0, 10, 30)
    y_true = 3.2 * (1 - np.exp(-0.55 * t))
    y_obs = y_true + rng.normal(0, 0.12, size=t.shape)
    tt = np.linspace(0, 10, 200)
    fig, ax = new_figure("single")
    ax.scatter(t, y_obs, s=16, color=NPG_COLORS[1], zorder=3, label="Observed")
    ax.plot(tt, 3.2 * (1 - np.exp(-0.55 * tt)), color=NPG_COLORS[0],
            lw=1.8, label="Model", zorder=2)
    ax.set_xlabel("Time (day)")
    ax.set_ylabel("Biomass (g)")
    ax.legend(loc="lower right")
    save_figure(fig, "demo1_model_vs_data", outdir)

    # 2) 置信带
    x = np.linspace(0, 24, 100)
    fig, ax = new_figure("single")
    for i, (mu, lab) in enumerate([(0.9, "Low"), (1.3, "Medium"), (1.8, "High")]):
        mean = mu * np.sin(x / 4) + mu
        std = 0.08 * np.abs(mean) + 0.02
        plot_with_band(ax, x, mean, std, NPG_COLORS[i], label=lab + " scenario")
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Traffic flow (veh/min)")
    ax.legend(loc="upper left")
    save_figure(fig, "demo2_confidence_band", outdir)

    # 3) 多面板
    fig, axes = new_figure("double", nrows=1, ncols=3)
    x = np.linspace(-3, 3, 200)
    for i, ax in enumerate(axes):
        ax.plot(x, np.exp(-0.5 * (x / (0.6 + 0.3 * i)) ** 2), color=NPG_COLORS[i])
        ax.set_xlabel("Deviation (σ)")
        if i == 0:
            ax.set_ylabel("Probability density")
        panel_label(ax, f"({chr(97 + i)})")
    save_figure(fig, "demo3_multi_panel", outdir)

    # 4) 敏感性热图
    p1 = np.linspace(0.5, 1.5, 60)
    p2 = np.linspace(0.5, 1.5, 60)
    P1, P2 = np.meshgrid(p1, p2)
    Z = 40 * (P1 - 1) - 25 * (P2 - 1) + 8 * (P1 - 1) * (P2 - 1)
    fig, ax = new_figure("single")
    vmax = np.abs(Z).max()
    pc = ax.pcolormesh(P1, P2, Z, cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                       shading="auto")
    cb = fig.colorbar(pc, ax=ax)
    cb.set_label("Output change (%)", fontsize=8.5)
    cb.ax.tick_params(labelsize=8)
    cb.outline.set_visible(False)
    ax.contour(P1, P2, Z, levels=[0], colors=NEAR_BLACK, linewidths=0.8)
    ax.set_xlabel(r"Growth rate $r$ (relative)")
    ax.set_ylabel(r"Carrying capacity $K$ (relative)")
    save_figure(fig, "demo4_sensitivity_heatmap", outdir)

    # 5) Tornado
    fig, ax = new_figure("single")
    tornado_plot(ax,
                 ["Growth rate $r$", "Carrying cap. $K$", "Initial size $N_0$",
                  "Harvest rate $h$", "Diffusion $D$"],
                 [18.2, -12.5, 6.1, -4.3, 2.0])
    save_figure(fig, "demo5_tornado", outdir)

    # 6) 分组柱状图
    fig, ax = new_figure("single")
    grouped_bar(ax,
                ["A", "B", "C", "D"],
                ["Model I", "Model II", "Model III"],
                [[3.1, 4.5, 2.8, 5.0],
                 [2.9, 3.8, 3.5, 4.6],
                 [3.5, 4.0, 3.2, 4.9]],
                ylabel="Score")
    save_figure(fig, "demo6_grouped_bar", outdir)

    # 7) 箱线 + strip
    fig, ax = new_figure("single")
    data = [rng.normal(0, 1, n) * (0.5 + i * 0.3) for i, n in enumerate([8, 12, 20])]
    box_strip_plot(ax, data, ["Group A", "Group B", "Group C"], ylabel="Value")
    save_figure(fig, "demo7_box_strip", outdir)

    # 8) 散点 + 回归
    fig, ax = new_figure("single")
    x = rng.normal(50, 10, 40)
    y = 0.8 * x + rng.normal(0, 5, 40)
    scatter_with_fit(ax, x, y, xlabel="Input", ylabel="Output")
    save_figure(fig, "demo8_scatter_fit", outdir)

    # 9) 相关热图
    fig, ax = new_figure("onehalf")
    labels = ["$x_1$", "$x_2$", "$x_3$", "$x_4$", "$x_5$"]
    corr = np.corrcoef(rng.normal(0, 1, (5, 100)))
    im = correlation_heatmap(ax, corr, labels)
    cb = fig.colorbar(im, ax=ax, shrink=0.7)
    cb.outline.set_visible(False)
    save_figure(fig, "demo9_corr_heatmap", outdir)

    # 10) 雷达图
    fig = plt.figure(figsize=(4.5, 4.5))
    ax = fig.add_subplot(111, polar=True)
    radar_chart(ax,
                ["Accuracy", "Speed", "Cost", "Robustness", "Scalability"],
                [[0.85, 0.70, 0.60, 0.90, 0.75],
                 [0.75, 0.90, 0.80, 0.65, 0.85]],
                labels=["Model A", "Model B"])
    save_figure(fig, "demo10_radar", outdir)

    # 11) 堆叠面积
    fig, ax = new_figure("onehalf")
    x = np.linspace(0, 10, 100)
    y1 = np.exp(-0.2 * x)
    y2 = 1.2 * np.exp(-0.5 * x)
    y3 = 0.8 * (1 - np.exp(-0.3 * x))
    stacked_area(ax, x, [y1, y2, y3], ["Susceptible", "Infected", "Recovered"],
                 xlabel="Time (day)", ylabel="Proportion")
    save_figure(fig, "demo11_stacked_area", outdir)

    # 12) 相图
    fig, ax = new_figure("onehalf")
    def lotka_volterra(X, Y, a=1.0, b=0.1, c=1.5, d=0.075):
        return a * X - b * X * Y, -c * Y + d * X * Y
    phase_portrait(ax, lambda X, Y: lotka_volterra(X, Y),
                   xlim=(0, 5), ylim=(0, 3),
                   xlabel="Prey", ylabel="Predator")
    save_figure(fig, "demo12_phase_portrait", outdir)

    # 13) 直方图 + KDE
    fig, ax = new_figure("single")
    hist_kde(ax, rng.lognormal(0, 0.5, 300), xlabel="Latency (ms)")
    save_figure(fig, "demo13_hist_kde", outdir)

    # 14) 配对云雨图
    fig, ax = new_figure("single")
    paired_raincloud(ax, rng.normal(5, 1, 40), rng.normal(6.2, 1.1, 40),
                     group_labels=("Baseline", "Intervention"),
                     ylabel="Response time (s)")
    save_figure(fig, "demo14_raincloud", outdir)

    # 15) 小提琴图
    fig, ax = new_figure("single")
    violin_plot(ax, [rng.normal(0, 1, 60), rng.normal(0.5, 1.2, 60),
                     rng.normal(-0.3, 0.8, 60)],
                ["Ctrl", "Trt1", "Trt2"], show_box=True)
    save_figure(fig, "demo15_violin", outdir)

    # 16) 时间线
    fig, ax = new_figure("onehalf")
    timeline(ax,
             ["Data prep", "Modeling", "Validation", "Writing"],
             [0, 1, 3, 5],
             [1, 2, 2, 3],
             xlabel="Day")
    save_figure(fig, "demo16_timeline", outdir)

    print("\nAll demo figures written to ./nature_demo/")


def _demo2():
    """生成扩展图型（12-20 节）的示例图。"""
    apply_nature_style()
    outdir = "nature_demo"
    rng = np.random.default_rng(11)

    # 棒棒糖
    fig, ax = new_figure("single")
    lollipop_chart(ax, ["USA", "CHN", "GBR", "JPN", "AUS", "FRA"],
                   [167, 86, 63, 45, 41, 32], xlabel="Projected medals")
    save_figure(fig, "demo17_lollipop", outdir)

    # 正负发散柱
    fig, ax = new_figure("single")
    diverging_bar(ax, ["USA", "CHN", "GBR", "FRA", "JPN"],
                  [25.2, 6.4, -3.1, -27.7, 2.0], xlabel="Change vs 2024")
    save_figure(fig, "demo18_diverging_bar", outdir)

    # 点图
    fig, ax = new_figure("single")
    dot_plot(ax, ["Gymnastics", "Diving", "Table tennis", "Weightlifting", "Shooting"],
             [12, 9, 8, 7, 5], xlabel="Medals")
    save_figure(fig, "demo19_dot_plot", outdir)

    # 环形图
    fig, ax = new_figure("single")
    donut_chart(ax, [40, 35, 15, 10], ["Sport A", "Sport B", "Sport C", "Other"],
                center_text="100")
    save_figure(fig, "demo20_donut", outdir)

    # 华夫图
    fig, ax = new_figure("single")
    waffle_chart(ax, [48, 27, 15, 10], ["Econ", "Social", "Env", "Other"])
    save_figure(fig, "demo21_waffle", outdir)

    # 百分比堆叠
    fig, ax = new_figure("onehalf")
    stacked_bar_100(ax, ["2016", "2020", "2024", "2028*"],
                    ["Asia", "Europe", "Americas"],
                    [[45, 48, 52, 55], [35, 33, 31, 29], [20, 19, 17, 16]],
                    ylabel="Medal share (%)")
    save_figure(fig, "demo22_stacked100", outdir)

    # 瀑布图
    fig, ax = new_figure("onehalf")
    waterfall_chart(ax, ["Base", "Host", "Coach", "Event+", "Decline"],
                    [100, 41, 8, 6, -22], ylabel="Total medals")
    save_figure(fig, "demo23_waterfall", outdir)

    # ECDF
    fig, ax = new_figure("single")
    ecdf_plot(ax, [rng.normal(0, 1, 200), rng.normal(0.7, 1.2, 200)],
              ["Baseline", "Improved"], xlabel="Error")
    save_figure(fig, "demo24_ecdf", outdir)

    # QQ
    fig, ax = new_figure("single")
    qq_plot(ax, rng.normal(2, 1, 150))
    save_figure(fig, "demo25_qq", outdir)

    # 残差
    fig, ax = new_figure("single")
    fit = rng.uniform(0, 10, 60)
    residual_plot(ax, fit, rng.normal(0, 0.6, 60))
    save_figure(fig, "demo26_residual", outdir)

    # ROC / PR
    yt = rng.integers(0, 2, 200)
    sc = yt * 0.9 + rng.normal(0, 1.0, 200)
    fig, ax = new_figure("single")
    roc_curve(ax, yt, sc)
    save_figure(fig, "demo27_roc", outdir)
    fig, ax = new_figure("single")
    pr_curve(ax, yt, sc)
    save_figure(fig, "demo28_pr", outdir)

    # 收敛曲线
    fig, ax = new_figure("single")
    ep = np.arange(1, 51)
    learning_curve(ax, ep, 0.5 + 3 * np.exp(-ep / 8), 0.9 + 3 * np.exp(-ep / 12))
    save_figure(fig, "demo29_learning_curve", outdir)

    # 特征重要性
    fig, ax = new_figure("single")
    feature_importance(ax, ["GDP", "Delegation", "Host", "Events", "History"],
                       [0.32, 0.28, 0.18, 0.13, 0.09])
    save_figure(fig, "demo30_feature_importance", outdir)

    # 森林图
    fig, ax = new_figure("single")
    forest_plot(ax, ["Host", "Coach", "Event+", "Delegation"],
                [1.41, 4.20, 0.80, 0.55],
                [1.12, 2.10, 0.20, 0.30], [1.70, 6.30, 1.40, 0.80])
    save_figure(fig, "demo31_forest", outdir)

    # 扇形预测
    fig, ax = new_figure("onehalf")
    yy = np.arange(2012, 2033, 4)
    mid = 100 + 4 * np.arange(len(yy))
    fan_chart(ax, yy, [(mid - 30, mid + 30), (mid - 15, mid + 15)],
              xlabel="Year", ylabel="Total medals")
    save_figure(fig, "demo32_fan_chart", outdir)

    # 预测 vs 实际
    fig, ax = new_figure("single")
    a = rng.uniform(0, 120, 60)
    pred_vs_actual(ax, a, a + rng.normal(0, 8, 60))
    save_figure(fig, "demo33_pred_vs_actual", outdir)

    # 气泡
    fig, ax = new_figure("single")
    bubble_chart(ax, rng.uniform(0, 10, 40), rng.uniform(0, 10, 40),
                 rng.uniform(1, 100, 40), colorvals=rng.normal(0, 1, 40),
                 xlabel="Event count", ylabel="Medals", cbar_label="GDP rank")
    save_figure(fig, "demo34_bubble", outdir)

    # 2D 密度
    fig, ax = new_figure("single")
    xx = rng.normal(0, 1, 3000); yy = xx * 0.6 + rng.normal(0, 1, 3000)
    density_2d(ax, xx, yy, kind="hexbin", xlabel="x", ylabel="y")
    save_figure(fig, "demo35_density2d", outdir)

    # 散点矩阵
    fig = pairplot(rng.normal(0, 1, (200, 4)),
                   names=["GDP", "Pop", "Athl", "Medal"],
                   color_by=rng.integers(0, 2, 200))
    save_figure(fig, "demo36_pairplot", outdir)

    # 网络图
    fig, ax = new_figure("onehalf")
    network_graph(ax, [(0, 1, 3), (1, 2, 1), (2, 3, 2), (3, 0, 1), (0, 2, 2), (1, 3, 1)],
                  node_labels={0: "A", 1: "B", 2: "C", 3: "D"})
    save_figure(fig, "demo37_network", outdir)

    # 平行坐标
    fig, ax = new_figure("onehalf")
    dat = rng.normal(0, 1, (20, 5))
    parallel_coordinates(ax, dat, ["GDP", "Pop", "Athl", "Events", "Host"],
                         target=rng.uniform(0, 100, 20))
    save_figure(fig, "demo38_parallel_coords", outdir)

    # 通用标注热图
    fig, ax = new_figure("onehalf")
    heatmap_annotated(ax, rng.uniform(0, 1, (4, 5)),
                      ["A", "B", "C", "D"], ["s1", "s2", "s3", "s4", "s5"],
                      cmap="YlGnBu", cbar_label="Score")
    save_figure(fig, "demo39_heatmap_annotated", outdir)

    # 聚类热图
    fig, ax = new_figure("onehalf")
    base = rng.normal(0, 1, (6, 8))
    clustermap(ax, base, row_labels=[f"r{i}" for i in range(6)],
               col_labels=[f"c{i}" for i in range(8)])
    save_figure(fig, "demo40_clustermap", outdir)

    # 树状图（需 scipy）
    if HAS_SCIPY:
        fig, ax = new_figure("onehalf")
        dendrogram_plot(ax, rng.normal(0, 1, (8, 5)),
                        labels=[f"obs{i}" for i in range(8)])
        save_figure(fig, "demo41_dendrogram", outdir)

    # 斜率图
    fig, ax = new_figure("single")
    slope_chart(ax, ["USA", "CHN", "GBR", "FRA", "JPN"],
                [126, 91, 65, 64, 45], [167, 86, 63, 36, 45],
                group1="2024", group2="2028")
    save_figure(fig, "demo42_slope", outdir)

    # 哑铃图
    fig, ax = new_figure("single")
    dumbbell_plot(ax, ["USA", "CHN", "GBR", "JPN"],
                  [40, 40, 14, 20], [55, 34, 16, 22], a_label="2024", b_label="2028")
    save_figure(fig, "demo43_dumbbell", outdir)

    # 小倍数
    fig, axes = new_figure("double", nrows=2, ncols=3)
    axes = np.ravel(axes)
    tt = np.linspace(0, 5, 60)
    series = [(tt, np.sin(tt + k / 2) * (1 + k / 3)) for k in range(6)]
    small_multiples(axes, series, [f"Country {i+1}" for i in range(6)],
                    xlabel="Year", ylabel="Medals")
    save_figure(fig, "demo44_small_multiples", outdir)

    # 极坐标柱
    fig = plt.figure(figsize=(3.6, 3.6))
    ax = fig.add_subplot(111, polar=True)
    polar_bar(ax, ["N", "E", "S", "W", "NE", "NW"], [8, 6, 5, 7, 4, 3])
    save_figure(fig, "demo45_polar_bar", outdir)

    print("\nExtended demo figures (17-45) written to ./nature_demo/")


if __name__ == "__main__":
    _demo()
    _demo2()
