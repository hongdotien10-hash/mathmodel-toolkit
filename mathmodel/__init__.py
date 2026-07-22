"""
MathModel Toolkit — 数学建模竞赛全自动求解器
=============================================

上传题目文件，一键生成完整竞赛论文。

.. code-block:: python

    from mathmodel import Pipeline

    pipe = Pipeline(problem="赛题.pdf", data="附件.xlsx")
    pipe.run()
    paper = pipe.get_paper()

Modules:
    - pipeline:    核心流水线引擎（调度器、进度系统、配置）
    - parser:      文档解析（PDF/DOCX 题目提取、数据加载）
    - analyzer:    题目分析与智能模型推荐
    - preprocessing: 数据预处理
    - models:      模型库（优化/微分方程/统计/ML/图论/评价）
    - solver:      自动求解引擎
    - sensitivity: 灵敏度分析
    - visualization: 论文级可视化
    - paper:       论文自动生成与编译
    - io:          数据读写
    - utils:       通用工具函数
"""

__version__ = "0.1.0"
__author__ = "MathModel Toolkit Contributors"

# ---- Top-level API -----------------------------------------------------------

from mathmodel.pipeline import Pipeline, ProgressTracker, PipelineConfig
from mathmodel.pipeline.orchestrator import Pipeline as Pipeline

__all__ = [
    "Pipeline",
    "ProgressTracker",
    "PipelineConfig",
    "__version__",
]
