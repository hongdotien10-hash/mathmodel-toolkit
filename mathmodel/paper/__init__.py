"""论文生成引擎 — 章节撰写、模板填充、LaTeX/Typst 编译。"""

from mathmodel.paper.writer import PaperWriter
from mathmodel.paper.compiler import PaperCompiler

__all__ = [
    "PaperWriter",
    "PaperCompiler",
]
