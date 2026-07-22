"""论文可视化风格配置。

提供统一的图表风格，支持中英文字体适配。
"""

from typing import Optional


# ---- 调色板 ---------------------------------------------------------------

# 学术风格配色（Nature/AAAS 风格，色盲友好）
PALETTES = {
    "default": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"],
    "warm": ["#D62728", "#FF7F0E", "#E377C2", "#8C564B"],
    "cool": ["#1F77B4", "#2CA02C", "#17BECF", "#9467BD"],
    "greyscale": ["#333333", "#666666", "#999999", "#BBBBBB", "#DDDDDD"],
}

# 默认样式参数
DEFAULT_STYLE = {
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "axes.linewidth": 1.0,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "grid.alpha": 0.3,
    "axes.grid": True,
    "grid.linestyle": "--",
}

# 中文字体回退链
CN_FONT_SANS = ["SimHei", "Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Micro Hei", "Arial Unicode MS"]
CN_FONT_SERIF = ["SimSun", "Noto Serif CJK SC", "STSong"]
CN_FONT_MONO = ["SimHei", "Microsoft YaHei"]


def set_style(language: str = "zh", palette: str = "default") -> None:
    """设置全局图表样式。

    Args:
        language: 'zh' 中文 或 'en' 英文
        palette: 调色板名称
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib as mpl
    except ImportError:
        return

    # 基础样式
    for key, value in DEFAULT_STYLE.items():
        mpl.rcParams[key] = value

    # 字体配置
    if language == "zh":
        _configure_cn_fonts()
    else:
        mpl.rcParams["font.family"] = "sans-serif"
        mpl.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]

    # 调色板
    colors = PALETTES.get(palette, PALETTES["default"])
    mpl.rcParams["axes.prop_cycle"] = plt.cycler(color=colors)


def _configure_cn_fonts() -> None:
    """配置中文字体。"""
    import matplotlib as mpl
    import matplotlib.font_manager as fm

    available = {f.name for f in fm.fontManager.ttflist}

    # 按优先级查找可用中文字体
    sans = None
    for name in CN_FONT_SANS:
        if name in available:
            sans = name
            break

    if sans:
        mpl.rcParams["font.family"] = "sans-serif"
        mpl.rcParams["font.sans-serif"] = [sans, "DejaVu Sans"]
    else:
        mpl.rcParams["font.family"] = "sans-serif"

    # 负号显示
    mpl.rcParams["axes.unicode_minus"] = False


def get_style() -> dict:
    """获取当前样式配置。"""
    try:
        import matplotlib as mpl
        return {k: mpl.rcParams.get(k) for k in DEFAULT_STYLE}
    except ImportError:
        return dict(DEFAULT_STYLE)
