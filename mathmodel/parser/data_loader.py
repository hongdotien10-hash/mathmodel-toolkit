"""数据附件自动发现和加载。"""

from pathlib import Path
from typing import Union

import pandas as pd


class DataLoader:
    """数据加载器。

    自动识别目录下的数据文件，加载为统一的 DataFrame / dict 格式。

    Usage::

        loader = DataLoader()
        data = loader.load_all("./data/")
        # {"附件1": DataFrame, "附件2_sheet1": DataFrame, ...}
    """

    SUPPORTED = {".xlsx", ".xls", ".csv", ".json", ".txt"}

    def __init__(self):
        self.loaded: dict[str, Union[pd.DataFrame, dict, str]] = {}

    def load_all(self, path: str | Path) -> dict:
        """加载目录下所有支持的数据文件。

        Args:
            path: 文件路径或目录路径

        Returns:
            dict: {文件名: 数据} 字典
        """
        p = Path(path)
        if p.is_file():
            return self._load_file(p)
        elif p.is_dir():
            result = {}
            for f in sorted(p.iterdir()):
                if f.suffix.lower() in self.SUPPORTED:
                    result.update(self._load_file(f))
            self.loaded.update(result)
            return result
        else:
            raise FileNotFoundError(f"路径不存在: {path}")

    def load_single(self, path: str | Path) -> Union[pd.DataFrame, dict, str]:
        """加载单个文件。"""
        p = Path(path)
        result = self._load_file(p)
        key = p.stem
        self.loaded[key] = result.get(key)
        return self.loaded[key]

    def _load_file(self, path: Path) -> dict:
        """加载单个文件，返回 {名称: 数据}。"""
        suffix = path.suffix.lower()
        name = path.stem

        if suffix in (".xlsx", ".xls"):
            xl = pd.ExcelFile(path)
            if len(xl.sheet_names) == 1:
                return {name: pd.read_excel(path)}
            return {
                f"{name}_{sheet}": pd.read_excel(path, sheet_name=sheet)
                for sheet in xl.sheet_names
            }

        elif suffix == ".csv":
            try:
                return {name: pd.read_csv(path, encoding="utf-8")}
            except UnicodeDecodeError:
                return {name: pd.read_csv(path, encoding="gbk")}

        elif suffix == ".json":
            import json
            with open(path, "r", encoding="utf-8") as f:
                return {name: json.load(f)}

        elif suffix == ".txt":
            try:
                return {name: path.read_text(encoding="utf-8")}
            except UnicodeDecodeError:
                return {name: path.read_text(encoding="gbk")}

        else:
            raise ValueError(f"不支持的文件格式: {suffix}")

    def summary(self) -> str:
        """生成已加载数据的摘要。"""
        lines = []
        for name, data in self.loaded.items():
            if isinstance(data, pd.DataFrame):
                lines.append(
                    f"  {name}: {data.shape[0]} 行 × {data.shape[1]} 列 "
                    f"[{data.shape[0] * data.shape[1]} 单元格]"
                )
            elif isinstance(data, dict):
                lines.append(f"  {name}: dict, {len(data)} keys")
            elif isinstance(data, str):
                lines.append(f"  {name}: str, {len(data)} chars")
            else:
                lines.append(f"  {name}: {type(data).__name__}")
        return "\n".join(lines) if lines else "（未加载数据）"
