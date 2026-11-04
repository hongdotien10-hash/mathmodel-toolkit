#!/usr/bin/env python3
"""journalplot skill 的自包含脚本：期刊/论文图表规范应用与投稿前检查。

不依赖 pip 安装，只需要 matplotlib（检查位图时额外需要 Pillow）。

面向两类场景：
  数模竞赛  —— 快速出图、全篇风格统一、直接插 Word
  科研投稿  —— 逐项核对目标期刊规范

用法：
    python journal_fig.py presets
    python journal_fig.py apply cumcm
    python journal_fig.py template dual-axis
    python journal_fig.py check fig.pdf fig.png --preset ieee
    python journal_fig.py batch ./figs --preset cumcm
    python journal_fig.py consistency ./figs
    python journal_fig.py doctor
    python journal_fig.py check-text --preset cumcm "负荷 (kW)" "Time (h)"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BASE_RC = {
    "figure.dpi": 120,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "axes.axisbelow": True,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "legend.frameon": False,
    "axes.grid": False,
}

STYLES = {
    "ieee": {
        "label": "IEEE (journal / conference, two-column)",
        "single_in": 3.5,
        "double_in": 7.16,
        "min_text_pt": 8.0,
        "rc": {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.5,
            "lines.markersize": 4,
            "patch.linewidth": 0.8,
            "grid.linewidth": 0.5,
        },
    },
    "elsevier": {
        "label": "Elsevier (single column 90 mm)",
        "single_in": 3.54,
        "double_in": 7.48,
        "min_text_pt": 7.0,
        "rc": {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.3,
            "lines.markersize": 3.5,
            "patch.linewidth": 0.7,
            "grid.linewidth": 0.5,
        },
    },
    "cn-journal": {
        "label": "Chinese journal (学报 / 中文核心)",
        "single_in": 2.95,
        "double_in": 5.91,
        "min_text_pt": 7.5,
        "rc": {
            "font.family": "sans-serif",
            # 宋体必须排第一。matplotlib 不做单字形跨字体回退，
            # 反过来写 ['Times New Roman', 'SimSun'] 会让中文全变豆腐块。
            "font.sans-serif": ["SimSun", "STSong", "DejaVu Sans"],
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.5,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.3,
            "lines.markersize": 3.5,
            "patch.linewidth": 0.7,
            "grid.linewidth": 0.5,
            "axes.unicode_minus": False,
        },
    },
    "cumcm": {
        "label": "数学建模竞赛论文 (国赛 / 美赛, Word 排版)",
        "single_in": 2.95,
        "double_in": 5.91,
        "min_text_pt": 8.0,
        "rc": {
            "font.family": "sans-serif",
            "font.sans-serif": ["SimSun", "STSong", "DejaVu Sans"],
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.6,
            "lines.markersize": 4.5,
            "patch.linewidth": 0.8,
            "grid.linewidth": 0.5,
            "grid.alpha": 0.3,
            "axes.grid": True,
            "axes.unicode_minus": False,
            # 论文要插进 Word：300dpi 的 PNG 足够清晰，
            # 600dpi 会让整篇论文膨胀到几十 MB，评委打开就卡。
            "savefig.dpi": 300,
            "savefig.format": "png",
            # 不用 bbox='tight'：它按内容裁剪，每张图会得到不同宽度，
            # 插进 Word 同一栏里参差不齐。数模论文要求图宽一致。
            "savefig.bbox": "standard",
        },
    },
}

OKABE_ITO = [
    "#0072B2", "#D55E00", "#009E73", "#CC79A7",
    "#E69F00", "#56B4E9", "#F0E442", "#000000",
]

_MISSING_GLYPH = re.compile(r"Glyph \d+ \(\\N\{([^}]+)\}\) missing from")
_PDF_IMAGE = re.compile(rb"/Subtype\s*/Image\b")
_PDF_FONTFILE = re.compile(rb"/FontFile\d?\b")
_PDF_MEDIABOX = re.compile(
    rb"/MediaBox\s*\[\s*(-?[\d.]+)\s+(-?[\d.]+)\s*(-?[\d.]+)\s+(-?[\d.]+)\s*\]"
)

IMG_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".pdf", ".eps"}


def build_rc(preset: str, width: str = "single") -> dict:
    if preset not in STYLES:
        raise KeyError(f"unknown preset {preset!r}; available: {', '.join(STYLES)}")
    style = STYLES[preset]
    rc = dict(BASE_RC)
    rc.update(style["rc"])
    from cycler import cycler

    rc["axes.prop_cycle"] = cycler(color=OKABE_ITO)
    w = style["double_in"] if width == "double" else style["single_in"]
    rc["figure.figsize"] = (w, round(w * 0.62, 2))
    return rc


def apply_style(preset: str, width: str = "single") -> dict:
    """在调用方的 matplotlib 上应用预设，返回实际生效的 rc。"""
    import matplotlib as mpl

    rc = build_rc(preset, width)
    mpl.rcParams.update(rc)
    return rc


def _target_mm(preset: str, width: str = "single") -> float:
    style = STYLES[preset]
    return (style["double_in"] if width == "double" else style["single_in"]) * 25.4


def _scale_hint(preset: str, width: str) -> str:
    other = "double" if width == "single" else "single"
    return (f" If this figure is meant to span {other}-column width, pass "
            f"--width {other} before treating this as a defect.")


def _size_verdict(name: str, mm_w: float, preset: str, width: str) -> dict:
    """把图的物理宽度与目标栏宽比对：过窄和过宽都会改变图内字号。"""
    target_mm = _target_mm(preset, width)
    base_pt = STYLES[preset]["rc"].get("font.size", 9)
    if mm_w < target_mm * 0.95:
        return {
            "level": "warn", "code": "size-narrow",
            "msg": f"{name} width {mm_w:.1f} mm vs {preset} {width} column "
                   f"{target_mm:.0f} mm; narrower than the column — usually tight bbox "
                   f"trimming or authoring at a smaller size. It will be scaled up on "
                   f"placement, changing text size (and dropping effective dpi for "
                   f"rasters). Author at the column width.{_scale_hint(preset, width)}",
        }
    if mm_w > target_mm * 1.15:
        scale = target_mm / mm_w
        return {
            "level": "warn", "code": "size-wide",
            "msg": f"{name} width {mm_w:.1f} mm vs {preset} {width} column "
                   f"{target_mm:.0f} mm; will be scaled to {scale * 100:.0f}% on "
                   f"placement, so {base_pt} pt text becomes {base_pt * scale:.1f} pt "
                   f"— the most common 'text too small' rejection.{_scale_hint(preset, width)}",
        }
    return {
        "level": "pass", "code": "size-ok",
        "msg": f"{name} width {mm_w:.1f} mm vs {preset} {width} column "
               f"{target_mm:.0f} mm",
    }


def _font_chain(style: dict) -> list[str]:
    rc = style["rc"]
    family = rc.get("font.family", "sans-serif")
    key = "font.serif" if family == "serif" else "font.sans-serif"
    return list(rc.get(key) or [])


def doctor(preset: str | None = None, available: set[str] | None = None) -> list[dict]:
    """检查预设要求的字体在本机是否真的存在。"""
    if available is None:
        from matplotlib import font_manager as fm

        available = {f.name for f in fm.fontManager.ttflist}

    out = []
    for name in ([preset] if preset else sorted(STYLES)):
        if name not in STYLES:
            out.append({"level": "error", "code": "unknown-preset",
                        "msg": f"unknown preset {name!r}"})
            continue
        chain = _font_chain(STYLES[name])
        first = chain[0] if chain else None
        if first and first in available:
            out.append({"level": "pass", "code": "font-ok",
                        "msg": f"[{name}] first font {first!r} available"})
            continue
        fallback = next((f for f in chain if f in available), None)
        if fallback:
            out.append({
                "level": "warn", "code": "font-missing",
                "msg": f"[{name}] {first!r} missing on this machine, falls back to "
                       f"{fallback!r} — the figure will not match the spec",
            })
        else:
            out.append({
                "level": "error", "code": "font-missing",
                "msg": f"[{name}] none of {chain} exist here; falls back to the "
                       f"matplotlib default, so the preset is a no-op",
            })
    return out


def check_text(*texts: str) -> list[dict]:
    """渲染一遍给定文字，报告缺字形（豆腐块）。"""
    import warnings

    import matplotlib.pyplot as plt

    if not texts:
        return [{"level": "warn", "code": "no-input", "msg": "no text given"}]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.axis("off")
        for i, t in enumerate(texts):
            ax.text(0.01, 0.9 - 0.25 * (i % 4), t, fontsize=12, transform=ax.transAxes)
        fig.canvas.draw()
        plt.close(fig)

    seen, out = set(), []
    for w in caught:
        m = _MISSING_GLYPH.search(str(w.message))
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        name = m.group(1)
        if name.startswith("CJK"):
            advice = "Put a CJK-capable font first in font.sans-serif."
        elif name == "MINUS SIGN":
            advice = ("Replace the U+2212 character in the string with an ASCII "
                      "hyphen, or pick a font that contains U+2212 "
                      "(axes.unicode_minus only affects tick labels, not literal text).")
        else:
            advice = ("Switch to a font that contains this glyph, or replace the "
                      "character in the label.")
        out.append({
            "level": "error", "code": "missing-glyph",
            "msg": f"glyph {name!r} missing from the active font -> renders as an "
                   f"empty box. {advice}",
        })
    if not out:
        out.append({"level": "pass", "code": "text-ok",
                    "msg": f"all {len(texts)} strings render without missing glyphs"})
    return out


def check_file(path: str, preset: str | None = None, min_dpi: float = 300.0,
               width: str = "single") -> list[dict]:
    p = Path(path)
    if not p.exists():
        return [{"level": "error", "code": "not-found", "msg": f"file not found: {p}"}]
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return _check_pdf(p, preset, width)
    if suffix in {".png", ".tif", ".tiff", ".jpg", ".jpeg", ".bmp"}:
        return _check_raster(p, min_dpi, preset, width)
    if suffix == ".eps":
        return [{"level": "pass", "code": "vector",
                 "msg": f"{p.name} is EPS vector, preferred for submission"}]
    return [{"level": "warn", "code": "unsupported", "msg": f"cannot inspect .{suffix}"}]


def image_info(path: str) -> dict | None:
    """读取图片的 DPI / 物理尺寸 / 是否矢量，供一致性检查使用。"""
    p = Path(path)
    if not p.exists():
        return None
    if p.suffix.lower() in {".pdf", ".eps"}:
        return {"name": p.name, "kind": "vector", "dpi": None,
                "width_mm": None, "height_mm": None}
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(p) as im:
            dpi = im.info.get("dpi")
            w_px, h_px = im.size
    except Exception:
        return None
    if not dpi:
        return {"name": p.name, "kind": "raster", "dpi": None,
                "width_mm": None, "height_mm": None}
    dpi_x = float(dpi[0]) if isinstance(dpi, tuple) else float(dpi)
    return {"name": p.name, "kind": "raster", "dpi": round(dpi_x),
            "width_mm": round(w_px / dpi_x * 25.4, 1),
            "height_mm": round(h_px / dpi_x * 25.4, 1)}


def _check_raster(p: Path, min_dpi: float, preset: str | None = None,
                  width: str = "single") -> list[dict]:
    try:
        from PIL import Image
    except ImportError:
        return [{"level": "warn", "code": "no-pillow",
                 "msg": "Pillow not installed, cannot read DPI/size"}]

    out = []
    with Image.open(p) as im:
        dpi = im.info.get("dpi")
        w_px, h_px = im.size
    if not dpi:
        return [{"level": "warn", "code": "dpi-unknown",
                 "msg": f"{p.name} has no DPI metadata; journals and Word may assume 72dpi"}]
    dpi_x = float(dpi[0]) if isinstance(dpi, tuple) else float(dpi)

    # PNG stores DPI as integer pixels-per-metre, so 300dpi reads back as
    # 299.9997 and a strict >= comparison fails on an exact threshold.
    dpi_ok = dpi_x >= min_dpi - 0.5
    out.append({
        "level": "pass" if dpi_ok else "warn",
        "code": "dpi-ok" if dpi_ok else "dpi-low",
        "msg": f"{p.name} DPI={dpi_x:.0f} (min {min_dpi:.0f})",
    })

    mm_w, mm_h = w_px / dpi_x * 25.4, h_px / dpi_x * 25.4
    if preset in STYLES:
        out.append(_size_verdict(p.name, mm_w, preset, width))
    else:
        ok = min(mm_w, mm_h) >= 45
        out.append({
            "level": "pass" if ok else "warn",
            "code": "size-ok" if ok else "size-small",
            "msg": f"{p.name} physical size {mm_w:.1f} x {mm_h:.1f} mm",
        })
    return out


def _pdf_width_mm(raw: bytes) -> float | None:
    """从第一页 MediaBox 读取物理宽度（pt -> mm）。"""
    m = _PDF_MEDIABOX.search(raw)
    if not m:
        return None
    x0, _, x1, _ = (float(g) for g in m.groups())
    return (x1 - x0) * 25.4 / 72.0


def _check_pdf(p: Path, preset: str | None = None,
               width: str = "single") -> list[dict]:
    raw = p.read_bytes()
    if not raw.startswith(b"%PDF"):
        return [{"level": "error", "code": "bad-pdf", "msg": f"{p.name} is not a valid PDF"}]

    out = []
    if b"/CharProcs" in raw:
        out.append({"level": "pass", "code": "font-embedded",
                    "msg": f"{p.name} fonts embedded (Type3)"})
    elif _PDF_FONTFILE.search(raw):
        out.append({"level": "pass", "code": "font-embedded",
                    "msg": f"{p.name} fonts embedded (TrueType)"})
    else:
        out.append({"level": "warn", "code": "font-missing",
                    "msg": f"{p.name} no embedded font detected; text may be substituted "
                           f"at the editor. Set pdf.fonttype=42 or keep the default 3."})

    # matplotlib always writes /ProcSet [/ImageB /ImageC] — a declaration, not an
    # image. Only /Subtype /Image is a real raster object.
    n = len(_PDF_IMAGE.findall(raw))
    if n:
        out.append({"level": "warn", "code": "raster-in-pdf",
                    "msg": f"{p.name} contains {n} raster object(s)"})
    else:
        out.append({"level": "pass", "code": "vector", "msg": f"{p.name} fully vector"})

    if preset in STYLES:
        w_mm = _pdf_width_mm(raw)
        if w_mm:
            out.append(_size_verdict(p.name, w_mm, preset, width))
        else:
            out.append({"level": "warn", "code": "size-unknown",
                        "msg": f"{p.name} MediaBox not readable; physical width not checked"})
    return out


def _collect_images(target: str) -> list[Path]:
    p = Path(target)
    if p.is_file():
        return [p]
    if not p.is_dir():
        return []
    return sorted(x for x in p.rglob("*") if x.suffix.lower() in IMG_EXTS)


def batch_check(target: str, preset: str | None = None,
                min_dpi: float = 300.0,
                width: str = "single") -> tuple[list[dict], int]:
    """批量检查一个目录下的所有图片，按问题类型汇总。"""
    files = _collect_images(target)
    rows: list[dict] = []
    for f in files:
        for r in check_file(str(f), preset, min_dpi, width):
            rows.append({**r, "file": f.name})
    return rows, len(files)


def consistency(target: str) -> list[dict]:
    """检查一组图是否风格一致：DPI 统一、宽度统一、矢量与位图不混用。"""
    files = _collect_images(target)
    if not files:
        return [{"level": "warn", "code": "no-files", "msg": f"no images under {target}"}]

    infos = [i for i in (image_info(str(f)) for f in files) if i]
    if not infos:
        return [{"level": "warn", "code": "no-files", "msg": "could not read any image"}]

    out: list[dict] = []

    kinds = {i["kind"] for i in infos}
    if len(kinds) > 1:
        vec = sum(1 for i in infos if i["kind"] == "vector")
        ras = len(infos) - vec
        out.append({
            "level": "warn", "code": "mixed-format",
            "msg": f"vector and raster figures are mixed (vector {vec}, raster {ras}) "
                   f"— the paper will look inconsistent",
        })
    else:
        out.append({"level": "pass", "code": "format-consistent",
                    "msg": f"all {len(infos)} figures are {infos[0]['kind']}"})

    dpis = sorted({i["dpi"] for i in infos if i["dpi"]})
    if len(dpis) > 1:
        detail = ", ".join(
            f"{d}dpi x{sum(1 for i in infos if i['dpi'] == d)}" for d in dpis
        )
        out.append({"level": "warn", "code": "dpi-inconsistent",
                    "msg": f"DPI differs across figures ({detail})"})
    elif dpis:
        out.append({"level": "pass", "code": "dpi-consistent",
                    "msg": f"all figures at {dpis[0]}dpi"})

    widths = [i for i in infos if i["width_mm"]]
    if widths:
        groups: dict[int, list[str]] = {}
        for i in widths:
            groups.setdefault(round(i["width_mm"]), []).append(i["name"])
        if len(groups) <= 2:
            detail = ", ".join(f"{w}mm x{len(n)}" for w, n in sorted(groups.items()))
            out.append({"level": "pass", "code": "width-consistent",
                        "msg": f"widths fall into {len(groups)} group(s): {detail}"})
        else:
            detail = ", ".join(f"{w}mm" for w in sorted(groups))
            out.append({
                "level": "warn", "code": "width-inconsistent",
                "msg": f"{len(groups)} distinct widths ({detail}). "
                       f"savefig.bbox='tight' crops each figure to its content, so figures "
                       f"placed in the same column end up ragged. Set "
                       f"savefig.bbox='standard' (or a fixed figsize) when the figures must "
                       f"line up in Word.",
            })
    return out


TEMPLATES = {
    "dual-axis": (
        "双轴折线（负荷 + SOC，数模最高频）",
        '''import numpy as np
import matplotlib.pyplot as plt

t = np.linspace(0, 24, 96)
load = 1.6 + 0.9 * np.sin((t - 8) / 24 * 2 * np.pi)
soc = 0.5 + 0.32 * np.sin((t - 6) / 24 * 2 * np.pi)

fig, ax = plt.subplots()
ax.plot(t, load, label="负荷")
ax.set_xlabel("时刻 (h)")
ax.set_ylabel("功率 (kW)")

ax2 = ax.twinx()
ax2.plot(t, soc, ls="--", label="电池 SOC")
ax2.set_ylabel("SOC")

# 纵轴下沿留出空白带，图例才能落在没有曲线的地方。
ax.set_ylim(0.3, 2.7)
ax2.set_ylim(0.05, 0.92)

h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="lower center", ncol=2,
          frameon=True, facecolor="white", edgecolor="none", framealpha=0.9)

fig.tight_layout()
fig.savefig("fig-dual.png")
'''),
    "bar-line": (
        "柱状 + 折线（方案对比 + 趋势）",
        '''import numpy as np
import matplotlib.pyplot as plt

x = np.arange(5)
cost = [12, 18, 15, 22, 19]
eff = [0.62, 0.71, 0.66, 0.80, 0.75]

fig, ax = plt.subplots()
ax.bar(x, cost, width=0.55, label="成本")
ax.set_xticks(x)
ax.set_xticklabels(["方案A", "方案B", "方案C", "方案D", "方案E"])
ax.set_ylabel("成本 (万元)")

ax2 = ax.twinx()
ax2.plot(x, eff, "o-", label="效率")
ax2.set_ylabel("效率")

h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper left", ncol=2,
          frameon=True, facecolor="white", edgecolor="none", framealpha=0.9)

fig.tight_layout()
fig.savefig("fig-barline.png")
'''),
    "band": (
        "带置信区间的折线（预测 + 误差带）",
        '''import numpy as np
import matplotlib.pyplot as plt

t = np.linspace(0, 24, 96)
mu = 1.6 + 0.9 * np.sin((t - 8) / 24 * 2 * np.pi)
sd = 0.15 + 0.05 * np.cos(t / 24 * 2 * np.pi)

fig, ax = plt.subplots()
ax.fill_between(t, mu - sd, mu + sd, alpha=0.25, linewidth=0, label="95% 置信区间")
ax.plot(t, mu, label="预测值")
ax.set_xlabel("时刻 (h)")
ax.set_ylabel("功率 (kW)")
ax.legend(loc="upper left")

fig.tight_layout()
fig.savefig("fig-band.png")
'''),
    "heatmap": (
        "相关性热力图",
        '''import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(0)
m = rng.uniform(-1, 1, (5, 5))
m = (m + m.T) / 2
np.fill_diagonal(m, 1.0)
labels = ["负荷", "光伏", "电价", "温度", "SOC"]

fig, ax = plt.subplots()
im = ax.imshow(m, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45, ha="right")
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels)
fig.colorbar(im, ax=ax, shrink=0.85, label="相关系数")

fig.tight_layout()
fig.savefig("fig-heat.png")
'''),
    "subplots": (
        "2x2 子图（多指标并列）",
        '''import numpy as np
import matplotlib.pyplot as plt

t = np.linspace(0, 24, 96)
series = {
    "负荷 (kW)": 1.6 + 0.9 * np.sin((t - 8) / 24 * 2 * np.pi),
    "光伏 (kW)": 2.4 * np.clip(np.sin((t - 7) / 12 * np.pi), 0, None),
    "电价 (元)": 0.5 + 0.3 * np.sin((t - 10) / 24 * 2 * np.pi),
    "SOC": 0.5 + 0.32 * np.sin((t - 6) / 24 * 2 * np.pi),
}

fig, axes = plt.subplots(2, 2, figsize=(5.91, 4.4))
for ax, (label, y) in zip(axes.ravel(), series.items()):
    ax.plot(t, y)
    ax.set_xlabel("时刻 (h)")
    ax.set_ylabel(label)

fig.tight_layout()
fig.savefig("fig-subplots.png")
'''),
}


def _print(rows: list[dict]) -> int:
    bad = 0
    for r in rows:
        mark = {"pass": "  ok  ", "warn": "  !   ", "error": "  x   "}[r["level"]]
        print(f"{mark} {r['msg']}")
        bad += r["level"] != "pass"
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="journal_fig")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("presets")

    p = sub.add_parser("apply")
    p.add_argument("preset", nargs="?", default="ieee")
    p.add_argument("--width", choices=["single", "double"], default="single")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("template")
    p.add_argument("name", nargs="?", default=None)

    p = sub.add_parser("check")
    p.add_argument("files", nargs="+")
    p.add_argument("--preset", default=None)
    p.add_argument("--width", choices=["single", "double"], default="single")
    p.add_argument("--min-dpi", type=float, default=300.0)

    p = sub.add_parser("batch")
    p.add_argument("target")
    p.add_argument("--preset", default=None)
    p.add_argument("--width", choices=["single", "double"], default="single")
    p.add_argument("--min-dpi", type=float, default=300.0)

    p = sub.add_parser("consistency")
    p.add_argument("target")

    p = sub.add_parser("doctor")
    p.add_argument("--preset", default=None)

    p = sub.add_parser("check-text")
    p.add_argument("texts", nargs="+")
    p.add_argument("--preset", default=None,
                   help="apply a preset's font chain before testing glyphs")
    p.add_argument("--width", choices=["single", "double"], default="single")

    args = ap.parse_args(argv)

    if args.cmd == "presets":
        for name, s in STYLES.items():
            print(f"{name:<12} {s['label']}")
            print(f"{'':<12} single {s['single_in']}in / {s['single_in']*25.4:.0f}mm   "
                  f"double {s['double_in']}in / {s['double_in']*25.4:.0f}mm   "
                  f"min text {s['min_text_pt']}pt")
        return 0

    if args.cmd == "template":
        if args.name is None:
            for k, (desc, _) in TEMPLATES.items():
                print(f"{k:<12} {desc}")
            return 0
        if args.name not in TEMPLATES:
            print(f"unknown template {args.name!r}; available: {', '.join(TEMPLATES)}",
                  file=sys.stderr)
            return 2
        desc, code = TEMPLATES[args.name]
        print(f"# {desc}")
        print(code)
        return 0

    if args.cmd == "apply":
        rc = build_rc(args.preset, args.width)
        if args.json:
            payload = {k: v for k, v in rc.items() if not k.startswith("_")}
            payload["axes.prop_cycle"] = OKABE_ITO
            print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        else:
            w, h = rc["figure.figsize"]
            print(f"# {args.preset} / {args.width}: figsize=({w:.2f}, {h:.2f}) in "
                  f"= {w*25.4:.1f} x {h*25.4:.1f} mm")
            print("from cycler import cycler")
            print("import matplotlib as mpl")
            print("mpl.rcParams.update({")
            for k, v in rc.items():
                if k == "axes.prop_cycle":
                    print(f'    "{k}": cycler(color={OKABE_ITO}),')
                else:
                    print(f'    "{k}": {v!r},')
            print("})")
        return 0

    if args.cmd == "doctor":
        return 1 if _print(doctor(args.preset)) else 0

    if args.cmd == "check-text":
        if args.preset:
            if args.preset not in STYLES:
                print(f"unknown preset {args.preset!r}; available: {', '.join(STYLES)}",
                      file=sys.stderr)
                return 2
            apply_style(args.preset, args.width)
        return 1 if _print(check_text(*args.texts)) else 0

    if args.cmd == "check":
        bad = 0
        for f in args.files:
            print(f"\n{f}")
            bad += _print(check_file(f, args.preset, args.min_dpi, args.width))
        return 1 if bad else 0

    if args.cmd == "batch":
        rows, n = batch_check(args.target, args.preset, args.min_dpi, args.width)
        print(f"扫描 {n} 个文件\n")
        bad = _print([r for r in rows if r["level"] != "pass"])
        if not bad:
            print("  全部通过")
            return 0
        groups: dict[str, list[str]] = {}
        for r in rows:
            if r["level"] != "pass":
                groups.setdefault(r["code"], []).append(r["file"])
        print("\n按问题汇总：")
        for code, names in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            print(f"  {code:<18} {len(names)} 个：{', '.join(sorted(set(names)))}")
        return 1

    if args.cmd == "consistency":
        return 1 if _print(consistency(args.target)) else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
