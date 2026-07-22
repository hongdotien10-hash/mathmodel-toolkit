"""数据读写工具。

提供竞赛常用的数据读写操作：Excel/CSV 批量加载、保存、LaTeX 表格导出等。
"""

from pathlib import Path
from typing import Optional, Union

import pandas as pd


def read_data(path: str | Path, **kwargs) -> pd.DataFrame:
    """智能读取数据文件，自动识别格式。

    Args:
        path: 文件路径（.xlsx/.xls/.csv/.json）
        **kwargs: 传递给 pd.read_csv / pd.read_excel 的额外参数

    Returns:
        pd.DataFrame: 数据
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path, **kwargs)
    elif suffix == ".csv":
        try:
            return pd.read_csv(path, encoding="utf-8", **kwargs)
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="gbk", **kwargs)
    elif suffix == ".json":
        return pd.read_json(path, **kwargs)
    else:
        raise ValueError(f"不支持的文件格式: {suffix}")


def read_excel_all(path: str | Path) -> dict[str, pd.DataFrame]:
    """读取 Excel 文件的所有 sheet。

    Args:
        path: Excel 文件路径

    Returns:
        dict: {sheet_name: DataFrame} 字典
    """
    xl = pd.ExcelFile(path)
    return {sheet: pd.read_excel(path, sheet_name=sheet) for sheet in xl.sheet_names}


def write_data(
    data: Union[pd.DataFrame, dict],
    path: str | Path,
    **kwargs,
) -> None:
    """保存数据到文件，自动识别格式。

    Args:
        data: 要保存的数据 (DataFrame 或 {sheet: DataFrame})
        path: 输出路径
        **kwargs: 传递给底层保存函数的额外参数
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()

    if suffix in (".xlsx", ".xls"):
        if isinstance(data, dict):
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                for sheet, df in data.items():
                    df.to_excel(writer, sheet_name=str(sheet)[:31], index=False, **kwargs)
        else:
            data.to_excel(path, index=False, **kwargs)
    elif suffix == ".csv":
        data.to_csv(path, index=False, encoding="utf-8-sig", **kwargs)
    elif suffix == ".json":
        if isinstance(data, pd.DataFrame):
            data.to_json(path, orient="records", force_ascii=False, indent=2, **kwargs)
        else:
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        raise ValueError(f"不支持的输出格式: {suffix}")


def to_latex_table(
    df: pd.DataFrame,
    caption: str = "",
    label: str = "",
    precision: int = 4,
    column_format: Optional[str] = None,
) -> str:
    """将 DataFrame 导出为 LaTeX 表格源码。

    Args:
        df: 数据表
        caption: 表格标题
        label: LaTeX label
        precision: 数值精度
        column_format: 列格式字符串（如 "lccc"），默认自动生成

    Returns:
        str: LaTeX tabular 代码
    """
    if column_format is None:
        column_format = "l" + "c" * (len(df.columns) - 1) if len(df.columns) > 1 else "lc"

    latex = df.to_latex(
        index=False,
        float_format=f"%.{precision}g",
        column_format=column_format,
        caption=caption,
        label=label,
        escape=False,
    )
    return latex
