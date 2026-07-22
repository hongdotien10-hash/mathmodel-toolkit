"""通用工具函数。

提供整个工具包共用的基础工具：随机种子、计时器、日志、进度回调等。
"""

import random
import time
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Optional, Callable
from datetime import timedelta


def set_seed(seed: int = 42) -> None:
    """设置全局随机种子，确保结果可复现。

    Args:
        seed: 随机种子值，默认 42
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass


def ensure_dir(path: str | Path) -> Path:
    """确保目录存在，不存在则创建。

    Args:
        path: 目录路径

    Returns:
        Path: 创建后的目录 Path 对象
    """
    p = Path(path) if not isinstance(path, Path) else path
    p.mkdir(parents=True, exist_ok=True)
    return p


def format_duration(seconds: float) -> str:
    """将秒数格式化为可读的时间字符串。

    Args:
        seconds: 秒数

    Returns:
        str: 格式化后的时间，如 "1h 23min 45s"
    """
    delta = timedelta(seconds=int(seconds))
    parts = []
    h, remainder = divmod(delta.seconds, 3600)
    m, s = divmod(remainder, 60)
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}min")
    parts.append(f"{s}s")
    return " ".join(parts)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """获取统一格式的 logger。

    Args:
        name: Logger 名称
        level: 日志级别

    Returns:
        logging.Logger: 配置好的 logger
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(name)-20s %(levelname)-8s %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


class Timer:
    """上下文管理器计时器。

    Usage::

        with Timer("模型求解") as t:
            solve_problem()
        print(t.elapsed)  # 耗时（秒）

        with Timer() as t:
            heavy_compute()
        print(t.duration)  # 输出耗时字符串
    """

    def __init__(self, label: str = ""):
        self.label = label
        self._start: float = 0.0
        self._end: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self._end = time.perf_counter()
        self.elapsed = self._end - self._start

    @property
    def duration(self) -> str:
        """返回格式化的耗时字符串。"""
        return format_duration(self.elapsed)

    def __repr__(self) -> str:
        label = f" [{self.label}]" if self.label else ""
        return f"Timer{label}: {self.duration}"


class ProgressCallback:
    """进度回调基类。

    用于在模型求解/数据处理过程中报告进度。
    子类可继承实现自定义的进度展示方式。

    Usage::

        cb = ProgressCallback()
        cb.update(0.5, "数据预处理完成")
    """

    def __init__(self, total: float = 1.0):
        self.total = total
        self.current: float = 0.0
        self.message: str = ""
        self._on_update: Optional[Callable[[float, str], None]] = None

    def on_update(self, fn: Callable[[float, str], None]) -> "ProgressCallback":
        """注册进度更新回调函数。"""
        self._on_update = fn
        return self

    def update(self, progress: float, message: str = "") -> None:
        """更新进度。

        Args:
            progress: 当前进度 (0 ~ total)
            message: 进度描述
        """
        self.current = progress
        self.message = message
        if self._on_update:
            self._on_update(progress / self.total if self.total else 0, message)

    def reset(self, total: float = 1.0) -> None:
        """重置进度。"""
        self.total = total
        self.current = 0.0
        self.message = ""


# ================================================================
# 安全执行工具 — 超时跳过，永不卡死
# ================================================================

def safe_call(fn: Callable, desc: str = "", timeout: float = 0,
              default=None, verbose: bool = True):
    """安全调用函数：超时/异常时返回 default，永不抛异常。

    Args:
        fn: 要调用的函数（无参数）
        desc: 描述文字
        timeout: 超时秒数，0=不限
        default: 失败时的默认返回值
        verbose: 是否打印错误
    """
    if timeout <= 0:
        try:
            return fn()
        except Exception as e:
            if verbose:
                print(f"  [SKIP] {desc}: {e}")
            return default

    # 线程超时实现（跨平台）
    result = [default]
    exc_info = [None]

    def worker():
        try:
            result[0] = fn()
        except Exception as e:
            exc_info[0] = e

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout)

    if t.is_alive():
        if verbose:
            print(f"  [TIMEOUT] {desc} ({timeout}s) — skipped")
        return default

    if exc_info[0] is not None:
        if verbose:
            print(f"  [SKIP] {desc}: {exc_info[0]}")
        return default

    return result[0]


class PhaseGuard:
    """阶段保护器：超时或异常时自动跳过，记录失败"""

    def __init__(self, max_phase_seconds: float = 300):
        self.max_seconds = max_phase_seconds
        self.failures: list[str] = []
        self.skips: list[str] = []

    def run(self, desc: str, fn: Callable, timeout: float = 0, default=None):
        """运行一个步骤，失败则记录并继续"""
        if timeout <= 0:
            timeout = self.max_seconds
        result = safe_call(fn, desc=desc, timeout=timeout, default=default)
        if result is default and default is not None:
            self.skips.append(desc)
        return result

    def report(self):
        """打印跳过摘要"""
        if self.skips:
            print(f"\n  [GUARD] {len(self.skips)} steps skipped: {', '.join(self.skips[:10])}")
        if self.failures:
            print(f"  [GUARD] {len(self.failures)} steps failed: {', '.join(self.failures[:10])}")
        return len(self.skips) + len(self.failures)
