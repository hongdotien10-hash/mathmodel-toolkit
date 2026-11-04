#!/usr/bin/env python3
"""
生成 mcm-math-modeling 的 Agensi 市场图标（512×512 PNG）。

设计原则（见 SUBMIT-GUIDE.md 第四节）：
- 正方形，512×512，市场首页展示为 80×80
- 深色底 + 白色数学符号，比界面截图更抓眼
- 配色取自本包自带 nature_plot.py 的 NPG_COLORS 体系，保持视觉一致

主体符号：f(x) = max，并叠加约束感知的视觉元素（决策点门禁 + 多子问题扇出）。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle

from nature_plot import NPG_COLORS, apply_nature_style

OUT_PNG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.png")

DARK_BG = "#11151C"
FG = "#F5F7FA"
MUTED = "#8A94A6"


def build_icon():
    apply_nature_style()

    fig = plt.figure(figsize=(5.12, 5.12), dpi=100)
    fig.patch.set_facecolor(DARK_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(DARK_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    # 精确 512×512：关闭自动裁切，savefig 用固定像素尺寸
    ax.set_position([0, 0, 1, 1])

    # 顶部三个彩色节点：代表子问题拆解（CP1 要求子问题数与题面一致）
    node_y = 78
    node_xs = [30, 50, 70]
    for i, (nx, color) in enumerate(zip(node_xs, NPG_COLORS[:3])):
        ax.add_patch(Circle((nx, node_y), 3.6, facecolor=color,
                            edgecolor="none", zorder=3))
        # 连向主体
        ax.add_patch(FancyArrowPatch(
            (nx, node_y - 4.2), (50, 56),
            arrowstyle="-", color=MUTED, lw=1.1, alpha=0.55, zorder=1))

    # 主体：f(x) = max
    ax.text(50, 46, r"$f(x) = \max$", ha="center", va="center",
            color=FG, fontsize=40, fontweight="bold", zorder=4)

    # 下方约束括号：表示约束追溯矩阵（每条约束必须落地）
    bracket_y = 24
    ax.plot([22, 26], [bracket_y, bracket_y], color=NPG_COLORS[0],
            lw=3.2, solid_capstyle="round", zorder=3)
    ax.plot([26, 26], [bracket_y, bracket_y + 9], color=NPG_COLORS[0],
            lw=3.2, solid_capstyle="round", zorder=3)
    ax.plot([74, 78], [bracket_y, bracket_y], color=NPG_COLORS[0],
            lw=3.2, solid_capstyle="round", zorder=3)
    ax.plot([74, 74], [bracket_y, bracket_y + 9], color=NPG_COLORS[0],
            lw=3.2, solid_capstyle="round", zorder=3)
    ax.plot([22, 78], [bracket_y, bracket_y], color=NPG_COLORS[0],
            lw=3.2, solid_capstyle="round", zorder=3)

    # 括号内三条约束（对应 约束→公式→代码接口 三段追溯）
    for i, color in enumerate(NPG_COLORS[1:4]):
        y = bracket_y + 2.6 + i * 2.6
        ax.plot([34, 66], [y, y], color=color, lw=2.6,
                solid_capstyle="round", alpha=0.9, zorder=3)

    # 底部文字条：论文输出
    ax.text(50, 9.5, "MATH MODELING", ha="center", va="center",
            color=MUTED, fontsize=9.5, fontweight="normal",
            fontfamily="DejaVu Sans", zorder=4)

    fig.savefig(OUT_PNG, dpi=100, facecolor=DARK_BG,
                bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print("saved:", OUT_PNG)


if __name__ == "__main__":
    build_icon()
