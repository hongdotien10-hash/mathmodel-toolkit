"""论文编译器。

调用 LaTeX/Typst 将 .tex/.typ 编译为 PDF。
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from mathmodel.utils.helpers import get_logger, ensure_dir

logger = get_logger("mathmodel.paper.compiler")

# 编译器查找优先级
_COMPILERS = ["xelatex", "pdflatex", "lualatex"]
_TYPST_COMPILER = "typst"


class PaperCompiler:
    """论文编译器。

    自动检测系统中可用的 LaTeX/Typst 编译器，编译 .tex/.typ 文件为 PDF。

    Usage::

        compiler = PaperCompiler()
        pdf_path = compiler.compile("output/paper_src/paper.tex")
        # 或
        pdf_path = compiler.compile_latex(tex_content, output_dir)
    """

    def __init__(self, engine: str = "latex", timeout: int = 120):
        """
        Args:
            engine: 编译引擎 "latex" 或 "typst"
            timeout: 编译超时时间（秒）
        """
        self.engine = engine
        self.timeout = timeout
        self._compiler_path: Optional[str] = None

    def compile(self, source_path: str | Path) -> Path:
        """编译单个源文件。

        Args:
            source_path: .tex 或 .typ 文件路径

        Returns:
            Path: 生成的 PDF 路径
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"源文件不存在: {source}")

        if source.suffix == ".tex" or self.engine == "latex":
            return self.compile_latex(source)
        elif source.suffix == ".typ" or self.engine == "typst":
            return self.compile_typst(source)
        else:
            raise ValueError(f"不支持的源文件格式: {source.suffix}")

    def compile_latex(self, tex_path: Path) -> Path:
        """编译 LaTeX 源文件。

        Args:
            tex_path: .tex 文件路径

        Returns:
            Path: PDF 路径
        """
        work_dir = tex_path.parent

        # 查找可用的编译器
        compiler = self._find_latex_compiler()
        if not compiler:
            logger.warning("未找到 LaTeX 编译器。请安装 TeX Live 或 MiKTeX。")
            return tex_path  # 返回 .tex 路径而非 .pdf

        logger.info(f"使用 LaTeX 编译器: {compiler}")

        # 运行两次以解决交叉引用
        for run in range(2):
            try:
                result = subprocess.run(
                    [
                        compiler,
                        "-interaction=nonstopmode",
                        "-output-directory", str(work_dir),
                        tex_path.name,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=str(work_dir),
                )
                if result.returncode != 0:
                    self._log_latex_errors(result.stdout, result.stderr)
            except subprocess.TimeoutExpired:
                logger.error(f"LaTeX 编译超时 ({self.timeout}s)")
                break
            except Exception as e:
                logger.error(f"LaTeX 编译异常: {e}")
                break

        pdf_path = work_dir / f"{tex_path.stem}.pdf"
        if pdf_path.exists():
            logger.info(f"PDF 编译完成: {pdf_path}")
            return pdf_path
        else:
            logger.warning("PDF 编译失败，返回 .tex 源文件")
            return tex_path

    def compile_typst(self, typ_path: Path) -> Path:
        """编译 Typst 源文件。"""
        compiler = shutil.which(_TYPST_COMPILER)
        if not compiler:
            logger.warning("未找到 Typst 编译器。请安装: https://github.com/typst/typst")
            return typ_path

        work_dir = typ_path.parent
        pdf_path = work_dir / f"{typ_path.stem}.pdf"

        try:
            result = subprocess.run(
                [compiler, "compile", str(typ_path), str(pdf_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(work_dir),
            )
            if result.returncode == 0:
                logger.info(f"Typst 编译完成: {pdf_path}")
                return pdf_path
            else:
                logger.error(f"Typst 编译错误: {result.stderr}")
                return typ_path
        except Exception as e:
            logger.error(f"Typst 编译异常: {e}")
            return typ_path

    def compile_from_string(
        self,
        content: str,
        output_dir: str | Path,
        filename: str = "paper",
    ) -> Path:
        """从字符串编译论文。

        Args:
            content: LaTeX/Typst 源码
            output_dir: 输出目录
            filename: 文件名（不含扩展名）

        Returns:
            Path: PDF 路径
        """
        out = Path(output_dir)
        ensure_dir(out)

        ext = ".tex" if self.engine == "latex" else ".typ"
        source_path = out / f"{filename}{ext}"
        source_path.write_text(content, encoding="utf-8")

        return self.compile(source_path)

    def _find_latex_compiler(self) -> Optional[str]:
        """查找可用的 LaTeX 编译器。"""
        for compiler in _COMPILERS:
            path = shutil.which(compiler)
            if path:
                return compiler
        return None

    def _log_latex_errors(self, stdout: str, stderr: str) -> None:
        """记录 LaTeX 编译错误的关键行。"""
        for line in (stdout + stderr).split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("!") or "Error" in line or "Fatal" in line:
                logger.warning(f"LaTeX: {line[:150]}")

    @staticmethod
    def is_latex_available() -> bool:
        """检查系统是否安装了 LaTeX。"""
        return any(shutil.which(c) for c in _COMPILERS)

    @staticmethod
    def is_typst_available() -> bool:
        """检查系统是否安装了 Typst。"""
        return shutil.which(_TYPST_COMPILER) is not None
