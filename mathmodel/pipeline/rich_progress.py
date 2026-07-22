"""Rich 进度追踪 — 专业终端UI，替代 print 满天飞"""

import sys
from contextlib import contextmanager
from typing import Optional

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
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class PhaseTracker:
    """国赛工具包进度追踪器 — Rich终端UI"""

    def __init__(self, title: str = "MathModel Toolkit"):
        self.title = title
        self.phases: list[dict] = []
        self._current_phase: Optional[str] = None
        self._progress: Optional[Progress] = None
        self._console: Optional["Console"] = None
        self._task_id: Optional[TaskID] = None

        if HAS_RICH:
            self._console = Console()
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

    # ================================================================
    # Phase management
    # ================================================================

    def start_phase(self, name: str, total_steps: int = 100) -> None:
        """开始一个新阶段"""
        self._current_phase = name
        if HAS_RICH and self._progress:
            self._task_id = self._progress.add_task(
                f"[bold]{name}[/bold]", total=total_steps
            )
            self.phases.append({"name": name, "total": total_steps, "current": 0})
        else:
            print(f"\n{'─'*50}\n  {name}\n{'─'*50}")

    def update(self, n: int = 1, status: str = "") -> None:
        """推进进度"""
        if HAS_RICH and self._progress and self._task_id is not None:
            desc = f"[bold]{self._current_phase}[/bold]"
            if status:
                desc += f"  {status}"
            self._progress.update(self._task_id, advance=n, description=desc)
        elif status:
            print(f"  {status}")

    def complete_phase(self, message: str = "") -> None:
        """完成当前阶段"""
        if HAS_RICH and self._progress and self._task_id is not None:
            self._progress.update(self._task_id, completed=self._progress.tasks[self._task_id].total)
            self._progress.remove_task(self._task_id)
        if message:
            if HAS_RICH and self._console:
                self._console.print(f"  [green]✓[/green] {message}")
            else:
                print(f"  ✓ {message}")

    def log(self, message: str, style: str = "") -> None:
        """记录一条消息到终端"""
        if HAS_RICH and self._console:
            if style == "success":
                self._console.print(f"  [green]✓[/green] {message}")
            elif style == "error":
                self._console.print(f"  [red]✗[/red] {message}")
            elif style == "warning":
                self._console.print(f"  [yellow]![/yellow] {message}")
            elif style == "info":
                self._console.print(f"  [cyan]→[/cyan] {message}")
            elif style == "data":
                self._console.print(f"  [blue]📊[/blue] {message}")
            elif style == "model":
                self._console.print(f"  [magenta]🧠[/magenta] {message}")
            elif style == "ai":
                self._console.print(f"  [yellow]🤖[/yellow] {message}")
            else:
                self._console.print(f"  {message}")
        else:
            print(f"  {message}")

    def print_table(self, title: str, rows: list[list[str]], columns: list[str]) -> None:
        """打印表格"""
        if HAS_RICH and self._console:
            table = Table(title=title, box=box.SIMPLE, expand=False)
            for col in columns:
                table.add_column(col, style="cyan" if columns.index(col) == 0 else "")
            for row in rows:
                table.add_row(*[str(c) for c in row])
            self._console.print(table)
        else:
            print(f"\n  {title}")
            print("  " + " | ".join(columns))
            print("  " + "-" * 40)
            for row in rows:
                print("  " + " | ".join(str(c) for c in row))

    def print_panel(self, content: str, title: str = "", border_style: str = "blue") -> None:
        """打印面板"""
        if HAS_RICH and self._console:
            self._console.print(Panel(content, title=title, border_style=border_style, expand=False))
        else:
            print(f"\n  === {title} ===\n{content}\n  {'='*len(title)}")

    def finish(self) -> None:
        """关闭进度追踪器"""
        if HAS_RICH and self._progress:
            self._progress.stop()

    @contextmanager
    def phase(self, name: str, total: int = 100):
        """上下文管理器：自动开始/完成阶段"""
        self.start_phase(name, total)
        try:
            yield self
        finally:
            self.complete_phase()


# ================================================================
# 便捷函数 — 无Rich时的回退
# ================================================================

def print_header(text: str, width: int = 60) -> None:
    """打印标题栏"""
    if HAS_RICH:
        console = Console()
        console.print()
        console.rule(f"[bold blue]{text}[/bold blue]")
    else:
        print(f"\n{'='*width}\n  {text}\n{'='*width}")


def print_section(text: str) -> None:
    """打印小节标题"""
    if HAS_RICH:
        console = Console()
        console.print(f"\n  [bold cyan]▸ {text}[/bold cyan]")
    else:
        print(f"\n--- {text} ---")


def print_result_summary(sub_problems: list[dict], results: dict) -> None:
    """打印结果摘要表格"""
    if HAS_RICH:
        console = Console()
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
    else:
        print(f"\n{'─'*50}\n  Results Summary\n{'─'*50}")
        for sp in sub_problems:
            sp_id = sp["id"]
            r = results.get(f"sub_{sp_id}", {})
            summary = r.get("summary", str(r.get("mape", "")) if "mape" in r else "-")
            print(f"  Q{sp_id} [{sp.get('type','?')}] {sp.get('model','?')}: {str(summary)[:80]}")
