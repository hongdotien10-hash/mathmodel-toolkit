"""Rich 进度追踪 — 专业终端UI，替代 print 满天飞"""

import sys
import os
from contextlib import contextmanager
from typing import Optional

# 修复 Windows GBK 终端 Rich 崩溃问题
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

try:
    from rich.console import Console
    from rich.progress import (
        Progress, SpinnerColumn, BarColumn, TextColumn,
        TimeElapsedColumn, TimeRemainingColumn, TaskID,
    )
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich import box

    # 验证 Rich 在当前终端可用
    try:
        _test_console = Console(force_terminal=False)
        _test_console.print("")
        HAS_RICH = True
    except Exception:
        HAS_RICH = False
except ImportError:
    HAS_RICH = False


# ================================================================
# 安全打印函数 — Rich 不可用时自动回退
# ================================================================

def _safe_rich(func):
    """装饰器：Rich 调用失败时回退到 plain print"""
    if not HAS_RICH:
        return None
    return func


def print_header(text: str, width: int = 60) -> None:
    """打印标题栏"""
    if HAS_RICH:
        try:
            console = Console(force_terminal=False)
            console.print()
            console.rule(f"[bold blue]{text}[/bold blue]")
            return
        except Exception:
            pass
    print(f"\n{'='*width}\n  {text}\n{'='*width}")


def print_section(text: str) -> None:
    """打印小节标题"""
    if HAS_RICH:
        try:
            console = Console(force_terminal=False)
            console.print(f"\n  [bold cyan]> {text}[/bold cyan]")
            return
        except Exception:
            pass
    print(f"\n--- {text} ---")


def print_result_summary(sub_problems: list[dict], results: dict) -> None:
    """打印结果摘要表格"""
    if HAS_RICH:
        try:
            console = Console(force_terminal=False)
            table = Table(title="Solving Results", box=box.SIMPLE, expand=False)
            table.add_column("Q#", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Model", style="magenta")
            table.add_column("Result", style="green")

            for sp in sub_problems:
                sp_id = sp["id"]
                r = results.get(f"sub_{sp_id}", {})
                summary = r.get("summary", str(r.get("mape", "")) if "mape" in r else "-")
                table.add_row(
                    f"Q{sp_id}", sp.get("type", "?"), sp.get("model", "?")[:30],
                    str(summary)[:80]
                )
            console.print(table)
            return
        except Exception:
            pass
    # Plain fallback
    print(f"\n{'─'*50}\n  Results Summary\n{'─'*50}")
    for sp in sub_problems:
        sp_id = sp["id"]
        r = results.get(f"sub_{sp_id}", {})
        summary = r.get("summary", str(r.get("mape", "")) if "mape" in r else "-")
        print(f"  Q{sp_id} [{sp.get('type','?')}] {sp.get('model','?')}: {str(summary)[:80]}")


class PhaseTracker:
    """国赛工具包进度追踪器 — Rich终端UI，不可用时自动回退"""

    def __init__(self, title: str = "MathModel Toolkit"):
        self.title = title
        self.phases: list[dict] = []
        self._current_phase: Optional[str] = None
        self._progress: Optional["Progress"] = None
        self._console: Optional["Console"] = None
        self._task_id: Optional[TaskID] = None

        if HAS_RICH:
            try:
                self._console = Console(force_terminal=False)
                self._progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(bar_width=30, style="blue"),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                    console=self._console,
                    expand=False,
                )
                self._progress.start()
            except Exception:
                self._progress = None
                self._console = None

    # ================================================================
    # Phase management
    # ================================================================

    def start_phase(self, name: str, total_steps: int = 100) -> None:
        """开始一个新阶段"""
        self._current_phase = name
        if self._progress:
            try:
                self._task_id = self._progress.add_task(
                    f"[bold]{name}[/bold]", total=total_steps
                )
                self.phases.append({"name": name, "total": total_steps, "current": 0})
                return
            except Exception:
                pass
        print(f"\n{'─'*50}\n  {name}\n{'─'*50}")

    def update(self, n: int = 1, status: str = "") -> None:
        """推进进度"""
        if self._progress and self._task_id is not None:
            try:
                desc = f"[bold]{self._current_phase}[/bold]"
                if status:
                    desc += f"  {status}"
                self._progress.update(self._task_id, advance=n, description=desc)
                return
            except Exception:
                pass
        if status:
            print(f"  {status}")

    def complete_phase(self, message: str = "") -> None:
        """完成当前阶段"""
        if self._progress and self._task_id is not None:
            try:
                self._progress.update(self._task_id, completed=self._progress.tasks[self._task_id].total)
                self._progress.remove_task(self._task_id)
            except Exception:
                pass
        if message:
            print(f"  OK {message}")

    def log(self, message: str, style: str = "") -> None:
        """记录一条消息到终端"""
        if self._console:
            try:
                prefixes = {
                    "success": "[green]OK[/green]",
                    "error": "[red]FAIL[/red]",
                    "warning": "[yellow]![/yellow]",
                    "info": "[cyan]>[/cyan]",
                    "data": "[blue]DATA[/blue]",
                    "model": "[magenta]MODEL[/magenta]",
                    "ai": "[yellow]AI[/yellow]",
                }
                prefix = prefixes.get(style, "")
                msg = f"  {prefix} {message}" if prefix else f"  {message}"
                self._console.print(msg)
                return
            except Exception:
                pass
        print(f"  {message}")

    def print_table(self, title: str, rows: list[list[str]], columns: list[str]) -> None:
        """打印表格"""
        if self._console:
            try:
                table = Table(title=title, box=box.SIMPLE, expand=False)
                for col in columns:
                    table.add_column(col, style="cyan" if columns.index(col) == 0 else "")
                for row in rows:
                    table.add_row(*[str(c) for c in row])
                self._console.print(table)
                return
            except Exception:
                pass
        print(f"\n  {title}")
        print("  " + " | ".join(columns))
        print("  " + "-" * 40)
        for row in rows:
            print("  " + " | ".join(str(c) for c in row))

    def print_panel(self, content: str, title: str = "", border_style: str = "blue") -> None:
        """打印面板"""
        if self._console:
            try:
                self._console.print(Panel(content, title=title, border_style=border_style, expand=False))
                return
            except Exception:
                pass
        print(f"\n  === {title} ===\n{content}\n  {'='*len(title)}")

    def finish(self) -> None:
        """关闭进度追踪器"""
        if self._progress:
            try:
                self._progress.stop()
            except Exception:
                pass

    @contextmanager
    def phase(self, name: str, total: int = 100):
        """上下文管理器：自动开始/完成阶段"""
        self.start_phase(name, total)
        try:
            yield self
        finally:
            self.complete_phase()
