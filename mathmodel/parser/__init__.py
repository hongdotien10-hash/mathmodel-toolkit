"""文档解析模块 — PDF/DOCX 题目提取、数据加载、子问题拆分。"""

from mathmodel.parser.pdf_reader import PDFReader
from mathmodel.parser.docx_reader import DocxReader
from mathmodel.parser.data_loader import DataLoader
from mathmodel.parser.problem_splitter import ProblemSplitter

__all__ = [
    "PDFReader",
    "DocxReader",
    "DataLoader",
    "ProblemSplitter",
]
