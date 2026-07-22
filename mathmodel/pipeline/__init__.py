"""核心流水线引擎 — 总调度、进度追踪、配置管理。

提供端到端的自动求解流程控制：::

    from mathmodel.pipeline import Pipeline, PipelineConfig

    config = PipelineConfig(auto_select_model=True, engine="latex")
    pipe = Pipeline(config=config)
    pipe.run(problem="赛题.pdf", data=["附件1.xlsx", "附件2.csv"])
    pipe.export(output_dir="./output")
"""

from mathmodel.pipeline.orchestrator import Pipeline
from mathmodel.pipeline.progress import ProgressTracker, Stage, StageStatus
from mathmodel.pipeline.config import PipelineConfig

__all__ = [
    "Pipeline",
    "ProgressTracker",
    "Stage",
    "StageStatus",
    "PipelineConfig",
]
