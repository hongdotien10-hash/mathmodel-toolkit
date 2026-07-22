"""PDF 题目解析器。

支持 pdfplumber 和 PyMuPDF 双引擎，自动回退。
"""

from pathlib import Path
from typing import Optional


class PDFReader:
    """PDF 文档读取器。

    自动尝试 pdfplumber → PyMuPDF → 报错。

    Usage::

        reader = PDFReader()
        text = reader.read("2024国赛A题.pdf")
        metadata = reader.get_metadata("2024国赛A题.pdf")
    """

    def __init__(self, engine: str = "auto"):
        """
        Args:
            engine: 解析引擎，可选 "auto" / "pdfplumber" / "pymupdf"
        """
        self.engine = engine
        self._available_engine: Optional[str] = None

    def _detect_engine(self) -> str:
        """检测可用的 PDF 引擎。"""
        if self.engine != "auto":
            return self.engine

        # 优先 pdfplumber（表格提取更好）
        try:
            import pdfplumber  # noqa: F401
            self._available_engine = "pdfplumber"
            return "pdfplumber"
        except ImportError:
            pass

        try:
            import fitz  # noqa: F401
            self._available_engine = "pymupdf"
            return "pymupdf"
        except ImportError:
            pass

        raise ImportError(
            "需要安装 PDF 解析库: pip install mathmodel-toolkit[pdf]\n"
            "  或手动安装: pip install pdfplumber 或 pip install PyMuPDF"
        )

    def read(self, path: str | Path, pages: Optional[list[int]] = None) -> str:
        """读取 PDF 文本内容。

        Args:
            path: PDF 文件路径
            pages: 指定页码列表（1-based），None 表示全部

        Returns:
            str: 提取的文本内容
        """
        engine = self._detect_engine()
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {path}")

        if engine == "pdfplumber":
            return self._read_pdfplumber(path, pages)
        else:
            return self._read_pymupdf(path, pages)

    def _read_pdfplumber(self, path: Path, pages: Optional[list[int]]) -> str:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(str(path)) as pdf:
            targets = pages or range(1, len(pdf.pages) + 1)
            for i in targets:
                page = pdf.pages[i - 1]  # pdfplumber 是 0-based
                t = page.extract_text()
                if t:
                    text_parts.append(f"[第{i}页]\n{t}")

        return "\n\n".join(text_parts)

    def _read_pymupdf(self, path: Path, pages: Optional[list[int]]) -> str:
        import fitz

        doc = fitz.open(str(path))
        text_parts = []
        targets = pages or range(1, doc.page_count + 1)
        for i in targets:
            page = doc[i - 1]
            t = page.get_text()
            if t:
                text_parts.append(f"[第{i}页]\n{t}")

        doc.close()
        return "\n\n".join(text_parts)

    def get_metadata(self, path: str | Path) -> dict:
        """获取 PDF 元数据。"""
        engine = self._detect_engine()
        path = Path(path)

        if engine == "pdfplumber":
            import pdfplumber
            with pdfplumber.open(str(path)) as pdf:
                return {
                    "pages": len(pdf.pages),
                    "metadata": pdf.metadata or {},
                }
        else:
            import fitz
            doc = fitz.open(str(path))
            info = {
                "pages": doc.page_count,
                "metadata": doc.metadata or {},
            }
            doc.close()
            return info

    def extract_tables(self, path: str | Path) -> list:
        """提取 PDF 中的表格。"""
        engine = self._detect_engine()

        if engine == "pdfplumber":
            import pdfplumber
            tables = []
            with pdfplumber.open(str(path)) as pdf:
                for page in pdf.pages:
                    t = page.extract_tables()
                    if t:
                        tables.extend(t)
            return tables
        else:
            # PyMuPDF 不直接支持表格提取
            return []
