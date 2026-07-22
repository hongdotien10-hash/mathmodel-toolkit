"""流水线配置管理。

提供全局配置类，控制流水线各阶段的行为参数。
支持从 YAML/JSON 文件加载配置。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Literal, Optional


@dataclass
class PipelineConfig:
    """数学建模流水线全局配置。

    Attributes:
        auto_select_model: 是否自动选择模型（False 时每个子问题会请求用户确认）
        engine: 论文排版引擎，latex 或 typst
        contest_type: 比赛类型，cumcm（国赛）或 mcm（美赛），auto 为自动检测
        output_dir: 输出目录
        figures_dir: 图表输出子目录
        random_seed: 全局随机种子
        language: 论文语言，zh 为中文，en 为英文
        timeout_per_stage: 每个阶段的最大执行时间（秒），0 表示无限制
        save_intermediate: 是否保存所有中间结果（代码、数据、日志）
        verbose: 详细输出模式
        matlab_fallback: Python 求解失败时是否尝试 MATLAB
        data_preview_rows: 数据预览时显示的行数
        figure_dpi: 图表 DPI
        figure_format: 图表格式（pdf 用于 LaTeX，png 用于 Typst）
    """

    # ---- 核心选项 -----------------------------------------------------------
    auto_select_model: bool = True
    engine: Literal["latex", "typst"] = "latex"
    contest_type: Literal["auto", "cumcm", "mcm"] = "auto"
    language: Literal["zh", "en"] = "zh"

    # ---- 路径 ---------------------------------------------------------------
    output_dir: str = "./output"
    figures_dir: str = "figures"
    templates_dir: Optional[str] = None  # None 表示使用内置模板

    # ---- 执行控制 -----------------------------------------------------------
    random_seed: int = 42
    timeout_per_stage: int = 600  # 10 分钟
    save_intermediate: bool = True
    verbose: bool = True
    matlab_fallback: bool = False

    # ---- 数据预览 -----------------------------------------------------------
    data_preview_rows: int = 10

    # ---- 可视化 -------------------------------------------------------------
    figure_dpi: int = 300
    figure_format: Literal["pdf", "png", "svg"] = "pdf"

    # ---- 模型推荐 -----------------------------------------------------------
    top_k_models: int = 3  # 推荐的前 K 个模型方案
    recommend_min_confidence: float = 0.3  # 最低推荐置信度

    # ---- 论文生成 -----------------------------------------------------------
    paper_max_pages: int = 30  # 论文最大页数（用于检查）

    # =====================================================================
    # Factory & I/O
    # =====================================================================

    @classmethod
    def from_file(cls, path: str | Path) -> "PipelineConfig":
        """从 YAML 或 JSON 文件加载配置。

        Args:
            path: 配置文件路径

        Returns:
            PipelineConfig 实例
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                try:
                    import yaml
                    data = yaml.safe_load(f) or {}
                except ImportError:
                    raise ImportError("读取 YAML 需要安装 PyYAML: pip install pyyaml")
            elif path.suffix == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"不支持的配置格式: {path.suffix}，请使用 .yaml / .json")

        # 过滤掉 dataclass 中没有的字段
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def to_file(self, path: str | Path) -> None:
        """保存配置到文件。"""
        path = Path(path)
        data = {f.name: getattr(self, f.name) for f in fields(self)}
        with open(path, "w", encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                try:
                    import yaml
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
                except ImportError:
                    raise ImportError("写入 YAML 需要安装 PyYAML")
            else:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def ensure_output_dirs(self) -> tuple[Path, Path]:
        """确保输出目录存在，返回 (output_dir, figures_dir)。"""
        out = Path(self.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        fig = out / self.figures_dir
        fig.mkdir(parents=True, exist_ok=True)
        return out, fig

    def resolve_templates_dir(self) -> Path:
        """解析模板目录路径。"""
        if self.templates_dir:
            return Path(self.templates_dir)
        return Path(__file__).parent.parent.parent / "templates"


# =========================================================================
# 全局默认配置
# =========================================================================

_default_config: Optional[PipelineConfig] = None


def get_default_config() -> PipelineConfig:
    """获取全局默认配置（单例）。"""
    global _default_config
    if _default_config is None:
        _default_config = PipelineConfig()
    return _default_config


def set_default_config(config: PipelineConfig) -> None:
    """设置全局默认配置。"""
    global _default_config
    _default_config = config
