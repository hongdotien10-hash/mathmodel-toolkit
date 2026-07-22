"""数据读写模块 — Excel/CSV/MAT/JSON 快速读写。"""

from mathmodel.io.data import (
    read_data,
    write_data,
    read_excel_all,
    to_latex_table,
)

__all__ = [
    "read_data",
    "write_data",
    "read_excel_all",
    "to_latex_table",
]
