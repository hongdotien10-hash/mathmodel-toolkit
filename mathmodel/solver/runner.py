"""代码执行器。

在安全隔离环境中执行求解代码，收集输出和结果。
"""

import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from mathmodel.utils.helpers import get_logger

logger = get_logger("mathmodel.solver.runner")


class CodeRunner:
    """求解代码执行器。

    Usage::

        runner = CodeRunner(timeout=300)
        result = runner.run("solve_problem1.py")
        print(result["stdout"])
        print(result["success"])
    """

    def __init__(
        self,
        timeout: int = 600,
        python: str = "python",
        work_dir: Optional[str | Path] = None,
    ):
        """
        Args:
            timeout: 超时时间（秒）
            python: Python 解释器
            work_dir: 工作目录
        """
        self.timeout = timeout
        self.python = python
        self.work_dir = Path(work_dir) if work_dir else None

    def run(self, code_or_path: str, is_file: bool = True) -> dict:
        """执行求解代码。

        Args:
            code_or_path: Python 代码字符串或脚本路径
            is_file: True 表示文件路径，False 表示代码字符串

        Returns:
            dict: {
                "success": bool,
                "stdout": str,
                "stderr": str,
                "elapsed": float (秒),
                "returncode": int,
            }
        """
        if is_file:
            script_path = Path(code_or_path)
            if not script_path.exists():
                return {"success": False, "stdout": "", "stderr": f"文件不存在: {script_path}", "elapsed": 0, "returncode": -1}
        else:
            # 写入临时文件
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            )
            tmp.write(code_or_path)
            tmp.close()
            script_path = Path(tmp.name)

        cwd = str(self.work_dir) if self.work_dir else str(script_path.parent)
        logger.info(f"执行: {script_path.name}")

        t0 = time.perf_counter()

        try:
            proc = subprocess.run(
                [self.python, str(script_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd,
            )

            elapsed = time.perf_counter() - t0
            success = proc.returncode == 0

            return {
                "success": success,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "elapsed": round(elapsed, 2),
                "returncode": proc.returncode,
            }

        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - t0
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时 ({self.timeout}s)",
                "elapsed": round(elapsed, 2),
                "returncode": -1,
            }
        except Exception as e:
            elapsed = time.perf_counter() - t0
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "elapsed": round(elapsed, 2),
                "returncode": -1,
            }
        finally:
            # 清理临时文件
            if not is_file:
                try:
                    script_path.unlink()
                except Exception:
                    pass

    def run_all(
        self,
        scripts: dict[int, str],  # {sub_id: code_string}
        parallel: bool = False,
    ) -> dict[int, dict]:
        """批量执行求解脚本。

        Args:
            scripts: {子问题ID: 代码} 字典
            parallel: 是否并行执行

        Returns:
            dict: {子问题ID: 执行结果}
        """
        results = {}

        if parallel:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(self.run, code, False): sub_id
                    for sub_id, code in scripts.items()
                }
                for future in as_completed(futures):
                    sub_id = futures[future]
                    try:
                        results[sub_id] = future.result()
                    except Exception as e:
                        results[sub_id] = {
                            "success": False, "stdout": "", "stderr": str(e),
                            "elapsed": 0, "returncode": -1,
                        }
        else:
            for sub_id, code in scripts.items():
                results[sub_id] = self.run(code, is_file=False)

        return results
