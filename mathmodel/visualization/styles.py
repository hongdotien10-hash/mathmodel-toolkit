"""国赛论文可视化风格 — 对标优秀论文标准"""

from typing import Optional

# 国赛调色板 — 颜色鲜艳、可灰度区分、色盲友好
PALETTES = {
    "default":  ["#D62728", "#1F77B4", "#2CA02C", "#FF7F0E", "#9467BD",
                 "#8C564B", "#E377C2", "#17BECF", "#BCBD22", "#7F7F7F"],
    "cool":     ["#1F77B4", "#2CA02C", "#17BECF", "#9467BD"],
    "warm":     ["#D62728", "#FF7F0E", "#E377C2", "#8C564B"],
    "contrast": ["#D62728", "#1F77B4", "#FF7F0E", "#2CA02C"],
}

# 国赛标准：150dpi，无标题，despine
DEFAULT_STYLE = {
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.08,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "grid.alpha": 0.25,
    "grid.linestyle": ":",
    "axes.grid": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
}

CN_FONT_SANS = ["SimHei", "Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Micro Hei"]
CN_FONT_SERIF = ["SimSun", "Noto Serif CJK SC"]


def set_style(language: str = "zh", palette: str = "default"):
    """设置国赛图表全局样式"""
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    for k, v in DEFAULT_STYLE.items():
        mpl.rcParams[k] = v

    if language == "zh":
        _configure_cn_fonts()

    colors = PALETTES.get(palette, PALETTES["default"])
    mpl.rcParams["axes.prop_cycle"] = plt.cycler(color=colors)


def _configure_cn_fonts():
    import matplotlib as mpl
    import matplotlib.font_manager as fm

    available = {f.name for f in fm.fontManager.ttflist}
    sans = next((n for n in CN_FONT_SANS if n in available), None)
    if sans:
        mpl.rcParams["font.family"] = "sans-serif"
        mpl.rcParams["font.sans-serif"] = [sans, "DejaVu Sans"]
    mpl.rcParams["axes.unicode_minus"] = False


def despine(ax):
    """去除顶部和右侧边框 — 国赛标配"""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def get_colors(n: int, palette: str = "default"):
    """获取 n 个颜色"""
    return PALETTES.get(palette, PALETTES["default"])[:n]
