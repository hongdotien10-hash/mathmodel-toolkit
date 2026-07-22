"""进度追踪系统。

提供流水线各阶段的状态追踪和可视化进度展示。
支持终端 Rich 面板 + JSON 文件双通道输出。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from mathmodel.utils.helpers import format_duration


class StageStatus(str, Enum):
    """阶段状态枚举。"""
    PENDING = "pending"       # 等待中
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    SKIPPED = "skipped"       # 已跳过
    CANCELLED = "cancelled"   # 已取消


@dataclass
class SubStep:
    """子步骤信息。"""
    name: str
    status: StageStatus = StageStatus.PENDING
    message: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0

    @property
    def elapsed(self) -> float:
        if self.started_at == 0:
            return 0.0
        end = self.finished_at if self.finished_at > 0 else time.perf_counter()
        return end - self.started_at


@dataclass
class Stage:
    """流水线阶段信息。

    Attributes:
        id: 阶段唯一标识
        name: 阶段显示名称
        status: 当前状态
        message: 当前消息/描述
        sub_steps: 子步骤列表
        started_at: 开始时间戳
        finished_at: 结束时间戳
        weight: 阶段权重（用于计算总进度百分比）
    """
    id: str
    name: str
    status: StageStatus = StageStatus.PENDING
    message: str = ""
    sub_steps: list[SubStep] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0
    weight: float = 1.0

    @property
    def elapsed(self) -> float:
        if self.started_at == 0:
            return 0.0
        end = self.finished_at if self.finished_at > 0 else time.perf_counter()
        return end - self.started_at

    @property
    def sub_progress(self) -> float:
        """子步骤完成比例 (0~1)。"""
        if not self.sub_steps:
            return 0.0
        done = sum(1 for s in self.sub_steps if s.status == StageStatus.COMPLETED)
        return done / len(self.sub_steps)


class ProgressTracker:
    """进度追踪器。

    管理流水线各阶段的状态，计算总进度百分比，支持终端 Rich 展示
    和 JSON 文件输出。

    Usage::

        tracker = ProgressTracker(total_stages=6)
        tracker.start_stage("parse", "文档解析", weight=1.0)
        tracker.add_sub_step("parse", "PDF提取", status=StageStatus.RUNNING)
        # ... do work ...
        tracker.complete_sub_step("parse", "PDF提取", "提取完成，共12页")
        tracker.complete_stage("parse")
        tracker.summary()  # 打印进度摘要
    """

    def __init__(self, total_stages: int = 6):
        self.total_stages = total_stages
        self.stages: dict[str, Stage] = {}
        self._started_at: float = time.perf_counter()
        self._stage_order: list[str] = []
        self._json_path: Optional[Path] = None

        # Rich 相关（延迟导入）
        self._rich_available: Optional[bool] = None
        self._progress = None
        self._live = None

    # =====================================================================
    # JSON 输出
    # =====================================================================

    def enable_json(self, path: str | Path) -> "ProgressTracker":
        """启用 JSON 进度输出文件。

        Args:
            path: JSON 输出路径

        Returns:
            self，支持链式调用
        """
        self._json_path = Path(path)
        self._write_json()
        return self

    def _write_json(self) -> None:
        """写入当前状态到 JSON 文件。"""
        if not self._json_path:
            return
        self._json_path.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_dict()
        with open(self._json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # =====================================================================
    # 阶段管理
    # =====================================================================

    def start_stage(self, stage_id: str, name: str, weight: float = 1.0,
                    message: str = "") -> Stage:
        """开始一个新阶段。

        Args:
            stage_id: 阶段唯一标识（如 "parse", "analyze"）
            name: 阶段显示名称
            weight: 阶段权重
            message: 初始消息
        """
        stage = Stage(
            id=stage_id,
            name=name,
            status=StageStatus.RUNNING,
            message=message,
            weight=weight,
            started_at=time.perf_counter(),
        )
        self.stages[stage_id] = stage
        self._stage_order.append(stage_id)
        self._write_json()
        return stage

    def complete_stage(self, stage_id: str, message: str = "") -> Stage:
        """标记阶段完成。"""
        stage = self.stages[stage_id]
        stage.status = StageStatus.COMPLETED
        stage.finished_at = time.perf_counter()
        stage.message = message or f"完成 ({format_duration(stage.elapsed)})"
        self._write_json()
        return stage

    def fail_stage(self, stage_id: str, message: str) -> Stage:
        """标记阶段失败。"""
        stage = self.stages[stage_id]
        stage.status = StageStatus.FAILED
        stage.finished_at = time.perf_counter()
        stage.message = message
        self._write_json()
        return stage

    def skip_stage(self, stage_id: str, reason: str = "") -> Stage:
        """跳过阶段。"""
        stage = self.stages.get(stage_id) or Stage(
            id=stage_id, name=stage_id, status=StageStatus.SKIPPED
        )
        stage.status = StageStatus.SKIPPED
        stage.message = reason
        if stage_id not in self.stages:
            self.stages[stage_id] = stage
            self._stage_order.append(stage_id)
        self._write_json()
        return stage

    def update_message(self, stage_id: str, message: str) -> None:
        """更新阶段的当前消息。"""
        if stage_id in self.stages:
            self.stages[stage_id].message = message
            self._write_json()

    # =====================================================================
    # 子步骤管理
    # =====================================================================

    def add_sub_step(self, stage_id: str, name: str,
                     status: StageStatus = StageStatus.PENDING) -> SubStep:
        """向某个阶段添加子步骤。"""
        if stage_id not in self.stages:
            self.start_stage(stage_id, name=stage_id)
        step = SubStep(name=name, status=status)
        self.stages[stage_id].sub_steps.append(step)
        self._write_json()
        return step

    def start_sub_step(self, stage_id: str, sub_name: str) -> Optional[SubStep]:
        """开始执行某个子步骤。返回 None 如果未找到。"""
        stage = self.stages.get(stage_id)
        if not stage:
            return None
        for s in stage.sub_steps:
            if s.name == sub_name:
                s.status = StageStatus.RUNNING
                s.started_at = time.perf_counter()
                self._write_json()
                return s
        # 不存在则创建
        step = SubStep(name=sub_name, status=StageStatus.RUNNING, started_at=time.perf_counter())
        stage.sub_steps.append(step)
        self._write_json()
        return step

    def complete_sub_step(self, stage_id: str, sub_name: str,
                          message: str = "") -> Optional[SubStep]:
        """标记子步骤完成。"""
        stage = self.stages.get(stage_id)
        if not stage:
            return None
        for s in stage.sub_steps:
            if s.name == sub_name:
                s.status = StageStatus.COMPLETED
                s.finished_at = time.perf_counter()
                s.message = message or "完成"
                self._write_json()
                return s
        return None

    def fail_sub_step(self, stage_id: str, sub_name: str,
                      error: str) -> Optional[SubStep]:
        """标记子步骤失败。"""
        stage = self.stages.get(stage_id)
        if not stage:
            return None
        for s in stage.sub_steps:
            if s.name == sub_name:
                s.status = StageStatus.FAILED
                s.finished_at = time.perf_counter()
                s.message = error
                self._write_json()
                return s
        return None

    # =====================================================================
    # 进度计算
    # =====================================================================

    @property
    def total_weight(self) -> float:
        """所有阶段的权重之和。"""
        return sum(s.weight for s in self.stages.values())

    @property
    def overall_progress(self) -> float:
        """总进度 (0~1)。

        已完成的阶段贡献全部权重，运行中阶段按其子步骤完成比例贡献。
        """
        if not self.stages:
            return 0.0
        tw = self.total_weight
        if tw == 0:
            return 0.0
        progressed = 0.0
        for stage in self.stages.values():
            if stage.status == StageStatus.COMPLETED:
                progressed += stage.weight
            elif stage.status == StageStatus.RUNNING:
                # 运行中的阶段，按子步骤完成度计算
                progressed += stage.weight * stage.sub_progress
        return min(progressed / tw, 1.0)

    @property
    def elapsed_total(self) -> float:
        """从开始到现在的总耗时（秒）。"""
        return time.perf_counter() - self._started_at

    def estimate_remaining(self) -> float:
        """估算剩余时间（秒）。

        基于已完成阶段的平均速度和当前进度线性估算。
        """
        p = self.overall_progress
        if p < 0.01:
            return float("inf")
        return self.elapsed_total * (1 - p) / p

    @property
    def is_complete(self) -> bool:
        """所有阶段是否已完成。"""
        return all(
            s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED, StageStatus.FAILED)
            for s in self.stages.values()
        )

    @property
    def has_failures(self) -> bool:
        """是否有阶段失败。"""
        return any(s.status == StageStatus.FAILED for s in self.stages.values())

    # =====================================================================
    # 输出
    # =====================================================================

    def summary(self) -> str:
        """生成进度摘要字符串。"""
        lines = []
        total_w = self.total_weight
        for stage_id in self._stage_order:
            stage = self.stages[stage_id]
            icon = _status_icon(stage.status)
            elapsed = format_duration(stage.elapsed) if stage.started_at else ""
            pct = f"({stage.weight / total_w * 100:.0f}%)" if total_w > 0 else ""
            lines.append(
                f"  {icon} {stage.name:<12s} {pct:<6s} "
                f"[{elapsed:<10s}] {stage.message}"
            )
            # 子步骤
            for sub in stage.sub_steps:
                sub_icon = _status_icon(sub.status)
                lines.append(f"       {sub_icon} {sub.name}  {sub.message}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """序列化为字典（供 JSON/API 使用）。"""
        return {
            "overall_progress": round(self.overall_progress, 4),
            "elapsed_total": round(self.elapsed_total, 2),
            "estimated_remaining": round(self.estimate_remaining(), 2),
            "is_complete": self.is_complete,
            "has_failures": self.has_failures,
            "stages": [
                {
                    "id": s.id,
                    "name": s.name,
                    "status": s.status.value,
                    "message": s.message,
                    "weight": s.weight,
                    "elapsed": round(s.elapsed, 2),
                    "sub_progress": round(s.sub_progress, 4),
                    "sub_steps": [
                        {
                            "name": ss.name,
                            "status": ss.status.value,
                            "message": ss.message,
                        }
                        for ss in s.sub_steps
                    ],
                }
                for s in [self.stages[k] for k in self._stage_order]
            ],
        }

    # =====================================================================
    # Rich 终端展示
    # =====================================================================

    def _check_rich(self) -> bool:
        """检查 Rich 是否可用。"""
        if self._rich_available is None:
            try:
                import rich  # noqa: F401
                self._rich_available = True
            except ImportError:
                self._rich_available = False
        return self._rich_available

    def render_rich(self) -> str:
        """使用 Rich 渲染进度面板。

        Returns:
            str: Rich 渲染后的 ANSI 字符串（可直接 print）
        """
        if not self._check_rich():
            return self.summary()

        from rich.console import Console
        from rich.panel import Panel
        from rich.progress_bar import ProgressBar
        from rich.table import Table
        from rich.text import Text

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("icon", width=2)
        table.add_column("stage", width=14)
        table.add_column("time", width=10)
        table.add_column("detail")

        for stage_id in self._stage_order:
            s = self.stages[stage_id]
            icon = _rich_status_icon(s.status)
            elapsed = format_duration(s.elapsed) if s.started_at else ""
            detail = Text(s.message, style="dim")
            table.add_row(icon, s.name, elapsed, detail)

            for sub in s.sub_steps:
                sub_icon = _rich_status_icon(sub.status)
                sub_detail = Text(sub.message, style="dim")
                table.add_row("", f"  ↳ {sub.name}", "", sub_detail)

        p = self.overall_progress
        bar = ProgressBar(total=100, completed=int(p * 100), width=30)
        remaining = format_duration(self.estimate_remaining()) if p > 0 else "--"

        title = Text("🚀 数学建模自动求解流水线", style="bold cyan")
        footer_text = (
            f"📊 总进度: {p*100:.0f}%  |  "
            f"已耗时: {format_duration(self.elapsed_total)}  |  "
            f"预计剩余: {remaining}"
        )

        console = Console(no_color=False, width=80)
        with console.capture() as capture:
            console.print(Panel(table, title=title, border_style="cyan"))
            console.print(bar)
            console.print(Text(footer_text, style="yellow"))
        return capture.get()


def _status_icon(status: StageStatus) -> str:
    """返回纯文本状态图标。"""
    return {
        StageStatus.PENDING: "⏳",
        StageStatus.RUNNING: "🔄",
        StageStatus.COMPLETED: "✅",
        StageStatus.FAILED: "❌",
        StageStatus.SKIPPED: "⏭️",
        StageStatus.CANCELLED: "🚫",
    }.get(status, "❓")


def _rich_status_icon(status: StageStatus) -> Text:
    """返回 Rich Text 格式的状态图标。"""
    from rich.text import Text
    mapping = {
        StageStatus.PENDING: ("⏳", "dim"),
        StageStatus.RUNNING: ("🔄", "bold yellow"),
        StageStatus.COMPLETED: ("✅", "bold green"),
        StageStatus.FAILED: ("❌", "bold red"),
        StageStatus.SKIPPED: ("⏭️", "dim"),
        StageStatus.CANCELLED: ("🚫", "dim"),
    }
    icon, style = mapping.get(status, ("❓", ""))
    return Text(icon, style=style)
