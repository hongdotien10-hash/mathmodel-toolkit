r"""
flowchart.py — Nature 风格「流程图 / 框架图」模板库（14 种），美赛论文专用。

为什么用代码画流程图？
    draw.io / Graphviz / TikZ 生成的是外部文件，改一个字都要手工拖动，且容易
    出现「箭头指错框、箭头穿过文字、框大小不一」等错误。本模块用 matplotlib
    精确绘制：所有箭头都从「框的边界锚点」出发，坐标由布局函数算出，不可能指错；
    内容全部是字符串参数，可随意替换；输出 PDF(矢量) + PNG(300dpi)。

用法
----
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from flowchart import apply_fc_style, save_figure, flow_vertical, framework_bands

    apply_fc_style()
    fig = flow_vertical(["Problem", "Model", "Validation", "Conclusion"],
                        title="Research workflow")
    save_figure(fig, "fig_framework")          # -> fig_framework.pdf + .png

14 种模板
--------
  1. flow_vertical          纵向线性流程
  2. flow_horizontal        横向线性流程
  3. flow_snake             蛇形流程（超长链条折行）
  4. flow_decision          判断/分支流程（菱形 + Yes/No）
  5. flow_iterative         迭代/循环流程（带反馈回路）
  6. framework_bands        五带技术路线图（MCM 默认框架图）
  7. framework_three_column Phase | Content | Methods 三栏框架
  8. swimlane               泳道图（阶段/角色横泳道）
  9. layered_architecture   分层架构图
 10. method_mapping         Phase × Method 方法映射矩阵
 11. decomposition_tree     问题分解树
 12. ipo_pipeline           Input → Process → Output 数据流水线
 13. timeline_phases        阶段时间轴
 14. problem_model_output   问题 → 模型 → 产出 映射图

直接运行本文件可生成全部 14 张示例图：
    python flowchart.py [输出目录]        # 默认 ./fc_demo
"""

from __future__ import annotations

import math
import os
from pathlib import Path
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
from matplotlib.path import Path

# ---------------------------------------------------------------------------
# 配色（与 nature_plot.py 的 NPG 配色保持一致）
# ---------------------------------------------------------------------------

NEAR_BLACK = "#1A1A1A"
INK = "#262626"
EDGE = "#5A6472"
MUTE = "#8491B4"

# 每种「框类型」= (填充色, 描边色)：浅填充 + 深描边，保证打印可读
FILL = {
    "terminal": ("#D9EFE7", "#00846B"),   # 起止（圆角胶囊）
    "process":  ("#E6EEF6", "#3C5488"),   # 普通处理
    "decision": ("#FBE7DC", "#C25E1E"),   # 判断（菱形）
    "io":       ("#ECECEC", "#6B6B6B"),   # 输入/输出
    "data":     ("#EAE3F2", "#6A4C93"),   # 数据
    "emphasis": ("#FADDD8", "#B03A2E"),   # 强调/关键产出
    "note":     ("#FFF6DC", "#B8860B"),   # 备注
    "ghost":    ("#FFFFFF", "#8491B4"),   # 空心
}
MODE_FILL = ("#F3C6BC", "#A93226")        # 高亮模式框（强调色块）

# 阶段配色（用于 framework / swimlane 的分带底色，保持同色系深浅）
BAND_COLORS = ["#3C5488", "#4DBBD5", "#00A087", "#F39B7F", "#8491B4",
               "#B09C85", "#91D1C2", "#C25E1E"]


def _dark(color: str, f: float = 0.78) -> str:
    """把颜色按比例压暗，用作白底上的彩色文字，保证可读性。"""
    c = color.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(r * f), int(g * f), int(b * f))


def apply_fc_style():
    """一键应用流程图 rcParams（与 Nature 风格一致）。"""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8.5,
        "mathtext.fontset": "stixsans",
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "pdf.fonttype": 42,       # 文字可编辑
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def save_figure(fig, name, outdir="."):
    """同时导出矢量 PDF 与 300dpi PNG。name 不含扩展名。"""
    os.makedirs(outdir, exist_ok=True)
    pdf_path = os.path.join(outdir, name + ".pdf")
    png_path = os.path.join(outdir, name + ".png")
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print(f"saved: {png_path}")
    return pdf_path, png_path


# ---------------------------------------------------------------------------
# 基础绘制原语
# ---------------------------------------------------------------------------

def new_canvas(w: float, h: float):
    """创建以「英寸」为坐标单位的画布：1 数据单位 = 1 英寸。"""
    fig = plt.figure(figsize=(w, h))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _wrap(text: str, n: int) -> str:
    """按字符数 n 折行；保留调用方写入的换行。"""
    if n is None or n <= 0:
        return str(text)
    out = []
    for para in str(text).split("\n"):
        if not para.strip():
            out.append("")
            continue
        out.extend(textwrap.wrap(para, n) or [""])
    return "\n".join(out)


def _fit_wrap(text: str, width_in: float, fs: float) -> str:
    """根据框宽和字号估算折行宽度（避免文字溢出框）。"""
    char_w = fs / 72.0 * 0.56          # 单字符近似宽度（英寸）
    n = int(max(4, (width_in - 0.16) / char_w))
    return _wrap(text, n)


def box(ax, x, y, w, h, text="", kind="process", fs=8.0,
        fc=None, ec=None, tc=None, lw=1.0, bold=False, wrap=None, z=3):
    """画一个节点框，返回 9 个边界锚点。

    参数
    ----
    x, y   : 中心坐标（英寸）
    kind   : terminal/process/decision/io/data/emphasis/note/ghost
    tc     : 文字颜色（默认深灰；深底框可传 "white"）
    返回   : dict(c,t,b,l,r,tl,tr,bl,br) —— 连接箭头时请使用这些锚点，
             它们恰好落在框边缘，箭头不会「指进框里」或「指不到框」。
    """
    f_def, e_def = FILL.get(kind, FILL["process"])
    fc = fc or f_def
    ec = ec or e_def

    if kind == "decision":                       # 菱形
        verts = [(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)]
        ax.add_patch(Polygon(verts, closed=True, facecolor=fc, edgecolor=ec,
                             linewidth=lw, zorder=z, joinstyle="miter"))
        tw = w * 0.62
    else:
        if kind == "terminal":                   # 胶囊
            r = min(w, h) / 2.0 * 0.999
        else:                                    # 圆角矩形
            r = min(0.11, h * 0.32, w * 0.32)
        ax.add_patch(FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle=f"round,pad=0,rounding_size={r:.5f}",
            facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z,
            mutation_aspect=1))
        tw = w

    if text:
        ax.text(x, y, _fit_wrap(text, tw, fs), ha="center", va="center",
                fontsize=fs, color=tc or INK, zorder=z + 1, linespacing=1.25,
                fontweight="bold" if bold else "normal")

    return {"c": (x, y), "t": (x, y + h / 2), "b": (x, y - h / 2),
            "l": (x - w / 2, y), "r": (x + w / 2, y),
            "tl": (x - w / 2, y + h / 2), "tr": (x + w / 2, y + h / 2),
            "bl": (x - w / 2, y - h / 2), "br": (x + w / 2, y - h / 2)}


def poly_arrow(ax, pts, color=EDGE, lw=1.15, arrow=True, style="-|>",
               ms=9, z=2, ls="-", both=False):
    """沿给定折线画箭头（2 点=直线，3+ 点=折线/肘形）。"""
    verts = [tuple(p) for p in pts]
    codes = [Path.MOVETO] + [Path.LINETO] * (len(verts) - 1)
    st = "<|-|>" if both else style
    ax.add_patch(FancyArrowPatch(
        path=Path(verts, codes), arrowstyle=st if arrow else "-",
        mutation_scale=ms, lw=lw, color=color, zorder=z,
        shrinkA=0, shrinkB=0, linestyle=ls,
        joinstyle="miter", capstyle="butt"))


def line(ax, pts, color=EDGE, lw=1.15, z=2, ls="-"):
    """画无箭头折线。"""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=color, lw=lw, zorder=z, ls=ls,
            solid_capstyle="butt")


def link(ax, A, sa, B, sb, color=EDGE, lw=1.15, style="-|>", ms=9, z=2,
         ls="-"):
    """两点直连箭头：从 A 的 sa 锚点到 B 的 sb 锚点。"""
    poly_arrow(ax, [A[sa], B[sb]], color=color, lw=lw, style=style,
               ms=ms, z=z, ls=ls)


def elbow(ax, A, sa, B, sb, color=EDGE, lw=1.15, ms=9, z=2):
    """正交（直角）连线：自动在水平/垂直段之间切换，避免斜穿文字。"""
    p0, p1 = A[sa], B[sb]
    hor_a = sa in ("l", "r")
    hor_b = sb in ("l", "r")
    if hor_a and hor_b:
        mx = (p0[0] + p1[0]) / 2.0
        pts = [p0, (mx, p0[1]), (mx, p1[1]), p1]
    elif (not hor_a) and (not hor_b):
        my = (p0[1] + p1[1]) / 2.0
        pts = [p0, (p0[0], my), (p1[0], my), p1]
    elif hor_a and not hor_b:                 # r/l -> t/b
        pts = [p0, (p1[0], p0[1]), p1]
    else:                                     # t/b -> l/r
        pts = [p0, (p0[0], p1[1]), p1]
    poly_arrow(ax, pts, color=color, lw=lw, ms=ms, z=z)


def tag(ax, p, text, color=INK, fs=7.0, dx=0.0, dy=0.0):
    """在箭头上/旁加文字标签（带白底，避免压线）。"""
    ax.text(p[0] + dx, p[1] + dy, text, ha="center", va="center",
            fontsize=fs, color=color, zorder=6,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.92))


def header(ax, w, h, title, sub=None):
    """图上方的标题（不进 caption），返回内容区顶部 y。"""
    y = h - 0.24
    if title:
        ax.text(w / 2, y, title, ha="center", va="top", fontsize=10.5,
                fontweight="bold", color=NEAR_BLACK, zorder=6)
        y -= 0.30
    if sub:
        ax.text(w / 2, y, sub, ha="center", va="top", fontsize=8,
                color=EDGE, zorder=6)
        y -= 0.24
    return y - 0.12


# ===========================================================================
# 1. 纵向线性流程
# ===========================================================================

def flow_vertical(labels, kinds=None, title=None, bw=3.2, bh=0.62, gap=0.42,
                  w=None, fs=8.2):
    """自上而下的线性流程。labels 为字符串列表，kinds 自定义框类型。"""
    n = len(labels)
    kinds = kinds or (["terminal"] + ["process"] * (n - 2) + ["terminal"]
                      if n >= 2 else ["terminal"])
    w = w or (bw + 1.6)
    body = n * bh + (n - 1) * gap
    h = body + 0.95
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)
    cx = w / 2
    y = ytop - bh / 2
    boxes = []
    for i, lab in enumerate(labels):
        boxes.append(box(ax, cx, y, bw, bh, lab, kind=kinds[i], fs=fs))
        y -= (bh + gap)
    for i in range(n - 1):
        link(ax, boxes[i], "b", boxes[i + 1], "t")
    return fig


# ===========================================================================
# 2. 横向线性流程
# ===========================================================================

def flow_horizontal(labels, kinds=None, title=None, bh=0.70, gap=0.42,
                    margin=0.35, w=7.0, fs=8.0):
    """自左而右的线性流程。"""
    n = len(labels)
    kinds = kinds or (["terminal"] + ["process"] * (n - 2) + ["terminal"]
                      if n >= 2 else ["terminal"])
    h = 1.95 if title else 1.55
    bw = (w - 2 * margin - (n - 1) * gap) / n
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)
    y = ytop - bh / 2 - 0.05
    x = margin + bw / 2
    boxes = []
    for i, lab in enumerate(labels):
        boxes.append(box(ax, x, y, bw, bh, lab, kind=kinds[i], fs=fs))
        x += (bw + gap)
    for i in range(n - 1):
        link(ax, boxes[i], "r", boxes[i + 1], "l")
    return fig


# ===========================================================================
# 3. 蛇形流程（超长链条折行）
# ===========================================================================

def flow_snake(labels, ncol=4, title=None, bw=1.35, bh=0.62, gap=0.34,
               rowgap=0.60, margin=0.30, fs=8.0):
    """蛇形折行流程：行内左→右、右→左交替，行末用肘形箭头折到下一行。"""
    n = len(labels)
    nrow = math.ceil(n / ncol)
    w = 2 * margin + ncol * bw + (ncol - 1) * gap
    h = nrow * bh + (nrow - 1) * rowgap + 0.95
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)

    pos, boxes = [], []
    for i in range(n):
        r, c = divmod(i, ncol)
        c_eff = c if r % 2 == 0 else (ncol - 1 - c)
        x = margin + bw / 2 + c_eff * (bw + gap)
        y = ytop - bh / 2 - r * (bh + rowgap)
        pos.append((r, c_eff, x, y, c))
        boxes.append(box(ax, x, y, bw, bh, labels[i],
                         kind="process", fs=fs))

    for i in range(n - 1):
        r0, _, x0, y0, c0 = pos[i]
        r1, _, x1, y1, c1 = pos[i + 1]
        A, B = boxes[i], boxes[i + 1]
        if r0 == r1:                                  # 同行：水平箭头
            if x1 > x0:
                link(ax, A, "r", B, "l")
            else:
                link(ax, A, "l", B, "r")
        else:                                         # 换行：底→顶 Z 形折线
            my = (A["b"][1] + B["t"][1]) / 2.0
            poly_arrow(ax, [A["b"], (A["b"][0], my),
                            (B["t"][0], my), B["t"]])
    return fig


# ===========================================================================
# 4. 判断/分支流程
# ===========================================================================

def flow_decision(start, question, branches, end, title=None, w=6.8,
                  sh=0.60, dh=1.05, bh=0.56, gap=0.38, fs=8.0,
                  margin=0.35, yes_no=True):
    """判断分支流程（菱形判断 + Yes/No 分支 + 汇合总线）。

    branches : [(分支结果标签, [该分支下的步骤...]), ...]，通常 2 支。
    分支框宽度按画布自适应，左右留边，绝不越界；分支下方用汇合总线收束，
    再进入 end，不产生交叉线。
    """
    nb = len(branches)
    bw = min(2.2, (w - 2 * margin - 0.45 * (nb - 1)) / nb)
    span = (w - 2 * margin - bw)
    centers = ([margin + bw / 2 + i * span / (nb - 1) for i in range(nb)]
               if nb > 1 else [w / 2])
    cx = w / 2
    dw = 2 * min(1.30, max(0.85, (cx - centers[0]) - 0.30))

    def col_h(k):
        return bh + (k * (gap + bh) if k else 0)

    maxcol = max(col_h(len(s)) for _, s in branches)
    g1, g2, g3, g4 = 0.48, 0.55, 0.46, 0.46
    Hc = sh + g1 + dh + g2 + maxcol + g3 + g4 + sh
    top_m = 0.70 if title else 0.30
    h = Hc + top_m + 0.25
    fig, ax = new_canvas(w, h)
    if title:
        ax.text(w / 2, h - 0.26, title, ha="center", va="top", fontsize=10.5,
                fontweight="bold", color=NEAR_BLACK, zorder=6)
    top = h - top_m

    # 起始框
    yS = top - sh / 2
    S = box(ax, cx, yS, min(2.4, w - 2 * margin), sh, start, kind="terminal")
    # 判断菱形
    yD = yS - sh / 2 - g1 - dh / 2
    D = box(ax, cx, yD, dw, dh, question, kind="decision", fs=fs - 0.3)
    link(ax, S, "b", D, "t")

    # 分支列
    yB0 = yD - dh / 2 - g2 - bh / 2
    lasts = []
    for i, (lab, steps) in enumerate(branches):
        x = centers[i]
        col = BAND_COLORS[i % len(BAND_COLORS)]
        fb = box(ax, x, yB0, bw, bh, lab, kind="process",
                 fc="white", ec=col, tc=_dark(col), fs=fs, lw=1.2, bold=True)
        sa = "l" if x < cx else "r"
        poly_arrow(ax, [D[sa], (x, D[sa][1]), fb["t"]], color=EDGE)
        if yes_no:
            tag(ax, ((D[sa][0] + x) / 2, D[sa][1] + 0.10),
                "No" if sa == "l" else "Yes")
        yy = yB0 - (bh + gap)
        prev = fb
        for s in steps:
            bb = box(ax, x, yy, bw, bh, s, kind="process",
                     fc="white", ec=col, fs=fs - 0.3)
            link(ax, prev, "b", bb, "t", color="#B0B7C3", ms=8)
            prev = bb
            yy -= (bh + gap)
        lasts.append(prev["b"])

    # 汇合总线
    ybus = min(p[1] for p in lasts) - g3
    for lb in lasts:
        poly_arrow(ax, [lb, (lb[0], ybus)], ms=8)
    xs_ = sorted(p[0] for p in lasts)
    line(ax, [(xs_[0], ybus), (xs_[-1], ybus)])
    E = box(ax, cx, ybus - g4 - sh / 2, min(2.4, w - 2 * margin), sh, end,
            kind="terminal")
    poly_arrow(ax, [(cx, ybus), E["t"]])
    return fig


# ===========================================================================
# 5. 迭代/循环流程
# ===========================================================================

def flow_iterative(labels, loop_label="iterate until converged",
                   title=None, bw=3.2, bh=0.62, gap=0.42, w=None, fs=8.0):
    """带反馈回路的迭代流程：最后一个框用回路箭头指回第一个框。"""
    n = len(labels)
    w = w or (bw + 2.6)
    body = n * bh + (n - 1) * gap
    h = body + 0.95
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)
    cx = w / 2 - 0.55
    y = ytop - bh / 2
    boxes = []
    for i, lab in enumerate(labels):
        k = "terminal" if i == 0 else ("process" if i < n - 1 else "emphasis")
        boxes.append(box(ax, cx, y, bw, bh, lab, kind=k, fs=fs))
        y -= (bh + gap)
    for i in range(n - 1):
        link(ax, boxes[i], "b", boxes[i + 1], "t")
    # 反馈回路：最后一个框右侧 -> 右侧竖线 -> 第一个框右侧
    xr = cx + bw / 2 + 0.75
    A, B = boxes[-1], boxes[0]
    poly_arrow(ax, [A["r"], (xr, A["r"][1]), (xr, B["r"][1]), B["r"]],
               color="#B03A2E", ls="--")
    ax.text(xr + 0.10, (A["r"][1] + B["r"][1]) / 2, loop_label, rotation=90,
            ha="center", va="center", fontsize=7.2, color="#B03A2E", zorder=6)
    return fig


# ===========================================================================
# 6. 五带技术路线图（MCM 默认框架图）
# ===========================================================================

def framework_bands(bands, title=None, w=6.6, band_h=0.92, gap=0.36,
                    label_w=1.85, fs=8.2, title_fs=9.2):
    """五带技术路线图：左侧阶段标签 + 右侧内容块，条带间用向下箭头串联。

    bands : [(阶段名, [内容块1, 内容块2, ...]), ...]
    """
    n = len(bands)
    h = n * band_h + (n - 1) * (gap + 0.30) + (0.95 if title else 0.4)
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)

    band_boxes = []
    y = ytop - band_h / 2
    for i, (name, chips) in enumerate(bands):
        col = BAND_COLORS[i % len(BAND_COLORS)]
        # 整条带
        ax.add_patch(FancyBboxPatch(
            (0.22, y - band_h / 2), w - 0.44, band_h,
            boxstyle="round,pad=0,rounding_size=0.10",
            facecolor="#F7F8FA", edgecolor=col, linewidth=1.1, zorder=1))
        # 左侧阶段标签（实色）
        ax.add_patch(FancyBboxPatch(
            (0.22, y - band_h / 2), label_w, band_h,
            boxstyle="round,pad=0,rounding_size=0.10",
            facecolor=col, edgecolor=col, linewidth=0, zorder=2))
        ax.text(0.22 + label_w / 2, y, _wrap(name, 12), ha="center",
                va="center", fontsize=title_fs, color="white",
                fontweight="bold", zorder=3, linespacing=1.2)
        # 右侧内容块
        x0 = 0.22 + label_w + 0.22
        x1 = w - 0.34
        m = len(chips)
        if m:
            cg = 0.20
            cw = (x1 - x0 - (m - 1) * cg) / m
            for j, chip in enumerate(chips):
                cxc = x0 + cw / 2 + j * (cw + cg)
                box(ax, cxc, y, cw, band_h - 0.30, chip,
                    kind="process", fc="white", ec=col, fs=fs, lw=0.9)
        band_boxes.append((y, col, name))
        # 条带间向下箭头（在带间隙中）
        if i < n - 1:
            ya = y - band_h / 2                     # 本带底边
            yb = ya - (gap + 0.30)                  # 下一带顶边
            poly_arrow(ax, [(w / 2, ya), (w / 2, yb)], color="#B0B7C3", ms=9)
        y -= (band_h + gap + 0.30)
    return fig


# ===========================================================================
# 7. 三栏框架图（Phase | Content | Methods）
# ===========================================================================

def framework_three_column(rows, title=None, w=6.8, row_h=0.80, gap=0.30,
                           fs=8.0, headers=("Phase", "Content", "Methods")):
    """三栏框架：左=阶段（纵向串联），中=研究内容，右=方法。

    rows : [(阶段, 内容, 方法), ...]
    """
    n = len(rows)
    h = n * row_h + (n - 1) * gap + 1.30
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)

    m = 0.30
    cw1, cw3 = 1.15, 1.65
    cw2 = w - 2 * m - cw1 - cw3 - 0.6
    x1 = m + cw1 / 2
    x2 = m + cw1 + 0.3 + cw2 / 2
    x3 = m + cw1 + 0.3 + cw2 + 0.3 + cw3 / 2
    # 表头
    for xc, htxt in [(x1, headers[0]), (x2, headers[1]), (x3, headers[2])]:
        ax.text(xc, ytop - 0.06, htxt, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=EDGE, zorder=5)

    y = ytop - 0.42 - row_h / 2
    prev = None
    for i, (ph, ct, me) in enumerate(rows):
        col = BAND_COLORS[i % len(BAND_COLORS)]
        b1 = box(ax, x1, y, cw1, row_h - 0.06, ph, kind="ghost",
                 fc=col, ec=col, tc="white", fs=fs, bold=True)
        b2 = box(ax, x2, y, cw2, row_h - 0.06, ct, kind="process", fs=fs)
        b3 = box(ax, x3, y, cw3, row_h - 0.06, me, kind="io", fs=fs - 0.2)
        link(ax, b1, "r", b2, "l", color="#B0B7C3", ms=8)
        link(ax, b2, "r", b3, "l", color="#B0B7C3", ms=8)
        if prev is not None:
            link(ax, prev, "b", b1, "t", color="#C9CFD9", ms=8)
        prev = b1
        y -= (row_h + gap)
    return fig


# ===========================================================================
# 8. 泳道图
# ===========================================================================

def swimlane(lanes, title=None, w=7.0, lane_h=0.86, gap=0.24,
             label_w=1.30, fs=8.0):
    """泳道图：每条泳道一个阶段/角色，泳道内步骤自左向右。

    lanes : [(泳道名, [步骤...]), ...]
    """
    n = len(lanes)
    h = n * lane_h + (n - 1) * gap + (1.05 if title else 0.5)
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)

    y = ytop - lane_h / 2
    for i, (name, steps) in enumerate(lanes):
        col = BAND_COLORS[i % len(BAND_COLORS)]
        ax.add_patch(Rectangle((0.22, y - lane_h / 2), w - 0.44, lane_h,
                               facecolor="#FAFBFC", edgecolor="#DDE2E8",
                               linewidth=0.9, zorder=1))
        ax.add_patch(FancyBboxPatch(
            (0.22, y - lane_h / 2), label_w, lane_h,
            boxstyle="round,pad=0,rounding_size=0.08",
            facecolor=col, edgecolor=col, linewidth=0, zorder=2))
        ax.text(0.22 + label_w / 2, y, _wrap(name, 10), ha="center",
                va="center", fontsize=8.4, color="white", fontweight="bold",
                zorder=3)
        k = len(steps)
        if k:
            x0 = 0.22 + label_w + 0.22
            x1 = w - 0.34
            cg = 0.26
            cw = (x1 - x0 - (k - 1) * cg) / k
            prev = None
            for j, s in enumerate(steps):
                xc = x0 + cw / 2 + j * (cw + cg)
                bb = box(ax, xc, y, cw, lane_h - 0.30, s, kind="process",
                         fc="white", ec=col, fs=fs, lw=0.9)
                if prev is not None:
                    link(ax, prev, "r", bb, "l", color=col, ms=8)
                prev = bb
        y -= (lane_h + gap)
    return fig


# ===========================================================================
# 9. 分层架构图
# ===========================================================================

def layered_architecture(layers, title=None, w=5.6, layer_h=0.80, gap=0.46,
                         fs=8.2):
    """分层架构图：自上而下每个层是一个通栏块，层间用双向箭头表示接口。

    layers : [(层名, 说明或子项列表), ...]，自上而下
    """
    n = len(layers)
    h = n * layer_h + (n - 1) * gap + (1.05 if title else 0.5)
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)

    y = ytop - layer_h / 2
    for i, (name, detail) in enumerate(layers):
        col = BAND_COLORS[i % len(BAND_COLORS)]
        box(ax, w / 2, y, w - 0.8, layer_h, "", kind="process",
            fc="white", ec=col, lw=1.3)
        xl = w / 2 - (w - 0.8) / 2 + 0.20
        xr = w / 2 + (w - 0.8) / 2 - 0.20
        ax.text(xl, y, name, ha="left", va="center", fontsize=9.2,
                fontweight="bold", color=_dark(col, 0.82), zorder=5)
        if detail:
            dtxt = detail if isinstance(detail, str) else " · ".join(detail)
            ax.text(xr, y, dtxt, ha="right", va="center", fontsize=7.6,
                    color=EDGE, zorder=5)
        if i < n - 1:
            poly_arrow(ax, [(w / 2, y - layer_h / 2),
                            (w / 2, y - layer_h / 2 - gap)], both=True,
                       color="#B0B7C3", ms=8)
        y -= (layer_h + gap)
    return fig


# ===========================================================================
# 10. 方法映射矩阵（Phase × Method）
# ===========================================================================

def method_mapping(phases, methods, mapping, title=None, w=None,
                   cell=0.52, row_label_w=1.6, fs=8.0):
    """方法映射矩阵：行=阶段，列=方法；mapping[i][j]=True 表示使用。

    mapping : 与 phases 等长的列表，每项是与 methods 等长的 0/1 或布尔列表。
    """
    nr, nc = len(phases), len(methods)
    w = w or (row_label_w + nc * cell + 1.2)
    hh = 0.66 if title else 0.36
    h = hh + 0.55 + nr * cell + 0.30
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)

    x0 = row_label_w + 0.30
    y0 = ytop - 0.55
    # 列表头
    for j, me in enumerate(methods):
        ax.text(x0 + j * cell + cell / 2, y0 + 0.05, _wrap(me, 10),
                ha="center", va="bottom", fontsize=7.4, rotation=0,
                color=EDGE, zorder=5)
    # 单元格
    for i, ph in enumerate(phases):
        yy = y0 - cell / 2 - i * cell
        ax.text(x0 - 0.10, yy, _wrap(ph, 14), ha="right", va="center",
                fontsize=7.8, color=INK, zorder=5)
        for j in range(nc):
            on = bool(mapping[i][j])
            ax.add_patch(Rectangle(
                (x0 + j * cell + 0.02, yy - cell / 2 + 0.02),
                cell - 0.04, cell - 0.04,
                facecolor=BAND_COLORS[j % len(BAND_COLORS)] if on else "#F0F2F5",
                edgecolor="#DDE2E8", linewidth=0.7, zorder=2))
            if on:
                ax.text(x0 + j * cell + cell / 2, yy, "●", ha="center",
                        va="center", fontsize=7.5, color="white", zorder=3)
    return fig


# ===========================================================================
# 11. 问题分解树
# ===========================================================================

def decomposition_tree(root, branches, title=None, w=6.6, bh=0.60,
                       margin=0.40, fs=8.0, level2=True):
    """两级分解树：root → 若干分支，每条分支下可再挂一串子项。

    branches : [branch, ...] 或 [(branch, [sub...]), ...]
    分支中心按画布宽度均匀分布并留边，左右框不会被裁切。
    """
    norm = []
    for b in branches:
        if isinstance(b, (tuple, list)) and len(b) == 2 and isinstance(b[1], (list, tuple)):
            norm.append((b[0], list(b[1])))
        else:
            norm.append((b, []))
    nb = len(norm)
    bwl = min(1.8, (w - 2 * margin - 0.35 * (nb - 1)) / nb)
    span = w - 2 * margin - bwl
    bxs = ([margin + bwl / 2 + i * span / (nb - 1) for i in range(nb)]
           if nb > 1 else [w / 2])
    maxsub = max((len(s) for _, s in norm), default=0)
    sh_ = bh - 0.06
    g_root, g_sub, g_sib = 0.55, 0.30, 0.26
    subsH = (maxsub * sh_ + max(0, maxsub - 1) * g_sib) if (level2 and maxsub) else 0
    title_h = 0.66 if title else 0.10
    Hc = bh + g_root + bh + (g_sub + subsH if subsH else 0)
    h = Hc + title_h + 0.25
    fig, ax = new_canvas(w, h)
    if title:
        ax.text(w / 2, h - 0.26, title, ha="center", va="top", fontsize=10.5,
                fontweight="bold", color=NEAR_BLACK, zorder=6)
    top = h - title_h

    R = box(ax, w / 2, top - bh / 2, min(2.8, w - 1.2), bh, root,
            kind="emphasis", fs=fs + 0.4, bold=True)
    yb = top - bh - g_root - bh / 2
    for i, (name, subs) in enumerate(norm):
        bx = bxs[i]
        col = BAND_COLORS[i % len(BAND_COLORS)]
        bb = box(ax, bx, yb, bwl, bh, name, kind="process",
                 fc="white", ec=col, tc=_dark(col), fs=fs, lw=1.2, bold=True)
        poly_arrow(ax, [R["b"], (bx, yb + bh / 2)], color="#B0B7C3", ms=8)
        if level2 and subs:
            yy = yb - bh / 2 - g_sub - sh_ / 2
            prev = bb
            for s in subs:
                sb = box(ax, bx, yy, bwl, sh_, s, kind="io", fs=fs - 0.5)
                link(ax, prev, "b", sb, "t", color="#CDD3DC", ms=7)
                prev = sb
                yy -= (sh_ + g_sib)
    return fig


# ===========================================================================
# 12. Input → Process → Output 流水线
# ===========================================================================

def ipo_pipeline(inputs, processes, outputs, title=None, w=7.0, bh=0.58,
                 gap=0.22, fs=7.8, headers=("Input", "Process", "Output")):
    """数据/建模流水线：左=输入，中=处理，右=产出，三列各自纵向堆叠。"""
    nrows = max(len(inputs), len(processes), len(outputs))
    colh = nrows * bh + (nrows - 1) * gap
    h = colh + 1.35 + (1.0 if title else 0.4)
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)

    m = 0.35
    cw = (w - 2 * m - 0.9) / 3
    xs = [m + cw / 2, m + cw + 0.45 + cw / 2, m + 2 * (cw + 0.45) + cw / 2]
    cols = [("io", inputs, "#6B6B6B"), ("process", processes, "#3C5488"),
            ("emphasis", outputs, "#B03A2E")]
    col_boxes = []
    for ci, (kind, items, col) in enumerate(cols):
        ax.text(xs[ci], ytop - 0.02, headers[ci], ha="center", va="center",
                fontsize=8.6, fontweight="bold", color=col, zorder=5)
        y = ytop - 0.42 - bh / 2
        blist = []
        for it in items:
            blist.append(box(ax, xs[ci], y, cw, bh, it, kind=kind,
                             fc="white", ec=col, fs=fs, lw=1.1))
            y -= (bh + gap)
        col_boxes.append(blist)
    # 三列之间的箭头（取每列中间行）
    mid = nrows // 2
    for ci in range(2):
        a = col_boxes[ci][min(mid, len(col_boxes[ci]) - 1)]
        b = col_boxes[ci + 1][min(mid, len(col_boxes[ci + 1]) - 1)]
        link(ax, a, "r", b, "l", color="#B0B7C3", ms=10)
    return fig


# ===========================================================================
# 13. 阶段时间轴
# ===========================================================================

def timeline_phases(phases, title=None, w=7.2, bh=0.72, fs=8.0):
    """阶段时间轴：中轴线上标志点，阶段块上下交替，避免拥挤。

    phases : [阶段名, ...] 或 [(阶段名, 说明), ...]
    """
    norm = [(p, None) if isinstance(p, str) else (p[0], p[1]) for p in phases]
    n = len(norm)
    h = 2.30 if not title else 3.05
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)

    yaxis = ytop - 0.95
    m = 0.55
    ax.plot([m, w - m], [yaxis, yaxis], color=EDGE, lw=1.4, zorder=2)
    poly_arrow(ax, [(w - m - 0.05, yaxis), (w - m + 0.30, yaxis)],
               color=EDGE, ms=10)
    bw = min(1.5, (w - 2 * m) / max(1, n) - 0.12)
    span = w - 2 * m - bw
    xs = ([m + bw / 2 + i * span / (n - 1) for i in range(n)]
          if n > 1 else [w / 2])
    for i, (name, detail) in enumerate(norm):
        x = xs[i]
        up = (i % 2 == 0)
        yy = yaxis + 0.42 + bh / 2 if up else yaxis - 0.42 - bh / 2
        col = BAND_COLORS[i % len(BAND_COLORS)]
        ax.add_patch(plt.Circle((x, yaxis), 0.055, color=col, zorder=4))
        bb = box(ax, x, yy, bw, bh,
                 name + (("\n" + detail) if detail else ""),
                 kind="process", fc="white", ec=col, tc=_dark(col), fs=fs,
                 lw=1.2, bold=True)
        stem = {"t": (x, yaxis + 0.06), "b": (x, yaxis - 0.06)}
        link(ax, stem, "t" if up else "b", bb, "b" if up else "t",
             color="#B0B7C3", ms=7)
    return fig


# ===========================================================================
# 14. 问题 → 模型 → 产出 映射图
# ===========================================================================

def problem_model_output(problems, models, outputs, title=None, w=7.0,
                         row_h=0.66, gap=0.34, fs=7.9,
                         headers=("Problem", "Model / Method", "Deliverable")):
    """三列对应关系图：每行把「问题」映射到「模型」再映射到「产出」。"""
    n = max(len(problems), len(models), len(outputs))
    h = n * row_h + (n - 1) * gap + 1.30
    fig, ax = new_canvas(w, h)
    ytop = header(ax, w, h, title)

    m = 0.30
    cw = (w - 2 * m - 1.0) / 3
    xs = [m + cw / 2, m + cw + 0.5 + cw / 2, m + 2 * (cw + 0.5) + cw / 2]
    cols = [("data", problems, "#6A4C93"), ("process", models, "#3C5488"),
            ("emphasis", outputs, "#B03A2E")]
    for ci, (kind, items, col) in enumerate(cols):
        ax.text(xs[ci], ytop - 0.02, headers[ci], ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=col, zorder=5)
    y = ytop - 0.46 - row_h / 2
    for i in range(n):
        cells = []
        for ci, (kind, items, col) in enumerate(cols):
            txt = items[i] if i < len(items) else ""
            cells.append(box(ax, xs[ci], y, cw, row_h - 0.06, txt, kind=kind,
                             fc="white", ec=col, fs=fs, lw=1.1))
        link(ax, cells[0], "r", cells[1], "l", color="#B0B7C3", ms=9)
        link(ax, cells[1], "r", cells[2], "l", color="#B0B7C3", ms=9)
        y -= (row_h + gap)
    return fig


# ===========================================================================
# 示例（生成 14 张演示图）
# ===========================================================================

def _demo(outdir="fc_demo"):
    apply_fc_style()
    print(f"writing demo figures to: {os.path.abspath(outdir)}")

    save_figure(flow_vertical(
        ["Problem statement & goal",
         "Data collection & cleaning",
         "Model construction",
         "Validation & sensitivity",
         "Conclusion & policy"],
        title="(1) Vertical workflow"), "01_vertical", outdir)

    save_figure(flow_horizontal(
        ["Data", "Features", "Model", "Forecast", "Decision"],
        title="(2) Horizontal pipeline"), "02_horizontal", outdir)

    save_figure(flow_snake(
        ["Define scope", "Collect data", "Clean & merge", "EDA",
         "Build model", "Calibrate", "Validate", "Sensitivity",
         "Interpret", "Write up"],
        ncol=4, title="(3) Serpentine flow (long chain)"), "03_snake", outdir)

    save_figure(flow_decision(
        "Estimated\nmedals", "Above\nthreshold?",
        [("Reallocate\nresources", ["Revise training plan", "Seek funding"]),
         ("Expand\nprogram", ["Add coaching staff"])],
        "Final strategy", title="(4) Decision / branch flow"),
        "04_decision", outdir)

    save_figure(flow_iterative(
        ["Initial weights", "Train model", "Evaluate error",
         "Update parameters"],
        title="(5) Iterative loop"), "05_iterative", outdir)

    save_figure(framework_bands([
        ("Problem\n& Goal", ["Predict 2028 medal table", "Explain host effect"]),
        ("Data", ["Medal counts", "Athletes", "Hosts", "Programs"]),
        ("Modeling", ["Recency-weighted average", "Host premium",
                      "Bootstrap interval", "First-medal logistic"]),
        ("Validation", ["Leave-one-Games-out CV", "Calibration check"]),
        ("Conclusion", ["Ranking & policy", "Great-coach recommendation"]),
    ], title="(6) Five-band technical roadmap"), "06_framework_bands", outdir)

    save_figure(framework_three_column([
        ("Phase 1", "Understand data & define metrics", "EDA, descriptive stats"),
        ("Phase 2", "Forecast medal counts", "EWMA + host premium"),
        ("Phase 3", "Model first-medal events", "Logistic + Poisson"),
        ("Phase 4", "Validate & stress-test", "CV, bootstrap, sensitivity"),
    ], title="(7) Three-column framework"), "07_three_column", outdir)

    save_figure(swimlane([
        ("Data", ["Collect", "Clean", "Merge"]),
        ("Model", ["Baseline", "Adjust", "Calibrate"]),
        ("Validate", ["Cross-validate", "Diagnose"]),
        ("Report", ["Visualize", "Summarize"]),
    ], title="(8) Swimlane diagram"), "08_swimlane", outdir)

    save_figure(layered_architecture([
        ("Decision layer", "ranking, policy"),
        ("Ensemble layer", "EWMA + logistic + Poisson"),
        ("Feature layer", "medals, hosts, events, GDP"),
        ("Data layer", "5 official CSV files"),
    ], title="(9) Layered architecture"), "09_layered", outdir)

    save_figure(method_mapping(
        ["Problem 1", "Problem 2", "Problem 3", "Problem 4"],
        ["EWMA", "Host adj.", "Bootstrap", "Logistic", "Step change"],
        [[1, 1, 1, 0, 0],
         [1, 0, 0, 0, 0],
         [1, 0, 1, 1, 0],
         [1, 0, 0, 0, 1]],
        title="(10) Phase x method mapping"), "10_method_mapping", outdir)

    save_figure(decomposition_tree(
        "Olympic medal dynamics",
        [("Prediction", ["EWMA", "Host premium"]),
         ("Explanatory", ["Event growth", "Inclusivity"]),
         ("Structural", ["First medals", "Great coach"])],
        title="(11) Problem decomposition tree"), "11_tree", outdir)

    save_figure(ipo_pipeline(
        ["Medal counts", "Athletes", "Hosts", "Programs"],
        ["Clean & consolidate", "Weight recent Games",
         "Adjust host effect", "Calibrate probabilities"],
        ["2028 forecast", "Ranking table", "Policy advice"],
        title="(12) Input-Process-Output pipeline"), "12_ipo", outdir)

    save_figure(timeline_phases([
        ("Phase 1", "Data prep"), ("Phase 2", "Modeling"),
        ("Phase 3", "Validation"), ("Phase 4", "Reporting"),
    ], title="(13) Phase timeline"), "13_timeline", outdir)

    save_figure(problem_model_output(
        ["Forecast medals", "Explaining events", "First medals", "Coach effect"],
        ["EWMA + host premium", "Sport decomposition",
         "Logistic + Poisson", "Step-change test"],
        ["2028 table + PI", "Coefficients", "New-medal list", "Recommendations"],
        title="(14) Problem-Model-Deliverable map"), "14_pmo", outdir)

    print("\nAll 14 flowchart demos written.")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "fc_demo"
    _demo(out)
